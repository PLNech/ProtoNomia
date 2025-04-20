from datetime import datetime
from typing import Dict, List, Any, Optional
import random
import logging

from ...models.base import (
    Agent, EconomicInteraction, EconomicInteractionType, InteractionRole,
    InteractionOutcome, InteractionStrategy, ResourceBalance, ResourceType
)

logger = logging.getLogger(__name__)

# Base Interaction Handler
class InteractionHandler:
    """Base class for handling a specific economic interaction type"""
    
    interaction_type: EconomicInteractionType
    
    def create_interaction(self, **kwargs) -> EconomicInteraction:
        """Create a new interaction instance"""
        raise NotImplementedError("Subclasses must implement create_interaction")
    
    def progress_interaction(self, interaction: EconomicInteraction) -> EconomicInteraction:
        """Progress the interaction to its next state or complete it"""
        raise NotImplementedError("Subclasses must implement progress_interaction")
    
    def complete_interaction(self, interaction: EconomicInteraction) -> EconomicInteraction:
        """Complete the interaction and calculate outcomes"""
        raise NotImplementedError("Subclasses must implement complete_interaction")
    
    def get_resource_balance(self, agent: Agent, resource_type: ResourceType) -> float:
        """Helper to get an agent's balance of a specific resource"""
        for resource in agent.resources:
            if resource.resource_type == resource_type:
                return resource.amount
        return 0.0

# Ultimatum Game Implementation
class UltimatumGameHandler(InteractionHandler):
    """Handler for the Ultimatum Game interaction
    
    In the Ultimatum Game:
    1. The proposer offers a split of a resource
    2. The responder either accepts (both get their shares) or rejects (both get nothing)
    """
    
    interaction_type = EconomicInteractionType.ULTIMATUM
    
    def create_interaction(self, proposer: Agent, responder: Agent, 
                          amount: float, resource_type: ResourceType = ResourceType.CREDITS) -> EconomicInteraction:
        """Create a new ultimatum game interaction"""
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
        """Progress the ultimatum game to its next stage"""
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
        """Calculate the amount to propose based on agent personality"""
        # This would use the agent's personality and strategy in a full implementation
        # For MVP, use a random value weighted by fairness preference
        fairness = random.uniform(0.2, 0.5)  # Simulated fairness preference
        
        # More sophisticated calculation would consider past interactions, relationship, etc.
        proportion = max(0.01, min(0.99, random.normalvariate(fairness, 0.1)))
        return round(total_amount * proportion, 2)
    
    def _handle_response_stage(self, interaction: EconomicInteraction) -> EconomicInteraction:
        """Handle the response stage of the ultimatum game"""
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
        """Decide whether to accept the proposal"""
        # This would use the agent's personality and strategy in a full implementation
        # For MVP, use a simple fairness threshold
        proportion = proposed_amount / total_amount
        threshold = random.uniform(0.1, 0.3)  # Minimum acceptable proportion
        
        return proportion >= threshold
    
    def complete_interaction(self, interaction: EconomicInteraction) -> EconomicInteraction:
        """Complete the interaction and calculate outcomes"""
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


