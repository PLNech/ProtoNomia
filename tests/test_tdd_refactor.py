"""
Tests to verify the refactoring of the ProtoNomia codebase.
These tests ensure that:
1. LLM agent doesn't have mock functionality
2. LLM narrator doesn't have mock functionality
3. Simulation correctly initializes handlers without falling back to mocks
4. The headless.py script can run without the mock_llm parameter
"""
import pytest
import sys
import os
import inspect
from unittest.mock import patch, MagicMock

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.llm_agent import LLMAgent
from narrative.llm_narrator import LLMNarrator
from narrative.narrator import Narrator
from core.simulation import Simulation
from models.base import SimulationConfig, EconomicInteractionType
from economics.interactions.base import InteractionHandler
from economics.interactions.ultimatum import UltimatumGameHandler
from economics.interactions.trust import TrustGameHandler
from economics.interactions.public_goods import PublicGoodsGameHandler
import headless
from datetime import datetime


class TestRefactoring:
    """Tests to verify our refactoring of the codebase"""
    
    def test_llm_agent_has_no_mock_functionality(self):
        """Test that the LLMAgent class has no mock functionality"""
        # Check that there's no 'mock' parameter in the LLMAgent constructor
        signature = inspect.signature(LLMAgent.__init__)
        assert 'mock' not in signature.parameters
        
        # Check that there's no _mock_agent_action method
        assert not hasattr(LLMAgent, '_mock_agent_action')
        
        # Check no references to self.mock in any methods
        for name, method in inspect.getmembers(LLMAgent, predicate=inspect.isfunction):
            if method.__qualname__.startswith('LLMAgent.'):
                source = inspect.getsource(method)
                assert 'self.mock' not in source
    
    def test_llm_narrator_has_no_mock_functionality(self):
        """Test that the LLMNarrator class has no mock functionality"""
        # Check that there's no 'mock_llm' parameter in the LLMNarrator constructor
        signature = inspect.signature(LLMNarrator.__init__)
        assert 'mock_llm' not in signature.parameters
        
        # Check that there are no mock-related methods
        assert not hasattr(LLMNarrator, '_get_mock_narrative_parts')
        assert not hasattr(LLMNarrator, '_mock_generate')
        assert not hasattr(LLMNarrator, '_get_mock_daily_summary')
        
        # Check no references to self.mock_llm in any methods
        for name, method in inspect.getmembers(LLMNarrator, predicate=inspect.isfunction):
            if method.__qualname__.startswith('LLMNarrator.'):
                source = inspect.getsource(method)
                assert 'self.mock_llm' not in source
    
    def test_simulation_initializes_handlers_correctly(self):
        """Test that Simulation correctly initializes all required handlers"""
        # Create a simulation with mocked dependencies
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
            
            # Verify no mock_llm parameter in Simulation.__init__
            signature = inspect.signature(Simulation.__init__)
            assert 'mock_llm' not in signature.parameters
            
            # Create simulation without use_llm
            sim = Simulation(config=config)
            
            # Check that interaction handlers are initialized
            assert EconomicInteractionType.ULTIMATUM in sim.interaction_handlers
            assert EconomicInteractionType.TRUST in sim.interaction_handlers
            assert EconomicInteractionType.PUBLIC_GOODS in sim.interaction_handlers
            
            # Create simulation with use_llm=True
            sim_llm = Simulation(config=config, use_llm=True)
            
            # Check that LLMAgent and LLMNarrator are initialized
            assert sim_llm.llm_agent is not None
            assert isinstance(sim_llm.narrator, LLMNarrator)
    
    def test_headless_script_runs_without_mock_llm(self):
        """Test that the headless.py script can run without the mock_llm parameter"""
        # Check that there's no mock_llm argument in parse_args
        parser = headless.parse_args()
        assert not hasattr(parser, 'mock_llm')
        
        # Test running simulation with minimal mocks
        with patch('sys.argv', ['headless.py', '--ticks', '1']), \
             patch('headless.Simulation') as mock_sim:
            
            # Set up mocks
            mock_sim_instance = mock_sim.return_value
            mock_sim_instance.initialize.return_value = None
            mock_sim_instance.step.return_value = mock_sim_instance.state
            mock_sim_instance.state.population_size = 10
            mock_sim_instance.state.active_interactions = []
            mock_sim_instance.state.completed_interactions = []
            mock_sim_instance.state.narrative_events = []
            mock_sim_instance.state.economic_indicators = {}
            
            # Run simulation
            args = headless.parse_args()
            state = headless.run_simulation(args)
            
            # Verify that Simulation was created without mock_llm parameter
            mock_sim.assert_called_once()
            call_kwargs = mock_sim.call_args.kwargs
            assert 'mock_llm' not in call_kwargs 