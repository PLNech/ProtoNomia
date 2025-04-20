"""
Economic interaction handlers for different game theory simulations.

This package contains handlers for various economic games and interactions
that can occur between agents in the simulation.
"""

from datetime import datetime
from typing import Dict, List, Any, Optional
import logging

from ...models.base import (
    Agent, EconomicInteraction, EconomicInteractionType, InteractionRole,
    InteractionOutcome, InteractionStrategy, ResourceBalance, ResourceType
)

from .base import InteractionHandler
from .ultimatum import UltimatumGameHandler
from .trust import TrustGameHandler
from .public_goods import PublicGoodsGameHandler

logger = logging.getLogger(__name__)

# Registry to manage all interaction handlers
class InteractionRegistry:
    """Registry of all available interaction handlers"""
    
    def __init__(self):
        self.handlers: Dict[EconomicInteractionType, InteractionHandler] = {}
        self._register_handlers()
    
    def _register_handlers(self):
        """Register all available interaction handlers"""
        # Register handlers
        self.register_handler(UltimatumGameHandler())
        self.register_handler(TrustGameHandler())
        self.register_handler(PublicGoodsGameHandler())
        
        # TODO: Register more handlers as they are implemented
        # self.register_handler(CournotCompetitionHandler())
        # self.register_handler(BertrandCompetitionHandler())
        # self.register_handler(PrincipalAgentHandler())
        # self.register_handler(CoordinationGameHandler())
        # etc.
    
    def register_handler(self, handler: InteractionHandler):
        """Register a new interaction handler"""
        self.handlers[handler.interaction_type] = handler
        logger.info(f"Registered handler for {handler.interaction_type}")
    
    def create_interaction(self, interaction_type: EconomicInteractionType, **kwargs) -> EconomicInteraction:
        """Create a new interaction of the specified type"""
        if interaction_type not in self.handlers:
            raise ValueError(f"No handler registered for interaction type {interaction_type}")
        
        return self.handlers[interaction_type].create_interaction(**kwargs)
    
    def progress_interaction(self, interaction: EconomicInteraction) -> EconomicInteraction:
        """Progress an existing interaction"""
        if interaction.interaction_type not in self.handlers:
            raise ValueError(f"No handler registered for interaction type {interaction.interaction_type}")
        
        return self.handlers[interaction.interaction_type].progress_interaction(interaction)

# Import all handlers for easy access
__all__ = [
    'InteractionHandler',
    'UltimatumGameHandler',
    'TrustGameHandler',
    'PublicGoodsGameHandler',
    'InteractionRegistry'
]

"""Economic interaction handlers for ProtoNomia"""