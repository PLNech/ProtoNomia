"""
Tests for the narrator module, which generates narrative events from economic interactions.
"""
import pytest
from datetime import datetime
from unittest.mock import Mock, patch

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
        interaction_type=ActionType.APPLY,
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
        interaction_type=ActionType.BUY,
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

class MockNarrativeResponse:
    def __init__(self, title, description, tags):
        self.title = title
        self.description = description
        self.tags = tags

class MockSummaryResponse:
    def __init__(self, headline, summary, emerging_trends):
        self.headline = headline
        self.summary = summary
        self.emerging_trends = emerging_trends

class TestNarrator:
    """Tests for the Narrator class"""
    
    @patch('narrative.narrator.OllamaClient')
    def test_initialization(self, mock_ollama):
        """Test narrator initialization"""
        narrator = Narrator(verbosity=4)
        assert narrator.verbosity == 4
        
        narrator = Narrator(verbosity=10)  # Exceeds max
        assert narrator.verbosity == 5     # Should be capped at 5
        
        narrator = Narrator(verbosity=0)   # Below min
        assert narrator.verbosity == 1     # Should be at least 1
    
    @patch('narrative.narrator.OllamaClient')
    def test_generate_job_application_narrative(self, mock_ollama, test_agents, test_interactions):
        """Test generating narrative for a job application interaction"""
        # Set up the mock
        mock_client = Mock()
        mock_client.generate_narrative.return_value = MockNarrativeResponse(
            title="John Worker Hired by Employer Corp as Engineer",
            description="John Worker was hired as an Engineer by Employer Corp with a salary of 120.0 credits per turn.",
            tags=["job_application", "hiring", "employment", "success"]
        )
        mock_ollama.return_value = mock_client
        
        narrator = Narrator(verbosity=3)
        job_interaction = test_interactions[0]
        
        event = narrator.generate_event_from_interaction(job_interaction, test_agents)
        
        # Check event properties
        assert isinstance(event, NarrativeEvent)
        assert "Engineer" in event.title
        assert "hire" in event.title.lower() or "hired" in event.title.lower()
        assert len(event.agents_involved) == 2
        assert event.significance == job_interaction.narrative_significance
        assert "job_application" in event.tags
        assert "employment" in event.tags
        assert "success" in event.tags
        assert event.description is not None and len(event.description) > 0
    
    @patch('narrative.narrator.OllamaClient')
    def test_generate_goods_purchase_narrative(self, mock_ollama, test_agents, test_interactions):
        """Test generating narrative for a goods purchase interaction"""
        # Set up the mock
        mock_client = Mock()
        mock_client.generate_narrative.return_value = MockNarrativeResponse(
            title="John Worker Purchases food from Goods Vendor",
            description="John Worker purchased 5.0 units of food from Goods Vendor for 50.0 credits.",
            tags=["goods_purchase", "transaction", "commerce", "success"]
        )
        mock_ollama.return_value = mock_client
        
        narrator = Narrator(verbosity=3)
        purchase_interaction = test_interactions[1]
        
        event = narrator.generate_event_from_interaction(purchase_interaction, test_agents)
        
        # Check event properties
        assert isinstance(event, NarrativeEvent)
        assert "Purchase" in event.title or "Purchases" in event.title
        assert "food" in event.title.lower()
        assert len(event.agents_involved) == 2
        assert event.significance == purchase_interaction.narrative_significance
        assert "goods_purchase" in event.tags
        assert "transaction" in event.tags
        assert "commerce" in event.tags
        assert event.description is not None and len(event.description) > 0
    
    @patch('narrative.narrator.OllamaClient')
    def test_verbosity_levels(self, mock_ollama, test_agents, test_interactions):
        """Test different verbosity levels for narrative generation"""
        # Set up the mock
        mock_client = Mock()
        mock_client.generate_narrative.return_value = MockNarrativeResponse(
            title="John Worker Hired by Employer Corp as Engineer",
            description="John Worker was hired as an Engineer by Employer Corp with a salary of 120.0 credits per turn.",
            tags=["job_application", "hiring", "employment", "success"]
        )
        mock_ollama.return_value = mock_client
        
        # Test with LLM functionality - we're just checking it doesn't error
        narrator = Narrator(verbosity=3)
        event = narrator.generate_event_from_interaction(test_interactions[0], test_agents)
        
        assert event is not None
        assert isinstance(event, NarrativeEvent)
    
    @patch('narrative.narrator.OllamaClient')
    def test_daily_summary(self, mock_ollama, test_agents, test_interactions):
        """Test generating a daily summary from narrative events"""
        # Set up the mock
        mock_client = Mock()
        mock_client.generate_daily_summary.return_value = MockSummaryResponse(
            headline="Day 1 on Mars: New Beginnings",
            summary="The first day of the Mars colony saw several economic interactions...",
            emerging_trends="Resource scarcity is becoming a concern."
        )
        mock_ollama.return_value = mock_client
        
        narrator = Narrator(verbosity=3)
        
        # Generate events from interactions
        events = []
        for interaction in test_interactions:
            event = NarrativeEvent(
                timestamp=datetime.now(),
                title="Test Event",
                description="Test description",
                agents_involved=test_agents[:2],  # Just use the first two agents
                interaction_id=interaction.id,
                significance=interaction.narrative_significance,
                tags=["test"]
            )
            events.append(event)
        
        # Generate daily summary
        summary = narrator.generate_daily_summary(1, events, test_agents)
        
        # Check summary properties
        assert summary is not None
        assert "Day 1 on Mars: New Beginnings" in summary
        assert "The first day of the Mars colony" in summary
        assert "Resource scarcity" in summary 