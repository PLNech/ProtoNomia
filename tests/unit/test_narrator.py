import pytest
from datetime import datetime
from typing import Dict, List

from models.base import (
    Agent, AgentType, AgentFaction, AgentPersonality, 
    EconomicInteraction, EconomicInteractionType, InteractionRole,
    NarrativeEvent, NarrativeArc
)

from narrative.narrator import Narrator


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
    
    agent3 = Agent(
        name="MarsTech Corp",
        agent_type=AgentType.CORPORATION,
        faction=AgentFaction.TERRA_CORP,
        personality=AgentPersonality(
            cooperativeness=0.2,
            risk_tolerance=0.7,
            fairness_preference=0.3,
            altruism=0.1,
            rationality=0.9,
            long_term_orientation=0.9
        )
    )
    
    return [agent1, agent2, agent3]


@pytest.fixture
def test_interactions(test_agents):
    """Create test interactions for the narrator"""
    # Create an Ultimatum Game interaction
    ultimatum = EconomicInteraction(
        interaction_type=EconomicInteractionType.ULTIMATUM,
        participants={
            test_agents[0].id: InteractionRole.PROPOSER,
            test_agents[1].id: InteractionRole.RESPONDER
        },
        parameters={
            "total_amount": 100.0,
            "offer_amount": 20.0,
            "currency": "credits"
        },
        is_complete=True
    )
    
    # Create a Trust Game interaction
    trust = EconomicInteraction(
        interaction_type=EconomicInteractionType.TRUST,
        participants={
            test_agents[0].id: InteractionRole.INVESTOR,
            test_agents[2].id: InteractionRole.TRUSTEE
        },
        parameters={
            "investment_amount": 50.0,
            "multiplier": 3.0,
            "return_amount": 0.0,  # No reciprocation
            "currency": "credits"
        },
        is_complete=True
    )
    
    return [ultimatum, trust]


class TestNarrator:
    """Tests for the narrator functionality"""
    
    def test_create_narrator(self):
        """Test that a narrator can be created"""
        narrator = Narrator(verbosity=3)
        assert narrator.verbosity == 3
    
    def test_generate_event_from_interaction(self, test_agents, test_interactions):
        """Test that the narrator can generate events from interactions"""
        narrator = Narrator(verbosity=3)
        
        # Generate a narrative event from an ultimatum game
        ultimatum_event = narrator.generate_event_from_interaction(
            test_interactions[0],
            test_agents
        )
        
        # Verify event properties
        assert isinstance(ultimatum_event, NarrativeEvent)
        assert ultimatum_event.title is not None and len(ultimatum_event.title) > 0
        assert ultimatum_event.description is not None and len(ultimatum_event.description) > 0
        assert len(ultimatum_event.agents_involved) == 2
        assert test_agents[0] in ultimatum_event.agents_involved
        assert test_agents[1] in ultimatum_event.agents_involved
        
        # Generate a narrative event from a trust game
        trust_event = narrator.generate_event_from_interaction(
            test_interactions[1],
            test_agents
        )
        
        # Verify event properties
        assert isinstance(trust_event, NarrativeEvent)
        assert trust_event.title is not None and len(trust_event.title) > 0
        assert trust_event.description is not None and len(trust_event.description) > 0
        assert len(trust_event.agents_involved) == 2
        assert test_agents[0] in trust_event.agents_involved
        assert test_agents[2] in trust_event.agents_involved
        
        # Ensure the descriptions are different
        assert ultimatum_event.description != trust_event.description
    
    def test_create_narrative_arc(self, test_agents, test_interactions):
        """Test that the narrator can create narrative arcs from related events"""
        narrator = Narrator(verbosity=3)
        
        # Generate narrative events
        event1 = narrator.generate_event_from_interaction(test_interactions[0], test_agents)
        event2 = narrator.generate_event_from_interaction(test_interactions[1], test_agents)
        
        # Create a narrative arc
        arc = narrator.create_arc(
            title="Trust Issues",
            description="A series of betrayals between Mars natives and corporate interests",
            events=[event1, event2],
            agents=[test_agents[0], test_agents[1], test_agents[2]]
        )
        
        # Verify arc properties
        assert isinstance(arc, NarrativeArc)
        assert arc.title == "Trust Issues"
        assert len(arc.events) == 2
        assert len(arc.agents_involved) == 3
        assert not arc.is_complete
    
    def test_generate_daily_summary(self, test_agents, test_interactions):
        """Test that the narrator can generate daily summaries"""
        narrator = Narrator(verbosity=3)
        
        # Generate narrative events
        events = [
            narrator.generate_event_from_interaction(test_interactions[0], test_agents),
            narrator.generate_event_from_interaction(test_interactions[1], test_agents)
        ]
        
        # Generate daily summary
        summary = narrator.generate_daily_summary(
            day=5,
            events=events,
            agents=test_agents
        )
        
        # Verify summary
        assert "Day 5" in summary
        assert len(summary) > 100  # Should be reasonably detailed
        assert test_agents[0].name in summary
        assert test_agents[1].name in summary
        assert test_agents[2].name in summary 