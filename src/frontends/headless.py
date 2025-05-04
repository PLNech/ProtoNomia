"""
ProtoNomia Headless Frontend
This module provides a CLI frontend for the ProtoNomia API.
"""
import argparse
import logging
import os
import sys
import time
import signal
from typing import Optional, List
import requests

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.scribe import Scribe
from src.models import SimulationState, Agent, AgentActionResponse, ActionType, AgentAction
from src.frontends.frontend_base import FrontendBase

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create scribe for rich output
scribe = Scribe()


class HeadlessFrontend(FrontendBase):
    """
    Headless CLI frontend for the ProtoNomia API.
    Provides a terminal interface with rich output.
    """
    
    def __init__(
        self,
        api_url: str = "http://127.0.0.1:8000",
        log_level: str = "INFO",
        simulation_id: Optional[str] = None
    ):
        """
        Initialize the headless frontend.
        
        Args:
            api_url: URL of the ProtoNomia API
            log_level: Logging level
            simulation_id: Optional ID for an existing simulation
        """
        super().__init__(api_url, log_level)
        self.current_status = None
        self.simulation_id = simulation_id
        self.is_running = True
        
        # Set up signal handler for graceful shutdown
        signal.signal(signal.SIGINT, self._handle_sigint)
    
    def _handle_sigint(self, sig, frame):
        """Handle SIGINT (Ctrl+C) by saving state and exiting gracefully."""
        print("\n")
        self._show_status("Received interrupt signal, saving state and shutting down...")
        
        # Set running flag to false to stop any ongoing simulation
        self.is_running = False
        
        # Try to save state if we have an active simulation
        if self.simulation_id:
            try:
                # Make a request to ensure state is saved
                url = f"{self.api_url}/simulation/detail/{self.simulation_id}"
                self.session.get(url)
                self._show_status(f"Simulation state saved for ID: {self.simulation_id}")
            except Exception as e:
                self._show_error(f"Error saving state: {e}")
        
        self._show_status("Exiting gracefully")
        sys.exit(0)
    
    def _show_status(self, message: str) -> None:
        """
        Display a status message using the scribe.
        
        Args:
            message: The status message to display
        """
        # Use the scribe status to show loading indicators
        if self.current_status:
            self.current_status.stop()
            
        self.current_status = scribe.status(message)
        logger.info(message)
    
    def _show_error(self, message: str) -> None:
        """
        Display an error message.
        
        Args:
            message: The error message to display
        """
        if self.current_status:
            self.current_status.stop()
            self.current_status = None
            
        logger.error(message)
    
    def get_simulation_status(self):
        """
        Get the current status of the simulation.
        
        Returns:
            The simulation status response
        """
        if not self.simulation_id:
            self._show_error("No active simulation")
            raise ValueError("No active simulation")
            
        url = f"{self.api_url}/simulation/status/{self.simulation_id}"
        
        # Make the request
        try:
            response = self.session.get(url)
            response.raise_for_status()
            
            # Parse the response
            return response.json()
        except requests.RequestException as e:
            self._show_error(f"Failed to get simulation status: {e}")
            raise
    
    def _display_agents(self, agents: List[Agent]) -> None:
        """
        Display information about agents using the scribe.
        
        Args:
            agents: List of agents to display
        """
        for agent in agents:
            scribe.agent_created(agent)
    
    def _display_day_header(self, day: int) -> None:
        """
        Display a header for the current day.
        
        Args:
            day: The current day number
        """
        # Stop any active status indicator before printing the header
        if self.current_status:
            self.current_status.stop()
            self.current_status = None
            
        scribe.day_header(day)
    
    def _display_stage_info(self, status_response) -> None:
        """
        Display information about the current simulation stage.
        
        Args:
            status_response: The simulation status response
        """
        stage = status_response.get("current_stage", "initialization")
        agent_name = status_response.get("current_agent_name")
        
        if stage == "initialization":
            scribe.print("[bold cyan]Initializing simulation...[/bold cyan]")
        elif stage == "agent_day":
            if agent_name:
                scribe.print(f"[bold cyan]Waiting for {agent_name}'s day action...[/bold cyan]")
            else:
                scribe.print("[bold cyan]Processing day actions...[/bold cyan]")
        elif stage == "narrator":
            scribe.print("[bold cyan]Generating daily narrative...[/bold cyan]")
        elif stage == "agent_night":
            if agent_name:
                scribe.print(f"[bold cyan]Processing night activities for {agent_name}...[/bold cyan]")
            else:
                scribe.print("[bold cyan]Processing night activities...[/bold cyan]")
    
    def _process_day(self, day: int, prev_state: SimulationState, state: SimulationState) -> None:
        """
        Process and display events for the current day.
        
        Args:
            day: The current day number
            prev_state: The state before the day
            state: The state after the day
        """
        # Extract and display actions for this day
        action_logs = [log for log in state.actions if log.day == day]
        
        # Keep track of agents who died
        agents_alive_before = {agent.id: agent for agent in prev_state.agents}
        agents_alive_after = {agent.id: agent for agent in state.agents}
        
        # Stop any active status indicator before printing actions
        if self.current_status:
            self.current_status.stop()
            self.current_status = None
        
        # Print agent actions
        for log in action_logs:
            agent_id = log.agent_id
            agent = next((a for a in prev_state.agents if a.id == agent_id), None)
            
            if agent:
                # Display agent action choice with detailed info
                scribe.print(f"[cyan]Agent {agent.name} chose action {log.type}[/cyan]")
                
                # Display reasoning if available
                if log.reasoning:
                    scribe.print(f"[dim cyan]Reasoning: {log.reasoning}[/dim cyan]")
                
                # Display action details
                self._display_agent_action(agent, log)
                
                # Show the updated agent status
                updated_agent = next((a for a in state.agents if a.id == agent_id), None)
                if updated_agent:
                    # Display the consequences based on action type
                    self._display_action_consequences(agent, updated_agent, log)
        
        # Check for dead agents
        for agent_id, agent in agents_alive_before.items():
            if agent_id not in agents_alive_after:
                self._display_agent_death(agent.name)
        
        # Get and display narrative
        output_dir = "output"  # Default value
        narrative_file = os.path.join(output_dir, f"day_{day}_narrative.txt")
        if os.path.exists(narrative_file):
            with open(narrative_file, 'r') as f:
                lines = f.readlines()
                title = lines[0].strip("# \n")
                content = "".join(lines[2:])
                self._display_narrative(title, content, state)
        
        # Display night activities
        self._display_night_activities(state)
    
    def _display_agent_action(self, agent: Agent, action_log: AgentAction) -> None:
        """
        Display an agent action.
        
        Args:
            agent: The agent performing the action
            action_log: The action log entry
        """
        action_type = action_log.type
        extras = action_log.extras or {}
        
        # Create an action response to use with existing scribe functions
        action_response = AgentActionResponse(
            type=action_type,
            extras=extras,
            reasoning=action_log.reasoning
        )
        
        # Display the action using scribe
        scribe.agent_action(agent, action_response)
    
    def _display_action_consequences(self, before_agent: Agent, after_agent: Agent, action_log: AgentAction) -> None:
        """
        Display the consequences of an agent action.
        
        Args:
            before_agent: The agent before the action
            after_agent: The agent after the action
            action_log: The action log entry
        """
        action_type = action_log.type
        extras = action_log.extras or {}
        
        if action_type == ActionType.REST:
            # Calculate rest gained
            rest_gained = after_agent.needs.rest - before_agent.needs.rest
            scribe.print(f"[green]{before_agent.name} rested and recovered {rest_gained:.2%} rest. New rest: {after_agent.needs.rest:.2%}[/green]")
        
        elif action_type == ActionType.WORK:
            # Calculate credits earned
            credits_earned = after_agent.credits - before_agent.credits
            scribe.print(f"[green]{before_agent.name} worked and earned {credits_earned:.2f} credits. New credits: {after_agent.credits:.2f}[/green]")
        
        elif action_type == ActionType.HARVEST:
            # Calculate food gained
            food_gained = after_agent.needs.food - before_agent.needs.food
            scribe.print(f"[green]{before_agent.name} harvested mushrooms and gained {food_gained:.2%} food. New food: {after_agent.needs.food:.2%}[/green]")
        
        elif action_type == ActionType.CRAFT:
            # Find the new good that was crafted (should be in the agent's inventory)
            before_goods = {good.name: good for good in before_agent.goods}
            after_goods = {good.name: good for good in after_agent.goods}
            
            # Find items in after but not in before
            new_goods = [name for name in after_goods if name not in before_goods]
            if new_goods:
                new_good = after_goods[new_goods[0]]
                scribe.print(f"[green]{before_agent.name} crafted {new_good.name} ({new_good.type.value}) with quality {new_good.quality:.2f}[/green]")
            else:
                scribe.print(f"[yellow]{before_agent.name} attempted to craft something but no new item was found[/yellow]")
        
        elif action_type == ActionType.SELL:
            # Calculate credits earned
            credits_earned = after_agent.credits - before_agent.credits
            good_name = extras.get("goodName", "an item")
            scribe.print(f"[green]{before_agent.name} sold {good_name} and earned {credits_earned:.2f} credits. New credits: {after_agent.credits:.2f}[/green]")
        
        elif action_type == ActionType.BUY:
            # Calculate credits spent
            credits_spent = before_agent.credits - after_agent.credits
            
            # Find the new good that was bought
            before_goods = {good.name: good for good in before_agent.goods}
            after_goods = {good.name: good for good in after_agent.goods}
            
            # Find items in after but not in before
            new_goods = [name for name in after_goods if name not in before_goods]
            if new_goods:
                new_good = after_goods[new_goods[0]]
                scribe.print(f"[green]{before_agent.name} bought {new_good.name} for {credits_spent:.2f} credits. New credits: {after_agent.credits:.2f}[/green]")
            else:
                scribe.print(f"[yellow]{before_agent.name} attempted to buy something but no new item was found[/yellow]")
        
        elif action_type == ActionType.THINK:
            # Get thoughts from extras
            thoughts = extras.get("thoughts", "deep thoughts")
            theme = extras.get("theme", "unknown topic")
            scribe.print(f"[green]{before_agent.name} spent the day thinking about {theme}: {thoughts}[/green]")
        
        elif action_type == ActionType.COMPOSE:
            # Get song details from extras
            title = extras.get("title", "Untitled Song")
            genre = extras.get("genre", "Unknown Genre")
            scribe.print(f"[green]{before_agent.name} composed a new song: '{title}' in the genre '{genre}'[/green]")
    
    def _display_agent_death(self, agent_name: str) -> None:
        """
        Display an agent death message.
        
        Args:
            agent_name: Name of the deceased agent
        """
        scribe.agent_death(agent_name, "starvation")
    
    def _display_narrative(self, title: str, content: str, state: SimulationState) -> None:
        """
        Display the narrative for the day.
        
        Args:
            title: The narrative title
            content: The narrative content
            state: The simulation state
        """
        scribe.narrative_title(title)
        scribe.narrative_content(content, state)
    
    def _display_simulation_end(self, max_days: int) -> None:
        """
        Display a message at the end of the simulation.
        
        Args:
            max_days: The maximum number of days the simulation ran for
        """
        # Stop any active status indicator before printing the final message
        if self.current_status:
            self.current_status.stop()
            self.current_status = None
            
        scribe.simulation_end(max_days)

    def _display_night_activities(self, state: SimulationState) -> None:
        """
        Display night activities for all agents.
        
        Args:
            state: The simulation state
        """
        night_activities = state.today_night_activities
        
        if not night_activities:
            return
        
        scribe.print("\n[bold magenta]===== Night Activities =====[/bold magenta]")
        
        for activity in night_activities:
            agent_id = activity.agent_id
            agent = state.get_agent_by_id(agent_id)
            
            if not agent:
                continue
            
            # Display dinner consumption
            if activity.dinner_consumed:
                food_names = [f"{food.name} (quality: {food.quality:.2f})" for food in activity.dinner_consumed]
                scribe.print(f"[magenta]{agent.name} had dinner:[/magenta] {', '.join(food_names)}")
            
            # Display song listening
            if activity.song_choice_id:
                scribe.print(f"[magenta]{agent.name} listened to song:[/magenta] {activity.song_choice_id}")
            
            # Display letters
            if activity.letters:
                for letter in activity.letters:
                    scribe.print(f"[magenta]{agent.name} wrote a letter to {letter.recipient_name}:[/magenta]")
                    scribe.print(f"[dim magenta]Title:[/dim magenta] {letter.title}")
                    scribe.print(f"[dim magenta]Message:[/dim magenta] {letter.message}")
            
            scribe.print("")  # Empty line for readability

    def run_simulation(
        self,
        num_agents: int,
        max_days: int,
        **kwargs
    ) -> None:
        """
        Run a complete simulation, with step-by-step monitoring.
        
        Args:
            num_agents: Number of agents in the simulation
            max_days: Maximum number of days to run the simulation
            **kwargs: Additional parameters for simulation creation
        """
        # Print welcome message
        scribe.simulation_start(num_agents, max_days)
        
        # Create the simulation if we don't already have one
        if not self.simulation_id:
            self.create_simulation(num_agents, max_days, **kwargs)
        
        # Get the initial state
        state = self.get_simulation_detail()
        
        # Show initial agent status
        self._display_agents(state.agents)
        
        # Run for max_days
        for day in range(1, max_days + 1):
            if not self.is_running:
                self._show_status("Simulation stopped by user")
                break
                
            # Display day header
            self._display_day_header(day)
            
            # Get the initial state for this day
            prev_state = self.get_simulation_detail()
            
            # Get the current status to display simulation stage
            status_response = self.get_simulation_status()
            
            # Display information about the current stage
            self._display_stage_info(status_response)
            
            # Advance simulation by one day
            self._show_status(f"Processing day {day}...")
            
            try:
                # Use next endpoint for single day advancement
                url = f"{self.api_url}/simulation/next/{self.simulation_id}"
                response = self.session.post(url)
                response.raise_for_status()
                
                # Get the updated state
                state = self.get_simulation_detail()
                
                # Process the day's events
                self._process_day(day, prev_state, state)
                
                # Short delay for readability
                time.sleep(0.5)
            except Exception as e:
                self._show_error(f"Error processing day {day}: {e}")
                break
        
        # Display completion message
        self._display_simulation_end(day)


