import time
import uuid
from datetime import datetime
from enum import Enum
from typing import List, Dict, Optional, Literal, Any

from pydantic import BaseModel, Field, validator


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


class ActionType(str, Enum):
    """Types of actions and interactions an agent can take in the Mars economy"""
    # Basic individual actions
    REST = "REST"                     # Rest to recover energy
    WORK = "WORK"                     # Work at a job
    MOVE = "MOVE"                     # Move to a new location

    # Market-related actions
    HIRE = "HIRE"                     # Create a job listing
    FIRE = "FIRE"                     # Fire an employee
    APPLY = "APPLY"                   # Apply for a job listing
    LIST_GOODS = "LIST_GOODS"         # Create a goods listing (offer or request)
    BUY = "BUY"                       # Purchase from a goods listing.



class OfferData(BaseModel):
    """Data for an offer action"""
    target_agent_id: str = Field(..., description="ID of the agent receiving the offer")
    offer_resource_type: str = Field(..., description="Type of resource being offered")
    offer_amount: float = Field(..., description="Amount of resource being offered")
    request_resource_type: str = Field(..., description="Type of resource being requested")
    request_amount: float = Field(..., description="Amount of resource being requested")
    message: Optional[str] = Field(None, description="Optional message to accompany the offer")


class NegotiateData(BaseModel):
    """Data for a negotiate action"""
    offer_id: str = Field(..., description="ID of the offer being negotiated")
    counter_offer_resource_type: Optional[str] = Field(None, description="New type of resource being offered")
    counter_offer_amount: Optional[float] = Field(None, description="New amount of resource being offered")
    counter_request_resource_type: Optional[str] = Field(None, description="New type of resource being requested")
    counter_request_amount: Optional[float] = Field(None, description="New amount of resource being requested")
    message: str = Field(..., description="Message explaining the negotiation")


class AcceptData(BaseModel):
    """Data for an accept action"""
    offer_id: str = Field(..., description="ID of the offer being accepted")
    message: Optional[str] = Field(None, description="Optional message to accompany the acceptance")


class RejectData(BaseModel):
    """Data for a reject action"""
    offer_id: str = Field(..., description="ID of the offer being rejected")
    reason: Optional[str] = Field(None, description="Optional reason for rejection")


class WorkData(BaseModel):
    """Data for a work action"""
    job_id: str = Field(..., description="ID of the job to work on")
    effort_level: float = Field(1.0, ge=0.0, le=1.0, description="Level of effort to put into the work (0.0-1.0)")


class BuyData(BaseModel):
    """Data for a buy action"""
    item_type: str = Field(..., description="Type of item to buy")
    quantity: float = Field(1.0, gt=0.0, description="Quantity to buy")
    max_price: Optional[float] = Field(None, description="Maximum price willing to pay per unit")
    seller_id: Optional[str] = Field(None, description="Specific seller to buy from (optional)")


class SellData(BaseModel):
    """Data for a sell action"""
    item_type: str = Field(..., description="Type of item to sell")
    quantity: float = Field(1.0, gt=0.0, description="Quantity to sell")
    min_price: float = Field(..., gt=0.0, description="Minimum price willing to accept per unit")
    buyer_id: Optional[str] = Field(None, description="Specific buyer to sell to (optional)")


class MoveData(BaseModel):
    """Data for a move action"""
    destination: str = Field(..., description="Name of the location to move to")


class LearnData(BaseModel):
    """Data for a learn action"""
    skill_name: str = Field(..., description="Name of the skill to learn or improve")


class SocializeData(BaseModel):
    """Data for a socialize action"""
    target_agent_id: str = Field(..., description="ID of the agent to socialize with")
    interaction_type: str = Field(..., description="Type of social interaction")


class InvestData(BaseModel):
    """Data for an invest action"""
    project_id: str = Field(..., description="ID of the project to invest in")
    amount: float = Field(..., gt=0.0, description="Amount to invest")


class DonateData(BaseModel):
    """Data for a donate action"""
    recipient_id: str = Field(..., description="ID of the recipient (agent or public good)")
    resource_type: str = Field(..., description="Type of resource being donated")
    amount: float = Field(..., gt=0.0, description="Amount to donate")


class ProduceData(BaseModel):
    """Data for a produce action"""
    product_type: str = Field(..., description="Type of product to produce")
    quantity: float = Field(1.0, gt=0.0, description="Quantity to produce")


class ConsumeData(BaseModel):
    """Data for a consume action"""
    item_type: str = Field(..., description="Type of item to consume")
    quantity: float = Field(1.0, gt=0.0, description="Quantity to consume")


class StealData(BaseModel):
    """Data for a steal action"""
    target_agent_id: str = Field(..., description="ID of the agent to steal from")
    resource_type: str = Field(..., description="Type of resource to steal")
    amount: float = Field(..., gt=0.0, description="Amount to attempt to steal")