# Trust Game Implementation
class TrustGameHandler(InteractionHandler):
    """Handler for the Trust Game interaction
    
    In the Trust Game:
    1. The investor sends some amount to the trustee
    2. This amount is multiplied (typically by 3)
    3. The trustee decides how much to return to the investor
    """
    
    interaction_type = EconomicInteractionType.TRUST
    
    def create_interaction(self, investor: Agent, trustee: Agent, 
                         amount: float, multiplier: float = 3.0,
                         resource_type: ResourceType = ResourceType.CREDITS) -> EconomicInteraction:
        """Create a new trust game interaction"""
        # Check if investor has enough resources
        investor_balance = self.get_resource_balance(investor, resource_type)
        
        if investor_balance < amount:
            raise ValueError(f"Investor {investor.name} doesn't have enough {resource_type} ({investor_balance}) for this interaction ({amount})")
        
        # Create the interaction
        return EconomicInteraction(
            interaction_type=self.interaction_type,
            participants={
                investor.id: InteractionRole.INVESTOR,
                trustee.id: InteractionRole.TRUSTEE
            },
            parameters={
                "resource_type": resource_type,
                "initial_amount": amount,
                "multiplier": multiplier,
                "invested_amount": None,  # Will be set when investor makes investment
                "multiplied_amount": None,  # Will be calculated
                "returned_amount": None,  # Will be set when trustee returns
                "stage": "investment"  # Current stage: investment, return, completed
            },
            start_time=datetime.now(),
            is_complete=False
        )
    
    def progress_interaction(self, interaction: EconomicInteraction) -> EconomicInteraction:
        """Progress the trust game to its next stage"""
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
        
        # For MVP, simulate an investment based on simple personality-driven strategy
        initial_amount = interaction.parameters.get("initial_amount")
        invested_amount = self._calculate_investment_amount(investor_id, initial_amount)
        
        # Calculate multiplied amount
        multiplier = interaction.parameters.get("multiplier")
        multiplied_amount = invested_amount * multiplier
        
        # Update interaction parameters
        params = interaction.parameters.copy()
        params["invested_amount"] = invested_amount
        params["multiplied_amount"] = multiplied_amount
        params["stage"] = "return"
        
        interaction.parameters = params
        
        return interaction
    
    def _calculate_investment_amount(self, investor_id: str, initial_amount: float) -> float:
        """Calculate the amount to invest based on agent personality"""
        # This would use the agent's personality and strategy in a full implementation
        # For MVP, use a random value weighted by trust level
        trust = random.uniform(0.3, 0.8)  # Simulated trust level
        
        # More sophisticated calculation would consider past interactions, relationship, etc.
        proportion = max(0.0, min(1.0, random.normalvariate(trust, 0.15)))
        return round(initial_amount * proportion, 2)
    
    def _handle_return_stage(self, interaction: EconomicInteraction) -> EconomicInteraction:
        """Handle the return stage of the trust game"""
        # Find trustee
        trustee_id = next(id for id, role in interaction.participants.items() 
                         if role == InteractionRole.TRUSTEE)
        
        # For MVP, simulate a return based on simple fairness and reciprocity
        invested_amount = interaction.parameters.get("invested_amount")
        multiplied_amount = interaction.parameters.get("multiplied_amount")
        
        returned_amount = self._calculate_return_amount(trustee_id, invested_amount, multiplied_amount)
        
        # Update interaction parameters
        params = interaction.parameters.copy()
        params["returned_amount"] = returned_amount
        params["stage"] = "completed"
        
        interaction.parameters = params
        
        # Complete the interaction and calculate outcomes
        interaction = self.complete_interaction(interaction)
        
        return interaction
    
    def _calculate_return_amount(self, trustee_id: str, invested_amount: float, multiplied_amount: float) -> float:
        """Calculate the amount to return based on agent personality"""
        # This would use the agent's personality and strategy in a full implementation
        # For MVP, use a random value weighted by reciprocity level
        reciprocity = random.uniform(0.2, 0.7)  # Simulated reciprocity level
        
        # Attempt to return at least the original investment with some probability
        if random.random() < 0.7 and invested_amount > 0:
            min_return = invested_amount
        else:
            min_return = 0
            
        # Maximum return is the full multiplied amount
        max_return = multiplied_amount
        
        # Calculate return based on reciprocity
        target_return = min_return + (max_return - min_return) * reciprocity
        
        # Add some noise
        actual_return = target_return * random.uniform(0.9, 1.1)
        
        # Ensure return is within valid range
        return round(max(min_return, min(max_return, actual_return)), 2)
    
    def complete_interaction(self, interaction: EconomicInteraction) -> EconomicInteraction:
        """Complete the interaction and calculate outcomes"""
        # Extract relevant parameters
        initial_amount = interaction.parameters.get("initial_amount")
        invested_amount = interaction.parameters.get("invested_amount")
        multiplied_amount = interaction.parameters.get("multiplied_amount")
        returned_amount = interaction.parameters.get("returned_amount")
        resource_type = interaction.parameters.get("resource_type", ResourceType.CREDITS)
        
        # Find participant IDs
        investor_id = next(id for id, role in interaction.participants.items() 
                          if role == InteractionRole.INVESTOR)
        trustee_id = next(id for id, role in interaction.participants.items() 
                         if role == InteractionRole.TRUSTEE)
        
        # Calculate final balances
        investor_final = initial_amount - invested_amount + returned_amount
        trustee_final = multiplied_amount - returned_amount
        
        # Calculate utility changes
        investor_utility_change = investor_final - initial_amount
        trustee_utility_change = trustee_final
        
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
                    amount=investor_final
                )],
                utility_change=investor_utility_change,
                strategy_used=InteractionStrategy(
                    strategy_type="high_trust" if invested_amount >= initial_amount * 0.7 else 
                                 "medium_trust" if invested_amount >= initial_amount * 0.3 else 
                                 "low_trust",
                    parameters={"investment_ratio": invested_amount / initial_amount if initial_amount > 0 else 0}
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
                    amount=trustee_final
                )],
                utility_change=trustee_utility_change,
                strategy_used=InteractionStrategy(
                    strategy_type="trustworthy" if returned_amount >= invested_amount else "untrustworthy",
                    parameters={"return_ratio": returned_amount / multiplied_amount if multiplied_amount > 0 else 0}
                )
            )
        ]
        
        # Update the interaction
        interaction.outcomes = outcomes
        interaction.is_complete = True
        interaction.end_time = datetime.now()
        
        # Calculate narrative significance based on outcomes
        if invested_amount == 0:
            # No trust is interesting
            interaction.narrative_significance = 0.6
        elif returned_amount < invested_amount:
            # Betrayal is very interesting
            interaction.narrative_significance = 0.8
        elif returned_amount >= invested_amount * 2:
            # High reciprocity is interesting
            interaction.narrative_significance = 0.7
        else:
            # Normal outcomes less interesting
            interaction.narrative_significance = 0.4
        
        return interaction

