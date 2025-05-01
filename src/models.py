import enum
import hashlib
import logging
import uuid
from copy import deepcopy
from enum import Enum
from typing import List, Dict, Optional, Any

from pydantic import BaseModel, Field, field_validator, ConfigDict, model_validator

from src.generators import generate_thoughts

# noinspection PyDataclass
# The above error seems a false-positive
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


# Initialize a global counter for agent IDs
agent_counter = 0


def agent_id_factory() -> str:
    """Generate a simple ID for an agent"""
    global agent_counter
    agent_counter += 1
    return f"agent_{agent_counter}"


class AgentPersonality(BaseModel):
    text: str  # TODO: Could be developed into e.g. OCEAN model
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
    goods: list[Good] = Field(default_factory=list)

    history: list[tuple[float, AgentNeeds, list[Good], "AgentActionResponse"]] = Field(default_factory=list)
    memory: int = 5

    def record(self, action: "AgentActionResponse"):
        self.history.append((deepcopy(self.credits), deepcopy(self.needs), deepcopy(self.goods), action))


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
                    "Keep it SUPER SHORT and concise. e.g \"I'm low on food, gotta harvest some shrooms 2day\""
    )

    type: ActionType = Field(
        description=f"The type of action the agent will take. Must be one of {[a.value for a in ActionType]}"
    )

    extras: Dict[str, Any] = Field(description="Extra information specific to the action type", default_factory=dict)

    @model_validator(mode="after")
    def default_action_extras(cls, model):
        # Normalize thoughts and default to cached thoughts otherwise
        thoughts = model.extras.get("thoughts", model.extras.get("thinking", ""))
        if model.type == ActionType.THINK:
            if thoughts and thoughts.strip() != "":
                # print(f"Observed agent thinking: {thoughts}")
                pass
            else:
                # print(f"Observed no thinking... (extras={model.extras})", end="")
                thoughts = generate_thoughts()
                model.extras["thoughts"] = thoughts
                model.extras["theme"] = "cached"
                # print(f"default thoughts now: {thoughts}")

        # Normalize good types/materials, with default to random type
        elif model.type == ActionType.CRAFT:
            existing_type = model.extras.get("goodType", model.extras.get("good_type"))
            if existing_type:
                if GoodType.is_valid(existing_type):
                    model.extras["goodType"] = existing_type
                else:
                    model.extras["goodType"] = GoodType.random()
                    logger.error(
                        f"Invalid good type: {existing_type}. Defaulting to random={model.extras.get('goodType')}.")
            else:
                model.extras["goodType"] = GoodType.random()
            if hasattr(model.extras, "good_type"):
                del model.extras["good_type"]

            existing_materials = model.extras.get("materials", model.extras.get("materials"))
            if existing_materials:
                model.extras["materials"] = existing_materials
            else:
                model.extras["materials"] = 0

        elif model.type == ActionType.SELL:
            existing_price = model.extras.get("price")
            if not existing_price:
                model.extras["price"] = 100  # Default price

        return model


class DailySummaryResponse(BaseModel):
    """Structured response for daily simulation summary"""

    title: str = Field(
        description="A catchy title for today's events. REQUIRED. MAXIMUM 8 WORDS"
    )

    content: str = Field(
        description="A narrative summary of the day's events in the settlement. "
                    "You can use light markdown highlighting in bold/italics/inline code. "
                    "REQUIRED. MIN 10 WORDS MAX 30."
    )


class ActionLog(BaseModel):
    action: AgentActionResponse
    agent: Agent
    day: int


class Song(BaseModel):
    title: str
    genre: str = "Electronica"
    bpm: int = 113
    tags: list[str] = []
    description: Optional[str] = None

    def __str__(self) -> str:
        return f"{self.title} ({self.genre}@{self.bpm}BPM) - {'[' + ', '.join(self.tags) + ']' if len(self.tags) else ''}"


class SongEntry(BaseModel):
    agent: Agent
    song: Song


class SongBook(BaseModel):
    _history: Dict[int, list[SongEntry]] = {}  # day to song inventions
    genres: set[str] = set()

    @property
    def history(self):
        return self._history.copy()  # Read

    def day(self, day: int) -> List[SongEntry]:
        return self._history.get(day)

    def recompute_genres(self):
        all_genres = [entry.song.genre for day in self.history.values() for entry in day]
        self.genres = set(sorted(all_genres, key=lambda x: str(x)))

    def add_song(self, composer: Agent, song: Song, day: int):
        if day not in self._history:
            self.history[day] = []
        self._history[day].append(SongEntry(agent=composer, song=song))
        self.recompute_genres()


class SimulationState(BaseModel):
    """State of the simulation"""
    market: GlobalMarket = Field(default_factory=GlobalMarket)
    agents: list[Agent] = Field(default_factory=list)
    day: int = 0
    dead_agents: list[Agent] = Field(default_factory=list)
    actions: list[ActionLog] = Field(default_factory=list)
    # TODO: DefaultDicts would have been nicer, but I didn't manage to make them work with BaseModel...
    inventions: dict[int, list[tuple[Agent, Good]]] = Field(default_factory=dict)
    ideas: dict[int, list[tuple[Agent, str]]] = Field(default_factory=dict)
    songs: SongBook = SongBook()

    def add_action(self, agent: Agent, action: AgentActionResponse) -> None:
        self.actions.append(ActionLog(action=action, agent=agent, day=self.day))

    @property
    def today_actions(self) -> list[ActionLog]:
        return [a for a in self.actions if a.day is self.day]

    def count_inventions(self, on_day: Optional[int] = 0) -> int:
        if on_day:
            only_day = self.inventions[on_day]
            return len(set([g for (_, g) in only_day]))
        else:
            return len(set([g for inventions in self.inventions.values() for (_, g) in inventions]))


class History(BaseModel):
    steps: List[SimulationState] = Field(default_factory=list)

    def add(self, step: SimulationState):
        self.steps.append(deepcopy(step))


if __name__ == '__main__':
    import random

    print(GoodType.random())
