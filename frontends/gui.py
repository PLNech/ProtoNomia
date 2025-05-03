"""
ProtoNomia Gradio Frontend
This module provides a web-based data visualization interface for the ProtoNomia API.
"""
import argparse
import logging
import os
import sys
import requests
import gradio as gr
from collections import Counter, defaultdict
from typing import Dict, Any, List, Optional, Tuple
import time
import json

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from rich.console import Console

from frontends.frontend_base import FrontendBase
from models import SimulationState, Agent, ActionType, Good, GoodType

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Rich console for terminal output
console = Console()

# Cyberpunk color scheme
CYBERPUNK_COLORS = {
    "background": "#0a0a0f",
    "card": "#16161e",
    "text": "#e0e0ff",
    "accent": "#ff3366",
    "secondary": "#00ccff",
    "success": "#33ff99",
    "warning": "#ffcc00",
    "error": "#ff3333",
    "neon_pink": "#ff00ff",
    "neon_green": "#00ff99",
    "neon_blue": "#00ccff",
    "neon_yellow": "#ffff00",
    "grid": "#22222f"
}

# Action type colors for consistent visualization
ACTION_COLORS = {
    ActionType.REST: "#8c52ff",      # Purple
    ActionType.WORK: "#33ff99",      # Green
    ActionType.BUY: "#00ccff",       # Blue
    ActionType.SELL: "#ffcc00",      # Yellow
    ActionType.HARVEST: "#ff9933",   # Orange
    ActionType.CRAFT: "#ff3366",     # Pink
    ActionType.THINK: "#ffffff",     # White
    ActionType.COMPOSE: "#ff66cc",   # Light Pink
}

# Goods type colors
GOOD_COLORS = {
    GoodType.FOOD: "#33ff99",  # Green
    GoodType.REST: "#8c52ff",  # Purple
    GoodType.FUN: "#ff3366",   # Pink
}


