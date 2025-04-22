import enum
import time
import uuid
from datetime import datetime
from enum import Enum
from typing import List, Dict, Optional, Literal, Any

from pydantic import BaseModel, Field, validator, field_validator


# ========== Resource Models ==========

class GoodType(str, enum.Enum):
    FOOD = "food"
    REST = "rest"
    FUN = "fun"


class Good(BaseModel):
    type: GoodType
    quality: float = Field(0.1, ge=0.0, le=1.0)
    name: Optional[str] = None


def agent_id_factory() -> str:
    """Generate a simple ID for an agent"""
    global agent_counter
    agent_counter += 1
    return f"agent_{agent_counter}"


class AgentPersonality(BaseModel):
    personality: str
    # TODO: Could be developed into e.g. OCEAN model
    """A basic description of the agent's personality."""


class AgentNeeds(BaseModel):
    """Basic needs that agents try to satisfy"""
    food: float = Field(1.0, ge=0.0, le=1.0)  # You know, for basic survival
    rest: float = Field(1.0, ge=0.0, le=1.0)  # Everyone needs sleep, for now
    fun: float = Field(1.0, ge=0.0, le=1.0)  # ALL WORK AND NO PLAY MAKES MARS A DULL PLANET


class Agent(BaseModel):
    """Economic agent in the simulation"""
    id: str = Field(default_factory=agent_id_factory)
    name: str
    age_days: int = 0  # Age in simulation days
    death_day: Optional[int] = None
    is_alive: bool = True
    personality: AgentPersonality
    credits: float = 0
    needs: AgentNeeds = Field(default_factory=AgentNeeds)
    goods: List[Good] = Field(default_factory=list)


class ActionType(str, Enum):
    """Types of actions and interactions an agent can take in the Mars economy"""
    # Basic individual actions
    REST = "REST"        # Rest to recover energy
    WORK = "WORK"        # Work at a colony-provided job, get credits for your time
    BUY =  "BUY"         # Purchase from a goods listing.
    SELL = "SELL"        # Offer a goods for sale as a new listing.
    HARVEST = "HARVEST"  # Harvest shrooms from a colony farm, get food for your time
    CRAFT   = "CRAFT"    # Invent a new item

class NarrationRequest(BaseModel):
    """Interaction to narrate."""
    actions: list[tuple[Agent, ActionType]]
    interactions: list[str]
    """The actions taken by agents this turn."""

class NarrativeResponse(BaseModel):
    """Structured response for narrative event generation"""

    title: str = Field(
        description="A catchy, thematic title that captures the core economic tension or relationship",
        max_length=10,
    )

    description: str = Field(
        description="A detailed scene with dialogue showing this interaction through character actions and reactions, "
                    "including environmental details that ground this exchange in the Martian setting",
        max_length=100
    )

valid_action_types = [t.value for t in ActionType]

class AgentActionResponse(BaseModel):
    """Structured response for agent action generation"""

    type: ActionType = Field(
        description=f"The type of action the agent will take. Must be one of {valid_action_types}"
    )

    extra: Dict[str, Any] = Field(
        description="Extra information specific to the action type"
    )

    reasoning: Optional[str] = Field(
        default=None,
        description="The reasoning behind the agent's action choice",
        max_length=500
    )
