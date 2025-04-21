import time
from enum import Enum
from typing import Dict, List, Optional, Any

from pydantic import BaseModel, Field, validator
from models.base import ResourceBalance

class ActionType(str, Enum):
    """Types of actions an agent can take"""
    REST = "REST"                     # Rest to recover energy
    OFFER = "OFFER"                   # Make an offer to another agent
    NEGOTIATE = "NEGOTIATE"           # Negotiate on an existing offer
    ACCEPT = "ACCEPT"                 # Accept an offer
    REJECT = "REJECT"                 # Reject an offer
    SEARCH_JOB = "SEARCH_JOB"         # Look for employment
    WORK = "WORK"                     # Work at a job
    BUY = "BUY"                       # Purchase goods
    SELL = "SELL"  # Sell goods or services
    MOVE = "MOVE"  # Move to a new location
    LEARN = "LEARN"  # Learn a new skill or improve existing ones
    SOCIALIZE = "SOCIALIZE"  # Interact socially with other agents
    RESEARCH = "RESEARCH"  # Research new technologies or information
    INVEST = "INVEST"  # Invest in assets or projects
    DONATE = "DONATE"  # Donate to others or public goods
    PRODUCE = "PRODUCE"  # Produce goods or services
    CONSUME = "CONSUME"  # Consume goods or services
    STEAL = "STEAL"  # Attempt to steal resources (risky)
    SABOTAGE = "SABOTAGE"  # Attempt to sabotage others (risky)
    FORM_COALITION = "FORM_COALITION"  # Form a coalition with other agents

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
    to_agent_id: Optional[str] = None # Target agent (if specific)

class NegotiateAction(BaseModel):
    """Details for a NEGOTIATE action"""
    offer_id: str                     # ID of the offer being negotiated
    message: str                      # Negotiation message/counter-offer

class AcceptRejectAction(BaseModel):
    """Details for ACCEPT or REJECT actions"""
    offer_id: str                     # ID of the offer being accepted/rejected

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
    """Context provided to agent for decision making"""
    turn: int
    max_turns: int
    neighbors: List[str]
    pending_offers: List[Dict[str, Any]]
    jobs_available: List[Dict[str, Any]]
    items_for_sale: List[Dict[str, Any]]
    recent_interactions: List[Dict[str, Any]] = []

class AgentAction(BaseModel):
    """Represents an action taken by an agent"""
    type: ActionType
    agent_id: str
    turn: int
    timestamp: float = Field(default_factory=time.time)
    extra: Optional[Dict[str, Any]] = None
    
    # Action-specific details based on type
    offer_details: Optional[OfferAction] = None
    negotiate_details: Optional[NegotiateAction] = None
    accept_reject_details: Optional[AcceptRejectAction] = None
    work_details: Optional[WorkAction] = None
    buy_details: Optional[BuyAction] = None
    
    def __str__(self):
        return f"{self.agent_id} action at turn {self.turn}: {self.type} - extra={self.extra}"
        
    def __repr__(self):
        return f"ACTION({self.agent_id}, {self.type}, {self.extra})"
    
    @validator('offer_details')
    def validate_offer_details(cls, v, values):
        if values.get('type') == ActionType.OFFER and v is None:
            raise ValueError("Offer details required for OFFER action")
        return v
    
    @validator('negotiate_details')
    def validate_negotiate_details(cls, v, values):
        if values.get('type') == ActionType.NEGOTIATE and v is None:
            raise ValueError("Negotiate details required for NEGOTIATE action")
        return v
    
    @validator('accept_reject_details')
    def validate_accept_reject_details(cls, v, values):
        if values.get('type') in [ActionType.ACCEPT, ActionType.REJECT] and v is None:
            raise ValueError("Accept/Reject details required for ACCEPT or REJECT action")
        return v
    
    @validator('work_details')
    def validate_work_details(cls, v, values):
        if values.get('type') == ActionType.WORK and v is None:
            raise ValueError("Work details required for WORK action")
        return v
    
    @validator('buy_details')
    def validate_buy_details(cls, v, values):
        if values.get('type') == ActionType.BUY and v is None:
            raise ValueError("Buy details required for BUY action")
        return v

# Simplified model for LLM response
class AgentDecision(BaseModel):
    """Decision made by an agent via LLM"""
    type: ActionType = Field(..., description="Type of action to take")
    extra: Dict[str, Any] = Field(default_factory=dict, description="Additional data for the action")
    reasoning: Optional[str] = Field(None, description="Reasoning behind the decision")


# Models for the agent state provided to the LLM
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