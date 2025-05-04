"""
ProtoNomia Frontend Base Class
This module provides a base class for all ProtoNomia frontends.
"""
import abc
import logging
import requests
import time
from typing import Dict, Any, Optional, List

from src.models import SimulationState, Agent

# Default API configuration
DEFAULT_API_URL = "http://127.0.0.1:8000"


class FrontendBase(abc.ABC):
    """
    Abstract base class for all ProtoNomia frontends.
    Provides common methods for interacting with the API.
    """

    def __init__(
        self,
        api_url: str = DEFAULT_API_URL,
        log_level: str = "INFO"
    ):
        """
        Initialize the frontend.
        
        Args:
            api_url: URL of the ProtoNomia API
            log_level: Logging level
        """
        self.api_url = api_url
        self.simulation_id = None
        
        # Configure logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(getattr(logging, log_level))
        
        # Request session for API calls
        self.session = requests.Session()

    def create_simulation(
        self,
        num_agents: int,
        max_days: int,
        starting_credits: Optional[int] = None,
        model_name: str = "gemma3:4b",
        temperature: float = 0.7,
        output_dir: str = "output"
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
        self._show_status("Creating simulation...")
        
        url = f"{self.api_url}/simulation/start"
        
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
        try:
            response = self.session.post(url, json=data)
            response.raise_for_status()
            
            # Parse the response
            result = response.json()
            self.simulation_id = result["simulation_id"]
            
            self._show_status(f"Simulation created: {self.simulation_id}")
            return self.simulation_id
        except requests.RequestException as e:
            self._show_error(f"Failed to create simulation: {e}")
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
            
            # Convert to SimulationState
            return SimulationState.model_validate(state_data)
        except requests.RequestException as e:
            self._show_error(f"Failed to get simulation detail: {e}")
            raise

    def run_simulation_day(self) -> SimulationState:
        """
        Run the simulation for one day.
        
        Returns:
            SimulationState: The updated simulation state
        """
        if not self.simulation_id:
            self._show_error("No active simulation")
            raise ValueError("No active simulation")
            
        # Run the simulation for one day
        url = f"{self.api_url}/simulation/run/{self.simulation_id}?days=1"
        
        # Make the request
        try:
            self._show_status(f"Running simulation day...")
            response = self.session.post(url)
            response.raise_for_status()
            
            # Get the full state
            return self.get_simulation_detail()
        except requests.RequestException as e:
            self._show_error(f"Failed to run simulation day: {e}")
            raise

    def add_agent(
        self,
        name: Optional[str] = None,
        personality: Optional[str] = None,
        starting_credits: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Add a new agent to the simulation.
        
        Args:
            name: Name of the agent (optional)
            personality: Personality string (optional)
            starting_credits: Starting credits (optional)
            
        Returns:
            Dict[str, Any]: Response data
        """
        if not self.simulation_id:
            self._show_error("No active simulation")
            raise ValueError("No active simulation")
            
        url = f"{self.api_url}/agent/add"
        
        # Prepare request data
        data = {"simulation_id": self.simulation_id}
        
        if name:
            data["name"] = name
        if personality:
            data["personality"] = personality
        if starting_credits:
            data["starting_credits"] = starting_credits
        
        # Make the request
        try:
            self._show_status(f"Adding new agent...")
            response = self.session.post(url, json=data)
            response.raise_for_status()
            
            # Parse the response
            return response.json()
        except requests.RequestException as e:
            self._show_error(f"Failed to add agent: {e}")
            raise

    def kill_agent(self, agent_id: str) -> Dict[str, Any]:
        """
        Kill an agent in the simulation.
        
        Args:
            agent_id: ID of the agent to kill
            
        Returns:
            Dict[str, Any]: Response data
        """
        if not self.simulation_id:
            self._show_error("No active simulation")
            raise ValueError("No active simulation")
            
        url = f"{self.api_url}/agent/kill"
        
        # Make the request
        try:
            self._show_status(f"Killing agent...")
            response = self.session.delete(
                url,
                params={
                    "simulation_id": self.simulation_id,
                    "agent_id": agent_id
                }
            )
            response.raise_for_status()
            
            # Parse the response
            return response.json()
        except requests.RequestException as e:
            self._show_error(f"Failed to kill agent: {e}")
            raise

    def get_agent_status(self, agent_id: str) -> Dict[str, Any]:
        """
        Get status information about an agent.
        
        Args:
            agent_id: ID of the agent
            
        Returns:
            Dict[str, Any]: Agent data
        """
        if not self.simulation_id:
            self._show_error("No active simulation")
            raise ValueError("No active simulation")
            
        url = f"{self.api_url}/agent/status"
        
        # Make the request
        try:
            self._show_status(f"Getting agent status...")
            response = self.session.get(
                url,
                params={
                    "simulation_id": self.simulation_id,
                    "agent_id": agent_id
                }
            )
            response.raise_for_status()
            
            # Parse the response
            return response.json()
        except requests.RequestException as e:
            self._show_error(f"Failed to get agent status: {e}")
            raise
            
    def update_agent(self, agent_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an agent in the simulation.
        
        Args:
            agent_id: ID of the agent to update
            updates: Dictionary of updates to apply
            
        Returns:
            Dict[str, Any]: Updated agent data
        """
        if not self.simulation_id:
            self._show_error("No active simulation")
            raise ValueError("No active simulation")
            
        url = f"{self.api_url}/agent/update"
        
        # Prepare request data
        data = {
            "simulation_id": self.simulation_id,
            "agent_id": agent_id,
            "updates": updates
        }
        
        # Make the request
        try:
            self._show_status(f"Updating agent...")
            response = self.session.put(url, json=data)
            response.raise_for_status()
            
            # Parse the response
            return response.json()
        except requests.RequestException as e:
            self._show_error(f"Failed to update agent: {e}")
            raise
            
    def run_simulation(
        self,
        num_agents: int,
        max_days: int,
        **kwargs
    ) -> None:
        """
        Run a complete simulation from start to finish.
        
        Args:
            num_agents: Number of agents in the simulation
            max_days: Maximum number of days to run the simulation
            **kwargs: Additional parameters for simulation creation
        """
        # Create the simulation
        self.create_simulation(num_agents, max_days, **kwargs)
        
        # Get the initial state
        state = self.get_simulation_detail()
        
        # Show initial agent status
        self._display_agents(state.agents)
        
        # Run for max_days
        for day in range(1, max_days + 1):
            # Display day header
            self._display_day_header(day)
            
            # Get the initial state for this day
            prev_state = self.get_simulation_detail()
            
            # Run the day
            state = self.run_simulation_day()
            
            # Process the day's events
            self._process_day(day, prev_state, state)
            
            # Short delay for readability
            time.sleep(0.5)
            
        # Display completion message
        self._display_simulation_end(max_days)

    # Abstract methods to be implemented by subclasses
    
    @abc.abstractmethod
    def _show_status(self, message: str) -> None:
        """
        Display a status message.
        
        Args:
            message: The status message to display
        """
        pass
        
    @abc.abstractmethod
    def _show_error(self, message: str) -> None:
        """
        Display an error message.
        
        Args:
            message: The error message to display
        """
        pass
        
    @abc.abstractmethod
    def _display_agents(self, agents: List[Agent]) -> None:
        """
        Display information about agents.
        
        Args:
            agents: List of agents to display
        """
        pass
        
    @abc.abstractmethod
    def _display_day_header(self, day: int) -> None:
        """
        Display a header for the current day.
        
        Args:
            day: The current day number
        """
        pass
        
    @abc.abstractmethod
    def _process_day(self, day: int, prev_state: SimulationState, state: SimulationState) -> None:
        """
        Process and display events for the current day.
        
        Args:
            day: The current day number
            prev_state: The state before the day
            state: The state after the day
        """
        pass
        
    @abc.abstractmethod
    def _display_simulation_end(self, max_days: int) -> None:
        """
        Display a message at the end of the simulation.
        
        Args:
            max_days: The maximum number of days the simulation ran for
        """
        pass 