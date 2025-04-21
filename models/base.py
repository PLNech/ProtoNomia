from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional, Union, Tuple, Set, Literal, Any
from enum import Enum
from datetime import datetime
import uuid

# ========== Resource Models ==========

class ResourceType(str, Enum):
    """Types of resources in the Mars economy"""
    CREDITS = "credits"                      # Universal currency
    DIGITAL_GOODS = "digital_goods"          # Software, AI models, entertainment
    PHYSICAL_GOODS = "physical_goods"        # Manufactured items
    REPUTATION = "reputation"                # Social standing
    INFLUENCE = "influence"                  # Political/organizational power
    KNOWLEDGE = "knowledge"                  # Information and skills
    HEALTH = "health"                        # Physical wellbeing (for individuals)
    OXYGEN = "oxygen"                        # Life support resource
    WATER = "water"                          # Essential Mars resource
    FOOD = "food"                            # Essential Mars resource
    MINERALS = "minerals"                    # Raw materials
    ENERGY = "energy"                        # Power resource

class ResourceBalance(BaseModel):
    """Represents a quantity of a specific resource"""
    resource_type: ResourceType
    amount: float
    last_updated: datetime = Field(default_factory=datetime.now)

# ========== Agent Models ==========

class AgentType(str, Enum):
    """Types of economic agents"""
    INDIVIDUAL = "individual"        # Person
    CORPORATION = "corporation"      # Business entity
    COLLECTIVE = "collective"        # Community group
    GOVERNMENT = "government"        # Governing body
    AI = "ai"                        # Autonomous AI system

class AgentFaction(str, Enum):
    """Political/social factions on Mars"""
    TERRA_CORP = "terra_corporation"   # Earth-based corporate interests
    MARS_NATIVE = "mars_native"        # Born on Mars
    INDEPENDENT = "independent"        # Unaffiliated
    GOVERNMENT = "government"          # Official governance
    UNDERGROUND = "underground"        # Black market/rebellious

class AgentPersonality(BaseModel):
    """Personality traits affecting economic decisions"""
    cooperativeness: float = Field(0.5, ge=0.0, le=1.0)        # Willingness to cooperate
    risk_tolerance: float = Field(0.5, ge=0.0, le=1.0)         # Appetite for risk
    fairness_preference: float = Field(0.5, ge=0.0, le=1.0)    # Desire for equitable outcomes
    altruism: float = Field(0.5, ge=0.0, le=1.0)               # Generosity to others
    rationality: float = Field(0.5, ge=0.0, le=1.0)            # Logical vs. emotional decisions
    long_term_orientation: float = Field(0.5, ge=0.0, le=1.0)  # Future vs. present focus
    
    @validator('*')
    def check_range(cls, v):
        if not 0 <= v <= 1:
            raise ValueError("Personality traits must be between 0 and 1")
        return v

class AgentNeeds(BaseModel):
    """Basic needs that agents try to satisfy"""
    subsistence: float = Field(1.0, ge=0.0, le=1.0)    # Basic survival needs
    security: float = Field(1.0, ge=0.0, le=1.0)       # Safety and stability
    social: float = Field(1.0, ge=0.0, le=1.0)         # Connection with others
    esteem: float = Field(1.0, ge=0.0, le=1.0)         # Respect and recognition
    self_actualization: float = Field(1.0, ge=0.0, le=1.0)  # Fulfillment and growth
    
    @validator('*')
    def check_range(cls, v):
        if not 0 <= v <= 1:
            raise ValueError("Need values must be between 0 and 1")
        return v

agent_counter: int = 0
def agent_id_factory() -> str:
    """Generate a simple ID for an agent"""
    global agent_counter
    agent_counter += 1
    return f"agent_{agent_counter}"

