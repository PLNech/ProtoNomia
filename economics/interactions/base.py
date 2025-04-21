from datetime import datetime
from typing import Dict, List, Any, Optional
from abc import ABC, abstractmethod
import logging

from models.base import (
    Agent, EconomicInteraction, EconomicInteractionType, InteractionRole,
    InteractionOutcome, InteractionStrategy, ResourceBalance, ResourceType
)

logger = logging.getLogger(__name__)

class InteractionHandler(ABC):
    """Base class for handling a specific economic interaction type"""
    
    interaction_type: EconomicInteractionType
    
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
        if hasattr(agent, 'resources') and hasattr(agent.resources, 'balances'):
            return agent.resources.balances.get(resource_type, 0.0)
        
        # Legacy support for old Agent model
        for resource in agent.resources:
            if resource.resource_type == resource_type:
                return resource.amount
        return 0.0
    
    def update_agent_resources(
        self, 
        agent: Agent, 
        resource_type: ResourceType, 
        amount_change: float
    ) -> bool:
        """Update an agent's resource balance
        
        Args:
            agent: The agent to update
            resource_type: The type of resource to update
            amount_change: The amount to add (positive) or subtract (negative)
            
        Returns:
            True if the update was successful, False if insufficient resources
        """
        # Check if agent uses the new ResourceBalance model
        if hasattr(agent, 'resources') and hasattr(agent.resources, 'balances'):
            current_amount = agent.resources.balances.get(resource_type, 0.0)
            
            # Check if we have enough resources to subtract
            if amount_change < 0 and current_amount + amount_change < 0:
                return False
            
            # Update the resource
            agent.resources.balances[resource_type] = current_amount + amount_change
            return True
        
        # Legacy support for old Agent model
        # Find the resource
        resource = None
        for r in agent.resources:
            if r.resource_type == resource_type:
                resource = r
                break
        
        # If resource doesn't exist and we're adding, create it
        if resource is None and amount_change > 0:
            new_resource = ResourceBalance(
                resource_type=resource_type,
                amount=amount_change,
                last_updated=datetime.now()
            )
            agent.resources.append(new_resource)
            return True
        
        # If resource doesn't exist and we're subtracting, fail
        if resource is None and amount_change < 0:
            return False
        
        # Check if we have enough resources to subtract
        if amount_change < 0 and resource.amount + amount_change < 0:
            return False
        
        # Update the resource
        resource.amount += amount_change
        resource.last_updated = datetime.now()
        return True
    
    def calculate_narrative_significance(
        self, 
        interaction: EconomicInteraction, 
        outcomes: List[InteractionOutcome]
    ) -> float:
        """Calculate the narrative significance of an interaction based on outcomes
        
        Args:
            interaction: The interaction to evaluate
            outcomes: The outcomes of the interaction
            
        Returns:
            Narrative significance score (0.0-1.0)
        """
        # Base significance based on interaction type
        base_significance = {
            EconomicInteractionType.ULTIMATUM: 0.4,
            EconomicInteractionType.DICTATOR: 0.3,
            EconomicInteractionType.PUBLIC_GOODS: 0.5,
            EconomicInteractionType.TRUST: 0.6,
            EconomicInteractionType.COURNOT: 0.3,
            EconomicInteractionType.BERTRAND: 0.3,
            EconomicInteractionType.DOUBLE_AUCTION: 0.4,
            EconomicInteractionType.OLIGOPOLY: 0.5,
            EconomicInteractionType.RENT_SEEKING: 0.5,
            EconomicInteractionType.MATCHING: 0.3,
            EconomicInteractionType.PRINCIPAL_AGENT: 0.5,
            EconomicInteractionType.COORDINATION: 0.4,
            EconomicInteractionType.SIGNALING: 0.5,
            EconomicInteractionType.BEAUTY_CONTEST: 0.4,
            EconomicInteractionType.COMMON_POOL: 0.6,
            EconomicInteractionType.AGENT_BASED_MACRO: 0.3,
            EconomicInteractionType.EVOLUTIONARY: 0.4,
            EconomicInteractionType.INSTITUTIONAL: 0.5,
            EconomicInteractionType.NETWORK_FORMATION: 0.4,
            EconomicInteractionType.SABOTAGE: 0.7
        }.get(interaction.interaction_type, 0.5)
        
        # Adjust based on outcomes
        significance_factors = []
        
        # Look for large utility changes
        for outcome in outcomes:
            abs_utility_change = abs(outcome.utility_change)
            if abs_utility_change > 100:
                significance_factors.append(0.3)  # Very significant utility change
            elif abs_utility_change > 50:
                significance_factors.append(0.2)  # Significant utility change
            elif abs_utility_change > 20:
                significance_factors.append(0.1)  # Moderate utility change
        
        # Look for interesting strategy patterns
        strategy_types = [outcome.strategy_used.strategy_type for outcome in outcomes if outcome.strategy_used]
        
        # Conflicting strategies are interesting
        if "cooperator" in strategy_types and "free_rider" in strategy_types:
            significance_factors.append(0.2)
        
        if "trustworthy" in strategy_types and "untrustworthy" in strategy_types:
            significance_factors.append(0.25)
        
        # Extreme strategies are interesting
        extreme_strategies = ["high_trust", "always_defect", "fair_split", "selfish"]
        for strategy in extreme_strategies:
            if strategy in strategy_types:
                significance_factors.append(0.15)
        
        # Calculate final significance
        final_significance = base_significance
        for factor in significance_factors:
            # Add each factor, but with diminishing returns
            remaining_gap = 1.0 - final_significance
            final_significance += factor * remaining_gap
        
        return min(1.0, final_significance)
    
    def process(self, interaction: EconomicInteraction, agents: Dict[str, Agent]) -> EconomicInteraction:
        """Process an interaction, updating it and potentially affected agents
        
        Args:
            interaction: The interaction to process
            agents: Dictionary of agents keyed by agent ID
            
        Returns:
            Updated interaction
        """
        if not interaction.is_complete:
            # Progress the interaction
            updated_interaction = self.progress_interaction(interaction)
            
            # If the interaction is now complete, apply outcomes
            if updated_interaction.is_complete:
                updated_interaction = self.complete_interaction(updated_interaction)
                
                # Apply outcomes to agents
                if hasattr(updated_interaction, 'outcomes') and updated_interaction.outcomes:
                    for outcome in updated_interaction.outcomes:
                        if outcome.agent_id in agents:
                            agent = agents[outcome.agent_id]
                            # Update resources
                            for resource_type, amount in outcome.resource_changes.items():
                                self.update_agent_resources(agent, resource_type, amount)
            
            return updated_interaction
            
        return interaction