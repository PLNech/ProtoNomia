"""
Structured response models for LLM interactions in ProtoNomia.

This module defines the Pydantic models used for structured outputs from LLM calls.
"""
import re
from typing import Dict, Any, ClassVar
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator
from pydantic import model_validator

from models.actions import ActionType


class NarrativeResponse(BaseModel):
    """Structured response for narrative event generation"""

    title: str = Field(
        description="A catchy, thematic title that captures the core economic tension or relationship",
        max_length=100,
    )

    description: str = Field(
        description="A detailed scene with dialogue showing this interaction through character actions and reactions, "
                    "including environmental details that ground this exchange in the Martian setting",
        max_length=2000
    )

    tags: List[str] = Field(
        description="Keywords that categorize this event: one to five from [economics/conflict/collaboration/"
                    "resources/technology/politics/survival/trust/negotiation/faction].",
        min_length=1,
        max_length=5,
    )

    theme: Optional[str] = Field(
        description="The broader theme this event connects to (survival, community, adaptation, etc.)",
        default=None
    )

    setting_details: Optional[List[str]] = Field(
        description="Specific environmental or cultural details of Mars that were incorporated",
        default=None
    )

    @field_validator('description')
    @classmethod
    def validate_description(cls, v: str) -> str:
        """Validate that the description includes dialogue and setting details"""
        # Check for dialogue (quotes)
        if not re.search(r'["\'](.*?)["\']', v):
            print(f"SilentError: Description should include character dialogue in quotes ({v})")
            # raise ValueError("Description should include character dialogue in quotes")
        return v

    @field_validator('tags')
    @classmethod
    def validate_tags(cls, v: List[str]) -> List[str]:
        """Validate that tags are relevant to the Mars economy simulation"""
        valid_categories = [
            'economics', 'trade', 'conflict', 'collaboration', 'resources',
            'technology', 'politics', 'survival', 'trust', 'negotiation',
            'fairness', 'risk', 'innovation', 'community', 'faction'
        ]

        # At least one tag should be from valid categories
        if not any(tag.lower() in valid_categories for tag in v):
            print (f"SilentError: Tags should include at least one category from: {', '.join(valid_categories)}")
            # raise ValueError(f"Tags should include at least one category from: {', '.join(valid_categories)}")

        return v

class DailySummaryResponse(BaseModel):
    """Structured response for daily summary generation"""

    headline: str = Field(
        description="An engaging 5-10 words headline that captures the day's most important theme or development",
        min_length=10,
        max_length=100
    )

    summary: str = Field(
        description="A daily summary of MAX 15-30 words that weaves individual events into a cohesive narrative",
        min_length=40,
        max_length=2000
    )

    emerging_trends: Optional[List[str]] = Field(
        description="0-5 Emerging social, economic, or technological trends in the colony, as list of lowercase strings.",
        default=None,
        max_length=10
    )

    @field_validator('summary')
    @classmethod
    def validate_summary(cls, v: str) -> str:
        """Validate the summary to ensure it has proper content"""
        # Check if the summary has at least two paragraphs
        # paragraphs = [p for p in v.split('\n\n') if p.strip()]
        # if len(paragraphs) < 2:
            # print(f"SilentError: Summary should contain multiple paragraphs ({v})")
            # raise ValueError("Summary should contain multiple paragraphs")

        # Check if summary has reasonable length
        if len(v.split()) < 100:
            print(f"SilentError: Summary is too short, please provide more details ({v})")
            # raise ValueError("Summary is too short, please provide more details")

        return v
    
example_daily_summary_1: DailySummaryResponse = DailySummaryResponse(
    headline="Synthetic Oxygen Scarcity Triggers Paranoid Negotiation Protocol",
    summary="In the sterile corridors, Bob's memory implant flickered with desperation. "
            "Alice, her neural interface humming, negotiated oxygen credits with a mechanical precision that masked "
            "her underlying existential dread. The colony's breath hung in quantum uncertainty—each transaction a potential"
            " betrayal, each molecule of air a currency of survival in this red-dust hallucination we call home.",
    emerging_trends=['resource scarcity', 'neural negotiation', 'survival economics']
)