class Agent(BaseModel):
    """Economic agent in the simulation"""
    id: str = Field(default_factory=agent_id_factory)
    name: str
    agent_type: AgentType
    faction: AgentFaction
    age_days: int = 0  # Age in simulation days
    birth_date: datetime = Field(default_factory=datetime.now)
    death_date: Optional[datetime] = None
    is_alive: bool = True
    personality: AgentPersonality
    needs: AgentNeeds = Field(default_factory=AgentNeeds)
    resources: List[ResourceBalance] = Field(default_factory=list)
    relationships: Dict[str, float] = Field(default_factory=dict)  # Agent ID -> relationship score
    skills: Dict[str, float] = Field(default_factory=dict)
    memory: List[str] = Field(default_factory=list)  # IDs of significant events remembered
    location: str = "Mars Central"
    
    def calculate_age(self, current_date: datetime) -> int:
        """Calculate current age in days"""
        if not self.is_alive:
            return (self.death_date - self.birth_date).days
        return (current_date - self.birth_date).days

    def __eq__(self, other: Any) -> bool:
        """Check if two agents are the same"""
        if isinstance(other, Agent):
            return self.id == other.id
        return False
    
    def __str__(self) -> str:
        """String representation of an agent: 
        First a # Personal section: their name, age, alive status and birth date/death date+age or age+location if alive accordingly.
        Then a # Personality section: their core personality traits and needs.
        Then a # Resources section: their current resources and relationships and skills and memory.
        """
        full_str = f"# {self.name}\n ## Personal info\n"
        if self.is_alive:
            full_str += f"{self.age_days} days old, currently in {self.location}"
        else:
            full_str += f" (died {self.death_date} at {self.age_days} days old), buried in {self.location}"
        full_str += f"\n ## Personality\n"
        full_str += f"Cooperativeness: {self.personality.cooperativeness}\n"
        full_str += f"Risk tolerance: {self.personality.risk_tolerance}\n"
        full_str += f"Fairness preference: {self.personality.fairness_preference}\n"
        full_str += f"Altruism: {self.personality.altruism}\n"
        full_str += f"Rationality: {self.personality.rationality}\n"
        full_str += f"Long-term orientation: {self.personality.long_term_orientation}\n"
        full_str += f"\n ## Needs\n"
        full_str += f"Subsistence: {self.needs.subsistence}\n"
        full_str += f"Security: {self.needs.security}\n"
        full_str += f"Social: {self.needs.social}\n"
        full_str += f"Esteem: {self.needs.esteem}\n"
        full_str += f"Self-actualization: {self.needs.self_actualization}\n"
        full_str += f"\n ## Resources\n"
        for resource in self.resources:
            full_str += f"{resource.resource_type}: {resource.amount}\n"
        full_str += f"\n ## Relationships\n"
        for relationship in self.relationships:
            full_str += f"{relationship.agent_id}: {relationship.relationship_score}\n"
        full_str += f"\n ## Skills\n"
        for skill in self.skills:
            full_str += f"{skill.skill_type}: {skill.skill_level}\n"
        return full_str
    
    def __repr__(self) -> str:
        """A shorter unique identifier for an agent."""
        return f"Agent(id={self.id}, name={self.name})"

    def __hash__(self):
        return hash(self.id)
# ========== Economic Interaction Models ==========

class EconomicInteractionType(str, Enum):
    """Types of economic interactions based on game theory"""
    ULTIMATUM = "ultimatum_game"                 # Fairness & bargaining
    DICTATOR = "dictator_game"                   # Pure altruism
    PUBLIC_GOODS = "public_goods_game"           # Collective action
    TRUST = "trust_game"                         # Trust & reciprocity
    COURNOT = "cournot_competition"              # Quantity competition
    BERTRAND = "bertrand_competition"            # Price competition
    DOUBLE_AUCTION = "double_auction"            # Market price discovery
    OLIGOPOLY = "oligopoly_collusion"            # Collusion dynamics
    RENT_SEEKING = "rent_seeking"                # Resource competition
    MATCHING = "matching_market"                 # Two-sided matching
    PRINCIPAL_AGENT = "principal_agent"          # Contract design
    COORDINATION = "coordination_game"           # Coordination problems
    SIGNALING = "signaling_game"                 # Information asymmetry
    BEAUTY_CONTEST = "beauty_contest"            # Higher-order reasoning
    COMMON_POOL = "common_pool_resources"        # Resource management
    AGENT_BASED_MACRO = "agent_based_macro"      # Macroeconomic simulation
    EVOLUTIONARY = "evolutionary_game"           # Strategy evolution
    INSTITUTIONAL = "institutional_design"        # Rule creation
    NETWORK_FORMATION = "network_formation"      # Strategic linking
    SABOTAGE = "sabotage_espionage"              # Competitive disruption

class InteractionRole(str, Enum):
    """Roles agents can play in economic interactions
    
    Simplified to a few generic roles that can be used across different interaction types
    """
    INITIATOR = "initiator"     # Agent who started the interaction
    RESPONDER = "responder"     # Agent who responds to an initiated interaction
    PARTICIPANT = "participant" # Generic participant in multi-agent interactions
    
    # Legacy roles maintained for backward compatibility
    PROPOSER = "proposer"
    INVESTOR = "investor"
    TRUSTEE = "trustee"
    CONTRIBUTOR = "contributor"

