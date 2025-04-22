"""
Tests for the narrator module, which generates narrative events from economic interactions.
"""
import pytest
from datetime import datetime

from models.base import (
    Agent, AgentType, AgentFaction, AgentPersonality, ResourceBalance, ResourceType,
    EconomicInteraction, InteractionRole, NarrativeEvent, ActionType
)
from narrative.narrator import Narrator

@pytest.fixture
def test_agents():
    """Create test agents for the narrator tests"""
    employer = Agent(
        id="employer_1",
        name="Employer Corp",
        agent_type=AgentType.INDIVIDUAL,
        faction=AgentFaction.MARS_NATIVE,
        personality=AgentPersonality(
            cooperativeness=0.6,
            risk_tolerance=0.6,
            fairness_preference=0.5,
            altruism=0.4,
            rationality=0.8,
            long_term_orientation=0.7
        ),
        resources=[
            ResourceBalance(
                resource_type=ResourceType.CREDITS,
                amount=1000.0
            )
        ],
        is_alive=True
    )
    
    employee = Agent(
        id="employee_1",
        name="John Worker",
        agent_type=AgentType.INDIVIDUAL,
        faction=AgentFaction.MARS_NATIVE,
        personality=AgentPersonality(
            cooperativeness=0.7,
            risk_tolerance=0.5,
            fairness_preference=0.6,
            altruism=0.5,
            rationality=0.7,
            long_term_orientation=0.6
        ),
        resources=[
            ResourceBalance(
                resource_type=ResourceType.CREDITS,
                amount=500.0
            )
        ],
        is_alive=True
    )
    
    seller = Agent(
        id="seller_1",
        name="Goods Vendor",
        agent_type=AgentType.INDIVIDUAL,
        faction=AgentFaction.INDEPENDENT,
        personality=AgentPersonality(
            cooperativeness=0.5,
            risk_tolerance=0.7,
            fairness_preference=0.6,
            altruism=0.3,
            rationality=0.8,
            long_term_orientation=0.6
        ),
        resources=[
            ResourceBalance(
                resource_type=ResourceType.CREDITS,
                amount=800.0
            ),
            ResourceBalance(
                resource_type=ResourceType.FOOD,
                amount=100.0
            )
        ],
        is_alive=True
    )
    
    return [employer, employee, seller]

@pytest.fixture
def test_interactions(test_agents):
    """Create test interactions for the narrator"""
    # Create a job application interaction
    job_application = EconomicInteraction(
        interaction_type=ActionType.JOB_APPLICATION,
        participants={
            test_agents[0]: InteractionRole.INITIATOR,
            test_agents[1]: InteractionRole.RESPONDER
        },
        parameters={
            "job_type": "Engineer",
            "salary": 120.0,
            "application_successful": True,
            "stage": "complete"
        },
        is_complete=True,
        narrative_significance=0.7
    )
    
    # Create a goods purchase interaction
    goods_purchase = EconomicInteraction(
        interaction_type=ActionType.GOODS_PURCHASE,
        participants={
            test_agents[2]: InteractionRole.INITIATOR,
            test_agents[1]: InteractionRole.RESPONDER
        },
        parameters={
            "resource_type": ResourceType.FOOD,
            "purchase_amount": 5.0,
            "price_per_unit": 10.0,
            "total_price": 50.0,
            "purchase_successful": True,
            "stage": "complete"
        },
        is_complete=True,
        narrative_significance=0.6
    )
    
    return [job_application, goods_purchase]

class TestNarrator:
    """Tests for the Narrator class"""
    
    def test_initialization(self):
        """Test narrator initialization"""
        narrator = Narrator(verbosity=4)
        assert narrator.verbosity == 4
        
        narrator = Narrator(verbosity=10)  # Exceeds max
        assert narrator.verbosity == 5     # Should be capped at 5
        
        narrator = Narrator(verbosity=0)   # Below min
        assert narrator.verbosity == 1     # Should be at least 1
    
    def test_generate_job_application_narrative(self, test_agents, test_interactions):
        """Test generating narrative for a job application interaction"""
        narrator = Narrator(verbosity=3)
        job_interaction = test_interactions[0]
        
        event = narrator.generate_event_from_interaction(job_interaction, test_agents)
        
        # Check event properties
        assert isinstance(event, NarrativeEvent)
        assert "Engineer" in event.title
        assert "hire" in event.title.lower() or "hired" in event.title.lower()
        assert event.agents_involved == [test_agents[0], test_agents[1]]
        assert event.significance == job_interaction.narrative_significance
        assert "job_application" in event.tags
        assert "employment" in event.tags
        assert "success" in event.tags
        assert event.description is not None and len(event.description) > 0
    
    def test_generate_goods_purchase_narrative(self, test_agents, test_interactions):
        """Test generating narrative for a goods purchase interaction"""
        narrator = Narrator(verbosity=3)
        purchase_interaction = test_interactions[1]
        
        event = narrator.generate_event_from_interaction(purchase_interaction, test_agents)
        
        # Check event properties
        assert isinstance(event, NarrativeEvent)
        assert "Purchase" in event.title or "Purchases" in event.title
        assert "food" in event.title.lower()
        assert event.agents_involved == [test_agents[2], test_agents[1]]
        assert event.significance == purchase_interaction.narrative_significance
        assert "goods_purchase" in event.tags
        assert "transaction" in event.tags
        assert "commerce" in event.tags
        assert event.description is not None and len(event.description) > 0
    
    def test_verbosity_levels(self, test_agents, test_interactions):
        """Test different verbosity levels for narrative generation"""
        # Test with minimum verbosity
        narrator_min = Narrator(verbosity=1)
        event_min = narrator_min.generate_event_from_interaction(test_interactions[0], test_agents)
        
        # Test with medium verbosity
        narrator_med = Narrator(verbosity=3)
        event_med = narrator_med.generate_event_from_interaction(test_interactions[0], test_agents)
        
        # Test with maximum verbosity
        narrator_max = Narrator(verbosity=5)
        event_max = narrator_max.generate_event_from_interaction(test_interactions[0], test_agents)
        
        # Descriptions should get progressively longer with higher verbosity
        assert len(event_min.description) < len(event_med.description)
        assert len(event_med.description) < len(event_max.description)
    
    def test_daily_summary(self, test_agents, test_interactions):
        """Test generating a daily summary from narrative events"""
        narrator = Narrator(verbosity=3)
        
        # Generate narrative events from the interactions
        events = [
            narrator.generate_event_from_interaction(interaction, test_agents)
            for interaction in test_interactions
        ]
        
        # Generate daily summary
        summary = narrator.generate_daily_summary(1, events, test_agents)
        
        # Check summary properties
        assert "Day 1" in summary
        assert "Notable Events" in summary
        
        # Check that all event titles are mentioned in the summary
        for event in events:
            assert event.title in summary or event.agents_involved[0].name in summary 