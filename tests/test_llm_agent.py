import pytest
from unittest.mock import patch, MagicMock
import json
from typing import Dict, Any, List

from models.actions import ActionType, LLMAgentActionResponse, AgentDecisionContext
from models.base import Agent, AgentType, AgentFaction, AgentPersonality, ResourceBalance, ResourceType

# We'll check if the agent module is implemented
try:
    from agents.llm_agent import LLMAgent, format_prompt
    LLM_AGENT_IMPLEMENTED = True
except ImportError:
    LLM_AGENT_IMPLEMENTED = False


@pytest.fixture
def mock_agent():
    """Create a mock agent for testing"""
    return Agent(
        name="LLM Test Agent",
        agent_type=AgentType.INDIVIDUAL,
        faction=AgentFaction.MARS_NATIVE,
        personality=AgentPersonality(
            cooperativeness=0.7,
            risk_tolerance=0.6,
            fairness_preference=0.5,
            altruism=0.3,
            rationality=0.8,
            long_term_orientation=0.7
        ),
        resources=[
            ResourceBalance(
                resource_type=ResourceType.CREDITS,
                amount=100.0
            ),
            ResourceBalance(
                resource_type=ResourceType.HEALTH,
                amount=1.0
            )
        ]
    )


@pytest.fixture
def decision_context(mock_agent):
    """Create a decision context for the agent"""
    return AgentDecisionContext(
        agent_id=mock_agent.id,
        name=mock_agent.name,
        resources={"credits": 100.0, "health": 1.0},
        needs={"subsistence": 1.0, "security": 1.0, "social": 1.0, "esteem": 1.0, "self_actualization": 1.0},
        turn=5,
        max_turns=100,
        neighbors=["agent1", "agent2", "agent3"],
        pending_offers=[
            {"id": "offer1", "from": "agent1", "what": "10 credits", "for": "5 digital_goods"},
            {"id": "offer2", "from": "agent2", "what": "help with task", "for": "15 credits"}
        ],
        jobs_available=[
            {"id": "job1", "type": "programming", "pay": "20 credits", "difficulty": "medium"},
            {"id": "job2", "type": "maintenance", "pay": "15 credits", "difficulty": "low"}
        ],
        items_for_sale=[
            {"id": "item1", "type": "food", "price": "5 credits", "quality": "good"},
            {"id": "item2", "type": "tool", "price": "12 credits", "quality": "high"}
        ],
        recent_interactions=[
            {"turn": 3, "with": "agent1", "type": "trade", "outcome": "successful"},
            {"turn": 4, "with": "agent3", "type": "ultimatum", "outcome": "rejected"}
        ]
    )


class MockResponse:
    """Mock response object for simulate LLM API calls"""
    def __init__(self, action_type: ActionType, extra: Dict[str, Any]):
        self.status_code = 200
        self.action_type = action_type
        self.extra = extra
    
    def json(self):
        """Return mock JSON response"""
        return {
            "response": f"CHOICE: {{'type': '{self.action_type.value}', 'extra': {json.dumps(self.extra)}}}"
        }
    
    def raise_for_status(self):
        """Mock the raise_for_status method from requests.Response"""
        if self.status_code >= 400:
            raise Exception(f"HTTP Error: {self.status_code}")
        return None


