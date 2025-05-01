"""
Integration tests for Ollama LLM interactions.
These tests require a running Ollama server and will make real LLM calls.
"""
import logging
import os
import sys
import unittest

# Add the src directory to the path so we can import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from src.agent import LLMAgent
from src.narrator import Narrator
from src.models import (
    Agent, AgentPersonality, AgentNeeds, Good, GoodType,
    ActionType, AgentActionResponse, SimulationState
)
from src.llm_utils import OllamaClient
from src.settings import DEFAULT_LM

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestOllamaIntegration(unittest.TestCase):
    """
    Tests that interact with a real Ollama server.
    These tests are meant to be run when the server is available.
    """

    @classmethod
    def setUpClass(cls):
        """Set up common test fixtures."""
        # Check if we should skip tests
        cls.skip_tests = not cls._is_ollama_available()
        if cls.skip_tests:
            logger.warning("Ollama server not available, skipping integration tests")
            return

        # Create test agent
        cls.agent = Agent(
            name="Test Agent",
            personality=AgentPersonality(text="Pragmatic and efficient, focused on optimization"),
            credits=100,
            needs=AgentNeeds(food=0.7, rest=0.5, fun=0.8)
        )

        # Add a good to the agent's inventory
        cls.agent.goods.append(
            Good(type=GoodType.FOOD, quality=0.6, name="Red Mushroom")
        )

        # Create simulation state
        cls.state = SimulationState()
        cls.state.day = 1
        cls.state.agents.append(cls.agent)

        # Create a market listing
        good = Good(type=GoodType.FUN, quality=0.8, name="Solar Entertainment Unit")
        cls.state.market.add_listing(
            seller_id="other_agent",
            good=good,
            price=80,
            day=1
        )

        # Create LLM agent and narrator
        cls.llm_agent = LLMAgent(model_name=DEFAULT_LM)
        cls.narrator = Narrator(model_name=DEFAULT_LM)

        logger.info(f"Using LLM model: {DEFAULT_LM}")

    @staticmethod
    def _is_ollama_available():
        """Check if the Ollama server is available."""
        try:
            client = OllamaClient()
            return client.is_connected
        except Exception:
            return False

    def setUp(self):
        """Set up individual test."""
        if self.skip_tests:
            self.skipTest("Ollama server not available")

    def test_agent_action_generation(self):
        """Test generating agent actions."""
        try:
            action_response = self.llm_agent.generate_action(self.agent, self.state)

            # Check that we got a valid response
            self.assertIsNotNone(action_response)
            self.assertIn(action_response.type, list(ActionType))

            # Log the action
            logger.info(f"Agent chose action: {action_response.type.value}")
            if action_response.reasoning:
                logger.info(f"Reasoning: {action_response.reasoning}")

        except Exception as e:
            logger.error(f"Error in agent action generation: {e}")
            self.fail(f"Agent action generation failed: {e}")

    def test_daily_summary_generation(self):
        """Test generating daily summaries."""
        try:
            # Add an action to the state
            agent = Agent(name="Foo", id="agent_0")
            action = AgentActionResponse(
                type=ActionType.WORK
            )
            self.state.add_action(agent=agent, action=action)

            # Generate summary
            summary = self.narrator.generate_daily_summary(self.state)

            # Check that we got a valid response
            self.assertIsNotNone(summary)
            self.assertIsNotNone(summary.title)
            self.assertIsNotNone(summary.content)
            self.assertIsInstance(summary.highlights, list)

            # Log the summary
            logger.info(f"Daily summary title: {summary.title}")
            logger.info(f"Summary: {summary.content}")
            logger.info(f"Highlights: {summary.highlights}")

        except Exception as e:
            logger.error(f"Error in daily summary generation: {e}")
            self.fail(f"Daily summary generation failed: {e}")


if __name__ == '__main__':
    unittest.main()
