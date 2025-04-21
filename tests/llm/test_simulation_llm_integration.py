"""
Integration tests for the Simulation class with LLM components.
"""
import pytest
import sys
import os
from datetime import datetime
from typing import List

from settings import DEFAULT_LM

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from core.simulation import Simulation
from models.base import SimulationConfig, EconomicInteractionType, NarrativeEvent
from agents.llm_agent import LLMAgent
from narrative.llm_narrator import LLMNarrator


@pytest.mark.llm
@pytest.mark.skipif(not os.environ.get("RUN_LLM_TESTS"),
                    reason="LLM tests are disabled. Set RUN_LLM_TESTS=1 to enable.")
class TestSimulationLLMIntegration:
    """
    Integration tests for Simulation with LLM components.
    
    These tests require an actual LLM service running.
    """

    def test_simulation_initializes_llm_components(self):
        """Test that Simulation correctly initializes LLM components"""
        config = SimulationConfig(
            name="LLM Integration Test Simulation",
            seed=42,
            start_date=datetime(2993, 1, 1),
            initial_population=5,
            max_population=10,
            resource_scarcity=0.5,
            terra_mars_trade_ratio=0.6,
            enabled_interaction_types=[
                EconomicInteractionType.ULTIMATUM,
                EconomicInteractionType.TRUST
            ],
            narrative_verbosity=3
        )

        # Create simulation with use_llm=True
        sim = Simulation(
            config=config,
            use_llm=True,
            model_name=DEFAULT_LM,
            narrator_model_name=DEFAULT_LM
        )

        # Check that LLM components are initialized
        assert sim.llm_agent is not None
        assert isinstance(sim.llm_agent, LLMAgent)
        assert isinstance(sim.narrator, LLMNarrator)
        assert sim.narrator.model_name == DEFAULT_LM

    def test_simulation_run_with_llm(self):
        """Test running a minimal simulation with LLM components"""
        config = SimulationConfig(
            name="LLM Integration Test Simulation",
            seed=42,
            start_date=datetime(2993, 1, 1),
            initial_population=3,  # Small population for quick test
            max_population=5,
            resource_scarcity=0.5,
            terra_mars_trade_ratio=0.6,
            enabled_interaction_types=[
                EconomicInteractionType.ULTIMATUM
            ],
            narrative_verbosity=2  # Lower verbosity for quicker generation
        )

        # Create and initialize simulation
        sim = Simulation(
            config=config,
            use_llm=True
        )

        # Initialize and run for a few steps
        sim.initialize()

        # Run for a few ticks
        for _ in range(2):
            state = sim.step()

        # Check that we have some agents and possibly some narrative events
        assert len(sim.agents) > 0

        # It's possible we might not have narrative events yet, but the simulation should run without errors
        if len(sim.narrative_events) > 0:
            # If we have events, check they have proper fields
            event = list(sim.narrative_events.values())[0]
            assert isinstance(event, NarrativeEvent)
            assert event.title is not None and len(event.title) > 0
            assert event.description is not None and len(event.description) > 0
