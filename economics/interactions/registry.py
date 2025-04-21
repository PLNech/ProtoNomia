"""
Registry for economic interaction handlers in ProtoNomia.
"""
import logging
from typing import Dict, List, Optional

from models.base import Agent, EconomicInteraction, EconomicInteractionType
from economics.interactions.base import InteractionHandler
from economics.interactions.ultimatum import UltimatumGameHandler
from economics.interactions.trust import TrustGameHandler
from economics.interactions.public_goods import PublicGoodsGameHandler

logger = logging.getLogger(__name__)

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
        """Progress an existing interaction
        
        This updates the interaction state but does not directly modify agents' resources.
        The handler's complete_interaction method is responsible for updating agent resources.
        """
        if interaction.interaction_type not in self.handlers:
            raise ValueError(f"No handler registered for interaction type {interaction.interaction_type}")
        
        return self.handlers[interaction.interaction_type].progress_interaction(interaction)
    
    def process_interaction(self, interaction: EconomicInteraction) -> EconomicInteraction:
        """Process an interaction, advancing its state and applying resource changes
        
        Args:
            interaction: The interaction to process
            
        Returns:
            The updated interaction after processing
        """
        if interaction.is_complete:
            logger.debug(f"Interaction {interaction.id} is already complete")
            return interaction
        
        # Get the appropriate handler
        if interaction.interaction_type not in self.handlers:
            raise ValueError(f"No handler registered for interaction type {interaction.interaction_type}")
        
        handler = self.handlers[interaction.interaction_type]
        
        # Progress the interaction
        updated_interaction = handler.progress_interaction(interaction)
        
        # If the interaction is complete, the handler has already updated agent resources
        if updated_interaction.is_complete:
            logger.info(f"Interaction {interaction.id} completed with outcomes: {len(updated_interaction.outcomes)}")
            
            # Log narrative significance
            if updated_interaction.narrative_significance > 0.7:
                logger.info(f"Highly significant interaction: {updated_interaction.narrative_significance:.2f}")
            elif updated_interaction.narrative_significance > 0.4:
                logger.debug(f"Moderately significant interaction: {updated_interaction.narrative_significance:.2f}")
        
        return updated_interaction
    
    def find_agent_by_id(self, agent_id: str, agents: List[Agent]) -> Optional[Agent]:
        """Find an agent by its ID
        
        This helper method is useful for migrating from the old ID-based model
        to the new agent-reference model.
        
        Args:
            agent_id: The ID of the agent to find
            agents: List of agents to search in
            
        Returns:
            The agent with the given ID, or None if not found
        """
        for agent in agents:
            if agent.id == agent_id:
                return agent
        return None
    
    def migrate_interaction_to_agent_refs(self, interaction: EconomicInteraction, agents: List[Agent]) -> EconomicInteraction:
        """Migrate an interaction from using agent IDs to using agent references
        
        This is a migration helper for converting old interaction format to new format.
        
        Args:
            interaction: The interaction to migrate
            agents: List of all available agents
            
        Returns:
            The migrated interaction with direct agent references
        """
        # If the interaction already uses agent references, no need to migrate
        if not interaction.participants or all(isinstance(key, Agent) for key in interaction.participants.keys()):
            return interaction
        
        # Migrate participants
        new_participants = {}
        for agent_id, role in interaction.participants.items():
            agent = self.find_agent_by_id(agent_id, agents)
            if agent:
                new_participants[agent] = role
            else:
                logger.warning(f"Could not find agent with ID {agent_id} during migration")
        
        interaction.participants = new_participants
        
        # Migrate outcomes
        for outcome in interaction.outcomes:
            if hasattr(outcome, 'agent_id'):
                # Find the agent
                agent = self.find_agent_by_id(outcome.agent_id, agents)
                if agent:
                    outcome.agent = agent
                    # Delete the old agent_id attribute
                    delattr(outcome, 'agent_id')
                else:
                    logger.warning(f"Could not find agent with ID {outcome.agent_id} during outcome migration")
        
        return interaction 