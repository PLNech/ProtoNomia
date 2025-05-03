"""
ProtoNomia Simulation Models
This module contains Pydantic models for simulation state and actions.
"""
import enum
import hashlib
import logging
import uuid
import random
from collections import defaultdict
from enum import Enum
from typing import List, Dict, Optional, Any, DefaultDict, TYPE_CHECKING, Union, Set

from pydantic import BaseModel, Field, field_validator, ConfigDict, model_validator

from models.agent import Agent  # Import the Agent model

# Avoid circular imports while maintaining type checking
if TYPE_CHECKING:
    from models.agent import Agent

# Initialize logger
logger = logging.getLogger(__name__)


# ========== Resource Models ==========

class GoodType(str, enum.Enum):
    FOOD = "FOOD"
    REST = "REST"
    FUN = "FUN"

    @classmethod
    def random(cls) -> "GoodType":
        return random.choice([v for v in GoodType])

    @classmethod
    def is_valid(self, key: str) -> bool:
        return key in [v.value for v in GoodType]

    @staticmethod
    def all() -> str:
        return f"{', '.join([v.value for v in GoodType])}"


class Good(BaseModel):
    type: GoodType
    quality: float = Field(0.1)
    name: Optional[str] = None

    @field_validator('quality', mode='before')
    @classmethod
    def clamp_quality(cls, v: float) -> float:
        """Automatically clamp quality between 0 and 1"""
        return max(0.0, min(1.0, v))
    
    def __str__(self) -> str:
        return f"{self.name or 'Random {self.type.value} item'} [{self.type.value}] ({self.quality:.2f} quality)"

    def __hash__(self) -> int:
        # Convert None to empty string for consistent hashing
        str_part = f"{self.name or ''} - {self.type}"
        # Convert float to string with fixed precision
        float_str = f"{self.quality:.6f}"

        # Serialize components in consistent order
        hash_input = (
                str_part.encode() +
                float_str.encode()
        )

        # Generate SHA256 hash and convert to integer
        return int.from_bytes(
            hashlib.sha256(hash_input).digest(),
            byteorder='big'
        )


class ActionType(str, Enum):
    """Types of actions and interactions an agent can take in the Mars economy.

    When adding a new one, you must:
    - Define it here
    - Add it to the below ACTION_DESCRIPTIONS with a straightforward description.
    - Ensure it's presented with eventual extras in format_prompt()
    - Add to SimulationState a state tracking of this new action consequences
    - Add a simulation.execute_XXX function
    - Add to the narrator some new state description

    """
    # Basic individual actions
    REST = "REST"  # Rest to recover energy
    WORK = "WORK"  # Work at a settlement-provided job, get credits for your time
    BUY = "BUY"  # Purchase from a goods listing.
    SELL = "SELL"  # Offer a goods for sale as a new listing.
    HARVEST = "HARVEST"  # Harvest shrooms from a settlement farm, get food for your time
    CRAFT = "CRAFT"  # Invent a new item
    THINK = "THINK"  # Spend the day thinking
    COMPOSE = "COMPOSE"  # Make some music


