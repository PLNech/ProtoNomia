from datetime import datetime
import random
import logging
from typing import Dict, List, Any, Optional

from ...models.base import (
    Agent, EconomicInteraction, EconomicInteractionType, InteractionRole,
    InteractionOutcome, InteractionStrategy, ResourceBalance, ResourceType
)
from .base import InteractionHandler

logger = logging.getLogger(__name__)

class UltimatumGameHandler(InteractionHandler):
    """Handler for the Ultimatum Game interaction
    
    In the Ultimatum Game:
    1. The proposer offers a split of a resource
    2. The responder either accepts (both get their shares) or rejects (both get nothing)
    
    This tests fairness norms and bargaining behavior.
    """
    
    interaction_type = EconomicInteractionType.ULTIMATUM
    
    def create_interaction(self, proposer: Agent, responder: Agent, 
                          amount: float, resource_type: ResourceType = ResourceType.CREDITS) -> EconomicInteraction:
        """Create a new ultimatum game interaction
        
        Args:
            proposer: The agent making the offer
            responder: The agent responding to the offer
            amount: The total amount to be split
            resource_type: The type of resource being split
            
        Returns:
            A new ultimatum game interaction
        """
        # Check if proposer has enough resources
        proposer_balance = self.get_resource_balance(proposer, resource_type)
        
        if proposer_balance < amount:
            raise ValueError(f"Proposer {proposer.name} doesn't have enough {resource_type} ({proposer_balance}) for this interaction ({amount})")
        
        # Create the interaction
        return EconomicInteraction(
            interaction_type=self.interaction_type,
            participants={
                proposer.id: InteractionRole.PROPOSER,
                responder.id: InteractionRole.RESPONDER
            },
            parameters={
                "resource_type": resource_type,
                "total_amount": amount,
                "proposed_amount": None,  # Will be set when proposer makes an offer
                "response": None,  # Will be set when responder responds
                "stage": "proposal"  # Current stage: proposal, response, completed
            },
            start_time=datetime.now(),
            is_complete=False
        )
    
    def progress_interaction(self, interaction: EconomicInteraction) -> EconomicInteraction:
        """Progress the ultimatum game to its next stage
        
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
        """Handle the proposal stage of the ultimatum game
        
        Args:
            interaction: The interaction to update
            
        Returns:
            The updated interaction
        """
        # Find proposer
        proposer_id = next(id for id, role in interaction.participants.items() 
                          if role == InteractionRole.PROPOSER)
        
        # For MVP, simulate a proposal based on simple personality-driven strategy
        # In a full implementation, this would use more complex agent decision-making
        total_amount = interaction.parameters.get("total_amount")
        proposed_amount = self._calculate_proposal_amount(proposer_id, total_amount)
        
        # Update interaction parameters
        params = interaction.parameters.copy()
        params["proposed_amount"] = proposed_amount
        params["stage"] = "response"
        
        interaction.parameters = params
        
        return interaction
    
    def _calculate_proposal_amount(self, proposer_id: str, total_amount: float) -> float:
        """Calculate the amount to propose based on agent personality
        
        Args:
            proposer_id: ID of the proposing agent
            total_amount: Total amount to be split
            
        Returns:
            Amount to propose to the responder
        """
        # This would use the agent's personality and strategy in a full implementation
        # For MVP, use a random value weighted by fairness preference
        fairness = random.uniform(0.2, 0.5)  # Simulated fairness preference
        
        # More sophisticated calculation would consider past interactions, relationship, etc.
        proportion = max(0.01, min(0.99, random.normalvariate(fairness, 0.1)))
        return round(total_amount * proportion, 2)
    
    def _handle_response_stage(self, interaction: EconomicInteraction) -> EconomicInteraction:
        """Handle the response stage of the ultimatum game
        
        Args:
            interaction: The interaction to update
            
        Returns:
            The updated interaction
        """
        # Find responder
        responder_id = next(id for id, role in interaction.participants.items() 
                           if role == InteractionRole.RESPONDER)
        
        # For MVP, simulate a response based on simple fairness threshold
        total_amount = interaction.parameters.get("total_amount")
        proposed_amount = interaction.parameters.get("proposed_amount")
        
        acceptance = self._decide_acceptance(responder_id, proposed_amount, total_amount)
        
        # Update interaction parameters
        params = interaction.parameters.copy()
        params["response"] = acceptance
        params["stage"] = "completed"
        
        interaction.parameters = params
        
        # Complete the interaction and calculate outcomes
        interaction = self.complete_interaction(interaction)
        
        return interaction
    
    def _decide_acceptance(self, responder_id: str, proposed_amount: float, total_amount: float) -> bool:
        """Decide whether to accept the proposal
        
        Args:
            responder_id: ID of the responding agent
            proposed_amount: Amount proposed to the responder
            total_amount: Total amount being split
            
        Returns:
            True if the offer is accepted, False otherwise
        """
        # This would use the agent's personality and strategy in a full implementation
        # For MVP, use a simple fairness threshold
        proportion = proposed_amount / total_amount
        threshold = random.uniform(0.1, 0.3)  # Minimum acceptable proportion
        
        return proportion >= threshold
    
    def complete_interaction(self, interaction: EconomicInteraction) -> EconomicInteraction:
        """Complete the interaction and calculate outcomes
        
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
        
        # Find participant IDs
        proposer_id = next(id for id, role in interaction.participants.items() 
                          if role == InteractionRole.PROPOSER)
        responder_id = next(id for id, role in interaction.participants.items() 
                           if role == InteractionRole.RESPONDER)
        
        # Calculate outcomes based on acceptance
        if acceptance:
            # Offer accepted: proposer gets (total - proposed), responder gets proposed
            proposer_gain = total_amount - proposed_amount
            responder_gain = proposed_amount
        else:
            # Offer rejected: both get nothing
            proposer_gain = 0
            responder_gain = 0
        
        # Create outcome objects
        outcomes = [
            InteractionOutcome(
                interaction_id=interaction.id,
                agent_id=proposer_id,
                role=InteractionRole.PROPOSER,
                resources_before=[ResourceBalance(
                    resource_type=resource_type,
                    amount=total_amount
                )],
                resources_after=[ResourceBalance(
                    resource_type=resource_type,
                    amount=proposer_gain
                )],
                utility_change=proposer_gain - total_amount,
                strategy_used=InteractionStrategy(
                    strategy_type="fair_split" if proposed_amount / total_amount >= 0.4 else "selfish",
                    parameters={"offered_proportion": proposed_amount / total_amount}
                )
            ),
            InteractionOutcome(
                interaction_id=interaction.id,
                agent_id=responder_id,
                role=InteractionRole.RESPONDER,
                resources_before=[ResourceBalance(
                    resource_type=resource_type,
                    amount=0
                )],
                resources_after=[ResourceBalance(
                    resource_type=resource_type,
                    amount=responder_gain
                )],
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
        
        # Calculate narrative significance
        interaction.narrative_significance = self.calculate_narrative_significance(interaction, outcomes)
        
        return interaction