class GradioFrontend(FrontendBase):
    """
    Gradio-based web frontend for the ProtoNomia API.
    Provides real-time visualization of simulation data.
    """
    
    def __init__(
        self,
        api_url: str = "http://127.0.0.1:8000",
        log_level: str = "INFO",
        auto_refresh: bool = True,
        refresh_interval: int = 3
    ):
        """
        Initialize the Gradio frontend.
        
        Args:
            api_url: URL of the ProtoNomia API
            log_level: Logging level
            auto_refresh: Whether to automatically refresh data
            refresh_interval: Time between auto-refreshes in seconds
        """
        super().__init__(api_url, log_level)
        
        # Auto-refresh settings
        self.auto_refresh = auto_refresh
        self.refresh_interval = refresh_interval
        
        # Data storage for historical tracking
        self.simulation_history = []
        self.agent_history = defaultdict(list)
        self.day_history = []
        self.action_history = defaultdict(list)
        self.market_history = []
        self.invention_history = []
        self.song_history = []
        self.narrative_history = {}
        
        # Simulation status flags
        self.is_running = False
        self.is_paused = False
        self.current_day = 0
        
        # Currently selected agent for detailed view
        self.selected_agent_id = None
        
        # Initialize Gradio interface
        self._setup_interface()
    
    def _show_status(self, message: str) -> None:
        """
        Display a status message in the terminal and update status in UI.
        
        Args:
            message: The status message to display
        """
        # Log to terminal
        console.print(f"[cyan]{message}[/cyan]")
        
        # Update UI if available
        if hasattr(self, 'status_text') and self.status_text:
            try:
                self.status_text.value = message
            except Exception as e:
                console.print(f"[red]Error updating status: {e}[/red]")
        
        # Log to file
        self.logger.info(message)
    
    def _show_error(self, message: str) -> None:
        """
        Display an error message in the terminal and update UI.
        
        Args:
            message: The error message to display
        """
        # Log to terminal
        console.print(f"[red]{message}[/red]")
        
        # Update UI if available
        if hasattr(self, 'status_text') and self.status_text:
            try:
                self.status_text.value = f"ERROR: {message}"
            except Exception as e:
                console.print(f"[red]Error updating error status: {e}[/red]")
        
        # Log to file
        self.logger.error(message)
    
    def _display_agents(self, agents: List[Agent]) -> None:
        """
        Store agent data for display.
        
        Args:
            agents: List of agents to display
        """
        try:
            # Store agent data in history
            for agent in agents:
                self.agent_history[agent.id].append({
                    'day': self.current_day,
                    'name': agent.name,
                    'credits': agent.credits,
                    'needs': {
                        'food': agent.needs.food,
                        'rest': agent.needs.rest,
                        'fun': agent.needs.fun
                    },
                    'goods': [
                        {'name': good.name, 'type': good.type, 'quality': good.quality}
                        for good in agent.goods
                    ],
                    'is_alive': agent.is_alive
                })
            
            # Update agent statistics
            if hasattr(self, 'agent_table') and self.agent_table:
                try:
                    self.agent_table.value = self._create_agent_dataframe(agents)
                except Exception as e:
                    console.print(f"[red]Error updating agent table: {e}[/red]")
                    self.logger.error(f"Error updating agent table: {e}")
        except Exception as e:
            console.print(f"[red]Error processing agents data: {e}[/red]")
            self.logger.error(f"Error processing agents data: {e}")
    
    def _display_day_header(self, day: int) -> None:
        """
        Update day counter in UI.
        
        Args:
            day: The current day number
        """
        self.current_day = day
        self.day_history.append(day)
        
        # Update day counter in UI
        if hasattr(self, 'day_counter') and self.day_counter:
            try:
                self.day_counter.value = f"Day {day}"
            except Exception as e:
                console.print(f"[red]Error updating day counter: {e}[/red]")
    
    def _process_day(self, day: int, prev_state: SimulationState, state: SimulationState) -> None:
        """
        Process and store data for the current day.
        
        Args:
            day: The current day number
            prev_state: The state before the day
            state: The state after the day
        """
        # Store full state for historical tracking
        self.simulation_history.append({
            'day': day,
            'population': len(state.agents),
            'market_listings': len(state.market.listings),
            'inventions': state.count_inventions(),
            'songs': len(state.songs.genres),
            'total_credits': sum(agent.credits for agent in state.agents),
            'state': state
        })
        
        # Process actions for this day
        action_logs = [log for log in state.actions if log.day == day]
        
        # Store actions in history
        for log in action_logs:
            agent = log.agent
            action = log.action
            
            self.action_history[agent.id].append({
                'day': day,
                'agent_id': agent.id,
                'agent_name': agent.name,
                'action_type': action.type,
                'reasoning': action.reasoning,
                'extras': action.extras
            })
        
        # Check for narrative data
        narrative_file = os.path.join("output", f"day_{day}_narrative.txt")
        if os.path.exists(narrative_file):
            with open(narrative_file, 'r') as f:
                lines = f.readlines()
                title = lines[0].strip("# \n")
                content = "".join(lines[2:])
                self.narrative_history[day] = {
                    'title': title,
                    'content': content
                }
        
        # Update UI elements with new data
        self._update_ui_elements(state)
    
    def _display_simulation_end(self, max_days: int) -> None:
        """
        Display a message at the end of the simulation.
        
        Args:
            max_days: The maximum number of days the simulation ran for
        """
        self._show_status(f"Simulation completed after {max_days} days")
        
        # Update UI with final state
        if hasattr(self, 'status_text') and self.status_text:
            try:
                self.status_text.value = f"Simulation completed after {max_days} days"
            except Exception as e:
                console.print(f"[red]Error updating status text at simulation end: {e}[/red]")
    
    def _get_ollama_models(self) -> List[str]:
        """Get a list of available Ollama models."""
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=2)
            if response.status_code == 200:
                names = [model["name"] for model in response.json().get("models", [])]
            else:
                logger.warning(f"Failed to get Ollama models, status code: {response.status_code}")
                names = []
        except requests.RequestException as e:
            logger.warning(f"Error connecting to Ollama: {e}")
            names = ["gemma:2b", "llama3:8b", "mistral:7b"]  # Fallback models
        
        try:
            response = requests.get("https://ollama.com/library", timeout=3)
            popular = []
            # Parse the HTML response to extract popular models from Ollama's library
            try:
                html_content = response.text
                # Find the repository grid section
                repo_section_start = html_content.find('id="repo"')
                if repo_section_start != -1:
                    # Extract model names from the grid items
                    popular = []
                    current_pos = repo_section_start
                    
                    # Look for model entries in the HTML
                    while True:
                        model_title_start = html_content.find('x-test-model-title=""', current_pos)
                        if model_title_start == -1:
                            break
                        
                        # Find the model name
                        title_start = html_content.find('title="', model_title_start)
                        if title_start != -1:
                            title_start += 7  # Length of 'title="'
                            title_end = html_content.find('"', title_start)
                            if title_end != -1:
                                model_name = html_content[title_start:title_end]
                                popular.append(model_name)
                        
                        current_pos = model_title_start + 1
                
                logger.info(f"Found {len(popular)} popular models from Ollama library")
            except Exception as e:
                logger.error(f"Error parsing Ollama library: {e}")
                popular = []
        except requests.RequestException as e:
            logger.warning(f"Error fetching Ollama library: {e}")
            popular = []
        
        # If no models were found, provide some default models
        if not names and not popular:
            names = ["gemma:2b", "llama3:8b", "mistral:7b"]
            
        # Sort names to put popular models first
        if names:
            names = sorted(names, key=lambda x: x.split(":")[1] if ":" in x else x)
        if popular:
            popular = sorted(popular, key=lambda x: x.split(":")[1] if ":" in x else x)
            
        all_models = popular + [name for name in names if name not in popular]
        
        # Ensure we have at least some models available
        if not all_models:
            all_models = ["gemma:2b", "llama3:8b", "mistral:7b"]
            
        return all_models
    
    def _setup_interface(self) -> None:
        """Set up the Gradio interface with all visualization components."""
        
        # Define theme
        theme = gr.Theme.from_hub("earneleh/paris")
        theme.set(
            # background_fill=CYBERPUNK_COLORS["background"],
            block_background_fill=CYBERPUNK_COLORS["card"],
            block_label_text_color=CYBERPUNK_COLORS["accent"],
            block_title_text_color=CYBERPUNK_COLORS["accent"],
            border_color_primary=CYBERPUNK_COLORS["secondary"],
            button_primary_background_fill=CYBERPUNK_COLORS["accent"],
            button_primary_text_color=CYBERPUNK_COLORS["text"],
            button_secondary_background_fill=CYBERPUNK_COLORS["card"],
            button_secondary_text_color=CYBERPUNK_COLORS["text"],
            color_accent=CYBERPUNK_COLORS["accent"],
            input_background_fill=CYBERPUNK_COLORS["background"],
            input_border_color=CYBERPUNK_COLORS["secondary"],
            input_placeholder_color="#aaaacc",
            # input_text_color=CYBERPUNK_COLORS["text"],
            panel_background_fill=CYBERPUNK_COLORS["card"],
            # text_color=CYBERPUNK_COLORS["text"],
            body_text_color=CYBERPUNK_COLORS["text"],
            body_text_color_subdued="#bbbbdd",
            stat_background_fill=CYBERPUNK_COLORS["card"],
        )
        
        with gr.Blocks(theme=theme, title="ProtoNomia Simulation Dashboard") as app:
            # Header
            with gr.Row():
                gr.Markdown("# ProtoNomia Mars Settlement Dashboard")
            
            # Status and control bar
            with gr.Row():
                with gr.Column(scale=1):
                    self.day_counter = gr.Textbox(
                        label="Current Day",
                        value="Day 0",
                        interactive=False
                    )
                
                with gr.Column(scale=3):
                    self.status_text = gr.Textbox(
                        label="Status",
                        value="Ready to start simulation",
                        interactive=False
                    )
                
                with gr.Column(scale=2):
                    with gr.Row():
                        start_btn = gr.Button(
                            "Start Simulation",
                            variant="primary"
                        )
                        stop_btn = gr.Button(
                            "Stop",
                            variant="stop"
                        )
            
            # Configuration tab
            with gr.Tab("Configuration"):
                with gr.Row():
                    with gr.Column():
                        num_agents = gr.Slider(
                            label="Number of Agents",
                            minimum=1,
                            maximum=20,
                            value=5,
                            step=1
                        )
                        max_days = gr.Slider(
                            label="Max Days",
                            minimum=1,
                            maximum=100,
                            value=30,
                            step=1
                        )
                        starting_credits = gr.Number(
                            label="Starting Credits (blank for random)",
                            value=None
                        )
                    
                    with gr.Column():
                        model_name = gr.Dropdown(
                            label="LLM Model",
                            choices=self._get_ollama_models(),
                            value=self._get_ollama_models()[0] if self._get_ollama_models() else None
                        )
                        temperature = gr.Slider(
                            label="Temperature",
                            minimum=0.1,
                            maximum=1.0,
                            value=0.7,
                            step=0.1
                        )
                        output_dir = gr.Textbox(
                            label="Output Directory",
                            value="output"
                        )
            
            # Setup tabs for different view modes
            with gr.Tabs():
                # Overview Tab
                with gr.Tab("Overview"):
                    with gr.Row():
                        with gr.Column():
                            population_plot = gr.Plot(
                                label="Population Over Time",
                                show_label=True
                            )
                        
                        with gr.Column():
                            actions_plot = gr.Plot(
                                label="Actions Distribution",
                                show_label=True
                            )
                    
                    with gr.Row():
                        with gr.Column():
                            economy_plot = gr.Plot(
                                label="Economy Stats",
                                show_label=True
                            )
                        
                        with gr.Column():
                            creation_plot = gr.Plot(
                                label="Creative Output",
                                show_label=True
                            )
                
                # Agents Tab
                with gr.Tab("Agents"):
                    with gr.Row():
                        # Agent selection dropdown to be populated dynamically
                        agent_selector = gr.Dropdown(
                            label="Select Agent",
                            choices=[],
                            value=None,
                            scale=1
                        )
                        
                        agent_status = gr.Textbox(
                            label="Status",
                            value="",
                            interactive=False,
                            scale=2
                        )
                    
                    with gr.Row():
                        self.agent_table = gr.DataFrame(
                            label="Agents Overview",
                            headers=["ID", "Name", "Credits", "Food", "Rest", "Fun", "Goods", "Status"],
                            interactive=False
                        )
                    
                    with gr.Row():
                        with gr.Column():
                            agent_needs_plot = gr.Plot(
                                label="Agent Needs Over Time",
                                show_label=True
                            )
                        
                        with gr.Column():
                            agent_credits_plot = gr.Plot(
                                label="Agent Credits Over Time",
                                show_label=True
                            )
                    
                    with gr.Row():
                        agent_actions_plot = gr.Plot(
                            label="Agent Actions",
                            show_label=True
                        )
                
                # Market Tab
                with gr.Tab("Market"):
                    with gr.Row():
                        with gr.Column():
                            market_listings_plot = gr.Plot(
                                label="Market Listings by Type",
                                show_label=True
                            )
                        
                        with gr.Column():
                            market_quality_plot = gr.Plot(
                                label="Goods Quality Distribution",
                                show_label=True
                            )
                    
                    with gr.Row():
                        market_listings_table = gr.DataFrame(
                            label="Active Market Listings",
                            headers=["ID", "Seller", "Good", "Type", "Quality", "Price", "Listed On Day"],
                            interactive=False
                        )
                
                # Creations Tab
                with gr.Tab("Creations"):
                    with gr.Row():
                        with gr.Column():
                            inventions_plot = gr.Plot(
                                label="Inventions Over Time",
                                show_label=True
                            )
                        
                        with gr.Column():
                            songs_plot = gr.Plot(
                                label="Songs by Genre",
                                show_label=True
                            )
                    
                    with gr.Row():
                        song_bpm_plot = gr.Plot(
                            label="Song BPM Distribution",
                            show_label=True
                        )
                
                # Narrative Tab
                with gr.Tab("Narrative"):
                    with gr.Row():
                        narrative_day_selector = gr.Slider(
                            label="Day",
                            minimum=1,
                            maximum=1,
                            value=1,
                            step=1
                        )
                    
                    with gr.Row():
                        narrative_title = gr.Textbox(
                            label="Title",
                            value="",
                            interactive=False
                        )
                    
                    with gr.Row():
                        narrative_content = gr.Markdown(
                            label="Content",
                            value=""
                        )
                    
                    with gr.Row():
                        word_cloud = gr.Plot(
                            label="Thought Themes",
                            show_label=True
                        )
                
                # Thoughts Tab (for agent thoughts analysis)
                with gr.Tab("Thoughts"):
                    with gr.Row():
                        thoughts_agent_selector = gr.Dropdown(
                            label="Select Agent",
                            choices=[],
                            value=None
                        )
                    
                    with gr.Row():
                        with gr.Column():
                            thoughts_list = gr.Dataframe(
                                label="Agent Thoughts",
                                headers=["Day", "Agent", "Thought"],
                                interactive=False
                            )
                        
                        with gr.Column():
                            thoughts_themes_plot = gr.Plot(
                                label="Common Themes in Thoughts",
                                show_label=True
                            )
            
            # Define event handlers
            start_btn.click(
                fn=self._start_simulation_handler,
                inputs=[num_agents, max_days, starting_credits, model_name, temperature, output_dir],
                outputs=[self.status_text]
            )
            
            stop_btn.click(
                fn=self._stop_simulation_handler,
                outputs=[self.status_text]
            )
            
            agent_selector.change(
                fn=self._select_agent_handler,
                inputs=[agent_selector],
                outputs=[agent_status, agent_needs_plot, agent_credits_plot, agent_actions_plot]
            )
            
            narrative_day_selector.change(
                fn=self._select_narrative_day_handler,
                inputs=[narrative_day_selector],
                outputs=[narrative_title, narrative_content, word_cloud]
            )
            
            thoughts_agent_selector.change(
                fn=self._select_thoughts_agent_handler,
                inputs=[thoughts_agent_selector],
                outputs=[thoughts_list, thoughts_themes_plot]
            )
        
        # Store the app for later use
        self.app = app
    
    def _update_ui_elements(self, state: SimulationState) -> None:
        """
        Update all UI elements with fresh data.
        
        Args:
            state: Current simulation state
        """
        # This method will be called after each day to update the UI
        # Delegate to specific update methods for each section
        pass
    
    def _create_agent_dataframe(self, agents: List[Agent]) -> pd.DataFrame:
        """
        Create a dataframe for the agents table.
        
        Args:
            agents: List of agents
            
        Returns:
            pd.DataFrame: Dataframe with agent data
        """
        data = []
        for agent in agents:
            goods_count = len(agent.goods)
            goods_text = f"{goods_count} items" if goods_count > 0 else "None"
            
            data.append([
                agent.id,
                agent.name,
                f"{agent.credits:.0f}",
                f"{agent.needs.food:.2f}",
                f"{agent.needs.rest:.2f}",
                f"{agent.needs.fun:.2f}",
                goods_text,
                "Alive" if agent.is_alive else "Dead"
            ])
        
        return pd.DataFrame(
            data,
            columns=["ID", "Name", "Credits", "Food", "Rest", "Fun", "Goods", "Status"]
        )
    
    def _start_simulation_handler(
        self,
        num_agents: int,
        max_days: int,
        starting_credits: Optional[float],
        model_name: str,
        temperature: float,
        output_dir: str
    ) -> str:
        """
        Handle the start simulation button click.
        
        Args:
            num_agents: Number of agents
            max_days: Maximum days to run
            starting_credits: Starting credits (optional)
            model_name: LLM model name
            temperature: Model temperature
            output_dir: Output directory
            
        Returns:
            str: Status message
        """
        try:
            # Clear any existing data
            self._reset_data()
            
            # Check if the API is running
            try:
                response = requests.get(f"{self.api_url}/health", timeout=2)
                response.raise_for_status()
                self._show_status("Connected to API server")
            except requests.RequestException:
                self._show_status("API server not detected. Starting API server...")
                self._start_api_server()
            
            # Start the simulation
            self.is_running = True
            
            # Run in a separate thread to keep UI responsive
            import threading
            
            def run_sim():
                try:
                    self.run_simulation(
                        num_agents=num_agents,
                        max_days=max_days,
                        starting_credits=starting_credits,
                        model_name=model_name,
                        temperature=temperature,
                        output_dir=output_dir
                    )
                except Exception as e:
                    self._show_error(f"Error in simulation: {e}")
                finally:
                    self.is_running = False
            
            # Start the thread
            thread = threading.Thread(target=run_sim)
            thread.daemon = True
            thread.start()
            
            return "Simulation started"
        except Exception as e:
            self._show_error(f"Failed to start simulation: {e}")
            return f"Error: {str(e)}"
    
    def _stop_simulation_handler(self) -> str:
        """
        Handle the stop simulation button click.
        
        Returns:
            str: Status message
        """
        self.is_running = False
        return "Simulation stopped"
    
    def _reset_data(self) -> None:
        """Reset all stored data for a new simulation."""
        self.simulation_history = []
        self.agent_history = defaultdict(list)
        self.day_history = []
        self.action_history = defaultdict(list)
        self.market_history = []
        self.invention_history = []
        self.song_history = []
        self.narrative_history = {}
        self.current_day = 0
    
    def _select_agent_handler(self, agent_id: str) -> Tuple[str, gr.Plot, gr.Plot, gr.Plot]:
        """
        Handle agent selection for detailed view.
        
        Args:
            agent_id: ID of the selected agent
            
        Returns:
            Tuple with agent status and plot objects
        """
        self.selected_agent_id = agent_id
        
        # Get agent data
        agent_data = self.agent_history.get(agent_id, [])
        if not agent_data:
            return "Agent not found", None, None, None
        
        # Latest agent data
        latest = agent_data[-1]
        
        # Create agent status text
        status = f"Agent: {latest['name']}\n"
        status += f"Credits: {latest['credits']:.0f}\n"
        status += f"Status: {'Alive' if latest['is_alive'] else 'Dead'}\n"
        status += f"Needs: Food: {latest['needs']['food']:.2f}, Rest: {latest['needs']['rest']:.2f}, Fun: {latest['needs']['fun']:.2f}\n"
        status += f"Goods: {len(latest['goods'])} items"
        
        # Create agent needs plot
        needs_df = pd.DataFrame([
            {
                'Day': d['day'],
                'Food': d['needs']['food'],
                'Rest': d['needs']['rest'],
                'Fun': d['needs']['fun']
            }
            for d in agent_data
        ])
        
        needs_fig = px.line(
            needs_df,
            x='Day',
            y=['Food', 'Rest', 'Fun'],
            labels={'value': 'Need Level', 'variable': 'Need Type'},
            title=f"{latest['name']}'s Needs Over Time",
            color_discrete_map={
                'Food': GOOD_COLORS[GoodType.FOOD],
                'Rest': GOOD_COLORS[GoodType.REST],
                'Fun': GOOD_COLORS[GoodType.FUN]
            }
        )
        needs_fig.update_layout(
            template="plotly_dark",
            paper_bgcolor=CYBERPUNK_COLORS["card"],
            plot_bgcolor=CYBERPUNK_COLORS["background"],
            font=dict(color=CYBERPUNK_COLORS["text"]),
            xaxis=dict(gridcolor=CYBERPUNK_COLORS["grid"]),
            yaxis=dict(gridcolor=CYBERPUNK_COLORS["grid"])
        )
        
        # Create agent credits plot
        credits_df = pd.DataFrame([
            {'Day': d['day'], 'Credits': d['credits']}
            for d in agent_data
        ])
        
        credits_fig = px.line(
            credits_df,
            x='Day',
            y='Credits',
            title=f"{latest['name']}'s Credits Over Time",
            color_discrete_sequence=[CYBERPUNK_COLORS["neon_green"]]
        )
        credits_fig.update_layout(
            template="plotly_dark",
            paper_bgcolor=CYBERPUNK_COLORS["card"],
            plot_bgcolor=CYBERPUNK_COLORS["background"],
            font=dict(color=CYBERPUNK_COLORS["text"]),
            xaxis=dict(gridcolor=CYBERPUNK_COLORS["grid"]),
            yaxis=dict(gridcolor=CYBERPUNK_COLORS["grid"])
        )
        
        # Create agent actions plot
        actions = self.action_history.get(agent_id, [])
        if actions:
            action_counts = Counter([a['action_type'] for a in actions])
            actions_fig = px.pie(
                names=list(action_counts.keys()),
                values=list(action_counts.values()),
                title=f"{latest['name']}'s Actions",
                color=list(action_counts.keys()),
                color_discrete_map={str(k): ACTION_COLORS.get(k, "#ffffff") for k in action_counts.keys()}
            )
            actions_fig.update_layout(
                template="plotly_dark",
                paper_bgcolor=CYBERPUNK_COLORS["card"],
                plot_bgcolor=CYBERPUNK_COLORS["background"],
                font=dict(color=CYBERPUNK_COLORS["text"])
            )
        else:
            actions_fig = go.Figure()
            actions_fig.update_layout(
                title=f"No actions for {latest['name']}",
                template="plotly_dark",
                paper_bgcolor=CYBERPUNK_COLORS["card"],
                plot_bgcolor=CYBERPUNK_COLORS["background"],
                font=dict(color=CYBERPUNK_COLORS["text"])
            )
        
        return status, needs_fig, credits_fig, actions_fig
    
    def _select_narrative_day_handler(self, day: int) -> Tuple[str, str, gr.Plot]:
        """
        Handle narrative day selection.
        
        Args:
            day: Selected day
            
        Returns:
            Tuple with narrative title, content, and word cloud
        """
        narrative = self.narrative_history.get(day, {})
        title = narrative.get('title', f"No narrative for day {day}")
        content = narrative.get('content', "No content available")
        
        # Generate word cloud from thoughts on this day
        # In a real implementation, we would analyze thoughts from all agents on this day
        word_cloud_fig = go.Figure()
        word_cloud_fig.update_layout(
            title="Thought Themes (Word Cloud not implemented)",
            template="plotly_dark",
            paper_bgcolor=CYBERPUNK_COLORS["card"],
            plot_bgcolor=CYBERPUNK_COLORS["background"],
            font=dict(color=CYBERPUNK_COLORS["text"])
        )
        
        return title, content, word_cloud_fig
    
    def _select_thoughts_agent_handler(self, agent_id: str) -> Tuple[pd.DataFrame, gr.Plot]:
        """
        Handle thoughts agent selection.
        
        Args:
            agent_id: ID of the selected agent
            
        Returns:
            Tuple with thoughts dataframe and themes plot
        """
        # Collect thoughts for this agent
        thoughts = []
        for action in self.action_history.get(agent_id, []):
            if action['action_type'] == ActionType.THINK:
                thought = action['extras'].get('thoughts', "")
                if thought:
                    thoughts.append({
                        'Day': action['day'],
                        'Agent': action['agent_name'],
                        'Thought': thought
                    })
        
        # Create dataframe
        thoughts_df = pd.DataFrame(thoughts) if thoughts else pd.DataFrame(columns=['Day', 'Agent', 'Thought'])
        
        # Create themes plot (this would be more sophisticated in a real implementation)
        themes_fig = go.Figure()
        themes_fig.update_layout(
            title="Thought Theme Analysis (Not implemented)",
            template="plotly_dark",
            paper_bgcolor=CYBERPUNK_COLORS["card"],
            plot_bgcolor=CYBERPUNK_COLORS["background"],
            font=dict(color=CYBERPUNK_COLORS["text"])
        )
        
        return thoughts_df, themes_fig
    
    def launch(self, share: bool = False) -> None:
        """
        Launch the Gradio interface.
        
        Args:
            share: Whether to create a public link
        """
        self.app.launch(share=share)

    def _start_api_server(self):
        """Start the API server if it's not already running"""
        import subprocess
        import os

        try:
            # Get the directory containing this script
            script_dir = os.path.dirname(os.path.abspath(__file__))
            # Get the project root directory (one level up)
            root_dir = os.path.dirname(script_dir)

            # Start the API server in a separate process
            process = subprocess.Popen(
                ["python", "-m", "api.main"],
                cwd=root_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True
            )
            
            self._show_status(f"API server started with PID {process.pid}. Waiting for it to initialize...")
            
            # Wait for API to become available
            max_retries = 15
            retry_delay = 1
            for i in range(max_retries):
                try:
                    response = requests.get(f"{self.api_url}/health", timeout=2)
                    if response.status_code == 200:
                        self._show_status("API server is now available")
                        return
                except requests.RequestException:
                    if i < max_retries - 1:
                        self._show_status(f"Waiting for API server to start (attempt {i+1}/{max_retries})...")
                        time.sleep(retry_delay)
                        retry_delay = min(retry_delay * 1.5, 3)  # Exponential backoff with cap
            
            self._show_error("Failed to connect to API server after multiple attempts")
            
            # Try to check if the process is still running and capture any error output
            if process.poll() is None:
                self._show_status("API server process is still running but not responding")
            else:
                stderr = process.stderr.read().decode('utf-8')
                if stderr:
                    self._show_error(f"API server process terminated with error: {stderr}")
                else:
                    self._show_error("API server process terminated without error messages")
                    
        except Exception as e:
            self._show_error(f"Failed to start API server: {e}")

    def run_simulation(
        self,
        num_agents: int,
        max_days: int,
        **kwargs
    ) -> None:
        """
        Run the simulation from start to finish.
        
        Args:
            num_agents: Number of agents
            max_days: Max days to run
            **kwargs: Additional arguments for create_simulation
        """
        try:
            # Create the simulation
            self.create_simulation(num_agents, max_days, **kwargs)
            
            # Get the initial state
            state = self.get_simulation_detail()
            prev_state = state
            
            # Store agent data
            self._display_agents(state.agents)
            
            # Run the simulation day by day
            for day in range(1, max_days + 1):
                if not self.is_running:
                    self._show_status("Simulation stopped by user")
                    break
                
                # Display the day header
                self._display_day_header(day)
                
                # Run the day
                state = self.run_simulation_day()
                
                # Process the day
                self._process_day(day, prev_state, state)
                
                # Update prev_state for the next iteration
                prev_state = state
                
                # Check if all agents are dead
                if all(not agent.is_alive for agent in state.agents):
                    self._show_status("All agents have died. Simulation ended.")
                    break
            
            # Display simulation end
            self._display_simulation_end(day)
        except Exception as e:
            self._show_error(f"Error in simulation: {e}")
            import traceback
            traceback.print_exc()
            raise

    def get_simulation_detail(self) -> SimulationState:
        """
        Get detailed information about the current simulation.
        
        Returns:
            SimulationState: The simulation state
        """
        if not self.simulation_id:
            self._show_error("No active simulation")
            raise ValueError("No active simulation")
        
        url = f"{self.api_url}/simulation/detail/{self.simulation_id}"
        
        # Make the request
        try:
            self._show_status(f"Getting simulation details...")
            response = self.session.get(url)
            response.raise_for_status()
            
            # Parse the response
            result = response.json()
            state_data = result["state"]
            
            # Debug log the state data
            if self.logger.level <= logging.DEBUG:
                self.logger.debug(f"Raw state data: {json.dumps(state_data, indent=2)}")
            
            # Validate agent data before conversion 
            self._validate_agent_data(state_data.get("agents", []))
            
            try:
                # Convert to SimulationState
                return SimulationState.model_validate(state_data)
            except Exception as e:
                self.logger.error(f"Model validation error: {e}")
                # More detailed logging to identify the issue
                if "agents" in state_data:
                    for i, agent in enumerate(state_data["agents"]):
                        try:
                            Agent.model_validate(agent)
                        except Exception as ae:
                            self.logger.error(f"Agent {i} validation error: {ae}, data: {agent}")
                raise
        except requests.RequestException as e:
            self._show_error(f"Failed to get simulation detail: {e}")
            raise

    def _validate_agent_data(self, agents_data: List[Dict[str, Any]]) -> None:
        """
        Validate and fix agent data before model validation.
        
        Args:
            agents_data: List of agent data dictionaries
        """
        if not agents_data:
            return
        
        for agent in agents_data:
            # Ensure agent has a name
            if "name" not in agent or not agent["name"]:
                agent["name"] = f"Agent-{agent.get('id', 'Unknown')}"
            
            # Ensure needs is a dictionary, not a string or None
            if "needs" not in agent or not isinstance(agent["needs"], dict):
                agent["needs"] = {"food": 0.5, "rest": 0.5, "fun": 0.5}
            
            # Ensure goods is a list
            if "goods" not in agent or not isinstance(agent["goods"], list):
                agent["goods"] = []
            
            # Validate each good
            if "goods" in agent and isinstance(agent["goods"], list):
                for i, good in enumerate(agent["goods"]):
                    if not isinstance(good, dict):
                        agent["goods"][i] = {"type": "FOOD", "quality": 0.5, "name": "Unknown Item"}
                    elif "type" not in good:
                        good["type"] = "FOOD"
                    elif "quality" not in good:
                        good["quality"] = 0.5


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="ProtoNomia Gradio Frontend")
    parser.add_argument(
        "-u", "--api-url",
        type=str,
        default="http://127.0.0.1:8000",
        help="URL of the ProtoNomia API"
    )
    parser.add_argument(
        "-l", "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level"
    )
    parser.add_argument(
        "-s", "--share",
        action="store_true",
        help="Create a public link"
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    
    # Set up logging
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    # Create and launch the frontend
    frontend = GradioFrontend(api_url=args.api_url, log_level=args.log_level)
    frontend.launch(share=args.share)
