"""
Models for LLM responses specifically for Narrator functionality.
"""
from typing import List, Optional
from pydantic import BaseModel, Field


class NarrativeResponse(BaseModel):
    """Structured response for narrative event generation"""

    title: str = Field(
        description="A catchy, thematic title that captures the core economic tension or relationship",
        max_length=50,
    )

    description: str = Field(
        description="A detailed scene with dialogue showing this interaction through character actions and reactions, "
                    "including environmental details that ground this exchange in the Martian setting",
        max_length=500
    )


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