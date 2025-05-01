"""
Unit tests for the agent module.
"""
import unittest
from unittest.mock import MagicMock, patch

from src.agent import LLMAgent, format_prompt
from src.models import (
    Agent, AgentPersonality, AgentNeeds, Good, GoodType, 
    ActionType, AgentActionResponse, SimulationState
)


class TestAgentModule(unittest.TestCase):
    """Test cases for the agent module."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_ollama_client = MagicMock()
        
        # Create an agent instance for testing
        self.agent = Agent(
            name="Test Agent", 
            personality=AgentPersonality(text="Cautious and methodical")
        )
        
        # Create a simulation state for testing
        self.simulation_state = SimulationState()
        self.simulation_state.day = 1
        self.simulation_state.agents.append(self.agent)

    @patch('src.agent.OllamaClient')
    def test_llm_agent_init(self, mock_ollama_class):
        """Test LLMAgent initialization."""
        # Setup the mock
        mock_ollama_class.return_value = self.mock_ollama_client
        
        # Create the LLMAgent
        agent = LLMAgent(model_name="test-model")
        
        # Verify OllamaClient was initialized correctly
        mock_ollama_class.assert_called_once()
        self.assertEqual(agent.model_name, "test-model")

    @patch('src.agent.OllamaClient')
    def test_generate_action(self, mock_ollama_class):
        """Test generate_action method."""
        # Setup mocks
        mock_ollama_class.return_value = self.mock_ollama_client
        
        # Setup mock response
        mock_action_response = AgentActionResponse(
            type=ActionType.REST,
            extras={},
            reasoning="Test reasoning"
        )
        self.mock_ollama_client.generate_structured.return_value = mock_action_response
        
        # Create agent and call generate_action
        llm_agent = LLMAgent()
        result = llm_agent.generate_action(self.agent, self.simulation_state)
        
        # Verify the result
        self.assertEqual(result.type, ActionType.REST)
        self.assertEqual(result.reasoning, "Test reasoning")
        
        # Verify generate_structured was called with correct parameters
        self.mock_ollama_client.generate_structured.assert_called_once()

    def test_format_prompt(self):
        """Test format_prompt function."""
        # Add some data to the agent and simulation state
        self.agent.credits = 100
        self.agent.needs.food = 0.8
        self.agent.needs.rest = 0.6
        self.agent.needs.fun = 0.7
        
        # Add a good to the agent's inventory
        self.agent.goods.append(
            Good(type=GoodType.FOOD, quality=0.5, name="Test Food")
        )
        
        # Add a market listing
        good = Good(type=GoodType.FUN, quality=0.8, name="Fun Item")
        self.simulation_state.market.add_listing(
            seller_id=self.agent.id,
            good=good,
            price=50,
            day=1
        )
        
        # Format the prompt
        prompt = format_prompt(self.agent, self.simulation_state)
        
        # Check that the prompt contains essential information
        self.assertIn(f"MARS COLONY DAY {self.simulation_state.day}", prompt)
        self.assertIn(f"Name: {self.agent.name}", prompt)
        self.assertIn(f"Credits: {self.agent.credits}", prompt)
        self.assertIn(f"Food: {self.agent.needs.food:.2f}", prompt)
        self.assertIn(f"Rest: {self.agent.needs.rest:.2f}", prompt)
        self.assertIn(f"Fun: {self.agent.needs.fun:.2f}", prompt)
        self.assertIn("Test Food", prompt)  # Agent's inventory
        self.assertIn("Fun Item", prompt)   # Market listing
        
        # Check that all action types are mentioned
        for action_type in ActionType:
            self.assertIn(action_type.value, prompt)

    def test_fallback_action(self):
        """Test fallback action generation."""
        llm_agent = LLMAgent()
        
        # Call the fallback action directly
        action = llm_agent._fallback_action()
        
        # Verify it returns a valid action
        self.assertIsInstance(action, AgentActionResponse)
        self.assertIn(action.type, list(ActionType))
        self.assertIsNotNone(action.reasoning)
        self.assertIn("fallback", action.reasoning.lower())


if __name__ == '__main__':
    unittest.main() 