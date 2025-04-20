import logging
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

from ..core.simulation import ProtoNomiaSimulation, create_simulation
from ..models.base import SimulationConfig

logger = logging.getLogger(__name__)

# API Models
class SimulationConfigRequest(BaseModel):
    """Configuration for creating a new simulation"""
    name: str = Field("ProtoNomia", description="Name of the simulation")
    seed: Optional[int] = Field(None, description="Random seed for reproducibility")
    initial_population: int = Field(100, description="Initial population size")
    max_population: int = Field(1000, description="Maximum population size")
    resource_scarcity: float = Field(0.5, ge=0.0, le=1.0, description="Resource scarcity level (0.0-1.0)")
    technological_level: float = Field(0.8, ge=0.0, le=1.0, description="Technological advancement level (0.0-1.0)")
    narrative_verbosity: int = Field(3, ge=1, le=5, description="Narrative detail level (1-5)")
    agent_model: str = Field("gemma:1b", description="LLM model for agent decisions")
    narrator_model: str = Field("gemma:1b", description="LLM model for narrative generation")
    ollama_base_url: str = Field("http://localhost:11434/v1", description="Ollama API base URL")

class SimulationResponse(BaseModel):
    """Response with simulation information"""
    id: str
    name: str
    current_tick: int
    current_date: str
    active_agents: int
    deceased_agents: int
    active_interactions: int
    narrative_events: int

class AgentResponse(BaseModel):
    """Response with agent information"""
    id: str
    name: str
    type: str
    faction: str
    age_days: int
    is_alive: bool
    location: str
    personality: Dict[str, float]
    needs: Dict[str, float]
    resources: List[Dict[str, Any]]
    background: str

class NarrativeEventResponse(BaseModel):
    """Response with narrative event information"""
    id: str
    timestamp: str
    title: str
    description: str
    agents_involved: List[str]
    significance: float
    tags: List[str]

class EconomicReportResponse(BaseModel):
    """Response with economic report information"""
    indicators: Dict[str, float]
    resource_distribution: Dict[str, float]
    faction_wealth: Dict[str, float]
    active_interactions_by_type: Dict[str, int]

class NarrativeSummaryResponse(BaseModel):
    """Response with narrative summary"""
    summary: str
    date: str

class TickResponse(BaseModel):
    """Response for a simulation tick"""
    tick: int
    date: str
    active_agents: int
    active_interactions: int
    economic_indicators: Dict[str, float]

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, simulation_id: str):
        await websocket.accept()
        if simulation_id not in self.active_connections:
            self.active_connections[simulation_id] = []
        self.active_connections[simulation_id].append(websocket)

    def disconnect(self, websocket: WebSocket, simulation_id: str):
        if simulation_id in self.active_connections:
            if websocket in self.active_connections[simulation_id]:
                self.active_connections[simulation_id].remove(websocket)
            
            # Clean up empty lists
            if not self.active_connections[simulation_id]:
                del self.active_connections[simulation_id]

    async def broadcast(self, simulation_id: str, message: Dict[str, Any]):
        if simulation_id in self.active_connections:
            for connection in self.active_connections[simulation_id]:
                await connection.send_json(message)

