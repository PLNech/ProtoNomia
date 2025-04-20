"""
Pydantic models for structured LLM responses in ProtoNomia.
These models define the structure that LLMs should return when generating narrative content.
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class NarrativeResponse(BaseModel):
    """Base model for narrative responses from LLMs"""
    title: str = Field(
        description="A brief, engaging title for the narrative event",
        examples=["Tense Ultimatum Negotiation in Mars Dome"]
    )
    description: str = Field(
        description="A detailed description of what happened during the event",
        examples=["Alice offered Bob 30 credits out of a 100 credit pot. After careful consideration, Bob accepted the offer, though clearly dissatisfied with the terms."]
    )
    tags: List[str] = Field(
        description="A list of tags categorizing the event",
        examples=[["ultimatum", "negotiation", "economic_exchange"]]
    )


class DailySummaryResponse(BaseModel):
    """Model for daily summary responses from LLMs"""
    summary: str = Field(
        description="A markdown-formatted summary of the day's events on Mars",
        examples=["# Day 5 on Mars\n\nThe red dust swirled outside the habitats as colonists engaged in various economic activities...\n\n## Notable Events\n\n### Tense Negotiation at Olympus Market\n\nTwo colonists engaged in a heated bargaining session..."]
    )


class AgentActionResponse(BaseModel):
    """Model for agent action decisions from LLMs"""
    type: str = Field(
        description="The type of action the agent has decided to take",
        examples=["OFFER", "NEGOTIATE", "ACCEPT", "REJECT", "WORK", "REST", "BUY", "SEARCH_JOB"]
    )
    extra: Dict[str, Any] = Field(
        description="Additional details specific to the action type",
        examples=[
            {"what": "10 credits", "against_what": "5 digital_goods", "to_agent_id": "agent_54321"},
            {"offer_id": "offer_12345", "message": "I would like to counter with a better offer."},
            {"offer_id": "offer_12345"},
            {"job_id": "job_12345"},
            {"desired_item": "item_12345"},
            {"reason": "Need to recover energy"}
        ]
    )
    reasoning: Optional[str] = Field(
        description="The agent's reasoning for choosing this action based on their personality and context",
        examples=[
            "As a highly cooperative agent, I've decided to make a fair offer to build trust with my neighbor.",
            "Given my high risk tolerance and the available resources, buying this item is a strategic investment.",
            "With my fairness preference, I can't accept such an imbalanced offer and must reject it."
        ]
    ) 