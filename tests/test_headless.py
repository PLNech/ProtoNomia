"""
Tests for the headless.py script.
"""
import pytest
import sys
import os
import tempfile
import json
from unittest.mock import patch

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import headless


class TestHeadlessScript:
    """Tests for the headless.py script"""
    
    def test_parse_args_defaults(self):
        """Test that argument parsing works with defaults"""
        # Mock sys.argv for the test
        with patch('sys.argv', ['headless.py']):
            args = headless.parse_args()
            
            # Check default values
            assert args.initial_population == 20
            assert args.max_population == 100
            assert args.ticks == 100
            assert args.timeout is None
            assert args.resource_scarcity == 0.5
            assert args.terra_mars_trade_ratio == 0.6
            assert args.interactions == ['trust_game', 'ultimatum_game']
            assert args.birth_rate == 0.01
            assert args.death_rate == 0.005
            assert args.verbosity == 3
            assert args.use_llm is False
    
    def test_parse_args_custom(self):
        """Test that argument parsing works with custom values"""
        # Mock sys.argv for the test
        with patch('sys.argv', [
            'headless.py',
            '--initial-population', '50',
            '--max-population', '200',
            '--ticks', '50',
            '--timeout', '30',
            '--resource-scarcity', '0.3',
            '--terra-mars-trade-ratio', '0.8',
            '--interactions', 'trust_game',
            '--birth-rate', '0.02',
            '--death-rate', '0.006',
            '--verbosity', '4',
            '--use-llm',
            '--model-name', 'foo:42b'
        ]):
            args = headless.parse_args()
            
            # Check custom values
            assert args.initial_population == 50
            assert args.max_population == 200
            assert args.ticks == 50
            assert args.timeout == 30
            assert args.resource_scarcity == 0.3
            assert args.terra_mars_trade_ratio == 0.8
            assert args.interactions == ['trust_game']
            assert args.birth_rate == 0.02
            assert args.death_rate == 0.006
            assert args.verbosity == 4
            assert args.use_llm is True
            assert args.model_name == 'foo:42b'
    
    def test_timeout_functionality(self):
        """Test that the timeout parameter works correctly"""
        # Create args with a very short timeout
        with patch('sys.argv', ['headless.py', '--timeout', '0.1', '--ticks', '1000']):
            args = headless.parse_args()
            
            # Patch the Simulation class to avoid actual initialization
            with patch('core.simulation.Simulation') as mock_sim:
                # Set up mocks
                mock_sim_instance = mock_sim.return_value
                mock_sim_instance.initialize.return_value = None
                mock_sim_instance.step.return_value = mock_sim_instance.state
                
                # Run with a very short timeout
                result = headless.run_simulation(args)
                
                # The simulation should have exited early due to timeout
                assert mock_sim_instance.step.call_count < args.ticks
    
    @pytest.mark.skipif(True, reason="Integration test that requires implemented modules")
    def test_output_file_generation(self):
        """Test that an output file is generated correctly"""
        # Create a temporary file for output
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as temp_file:
            output_path = temp_file.name
        
        try:
            # Run with minimal ticks and output to the temp file
            with patch('sys.argv', [
                'headless.py',
                '--ticks', '2',
                '--initial-population', '3',
                '--output', output_path
            ]):
                args = headless.parse_args()
                
                # Patch the Simulation class to avoid actual initialization
                with patch('headless.Simulation') as mock_sim:
                    # Set up mocks
                    mock_sim_instance = mock_sim.return_value
                    mock_sim_instance.initialize.return_value = None
                    mock_sim_instance.step.return_value = mock_sim_instance.state
                    mock_sim_instance.state.population_size = 3
                    mock_sim_instance.state.active_interactions = []
                    mock_sim_instance.state.completed_interactions = []
                    mock_sim_instance.state.narrative_events = []
                    mock_sim_instance.state.economic_indicators = {}
                    
                    # Run simulation
                    headless.run_simulation(args)
                    
                    # Check that the output file exists and contains valid JSON
                    assert os.path.exists(output_path)
                    with open(output_path, 'r') as f:
                        data = json.load(f)
                        
                        # Check basic structure
                        assert 'config' in data
                        assert 'metrics' in data
                        assert 'final_state' in data
                        
                        # Check metrics has correct number of entries
                        assert len(data['metrics']) == 2  # One for each tick
        finally:
            # Clean up
            if os.path.exists(output_path):
                os.unlink(output_path) 