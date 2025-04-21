"""
Integration tests for the LLM-based narrator with actual LLM service.
"""
from unittest import TestCase

import pytest
import sys
import os
from datetime import datetime
import json

from settings import DEFAULT_LM

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from narrative.llm_narrator import LLMNarrator
from models.base import (
    Agent, AgentType, AgentFaction, AgentPersonality, 
    EconomicInteraction, EconomicInteractionType, InteractionRole,
    NarrativeEvent
)


@pytest.fixture
def test_agents():
    """Create a set of test agents for the narrator"""
    agent1 = Agent(
        name="Alice Chen",
        agent_type=AgentType.INDIVIDUAL,
        faction=AgentFaction.MARS_NATIVE,
        personality=AgentPersonality(
            cooperativeness=0.8,
            risk_tolerance=0.4,
            fairness_preference=0.9,
            altruism=0.7,
            rationality=0.6,
            long_term_orientation=0.5
        )
    )
    
    agent2 = Agent(
        name="Bob Rodriguez",
        agent_type=AgentType.INDIVIDUAL,
        faction=AgentFaction.INDEPENDENT,
        personality=AgentPersonality(
            cooperativeness=0.3,
            risk_tolerance=0.8,
            fairness_preference=0.4,
            altruism=0.2,
            rationality=0.9,
            long_term_orientation=0.3
        )
    )
    
    return [agent1, agent2]


@pytest.fixture
def test_interaction(test_agents):
    """Create a test ultimatum interaction"""
    return EconomicInteraction(
        interaction_type=EconomicInteractionType.ULTIMATUM,
        participants={
            test_agents[0].id: InteractionRole.PROPOSER,
            test_agents[1].id: InteractionRole.RESPONDER
        },
        parameters={
            "total_amount": 100.0,
            "offer_amount": 30.0,
            "responder_accepts": True,
            "currency": "credits"
        },
        is_complete=True,
        narrative_significance=0.7
    )


@pytest.mark.llm
@pytest.mark.skipif(not os.environ.get("RUN_LLM_TESTS"), reason="LLM tests are disabled. Set RUN_LLM_TESTS=1 to enable.")
class TestLLMNarratorIntegration():
    """
    Integration tests for LLMNarrator with actual LLM service.
    
    These tests require an actual LLM service running.
    """
    
    def test_llm_narrator_connection(self):
        """Test that we can connect to the LLM service"""
        try:
            narrator = LLMNarrator()
            # If we got here without exception, connection was successful
            assert True
        except Exception as e:
            pytest.fail(f"Failed to connect to LLM service: {e}")
    
    def test_generate_event_from_interaction(self, test_agents, test_interaction):
        """Test generating a narrative event from an interaction using LLM"""
        narrator = LLMNarrator()
        
        # Generate a narrative event
        event = narrator.generate_event_from_interaction(test_interaction, test_agents)
        
        # Verify basic properties of the event
        assert event is not None
        assert isinstance(event, NarrativeEvent)
        assert event.title is not None and len(event.title) > 0
        assert event.description is not None and len(event.description) > 0
        assert len(event.agents_involved) == 2
        assert len(event.tags) > 0
        
        # Check for reasonable content
        assert "Alice" in event.description or "Bob" in event.description
        assert "credit" in event.description.lower() or "offer" in event.description.lower()
    
    def test_daily_summary_generation(self, test_agents):
        """Test generating a daily summary using LLM"""
        narrator = LLMNarrator(max_retries=1)
        
        # Create some narrative events
        events = [
            NarrativeEvent(
                timestamp=datetime.now(),
                title="Risky Deal in Olympus Market",
                description="Alice Chen offered Bob Rodriguez 30 credits from a 100 credit pot. Bob accepted the offer despite its unfairness.",
                agents_involved=[agent for agent in test_agents],
                interaction_id="test-interaction-1",
                significance=0.7,
                tags=["ultimatum", "economics", "negotiation"]
            ),
            NarrativeEvent(
                timestamp=datetime.now(),
                title="Resource Shortage Hits Phobos Colony",
                description="A resource shortage has affected the Phobos Colony, leading to increased prices for basic necessities.",
                agents_involved=[test_agents[0]],
                interaction_id="test-interaction-2",
                significance=0.9,
                tags=["crisis", "resources", "economy"]
            )
        ]
        
        # Generate a daily summary
        retries = 5
        any_success = False
        for retry in range(retries):
            try:
                summary = narrator.generate_daily_summary(day=42, events=events, agents=test_agents)

                # Verify basic properties of the summary
                assert summary is not None and len(summary) > 0
                assert "Alice" in summary and "Bob" in summary, "Misses protagonists"
                any_success = True
            except AssertionError as exc:
                print(f"Failed try {retry}: {summary} -> {exc}")
        if not any_success:
            raise AssertionError(f"No success after {retries} retries.")