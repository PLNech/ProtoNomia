"""
Integration tests for the LLMAgent with actual LLM service.
"""
import os
import sys

import pytest

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from agents.llm_agent import LLMAgent
from models.base import Agent, AgentType, AgentFaction, AgentPersonality, ResourceBalance, ResourceType, ActionType, \
    AgentDecisionContext


@pytest.fixture
def test_agent():
    """Create a test agent for the LLM integration tests"""
    return Agent(
        name="Test Agent",
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
                resource_type=ResourceType.FOOD,
                amount=50.0
            )
        ]
    )


@pytest.fixture
def decision_context(test_agent):
    """Create a decision context for the agent"""
    return AgentDecisionContext(
        turn=10,
        max_turns=100,
        neighbors=["Agent1", "Agent2"],
        pending_offers=[
            {"id": "offer1", "from_agent": "Agent1", "what": "10 credits", "against_what": "5 food",
             "status": "pending"}
        ],
        jobs_available=[
            {"id": "job1", "title": "Engineer", "salary": 20, "duration": 5}
        ],
        items_for_sale=[
            {"id": "item1", "name": "Medical Kit", "price": 15, "seller": "Agent2"}
        ]
    )


@pytest.mark.llm
@pytest.mark.skipif(not os.environ.get("RUN_LLM_TESTS"),
                    reason="LLM tests are disabled. Set RUN_LLM_TESTS=1 to enable.")
class TestLLMAgentIntegration:
    """
    Integration tests for LLMAgent with actual LLM service.
    
    These tests require an actual LLM service running.
    """

    def test_ollama_connection(self):
        """Test that we can connect to Ollama"""
        try:
            agent = LLMAgent()
            # If we got here without exception, connection was successful
            assert True
        except Exception as e:
            pytest.fail(f"Failed to connect to Ollama: {e}")

    def test_agent_action_generation(self, test_agent, decision_context):
        """Test that the agent can generate actions using LLM"""
        agent = LLMAgent()

        # Generate an action
        action = agent.generate_action(test_agent, decision_context)

        # Verify basic properties of the action
        assert action is not None
        assert action.agent_id == test_agent.id
        assert action.turn == decision_context.turn
        assert action.type in [member for member in ActionType]

    def test_agent_action_stability(self, test_agent, decision_context):
        """Test that agent actions are somewhat consistent for the same input"""
        agent = LLMAgent(temperature=0.1)  # Low temperature for more deterministic results

        # Generate actions multiple times and ensure they're not all over the place
        action_types = set()
        for _ in range(3):
            action = agent.generate_action(test_agent, decision_context)
            action_types.add(action.type)

        # While the exact action may vary, we shouldn't see more than 2 different
        # action types for the same input with low temperature
        assert len(action_types) <= 2, f"Too many different action types: {action_types}"
