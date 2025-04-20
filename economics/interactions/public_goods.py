from datetime import datetime
import random
import logging
from typing import Dict, List, Any, Optional
import math

from ...models.base import (
    Agent, EconomicInteraction, EconomicInteractionType, InteractionRole,
    InteractionOutcome, InteractionStrategy, ResourceBalance, ResourceType
)
from .base import InteractionHandler

logger = logging.getLogger(__name__)

class PublicGoodsGameHandler(InteractionHandler):
    """Handler for the Public Goods Game interaction
    
    In the Public Goods Game:
    1. Each participant receives an endowment
    2. They decide how much to contribute to a common pool
    3. The pool is multiplied by some factor
    4. The resulting amount is distributed equally among all participants
    
    This tests cooperation and free-riding in collective action problems.
    """
    
    interaction_type = EconomicInteractionType.PUBLIC_GOODS
    
    def create_interaction(self, participants: List[Agent], 
                         endowment: float, multiplier: float = 1.6,
                         resource_type: ResourceType = ResourceType.CREDITS) -> EconomicInteraction:
        """Create a new public goods game interaction
        
        Args:
            participants: List of participating agents
            endowment: Amount each participant receives at start
            multiplier: Multiplier for the common pool (should be > 1 and < n)
            resource_type: Type of resource being used
            
        Returns:
            A new public goods game interaction
        """
        # Ensure we have at least 2 participants
        if len(participants) < 2:
            raise ValueError("Public Goods Game requires at least 2 participants")
        
        # Check if all participants have enough resources
        for agent in participants:
            agent_balance = self.get_resource_balance(agent, resource_type)
            if agent_balance < endowment:
                raise ValueError(f"Agent {agent.name} doesn't have enough {resource_type} ({agent_balance}) for this interaction ({endowment})")
        
        # Create the interaction
        participant_dict = {
            agent.id: InteractionRole.CONTRIBUTOR for agent in participants
        }
        
        return EconomicInteraction(
            interaction_type=self.interaction_type,
            participants=participant_dict,
            parameters={
                "resource_type": resource_type,
                "endowment": endowment,
                "multiplier": multiplier,
                "contributions": {},  # Will be filled with agent_id -> contribution
                "stage": "contribution"  # Current stage: contribution, completed
            },
            start_time=datetime.now(),
            is_complete=False
        )
    
    def progress_interaction(self, interaction: EconomicInteraction) -> EconomicInteraction:
        """Progress the public goods game to its next stage
        
        Args:
            interaction: The interaction to progress
            
        Returns:
            The updated interaction
        """
        if interaction.is_complete:
            return interaction
        
        stage = interaction.parameters.get("stage")
        
        if stage == "contribution":
            interaction = self._handle_contribution_stage(interaction)
        
        return interaction
    
    def _handle_contribution_stage(self, interaction: EconomicInteraction) -> EconomicInteraction:
        """Handle the contribution stage
        
        Args:
            interaction: The interaction to update
            
        Returns:
            The updated interaction
        """
        # For each participant, determine their contribution
        params = interaction.parameters.copy()
        endowment = params.get("endowment")
        
        contributions = {}
        for agent_id in interaction.participants.keys():
            # Simulate contribution decision based on personality
            contribution = self._calculate_contribution(agent_id, endowment)
            contributions[agent_id] = contribution
        
        params["contributions"] = contributions
        params["stage"] = "completed"
        
        interaction.parameters = params
        
        # Complete the interaction and calculate outcomes
        interaction = self.complete_interaction(interaction)
        
        return interaction
    
    def _calculate_contribution(self, agent_id: str, endowment: float) -> float:
        """Calculate how much an agent contributes based on personality
        
        Args:
            agent_id: ID of the contributing agent
            endowment: Amount the agent can contribute
            
        Returns:
            Amount the agent contributes
        """
        # This would use the agent's personality and strategy in a full implementation
        # For MVP, use a random value weighted by cooperativeness
        cooperativeness = random.uniform(0.2, 0.8)  # Simulated cooperativeness level
        
        # More sophisticated calculation would consider past interactions, group composition, etc.
        proportion = max(0.0, min(1.0, random.normalvariate(cooperativeness, 0.2)))
        return round(endowment * proportion, 2)
    
    def complete_interaction(self, interaction: EconomicInteraction) -> EconomicInteraction:
        """Complete the interaction and calculate outcomes
        
        Args:
            interaction: The interaction to complete
            
        Returns:
            The completed interaction with outcomes
        """
        # Extract relevant parameters
        endowment = interaction.parameters.get("endowment")
        multiplier = interaction.parameters.get("multiplier")
        contributions = interaction.parameters.get("contributions", {})
        resource_type = interaction.parameters.get("resource_type", ResourceType.CREDITS)
        
        # Calculate the total contribution and return
        total_contribution = sum(contributions.values())
        total_return = total_contribution * multiplier
        per_agent_return = total_return / len(interaction.participants) if interaction.participants else 0
        
        # Calculate average contribution for reference
        avg_contribution = total_contribution / len(contributions) if contributions else 0
        
        # Create outcome objects
        outcomes = []
        for agent_id, role in interaction.participants.items():
            contribution = contributions.get(agent_id, 0)
            final_balance = endowment - contribution + per_agent_return
            utility_change = final_balance - endowment
            
            # Determine strategy type based on contribution relative to average
            if contribution <= 0.2 * endowment:
                strategy_type = "free_rider"
            elif contribution >= 0.8 * endowment:
                strategy_type = "cooperator"
            elif contribution < avg_contribution * 0.8:
                strategy_type = "under_contributor"
            elif contribution > avg_contribution * 1.2:
                strategy_type = "over_contributor"
            else:
                strategy_type = "moderate_contributor"
            
            outcomes.append(
                InteractionOutcome(
                    interaction_id=interaction.id,
                    agent_id=agent_id,
                    role=role,
                    resources_before=[ResourceBalance(
                        resource_type=resource_type,
                        amount=endowment
                    )],
                    resources_after=[ResourceBalance(
                        resource_type=resource_type,
                        amount=final_balance
                    )],
                    utility_change=utility_change,
                    strategy_used=InteractionStrategy(
                        strategy_type=strategy_type,
                        parameters={
                            "contribution_ratio": contribution / endowment if endowment > 0 else 0,
                            "relative_to_avg": contribution / avg_contribution if avg_contribution > 0 else 0
                        }
                    )
                )
            )
        
        # Update the interaction
        interaction.outcomes = outcomes
        interaction.is_complete = True
        interaction.end_time = datetime.now()
        
        # Calculate narrative significance
        # Base significance calculation from parent class
        base_significance = self.calculate_narrative_significance(interaction, outcomes)
        
        # Add public goods specific significance factors:
        
        # 1. Measure heterogeneity in contributions (standard deviation)
        contribution_values = list(contributions.values())
        if contribution_values:
            mean = sum(contribution_values) / len(contribution_values)
            variance = sum((x - mean) ** 2 for x in contribution_values) / len(contribution_values)
            std_dev = math.sqrt(variance)
            normalized_std_dev = std_dev / endowment if endowment > 0 else 0
            
            # High standard deviation means interesting heterogeneity
            heterogeneity_factor = min(0.3, normalized_std_dev)
        else:
            heterogeneity_factor = 0
        
        # 2. Check if there are extreme contributors or free-riders
        strategy_types = [outcome.strategy_used.strategy_type for outcome in outcomes]
        has_free_riders = "free_rider" in strategy_types
        has_cooperators = "cooperator" in strategy_types
        
        extreme_behavior_factor = 0
        if has_free_riders and has_cooperators:
            # Most interesting when both extremes exist
            extreme_behavior_factor = 0.25
        elif has_free_riders or has_cooperators:
            # Somewhat interesting with one extreme
            extreme_behavior_factor = 0.15
        
        # 3. Check efficiency (how close to optimal outcome)
        # In public goods, full contribution is most efficient
        efficiency = total_contribution / (endowment * len(contributions)) if endowment > 0 and contributions else 0
        efficiency_factor = 0
        
        if efficiency < 0.2:
            # Very inefficient outcomes are interesting
            efficiency_factor = 0.2
        elif efficiency > 0.8:
            # Very efficient outcomes are also interesting
            efficiency_factor = 0.15
        
        # Combine factors, but ensure we don't exceed 1.0
        additional_significance = heterogeneity_factor + extreme_behavior_factor + efficiency_factor
        remaining_room = 1.0 - base_significance
        final_significance = base_significance + (additional_significance * remaining_room)
        
        interaction.narrative_significance = min(1.0, final_significance)
        
        return interaction