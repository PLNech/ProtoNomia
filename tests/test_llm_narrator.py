"""
Tests for the LLM-based narrator functionality.
"""
import pytest
from unittest.mock import patch, MagicMock
import json
from datetime import datetime

from models.base import (
    Agent, AgentType, AgentFaction, AgentPersonality, 
    EconomicInteraction, EconomicInteractionType, InteractionRole,
    NarrativeEvent
)

# Check if the LLM narrator is implemented
try:
    from narrative import LLMNarrator, HAS_LLM_NARRATOR
    LLM_NARRATOR_IMPLEMENTED = HAS_LLM_NARRATOR
except ImportError:
    LLM_NARRATOR_IMPLEMENTED = False


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


class MockResponse:
    """Mock response for Ollama API calls"""
    def __init__(self, text, status_code=200):
        self.text = text
        self.status_code = status_code
    
    def json(self):
        return {"response": self.text}
    
    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f"HTTP Error: {self.status_code}")


@pytest.mark.skipif(not LLM_NARRATOR_IMPLEMENTED, reason="LLM Narrator not implemented yet")
class TestLLMNarrator:
    """Tests for the LLM-based narrator functionality"""
    
    def test_create_llm_narrator(self):
        """Test that an LLM narrator can be created with mock mode"""
        narrator = LLMNarrator(mock_llm=True)
        assert narrator.verbosity == 3
        assert narrator.model_name == "gemma3:1b"
        assert narrator.mock_llm == True
    
    @patch("requests.post")
    def test_test_ollama_connection(self, mock_post):
        """Test the Ollama connection test functionality"""
        # Set up successful response
        mock_post.return_value = MockResponse(
            text='{"response": "Yes, I am working"}',
            status_code=200
        )
        
        # Test successful connection
        narrator = LLMNarrator(mock_llm=False)
        assert narrator.mock_llm == False  # Should still be False after successful connection
        
        # Set up failing response
        mock_post.side_effect = Exception("Connection failed")
        
        # Test failed connection
        narrator = LLMNarrator(mock_llm=False)
        assert narrator.mock_llm == True  # Should be set to True after failed connection
    
    @patch("requests.post")
    def test_generate_event_from_interaction_with_ollama(self, mock_post, test_agents, test_interaction):
        """Test generating a narrative event using mocked Ollama"""
        # Set up mock response - first for connection test, then for actual narrative
        connection_response = MockResponse(
            text='{"response": "Yes, I am working"}',
            status_code=200
        )
        
        narrative_response = MockResponse(
            text=json.dumps({
                "title": "Unexpected Deal in Olympus Market",
                "description": "Alice Chen offered Bob Rodriguez 30 credits from a 100 credit pot. To everyone's surprise, Bob accepted the unfair offer.",
                "tags": ["ultimatum", "economics", "negotiation"]
            }),
            status_code=200
        )
        
        # Set up side_effect to return different responses
        mock_post.side_effect = [connection_response, narrative_response]
        
        # Create narrator and generate event
        narrator = LLMNarrator(mock_llm=False)
        event = narrator.generate_event_from_interaction(test_interaction, test_agents)
        
        # Verify event
        assert isinstance(event, NarrativeEvent)
        assert "Unexpected Deal" in event.title
        assert "Alice Chen" in event.description
        assert "Bob Rodriguez" in event.description
        assert "30 credits" in event.description
        assert len(event.tags) == 3
        assert "ultimatum" in event.tags
        
        # Verify that Ollama was called twice (once for connection test, once for narrative)
        assert mock_post.call_count == 2
        
        # Check the second call parameters (the actual narrative generation)
        args, kwargs = mock_post.call_args_list[1]
        assert kwargs['json']['model'] == "gemma3:1b"
        assert "economic interaction on Mars" in kwargs['json']['prompt']
        assert "Ultimatum" in kwargs['json']['prompt']
        assert "Alice Chen" in kwargs['json']['prompt']
    
    def test_generate_event_from_interaction_with_mock(self, test_agents, test_interaction):
        """Test generating a narrative event using mock responses"""
        # Create narrator with mock mode
        narrator = LLMNarrator(mock_llm=True)
        event = narrator.generate_event_from_interaction(test_interaction, test_agents)
        
        # Verify event
        assert isinstance(event, NarrativeEvent)
        assert "Tense Ultimatum Negotiation" in event.title
        assert "credit" in event.description
        assert len(event.tags) == 3
    
    @patch("requests.post")
    def test_generate_event_with_ollama_failure(self, mock_post, test_agents, test_interaction):
        """Test fallback to rule-based generation when Ollama fails"""
        # Set up failing response
        mock_post.side_effect = Exception("Ollama generation failed")
        
        # Create narrator and generate event
        narrator = LLMNarrator(mock_llm=False)
        event = narrator.generate_event_from_interaction(test_interaction, test_agents)
        
        # Verify event was generated using rule-based approach
        assert isinstance(event, NarrativeEvent)
        assert event.title is not None and len(event.title) > 0
        assert event.description is not None and len(event.description) > 0
        assert len(event.agents_involved) == 2
    
    @patch("requests.post")
    def test_generate_daily_summary(self, mock_post, test_agents):
        """Test generating a daily summary"""
        # Create some narrative events
        events = [
            NarrativeEvent(
                timestamp=datetime.now(),
                title="Event 1",
                description="Description of event 1",
                agents_involved=[test_agents[0].id, test_agents[1].id],
                significance=0.8,
                tags=["tag1", "tag2"]
            ),
            NarrativeEvent(
                timestamp=datetime.now(),
                title="Event 2",
                description="Description of event 2",
                agents_involved=[test_agents[0].id],
                significance=0.5,
                tags=["tag3", "tag4"]
            )
        ]
        
        # Set up mock response - first for connection test, then for actual summary
        connection_response = MockResponse(
            text='{"response": "Yes, I am working"}',
            status_code=200
        )
        
        summary_response = MockResponse(
            text="# Day 5 on Mars\n\nThe colony was busy today with various activities.\n\n## Notable Events\n\n### Event 1\nDetails about event 1\n\n### Event 2\nDetails about event 2\n\nThe day ended with residents preparing for tomorrow.",
            status_code=200
        )
        
        # Set up side_effect to return different responses
        mock_post.side_effect = [connection_response, summary_response]
        
        # Create narrator and generate summary
        narrator = LLMNarrator(mock_llm=False)
        summary = narrator.generate_daily_summary(5, events, test_agents)
        
        # Verify summary
        assert "Day 5 on Mars" in summary
        assert "Notable Events" in summary
        assert "Event 1" in summary
        assert "Event 2" in summary
        
        # Verify that Ollama was called twice (once for connection test, once for summary)
        assert mock_post.call_count == 2
        
        # Check the second call parameters (the actual summary generation)
        args, kwargs = mock_post.call_args_list[1]
        assert kwargs['json']['model'] == "gemma3:1b"
        assert "daily summary for Day 5" in kwargs['json']['prompt']
        assert "2 colonists" in kwargs['json']['prompt']
        assert "2 significant events" in kwargs['json']['prompt']
    
    def test_get_mock_daily_summary(self):
        """Test the mock daily summary generation"""
        narrator = LLMNarrator(mock_llm=True)
        summary = narrator._get_mock_daily_summary(7, 3)
        
        assert "# Day 7 on Mars" in summary
        assert "3 notable events" in summary
        assert "## Notable Events" in summary
        assert "### Tense Negotiation" in summary
        assert "### Trust Betrayed" in summary
    
    @patch("requests.post")
    def test_handle_malformed_json_response(self, mock_post, test_agents, test_interaction):
        """Test handling of malformed JSON in LLM response"""
        # Set up mock responses - first for connection test, then for narrative with bad JSON
        connection_response = MockResponse(
            text='{"response": "Yes, I am working"}',
            status_code=200
        )
        
        # Create a malformed JSON response (missing closing brace, extra commas, etc.)
        malformed_json_response = MockResponse(
            text='''
            {
                "title": "Economic Negotiation on Mars",
                "description": "Two settlers engaged in an ultimatum game, with one offering 30% of resources to the other.,
                "tags": ["ultimatum", "economics", "negotiation",]
            
            The negotiation proceeded with tension as both parties assessed their positions.
            ''',
            status_code=200
        )
        
        # Set up side_effect to return different responses
        mock_post.side_effect = [connection_response, malformed_json_response]
        
        # Create narrator and generate event
        narrator = LLMNarrator(mock_llm=False)
        event = narrator.generate_event_from_interaction(test_interaction, test_agents)
        
        # Verify that we still got a valid event despite malformed JSON
        assert isinstance(event, NarrativeEvent)
        assert event.title is not None and len(event.title) > 0
        assert event.description is not None and len(event.description) > 0
        assert event.agents_involved == list(test_interaction.participants.keys())
    
    @patch("requests.post")
    def test_handle_extra_text_in_json_response(self, mock_post, test_agents, test_interaction):
        """Test handling of JSON with extra text before/after in LLM response"""
        # Set up mock responses - first for connection test, then for narrative with extra text
        connection_response = MockResponse(
            text='{"response": "Yes, I am working"}',
            status_code=200
        )
        
        # Create a response with valid JSON but extra text around it
        extra_text_response = MockResponse(
            text='''
            I'll generate a narrative for this economic interaction on Mars:
            
            {
                "title": "Ultimatum at Olympus Market",
                "description": "Alice offered Bob 30 credits out of a 100 credit pot. After consideration, Bob accepted the offer.",
                "tags": ["ultimatum", "negotiation", "economic"]
            }
            
            I hope this narrative is suitable for your Mars colony simulation!
            ''',
            status_code=200
        )
        
        # Set up side_effect to return different responses
        mock_post.side_effect = [connection_response, extra_text_response]
        
        # Create narrator and generate event
        narrator = LLMNarrator(mock_llm=False)
        event = narrator.generate_event_from_interaction(test_interaction, test_agents)
        
        # Verify that we extracted the correct JSON content
        assert isinstance(event, NarrativeEvent)
        assert "Ultimatum at Olympus Market" == event.title
        assert "Alice offered Bob 30 credits" in event.description
        assert len(event.tags) == 3
        assert "ultimatum" in event.tags 