class SabotageData(BaseModel):
    """Data for a sabotage action"""
    target_id: str = Field(..., description="ID of the agent or project to sabotage")
    sabotage_type: str = Field(..., description="Type of sabotage")
    intensity: float = Field(0.5, ge=0.0, le=1.0, description="Intensity of the sabotage attempt (0.0-1.0)")


class FormCoalitionData(BaseModel):
    """Data for a form coalition action"""
    target_agent_ids: List[str] = Field(..., description="IDs of the agents to form a coalition with")
    purpose: str = Field(..., description="Purpose of the coalition")
    terms: Dict[str, Any] = Field(..., description="Terms of the coalition")


class OfferAction(BaseModel):
    """Details for an OFFER action"""
    what: str                         # What is being offered
    against_what: str                 # What is expected in return
    to_agent_id: Optional[str] = None # Who the offer is directed to


class NegotiateAction(BaseModel):
    """Details for a NEGOTIATE action"""
    offer_id: str                     # ID of the offer to negotiate
    message: str                      # Negotiation message


class AcceptRejectAction(BaseModel):
    """Details for ACCEPT or REJECT actions"""
    offer_id: str                     # ID of the offer to accept/reject


class WorkAction(BaseModel):
    """Details for a WORK action"""
    job_id: str                       # ID of the job to work on


class BuyAction(BaseModel):
    """Details for a BUY action"""
    desired_item: str                 # Item to purchase


class SearchJobAction(BaseModel):
    """Details for a SEARCH_JOB action"""
    # No additional fields needed, just a placeholder
    pass


class RestAction(BaseModel):
    """Details for a REST action"""
    # No additional fields needed, just a placeholder
    pass


class LLMAgentActionResponse(BaseModel):
    """Model for structured output from LLM agent responses"""
    type: ActionType
    extra: Dict[str, Any] = Field(default_factory=dict)


class AgentDecisionContext(BaseModel):
    """Context for agent decision making"""
    turn: int                         # Current turn
    max_turns: int                    # Maximum number of turns
    neighbors: List[str]              # Neighbor agent IDs
    pending_offers: List[Dict]        # Pending offers for the agent
    jobs_available: List[Dict]        # Available jobs
    items_for_sale: List[Dict]        # Items for sale
    recent_interactions: List[Dict]   # Recent interactions with other agents
    goods_listings: List[Dict] = Field(default_factory=list)  # Goods market listings
    job_listings: List[Dict] = Field(default_factory=list)    # Job market listings
    market_summary: Optional[Dict] = None                     # Summary of market trends


class AgentDecision(BaseModel):
    """Decision made by an agent via LLM"""
    type: ActionType = Field(..., description="Type of action to take")
    extra: Dict[str, Any] = Field(default_factory=dict, description="Additional data for the action")
    reasoning: Optional[str] = Field(None, description="Reasoning behind the decision")


class AgentNeighbor(BaseModel):
    """Information about a neighboring agent"""
    id: str = Field(..., description="ID of the neighbor")
    name: str = Field(..., description="Name of the neighbor")
    faction: str = Field(..., description="Faction the neighbor belongs to")
    relationship: float = Field(..., description="Relationship score with this neighbor (-1.0 to 1.0)")
    recent_interactions: List[str] = Field(default_factory=list, description="Recent interactions with this neighbor")


class Offer(BaseModel):
    """An offer in the system"""
    id: str = Field(..., description="ID of the offer")
    from_agent_id: str = Field(..., description="ID of the agent making the offer")
    from_agent_name: str = Field(..., description="Name of the agent making the offer")
    to_agent_id: str = Field(..., description="ID of the agent receiving the offer")
    offer_resource_type: str = Field(..., description="Type of resource being offered")
    offer_amount: float = Field(..., description="Amount of resource being offered")
    request_resource_type: str = Field(..., description="Type of resource being requested")
    request_amount: float = Field(..., description="Amount of resource being requested")
    message: Optional[str] = Field(None, description="Message accompanying the offer")
    created_at: str = Field(..., description="When the offer was created")


class Job(BaseModel):
    """A job in the system"""
    id: str = Field(..., description="ID of the job")
    title: str = Field(..., description="Title of the job")
    employer_id: str = Field(..., description="ID of the employer")
    employer_name: str = Field(..., description="Name of the employer")
    salary: float = Field(..., description="Salary per work session")
    required_skills: List[str] = Field(default_factory=list, description="Skills required for the job")


class AgentMemoryEntry(BaseModel):
    """An entry in the agent's memory"""
    timestamp: str = Field(..., description="When the memory was created")
    content: str = Field(..., description="Content of the memory")
    importance: float = Field(..., description="Importance of the memory (0.0-1.0)")


class MarketItem(BaseModel):
    """An item available in the market"""
    item_type: str = Field(..., description="Type of item")
    avg_price: float = Field(..., description="Average market price")
    availability: float = Field(..., description="Availability (0.0-1.0)")


