"""
Tests for agent API routes.
"""
import unittest
from unittest.mock import patch, MagicMock

from fastapi.testclient import TestClient

from api.main import app
from api.simulation_manager import simulation_manager
from engine.simulation import SimulationEngine
from models import SimulationState, Agent, AgentPersonality, AgentNeeds

client = TestClient(app)


class TestAgentRoutes(unittest.TestCase):
    """Test cases for agent routes."""

    def setUp(self):
        """Set up test fixtures."""
        # Mock the simulation manager
        self.original_get_simulation = simulation_manager.get_simulation
        self.original_get_agent = simulation_manager.get_agent
        self.original_create_agent = simulation_manager.create_agent
        self.original_kill_agent = simulation_manager.kill_agent
        self.original_update_agent = simulation_manager.update_agent
        
        # Create a mock simulation
        self.mock_simulation = MagicMock(spec=SimulationEngine)
        self.mock_simulation.simulation_id = "test-123"
        self.mock_simulation.state = SimulationState()
        
        # Create a mock agent
        self.mock_agent = Agent(
            id="agent-123",
            name="Test Agent",
            personality=AgentPersonality(text="Friendly and helpful"),
            needs=AgentNeeds(),
            credits=100
        )

    def tearDown(self):
        """Clean up after tests."""
        # Restore original methods
        simulation_manager.get_simulation = self.original_get_simulation
        simulation_manager.get_agent = self.original_get_agent
        simulation_manager.create_agent = self.original_create_agent
        simulation_manager.kill_agent = self.original_kill_agent
        simulation_manager.update_agent = self.original_update_agent

    def test_add_agent(self):
        """Test adding a new agent."""
        # Mock the get_simulation method
        simulation_manager.get_simulation = MagicMock(return_value=self.mock_simulation)
        
        # Mock the create_agent method
        simulation_manager.create_agent = MagicMock(return_value=self.mock_agent)
        
        # Make the request
        response = client.post(
            "/agent/add",
            json={
                "simulation_id": "test-123",
                "name": "Test Agent",
                "personality": "Friendly and helpful",
                "starting_credits": 100
            }
        )
        
        # Check the response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["agent_id"], "agent-123")
        self.assertEqual(data["name"], "Test Agent")
        self.assertEqual(data["status"], "created")
        
        # Verify methods were called
        simulation_manager.get_simulation.assert_called_once_with("test-123")
        simulation_manager.create_agent.assert_called_once_with(
            "test-123", 
            name="Test Agent", 
            personality_str="Friendly and helpful", 
            starting_credits=100
        )

    def test_kill_agent(self):
        """Test killing an agent."""
        # Mock the get_agent method
        simulation_manager.get_agent = MagicMock(return_value=self.mock_agent)
        
        # Mock the kill_agent method
        simulation_manager.kill_agent = MagicMock(return_value=True)
        
        # Make the request
        # For DELETE request, use query parameters or content for request body
        response = client.delete(
            "/agent/kill",
            params={
                "simulation_id": "test-123",
                "agent_id": "agent-123"
            }
        )
        
        # Check the response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("killed", data["message"])
        
        # Verify methods were called
        simulation_manager.get_agent.assert_called_once_with("test-123", agent_id="agent-123", agent_name=None)
        simulation_manager.kill_agent.assert_called_once_with("test-123", self.mock_agent)

    def test_get_agent_status(self):
        """Test getting agent status."""
        # Mock the get_agent method
        simulation_manager.get_agent = MagicMock(return_value=self.mock_agent)
        
        # Make the request
        response = client.get("/agent/status?simulation_id=test-123&agent_id=agent-123")
        
        # Check the response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["agent"]["id"], "agent-123")
        self.assertEqual(data["agent"]["name"], "Test Agent")
        self.assertEqual(data["status"], "active")
        
        # Verify the method was called
        simulation_manager.get_agent.assert_called_once_with("test-123", agent_id="agent-123", agent_name=None)

    def test_update_agent(self):
        """Test updating an agent."""
        # Mock the get_agent method
        simulation_manager.get_agent = MagicMock(return_value=self.mock_agent)
        
        # Mock the update_agent method
        simulation_manager.update_agent = MagicMock(return_value=True)
        
        # Make the request
        response = client.put(
            "/agent/update",
            json={
                "simulation_id": "test-123",
                "agent_id": "agent-123",
                "updates": {
                    "credits": 200,
                    "needs": {
                        "food": 0.8,
                        "rest": 0.9
                    }
                }
            }
        )
        
        # Check the response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["agent"]["id"], "agent-123")
        self.assertEqual(data["status"], "updated")
        
        # Verify methods were called
        simulation_manager.get_agent.assert_called_once_with("test-123", agent_id="agent-123")
        simulation_manager.update_agent.assert_called_once_with(
            "test-123", 
            self.mock_agent, 
            {"credits": 200, "needs": {"food": 0.8, "rest": 0.9}}
        )

    def test_agent_not_found(self):
        """Test error handling when an agent is not found."""
        # Mock the get_agent method to return None
        simulation_manager.get_agent = MagicMock(return_value=None)
        
        # Make the request
        response = client.get("/agent/status?simulation_id=test-123&agent_id=not-exists")
        
        # Check the response
        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertIn("detail", data)
        
        # Verify the method was called
        simulation_manager.get_agent.assert_called_once_with("test-123", agent_id="not-exists", agent_name=None)

    def test_simulation_not_found(self):
        """Test error handling when a simulation is not found."""
        # Mock the get_simulation method to return None
        simulation_manager.get_simulation = MagicMock(return_value=None)
        
        # Make the request
        response = client.post(
            "/agent/add",
            json={
                "simulation_id": "not-exists",
                "name": "Test Agent"
            }
        )
        
        # Check the response
        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertIn("detail", data)
        
        # Verify the method was called
        simulation_manager.get_simulation.assert_called_once_with("not-exists")


if __name__ == "__main__":
    unittest.main() 