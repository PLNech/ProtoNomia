import enum
import time
import uuid
from datetime import datetime
from enum import Enum
from typing import List, Dict, Optional, Literal, Any

from pydantic import BaseModel, Field, validator, field_validator, ConfigDict, model_validator

from src.generators import generate_thoughts


# noinspection PyDataclass
# The above error seems a false-positive


# ========== Resource Models ==========

class GoodType(str, enum.Enum):
    FOOD = "food"
    REST = "rest"
    FUN = "fun"


class Good(BaseModel):
    type: GoodType
    quality: float = Field(0.1)
    name: Optional[str] = None

    @field_validator('quality', mode='before')
    @classmethod
    def clamp_quality(cls, v: float) -> float:
        """Automatically clamp quality between 0 and 1"""
        return max(0.0, min(1.0, v))


# Initialize a global counter for agent IDs
agent_counter = 0


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
    personality: AgentPersonality = "no personality."
    credits: float = 0
    needs: AgentNeeds = Field(default_factory=AgentNeeds)
    goods: List[Good] = Field(default_factory=list)


class ActionType(str, Enum):
    """Types of actions and interactions an agent can take in the Mars economy"""
    # Basic individual actions
    REST = "REST"  # Rest to recover energy
    WORK = "WORK"  # Work at a colony-provided job, get credits for your time
    BUY = "BUY"  # Purchase from a goods listing.
    SELL = "SELL"  # Offer a goods for sale as a new listing.
    HARVEST = "HARVEST"  # Harvest shrooms from a colony farm, get food for your time
    CRAFT = "CRAFT"  # Invent a new item
    THINK = "THINK"  # Spend the day thinking

ACTION_DESCRIPTIONS = {ActionType.REST: "Rest to recover energy",
                       ActionType.WORK: "Work at a colony-provided job, get credits for your time",
                       ActionType.BUY: "Purchase from a goods listing.",
                       ActionType.SELL: "Offer a goods for sale as a new listing.",
                       ActionType.HARVEST: "Harvest shrooms from a colony farm, get food for your time",
                       ActionType.CRAFT: "Invent an item which could improve your conditions or be sold for credits.",
                       ActionType.THINK: "Spend the day creatively thinking about inventions, culture, philosophy, "
                                         "etc. YOU MUST PUT YOUR THOUGHTS INSIDE YOUR REASONING FIELD"
                       }

class MarketListing(BaseModel):
    """A listing on the global market"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    seller_id: str
    good: Good
    price: float
    listed_on_day: int


class GlobalMarket(BaseModel):
    """Global market for goods exchange"""
    listings: List[MarketListing] = Field(default_factory=list)

    def add_listing(self, seller_id: str, good: Good, price: float, day: int) -> MarketListing:
        """Add a new listing to the market"""
        listing = MarketListing(
            seller_id=seller_id,
            good=good,
            price=price,
            listed_on_day=day
        )
        self.listings.append(listing)
        return listing

    def remove_listing(self, listing_id: str) -> bool:
        """Remove a listing from the market"""
        for i, listing in enumerate(self.listings):
            if listing.id == listing_id:
                self.listings.pop(i)
                return True
        return False

    def get_listings(self, filter_type: Optional[GoodType] = None) -> List[MarketListing]:
        """Get all listings, optionally filtered by type"""
        if filter_type is None:
            return self.listings
        return [l for l in self.listings if l.good.type == filter_type]


class AgentAction(BaseModel):
    """An action taken by an agent in the simulation"""
    agent_id: str
    type: ActionType
    extras: Dict[str, Any] = Field(default_factory=dict)
    reasoning: str = ""
    day: int


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
        description="A detailed scene with dialogue (always inside double quotes) showing this interaction through character actions and reactions, "
                    "including environmental details that ground this exchange in the Martian setting",
        max_length=100
    )


class AgentActionResponse(BaseModel):
    """Structured response for agent action generation"""

    model_config = ConfigDict(extra='allow')

    reasoning: Optional[str] = Field(
        default=None,
        description="Your short step-by-step reasoning for choosing this Action Type. "
                    "You must talk first person as the agent, don't break character, don't mention validation. "
                    "MAX 20 words. Use abbrevs and Mars 2993-setting appropriate urban slang. "
                    "Keep it EXTRA SHORT and concise. e.g \"I'm low on food, gotta harvest some shrooms 2day\""
    )

    type: ActionType = Field(
        description=f"The type of action the agent will take. Must be one of {[a.value for a in ActionType]}"
    )

    extras: Dict[str, Any] = Field(description="Extra information specific to the action type", default_factory=dict)


    @model_validator(mode="after")
    def default_reasoning_for_think(cls, model):
        if (
            model.type == ActionType.THINK and
            (model.reasoning is None or model.reasoning.strip() == "")
        ):
            model.reasoning = generate_thoughts()
        return model



class DailySummaryResponse(BaseModel):
    """Structured response for daily simulation summary"""

    title: str = Field(
        description="A catchy title for today's events. REQUIRED. MAXIMUM 8 WORDS"
    )

    content: str = Field(
        description="A narrative summary of the day's events in the colony. "
                    "You can use light markdown highlighting in bold/italics/inlinecode. "
                    "REQUIRED. MIN 10 WORDS MAX 30."
    )


class ActionLog(BaseModel):
    action: AgentActionResponse
    agent: Agent
    day: int


class SimulationState(BaseModel):
    """State of the simulation"""
    market: GlobalMarket = Field(default_factory=GlobalMarket)
    agents: List[Agent] = Field(default_factory=list)
    day: int = 0
    dead_agents: List[Agent] = Field(default_factory=list)
    actions: List[ActionLog] = Field(default_factory=list)

    def add_action(self, agent: Agent, action: AgentActionResponse) -> None:
        self.actions.append(ActionLog(action=action, agent=agent, day=self.day))

    @property
    def today_actions(self) -> List[ActionLog]:
        return [a for a in self.actions if a.day is self.day]
