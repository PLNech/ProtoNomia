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
        description="Extra information specific to the action type",
        default_factory=dict
    )

    reasoning: Optional[str] = Field(
        default=None,
        description="The reasoning behind the agent's choice",
        max_length=500
    )


# Daily Summary Response for day-level narration
class DailySummaryResponse(BaseModel):
    """Structured response for daily simulation summary"""

    title: str = Field(
        description="A catchy title for the day's events",
        max_length=50
    )

    summary: str = Field(
        description="A narrative summary of the day's events in the colony",
        max_length=500
    )

    highlights: List[str] = Field(
        description="Key moments or interesting events from the day",
        max_length=100
    )


# Example Daily Summaries for LLM guidance
example_daily_summary_1 = DailySummaryResponse(
    title="Dusty Deals and Shroom Dreams",
    summary="Day 3 on Mars brought economic stirrings as colonists began establishing trade. Sarah crafted a makeshift air filter, while Malik harvested the first batch of Martian mushrooms. Despite fatigue, colonists showed remarkable resilience, with jokes about 'getting rich in red dirt' echoing through the habitation units.",
    highlights=[
        "First market transaction: Malik sold Glowcaps to Alex for 50 credits",
        "Sarah's air filter invention was rated exceptional quality (0.9)",
        "Three colonists reported dangerous fatigue levels below 0.3"
    ]
)

example_daily_summary_2 = DailySummaryResponse(
    title="Fungal Fortune, Colonial Crisis",
    summary="Day 7 marked contrasts in the colony's development. The mushroom trade flourished with Dave's discovery of a premium growth technique, while resource scarcity led to the first heated market disputes. Meanwhile, Elena's critical rest levels resulted in the colony's first medical emergency, prompting discussions about work-life balance in the harsh Martian environment.",
    highlights=[
        "Dave improved mushroom quality through experimental growing techniques",
        "Market prices for food increased by 30% due to demand",
        "Elena collapsed from exhaustion (rest: 0.1), first critical health incident",
        "Colony implemented new rest rotation schedule"
    ]
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