# Public Goods Game Implementation
class PublicGoodsGameHandler(InteractionHandler):
    """Handler for the Public Goods Game interaction
    
    In the Public Goods Game:
    1. Each participant receives an endowment
    2. They decide how much to contribute to a common pool
    3. The pool is multiplied by some factor
    4. The resulting amount is distributed equally among all participants
    """
    
    interaction_type = EconomicInteractionType.PUBLIC_GOODS
    
    def create_interaction(self, participants: List[Agent], 
                         endowment: float, multiplier: float = 1.6,
                         resource_type: ResourceType = ResourceType.CREDITS) -> EconomicInteraction:
        """Create a new public goods game interaction"""
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
        """Progress the public goods game to its next stage"""
        if interaction.is_complete:
            return interaction
        
        stage = interaction.parameters.get("stage")
        
        if stage == "contribution":
            interaction = self._handle_contribution_stage(interaction)
        
        return interaction
    
    def _handle_contribution_stage(self, interaction: EconomicInteraction) -> EconomicInteraction:
        """Handle the contribution stage"""
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
        """Calculate how much an agent contributes based on personality"""
        # This would use the agent's personality and strategy in a full implementation
        # For MVP, use a random value weighted by cooperativeness
        cooperativeness = random.uniform(0.2, 0.8)  # Simulated cooperativeness level
        
        # More sophisticated calculation would consider past interactions, group composition, etc.
        proportion = max(0.0, min(1.0, random.normalvariate(cooperativeness, 0.2)))
        return round(endowment * proportion, 2)
    
    def complete_interaction(self, interaction: EconomicInteraction) -> EconomicInteraction:
        """Complete the interaction and calculate outcomes"""
        # Extract relevant parameters
        endowment = interaction.parameters.get("endowment")
        multiplier = interaction.parameters.get("multiplier")
        contributions = interaction.parameters.get("contributions", {})
        resource_type = interaction.parameters.get("resource_type", ResourceType.CREDITS)
        
        # Calculate the total contribution and return
        total_contribution = sum(contributions.values())
        total_return = total_contribution * multiplier
        per_agent_return = total_return / len(interaction.participants) if interaction.participants else 0
        
        # Create outcome objects
        outcomes = []
        for agent_id, role in interaction.participants.items():
            contribution = contributions.get(agent_id, 0)
            final_balance = endowment - contribution + per_agent_return
            utility_change = final_balance - endowment
            
            # Determine strategy type
            if contribution <= endowment * 0.2:
                strategy_type = "free_rider"
            elif contribution >= endowment * 0.8:
                strategy_type = "cooperator"
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
                        parameters={"contribution_ratio": contribution / endowment if endowment > 0 else 0}
                    )
                )
            )
        
        # Update the interaction
        interaction.outcomes = outcomes
        interaction.is_complete = True
        interaction.end_time = datetime.now()
        
        # Calculate narrative significance based on outcome
        # High variance in contributions is interesting
        contribution_values = list(contributions.values())
        if contribution_values:
            std_dev = (sum((x - (sum(contribution_values) / len(contribution_values)))**2 for x in contribution_values) / len(contribution_values))**0.5
            normalized_std_dev = std_dev / endowment if endowment > 0 else 0
            
            # High standard deviation means interesting heterogeneity
            interaction.narrative_significance = min(0.9, normalized_std_dev * 2)
            
            # If everyone contributes almost nothing or almost everything, that's also interesting
            avg_contribution_ratio = sum(contribution_values) / (len(contribution_values) * endowment) if endowment > 0 else 0
            if avg_contribution_ratio < 0.1 or avg_contribution_ratio > 0.9:
                interaction.narrative_significance = max(interaction.narrative_significance, 0.7)
        else:
            interaction.narrative_significance = 0.1
        
        return interaction


# Registry to manage all interaction handlers
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
        """Progress an existing interaction"""
        if interaction.interaction_type not in self.handlers:
            raise ValueError(f"No handler registered for interaction type {interaction.interaction_type}")
        
        return self.handlers[interaction.interaction_type].progress_interaction(interaction)