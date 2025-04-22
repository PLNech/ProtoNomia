"""
Integration test for a full simulation run.
This test requires a running Ollama server and will make real LLM calls.
"""
import logging
import os
import sys
import unittest

# Add the src directory to the path so we can import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from src.simulation import Simulation
from src.llm_utils import OllamaClient

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestSimulationRun(unittest.TestCase):
    """
    Test the full simulation run.
    This is an integration test that runs the simulation for a few days.
    """

    @classmethod
    def setUpClass(cls):
        """Set up common test fixtures."""
        # Check if we should skip tests
        cls.skip_tests = not cls._is_ollama_available()
        if cls.skip_tests:
            logger.warning("Ollama server not available, skipping integration tests")

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

    def test_simulation_run(self):
        """Test running the simulation for a few days."""
        try:
            # Create a simulation with small values for testing
            simulation = Simulation(
                num_agents=2,  # Small number of agents
                max_days=2,  # Run for just 2 days
            )

            # Run the simulation
            logger.info("Starting simulation test run")
            simulation.run()

            # Check that the simulation ran
            self.assertEqual(simulation.state.day, 2)
            self.assertGreaterEqual(len(simulation.state.actions), 2)  # At least one action per day per agent

            # Check agent states
            for agent in simulation.state.agents:
                self.assertIsNotNone(agent.needs.food)
                self.assertIsNotNone(agent.needs.rest)
                self.assertIsNotNone(agent.needs.fun)
                self.assertIsNotNone(agent.credits)

            logger.info("Simulation test run completed successfully")

        except Exception as e:
            logger.error(f"Error in simulation run: {e}")
            self.fail(f"Simulation run failed: {e}")


if __name__ == '__main__':
    unittest.main()
