"""
Trust Game interaction for ProtoNomia.
This module implements the handler for the Trust Game economic interaction.
"""
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

from models.base import (
    Agent, ResourceType, ResourceBalance, EconomicInteraction, 
    EconomicInteractionType, InteractionRole, InteractionOutcome
)

# Initialize logger
logger = logging.getLogger(__name__)


class TrustGameHandler:
    """
    Handles Trust Game interactions between agents.
    
    In the Trust Game:
    1. An investor sends some amount of resources to a trustee
    2. The amount is multiplied (typically 2x or 3x)
    3. The trustee decides how much to return to the investor
    4. This tests trust and reciprocity
    """
    
    def __init__(self):
        """Initialize the Trust Game handler"""
        pass
    
    def execute(
        self,
        investor: Agent,
        trustee: Agent,
        investment_amount: float,
        multiplier: float = 3.0,
        return_amount: float = 0.0,
        currency: ResourceType = ResourceType.CREDITS
    ) -> EconomicInteraction:
        """
        Execute a Trust Game interaction between two agents.
        
        Args:
            investor: The agent investing resources
            trustee: The agent receiving the investment
            investment_amount: The amount invested
            multiplier: The multiplier for the investment (typically 2x or 3x)
            return_amount: The amount returned by the trustee
            currency: The type of resource being exchanged
            
        Returns:
            EconomicInteraction: The completed interaction
        """
        logger.info(f"Executing Trust Game: {investor.name} invests {investment_amount} {currency} with {trustee.name}")
        
        # Create the interaction object
        interaction = EconomicInteraction(
            interaction_type=EconomicInteractionType.TRUST,
            participants={
                investor.id: InteractionRole.INVESTOR,
                trustee.id: InteractionRole.TRUSTEE
            },
            parameters={
                "investment_amount": investment_amount,
                "multiplier": multiplier,
                "return_amount": return_amount,
                "currency": currency.value
            },
            start_time=datetime.now()
        )
        
        # Record initial resource states
        investor_resources_before = self._get_resource_state(investor)
        trustee_resources_before = self._get_resource_state(trustee)
        
        # Calculate the multiplied amount
        multiplied_amount = investment_amount * multiplier
        
        # Ensure return amount doesn't exceed multiplied amount
        return_amount = min(return_amount, multiplied_amount)
        
        # Execute the game logic
        
        # Step 1: Investor sends investment
        self._update_resource(investor, currency, -investment_amount)
        
        # Step 2: Trustee receives multiplied investment
        self._update_resource(trustee, currency, multiplied_amount)
        
        # Step 3: Trustee returns some amount
        self._update_resource(trustee, currency, -return_amount)
        self._update_resource(investor, currency, return_amount)
        
        # Calculate net changes
        investor_change = return_amount - investment_amount
        trustee_change = multiplied_amount - return_amount
        
        logger.info(f"Trust Game results: {investor.name} net change: {investor_change}, {trustee.name} net change: {trustee_change}")
        
        # Record outcomes
        investor_outcome = InteractionOutcome(
            interaction_id=interaction.id,
            agent_id=investor.id,
            role=InteractionRole.INVESTOR,
            resources_before=investor_resources_before,
            resources_after=self._get_resource_state(investor),
            utility_change=investor_change
        )
        
        trustee_outcome = InteractionOutcome(
            interaction_id=interaction.id,
            agent_id=trustee.id,
            role=InteractionRole.TRUSTEE,
            resources_before=trustee_resources_before,
            resources_after=self._get_resource_state(trustee),
            utility_change=trustee_change
        )
        
        # Update interaction
        interaction.outcomes = [investor_outcome, trustee_outcome]
        interaction.end_time = datetime.now()
        interaction.is_complete = True
        
        # Set narrative significance based on the interaction
        return_ratio = return_amount / multiplied_amount if multiplied_amount > 0 else 0
        
        # High investment + high return = high cooperation (interesting!)
        if investment_amount > 5.0 and return_ratio > 0.5:
            interaction.narrative_significance = 0.8
        # High investment + low return = betrayal (very interesting!)
        elif investment_amount > 5.0 and return_ratio < 0.2:
            interaction.narrative_significance = 0.9
        # Low investment + high return = unexpected generosity (interesting!)
        elif investment_amount < 2.0 and return_ratio > 0.7:
            interaction.narrative_significance = 0.7
        # Low investment + low return = mutual distrust (less interesting)
        else:
            interaction.narrative_significance = 0.3
        
        return interaction
    
    def _get_resource_state(self, agent: Agent) -> List[ResourceBalance]:
        """Get a copy of the agent's current resources"""
        return [
            ResourceBalance(
                resource_type=resource.resource_type,
                amount=resource.amount,
                last_updated=resource.last_updated
            )
            for resource in agent.resources
        ]
    
    def _update_resource(self, agent: Agent, resource_type: ResourceType, change: float) -> None:
        """Update the agent's resource of the given type"""
        # Find the resource
        for resource in agent.resources:
            if resource.resource_type == resource_type:
                resource.amount += change
                resource.last_updated = datetime.now()
                return
        
        # If resource doesn't exist yet, add it
        if change > 0:
            agent.resources.append(ResourceBalance(
                resource_type=resource_type,
                amount=change,
                last_updated=datetime.now()
            ))