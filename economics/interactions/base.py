from datetime import datetime
from typing import Dict, List, Any, Optional
from abc import ABC, abstractmethod
import logging

from models.base import (
    Agent, EconomicInteraction, InteractionRole,
    InteractionOutcome, InteractionStrategy, ResourceBalance, ResourceType, ActionType
)

logger = logging.getLogger(__name__)

class InteractionHandler(ABC):
    """Base class for handling a specific economic interaction type"""
    
    interaction_type: ActionType
    
    @abstractmethod
    def create_interaction(self, **kwargs) -> EconomicInteraction:
        """Create a new interaction instance
        
        Args:
            **kwargs: Handler-specific parameters
            
        Returns:
            A new economic interaction
        """
        pass
    
    @abstractmethod
    def progress_interaction(self, interaction: EconomicInteraction) -> EconomicInteraction:
        """Progress the interaction to its next state or complete it
        
        Args:
            interaction: The interaction to progress
            
        Returns:
            The updated interaction
        """
        pass
    
    @abstractmethod
    def complete_interaction(self, interaction: EconomicInteraction) -> EconomicInteraction:
        """Complete the interaction and calculate outcomes
        
        Args:
            interaction: The interaction to complete
            
        Returns:
            The completed interaction with outcomes
        
        Implementation MUST update the agent resources directly based on the
        calculated outcomes. Don't just calculate the outcomes - apply them!
        """
        pass
    
    def get_resource_balance(self, agent: Agent, resource_type: ResourceType) -> float:
        """Helper to get an agent's balance of a specific resource
        
        Args:
            agent: The agent to query
            resource_type: The type of resource to get
            
        Returns:
            The amount of the resource, or 0 if not found
        """
        for resource in agent.resources:
            if resource.resource_type == resource_type:
                return resource.amount
        return 0.0
    
    def update_agent_resource(self, agent: Agent, resource_type: ResourceType, change: float) -> bool:
        """Update an agent's resource of the given type by the specified amount.
        
        Args:
            agent: The agent whose resources to update
            resource_type: The type of resource to update
            change: The amount to add (positive) or subtract (negative)
            
        Returns:
            True if the update was successful, False if insufficient resources
        """
        # Find the resource
        resource = None
        for r in agent.resources:
            if r.resource_type == resource_type:
                resource = r
                break
        
        # If resource doesn't exist and we're adding, create it
        if resource is None and change > 0:
            agent.resources.append(ResourceBalance(
                resource_type=resource_type,
                amount=change,
                last_updated=datetime.now()
            ))
            return True
        
        # If resource doesn't exist and we're subtracting, fail
        if resource is None and change < 0:
            logger.warning(f"Cannot subtract {-change} of {resource_type} from {agent.name} - no such resource")
            return False
        
        # Check if we have enough resources to subtract
        if change < 0 and resource.amount + change < 0:
            logger.warning(f"Cannot subtract {-change} of {resource_type} from {agent.name} - insufficient balance ({resource.amount})")
            return False
        
        # Update the resource
        resource.amount += change
        resource.last_updated = datetime.now()
        logger.debug(f"Updated {agent.name}'s {resource_type} by {change}, new balance: {resource.amount}")
        return True
    
    def get_resource_state(self, agent: Agent) -> List[ResourceBalance]:
        """Get a copy of the agent's current resources
        
        Useful for recording the state before an interaction
        
        Args:
            agent: The agent whose resources to copy
            
        Returns:
            A list of ResourceBalance objects
        """
        return [
            ResourceBalance(
                resource_type=resource.resource_type,
                amount=resource.amount,
                last_updated=resource.last_updated
            )
            for resource in agent.resources
        ]
    
    def apply_outcomes(self, interaction: EconomicInteraction) -> None:
        """Apply the outcomes of an interaction to the involved agents
        
        This updates the agents' resources based on the outcomes calculated
        in the complete_interaction method.
        
        Args:
            interaction: The completed interaction with outcomes
        """
        if not interaction.is_complete or not interaction.outcomes:
            logger.warning("Cannot apply outcomes - interaction is not complete or has no outcomes")
            return
        
        for outcome in interaction.outcomes:
            agent = outcome.agent
            
            # Get the resource changes by comparing before and after
            for resource_after in outcome.resources_after:
                resource_type = resource_after.resource_type
                amount_after = resource_after.amount
                
                # Find the corresponding "before" resource
                amount_before = 0
                for resource_before in outcome.resources_before:
                    if resource_before.resource_type == resource_type:
                        amount_before = resource_before.amount
                        break
                
                # Calculate and apply the change
                change = amount_after - amount_before
                if change != 0:
                    self.update_agent_resource(agent, resource_type, change)
    
    def calculate_narrative_significance(self, interaction: EconomicInteraction) -> float:
        """Calculate the narrative significance of an interaction based on outcomes
        
        Args:
            interaction: The interaction to evaluate
            
        Returns:
            Narrative significance score (0.0-1.0)
        """
        # Override in subclasses for interaction-specific significance calculation
        return 0.5  # Default medium significance