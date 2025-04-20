"""
Integration tests for ProtoNomia components working together.
"""
import os
import tempfile
import pytest
from datetime import datetime
from typing import List, Dict

from models.base import (
    Agent, AgentType, AgentFaction, AgentPersonality,
    EconomicInteraction, EconomicInteractionType, InteractionRole,
    SimulationConfig, ResourceType, ResourceBalance
)
from core.simulation import Simulation

# Check if the LLM components are available
try:
    from narrative import LLMNarrator, HAS_LLM_NARRATOR
    from agents.llm_agent import LLMAgent
    HAS_LLM_COMPONENTS = HAS_LLM_NARRATOR
except ImportError:
    HAS_LLM_COMPONENTS = False


@pytest.mark.skipif(not HAS_LLM_COMPONENTS, reason="LLM components not implemented yet")
class TestLLMNarratorIntegration:
    """Integration tests for LLM-based narrator with simulation"""
    
    def test_llm_narrator_in_simulation(self):
        """Test that LLM narrator can be used in a simulation with mocked responses"""
        # Create a simulation configuration
        config = SimulationConfig(
            name="Test Simulation",
            seed=42,  # For reproducibility
            start_date=datetime(2993, 1, 1),
            initial_population=5,
            max_population=10,
            resource_scarcity=0.5,
            enabled_interaction_types=[
                EconomicInteractionType.TRUST,
                EconomicInteractionType.ULTIMATUM
            ],
            narrative_verbosity=4
        )
        
        # Create a simulation with LLM narrator in mock mode
        simulation = Simulation(
            config=config,
            use_llm=True,
            mock_llm=True,
            model_name="gemma:1b",
            narrator_model_name="gemma3:1b"
        )
        
        # Initialize and run for a few ticks
        simulation.initialize()
        
        for _ in range(3):
            simulation.step()
        
        # Verify that the simulation has been initialized with a LLM narrator
        assert simulation.narrator is not None
        assert hasattr(simulation.narrator, "model_name")
        assert simulation.narrator.model_name == "gemma3:1b"
        
        # Create a simulated interaction to test narrative generation
        test_agent1 = self._create_test_agent("Alice", AgentType.INDIVIDUAL, AgentFaction.MARS_NATIVE)
        test_agent2 = self._create_test_agent("Bob", AgentType.INDIVIDUAL, AgentFaction.INDEPENDENT)
        
        simulation.agents[test_agent1.id] = test_agent1
        simulation.agents[test_agent2.id] = test_agent2
        
        # Create a test interaction
        interaction = EconomicInteraction(
            interaction_type=EconomicInteractionType.ULTIMATUM,
            participants={
                test_agent1.id: InteractionRole.PROPOSER,
                test_agent2.id: InteractionRole.RESPONDER
            },
            parameters={
                "total_amount": 100.0,
                "offer_amount": 30.0,
                "responder_accepts": True,
                "currency": "credits"
            },
            is_complete=True,
            narrative_significance=0.8
        )
        
        # Generate a narrative event for the interaction
        event = simulation.narrator.generate_event_from_interaction(
            interaction,
            [test_agent1, test_agent2]
        )
        
        # Verify that a narrative event was created
        assert event is not None
        assert event.title is not None and len(event.title) > 0
        assert event.description is not None and len(event.description) > 0
        assert len(event.agents_involved) == 2
        
        # Verify that we can generate a daily summary
        summary = simulation.narrator.generate_daily_summary(
            day=1,
            events=[event],
            agents=[test_agent1, test_agent2]
        )
        
        # Check that the summary was created
        assert summary is not None
        assert len(summary) > 0
        assert "Day 1 on Mars" in summary
    
    def test_scenario_extreme_offer(self):
        """Test a scenario with an extreme ultimatum offer to see how the narrator describes it"""
        # Create test agents with extreme personality traits
        altruistic_agent = self._create_test_agent(
            "Altruist",
            AgentType.INDIVIDUAL,
            AgentFaction.MARS_NATIVE,
            personality=AgentPersonality(
                cooperativeness=0.9,
                risk_tolerance=0.3,
                fairness_preference=0.9,
                altruism=0.9,
                rationality=0.7,
                long_term_orientation=0.8
            )
        )

        selfish_agent = self._create_test_agent(
            "Selfish",
            AgentType.INDIVIDUAL,
            AgentFaction.TERRA_CORP,
            personality=AgentPersonality(
                cooperativeness=0.1,
                risk_tolerance=0.8,
                fairness_preference=0.2,
                altruism=0.1,
                rationality=0.6,
                long_term_orientation=0.3
            )
        )

        # Create a narrator with mock mode
        from narrative.llm_narrator import LLMNarrator
        narrator = LLMNarrator(verbosity=4, mock_llm=True)
        
        # Customize mock response for this specific test
        original_mock_generate = narrator._mock_generate
        narrator._mock_generate = lambda prompt: "Selfish offered Altruist a mere 10 credits out of a 1000 credit pot, an extremely unfair division. Despite the blatant selfishness of the offer, Altruist reluctantly accepted, prioritizing some gain over none, though clearly displeased with the inequitable terms."

        try:
            # Create an extremely unfair interaction
            interaction = EconomicInteraction(
                interaction_type=EconomicInteractionType.ULTIMATUM,
                participants={
                    selfish_agent.id: InteractionRole.PROPOSER,
                    altruistic_agent.id: InteractionRole.RESPONDER
                },
                parameters={
                    "total_amount": 1000.0,
                    "offer_amount": 10.0,  # Very unfair 1% offer
                    "responder_accepts": True,  # Altruistic agent accepts anyway
                    "currency": "credits"
                },
                is_complete=True,
                narrative_significance=0.9
            )

            # Generate narrative event
            event = narrator.generate_event_from_interaction(
                interaction,
                [altruistic_agent, selfish_agent]
            )

            # Verify the narrative captures the extreme scenario
            assert event is not None
            assert any(word in event.description.lower() for word in ["unfair", "extreme", "selfish", "inequitable", "mere"])
        finally:
            # Restore original mock method
            narrator._mock_generate = original_mock_generate
    
    def _create_test_agent(self, name: str, agent_type: AgentType, faction: AgentFaction, 
                          personality: AgentPersonality = None) -> Agent:
        """Helper method to create a test agent"""
        if personality is None:
            personality = AgentPersonality(
                cooperativeness=0.5,
                risk_tolerance=0.5,
                fairness_preference=0.5,
                altruism=0.5,
                rationality=0.5,
                long_term_orientation=0.5
            )
        
        return Agent(
            name=name,
            agent_type=agent_type,
            faction=faction,
            personality=personality,
            resources=[
                ResourceBalance(
                    resource_type=ResourceType.CREDITS,
                    amount=100.0
                ),
                ResourceBalance(
                    resource_type=ResourceType.HEALTH,
                    amount=1.0
                )
            ],
            birth_date=datetime(2950, 1, 1),
            is_alive=True
        ) 