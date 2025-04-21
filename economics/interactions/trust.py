"""
Trust Game interaction for ProtoNomia.
This module implements the handler for the Trust Game economic interaction.
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


class TrustGameHandler(InteractionHandler):
    """
    Handles Trust Game interactions between agents.
    
    In the Trust Game:
    1. An investor sends some amount of resources to a trustee
    2. The amount is multiplied (typically 2x or 3x)
    3. The trustee decides how much to return to the investor
    4. This tests trust and reciprocity
    """
    
    interaction_type = EconomicInteractionType.TRUST
    
    def create_interaction(
        self,
        investor: Agent,
        trustee: Agent,
        initial_amount: float,
        multiplier: float = 3.0,
        resource_type: ResourceType = ResourceType.CREDITS,
        **kwargs
    ) -> EconomicInteraction:
        """
        Create a new trust game interaction.
        
        Args:
            investor: The agent investing resources
            trustee: The agent receiving the investment
            initial_amount: The maximum amount the investor can invest
            multiplier: The multiplier for the investment (typically 2x or 3x)
            resource_type: The type of resource being exchanged
            
        Returns:
            EconomicInteraction: A new interaction
        """
        logger.info(f"Creating Trust Game: {investor.name} can invest up to {initial_amount} {resource_type} with {trustee.name}")
        
        # Create the interaction object
        interaction = EconomicInteraction(
            interaction_type=self.interaction_type,
            participants={
                investor.id: InteractionRole.INVESTOR,
                trustee.id: InteractionRole.TRUSTEE
            },
            parameters={
                "resource_type": resource_type,
                "initial_amount": initial_amount,
                "multiplier": multiplier,
                "invested_amount": None,  # Will be set during progress stage
                "returned_amount": None,  # Will be set during progress stage
                "stage": "investment"  # Current stage: investment, return, completed
            },
            start_time=datetime.now(),
            is_complete=False
        )
        
        return interaction
    
    def progress_interaction(self, interaction: EconomicInteraction) -> EconomicInteraction:
        """
        Progress the trust game to its next stage.
        
        Args:
            interaction: The interaction to progress
            
        Returns:
            The updated interaction
        """
        if interaction.is_complete:
            return interaction
        
        stage = interaction.parameters.get("stage")
        
        if stage == "investment":
            interaction = self._handle_investment_stage(interaction)
        elif stage == "return":
            interaction = self._handle_return_stage(interaction)
        
        return interaction
    
    def _handle_investment_stage(self, interaction: EconomicInteraction) -> EconomicInteraction:
        """Handle the investment stage of the trust game"""
        # Find investor
        investor_id = next(id for id, role in interaction.participants.items() 
                          if role == InteractionRole.INVESTOR)
        
        # For MVP, simulate an investment decision
        initial_amount = interaction.parameters.get("initial_amount")
        invested_amount = self._calculate_investment_amount(investor_id, initial_amount)
        
        # Update interaction parameters
        params = interaction.parameters.copy()
        params["invested_amount"] = invested_amount
        params["stage"] = "return"
        
        interaction.parameters = params
        
        return interaction
    
    def _calculate_investment_amount(self, investor_id: str, initial_amount: float) -> float:
        """Calculate the amount to invest based on agent personality"""
        # This would use the agent's personality and strategy in a full implementation
        # For MVP, use a random value
        trust = random.uniform(0.3, 0.8)  # Simulated trust level
        
        proportion = max(0.0, min(1.0, random.normalvariate(trust, 0.2)))
        return round(initial_amount * proportion, 2)
    
    def _handle_return_stage(self, interaction: EconomicInteraction) -> EconomicInteraction:
        """Handle the return stage of the trust game"""
        # Find trustee
        trustee_id = next(id for id, role in interaction.participants.items() 
                         if role == InteractionRole.TRUSTEE)
        
        # For MVP, simulate a return decision
        invested_amount = interaction.parameters.get("invested_amount")
        multiplier = interaction.parameters.get("multiplier")
        multiplied_amount = invested_amount * multiplier
        
        returned_amount = self._calculate_return_amount(trustee_id, multiplied_amount)
        
        # Update interaction parameters
        params = interaction.parameters.copy()
        params["returned_amount"] = returned_amount
        params["stage"] = "completed"
        
        interaction.parameters = params
        
        # Complete the interaction and calculate outcomes
        interaction = self.complete_interaction(interaction)
        
        return interaction
    
    def _calculate_return_amount(self, trustee_id: str, multiplied_amount: float) -> float:
        """Calculate the amount to return based on agent personality"""
        # This would use the agent's personality and strategy in a full implementation
        # For MVP, use a random value
        fairness = random.uniform(0.2, 0.6)  # Simulated fairness level
        
        proportion = max(0.0, min(1.0, random.normalvariate(fairness, 0.15)))
        return round(multiplied_amount * proportion, 2)
    
    def complete_interaction(self, interaction: EconomicInteraction) -> EconomicInteraction:
        """
        Complete the interaction and calculate outcomes.
        
        Args:
            interaction: The interaction to complete
            
        Returns:
            The completed interaction with outcomes
        """
        # Extract relevant parameters
        initial_amount = interaction.parameters.get("initial_amount")
        invested_amount = interaction.parameters.get("invested_amount")
        multiplier = interaction.parameters.get("multiplier")
        returned_amount = interaction.parameters.get("returned_amount")
        resource_type = interaction.parameters.get("resource_type", ResourceType.CREDITS)
        
        multiplied_amount = invested_amount * multiplier
        
        # Find participant IDs
        investor_id = next(id for id, role in interaction.participants.items() 
                          if role == InteractionRole.INVESTOR)
        trustee_id = next(id for id, role in interaction.participants.items() 
                         if role == InteractionRole.TRUSTEE)
        
        # Calculate outcomes
        investor_net = returned_amount - invested_amount
        trustee_net = multiplied_amount - returned_amount
        
        # Create outcome objects
        outcomes = [
            InteractionOutcome(
                interaction_id=interaction.id,
                agent_id=investor_id,
                role=InteractionRole.INVESTOR,
                resources_before=[ResourceBalance(
                    resource_type=resource_type,
                    amount=initial_amount
                )],
                resources_after=[ResourceBalance(
                    resource_type=resource_type,
                    amount=initial_amount - invested_amount + returned_amount
                )],
                utility_change=investor_net,
                strategy_used=InteractionStrategy(
                    strategy_type="high_trust" if invested_amount / initial_amount > 0.7 else "cautious",
                    parameters={"trust_level": invested_amount / initial_amount}
                )
            ),
            InteractionOutcome(
            interaction_id=interaction.id,
                agent_id=trustee_id,
            role=InteractionRole.TRUSTEE,
                resources_before=[ResourceBalance(
                    resource_type=resource_type,
                    amount=0
                )],
                resources_after=[ResourceBalance(
                    resource_type=resource_type,
                    amount=trustee_net
                )],
                utility_change=trustee_net,
                strategy_used=InteractionStrategy(
                    strategy_type="trustworthy" if returned_amount / multiplied_amount > 0.4 else "untrustworthy",
                    parameters={"return_ratio": returned_amount / multiplied_amount if multiplied_amount > 0 else 0}
                )
            )
        ]
        
        # Update the interaction
        interaction.outcomes = outcomes
        interaction.is_complete = True
        interaction.end_time = datetime.now()
        
        # Calculate narrative significance based on outcomes
        return_ratio = returned_amount / multiplied_amount if multiplied_amount > 0 else 0
        investment_ratio = invested_amount / initial_amount
        
        # High investment + high return = high cooperation (interesting!)
        if investment_ratio > 0.7 and return_ratio > 0.5:
            interaction.narrative_significance = 0.8
        # High investment + low return = betrayal (very interesting!)
        elif investment_ratio > 0.7 and return_ratio < 0.2:
            interaction.narrative_significance = 0.9
        # Low investment + high return = unexpected generosity (interesting!)
        elif investment_ratio < 0.3 and return_ratio > 0.7:
            interaction.narrative_significance = 0.7
        # Low investment + low return = mutual distrust (less interesting)
        else:
            interaction.narrative_significance = 0.3
        
        return interaction
    
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
        Execute a Trust Game interaction between two agents directly.
        This is a legacy method for backward compatibility.
        
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
        # Create the interaction
        interaction = self.create_interaction(
            investor=investor,
            trustee=trustee,
            initial_amount=investment_amount * 2,  # Set initial amount higher than investment
            multiplier=multiplier,
            resource_type=currency
        )
        
        # Force the investment amount
        params = interaction.parameters.copy()
        params["invested_amount"] = investment_amount
        params["stage"] = "return"
        interaction.parameters = params
        
        # Force the return amount
        params = interaction.parameters.copy()
        params["returned_amount"] = return_amount
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