"""
Tests for the FrontendBase class
"""
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.frontends import FrontendBase
from src.models import SimulationState


class TestFrontend(FrontendBase):
    """Concrete implementation of FrontendBase for testing."""
    
    def __init__(self, api_url="http://test-api", log_level="INFO"):
        super().__init__(api_url, log_level)
        self.status_messages = []
        self.error_messages = []
        self.displayed_agents = []
        self.day_headers = []
        self.processed_days = []
        self.simulation_end_called = False
    
    def _show_status(self, message):
        self.status_messages.append(message)
    
    def _show_error(self, message):
        self.error_messages.append(message)
    
    def _display_agents(self, agents):
        self.displayed_agents.extend(agents)
    
    def _display_day_header(self, day):
        self.day_headers.append(day)
    
    def _process_day(self, day, prev_state, state):
        self.processed_days.append((day, prev_state, state))
    
    def _display_simulation_end(self, max_days):
        self.simulation_end_called = True


class TestFrontendBase(unittest.TestCase):
    """Tests for the FrontendBase class."""
    
    def setUp(self):
        self.frontend = TestFrontend()
        self.mock_session = MagicMock()
        self.frontend.session = self.mock_session
    
    def test_init(self):
        """Test initialization of the frontend."""
        self.assertEqual(self.frontend.api_url, "http://test-api")
        self.assertIsNone(self.frontend.simulation_id)
    
    @patch('requests.Session')
    def test_create_simulation(self, mock_session_class):
        """Test creating a simulation."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {"simulation_id": "test-123"}
        self.mock_session.post.return_value = mock_response
        
        # Call method
        simulation_id = self.frontend.create_simulation(
            num_agents=5,
            max_days=10,
            starting_credits=100
        )
        
        # Check session call
        self.mock_session.post.assert_called_once()
        args, kwargs = self.mock_session.post.call_args
        self.assertEqual(args[0], "http://test-api/simulation/start")
        self.assertEqual(kwargs["json"]["num_agents"], 5)
        self.assertEqual(kwargs["json"]["max_days"], 10)
        self.assertEqual(kwargs["json"]["starting_credits"], 100)
        
        # Check result
        self.assertEqual(simulation_id, "test-123")
        self.assertEqual(self.frontend.simulation_id, "test-123")
        
        # Check status message
        self.assertIn("Creating simulation", self.frontend.status_messages[0])
    
    def test_get_simulation_detail_no_simulation(self):
        """Test getting simulation detail without an active simulation."""
        with self.assertRaises(ValueError):
            self.frontend.get_simulation_detail()
    
    def test_get_simulation_detail(self):
        """Test getting simulation detail."""
        # Setup simulation ID and mock response
        self.frontend.simulation_id = "test-123"
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "state": {
                "day": 1,
                "agents": [],
                "market": {"listings": []},
                "actions": [],
            }
        }
        self.mock_session.get.return_value = mock_response
        
        # Call method
        state = self.frontend.get_simulation_detail()
        
        # Check session call
        self.mock_session.get.assert_called_once_with(
            "http://test-api/simulation/detail/test-123"
        )
        
        # Check result is a SimulationState
        self.assertIsInstance(state, SimulationState)
    
    def test_run_simulation_day_no_simulation(self):
        """Test running a simulation day without an active simulation."""
        with self.assertRaises(ValueError):
            self.frontend.run_simulation_day()
    
    def test_run_simulation_day(self):
        """Test running a simulation day."""
        # Setup simulation ID and mock responses
        self.frontend.simulation_id = "test-123"
        
        mock_run_response = MagicMock()
        mock_detail_response = MagicMock()
        mock_detail_response.json.return_value = {
            "state": {
                "day": 2,
                "agents": [],
                "market": {"listings": []},
                "actions": [],
            }
        }
        
        self.mock_session.post.return_value = mock_run_response
        self.mock_session.get.return_value = mock_detail_response
        
        # Call method
        state = self.frontend.run_simulation_day()
        
        # Check session calls
        self.mock_session.post.assert_called_once_with(
            "http://test-api/simulation/run/test-123?days=1"
        )
        self.mock_session.get.assert_called_once()
        
        # Check result is a SimulationState
        self.assertIsInstance(state, SimulationState)
    
    def test_add_agent_no_simulation(self):
        """Test adding an agent without an active simulation."""
        with self.assertRaises(ValueError):
            self.frontend.add_agent(name="Test Agent")
    
    def test_add_agent(self):
        """Test adding an agent."""
        # Setup simulation ID and mock response
        self.frontend.simulation_id = "test-123"
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "agent_id": "agent-123",
            "name": "Test Agent"
        }
        self.mock_session.post.return_value = mock_response
        
        # Call method
        result = self.frontend.add_agent(
            name="Test Agent",
            personality="curious, inventive",
            starting_credits=200
        )
        
        # Check session call
        self.mock_session.post.assert_called_once()
        args, kwargs = self.mock_session.post.call_args
        self.assertEqual(args[0], "http://test-api/agent/add")
        self.assertEqual(kwargs["json"]["simulation_id"], "test-123")
        self.assertEqual(kwargs["json"]["name"], "Test Agent")
        self.assertEqual(kwargs["json"]["personality"], "curious, inventive")
        self.assertEqual(kwargs["json"]["starting_credits"], 200)
        
        # Check result
        self.assertEqual(result["agent_id"], "agent-123")
        self.assertEqual(result["name"], "Test Agent")
    
    def test_kill_agent_no_simulation(self):
        """Test killing an agent without an active simulation."""
        with self.assertRaises(ValueError):
            self.frontend.kill_agent("agent-123")
    
    def test_kill_agent(self):
        """Test killing an agent."""
        # Setup simulation ID and mock response
        self.frontend.simulation_id = "test-123"
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "success": True,
            "agent_id": "agent-123"
        }
        self.mock_session.delete.return_value = mock_response
        
        # Call method
        result = self.frontend.kill_agent("agent-123")
        
        # Check session call
        self.mock_session.delete.assert_called_once()
        args, kwargs = self.mock_session.delete.call_args
        self.assertEqual(args[0], "http://test-api/agent/kill")
        self.assertEqual(kwargs["params"]["simulation_id"], "test-123")
        self.assertEqual(kwargs["params"]["agent_id"], "agent-123")
        
        # Check result
        self.assertEqual(result["success"], True)
        self.assertEqual(result["agent_id"], "agent-123")
    
    def test_get_agent_status_no_simulation(self):
        """Test getting agent status without an active simulation."""
        with self.assertRaises(ValueError):
            self.frontend.get_agent_status("agent-123")
    
    def test_get_agent_status(self):
        """Test getting agent status."""
        # Setup simulation ID and mock response
        self.frontend.simulation_id = "test-123"
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": "agent-123",
            "name": "Test Agent",
            "credits": 150.0,
            "is_alive": True
        }
        self.mock_session.get.return_value = mock_response
        
        # Call method
        result = self.frontend.get_agent_status("agent-123")
        
        # Check session call
        self.mock_session.get.assert_called_once()
        args, kwargs = self.mock_session.get.call_args
        self.assertEqual(args[0], "http://test-api/agent/status")
        self.assertEqual(kwargs["params"]["simulation_id"], "test-123")
        self.assertEqual(kwargs["params"]["agent_id"], "agent-123")
        
        # Check result
        self.assertEqual(result["id"], "agent-123")
        self.assertEqual(result["name"], "Test Agent")
    
    def test_update_agent_no_simulation(self):
        """Test updating an agent without an active simulation."""
        with self.assertRaises(ValueError):
            self.frontend.update_agent("agent-123", {"credits": 300})
    
    def test_update_agent(self):
        """Test updating an agent."""
        # Setup simulation ID and mock response
        self.frontend.simulation_id = "test-123"
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "agent_id": "agent-123",
            "name": "Test Agent",
            "updated": ["credits"]
        }
        self.mock_session.put.return_value = mock_response
        
        # Call method
        result = self.frontend.update_agent("agent-123", {"credits": 300})
        
        # Check session call
        self.mock_session.put.assert_called_once()
        args, kwargs = self.mock_session.put.call_args
        self.assertEqual(args[0], "http://test-api/agent/update")
        self.assertEqual(kwargs["json"]["simulation_id"], "test-123")
        self.assertEqual(kwargs["json"]["agent_id"], "agent-123")
        self.assertEqual(kwargs["json"]["updates"], {"credits": 300})
        
        # Check result
        self.assertEqual(result["agent_id"], "agent-123")
        self.assertEqual(result["updated"], ["credits"])
    
    @patch.object(TestFrontend, 'create_simulation')
    @patch.object(TestFrontend, 'get_simulation_detail')
    @patch.object(TestFrontend, 'run_simulation_day')
    def test_run_simulation(self, mock_run_day, mock_get_detail, mock_create):
        """Test running a complete simulation."""
        # Setup mocks
        mock_create.return_value = "test-123"
        
        mock_initial_state = MagicMock(spec=SimulationState)
        mock_initial_state.agents = []
        
        mock_day1_state = MagicMock(spec=SimulationState)
        mock_day1_state.agents = []
        
        mock_get_detail.side_effect = [mock_initial_state, mock_initial_state, mock_day1_state]
        mock_run_day.return_value = mock_day1_state
        
        # Call method
        self.frontend.run_simulation(
            num_agents=5,
            max_days=1,
            model_name="test-model"
        )
        
        # Check method calls - use call() to validate the actual call
        # Get the actual call that was made
        call_args, call_kwargs = mock_create.call_args
        
        # Check that the values match, regardless of whether they were passed as positional or keyword arguments
        self.assertEqual(call_kwargs.get('num_agents', call_args[0] if call_args else None), 5)
        self.assertEqual(call_kwargs.get('max_days', call_args[1] if len(call_args) > 1 else None), 1)
        self.assertEqual(call_kwargs.get('model_name', None), 'test-model')
        
        # Should be called twice (initial + start of day 1)
        self.assertEqual(mock_get_detail.call_count, 2)
        
        # Should be called once (for day 1)
        mock_run_day.assert_called_once()
        
        # Check frontend state
        self.assertEqual(len(self.frontend.displayed_agents), 0)
        self.assertEqual(len(self.frontend.day_headers), 1)
        self.assertEqual(self.frontend.day_headers[0], 1)
        self.assertEqual(len(self.frontend.processed_days), 1)
        self.assertTrue(self.frontend.simulation_end_called)


if __name__ == "__main__":
    unittest.main() 