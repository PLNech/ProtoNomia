"""
Unit tests for the narrator module.
"""
import unittest
from unittest.mock import MagicMock, patch

from src.narrator import Narrator
from src.models import (
    Agent, AgentPersonality, AgentNeeds, Good, GoodType,
    ActionType, AgentAction, SimulationState, DailySummaryResponse, ActionLog, AgentActionResponse
)


class TestNarrator(unittest.TestCase):
    """Test cases for the Narrator class."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_ollama_client = MagicMock()

        # Create agents and simulation state for testing
        self.agent1 = Agent(
            name="Agent 1",
            personality=AgentPersonality(text="Cautious")
        )
        self.agent2 = Agent(
            name="Agent 2",
            personality=AgentPersonality(text="Adventurous")
        )

        # Create simulation state
        self.state = SimulationState()
        self.state.day = 0
        self.state.agents = [self.agent1, self.agent2]

        # Add some agent actions
        self.action1 = AgentActionResponse(
            type=ActionType.WORK
        )
        self.action2 = AgentActionResponse(
            type=ActionType.HARVEST
        )
        self.agent = Agent(name="0")

        self.state.actions = [ActionLog(action=a, agent=self.agent, day=0) for a in [self.action1, self.action2]]

    @patch('src.narrator.OllamaClient')
    def test_narrator_init(self, mock_ollama_class):
        """Test Narrator initialization."""
        # Setup the mock
        mock_ollama_class.return_value = self.mock_ollama_client

        # Create the Narrator
        narrator = Narrator(model_name="test-model")

        # Verify OllamaClient was initialized correctly
        mock_ollama_class.assert_called_once()
        self.assertEqual(narrator.model_name, "test-model")

    @patch('src.narrator.OllamaClient')
    def test_generate_daily_summary(self, mock_ollama_class):
        """Test generate_daily_summary method."""
        # Setup mocks
        mock_ollama_class.return_value = self.mock_ollama_client

        # Setup mock response
        mock_summary = DailySummaryResponse(
            title="Test Day",
            content="This is a test summary",
            highlights=["Highlight 1", "Highlight 2"]
        )
        self.mock_ollama_client.generate_daily_summary.return_value = mock_summary

        # Create narrator and call generate_daily_summary
        narrator = Narrator()
        result = narrator.generate_daily_summary(self.state)

        # Verify the result
        self.assertEqual(result.title, "Test Day")
        self.assertEqual(result.content, "This is a test summary")

        # Verify generate_daily_summary was called
        self.mock_ollama_client.generate_daily_summary.assert_called_once()

    @patch('src.narrator.OllamaClient')
    def test_format_summary_prompt(self, mock_ollama_class):
        """Test _format_summary_prompt method."""
        # Setup mocks
        mock_ollama_class.return_value = self.mock_ollama_client

        # Create narrator
        narrator = Narrator()

        # Create a good and listing
        good = Good(type=GoodType.FOOD, quality=0.8, name="Test Food")
        self.state.market.add_listing(
            seller_id=self.agent1.id,
            good=good,
            price=100,
            day=1
        )

        # Generate prompt
        prompt = narrator._format_summary_prompt(self.state)

        # Verify prompt contains necessary information
        self.assertIn(f"DAY {self.state.day}", prompt)
        self.assertIn(self.agent1.name, prompt)
        self.assertIn(self.agent2.name, prompt)
        self.assertIn("Test Food", prompt)
        self.assertIn("worked at the settlement job", prompt)  # Action description
        self.assertIn("harvested mushrooms", prompt)  # Action description

    @patch('src.narrator.OllamaClient')
    def test_describe_action(self, mock_ollama_class):
        """Test _describe_action method."""
        # Setup mocks
        mock_ollama_class.return_value = self.mock_ollama_client

        # Create narrator
        narrator = Narrator()

        # Test each action type
        action_rest = AgentAction(
            agent_id=self.agent1.id,
            type=ActionType.REST,
            extras={},
            day=1
        )
        self.assertIn("rest", narrator._describe_action(action_rest, self.agent1))

        action_work = AgentAction(
            agent_id=self.agent1.id,
            type=ActionType.WORK,
            extras={},
            day=1
        )
        self.assertIn("work", narrator._describe_action(action_work, self.agent1))

        action_harvest = AgentAction(
            agent_id=self.agent1.id,
            type=ActionType.HARVEST,
            extras={},
            day=1
        )
        self.assertIn("harvest", narrator._describe_action(action_harvest, self.agent1))

        action_craft = AgentAction(
            agent_id=self.agent1.id,
            type=ActionType.CRAFT,
            extras={"materials": 50},
            day=1
        )
        craft_desc = narrator._describe_action(action_craft, self.agent1)
        self.assertIn("craft", craft_desc)
        self.assertIn("50", craft_desc)

    @patch('src.narrator.OllamaClient')
    def test_fallback_summary(self, mock_ollama_class):
        """Test fallback summary generation."""
        # Setup mocks
        mock_ollama_class.return_value = self.mock_ollama_client

        # Create narrator
        narrator = Narrator()

        # Force LLM to throw an exception
        self.mock_ollama_client.generate_daily_summary.side_effect = Exception("Test exception")

        # Call generate_daily_summary, should use fallback
        result = narrator.generate_daily_summary(self.state)

        # Verify result is a valid DailySummaryResponse
        self.assertIsInstance(result, DailySummaryResponse)
        self.assertIsNotNone(result.title)
        self.assertIsNotNone(result.content)


if __name__ == '__main__':
    unittest.main()
