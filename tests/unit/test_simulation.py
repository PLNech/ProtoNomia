"""
Unit tests for the simulation module.
"""
import unittest
from unittest.mock import MagicMock, patch

from src.models import (
    AgentNeeds, GoodType,
    ActionType, AgentAction
)
from src.simulation import Simulation


class TestSimulation(unittest.TestCase):
    """Test cases for the Simulation class."""

    def setUp(self):
        """Set up test fixtures."""
        # Use small values for tests
        self.simulation = Simulation(num_agents=2, max_days=3)
        self.simulation._add_agent(self.simulation._create_agent("Test1"))
        self.simulation._add_agent(self.simulation._create_agent("Test2"))
        # Mock the LLM agent and narrator
        self.simulation.llm_agent = MagicMock()
        self.simulation.narrator = MagicMock()

    def test_initialization(self):
        """Test simulation initialization."""
        self.assertEqual(len(self.simulation.state.agents), 2)
        self.assertEqual(self.simulation.state.day, 0)
        self.assertEqual(len(self.simulation.state.market.listings), 0)

    def test_agent_creation(self):
        """Test agent creation."""
        agent = self.simulation._create_agent("Test Agent")
        self.assertEqual(agent.name, "Test Agent")
        self.assertTrue(0 <= agent.needs.food <= 1.0, f"Invalid food: {agent.needs.food}")
        self.assertTrue(0 <= agent.needs.rest <= 1.0, f"Invalid rest: {agent.needs.rest}")
        self.assertTrue(0 <= agent.needs.fun <= 1.0, f"Invalid fun: {agent.needs.fun}")
        self.assertTrue(50 <= agent.credits <= 10000000, f"Invalid credits: {agent.credits}")
        self.assertTrue(agent.is_alive)

    def test_step_needs(self):
        """Test the needs step."""
        # Set up agents with known needs
        agent1 = self.simulation.state.agents[0]
        agent2 = self.simulation.state.agents[1]

        agent1.needs = AgentNeeds(food=1.0, rest=1.0, fun=1.0)
        agent2.needs = AgentNeeds(food=0.2, rest=0.3, fun=0.4)

        # Run the needs step
        self.simulation._step_needs()

        # Check that needs were reduced
        self.assertEqual(agent1.needs.food, 0.9)  # 1.0 - 0.1
        self.assertEqual(agent1.needs.rest, 0.9)  # 1.0 - 0.1
        self.assertEqual(agent1.needs.fun, 0.9)  # 1.0 - 0.1

        self.assertEqual(agent2.needs.food, 0.1)  # 0.2 - 0.1
        self.assertEqual(agent2.needs.rest, 0.2)  # 0.3 - 0.1
        self.assertEqual(agent2.needs.fun, 0.3)  # 0.4 - 0.1

    def test_step_death(self):
        """Test the death step."""
        # Set up one agent to die
        agent1 = self.simulation.state.agents[0]
        agent2 = self.simulation.state.agents[1]

        agent1.needs = AgentNeeds(food=0.0, rest=0.5, fun=0.5)  # Should die (food = 0)
        agent2.needs = AgentNeeds(food=0.5, rest=0.0, fun=0.5)  # Should die (rest = 0)

        # Run the death step
        self.simulation._step_death()

        # Check that both agents died
        self.assertFalse(agent1.is_alive)
        self.assertFalse(agent2.is_alive)
        self.assertEqual(agent1.death_day, self.simulation.state.day)
        self.assertEqual(agent2.death_day, self.simulation.state.day)
        self.assertEqual(len(self.simulation.state.dead_agents), 2)

    @patch('random.uniform')
    def test_harvest_action(self, mock_uniform):
        """Test the harvest action."""
        # Mock random for deterministic tests
        mock_uniform.return_value = 0.5

        agent = self.simulation.state.agents[0]
        action = AgentAction(
            agent_id=agent.id,
            type=ActionType.HARVEST,
            extras={},
            day=1
        )

        # Run the consequence step for this action
        self.simulation._step_consequences([(agent, action)])

        # Check that the agent harvested a mushroom
        self.assertEqual(len(agent.goods), 1)
        self.assertEqual(agent.goods[0].type, GoodType.FOOD)
        self.assertTrue("Mushroom" in agent.goods[0].name)
        self.assertEqual(agent.goods[0].quality, 0.5)

    def test_rest_action(self):
        """Test the rest action."""
        agent = self.simulation.state.agents[0]
        agent.needs.rest = 0.5

        action = AgentAction(
            agent_id=agent.id,
            type=ActionType.REST,
            extras={},
            day=1
        )

        # Run the consequence step for this action
        self.simulation._step_consequences([(agent, action)])

        # Check that rest increased
        self.assertEqual(agent.needs.rest, 0.7)  # 0.5 + 0.2


if __name__ == '__main__':
    unittest.main()
