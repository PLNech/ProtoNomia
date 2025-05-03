"""
ProtoNomia Simulation Routes
This module provides API routes for simulation operations.
"""
import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, Path

from api.models import (
    SimulationCreateRequest, SimulationCreateResponse,
    SimulationStatusResponse, SimulationDetailResponse,
    StatusResponse
)
from api.simulation_manager import simulation_manager
from models import SimulationState

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/start", response_model=SimulationCreateResponse)
async def start_simulation(request: SimulationCreateRequest):
    """
    Start a new simulation with the specified parameters.
    
    Returns:
        SimulationCreateResponse: Information about the new simulation
    """
    try:
        # Create the simulation
        simulation = simulation_manager.create_simulation(
            num_agents=request.num_agents,
            max_days=request.max_days,
            starting_credits=request.starting_credits,
            model_name=request.model_name,
            temperature=request.temperature,
            top_p=request.top_p,
            top_k=request.top_k,
            output_dir=request.output_dir
        )
        
        # Initialize the simulation state
        simulation.setup_initial_state()
        
        return SimulationCreateResponse(
            simulation_id=simulation.simulation_id,
            status="created",
            num_agents=request.num_agents,
            max_days=request.max_days
        )
    except Exception as e:
        logger.error(f"Error starting simulation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error starting simulation: {str(e)}")


@router.get("/status/{simulation_id}", response_model=SimulationStatusResponse)
async def get_simulation_status(
    simulation_id: str = Path(..., description="ID of the simulation to get status for")
):
    """
    Get the current status of a simulation.
    
    Args:
        simulation_id: ID of the simulation
        
    Returns:
        SimulationStatusResponse: Summary of the simulation status
    """
    simulation = simulation_manager.get_simulation(simulation_id)
    if not simulation:
        raise HTTPException(status_code=404, detail=f"Simulation {simulation_id} not found")
    
    return SimulationStatusResponse(
        simulation_id=simulation_id,
        day=simulation.state.day,
        agents_count=len(simulation.state.agents),
        dead_agents_count=len(simulation.state.dead_agents),
        market_listings_count=len(simulation.state.market.listings),
        inventions_count=simulation.state.count_inventions(),
        ideas_count=sum(len(ideas) for ideas in simulation.state.ideas.values()),
        songs_count=len(simulation.state.songs)
    )


@router.get("/detail/{simulation_id}", response_model=SimulationDetailResponse)
async def get_simulation_detail(
    simulation_id: str = Path(..., description="ID of the simulation to get details for")
):
    """
    Get detailed information about a simulation.
    
    Args:
        simulation_id: ID of the simulation
        
    Returns:
        SimulationDetailResponse: Detailed simulation state
    """
    simulation = simulation_manager.get_simulation(simulation_id)
    if not simulation:
        raise HTTPException(status_code=404, detail=f"Simulation {simulation_id} not found")
    
    return SimulationDetailResponse(
        simulation_id=simulation_id,
        state=simulation.state
    )


@router.post("/run/{simulation_id}", response_model=SimulationStatusResponse)
async def run_simulation_day(
    simulation_id: str = Path(..., description="ID of the simulation to run"),
    days: int = Query(1, description="Number of days to simulate")
):
    """
    Run the simulation for a specified number of days.
    
    Args:
        simulation_id: ID of the simulation
        days: Number of days to simulate
        
    Returns:
        SimulationStatusResponse: Updated simulation status
    """
    simulation = simulation_manager.get_simulation(simulation_id)
    if not simulation:
        raise HTTPException(status_code=404, detail=f"Simulation {simulation_id} not found")
    
    try:
        for _ in range(days):
            simulation.process_day()
            
            # Save the state to history
            state_copy = SimulationState.model_validate(simulation.state.model_dump())
            simulation.history.add(state_copy)
            
            # Save state to file (optional)
            simulation._save_state()
            
            # Move to the next day
            simulation.state.day += 1
        
        return SimulationStatusResponse(
            simulation_id=simulation_id,
            day=simulation.state.day,
            agents_count=len(simulation.state.agents),
            dead_agents_count=len(simulation.state.dead_agents),
            market_listings_count=len(simulation.state.market.listings),
            inventions_count=simulation.state.count_inventions(),
            ideas_count=sum(len(ideas) for ideas in simulation.state.ideas.values()),
            songs_count=len(simulation.state.songs)
        )
    except Exception as e:
        logger.error(f"Error running simulation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error running simulation: {str(e)}")


@router.get("/list", response_model=List[str])
async def list_simulations():
    """
    Get a list of all simulation IDs.
    
    Returns:
        List[str]: List of simulation IDs
    """
    return simulation_manager.list_simulations()


@router.delete("/{simulation_id}", response_model=StatusResponse)
async def delete_simulation(
    simulation_id: str = Path(..., description="ID of the simulation to delete")
):
    """
    Delete a simulation.
    
    Args:
        simulation_id: ID of the simulation to delete
        
    Returns:
        StatusResponse: Result of the operation
    """
    if not simulation_manager.delete_simulation(simulation_id):
        raise HTTPException(status_code=404, detail=f"Simulation {simulation_id} not found")
    
    return StatusResponse(
        status="success",
        message=f"Simulation {simulation_id} deleted"
    ) 