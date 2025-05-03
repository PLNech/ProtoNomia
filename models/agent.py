"""
ProtoNomia Agent Models
This module contains Pydantic models for agents in the ProtoNomia simulation.
"""
import uuid
from copy import deepcopy
from typing import List, Optional, Any, Dict, Tuple

from pydantic import BaseModel, Field, field_validator


def agent_id_factory() -> str:
    """Generate a unique ID for an agent"""
    return str(uuid.uuid4())


class AgentPersonality(BaseModel):
    """A basic description of the agent's personality."""
    text: str  # TODO: Could be developed into e.g. OCEAN model


class AgentNeeds(BaseModel):
    """Basic needs that agents try to satisfy"""
    food: float = Field(1.0)  # You know, for basic survival
    rest: float = Field(1.0)  # Everyone needs sleep, for now
    fun: float = Field(1.0)  # ALL WORK AND NO PLAY MAKES MARS A DULL PLANET

    @field_validator('food', 'rest', 'fun', mode='before')
    @classmethod
    def clamp_needs(cls, v: float) -> float:
        """Automatically clamp needs between 0 and 1"""
        return max(0.0, min(1.0, v))

    def __repr__(self):
        return f"Food: {self.food:.2%}|Rest: {self.rest:.2%}|Fun: {self.fun:.2%}"

    def __str__(self):
        if self.food < 0.2:
            food_str = "Starving"
        elif self.food < 0.4:
            food_str = "Hungry"
        elif self.food < 0.6:
            food_str = "Somewhat hungry"
        elif self.food < 0.8:
            food_str = "Ate well"
        else:
            food_str = "Overfed"
        if self.rest < 0.2:
            rest_str = "Exhausted"
        elif self.rest < 0.4:
            rest_str = "Tired"
        elif self.rest < 0.6:
            rest_str = "Average energy"
        elif self.rest < 0.8:
            rest_str = "Energetic"
        else:
            rest_str = "Supercharged"
        if self.fun < 0.2:
            fun_str = "Bored to death"
        elif self.fun < 0.4:
            fun_str = "Pretty bored"
        elif self.fun < 0.6:
            fun_str = "Kinda bored"
        else:
            fun_str = "Having fun"
        return f"{food_str}, {rest_str}, {fun_str}"


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
    goods: List[Any] = Field(default_factory=list)  # Circular import prevention - will be List[Good]

    # Using Any type for AgentActionResponse to avoid circular imports
    history: List[Tuple[float, AgentNeeds, List[Any], Any]] = Field(default_factory=list)
    memory: int = 5

    def record(self, action: Any):
        """Record an action in the agent's history"""
        self.history.append((deepcopy(self.credits), deepcopy(self.needs), deepcopy(self.goods), action)) 