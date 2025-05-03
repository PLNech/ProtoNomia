"""
ProtoNomia API Routes
This module provides the API routes for the ProtoNomia simulation.
"""

from api.routes.simulation import router as simulation_router
from api.routes.agent import router as agent_router

__all__ = ['simulation_router', 'agent_router']