def run_headless_simulation(
    num_agents: int,
    max_days: int,
    starting_credits: Optional[int],
    model_name: str,
    temperature: float,
    output_dir: str,
    log_level: str,
    simulation_id: Optional[str] = None,
    reset_simulation: bool = False
) -> None:
    """
    Run a headless simulation using the API.
    
    Args:
        num_agents: Number of agents in the simulation
        max_days: Maximum number of days to run the simulation
        starting_credits: Starting credits for each agent
        model_name: Name of the LLM model to use
        temperature: Temperature for the LLM
        output_dir: Directory to store output files
        log_level: Logging level
        simulation_id: Optional ID for an existing simulation
        reset_simulation: Whether to reset the simulation before running
    """
    try:
        # Create the frontend
        frontend = HeadlessFrontend(log_level=log_level, simulation_id=simulation_id)
        
        # If we have a simulation ID and reset flag is set, reset the simulation
        if simulation_id and reset_simulation:
            try:
                url = f"{frontend.api_url}/simulation/reset/{simulation_id}"
                response = frontend.session.post(url)
                response.raise_for_status()
                frontend.simulation_id = simulation_id
                frontend._show_status(f"Simulation {simulation_id} has been reset")
            except Exception as e:
                frontend._show_error(f"Failed to reset simulation: {e}")
                return
        
        # Run the simulation
        frontend.run_simulation(
            num_agents=num_agents,
            max_days=max_days,
            starting_credits=starting_credits,
            model_name=model_name,
            temperature=temperature,
            output_dir=output_dir
        )
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt detected, exiting...")
    except Exception as e:
        logger.error(f"Error running simulation: {e}", exc_info=True)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Run a headless ProtoNomia simulation")
    parser.add_argument(
        "--initial-population", "-p",
        type=int,
        default=5,
        help="Initial population size"
    )
    parser.add_argument(
        "--ticks", "-t",
        type=int,
        default=30,
        help="Number of days to simulate"
    )
    parser.add_argument(
        "--starting-credits", "-c",
        type=int,
        default=None,
        help="Starting credits for each agent (random if not specified)"
    )
    parser.add_argument(
        "--api-url", "-u",
        type=str,
        default="http://127.0.0.1:8000",
        help="URL of the ProtoNomia API"
    )
    parser.add_argument(
        "--model", "-m",
        type=str,
        default="gemma:2b",
        help="Name of the LLM model to use"
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.7,
        help="Temperature for the LLM"
    )
    parser.add_argument(
        "--output-dir", "-o",
        type=str,
        default="output",
        help="Directory to store output files"
    )
    parser.add_argument(
        "--log-level", "-l",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Logging level"
    )
    parser.add_argument(
        "--simulation-id", "-s",
        type=str,
        default=None,
        help="ID of an existing simulation to use"
    )
    parser.add_argument(
        "--reset", "-r",
        action="store_true",
        help="Reset the simulation before running (only used with --simulation-id)"
    )
    parser.add_argument(
        "--verbosity", "-v",
        type=int,
        default=3,
        choices=[1, 2, 3, 4, 5],
        help="Verbosity level (1-5)"
    )
    parser.add_argument(
        "--resource-scarcity",
        type=float,
        default=0.2,
        help="Resource scarcity level (0.0-1.0)"
    )
    
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    
    # Set logging level
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    # Configure scribe verbosity
    scribe.verbosity = args.verbosity
    
    # Run the simulation
    run_headless_simulation(
        num_agents=args.initial_population,
        max_days=args.ticks,
        starting_credits=args.starting_credits,
        model_name=args.model,
        temperature=args.temperature,
        output_dir=args.output_dir,
        log_level=args.log_level,
        simulation_id=args.simulation_id,
        reset_simulation=args.reset
    ) 