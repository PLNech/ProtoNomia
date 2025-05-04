"""
ProtoNomia API Dependencies
This module provides dependency injections for FastAPI routes.
"""
from fastapi import Depends

from src.api.simulation_manager import SimulationManager, simulation_manager


def get_simulation_manager() -> SimulationManager:
    """
    Dependency to get the simulation manager.
    
    Returns:
        SimulationManager: Singleton instance of the simulation manager
    """
    return simulation_manager 