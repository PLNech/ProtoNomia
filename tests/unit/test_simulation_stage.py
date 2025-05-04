"""
Tests for simulation stages and night activity functionality.
"""
import unittest
from unittest.mock import patch, MagicMock

from src.models.simulation import (
    SimulationStage, Good, GoodType
)
from src.engine.simulation import SimulationEngine


class TestSimulationStages(unittest.TestCase):
    """Test cases for the simulation stage functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a simulation engine with mocked LLM
        with patch("engine.simulation.LLMAgent") as mock_llm:
            self.engine = SimulationEngine(num_agents=2, max_days=2)
            self.engine.setup_initial_state()
    
    def test_initial_stage(self):
        """Test that simulation starts in INITIALIZATION stage."""
        self.assertEqual(self.engine.state.current_stage, SimulationStage.INITIALIZATION)
        self.assertIsNone(self.engine.state.current_agent_id)
    
    def test_stage_transitions_day(self):
        """Test stage transitions during process_day."""
        # Mock agent day action to avoid LLM calls
        with patch.object(self.engine, "_process_agent_day_action") as mock_process:
            mock_process.return_value = MagicMock()
            
            # Start processing the day
            self.engine._process_day_stages()
            
            # After day stages, we should be in NARRATOR stage
            self.assertEqual(self.engine.state.current_stage, SimulationStage.NARRATOR)
    
    def test_next_agent_for_day(self):
        """Test get_next_agent_for_day method."""
        state = self.engine.state
        
        # Initially, all agents need actions
        next_agent = state.get_next_agent_for_day()
        self.assertIsNotNone(next_agent)
        
        # Mark this agent as having acted
        mock_action = MagicMock()
        mock_action.day = state.day
        state.add_action(next_agent, mock_action)
        
        # Get next agent
        next_agent2 = state.get_next_agent_for_day()
        
        # Should be a different agent
        if next_agent2:
            self.assertNotEqual(next_agent.id, next_agent2.id)
        
        # Mark all agents as having acted
        for agent in state.agents:
            if not any(a.agent.id == agent.id for a in state.today_actions):
                state.add_action(agent, mock_action)
        
        # Now no agent should need an action
        self.assertIsNone(state.get_next_agent_for_day())


class TestNightActivities(unittest.TestCase):
    """Test cases for the night activities functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a simulation engine with mocked LLM
        with patch("engine.simulation.LLMAgent") as mock_llm:
            self.engine = SimulationEngine(num_agents=2, max_days=2)
            self.engine.setup_initial_state()
            
            # Add food items to the first agent for dinner testing
            self.agent = self.engine.state.agents[0]
            self.agent.goods.append(Good(type=GoodType.FOOD, name="Low Quality Food", quality=0.2))
            self.agent.goods.append(Good(type=GoodType.FOOD, name="High Quality Food", quality=0.6))
            
            # Reduce agent's food needs
            self.agent.needs.food = 0.3
    
    def test_dinner_consumption(self):
        """Test that agents consume food items during dinner."""
        initial_food = self.agent.needs.food
        initial_goods_count = len(self.agent.goods)
        
        # Process dinner for this agent
        self.engine._process_agent_dinner(self.agent)
        
        # Food level should increase
        self.assertGreater(self.agent.needs.food, initial_food)
        
        # Should have consumed at least one food item
        self.assertLess(len(self.agent.goods), initial_goods_count)
        
        # Should be a night activity record for dinner
        self.assertTrue(any(
            activity.agent_id == self.agent.id and activity.dinner_consumed 
            for activity in self.engine.state.today_night_activities
        ))
    
    def test_night_activities(self):
        """Test night activities generation."""
        # Process night activities for this agent
        self.engine._process_agent_night_activities(self.agent)
        
        # Should be a night activity record
        night_activities = [
            activity for activity in self.engine.state.today_night_activities
            if activity.agent_id == self.agent.id and not activity.dinner_consumed
        ]
        
        self.assertEqual(len(night_activities), 1)
        
        # The night activity should have letters
        activity = night_activities[0]
        if len(self.engine.state.agents) > 1:  # Only test letters if we have other agents
            self.assertTrue(len(activity.letters) > 0)
    
    def test_letter_creation(self):
        """Test letter creation and structure in night activities."""
        # Process night activities for this agent
        self.engine._process_agent_night_activities(self.agent)
        
        # Get the night activity
        night_activities = [
            activity for activity in self.engine.state.today_night_activities
            if activity.agent_id == self.agent.id and not activity.dinner_consumed
        ]
        
        # Skip test if no other agents to receive letters
        if len(self.engine.state.agents) <= 1:
            self.skipTest("Need at least 2 agents to test letter functionality")
            
        # Get the first letter
        activity = night_activities[0]
        self.assertTrue(len(activity.letters) > 0)
        
        letter = activity.letters[0]
        # Check letter structure
        self.assertIsNotNone(letter.recipient_name)
        self.assertIsNotNone(letter.title)
        self.assertIsNotNone(letter.message)
        
        # Verify recipient exists
        recipient_exists = any(
            agent.name == letter.recipient_name for agent in self.engine.state.agents
        )
        self.assertTrue(recipient_exists, f"Recipient '{letter.recipient_name}' does not exist")
    
    def test_night_phase(self):
        """Test the complete night phase processing."""
        # Process the night phase
        self.engine.process_night()
        
        # Stage should be reset to INITIALIZATION
        self.assertEqual(self.engine.state.current_stage, SimulationStage.INITIALIZATION)
        
        # All agents should have night activities
        agent_ids = {agent.id for agent in self.engine.state.agents}
        activity_agent_ids = {activity.agent_id for activity in self.engine.state.today_night_activities}
        
        self.assertEqual(agent_ids, activity_agent_ids)


if __name__ == "__main__":
    unittest.main() 