ACTION_DESCRIPTIONS = {ActionType.REST: "Rest to recover energy",
                       ActionType.WORK: "Work at a low-pay settlement-provided job, get few credits for your time",
                       ActionType.BUY: "Purchase from a goods listing.",
                       ActionType.SELL: "Offer a goods for sale as a new listing.",
                       ActionType.HARVEST: "Harvest shrooms from a settlement farm, you get food for your time and eat a bit while working",
                       ActionType.CRAFT: "Invent an item which could improve your conditions or be sold for credits.",
                       ActionType.THINK: "Spend the day creatively thinking about inventions, culture, philosophy, "
                                         "etc. PUT THOSE THOUGHTS IN extras[\"thoughts\"] ",
                       ActionType.COMPOSE: "Be creative and make a new song to improve the vibe or express your feelings"
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
    actions: List[tuple["Agent", ActionType]]
    interactions: List[str]
    """The actions taken by agents this turn."""


class NarrativeResponse(BaseModel):
    """Structured response for narrative event generation"""

    title: str = Field(
        description="A catchy, thematic title that captures the core economic tension or relationship",
    )

    content: str = Field(
        description="A narrative description of the day's events in 3-4 paragraph",
    )


class AgentActionResponse(BaseModel):
    """Structured response for agent action generation"""

    model_config = ConfigDict(extra='allow')

    reasoning: Optional[str] = Field(
        default=None,
        description="Your short step-by-step reasoning for choosing this Action Type. "
                    "You must talk first person as the agent, don't break character, don't mention validation. "
                    "MAX 20 words. Use abbrevs and Mars 2993-setting appropriate urban slang. "
                    "Keep it SUPER SHORT and concise. e.g \"I'm low on food, gotta harvest some shrooms 2day\""
    )

    type: ActionType = Field(
        description=f"The type of action the agent will take. Must be one of {[a.value for a in ActionType]}"
    )

    extras: Dict[str, Any] = Field(description="Extra information specific to the action type", default_factory=dict)

    @model_validator(mode="after")
    def default_action_extras(cls, model):
        """Provide default extras based on action type"""
        if model.type == ActionType.CRAFT:
            if "goodType" not in model.extras:
                model.extras["goodType"] = random.choice([gt for gt in GoodType])
            if "materials" not in model.extras or model.extras["materials"] < 0:
                model.extras["materials"] = int(random.uniform(1, 100))
            if "name" not in model.extras:
                prefixes = ["Luxury", "Basic", "Compact", "Advanced", "Prototype", "Vintage", "Custom", "Portable", "Premium"]
                suffixes = ["Enhancer", "Device", "Module", "System", "Unit", "Tool", "Interface", "Catalyst", "Processor"]
                good_type = model.extras["goodType"].lower().capitalize()
                model.extras["name"] = f"{random.choice(prefixes)} {good_type} {random.choice(suffixes)}"
        elif model.type == ActionType.THINK:
            if "thoughts" not in model.extras and "thinking" not in model.extras:
                model.extras["thoughts"] = "I should think more clearly about my situation and plan ahead."
        elif model.type == ActionType.COMPOSE:
            if "title" not in model.extras:
                model.extras["title"] = "Untitled Mars Melody"
            if "genre" not in model.extras:
                model.extras["genre"] = "Mars Ambient"
            if "bpm" not in model.extras:
                model.extras["bpm"] = random.randint(60, 180)
            if "tags" not in model.extras:
                model.extras["tags"] = ["mars", "electronic", "ambient"]
        return model


class DailySummaryResponse(BaseModel):
    """Structured response for daily simulation summary"""

    title: str = Field(
        description="A catchy title for today's events. REQUIRED. MAXIMUM 8 WORDS"
    )

    content: str = Field(
        description="A narrative description of the day's events in the Mars settlement. REQUIRED."
    )


class ActionLog(BaseModel):
    action: AgentActionResponse
    agent: "Agent"
    day: int


class Song(BaseModel):
    title: str
    genre: str = "Electronica"
    bpm: int = Field(default=113)
    tags: List[str] = []
    description: Optional[str] = None

    model_config = ConfigDict(extra='allow')

    def __str__(self) -> str:
        description = ""
        if self.description:
            description = f" - {self.description}"
        tag_str = ""
        if self.tags:
            tag_str = f" [{', '.join(self.tags)}]"
        return f"'{self.title}' ({self.genre}, {self.bpm} BPM){tag_str}{description}"


class SongEntry(BaseModel):
    agent: "Agent"
    song: Song
    day: int


class SongBook(BaseModel):
    history_data: Dict[int, List[SongEntry]] = Field(default_factory=lambda: {})
    genres: Set[str] = Field(default_factory=set)

    @property
    def history(self):
        return self.history_data

    def day(self, day: int) -> List[SongEntry]:
        return self.history_data.get(day, [])

    def add_song(self, composer: "Agent", song: Song, day: int):
        if day not in self.history_data:
            self.history_data[day] = []
        entry = SongEntry(agent=composer, song=song, day=day)
        self.history_data[day].append(entry)
        self.genres.add(song.genre)

    def __len__(self):
        return sum(len(entries) for entries in self.history_data.values())


class SimulationState(BaseModel):
    """State of the simulation"""
    market: GlobalMarket = Field(default_factory=GlobalMarket)
    agents: List["Agent"] = Field(default_factory=list)
    day: int = 1
    dead_agents: List["Agent"] = Field(default_factory=list)
    actions: List[ActionLog] = Field(default_factory=list)
    # DefaultDicts would have been nicer, but using dict with default factory instead
    inventions: Dict[int, List[tuple["Agent", Good]]] = Field(default_factory=lambda: defaultdict(list))
    ideas: Dict[int, List[tuple["Agent", str]]] = Field(default_factory=lambda: defaultdict(list))
    songs: SongBook = Field(default_factory=SongBook)

    def add_action(self, agent: "Agent", action: AgentActionResponse) -> None:
        self.actions.append(ActionLog(agent=agent, action=action, day=self.day))

    @property
    def today_actions(self) -> List[ActionLog]:
        return [a for a in self.actions if a.day == self.day]

    def count_inventions(self, on_day: Optional[int] = 0) -> int:
        """Count the total number of inventions, or on a specific day if specified"""
        if on_day > 0:
            return len(self.inventions.get(on_day, []))
        return sum(len(day_inventions) for day_inventions in self.inventions.values())

    @model_validator(mode='after')
    def ensure_defaultdicts(self) -> 'SimulationState':
        """Ensure inventions and ideas are defaultdicts"""
        self.inventions = defaultdict(list, self.inventions)
        self.ideas = defaultdict(list, self.ideas)
        return self


class History(BaseModel):
    steps: List[SimulationState] = Field(default_factory=list)

    def add(self, step: SimulationState):
        self.steps.append(step) 