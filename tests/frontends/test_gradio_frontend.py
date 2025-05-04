"""
Tests for the GradioFrontend class
"""
import os
import sys
import unittest
from unittest.mock import MagicMock, patch
import pandas as pd

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.frontends import GradioFrontend
from src.models import Agent, AgentNeeds, AgentPersonality


class TestGradioFrontend(unittest.TestCase):
    """Tests for the GradioFrontend class."""
    
    def setUp(self):
        # First patch the Theme class to avoid the error with theme initialization
        theme_patcher = patch('gradio.Theme')
        self.mock_theme = theme_patcher.start()
        self.addCleanup(theme_patcher.stop)
        
        # Mock the Gradio components to avoid actual UI rendering
        blocks_patcher = patch('gradio.Blocks')
        self.mock_blocks = blocks_patcher.start()
        self.addCleanup(blocks_patcher.stop)
        
        # Mock all the other Gradio components
        components = [
            'Row', 'Column', 'Tab', 'Tabs', 'Markdown', 'Textbox', 
            'Button', 'Slider', 'Dropdown', 'Number', 'Plot', 
            'DataFrame', 'Dataframe'
        ]
        
        self.mock_components = {}
        for component in components:
            patcher = patch(f'gradio.{component}')
            self.mock_components[component] = patcher.start()
            self.addCleanup(patcher.stop)
        
        # Now we need to make the _setup_interface method a no-op
        with patch.object(GradioFrontend, '_setup_interface', return_value=None):
            self.frontend = GradioFrontend(api_url="http://test-api", log_level="INFO")
        
        # Mock the session for API calls
        self.mock_session = MagicMock()
        self.frontend.session = self.mock_session
        
        # Create mock UI components that would normally be created in _setup_interface
        self.frontend.status_text = MagicMock()
        self.frontend.day_counter = MagicMock()
        self.frontend.agent_table = MagicMock()
        self.frontend.app = MagicMock()
    
    def test_init(self):
        """Test initialization of the GradioFrontend."""
        self.assertEqual(self.frontend.api_url, "http://test-api")
        self.assertIsNone(self.frontend.simulation_id)
        self.assertEqual(self.frontend.current_day, 0)
        self.assertFalse(self.frontend.is_running)
        self.assertFalse(self.frontend.is_paused)
    
    def test_show_status(self):
        """Test showing status updates."""
        # Call the method
        self.frontend._show_status("Test status message")
        
        # Check that the status_text update was called
        self.frontend.status_text.update.assert_called_once_with("Test status message")
    
    def test_show_error(self):
        """Test showing error messages."""
        # Call the method
        self.frontend._show_error("Test error message")
        
        # Check that the status_text update was called with ERROR prefix
        self.frontend.status_text.update.assert_called_once_with("ERROR: Test error message")
    
    def test_display_agents(self):
        """Test displaying agents."""
        # Create test agents
        agent1 = Agent(
            id="agent-1",
            name="Test Agent 1",
            credits=100.0,
            needs=AgentNeeds(food=0.8, rest=0.7, fun=0.9),
            personality=AgentPersonality(text="test personality"),
            goods=[]
        )
        
        agent2 = Agent(
            id="agent-2",
            name="Test Agent 2",
            credits=200.0,
            needs=AgentNeeds(food=0.5, rest=0.6, fun=0.4),
            personality=AgentPersonality(text="test personality"),
            goods=[]
        )
        
        # Call the method
        self.frontend._display_agents([agent1, agent2])
        
        # Check agent history
        self.assertEqual(len(self.frontend.agent_history), 2)
        self.assertEqual(len(self.frontend.agent_history["agent-1"]), 1)
        self.assertEqual(len(self.frontend.agent_history["agent-2"]), 1)
        
        # Check that the agent_table update was called
        self.frontend.agent_table.update.assert_called_once()
    
    def test_display_day_header(self):
        """Test displaying day header."""
        # Call the method
        self.frontend._display_day_header(5)
        
        # Check that the day counter was updated
        self.assertEqual(self.frontend.current_day, 5)
        self.assertEqual(self.frontend.day_history, [5])
        self.frontend.day_counter.update.assert_called_once_with("Day 5")
    
    def test_process_day(self):
        """Test processing a simulation day."""
        # Create mock states with proper nested attributes
        prev_state = MagicMock()
        prev_state.agents = []
        prev_state.day = 4
        
        # Create mock market for the state
        mock_market = MagicMock()
        mock_market.listings = []
        
        # Create mock songs for the state
        mock_songs = MagicMock()
        mock_songs.genres = set()
        
        state = MagicMock()
        state.agents = []
        state.day = 5
        state.market = mock_market
        state.actions = []
        state.songs = mock_songs
        state.count_inventions = MagicMock(return_value=0)
        
        # Call the method
        self.frontend._process_day(5, prev_state, state)
        
        # Check simulation history
        self.assertEqual(len(self.frontend.simulation_history), 1)
        self.assertEqual(self.frontend.simulation_history[0]['day'], 5)
    
    @patch('frontends.gradio.GradioFrontend._reset_data')
    @patch('threading.Thread')
    def test_start_simulation_handler(self, mock_thread, mock_reset_data):
        """Test the start simulation handler."""
        # Call the method
        result = self.frontend._start_simulation_handler(
            num_agents=5,
            max_days=10,
            starting_credits=100,
            model_name="test-model",
            temperature=0.7,
            output_dir="output"
        )
        
        # Check that the data was reset
        mock_reset_data.assert_called_once()
        
        # Check that a thread was started
        mock_thread.assert_called_once()
        thread_instance = mock_thread.return_value
        thread_instance.daemon = True
        thread_instance.start.assert_called_once()
        
        # Check the result
        self.assertEqual(result, "Simulation started")
        self.assertTrue(self.frontend.is_running)
    
    def test_stop_simulation_handler(self):
        """Test the stop simulation handler."""
        # Set the simulation as running
        self.frontend.is_running = True
        
        # Call the method
        result = self.frontend._stop_simulation_handler()
        
        # Check the result
        self.assertEqual(result, "Simulation stopped")
        self.assertFalse(self.frontend.is_running)
    
    def test_reset_data(self):
        """Test resetting data."""
        # Add some test data
        self.frontend.simulation_history = ["test"]
        self.frontend.agent_history["agent-1"] = ["test"]
        self.frontend.day_history = [1, 2, 3]
        self.frontend.current_day = 3
        
        # Call the method
        self.frontend._reset_data()
        
        # Check that data was reset
        self.assertEqual(self.frontend.simulation_history, [])
        self.assertEqual(dict(self.frontend.agent_history), {})
        self.assertEqual(self.frontend.day_history, [])
        self.assertEqual(self.frontend.current_day, 0)
    
    @patch('plotly.express.line')
    @patch('plotly.express.pie')
    def test_select_agent_handler(self, mock_pie, mock_line):
        """Test the agent selection handler."""
        # Mock figures
        mock_line.return_value = MagicMock()
        mock_pie.return_value = MagicMock()
        
        # Add test data to agent history
        self.frontend.agent_history["agent-1"] = [
            {
                'day': 1,
                'name': 'Test Agent',
                'credits': 100.0,
                'needs': {'food': 0.8, 'rest': 0.7, 'fun': 0.9},
                'goods': [],
                'is_alive': True
            },
            {
                'day': 2,
                'name': 'Test Agent',
                'credits': 150.0,
                'needs': {'food': 0.9, 'rest': 0.8, 'fun': 0.7},
                'goods': [],
                'is_alive': True
            }
        ]
        
        # Add test data to action history
        self.frontend.action_history["agent-1"] = [
            {
                'day': 1,
                'agent_id': 'agent-1',
                'agent_name': 'Test Agent',
                'action_type': 'WORK',
                'reasoning': 'Need credits',
                'extras': {}
            }
        ]
        
        # Call the method
        status, needs_fig, credits_fig, actions_fig = self.frontend._select_agent_handler("agent-1")
        
        # Check the results
        self.assertIn("Test Agent", status)
        self.assertIn("Credits: 150", status)
        self.assertIn("Alive", status)
        
        # Check that the plots were created
        mock_line.assert_called()
        mock_pie.assert_called_once()
    
    def test_select_agent_handler_unknown_agent(self):
        """Test agent selection with unknown agent."""
        # Call the method with unknown agent
        result = self.frontend._select_agent_handler("unknown-agent")
        
        # Check the result
        self.assertEqual(result[0], "Agent not found")
        self.assertIsNone(result[1])
        self.assertIsNone(result[2])
        self.assertIsNone(result[3])
    
    def test_select_narrative_day_handler(self):
        """Test the narrative day selection handler."""
        # Add test narrative data
        self.frontend.narrative_history[1] = {
            'title': 'Test Narrative',
            'content': 'This is a test narrative.'
        }
        
        # Call the method
        title, content, word_cloud = self.frontend._select_narrative_day_handler(1)
        
        # Check the results
        self.assertEqual(title, 'Test Narrative')
        self.assertEqual(content, 'This is a test narrative.')
    
    def test_select_narrative_day_handler_unknown_day(self):
        """Test narrative day selection with unknown day."""
        # Call the method with unknown day
        title, content, word_cloud = self.frontend._select_narrative_day_handler(999)
        
        # Check the results
        self.assertEqual(title, "No narrative for day 999")
        self.assertEqual(content, "No content available")
    
    def test_select_thoughts_agent_handler(self):
        """Test the thoughts agent selection handler."""
        # Add test thought data
        self.frontend.action_history["agent-1"] = [
            {
                'day': 1,
                'agent_id': 'agent-1',
                'agent_name': 'Test Agent',
                'action_type': 'THINK',
                'reasoning': 'Thinking',
                'extras': {'thoughts': 'Test thought'}
            }
        ]
        
        # Call the method
        thoughts_df, themes_plot = self.frontend._select_thoughts_agent_handler("agent-1")
        
        # Check the results
        self.assertIsInstance(thoughts_df, pd.DataFrame)
        self.assertEqual(len(thoughts_df), 1)
        if len(thoughts_df) > 0:
            self.assertEqual(thoughts_df.iloc[0]['Thought'], 'Test thought')
    
    def test_select_thoughts_agent_handler_no_thoughts(self):
        """Test thoughts agent selection with no thoughts."""
        # Add test action data with no thoughts
        self.frontend.action_history["agent-1"] = [
            {
                'day': 1,
                'agent_id': 'agent-1',
                'agent_name': 'Test Agent',
                'action_type': 'WORK',
                'reasoning': 'Working',
                'extras': {}
            }
        ]
        
        # Call the method
        thoughts_df, themes_plot = self.frontend._select_thoughts_agent_handler("agent-1")
        
        # Check the results
        self.assertIsInstance(thoughts_df, pd.DataFrame)
        self.assertEqual(len(thoughts_df), 0)
    
    def test_launch(self):
        """Test launching the Gradio interface."""
        # Call the method
        self.frontend.launch(share=True)
        
        # Check that the launch method was called
        self.frontend.app.launch.assert_called_once_with(share=True)


if __name__ == "__main__":
    unittest.main() 