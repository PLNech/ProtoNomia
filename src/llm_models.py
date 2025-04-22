"""
Models for LLM responses specifically for Narrator functionality.
"""
from typing import List, Optional
from pydantic import BaseModel, Field


class NarrativeResponse(BaseModel):
    """Structured response for narrative event generation"""

    title: str = Field(
        description="A catchy, thematic title that captures the core economic tension or relationship. MAX 10 WORDS",
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
        description="A catchy title for the day's events. MAXIMUM 8 WORDS"
    )

    summary: str = Field(
        description="A narrative summary of the day's events in the colony. MIN 10 WORDS MAX 30."
    )



# Example Daily Summaries for LLM guidance
example_daily_summary_1 = DailySummaryResponse(
    title="Dusty Deals and Shroom Dreams",
    summary="Day 3 on Mars brought economic stirrings as colonists began establishing trade. Sarah crafted a makeshift air filter, while Malik harvested the first batch of Martian mushrooms. Despite fatigue, colonists showed remarkable resilience, with jokes about 'getting rich in red dirt' echoing through the habitation units.",
)

example_daily_summary_2 = DailySummaryResponse(
    title="Fungal Fortune, Colonial Crisis",
    summary="Day 7 marked contrasts in the colony's development. The mushroom trade flourished with Dave's discovery of a premium growth technique, while resource scarcity led to the first heated market disputes. Meanwhile, Elena's critical rest levels resulted in the colony's first medical emergency, prompting discussions about work-life balance in the harsh Martian environment.",
)