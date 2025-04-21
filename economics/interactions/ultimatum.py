"""
Ultimatum Game interaction for ProtoNomia.
This module implements the handler for the Ultimatum Game economic interaction.
"""
import logging
import random
from datetime import datetime
from typing import Dict, List, Optional, Any

from models.base import (
    Agent, ResourceType, ResourceBalance, EconomicInteraction, 
    EconomicInteractionType, InteractionRole, InteractionOutcome, InteractionStrategy
)
from economics.interactions.base import InteractionHandler

# Initialize logger
logger = logging.getLogger(__name__)


class UltimatumGameHandler(InteractionHandler):
    """
    Handles Ultimatum Game interactions between agents.
    
    In the Ultimatum Game:
    1. A proposer offers a split of a resource
    2. A responder can accept or reject the offer
    3. If accepted, both get their share
    4. If rejected, both get nothing
    """
    
    interaction_type = EconomicInteractionType.ULTIMATUM
    
    def create_interaction(
        self, 
        proposer: Agent, 
        responder: Agent,
        total_amount: float,
        resource_type: ResourceType = ResourceType.CREDITS,
        **kwargs
    ) -> EconomicInteraction:
        """
        Create a new ultimatum game interaction.
        
        Args:
            proposer: The agent making the offer
            responder: The agent responding to the offer
            total_amount: The total amount being divided
            resource_type: The type of resource being exchanged
            
        Returns:
            EconomicInteraction: A new interaction
        """
        logger.info(f"Creating Ultimatum Game: {proposer.name} will offer a split of {total_amount} {resource_type} to {responder.name}")
        
        # Create the interaction object
        interaction = EconomicInteraction(
            interaction_type=self.interaction_type,
            participants={
                proposer: InteractionRole.PROPOSER,
                responder: InteractionRole.RESPONDER
            },
            parameters={
                "resource_type": resource_type,
                "total_amount": total_amount,
                "proposed_amount": None,  # Will be set during progress stage
                "response": None,  # Will be set during progress stage
                "stage": "proposal"  # Current stage: proposal, response, completed
            },
            start_time=datetime.now(),
            is_complete=False
        )
        
        return interaction
    
    def progress_interaction(self, interaction: EconomicInteraction) -> EconomicInteraction:
        """
        Progress the ultimatum game to its next stage.
        
        Args:
            interaction: The interaction to progress
            
        Returns:
            The updated interaction
        """
        if interaction.is_complete:
            return interaction
        
        stage = interaction.parameters.get("stage")
        
        if stage == "proposal":
            interaction = self._handle_proposal_stage(interaction)
        elif stage == "response":
            interaction = self._handle_response_stage(interaction)
        
        return interaction
    
    def _handle_proposal_stage(self, interaction: EconomicInteraction) -> EconomicInteraction:
        """Handle the proposal stage of the ultimatum game"""
        # Find proposer
        proposer = next(agent for agent, role in interaction.participants.items() 
                      if role == InteractionRole.PROPOSER)
        
        # For MVP, simulate a proposal based on simple personality-driven strategy
        # In a full implementation, this would use more complex agent decision-making
        total_amount = interaction.parameters.get("total_amount")
        proposed_amount = self._calculate_proposal_amount(proposer, total_amount)
        
        # Update interaction parameters
        params = interaction.parameters.copy()
        params["proposed_amount"] = proposed_amount
        params["stage"] = "response"
        
        interaction.parameters = params
        
        return interaction
    
    def _calculate_proposal_amount(self, proposer: Agent, total_amount: float) -> float:
        """Calculate the amount to propose based on agent personality"""
        # Use the agent's fairness preference
        fairness = proposer.personality.fairness_preference
        
        # More sophisticated calculation would consider past interactions, relationship, etc.
        proportion = max(0.01, min(0.99, random.normalvariate(fairness, 0.1)))
        return round(total_amount * proportion, 2)
    
    def _handle_response_stage(self, interaction: EconomicInteraction) -> EconomicInteraction:
        """Handle the response stage of the ultimatum game"""
        # Find responder
        responder = next(agent for agent, role in interaction.participants.items() 
                       if role == InteractionRole.RESPONDER)
        
        # For MVP, simulate a response based on simple fairness threshold
        total_amount = interaction.parameters.get("total_amount")
        proposed_amount = interaction.parameters.get("proposed_amount")
        
        acceptance = self._decide_acceptance(responder, proposed_amount, total_amount)
        
        # Update interaction parameters
        params = interaction.parameters.copy()
        params["response"] = acceptance
        params["stage"] = "completed"
        
        interaction.parameters = params
        
        # Complete the interaction and calculate outcomes
        interaction = self.complete_interaction(interaction)
        
        return interaction
    
    def _decide_acceptance(self, responder: Agent, proposed_amount: float, total_amount: float) -> bool:
        """Decide whether to accept the proposal"""
        # This would use the agent's personality and strategy in a full implementation
        # Use a threshold based on the responder's fairness preference
        # Less fair agents will accept less fair offers
        threshold = max(0.05, min(0.5, responder.personality.fairness_preference * 0.3))
        proportion = proposed_amount / total_amount
        
        return proportion >= threshold
    
    def complete_interaction(self, interaction: EconomicInteraction) -> EconomicInteraction:
        """
        Complete the interaction and calculate outcomes.
        
        Args:
            interaction: The interaction to complete
            
        Returns:
            The completed interaction with outcomes
        """
        # Extract relevant parameters
        total_amount = interaction.parameters.get("total_amount")
        proposed_amount = interaction.parameters.get("proposed_amount")
        acceptance = interaction.parameters.get("response")
        resource_type = interaction.parameters.get("resource_type", ResourceType.CREDITS)
        
        # Find participants
        proposer = next(agent for agent, role in interaction.participants.items() 
                      if role == InteractionRole.PROPOSER)
        responder = next(agent for agent, role in interaction.participants.items() 
                       if role == InteractionRole.RESPONDER)
        
        # Get initial resources
        proposer_resources_before = self.get_resource_state(proposer)
        responder_resources_before = self.get_resource_state(responder)
        
        # Calculate outcomes based on acceptance
        if acceptance:
            # Offer accepted: proposer gets (total - proposed), responder gets proposed
            proposer_gain = total_amount - proposed_amount
            responder_gain = proposed_amount
            
            # Update resources
            # First, remove the total amount from the proposer
            self.update_agent_resource(proposer, resource_type, -total_amount)
            
            # Then, give each their share
            self.update_agent_resource(proposer, resource_type, proposer_gain)
            self.update_agent_resource(responder, resource_type, responder_gain)
        else:
            # Offer rejected: both get nothing
            proposer_gain = 0
            responder_gain = 0
        
        # Get final resources
        proposer_resources_after = self.get_resource_state(proposer)
        responder_resources_after = self.get_resource_state(responder)
        
        # Create outcome objects
        outcomes = [
            InteractionOutcome(
                interaction_id=interaction.id,
                agent=proposer,
                role=InteractionRole.PROPOSER,
                resources_before=proposer_resources_before,
                resources_after=proposer_resources_after,
                utility_change=proposer_gain if acceptance else 0,
                strategy_used=InteractionStrategy(
                    strategy_type="fair_split" if proposed_amount / total_amount >= 0.4 else "selfish",
                    parameters={"offered_proportion": proposed_amount / total_amount}
                )
            ),
            InteractionOutcome(
                interaction_id=interaction.id,
                agent=responder,
                role=InteractionRole.RESPONDER,
                resources_before=responder_resources_before,
                resources_after=responder_resources_after,
                utility_change=responder_gain,
                strategy_used=InteractionStrategy(
                    strategy_type="accept" if acceptance else "reject",
                    parameters={"acceptance_threshold": proposed_amount / total_amount if acceptance else (proposed_amount / total_amount) + 0.1}
                )
            )
        ]
        
        # Update the interaction
        interaction.outcomes = outcomes
        interaction.is_complete = True
        interaction.end_time = datetime.now()
        
        # Calculate narrative significance based on outcome
        if not acceptance:
            # Rejections are more narratively interesting
            interaction.narrative_significance = 0.7
        else:
            # Fair splits are moderately interesting
            fairness = proposed_amount / total_amount
            if fairness >= 0.45 and fairness <= 0.55:
                interaction.narrative_significance = 0.3
            else:
                interaction.narrative_significance = 0.2
        
        return interaction
    
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
        Execute an Ultimatum Game interaction between two agents directly.
        This is a legacy method for backward compatibility.
        
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
        # Create the interaction
        interaction = self.create_interaction(
            proposer=proposer,
            responder=responder,
            total_amount=total_amount,
            resource_type=currency
        )
        
        # Force the proposal amount
        params = interaction.parameters.copy()
        params["proposed_amount"] = offer_amount
        params["stage"] = "response"
        interaction.parameters = params
        
        # Force the response
        params = interaction.parameters.copy()
        params["response"] = responder_accepts
        params["stage"] = "completed"
        interaction.parameters = params
        
        # Complete the interaction
        interaction = self.complete_interaction(interaction)
        
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