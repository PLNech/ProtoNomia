"""
Structured response models for LLM interactions in ProtoNomia.

This module defines the Pydantic models used for structured outputs from LLM calls.
"""
from typing import List, Optional, Dict, Any, ClassVar
from pydantic import BaseModel, Field, field_validator, model_validator
import re


class NarrativeResponse(BaseModel):
    """Structured response for narrative generation"""
    
    title: str = Field(
        description="A catchy title for the narrative event",
        max_length=100
    )
    
    description: str = Field(
        description="A detailed description of what happened during the interaction",
        max_length=2000
    )
    
    tags: List[str] = Field(
        description="Relevant tags or keywords that categorize this event",
        max_items=10
    )
    
    # Prohibited terms that should not appear in narrative content
    PROHIBITED_TERMS: ClassVar[List[str]] = [
        "offensive", "inappropriate", "harmful", "violent"
    ]
    
    @field_validator('title')
    @classmethod
    def validate_title(cls, v: str) -> str:
        """Validate the title to ensure it doesn't contain prohibited terms and has proper formatting"""
        # Check for prohibited terms
        for term in cls.PROHIBITED_TERMS:
            if term.lower() in v.lower():
                raise ValueError(f"Title contains prohibited term: '{term}'")
        
        # Ensure title uses proper capitalization
        if not v[0].isupper() and len(v) > 0:
            v = v[0].upper() + v[1:]
            
        return v
    
    @field_validator('description')
    @classmethod
    def validate_description(cls, v: str) -> str:
        """Validate the description to ensure content quality"""
        # Check for prohibited terms
        for term in cls.PROHIBITED_TERMS:
            if term.lower() in v.lower():
                raise ValueError(f"Description contains prohibited term: '{term}'")
        
        # Ensure description is not too short
        if len(v.split()) < 10:
            raise ValueError("Description is too short, please provide more details")
            
        return v
    
    @field_validator('tags')
    @classmethod
    def validate_tags(cls, v: List[str]) -> List[str]:
        """Validate the tags to ensure they are properly formatted"""
        # Ensure tags are not empty
        if not v:
            raise ValueError("At least one tag must be provided")
        
        # Convert tags to lowercase and remove duplicates
        clean_tags = list(set([tag.lower() for tag in v]))
        
        # Remove empty tags
        clean_tags = [tag for tag in clean_tags if tag.strip()]
        
        # Ensure at least one tag remains after cleaning
        if not clean_tags:
            raise ValueError("All tags were empty or duplicates")
            
        return clean_tags
    
    @model_validator(mode='after')
    def validate_narrative_coherence(self) -> 'NarrativeResponse':
        """Validate that the title, description, and tags form a coherent narrative"""
        # Check if title is mentioned in description
        title_words = set(re.findall(r'\b\w+\b', self.title.lower()))
        desc_words = set(re.findall(r'\b\w+\b', self.description.lower()))
        
        # At least some words from title should appear in description
        common_words = title_words.intersection(desc_words)
        if len(common_words) < 1 and len(title_words) > 2:
            # Only check if title has more than 2 significant words
            significant_words = [w for w in title_words if len(w) > 3]
            if significant_words and not any(w in desc_words for w in significant_words):
                raise ValueError("Title and description appear to be unrelated")
        
        # Check if tags are relevant to the description
        tag_relevance = sum(1 for tag in self.tags if tag.lower() in self.description.lower())
        if tag_relevance == 0 and len(self.tags) > 1:
            raise ValueError("Tags should be relevant to the description content")
            
        return self


class DailySummaryResponse(BaseModel):
    """Structured response for daily summary generation"""
    
    summary: str = Field(
        description="A detailed daily summary in Markdown format",
        max_length=5000
    )
    
    @field_validator('summary')
    @classmethod
    def validate_summary(cls, v: str) -> str:
        """Validate the summary to ensure it has proper markdown formatting and content"""
        # Check if the summary has markdown headings
        if not re.search(r'#+ ', v):
            raise ValueError("Summary should contain Markdown headings")
        
        # Check if the summary has at least one paragraph
        paragraphs = [p for p in v.split('\n\n') if p.strip()]
        if len(paragraphs) < 2:
            raise ValueError("Summary should contain multiple paragraphs")
        
        # Check if summary has reasonable length
        if len(v.split()) < 50:
            raise ValueError("Summary is too short, please provide more details")
            
        return v


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
    
    # Valid action types
    VALID_ACTION_TYPES: ClassVar[List[str]] = [
        "REST", "OFFER", "NEGOTIATE", "ACCEPT", "REJECT", "WORK", "BUY", "SEARCH_JOB"
    ]
    
    @field_validator('type')
    @classmethod
    def validate_action_type(cls, v: str) -> str:
        """Validate that the action type is one of the allowed values"""
        if v not in cls.VALID_ACTION_TYPES:
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