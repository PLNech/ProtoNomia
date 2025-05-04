"""
ProtoNomia Simulation Manager
This module provides a singleton manager for simulation instances.
"""
import logging
from typing import Dict, Optional, List, Any
from copy import deepcopy

from src.engine.simulation import SimulationEngine
from src.models import Agent, SimulationState, Good, GoodType

# Configure logging
logger = logging.getLogger(__name__)


class SimulationManager:
    """
    Singleton manager for simulation instances.
    """
    _instance = None
    _simulations: Dict[str, SimulationEngine] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SimulationManager, cls).__new__(cls)
            cls._instance._simulations = {}
        return cls._instance

    def create_simulation(self, **kwargs) -> SimulationEngine:
        """
        Create a new simulation with the given parameters.

        Args:
            **kwargs: Parameters to pass to the SimulationEngine constructor

        Returns:
            SimulationEngine: The new simulation instance
        """
        simulation = SimulationEngine(**kwargs)
        self._simulations[simulation.simulation_id] = simulation
        return simulation

    def get_simulation(self, simulation_id: str) -> Optional[SimulationEngine]:
        """
        Get a simulation by its ID.

        Args:
            simulation_id: The ID of the simulation to get

        Returns:
            Optional[SimulationEngine]: The simulation or None if not found
        """
        return self._simulations.get(simulation_id)

    def delete_simulation(self, simulation_id: str) -> bool:
        """
        Delete a simulation by its ID.

        Args:
            simulation_id: The ID of the simulation to delete

        Returns:
            bool: True if the simulation was deleted, False otherwise
        """
        if simulation_id in self._simulations:
            del self._simulations[simulation_id]
            return True
        return False

    def list_simulations(self) -> List[str]:
        """
        Get a list of all simulation IDs.

        Returns:
            List[str]: List of simulation IDs
        """
        return list(self._simulations.keys())
    
    def get_agent(self, simulation_id: str, agent_id: Optional[str] = None, agent_name: Optional[str] = None) -> Optional[Agent]:
        """
        Get an agent from a simulation by ID or name.
        
        Args:
            simulation_id: The ID of the simulation
            agent_id: The ID of the agent (optional)
            agent_name: The name of the agent (optional)
            
        Returns:
            Optional[Agent]: The agent or None if not found
        """
        simulation = self.get_simulation(simulation_id)
        if not simulation:
            return None
        
        if agent_id:
            return simulation.get_agent_by_id(agent_id)
        elif agent_name:
            return simulation.get_agent_by_name(agent_name)
        
        return None
    
    def create_agent(self, simulation_id: str, **kwargs) -> Optional[Agent]:
        """
        Create a new agent in a simulation.
        
        Args:
            simulation_id: The ID of the simulation
            **kwargs: Parameters for agent creation
            
        Returns:
            Optional[Agent]: The new agent or None if the simulation was not found
        """
        simulation = self.get_simulation(simulation_id)
        if not simulation:
            return None
        
        # Convert goods data to Good objects if provided as dicts
        if "goods" in kwargs and kwargs["goods"]:
            goods = []
            for good_data in kwargs["goods"]:
                if isinstance(good_data, dict):
                    good_type = good_data.get("type")
                    if isinstance(good_type, str):
                        good_type = GoodType(good_type)
                    goods.append(Good(
                        type=good_type,
                        quality=good_data.get("quality", 0.5),
                        name=good_data.get("name")
                    ))
                else:
                    goods.append(good_data)
            kwargs["goods"] = goods
        
        # Create the agent
        agent = simulation.create_agent(**kwargs)
        
        # Add the agent to the simulation
        simulation.add_agent(agent)
        
        return agent
    
    def kill_agent(self, simulation_id: str, agent: Agent) -> bool:
        """
        Kill an agent in a simulation.
        
        Args:
            simulation_id: The ID of the simulation
            agent: The agent to kill
            
        Returns:
            bool: True if the agent was killed, False otherwise
        """
        simulation = self.get_simulation(simulation_id)
        if not simulation:
            return False
        
        return simulation.kill_agent(agent)
    
    def update_agent(self, simulation_id: str, agent: Agent, updates: Dict[str, Any]) -> bool:
        """
        Update an agent in a simulation.
        
        Args:
            simulation_id: The ID of the simulation
            agent: The agent to update
            updates: Dictionary of updates to apply
            
        Returns:
            bool: True if the agent was updated, False otherwise
        """
        simulation = self.get_simulation(simulation_id)
        if not simulation:
            return False
        
        return simulation.update_agent(agent, updates)
    
    def run_simulation_day(self, simulation_id: str) -> Optional[SimulationState]:
        """
        Run one day of a simulation.
        
        Args:
            simulation_id: The ID of the simulation
            
        Returns:
            Optional[SimulationState]: The updated simulation state or None if not found
        """
        simulation = self.get_simulation(simulation_id)
        if not simulation:
            return None
        
        simulation.process_day()
        simulation.state.day += 1
        
        # Save the state to history
        simulation.history.add(deepcopy(simulation.state))
        
        return simulation.state


# Create a singleton instance
simulation_manager = SimulationManager() 