# Initialize FastAPI app
app = FastAPI(
    title="ProtoNomia API",
    description="API for the ProtoNomia Mars economy simulation",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development - restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize WebSocket connection manager
manager = ConnectionManager()

# Store active simulations
simulations: Dict[str, ProtoNomiaSimulation] = {}

# Background tasks
running_tasks: Dict[str, asyncio.Task] = {}

# Event handlers
def on_agent_created(agent):
    """Handler for agent_created event"""
    simulation_id = "current"  # This should be dynamic in a multi-simulation environment
    if simulation_id in simulations:
        asyncio.create_task(
            manager.broadcast(
                simulation_id,
                {
                    "event": "agent_created",
                    "data": {
                        "id": agent.id,
                        "name": agent.name,
                        "faction": agent.faction.value,
                        "type": agent.agent_type.value,
                        "location": agent.location
                    }
                }
            )
        )

def on_interaction_completed(interaction):
    """Handler for interaction_completed event"""
    simulation_id = "current"  # This should be dynamic in a multi-simulation environment
    if simulation_id in simulations:
        asyncio.create_task(
            manager.broadcast(
                simulation_id,
                {
                    "event": "interaction_completed",
                    "data": {
                        "id": interaction.id,
                        "type": interaction.interaction_type.value,
                        "is_complete": interaction.is_complete,
                        "participants": list(interaction.participants.keys()),
                        "narrative_significance": interaction.narrative_significance
                    }
                }
            )
        )

def on_narrative_event(event):
    """Handler for narrative_event event"""
    simulation_id = "current"  # This should be dynamic in a multi-simulation environment
    if simulation_id in simulations:
        asyncio.create_task(
            manager.broadcast(
                simulation_id,
                {
                    "event": "narrative_event",
                    "data": {
                        "id": event.id,
                        "title": event.title,
                        "description": event.description,
                        "timestamp": event.timestamp.isoformat(),
                        "agents_involved": event.agents_involved,
                        "significance": event.significance
                    }
                }
            )
        )

def on_tick_completed(tick, date):
    """Handler for tick_completed event"""
    simulation_id = "current"  # This should be dynamic in a multi-simulation environment
    if simulation_id in simulations:
        sim = simulations[simulation_id]
        asyncio.create_task(
            manager.broadcast(
                simulation_id,
                {
                    "event": "tick_completed",
                    "data": {
                        "tick": tick,
                        "date": date.isoformat(),
                        "active_agents": len([a for a in sim.agents.values() if a.is_alive]),
                        "active_interactions": len(sim.active_interactions),
                        "economic_indicators": sim.economic_indicators
                    }
                }
            )
        )

# Background simulation runner
async def run_simulation(simulation_id: str, speed: float = 1.0):
    """Run a simulation in the background
    
    Args:
        simulation_id: ID of the simulation to run
        speed: How many seconds between ticks (lower is faster)
    """
    if simulation_id not in simulations:
        logger.error(f"Simulation {simulation_id} not found")
        return
    
    sim = simulations[simulation_id]
    logger.info(f"Starting simulation {simulation_id} at speed {speed}")
    
    try:
        while True:
            # Run one tick
            result = await sim.simulate_tick()
            
            # Wait for the next tick
            await asyncio.sleep(speed)
    except asyncio.CancelledError:
        logger.info(f"Simulation {simulation_id} stopped")
    except Exception as e:
        logger.error(f"Error running simulation {simulation_id}: {str(e)}")

# Routes
@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "ProtoNomia API is running"}

@app.post("/simulations", response_model=SimulationResponse)
async def create_new_simulation(config: SimulationConfigRequest):
    """Create a new simulation"""
    # For MVP, we only support one simulation
    simulation_id = "current"
    
    # Stop any existing simulation
    if simulation_id in running_tasks:
        running_tasks[simulation_id].cancel()
        try:
            await running_tasks[simulation_id]
        except asyncio.CancelledError:
            pass
    
    # Create simulation config
    sim_config = SimulationConfig(
        name=config.name,
        seed=config.seed,
        initial_population=config.initial_population,
        max_population=config.max_population,
        resource_scarcity=config.resource_scarcity,
        technological_level=config.technological_level,
        narrative_verbosity=config.narrative_verbosity
    )
    
    # Create and initialize simulation
    sim = create_simulation(
        config=sim_config,
        ollama_base_url=config.ollama_base_url,
        agent_model=config.agent_model,
        narrator_model=config.narrator_model
    )
    
    # Register event handlers
    sim.register_event_listener("agent_created", on_agent_created)
    sim.register_event_listener("interaction_completed", on_interaction_completed)
    sim.register_event_listener("narrative_event", on_narrative_event)
    sim.register_event_listener("tick_completed", on_tick_completed)
    
    # Store simulation
    simulations[simulation_id] = sim
    
    # Get simulation state
    state = sim.get_state_snapshot()
    
    return {
        "id": simulation_id,
        "name": config.name,
        "current_tick": state["current_tick"],
        "current_date": state["current_date"],
        "active_agents": state["active_agents"],
        "deceased_agents": state["deceased_agents"],
        "active_interactions": state["active_interactions"],
        "narrative_events": state["narrative_events"]
    }

@app.get("/simulations/{simulation_id}", response_model=SimulationResponse)
async def get_simulation(simulation_id: str):
    """Get information about a simulation"""
    if simulation_id not in simulations:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    sim = simulations[simulation_id]
    state = sim.get_state_snapshot()
    
    return {
        "id": simulation_id,
        "name": sim.config.name,
        "current_tick": state["current_tick"],
        "current_date": state["current_date"],
        "active_agents": state["active_agents"],
        "deceased_agents": state["deceased_agents"],
        "active_interactions": state["active_interactions"],
        "narrative_events": state["narrative_events"]
    }

