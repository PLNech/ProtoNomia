"""
Tests for the core Simulation class without LLM integration.
"""
import pytest
import sys
import os
import inspect
from unittest.mock import patch
from datetime import datetime

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from core.simulation import Simulation
from models.base import SimulationConfig, EconomicInteractionType


class TestSimulation:
    """Tests for the Simulation class implementation"""
    
    def test_simulation_initializes_handlers_correctly(self):
        """Test that Simulation correctly initializes all required handlers"""
        # Create a simulation with mocked dependencies to avoid actual LLM calls
        with patch('core.simulation.LLMAgent'), \
             patch('core.simulation.LLMNarrator'), \
             patch('core.simulation.Narrator'), \
             patch('core.simulation.UltimatumGameHandler'), \
             patch('core.simulation.TrustGameHandler'), \
             patch('core.simulation.PublicGoodsGameHandler'), \
             patch('core.simulation.PopulationController'):
            
            config = SimulationConfig(
                name="Test Simulation",
                seed=42,
                start_date=datetime(2993, 1, 1),
                initial_population=10,
                max_population=100,
                resource_scarcity=0.5,
                terra_mars_trade_ratio=0.6,
                enabled_interaction_types=[
                    EconomicInteractionType.ULTIMATUM,
                    EconomicInteractionType.TRUST,
                    EconomicInteractionType.PUBLIC_GOODS
                ],
                narrative_verbosity=3
            )
            
            # Create simulation without use_llm
            sim = Simulation(config=config)
            
            # Check that interaction handlers are initialized
            assert EconomicInteractionType.ULTIMATUM in sim.interaction_handlers
            assert EconomicInteractionType.TRUST in sim.interaction_handlers
            assert EconomicInteractionType.PUBLIC_GOODS in sim.interaction_handlers 