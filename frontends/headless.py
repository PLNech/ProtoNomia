"""
ProtoNomia Headless Frontend
This module provides a CLI frontend for the ProtoNomia API.
"""
import argparse
import json
import logging
import os
import sys
import time
import requests
from typing import Dict, Any, Optional

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.scribe import Scribe
from models import SimulationState, Agent, AgentActionResponse, ActionType

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create scribe for rich output
scribe = Scribe()

# API URL
API_BASE_URL = "http://127.0.0.1:8000"


def create_simulation(
    num_agents: int,
    max_days: int,
    starting_credits: Optional[int],
    model_name: str,
    temperature: float,
    output_dir: str
) -> str:
    """
    Create a new simulation via the API.
    
    Args:
        num_agents: Number of agents in the simulation
        max_days: Maximum number of days to run the simulation
        starting_credits: Optional starting credits for agents
        model_name: Name of the LLM model to use
        temperature: Model temperature
        output_dir: Directory for output files
        
    Returns:
        str: ID of the created simulation
    """
    url = f"{API_BASE_URL}/simulation/start"
    
    # Prepare request data
    data = {
        "num_agents": num_agents,
        "max_days": max_days,
        "model_name": model_name,
        "temperature": temperature,
        "output_dir": output_dir
    }
    
    if starting_credits is not None:
        data["starting_credits"] = starting_credits
    
    # Make the request
    response = requests.post(url, json=data)
    
    # Check for success
    if response.status_code != 200:
        error_msg = f"Failed to create simulation: {response.text}"
        logger.error(error_msg)
        raise Exception(error_msg)
    
    # Parse the response
    result = response.json()
    simulation_id = result["simulation_id"]
    
    return simulation_id


def get_simulation_detail(simulation_id: str) -> SimulationState:
    """
    Get detailed information about a simulation.
    
    Args:
        simulation_id: ID of the simulation
        
    Returns:
        SimulationState: The simulation state
    """
    url = f"{API_BASE_URL}/simulation/detail/{simulation_id}"
    
    # Make the request
    response = requests.get(url)
    
    # Check for success
    if response.status_code != 200:
        error_msg = f"Failed to get simulation detail: {response.text}"
        logger.error(error_msg)
        raise Exception(error_msg)
    
    # Parse the response
    result = response.json()
    
    # Convert to SimulationState
    state_data = result["state"]
    state = SimulationState.model_validate(state_data)
    
    return state


def run_simulation_day(simulation_id: str) -> SimulationState:
    """
    Run the simulation for one day.
    
    Args:
        simulation_id: ID of the simulation
        
    Returns:
        SimulationState: The updated simulation state
    """
    # Run the simulation for one day
    url = f"{API_BASE_URL}/simulation/run/{simulation_id}?days=1"
    
    # Make the request
    response = requests.post(url)
    
    # Check for success
    if response.status_code != 200:
        error_msg = f"Failed to run simulation day: {response.text}"
        logger.error(error_msg)
        raise Exception(error_msg)
    
    # Get the full state
    state = get_simulation_detail(simulation_id)
    
    return state


def print_simulation_start(num_agents: int, max_days: int) -> None:
    """
    Print the simulation start message.
    
    Args:
        num_agents: Number of agents in the simulation
        max_days: Maximum number of days to run the simulation
    """
    scribe.simulation_start(num_agents, max_days)


def print_simulation_end(max_days: int) -> None:
    """
    Print the simulation end message.
    
    Args:
        max_days: Maximum number of days of the simulation
    """
    scribe.simulation_end(max_days)


def print_agents_status(agents: list[Agent]) -> None:
    """
    Print the status of all agents.
    
    Args:
        agents: List of agents
    """
    for agent in agents:
        scribe.agent_created(agent)


def print_day_header(day: int) -> None:
    """
    Print the day header.
    
    Args:
        day: The current day
    """
    scribe.day_header(day)


def print_agent_action(agent: Agent, action: AgentActionResponse) -> None:
    """
    Print an agent action.
    
    Args:
        agent: The agent performing the action
        action: The action response
    """
    scribe.agent_action(agent, action)
    
    # Print additional details based on action type
    if action.type == ActionType.REST:
        # Assume typical rest amount
        rest_amount = 0.5
        new_rest = min(1.0, agent.needs.rest + rest_amount)
        scribe.agent_rest(agent.name, new_rest, rest_amount)
    elif action.type == ActionType.WORK:
        # Assume typical income
        income = 100
        scribe.agent_work(agent.name, income, agent.credits)
    elif action.type == ActionType.HARVEST:
        # Extract quality from extras if available, or assume default
        quality = 0.5
        food_level = agent.needs.food
        scribe.agent_harvest(agent.name, "Martian Mushrooms", quality, food_level)
    elif action.type == ActionType.CRAFT:
        # Extract details from extras
        good_type = action.extras.get("goodType", "FOOD")
        name = action.extras.get("name", "Unknown Item")
        materials = action.extras.get("materials", 50)
        quality = 0.5  # Assume default quality
        scribe.agent_craft(agent.name, name, good_type, quality, materials)
    elif action.type == ActionType.SELL:
        # Extract details from extras
        good_name = action.extras.get("goodName", "Unknown Item")
        price = action.extras.get("price", 100)
        # Assume type and quality
        good_type = "FOOD"
        quality = 0.5
        scribe.agent_sell(agent.name, good_name, good_type, quality, price)
    elif action.type == ActionType.BUY:
        # Extract details from extras
        listing_id = action.extras.get("listingId", "random")
        # Assume details about the purchased item
        good_name = "Unknown Item"
        good_type = "FOOD"
        quality = 0.5
        price = 100
        scribe.agent_buy(agent.name, good_name, good_type, quality, price)
    elif action.type == ActionType.THINK:
        # Extract thoughts from extras
        thoughts = action.extras.get("thoughts", "")
        scribe.agent_think(agent.name, thoughts, action.extras)
    elif action.type == ActionType.COMPOSE:
        # Extract song details from extras
        scribe.agent_song(agent.name, action.extras, action.extras)


