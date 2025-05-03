"""
Tests for simulation API routes.
"""
import unittest
from unittest.mock import patch, MagicMock

from fastapi.testclient import TestClient

from api.main import app
from api.simulation_manager import simulation_manager
from engine.simulation import SimulationEngine
from models import SimulationState, Agent

client = TestClient(app)


class TestSimulationRoutes(unittest.TestCase):
    """Test cases for simulation routes."""

    def setUp(self):
        """Set up test fixtures."""
        # Mock the simulation manager
        self.original_create_simulation = simulation_manager.create_simulation
        self.original_get_simulation = simulation_manager.get_simulation
        self.original_delete_simulation = simulation_manager.delete_simulation
        self.original_list_simulations = simulation_manager.list_simulations
        
        # Create a mock simulation
        self.mock_simulation = MagicMock(spec=SimulationEngine)
        self.mock_simulation.simulation_id = "test-123"
        self.mock_simulation.num_agents = 5
        self.mock_simulation.max_days = 30
        self.mock_simulation.state = SimulationState()

    def tearDown(self):
        """Clean up after tests."""
        # Restore original methods
        simulation_manager.create_simulation = self.original_create_simulation
        simulation_manager.get_simulation = self.original_get_simulation
        simulation_manager.delete_simulation = self.original_delete_simulation
        simulation_manager.list_simulations = self.original_list_simulations

    def test_start_simulation(self):
        """Test starting a new simulation."""
        # Mock the create_simulation method
        simulation_manager.create_simulation = MagicMock(return_value=self.mock_simulation)
        
        # Make the request
        response = client.post(
            "/simulation/start",
            json={
                "num_agents": 5,
                "max_days": 30,
                "model_name": "gemma3:4b",
                "temperature": 0.7,
                "output_dir": "output"
            }
        )
        
        # Check the response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["simulation_id"], "test-123")
        self.assertEqual(data["status"], "created")
        self.assertEqual(data["num_agents"], 5)
        self.assertEqual(data["max_days"], 30)
        
        # Verify the method was called
        simulation_manager.create_simulation.assert_called_once()

    def test_get_simulation_status(self):
        """Test getting simulation status."""
        # Mock the get_simulation method
        simulation_manager.get_simulation = MagicMock(return_value=self.mock_simulation)
        
        # Make the request
        response = client.get("/simulation/status/test-123")
        
        # Check the response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["simulation_id"], "test-123")
        self.assertEqual(data["day"], 1)  # Default day
        
        # Verify the method was called
        simulation_manager.get_simulation.assert_called_once_with("test-123")

    def test_get_simulation_detail(self):
        """Test getting detailed simulation information."""
        # Mock the get_simulation method
        simulation_manager.get_simulation = MagicMock(return_value=self.mock_simulation)
        
        # Make the request
        response = client.get("/simulation/detail/test-123")
        
        # Check the response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["simulation_id"], "test-123")
        self.assertIn("state", data)
        
        # Verify the method was called
        simulation_manager.get_simulation.assert_called_once_with("test-123")

    def test_run_simulation_day(self):
        """Test running the simulation for a day."""
        # Mock the get_simulation method
        simulation_manager.get_simulation = MagicMock(return_value=self.mock_simulation)
        
        # Mock the history attribute
        self.mock_simulation.history = MagicMock()
        self.mock_simulation.history.add = MagicMock()
        
        # Make the request
        response = client.post("/simulation/run/test-123")
        
        # Check the response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["simulation_id"], "test-123")
        
        # Verify methods were called
        simulation_manager.get_simulation.assert_called_with("test-123")
        self.mock_simulation.process_day.assert_called_once()
        self.mock_simulation.history.add.assert_called_once()

    def test_list_simulations(self):
        """Test listing all simulations."""
        # Mock the list_simulations method
        simulation_manager.list_simulations = MagicMock(return_value=["test-123", "test-456"])
        
        # Make the request
        response = client.get("/simulation/list")
        
        # Check the response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data, ["test-123", "test-456"])
        
        # Verify the method was called
        simulation_manager.list_simulations.assert_called_once()

    def test_delete_simulation(self):
        """Test deleting a simulation."""
        # Mock the delete_simulation method
        simulation_manager.delete_simulation = MagicMock(return_value=True)
        
        # Make the request
        response = client.delete("/simulation/test-123")
        
        # Check the response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        
        # Verify the method was called
        simulation_manager.delete_simulation.assert_called_once_with("test-123")

    def test_simulation_not_found(self):
        """Test error handling when a simulation is not found."""
        # Mock the get_simulation method to return None
        simulation_manager.get_simulation = MagicMock(return_value=None)
        
        # Make the request
        response = client.get("/simulation/status/not-exists")
        
        # Check the response
        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertIn("detail", data)


if __name__ == "__main__":
    unittest.main() 