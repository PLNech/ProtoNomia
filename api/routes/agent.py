"""
ProtoNomia Agent Routes
This module provides API routes for agent operations.
"""
import logging
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, HTTPException, Query, Path, Body

from api.models import (
    AgentCreateRequest, AgentCreateResponse,
    AgentDeleteRequest, AgentUpdateRequest,
    AgentResponse, StatusResponse
)
from api.simulation_manager import simulation_manager
from models import Agent, AgentNeeds, AgentPersonality, Good

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/add", response_model=AgentCreateResponse)
async def add_agent(request: AgentCreateRequest):
    """
    Add a new agent to a simulation.
    
    Args:
        request: Agent creation parameters
        
    Returns:
        AgentCreateResponse: Information about the new agent
    """
    # Check if the simulation exists
    simulation = simulation_manager.get_simulation(request.simulation_id)
    if not simulation:
        raise HTTPException(status_code=404, detail=f"Simulation {request.simulation_id} not found")
    
    try:
        # Prepare agent creation parameters
        agent_params = {}
        
        if request.name:
            agent_params["name"] = request.name
        
        if request.age_days:
            agent_params["age_days"] = request.age_days
        
        if request.personality:
            agent_params["personality_str"] = request.personality
        
        if request.needs:
            agent_params["needs"] = AgentNeeds(
                food=request.needs.get("food", 0.8),
                rest=request.needs.get("rest", 0.8),
                fun=request.needs.get("fun", 0.8)
            )
        
        if request.starting_credits:
            agent_params["starting_credits"] = request.starting_credits
        
        if request.goods:
            agent_params["goods"] = request.goods
        
        # Create the agent
        agent = simulation_manager.create_agent(request.simulation_id, **agent_params)
        
        return AgentCreateResponse(
            agent_id=agent.id,
            name=agent.name,
            status="created"
        )
    except Exception as e:
        logger.error(f"Error creating agent: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error creating agent: {str(e)}")


@router.delete("/kill", response_model=StatusResponse)
async def kill_agent(
    simulation_id: str = Query(..., description="ID of the simulation"),
    agent_id: Optional[str] = Query(None, description="ID of the agent"),
    agent_name: Optional[str] = Query(None, description="Name of the agent")
):
    """
    Kill an agent in a simulation.
    
    Args:
        simulation_id: ID of the simulation
        agent_id: ID of the agent (optional)
        agent_name: Name of the agent (optional)
        
    Returns:
        StatusResponse: Result of the operation
    """
    # Validate request
    if not agent_id and not agent_name:
        raise HTTPException(status_code=400, detail="Must provide either agent_id or agent_name")
    
    # Get the agent
    agent = simulation_manager.get_agent(
        simulation_id,
        agent_id=agent_id,
        agent_name=agent_name
    )
    
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent not found in simulation {request.simulation_id}")
    
    # Kill the agent
    if not simulation_manager.kill_agent(simulation_id, agent):
        raise HTTPException(status_code=500, detail=f"Failed to kill agent {agent.name}")
    
    return StatusResponse(
        status="success",
        message=f"Agent {agent.name} killed"
    )


@router.get("/status", response_model=AgentResponse)
async def get_agent_status(
    simulation_id: str = Query(..., description="ID of the simulation"),
    agent_id: Optional[str] = Query(None, description="ID of the agent"),
    agent_name: Optional[str] = Query(None, description="Name of the agent")
):
    """
    Get the status of an agent.
    
    Args:
        simulation_id: ID of the simulation
        agent_id: ID of the agent (optional)
        agent_name: Name of the agent (optional)
        
    Returns:
        AgentResponse: The agent information
    """
    # Validate request
    if not agent_id and not agent_name:
        raise HTTPException(status_code=400, detail="Must provide either agent_id or agent_name")
    
    # Get the agent
    agent = simulation_manager.get_agent(
        simulation_id,
        agent_id=agent_id,
        agent_name=agent_name
    )
    
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent not found in simulation {simulation_id}")
    
    return AgentResponse(
        agent=agent,
        status="active" if agent.is_alive else "dead"
    )


@router.put("/update", response_model=AgentResponse)
async def update_agent(request: AgentUpdateRequest):
    """
    Update an agent in a simulation.
    
    Args:
        request: Agent update parameters
        
    Returns:
        AgentResponse: The updated agent information
    """
    # Get the agent
    agent = simulation_manager.get_agent(
        request.simulation_id,
        agent_id=request.agent_id
    )
    
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent not found in simulation {request.simulation_id}")
    
    # Update the agent
    if not simulation_manager.update_agent(request.simulation_id, agent, request.updates):
        raise HTTPException(status_code=500, detail=f"Failed to update agent {agent.name}")
    
    return AgentResponse(
        agent=agent,
        status="updated"
    ) 