def print_narrative(title: str, content: str, state: SimulationState) -> None:
    """
    Print the narrative for the day.
    
    Args:
        title: The narrative title
        content: The narrative content
        state: The simulation state
    """
    scribe.narrative_title(title)
    scribe.narrative_content(content, state)


def print_agent_death(name: str) -> None:
    """
    Print an agent death message.
    
    Args:
        name: Name of the deceased agent
    """
    scribe.agent_death(name, "starvation")


def run_headless_simulation(
    num_agents: int,
    max_days: int,
    starting_credits: Optional[int],
    model_name: str,
    temperature: float,
    output_dir: str,
    log_level: str
) -> None:
    """
    Run a headless simulation using the API.
    
    Args:
        num_agents: Number of agents in the simulation
        max_days: Maximum number of days to run the simulation
        starting_credits: Optional starting credits for agents
        model_name: Name of the LLM model to use
        temperature: Model temperature
        output_dir: Directory for output files
        log_level: Logging level
    """
    # Set up logging
    logging.getLogger().setLevel(getattr(logging, log_level.upper()))
    
    try:
        # Print welcome message
        print_simulation_start(num_agents, max_days)
        
        # Create the simulation
        simulation_id = create_simulation(
            num_agents=num_agents,
            max_days=max_days,
            starting_credits=starting_credits,
            model_name=model_name,
            temperature=temperature,
            output_dir=output_dir
        )
        logger.info(f"Created simulation {simulation_id}")
        
        # Get the initial state
        state = get_simulation_detail(simulation_id)
        
        # Print the initial agent status
        print_agents_status(state.agents)
        
        # Run the simulation for max_days
        for day in range(1, max_days + 1):
            # Print day header
            print_day_header(day)
            
            # Get the initial state for this day
            prev_state = get_simulation_detail(simulation_id)
            
            # Run the simulation for one day
            state = run_simulation_day(simulation_id)
            
            # Extract and display actions for this day
            action_logs = [log for log in state.actions if log.day == day]
            
            # Keep track of agents who died
            agents_alive_before = {agent.id: agent for agent in prev_state.agents}
            agents_alive_after = {agent.id: agent for agent in state.agents}
            
            # Print agent actions
            for log in action_logs:
                agent = log.agent
                print_agent_action(agent, log.action)
            
            # Check for dead agents
            for agent_id, agent in agents_alive_before.items():
                if agent_id not in agents_alive_after:
                    print_agent_death(agent.name)
            
            # Print narrative
            narrative_file = os.path.join(output_dir, f"day_{day}_narrative.txt")
            if os.path.exists(narrative_file):
                with open(narrative_file, 'r') as f:
                    lines = f.readlines()
                    title = lines[0].strip("# \n")
                    content = "".join(lines[2:])
                    print_narrative(title, content, state)
            
            # Add a delay to make output readable
            time.sleep(1)
        
        # Print completion message
        print_simulation_end(max_days)
        
    except Exception as e:
        logger.error(f"Error running simulation: {e}", exc_info=True)
        sys.exit(1)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="ProtoNomia Headless Simulation")
    parser.add_argument(
        "-n", "--agents",
        type=int,
        default=5,
        help="Number of agents in the simulation"
    )
    parser.add_argument(
        "-d", "--days",
        type=int,
        default=30,
        help="Number of days to run the simulation"
    )
    parser.add_argument(
        "-c", "--credits",
        type=int,
        default=None,
        help="Number of credits each agent starts with (default: random)"
    )
    parser.add_argument(
        "-m", "--model",
        type=str,
        default="gemma3:4b",
        help="LLM model to use"
    )
    parser.add_argument(
        "-t", "--temperature",
        type=float,
        default=0.7,
        help="LLM temperature"
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        default="output",
        help="Output directory"
    )
    parser.add_argument(
        "-l", "--log-level",
        type=str,
        default="ERROR",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level"
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run_headless_simulation(
        num_agents=args.agents,
        max_days=args.days,
        starting_credits=args.credits,
        model_name=args.model,
        temperature=args.temperature,
        output_dir=args.output,
        log_level=args.log_level
    ) 