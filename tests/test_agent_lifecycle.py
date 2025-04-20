import pytest
from datetime import datetime, timedelta
from typing import List, Dict

from models.base import Agent, AgentType, AgentFaction, AgentPersonality, AgentNeeds, ResourceBalance, ResourceType


class TestAgentLifecycle:
    """Tests for agent lifecycle functionality"""
    
    def test_agent_creation(self):
        """Test that agents can be created with appropriate attributes"""
        # Create a basic agent
        agent = Agent(
            name="Test Agent",
            agent_type=AgentType.INDIVIDUAL,
            faction=AgentFaction.MARS_NATIVE,
            personality=AgentPersonality(
                cooperativeness=0.7,
                risk_tolerance=0.5,
                fairness_preference=0.8,
                altruism=0.6,
                rationality=0.7,
                long_term_orientation=0.6
            ),
            resources=[
                ResourceBalance(
                    resource_type=ResourceType.CREDITS,
                    amount=100.0
                ),
                ResourceBalance(
                    resource_type=ResourceType.HEALTH,
                    amount=1.0
                )
            ]
        )
        
        # Verify agent properties
        assert agent.name == "Test Agent"
        assert agent.agent_type == AgentType.INDIVIDUAL
        assert agent.faction == AgentFaction.MARS_NATIVE
        assert agent.age_days == 0
        assert agent.is_alive == True
        assert len(agent.resources) == 2
        
        # Verify personality traits
        assert agent.personality.cooperativeness == 0.7
        assert agent.personality.risk_tolerance == 0.5
        assert agent.personality.fairness_preference == 0.8
        
        # Verify default needs are all set to 1.0
        assert agent.needs.subsistence == 1.0
        assert agent.needs.security == 1.0
        assert agent.needs.social == 1.0
        assert agent.needs.esteem == 1.0
        assert agent.needs.self_actualization == 1.0
    
    def test_agent_age_calculation(self):
        """Test that an agent's age is calculated correctly"""
        # Create agent with a specific birth date
        birth_date = datetime(2993, 1, 1, 12, 0, 0)  # Set to noon on Jan 1, 2993
        
        agent = Agent(
            name="Age Test Agent",
            agent_type=AgentType.INDIVIDUAL,
            faction=AgentFaction.MARS_NATIVE,
            personality=AgentPersonality(),
            birth_date=birth_date
        )
        
        # Test different current dates
        current_date = birth_date + timedelta(days=10)
        assert agent.calculate_age(current_date) == 10
        
        current_date = birth_date + timedelta(days=365)
        assert agent.calculate_age(current_date) == 365
    
    def test_agent_death(self):
        """Test the agent death process"""
        # Create a living agent
        agent = Agent(
            name="Mortality Test Agent",
            agent_type=AgentType.INDIVIDUAL,
            faction=AgentFaction.MARS_NATIVE,
            personality=AgentPersonality(),
            birth_date=datetime(2993, 1, 1)
        )
        
        # Initially the agent should be alive
        assert agent.is_alive == True
        assert agent.death_date is None
        
        # Simulate death
        death_date = datetime(2993, 5, 15)
        agent.is_alive = False
        agent.death_date = death_date
        
        # Verify death properties
        assert agent.is_alive == False
        assert agent.death_date == death_date
        
        # Test age calculation for deceased agent
        current_date = datetime(2993, 12, 31)
        expected_age = (death_date - agent.birth_date).days
        assert agent.calculate_age(current_date) == expected_age
    
    def test_agent_with_invalid_personality(self):
        """Test that creating an agent with invalid personality traits raises an error"""
        with pytest.raises(ValueError):
            agent = Agent(
                name="Invalid Agent",
                agent_type=AgentType.INDIVIDUAL,
                faction=AgentFaction.MARS_NATIVE,
                personality=AgentPersonality(
                    cooperativeness=1.5,  # Invalid: greater than 1.0
                    risk_tolerance=0.5,
                    fairness_preference=0.8,
                    altruism=0.6,
                    rationality=0.7,
                    long_term_orientation=0.6
                )
            ) 