@app.post("/simulations/{simulation_id}/start")
async def start_simulation(simulation_id: str, speed: float = Query(1.0, ge=0.1, le=10.0)):
    """Start or resume a simulation"""
    if simulation_id not in simulations:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    # Cancel existing task if running
    if simulation_id in running_tasks:
        running_tasks[simulation_id].cancel()
        try:
            await running_tasks[simulation_id]
        except asyncio.CancelledError:
            pass
    
    # Start new background task
    task = asyncio.create_task(run_simulation(simulation_id, speed))
    running_tasks[simulation_id] = task
    
    return {"message": f"Simulation {simulation_id} started with speed {speed}"}

@app.post("/simulations/{simulation_id}/stop")
async def stop_simulation(simulation_id: str):
    """Stop a running simulation"""
    if simulation_id not in simulations:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    if simulation_id in running_tasks:
        running_tasks[simulation_id].cancel()
        try:
            await running_tasks[simulation_id]
        except asyncio.CancelledError:
            pass
        running_tasks.pop(simulation_id)
        return {"message": f"Simulation {simulation_id} stopped"}
    
    return {"message": f"Simulation {simulation_id} is not running"}

@app.post("/simulations/{simulation_id}/tick", response_model=TickResponse)
async def run_single_tick(simulation_id: str):
    """Run a single tick of the simulation"""
    if simulation_id not in simulations:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    # Cancel running task if present
    if simulation_id in running_tasks:
        running_tasks[simulation_id].cancel()
        try:
            await running_tasks[simulation_id]
        except asyncio.CancelledError:
            pass
        running_tasks.pop(simulation_id)
    
    # Run a single tick
    sim = simulations[simulation_id]
    result = await sim.simulate_tick()
    
    return result

@app.get("/simulations/{simulation_id}/agents", response_model=List[AgentResponse])
async def get_agents(
    simulation_id: str, 
    alive_only: bool = Query(True, description="Only return living agents"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of agents to return"),
    faction: Optional[str] = Query(None, description="Filter by faction")
):
    """Get agents in a simulation"""
    if simulation_id not in simulations:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    sim = simulations[simulation_id]
    
    # Filter agents
    filtered_agents = []
    for agent_id, agent in sim.agents.items():
        if alive_only and not agent.is_alive:
            continue
        if faction and agent.faction.value != faction:
            continue
        
        agent_data = sim.get_agent_details(agent_id)
        filtered_agents.append(agent_data)
        
        if len(filtered_agents) >= limit:
            break
    
    return filtered_agents

@app.get("/simulations/{simulation_id}/agents/{agent_id}", response_model=AgentResponse)
async def get_agent(simulation_id: str, agent_id: str):
    """Get information about a specific agent"""
    if simulation_id not in simulations:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    sim = simulations[simulation_id]
    agent_details = sim.get_agent_details(agent_id)
    
    if not agent_details:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return agent_details

@app.get("/simulations/{simulation_id}/narrative/events", response_model=List[NarrativeEventResponse])
async def get_narrative_events(
    simulation_id: str,
    limit: int = Query(20, ge=1, le=100, description="Maximum number of events to return")
):
    """Get recent narrative events"""
    if simulation_id not in simulations:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    sim = simulations[simulation_id]
    events = sim.get_recent_narrative_events(limit)
    
    return events

@app.get("/simulations/{simulation_id}/narrative/summary", response_model=NarrativeSummaryResponse)
async def get_narrative_summary(
    simulation_id: str,
    period: str = Query("day", description="Summary period (day, week, month)")
):
    """Get a narrative summary of recent events"""
    if simulation_id not in simulations:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    sim = simulations[simulation_id]
    summary = sim.narrator.get_narrative_summary(period)
    
    return {
        "summary": summary,
        "date": sim.current_date.isoformat()
    }

@app.get("/simulations/{simulation_id}/economy", response_model=EconomicReportResponse)
async def get_economic_report(simulation_id: str):
    """Get economic report for a simulation"""
    if simulation_id not in simulations:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    sim = simulations[simulation_id]
    report = sim.get_economic_report()
    
    return report

@app.websocket("/ws/{simulation_id}")
async def websocket_endpoint(websocket: WebSocket, simulation_id: str):
    """WebSocket endpoint for real-time updates"""
    if simulation_id not in simulations:
        await websocket.accept()
        await websocket.send_json({"error": "Simulation not found"})
        await websocket.close()
        return
    
    await manager.connect(websocket, simulation_id)
    
    try:
        while True:
            # Wait for client messages
            _ = await websocket.receive_text()
            
            # Send current state
            sim = simulations[simulation_id]
            state = sim.get_state_snapshot()
            await websocket.send_json({
                "event": "state_update",
                "data": state
            })
    except WebSocketDisconnect:
        manager.disconnect(websocket, simulation_id)

# Run the FastAPI app when this file is executed directly
if __name__ == "__main__":
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)