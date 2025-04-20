"""
Ultimatum Game interaction for ProtoNomia.
This module implements the handler for the Ultimatum Game economic interaction.
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


class UltimatumGameHandler:
    """
    Handles Ultimatum Game interactions between agents.
    
    In the Ultimatum Game:
    1. A proposer offers a split of a resource
    2. A responder can accept or reject the offer
    3. If accepted, both get their share
    4. If rejected, both get nothing
    """
    
    def __init__(self):
        """Initialize the Ultimatum Game handler"""
        pass
    
    def execute(
        self, 
        proposer: Agent, 
        responder: Agent,
        total_amount: float,
        offer_amount: float,
        responder_accepts: bool,
        currency: ResourceType = ResourceType.CREDITS
    ) -> EconomicInteraction:
        """
        Execute an Ultimatum Game interaction between two agents.
        
        Args:
            proposer: The agent making the offer
            responder: The agent responding to the offer
            total_amount: The total amount being divided
            offer_amount: The amount offered to the responder
            responder_accepts: Whether the responder accepts the offer
            currency: The type of resource being exchanged
            
        Returns:
            EconomicInteraction: The completed interaction
        """
        logger.info(f"Executing Ultimatum Game: {proposer.name} offers {offer_amount} of {total_amount} {currency} to {responder.name}")
        
        # Create the interaction object
        interaction = EconomicInteraction(
            interaction_type=EconomicInteractionType.ULTIMATUM,
            participants={
                proposer.id: InteractionRole.PROPOSER,
                responder.id: InteractionRole.RESPONDER
            },
            parameters={
                "total_amount": total_amount,
                "offer_amount": offer_amount,
                "responder_accepts": responder_accepts,
                "currency": currency.value
            },
            start_time=datetime.now()
        )
        
        # Record initial resource states
        proposer_resources_before = self._get_resource_state(proposer)
        responder_resources_before = self._get_resource_state(responder)
        
        # Execute the game logic
        proposer_change = 0.0
        responder_change = 0.0
        
        if responder_accepts:
            # Offer accepted: transfer resources
            proposer_change = total_amount - offer_amount  # Proposer keeps the rest
            responder_change = offer_amount               # Responder gets the offer
            
            # Update agent resources
            self._update_resource(proposer, currency, proposer_change)
            self._update_resource(responder, currency, responder_change)
            
            logger.info(f"Offer accepted: {proposer.name} keeps {proposer_change}, {responder.name} gets {responder_change}")
        else:
            # Offer rejected: no one gets anything
            proposer_change = 0.0
            responder_change = 0.0
            logger.info(f"Offer rejected: no resources transferred")
        
        # Record outcomes
        proposer_outcome = InteractionOutcome(
            interaction_id=interaction.id,
            agent_id=proposer.id,
            role=InteractionRole.PROPOSER,
            resources_before=proposer_resources_before,
            resources_after=self._get_resource_state(proposer),
            utility_change=proposer_change
        )
        
        responder_outcome = InteractionOutcome(
            interaction_id=interaction.id,
            agent_id=responder.id,
            role=InteractionRole.RESPONDER,
            resources_before=responder_resources_before,
            resources_after=self._get_resource_state(responder),
            utility_change=responder_change
        )
        
        # Update interaction
        interaction.outcomes = [proposer_outcome, responder_outcome]
        interaction.end_time = datetime.now()
        interaction.is_complete = True
        
        # Set narrative significance based on the interaction
        fairness = offer_amount / total_amount
        if responder_accepts:
            if fairness < 0.3:
                # Very unfair offer was accepted - noteworthy!
                interaction.narrative_significance = 0.8
            elif fairness > 0.5:
                # Fair or generous offer was accepted - somewhat noteworthy
                interaction.narrative_significance = 0.4
            else:
                # Moderately unfair but accepted - less noteworthy
                interaction.narrative_significance = 0.3
        else:
            if fairness > 0.4:
                # Fairly reasonable offer was rejected - noteworthy!
                interaction.narrative_significance = 0.7
            else:
                # Unfair offer was rejected - expected, less noteworthy
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