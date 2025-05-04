"""
ProtoNomia Simulation CLI
This module provides a CLI interface to run the ProtoNomia simulation without requiring the API server.
"""
import logging
import os
import sys
import time
import click

# Add the current directory to the path for imports
sys.path.insert(0, os.path.abspath("."))

from engine.simulation import SimulationEngine
from src.settings import DEFAULT_LM, LLM_MAX_RETRIES
from src.scribe import Scribe
from models import SimulationStage

# Initialize logger
logger = logging.getLogger(__name__)

# Create scribe for rich output
scribe = Scribe()

class SimulationCLI:
    """
    CLI interface for running the ProtoNomia simulation.
    Provides rich terminal output similar to the headless frontend but runs the engine directly.
    """
    
    def __init__(
        self,
        num_agents: int = 5,
        max_days: int = 30,
        starting_credits: int = None,
        model_name: str = DEFAULT_LM,
        output_dir: str = "output",
        temperature: float = 0.7,
        verbosity: int = 3
    ):
        """
        Initialize the simulation CLI.
        
        Args:
            num_agents: Number of agents in the simulation
            max_days: Maximum number of days to run the simulation
            starting_credits: Starting credits for each agent
            model_name: Name of the LLM model to use
            output_dir: Directory to store output files
            temperature: Temperature for the LLM
            verbosity: Verbosity level for output (1-5)
        """
        self.num_agents = num_agents
        self.max_days = max_days
        self.starting_credits = starting_credits
        self.model_name = model_name
        self.output_dir = output_dir
        self.temperature = temperature
        
        # Configure scribe verbosity
        scribe.verbosity = verbosity
        
        # Create the simulation engine
        self.engine = SimulationEngine(
            num_agents=num_agents,
            max_days=max_days,
            starting_credits=starting_credits,
            model_name=model_name,
            output_dir=output_dir,
            temperature=temperature,
            max_retries=LLM_MAX_RETRIES,
            retry_delay=5
        )
        
        # Initialize simulation state
        self.engine.setup_initial_state()
        
    def run(self):
        """Run the simulation with rich CLI output."""
        # Print welcome message
        scribe.simulation_start(self.num_agents, self.max_days)
        
        # Show initial agent status
        self._display_agents(self.engine.state.agents)
        
        # Run for the specified number of days
        for day in range(1, self.max_days + 1):
            # Display day header
            self._display_day_header(day)
            
            # Save the state before the day for comparison
            prev_state = self.engine.state.copy()
            
            # Process the day's events with stage reporting
            self._process_day(day)
            
            # Allow a moment for readability
            time.sleep(0.5)
        
        # Display completion message
        self._display_simulation_end(self.max_days)
    
    def _display_agents(self, agents):
        """Display information about agents using the scribe."""
        for agent in agents:
            scribe.agent_created(agent)
    
    def _display_day_header(self, day):
        """Display a header for the current day."""
        scribe.day_header(day)
    
    def _display_stage_info(self):
        """Display information about the current simulation stage."""
        stage = self.engine.state.current_stage
        
        # Get the agent being processed, if any
        agent_name = None
        if self.engine.state.current_agent_id:
            agent = self.engine.get_agent_by_id(self.engine.state.current_agent_id)
            if agent:
                agent_name = agent.name
        
        if stage == SimulationStage.INITIALIZATION:
            scribe.print("[bold cyan]Initializing simulation...[/bold cyan]")
        elif stage == SimulationStage.AGENT_DAY:
            if agent_name:
                scribe.print(f"[bold cyan]Processing day action for {agent_name}...[/bold cyan]")
            else:
                scribe.print("[bold cyan]Processing day actions...[/bold cyan]")
        elif stage == SimulationStage.NARRATOR:
            scribe.print("[bold cyan]Generating daily narrative...[/bold cyan]")
        elif stage == SimulationStage.AGENT_NIGHT:
            if agent_name:
                scribe.print(f"[bold cyan]Processing night activities for {agent_name}...[/bold cyan]")
            else:
                scribe.print("[bold cyan]Processing night activities...[/bold cyan]")
    
    def _process_day(self, day):
        """
        Process a day with stage-by-stage display.
        
        Args:
            day: The current day number
        """
        # Override the engine's process_day method to show stage info
        
        # Display stage: INITIALIZATION
        self._display_stage_info()
        
        # Decay agent needs at the start of the day
        self.engine._decay_agent_needs()
        
        # Set stage to AGENT_DAY for agent actions
        self.engine.state.current_stage = SimulationStage.AGENT_DAY
        self._display_stage_info()
        
        # Process each agent's action one at a time with UI updates
        while True:
            # Get the next agent that needs to act
            next_agent = self.engine.state.get_next_agent_for_day()
            if not next_agent:
                # All agents have acted, move to narrative stage
                break
            
            # Set the current agent
            self.engine.state.current_agent_id = next_agent.id
            self._display_stage_info()
            
            try:
                # Generate and execute action for this agent
                action = self.engine._process_agent_day_action(next_agent)
                
                # Display the action
                if action:
                    self._display_agent_action(next_agent, action)
            except Exception as e:
                logger.error(f"Error processing day action for {next_agent.name}: {e}")
        
        # All agents have acted, move to narrative stage
        self.engine.state.current_stage = SimulationStage.NARRATOR
        self.engine.state.current_agent_id = None
        self._display_stage_info()
        
        # Generate the daily narrative
        self.engine._generate_daily_narrative([])
        
        # Display narrative from file if available
        self._display_narrative_from_file(day)
        
        # Set stage to AGENT_NIGHT
        self.engine.state.current_stage = SimulationStage.AGENT_NIGHT
        self.engine.state.current_agent_id = None
        self._display_stage_info()
        
        # Process night activities
        self.engine.process_night()
        
        # Display night activities
        self._display_night_activities()
        
        # Check for any dead agents and remove them
        self.engine._check_agent_status()
    
    def _display_agent_action(self, agent, action):
        """
        Display an agent action.
        
        Args:
            agent: The agent that performed the action
            action: The action performed
        """
        scribe.print(f"[cyan]Agent {agent.name} chose action {action.type}[/cyan]")
        
        # Display reasoning if available
        if action.reasoning:
            scribe.print(f"[dim cyan]Reasoning: {action.reasoning}[/dim cyan]")
        
        # Display extras
        if action.extras:
            extras_str = ", ".join(f"{k}: {v}" for k, v in action.extras.items())
            scribe.print(f"[dim cyan]Details: {extras_str}[/dim cyan]")
    
    def _display_narrative_from_file(self, day):
        """
        Display the narrative for the day from the saved file.
        
        Args:
            day: The current day number
        """
        narrative_file = os.path.join(self.output_dir, f"day_{day}_narrative.txt")
        if os.path.exists(narrative_file):
            with open(narrative_file, 'r') as f:
                lines = f.readlines()
                title = lines[0].strip("# \n")
                content = "".join(lines[2:])
                
                # Display using scribe
                scribe.narrative_title(title)
                scribe.narrative_content(content, self.engine.state)
    
    def _display_night_activities(self):
        """Display night activities for all agents."""
        night_activities = self.engine.state.today_night_activities
        
        if not night_activities:
            return
        
        scribe.print("\n[bold magenta]===== Night Activities =====[/bold magenta]")
        
        for activity in night_activities:
            agent_id = activity.agent_id
            agent = self.engine.get_agent_by_id(agent_id)
            
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
    
    def _display_simulation_end(self, max_days):
        """
        Display a message at the end of the simulation.
        
        Args:
            max_days: The maximum number of days the simulation ran for
        """
        scribe.simulation_end(max_days)


