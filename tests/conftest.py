"""
Pytest configuration for ProtoNomia tests.
This module contains common fixtures and configuration for the test suite.
"""
import os
import logging
import random
import pytest
from datetime import datetime

from models.base import (
    Agent, AgentType, AgentFaction, AgentPersonality, ResourceBalance, 
    ResourceType, SimulationConfig
)

# Configure logging for tests
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Set up deterministic randomness for tests
@pytest.fixture(scope="session")
def fixed_seed():
    """Set a fixed random seed for tests"""
    random.seed(42)
    return 42


@pytest.fixture
def standard_config():
    """Create a standard simulation configuration for tests"""
    return SimulationConfig(
        name="Test Simulation",
        seed=42,
        start_date=datetime(2993, 1, 1),
        time_scale=1.0,
        initial_population=10,
        max_population=100,
        resource_scarcity=0.5,
        technological_level=0.8,
        narrative_verbosity=3
    )


@pytest.fixture
def mock_agent_factory():
    """Factory fixture for creating test agents"""
    def _create_agent(
        name=None,
        agent_type=AgentType.INDIVIDUAL,
        faction=AgentFaction.MARS_NATIVE,
        personality=None,
        resources=None
    ):
        """Create a test agent with the given parameters"""
        if name is None:
            name = f"Test Agent {random.randint(1000, 9999)}"
        
        if personality is None:
            personality = AgentPersonality(
                cooperativeness=0.5,
                risk_tolerance=0.5,
                fairness_preference=0.5,
                altruism=0.5,
                rationality=0.5,
                long_term_orientation=0.5
            )
        
        if resources is None:
            resources = [
                ResourceBalance(
                    resource_type=ResourceType.CREDITS,
                    amount=100.0
                ),
                ResourceBalance(
                    resource_type=ResourceType.HEALTH,
                    amount=1.0
                )
            ]
        
        return Agent(
            name=name,
            agent_type=agent_type,
            faction=faction,
            personality=personality,
            resources=resources
        )
    
    return _create_agent


@pytest.fixture
def skip_ollama_tests():
    """Skip tests that require Ollama if env var is set"""
    return os.environ.get("SKIP_OLLAMA_TESTS", "false").lower() in ("true", "1", "yes")


@pytest.fixture
def mock_ollama_response():
    """Mock Ollama response for testing"""
    class MockResponse:
        def __init__(self, text="Test response", status_code=200):
            self.text = text
            self.status_code = status_code
        
        def json(self):
            return {"response": self.text}
        
        def raise_for_status(self):
            if self.status_code >= 400:
                raise Exception(f"HTTP Error: {self.status_code}")
    
    return MockResponse 