class AgentState(BaseModel):
    """Current state of an agent to be provided to the LLM"""
    agent_id: str = Field(..., description="ID of the agent")
    name: str = Field(..., description="Name of the agent")
    faction: str = Field(..., description="Faction the agent belongs to")
    age_days: int = Field(..., description="Age in days")

    # Resources and needs
    resources: Dict[str, float] = Field(..., description="Current resources (type -> amount)")
    needs: Dict[str, float] = Field(..., description="Current needs (type -> level, 0.0-1.0)")

    # Skills and jobs
    skills: Dict[str, float] = Field(..., description="Skills (name -> level, 0.0-1.0)")
    current_job: Optional[Job] = Field(None, description="Current job, if any")

    # Social context
    location: str = Field(..., description="Current location")
    neighbors: List[AgentNeighbor] = Field(..., description="Neighboring agents")

    # Opportunities
    available_jobs: List[Job] = Field(default_factory=list, description="Available jobs")
    incoming_offers: List[Offer] = Field(default_factory=list, description="Offers made to this agent")
    outgoing_offers: List[Offer] = Field(default_factory=list, description="Offers made by this agent")

    # Market information
    market_items: List[MarketItem] = Field(default_factory=list, description="Items available in the market")

    # Memory and context
    memory: List[AgentMemoryEntry] = Field(default_factory=list, description="Agent's memory entries")
    personality: Dict[str, float] = Field(..., description="Personality traits (trait -> level, 0.0-1.0)")

    # Simulation metadata
    current_turn: int = Field(..., description="Current turn in the simulation")
    max_turns: int = Field(..., description="Maximum number of turns")
    global_economic_indicators: Dict[str, float] = Field(default_factory=dict, description="Global economic indicators")


class HireAction(BaseModel):
    """Details for a HIRE action"""
    job_type: str                     # Type of job being offered
    salary_per_turn: float            # Salary per turn
    requirements: str                 # Requirements for the job
    max_employees: int = 1            # Maximum number of employees for this job
    description: Optional[str] = None # Description of the job


class FireAction(BaseModel):
    """Details for a FIRE action"""
    employee_id: str                  # ID of the employee to fire
    job_id: str                       # ID of the job listing


class ApplyAction(BaseModel):
    """Details for an APPLY action"""
    listing_id: str                   # ID of the listing to apply to


class ListGoodsAction(BaseModel):
    """Details for a LIST_GOODS action"""
    is_offer: bool                    # True for offer, False for request
    resource_type: str                # Type of resource being traded
    amount: float                     # Amount (positive for offer, negative for request)
    price_per_unit: float             # Price per unit
    description: Optional[str] = None # Description of the listing


class RetractAction(BaseModel):
    """Details for a RETRACT action"""
    listing_id: str                   # ID of the listing to retract


class PurchaseAction(BaseModel):
    """Details for a PURCHASE action"""
    listing_id: str                   # ID of the listing to purchase from
    amount: float                     # Amount to purchase


class AgentAction(BaseModel):
    """Represents an action taken by an agent"""
    type: ActionType
    agent_id: str
    turn: int
    timestamp: float = Field(default_factory=time.time)
    extra: Optional[Dict[str, Any]] = None

    def __str__(self):
        return f"{self.agent_id} action at turn {self.turn}: {self.type} - extra={self.extra}"

    def __repr__(self):
        return f"ACTION({self.agent_id}, {self.type}, {self.extra})"

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

class InteractionRole(str, Enum):
    """Roles agents can play in economic interactions
    """
    
    INITIATOR = "initiator"         # Agent who started the interaction
    RESPONDER = "responder"         # Agent who responds to an initiated interaction

class InteractionStrategy(BaseModel):
    """Strategy used by an agent in an interaction"""
    strategy_type: str  # e.g., "tit_for_tat", "always_defect", "fair_split"
    parameters: Dict[str, Any] = Field(default_factory=dict)  # Strategy-specific parameters

class InteractionOutcome(BaseModel):
    """Result of an interaction for a specific agent"""
    interaction_id: str
    agent: Agent  # Direct reference to the agent instead of just ID
    role: InteractionRole
    resources_before: List[ResourceBalance]
    resources_after: List[ResourceBalance]
    utility_change: float
    strategy_used: Optional[InteractionStrategy] = None
    
class EconomicInteraction(BaseModel):
    """Economic interaction between agents"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    interaction_type: ActionType
    participants: Dict[Agent, InteractionRole]  # Full Agent object -> Role mapping
    start_time: datetime = Field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    is_complete: bool = False
    parameters: Dict[str, Any] = Field(default_factory=dict)  # Interaction-specific parameters
    outcomes: List[InteractionOutcome] = Field(default_factory=list)
    narrative_significance: float = 0.0  # How important is this for storytelling
    
    class Config:
        arbitrary_types_allowed = True  # Allow non-serializable types like direct Agent references

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
    enabled_interaction_types: List[ActionType] = Field(default_factory=list)
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

