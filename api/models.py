"""
ProtoNomia API Models
This module defines the Pydantic models for API requests and responses.
"""
from typing import Dict, List, Optional, Any, Union

from pydantic import BaseModel, Field

from models import (
    Agent, Good, GoodType, AgentNeeds, SimulationState,
    AgentPersonality, SimulationStage
)


# Common models
class StatusResponse(BaseModel):
    """Generic status response."""
    status: str
    message: str


# Simulation models
class SimulationCreateRequest(BaseModel):
    """Request body for creating a new simulation."""
    num_agents: int = Field(5, description="Number of agents in the simulation")
    max_days: int = Field(30, description="Maximum number of days to run the simulation")
    starting_credits: Optional[int] = Field(None, description="Starting credits for each agent (random if None)")
    model_name: str = Field("gemma3:4b", description="LLM model to use")
    temperature: float = Field(0.7, description="LLM temperature")
    top_p: float = Field(0.9, description="Top-p sampling parameter")
    top_k: int = Field(40, description="Top-k sampling parameter")
    output_dir: str = Field("output", description="Directory for output files")


class SimulationCreateResponse(BaseModel):
    """Response body for creating a new simulation."""
    simulation_id: str
    status: str
    num_agents: int
    max_days: int


class SimulationStatusResponse(BaseModel):
    """Response body for getting simulation status."""
    simulation_id: str
    day: int
    agents_count: int
    dead_agents_count: int
    market_listings_count: int
    inventions_count: int
    ideas_count: int
    songs_count: int
    current_stage: SimulationStage = Field(
        default=SimulationStage.INITIALIZATION,
        description="Current stage of the simulation"
    )
    current_agent_id: Optional[str] = Field(
        default=None,
        description="ID of the agent currently being processed (if applicable)"
    )
    current_agent_name: Optional[str] = Field(
        default=None,
        description="Name of the agent currently being processed (if applicable)"
    )
    night_activities_today: int = Field(
        default=0,
        description="Number of night activities processed today"
    )


class SimulationDetailResponse(BaseModel):
    """Detailed simulation status including all state."""
    simulation_id: str
    state: SimulationState


# Agent models
class AgentCreateRequest(BaseModel):
    """Request body for creating a new agent."""
    simulation_id: str
    name: Optional[str] = None
    age_days: Optional[int] = None
    personality: Optional[str] = None
    needs: Optional[Dict[str, float]] = None
    starting_credits: Optional[float] = None
    goods: Optional[List[Dict[str, Any]]] = None


class AgentCreateResponse(BaseModel):
    """Response body for creating a new agent."""
    agent_id: str
    name: str
    status: str


class AgentDeleteRequest(BaseModel):
    """Request body for deleting an agent."""
    simulation_id: str
    agent_id: Optional[str] = None
    agent_name: Optional[str] = None


class AgentUpdateRequest(BaseModel):
    """Request body for updating an agent."""
    simulation_id: str
    agent_id: str
    updates: Dict[str, Any] = Field(..., description="Agent properties to update")


class AgentResponse(BaseModel):
    """Response body for agent operations."""
    agent: Agent
    status: str 