from datetime import datetime
import random
import logging
from typing import Dict, List, Any, Optional
import math

from models.base import (
    Agent, EconomicInteraction, EconomicInteractionType, InteractionRole,
    InteractionOutcome, InteractionStrategy, ResourceBalance, ResourceType
)
from economics.interactions.base import InteractionHandler

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
    
    def create_interaction(
        self, 
        participants: List[Agent],
        endowment: float = 100.0,
        multiplier: float = 2.0,
        resource_type: ResourceType = ResourceType.CREDITS,
        **kwargs
    ) -> EconomicInteraction:
        """Create a public goods game interaction
        
        Args:
            participants: List of participating agents
            endowment: The initial amount each participant receives
            multiplier: The factor by which the pool is multiplied
            resource_type: The type of resource being used
            
        Returns:
            A new economic interaction
        """
        logger.info(f"Creating Public Goods Game with {len(participants)} participants, endowment={endowment}, multiplier={multiplier}")
        
        # Create participant dictionary
        participant_dict = {}
        for agent in participants:
            participant_dict[agent] = InteractionRole.CONTRIBUTOR
        
        # Create the interaction
        interaction = EconomicInteraction(
            interaction_type=EconomicInteractionType.PUBLIC_GOODS,
            participants=participant_dict,
            parameters={
                "endowment": endowment,
                "multiplier": multiplier,
                "resource_type": resource_type,
                "contributions": {},  # Will be filled in during progression
                "stage": "contribution"  # Stages: contribution, completed
            },
            start_time=datetime.now(),
            is_complete=False
        )
        
        return interaction

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
        for agent in interaction.participants.keys():
            # Simulate contribution decision based on personality
            contribution = self._calculate_contribution(agent, endowment)
            contributions[agent] = contribution

        params["contributions"] = contributions
        params["stage"] = "completed"

        interaction.parameters = params

        # Complete the interaction and calculate outcomes
        interaction = self.complete_interaction(interaction)

        return interaction
    
    def _calculate_contribution(self, agent: Agent, endowment: float) -> float:
        """Calculate how much an agent contributes
        
        In a full implementation, this would use agent personality and past behavior
        For MVP, we use a simple random distribution
        
        Args:
            agent: The agent making the contribution
            endowment: The amount available to contribute
            
        Returns:
            The contribution amount
        """
        # Generate a contribution with bias toward extremes (all or nothing)
        # or toward fairness (50%)
        mode = random.choice(["fair", "extreme"])
        
        if mode == "fair":
            # Contribute around 40-60% of endowment
            mean = 0.5
            std_dev = 0.1
        else:
            # Bimodal - either low or high contribution
            if random.random() < 0.5:
                # Free-rider tendency
                mean = 0.1
                std_dev = 0.1
            else:
                # Cooperator tendency
                mean = 0.9
                std_dev = 0.1
        
        # Generate and clamp contribution
        proportion = random.normalvariate(mean, std_dev)
        proportion = max(0.0, min(1.0, proportion))
        
        return round(proportion * endowment, 2)

    def complete_interaction(self, interaction: EconomicInteraction) -> EconomicInteraction:
        """Complete the interaction and calculate outcomes
        
        This updates agents' resources and records outcomes.
        
        Args:
            interaction: The interaction to complete
            
        Returns:
            The completed interaction
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
        
        # Process outcomes for each agent
        outcomes = []
        for agent, role in interaction.participants.items():
            # Record initial resources
            resources_before = self.get_resource_state(agent)
            
            # Calculate this agent's contribution and return
            contribution = contributions.get(agent, 0)
            
            # Apply resource changes
            self.update_agent_resource(agent, resource_type, -contribution)  # Take contribution
            self.update_agent_resource(agent, resource_type, per_agent_return)  # Give share of return
            
            # Record final resources
            resources_after = self.get_resource_state(agent)
            
            # Calculate utility change
            utility_change = per_agent_return - contribution
            
            # Determine strategy type
            if contribution <= endowment * 0.2:
                strategy_type = "free_rider"
            elif contribution >= endowment * 0.8:
                strategy_type = "cooperator"
            else:
                strategy_type = "moderate_contributor"
            
            # Create outcome
            outcomes.append(
                InteractionOutcome(
                    interaction_id=interaction.id,
                    agent=agent,
                    role=role,
                    resources_before=resources_before,
                    resources_after=resources_after,
                    utility_change=utility_change,
                    strategy_used=InteractionStrategy(
                        strategy_type=strategy_type,
                        parameters={"contribution_ratio": contribution / endowment if endowment > 0 else 0}
                    )
                )
            )
        
        # Update the interaction
        interaction.outcomes = outcomes
        interaction.is_complete = True
        interaction.end_time = datetime.now()
        
        # Calculate narrative significance
        interaction.narrative_significance = self._calculate_narrative_significance(contributions, endowment)
        
        return interaction
    
    def _calculate_narrative_significance(self, contributions, endowment):
        """Calculate narrative significance for this public goods game
        
        Args:
            contributions: The contributions made by each participant
            endowment: The initial amount each participant receives
            
        Returns:
            A narrative significance score (0.0-1.0)
        """
        # Base significance for public goods games
        base_significance = 0.5
        
        # Factors that make the interaction more interesting
        contribution_ratios = [
            contrib / endowment for contrib in contributions.values()
        ] if endowment > 0 else []
        
        if not contribution_ratios:
            return base_significance
        
        # Calculate heterogeneity of contributions - more varied is more interesting
        if len(contribution_ratios) > 1:
            mean_contribution = sum(contribution_ratios) / len(contribution_ratios)
            variance = sum((r - mean_contribution) ** 2 for r in contribution_ratios) / len(contribution_ratios)
            heterogeneity = min(0.5, math.sqrt(variance) * 2)  # Scale up, cap at 0.5
        else:
            heterogeneity = 0
        
        heterogeneity_factor = heterogeneity
        
        # Extreme behavior (all free riders or all cooperators) is interesting
        extreme_behavior = False
        free_riders = sum(1 for r in contribution_ratios if r < 0.2)
        cooperators = sum(1 for r in contribution_ratios if r > 0.8)
        
        if free_riders == len(contribution_ratios) or cooperators == len(contribution_ratios):
            extreme_behavior = True
            
        extreme_behavior_factor = 0.2 if extreme_behavior else 0.0
        
        # Efficiency (how close to optimal outcome)
        efficiency = sum(contribution_ratios) / len(contribution_ratios)
        
        efficiency_factor = 0.0
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

        return min(1.0, final_significance)