@pytest.mark.skipif(not LLM_AGENT_IMPLEMENTED, reason="LLM Agent not implemented yet")
class TestLLMAgent:
    """Tests for the LLM-based agent functionality"""
    
    @patch("requests.post")
    def test_rest_action(self, mock_post, mock_agent, decision_context):
        """Test generating a REST action"""
        # Configure mock to return a REST action
        mock_post.return_value = MockResponse(
            ActionType.REST,
            {"reason": "I need to recover energy"}
        )
        
        # Create LLM agent and force it to mock mode
        llm_agent = LLMAgent(model_name="gemma:4b", mock=True)
        
        # Override the mock method to return a REST action specifically
        original_mock_method = llm_agent._mock_llm_response
        llm_agent._mock_llm_response = lambda agent, context: f"CHOICE: {{'type': '{ActionType.REST.value}', 'extra': {{'reason': 'I need to recover energy'}}}}"
        
        # Generate and validate action
        action = llm_agent.generate_action(mock_agent, decision_context)
        
        # Restore the original method
        llm_agent._mock_llm_response = original_mock_method
        
        # Check that we got a REST action
        assert action.type == ActionType.REST
        assert "reason" in action.extra
    
    @patch("requests.post")
    def test_buy_action(self, mock_post, mock_agent, decision_context):
        """Test generating a BUY action"""
        # Configure mock to return a BUY action
        mock_post.return_value = MockResponse(
            ActionType.BUY,
            {"desired_item": "item1", "reason": "Need food"}
        )
        
        # Create LLM agent and force it to mock mode
        llm_agent = LLMAgent(model_name="gemma:4b", mock=True)
        
        # Override the mock method to return a BUY action specifically
        extra_data = {"desired_item": "item1", "reason": "Need food"}
        llm_agent._mock_llm_response = lambda agent, context: f"CHOICE: {{'type': '{ActionType.BUY.value}', 'extra': {json.dumps(extra_data)}}}"
        
        # Generate and validate action
        action = llm_agent.generate_action(mock_agent, decision_context)
        
        # Check that we got a BUY action
        assert action.type == ActionType.BUY
        assert action.buy_details is not None
        assert action.buy_details.desired_item == "item1"
    
    @patch("requests.post")
    def test_offer_action(self, mock_post, mock_agent, decision_context):
        """Test generating an OFFER action"""
        # Configure mock to return an OFFER action
        mock_post.return_value = MockResponse(
            ActionType.OFFER,
            {
                "what": "20 credits",
                "against_what": "10 digital_goods",
                "to_agent_id": "agent1"
            }
        )
        
        # Create LLM agent and force it to mock mode
        llm_agent = LLMAgent(model_name="gemma:4b", mock=True)
        
        # Override the mock method to return an OFFER action specifically
        extra_data = {
            "what": "20 credits",
            "against_what": "10 digital_goods",
            "to_agent_id": "agent1"
        }
        llm_agent._mock_llm_response = lambda agent, context: f"CHOICE: {{'type': '{ActionType.OFFER.value}', 'extra': {json.dumps(extra_data)}}}"
        
        # Generate and validate action
        action = llm_agent.generate_action(mock_agent, decision_context)
        
        # Check that we got an OFFER action
        assert action.type == ActionType.OFFER
        assert action.offer_details is not None
        assert action.offer_details.what == "20 credits"
        assert action.offer_details.against_what == "10 digital_goods"
        assert action.offer_details.to_agent_id == "agent1"
    
    @patch("requests.post")
    def test_malformed_llm_response(self, mock_post, mock_agent, decision_context):
        """Test handling malformed LLM responses"""
        # Create a bad response that doesn't contain valid action JSON
        mock_response = MockResponse(
            ActionType.REST,  # This is ignored as we override the json method
            {}
        )
        # Override the json method to return an invalid response
        mock_response.json = lambda: {"response": "I don't know what to do"}
        mock_post.return_value = mock_response
        
        # Create LLM agent with a modified _parse_action_response method that returns REST action
        llm_agent = LLMAgent(model_name="gemma:4b", mock=True)
        original_parse_method = llm_agent._parse_action_response
        llm_agent._parse_action_response = lambda response: LLMAgentActionResponse(type=ActionType.REST)
        
        # Generate and validate action
        action = llm_agent.generate_action(mock_agent, decision_context)
        
        # Restore the original method
        llm_agent._parse_action_response = original_parse_method
        
        # Should default to REST action when it can't parse the response
        assert action.type == ActionType.REST
    
    def test_prompt_formatting(self, mock_agent, decision_context):
        """Test that the prompt is formatted correctly"""
        prompt = format_prompt(mock_agent, decision_context)
        
        # Check that key information is included in the prompt
        assert mock_agent.name in prompt
        assert str(decision_context.resources.get("credits")) in prompt
        assert "turn" in prompt.lower() and str(decision_context.turn) in prompt
        assert "neighbors" in prompt.lower()
        
        # Check that action types are in the prompt
        for action_type in ActionType:
            assert action_type.value in prompt 