@click.command(context_settings=dict(help_option_names=["-h", "--help"]))
@click.option('-n', '--agents', default=5, help='Number of agents in the simulation')
@click.option('-d', '--days', default=30, help='Number of days to run the simulation')
@click.option('-c', '--credits', default=None, type=int, help='Number of credits each agent starts with (default: random wealth)')
@click.option('-m', '--model', default=DEFAULT_LM, help='LLM model to use')
@click.option('-o', '--output', default='output', help='Output directory')
@click.option('-t', '--temperature', default=0.7, help='LLM temperature')
@click.option('-l', '--log-level', default='ERROR', help='Logging level (DEBUG, INFO, WARNING, ERROR)')
@click.option('-v', '--verbosity', default=3, type=int, help='Verbosity level for output (1-5)')
def main(agents, days, credits, model, output, temperature, log_level, verbosity):
    """Run the ProtoNomia economic simulation directly, without requiring the API server."""
    # Configure logging
    log_level = getattr(logging, log_level.upper())
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
        ]
    )
    
    # Configure scribe verbosity
    scribe.verbosity = verbosity
    
    # Create and run the simulation CLI
    cli = SimulationCLI(
        num_agents=agents,
        max_days=days,
        starting_credits=credits,
        model_name=model,
        output_dir=output,
        temperature=temperature,
        verbosity=verbosity
    )
    
    # Run the simulation
    cli.run()

    # Print completion message
    click.echo(f"Simulation completed after {days} days. Output saved to {output}/")


if __name__ == "__main__":
    main()