class InteractionStrategy(BaseModel):
    """Strategy used by an agent in an interaction"""
    strategy_type: str  # e.g., "tit_for_tat", "always_defect", "fair_split"
    parameters: Dict[str, Any] = Field(default_factory=dict)  # Strategy-specific parameters

class InteractionOutcome(BaseModel):
    """Result of an interaction for a specific agent"""
    interaction_id: str
    agent_id: str
    role: InteractionRole
    resources_before: List[ResourceBalance]
    resources_after: List[ResourceBalance]
    utility_change: float
    strategy_used: Optional[InteractionStrategy] = None
    
class EconomicInteraction(BaseModel):
    """Economic interaction between agents"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    interaction_type: EconomicInteractionType
    participants: Dict[str, InteractionRole]  # Agent ID -> Role
    start_time: datetime = Field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    is_complete: bool = False
    parameters: Dict[str, Any] = Field(default_factory=dict)  # Interaction-specific parameters
    outcomes: List[InteractionOutcome] = Field(default_factory=list)
    narrative_significance: float = 0.0  # How important is this for storytelling

# ========== Narrative Models ==========

class NarrativeEvent(BaseModel):
    """Narratively significant event in the simulation"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.now)
    title: str
    description: str
    agents_involved: List[Agent] = Field(default_factory=list)
    interaction_id: Optional[str] = None  # If related to an interaction
    significance: float = Field(0.5, ge=0.0, le=1.0)  # How important is this event
    tags: List[str] = Field(default_factory=list)
    
class NarrativeArc(BaseModel):
    """Ongoing storyline spanning multiple events"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    events: List[str] = Field(default_factory=list)  # Event IDs in sequence
    agents_involved: List[Agent] = Field(default_factory=list)  # Agent IDs
    start_time: datetime = Field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    is_complete: bool = False
    
# ========== Simulation Models ==========

class SimulationConfig(BaseModel):
    """Configuration for the simulation"""
    name: str = "ProtoNomia"
    seed: Optional[int] = None
    start_date: datetime = Field(default_factory=datetime.now)
    time_scale: float = 1.0  # Simulation speed multiplier
    initial_population: int = 100
    max_population: int = 1000
    resource_scarcity: float = Field(0.5, ge=0.0, le=1.0)
    technological_level: float = Field(0.8, ge=0.0, le=1.0)
    terra_mars_trade_ratio: float = Field(0.6, ge=0.0, le=1.0)
    enabled_interaction_types: List[EconomicInteractionType] = Field(default_factory=list)
    narrative_verbosity: int = Field(3, ge=1, le=5)
    
class SimulationState(BaseModel):
    """Current state of the simulation"""
    config: SimulationConfig
    current_date: datetime
    current_tick: int = 0
    population_size: int
    active_agents: List[str]  # Agent IDs
    deceased_agents: List[str] = Field(default_factory=list)  # Agent IDs
    active_interactions: List[str] = Field(default_factory=list)  # Interaction IDs
    completed_interactions: List[str] = Field(default_factory=list)  # Interaction IDs
    narrative_events: List[str] = Field(default_factory=list)  # Event IDs
    narrative_arcs: List[str] = Field(default_factory=list)  # Arc IDs
    economic_indicators: Dict[str, float] = Field(default_factory=dict)

# ========== Population Control Models ==========
class PopulationEvent(BaseModel):
    """Event related to population changes"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: Literal["birth", "death", "immigration", "emigration"]
    agent_id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    reason: str
    related_agents: List[str] = Field(default_factory=list)  # e.g., parents for birth
    
class PopulationControlParams(BaseModel):
    """Parameters for population control"""
    birth_rate: float = 0.01  # Base probability per agent per day
    death_rate: float = 0.005  # Base probability per agent per day
    immigration_rate: float = 0.002  # New agents per day
    emigration_rate: float = 0.001  # Probability per agent per day
    resource_sensitivity: float = 0.5  # How much resource scarcity affects rates
    max_age_days: int = 36500  # 100 years in days
    
    @validator('birth_rate', 'death_rate', 'immigration_rate', 'emigration_rate')
    def check_rate_range(cls, v):
        if not 0 <= v <= 1:
            raise ValueError("Rates must be between 0 and 1")
        return v