example_daily_summary_2: DailySummaryResponse = DailySummaryResponse(
    headline="Hallucinatory VR Breakthrough Sparks Capitalist Fever Dream",
    summary="The VR headset materialized—not as technology, but as a collective hallucination. "
            "Inventors and speculators swarmed like digital parasites, their consciousness bleeding "
            "into marketing algorithms. Each pixel promised escape, each refresh rate a new reality construct.\n\n"
            "The entertainment industry mutated overnight, transforming from mere content delivery "
            "to a full-spectrum reality manipulation engine. "
            "Innovation became indistinguishable from mass delusion.",
    emerging_trends=['virtual reality', 'technological mutation', 'consciousness commodification']
)
    

class AgentActionResponse(BaseModel):
    """Structured response for agent action generation"""
    
    type: str = Field(
        description="The type of action the agent will take",
        examples=["REST", "OFFER", "NEGOTIATE", "ACCEPT", "REJECT", "WORK", "BUY", "SEARCH_JOB"]
    )
    
    extra: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Extra information specific to the action type"
    )
    
    reasoning: str = Field(
        description="The reasoning behind the agent's action choice",
        max_length=500
    )
    

    @field_validator('type')
    @classmethod
    def validate_action_type(cls, v: str) -> str:
        """Validate that the action type is one of the allowed values"""
        valid_list = [str(t) for t in ActionType]
        if v not in valid_list:
            raise ValueError(f"Invalid action type: {v}. Must be one of {cls.VALID_ACTION_TYPES}")
        return v
    
    @field_validator('reasoning')
    @classmethod
    def validate_reasoning(cls, v: str) -> str:
        """Validate that the reasoning is meaningful"""
        if len(v.split()) < 5:
            raise ValueError("Reasoning must be more detailed")
        return v
    
    @model_validator(mode='after')
    def validate_action_details(self) -> 'AgentActionResponse':
        """Validate that the action has the required details for its type"""
        if self.type == "OFFER":
            extra = self.extra or {}
            required_fields = ["what", "against_what", "to_agent_id"]
            for field in required_fields:
                if field not in extra:
                    raise ValueError(f"OFFER action requires '{field}' in extra data")
        
        elif self.type in ["NEGOTIATE", "ACCEPT", "REJECT"]:
            extra = self.extra or {}
            if "offer_id" not in extra:
                raise ValueError(f"{self.type} action requires 'offer_id' in extra data")
        
        elif self.type == "WORK":
            extra = self.extra or {}
            if "job_id" not in extra:
                raise ValueError("WORK action requires 'job_id' in extra data")
        
        elif self.type == "BUY":
            extra = self.extra or {}
            if "desired_item" not in extra:
                raise ValueError("BUY action requires 'desired_item' in extra data")
                
        return self


class PersonalityTraitsResponse(BaseModel):
    """Structured response for generating personality traits"""
    
    openness: float = Field(
        description="Openness to experience - high values indicate curiosity and creativity",
        ge=0.0,
        le=1.0
    )
    
    conscientiousness: float = Field(
        description="Conscientiousness - high values indicate organization and dependability",
        ge=0.0,
        le=1.0
    )
    
    extraversion: float = Field(
        description="Extraversion - high values indicate sociability and assertiveness",
        ge=0.0,
        le=1.0
    )
    
    agreeableness: float = Field(
        description="Agreeableness - high values indicate cooperation and compassion",
        ge=0.0,
        le=1.0
    )
    
    neuroticism: float = Field(
        description="Neuroticism - high values indicate emotional instability and anxiety",
        ge=0.0,
        le=1.0
    )
    
    risk_tolerance: float = Field(
        description="Willingness to take risks - high values indicate risk-seeking behavior",
        ge=0.0,
        le=1.0
    )
    
    trust: float = Field(
        description="Tendency to trust others - high values indicate readiness to trust",
        ge=0.0,
        le=1.0
    )
    
    altruism: float = Field(
        description="Concern for others' welfare - high values indicate selflessness",
        ge=0.0,
        le=1.0
    )
    
    @model_validator(mode='after')
    def validate_trait_balance(self) -> 'PersonalityTraitsResponse':
        """Validate that the personality traits are balanced and realistic"""
        # Check if all traits are at extreme values (unlikely for a real personality)
        extreme_traits = sum(1 for value in self.model_dump().values() if value > 0.9 or value < 0.1)
        if extreme_traits > 3:
            raise ValueError("Too many personality traits at extreme values")
            
        return self 