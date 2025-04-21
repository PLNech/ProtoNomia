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
        """Complete the interaction and calculate outcomes
        
        Implementation MUST update the agent resources directly based on the
        calculated outcomes. Don't just calculate the outcomes - apply them!
        """
        raise NotImplementedError("Subclasses must implement complete_interaction")
    
    def get_resource_balance(self, agent: Agent, resource_type: ResourceType) -> float:
        """Helper to get an agent's balance of a specific resource"""
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
        """Calculate the narrative significance of an interaction
        
        Override this in subclasses to provide interaction-specific significance calculation
        """
        return 0.5  # Default medium significance

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
                proposer: InteractionRole.PROPOSER,
                responder: InteractionRole.RESPONDER
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
        proposer = next(agent for agent, role in interaction.participants.items() 
                      if role == InteractionRole.PROPOSER)
        
        # Calculate proposal amount based on proposer's personality
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
        # Use the agent's fairness preference from personality
        fairness = proposer.personality.fairness_preference
        
        # More sophisticated calculation would consider past interactions, relationship, etc.
        # Add some randomness to the decision
        proportion = max(0.01, min(0.99, random.normalvariate(fairness, 0.1)))
        return round(total_amount * proportion, 2)
    
    def _handle_response_stage(self, interaction: EconomicInteraction) -> EconomicInteraction:
        """Handle the response stage of the ultimatum game"""
        # Find responder
        responder = next(agent for agent, role in interaction.participants.items() 
                       if role == InteractionRole.RESPONDER)
        
        # For MVP, simulate a response based on responder's personality
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
        # Use agent's fairness preference as the threshold, with some randomness
        threshold = max(0.05, min(0.5, random.normalvariate(0.3 - 0.2 * responder.personality.fairness_preference, 0.1)))
        proportion = proposed_amount / total_amount
        
        return proportion >= threshold
    
    def complete_interaction(self, interaction: EconomicInteraction) -> EconomicInteraction:
        """Complete the interaction and calculate outcomes"""
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
        
        # Calculate outcomes based on acceptance
        if acceptance:
            # Offer accepted: proposer gets (total - proposed), responder gets proposed
            proposer_gain = total_amount - proposed_amount
            responder_gain = proposed_amount
            
            # Remove total amount from proposer
            self.update_agent_resource(proposer, resource_type, -total_amount)
            
            # Add respective shares
            self.update_agent_resource(proposer, resource_type, proposer_gain)
            self.update_agent_resource(responder, resource_type, responder_gain)
        else:
            # Offer rejected: both get nothing
            proposer_gain = 0
            responder_gain = 0
        
        # Record the final resource state for each agent
        proposer_resources_after = self.get_resource_state(proposer)
        responder_resources_after = self.get_resource_state(responder)
        
        # Create outcome objects
        outcomes = [
            InteractionOutcome(
                interaction_id=interaction.id,
                agent=proposer,
                role=InteractionRole.PROPOSER,
                resources_before=[ResourceBalance(
                    resource_type=resource_type,
                    amount=total_amount
                )],
                resources_after=proposer_resources_after,
                utility_change=proposer_gain - total_amount,
                strategy_used=InteractionStrategy(
                    strategy_type="fair_split" if proposed_amount / total_amount >= 0.4 else "selfish",
                    parameters={"offered_proportion": proposed_amount / total_amount}
                )
            ),
            InteractionOutcome(
                interaction_id=interaction.id,
                agent=responder,
                role=InteractionRole.RESPONDER,
                resources_before=[ResourceBalance(
                    resource_type=resource_type,
                    amount=0
                )],
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
                investor: InteractionRole.INVESTOR,
                trustee: InteractionRole.TRUSTEE
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
        investor = next(agent for agent, role in interaction.participants.items() 
                      if role == InteractionRole.INVESTOR)
        
        # Calculate investment based on investor's personality
        initial_amount = interaction.parameters.get("initial_amount")
        invested_amount = self._calculate_investment_amount(investor, initial_amount)
        
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
    
    def _calculate_investment_amount(self, investor: Agent, initial_amount: float) -> float:
        """Calculate the amount to invest based on agent personality"""
        # Use the agent's risk tolerance and trust (approximate with cooperativeness)
        trust = (investor.personality.risk_tolerance + investor.personality.cooperativeness) / 2
        
        # More sophisticated calculation would consider past interactions, relationship, etc.
        proportion = max(0.0, min(1.0, random.normalvariate(trust, 0.15)))
        return round(initial_amount * proportion, 2)
    
    def _handle_return_stage(self, interaction: EconomicInteraction) -> EconomicInteraction:
        """Handle the return stage of the trust game"""
        # Find trustee
        trustee = next(agent for agent, role in interaction.participants.items() 
                     if role == InteractionRole.TRUSTEE)
        
        # Calculate return based on trustee's personality
        invested_amount = interaction.parameters.get("invested_amount")
        multiplied_amount = interaction.parameters.get("multiplied_amount")
        
        returned_amount = self._calculate_return_amount(trustee, invested_amount, multiplied_amount)
        
        # Update interaction parameters
        params = interaction.parameters.copy()
        params["returned_amount"] = returned_amount
        params["stage"] = "completed"
        
        interaction.parameters = params
        
        # Complete the interaction and calculate outcomes
        interaction = self.complete_interaction(interaction)
        
        return interaction
    
    def _calculate_return_amount(self, trustee: Agent, invested_amount: float, multiplied_amount: float) -> float:
        """Calculate the amount to return based on agent personality"""
        # Use the agent's fairness preference and altruism
        reciprocity = (trustee.personality.fairness_preference + trustee.personality.altruism) / 2
        
        # Attempt to return at least the original investment with some probability
        if random.random() < reciprocity and invested_amount > 0:
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
        
        # Find participants
        investor = next(agent for agent, role in interaction.participants.items() 
                      if role == InteractionRole.INVESTOR)
        trustee = next(agent for agent, role in interaction.participants.items() 
                     if role == InteractionRole.TRUSTEE)
        
        # Calculate final balances
        investor_final = initial_amount - invested_amount + returned_amount
        trustee_final = multiplied_amount - returned_amount
        
        # Calculate utility changes
        investor_utility_change = investor_final - initial_amount
        trustee_utility_change = trustee_final
        
        # Perform the resource transfers
        # Remove invested amount from investor
        self.update_agent_resource(investor, resource_type, -invested_amount)
        
        # Add multiplied amount to trustee
        self.update_agent_resource(trustee, resource_type, multiplied_amount)
        
        # Remove returned amount from trustee
        self.update_agent_resource(trustee, resource_type, -returned_amount)
        
        # Add returned amount to investor
        self.update_agent_resource(investor, resource_type, returned_amount)
        
        # Get final resource states
        investor_resources_after = self.get_resource_state(investor)
        trustee_resources_after = self.get_resource_state(trustee)
        
        # Create outcome objects
        outcomes = [
            InteractionOutcome(
                interaction_id=interaction.id,
                agent=investor,
                role=InteractionRole.INVESTOR,
                resources_before=[ResourceBalance(
                    resource_type=resource_type,
                    amount=initial_amount
                )],
                resources_after=investor_resources_after,
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
                agent=trustee,
                role=InteractionRole.TRUSTEE,
                resources_before=[ResourceBalance(
                    resource_type=resource_type,
                    amount=0
                )],
                resources_after=trustee_resources_after,
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
            agent: InteractionRole.CONTRIBUTOR for agent in participants
        }
        
        return EconomicInteraction(
            interaction_type=self.interaction_type,
            participants=participant_dict,
            parameters={
                "resource_type": resource_type,
                "endowment": endowment,
                "multiplier": multiplier,
                "contributions": {},  # Will be filled with agent -> contribution
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
        for agent in interaction.participants.keys():
            # Calculate contribution based on agent's personality
            contribution = self._calculate_contribution(agent, endowment)
            contributions[agent] = contribution
        
        params["contributions"] = contributions
        params["stage"] = "completed"
        
        interaction.parameters = params
        
        # Complete the interaction and calculate outcomes
        interaction = self.complete_interaction(interaction)
        
        return interaction
    
    def _calculate_contribution(self, agent: Agent, endowment: float) -> float:
        """Calculate how much an agent contributes based on personality"""
        # Use the agent's cooperativeness and fairness preference
        cooperativeness = agent.personality.cooperativeness
        fairness = agent.personality.fairness_preference
        contribution_tendency = (cooperativeness + fairness) / 2
        
        # More sophisticated calculation would consider past interactions, group composition, etc.
        proportion = max(0.0, min(1.0, random.normalvariate(contribution_tendency, 0.2)))
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
        for agent, role in interaction.participants.items():
            contribution = contributions.get(agent, 0)
            final_balance = endowment - contribution + per_agent_return
            utility_change = final_balance - endowment
            
            # Apply the resource changes
            # Take the endowment and contribution
            self.update_agent_resource(agent, resource_type, -contribution)
            
            # Give back the per-agent return
            self.update_agent_resource(agent, resource_type, per_agent_return)
            
            # Get final resources
            resources_after = self.get_resource_state(agent)
            
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
                    agent=agent,
                    role=role,
                    resources_before=[ResourceBalance(
                        resource_type=resource_type,
                        amount=endowment
                    )],
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
        """Progress an existing interaction
        
        This updates the interaction state but does not directly modify agents' resources.
        The handler's complete_interaction method is responsible for updating agent resources.
        """
        if interaction.interaction_type not in self.handlers:
            raise ValueError(f"No handler registered for interaction type {interaction.interaction_type}")
        
        return self.handlers[interaction.interaction_type].progress_interaction(interaction)
    
    def process_interaction(self, interaction: EconomicInteraction) -> EconomicInteraction:
        """Process an interaction, advancing its state and applying resource changes
        
        Args:
            interaction: The interaction to process
            
        Returns:
            The updated interaction after processing
        """
        if interaction.is_complete:
            logger.debug(f"Interaction {interaction.id} is already complete")
            return interaction
        
        # Get the appropriate handler
        if interaction.interaction_type not in self.handlers:
            raise ValueError(f"No handler registered for interaction type {interaction.interaction_type}")
        
        handler = self.handlers[interaction.interaction_type]
        
        # Progress the interaction
        updated_interaction = handler.progress_interaction(interaction)
        
        # If the interaction is complete, the handler has already updated agent resources
        if updated_interaction.is_complete:
            logger.info(f"Interaction {interaction.id} completed with outcomes: {len(updated_interaction.outcomes)}")
            
            # Log narrative significance
            if updated_interaction.narrative_significance > 0.7:
                logger.info(f"Highly significant interaction: {updated_interaction.narrative_significance:.2f}")
            elif updated_interaction.narrative_significance > 0.4:
                logger.debug(f"Moderately significant interaction: {updated_interaction.narrative_significance:.2f}")
        
        return updated_interaction
    
    def find_agent_by_id(self, agent_id: str, agents: List[Agent]) -> Optional[Agent]:
        """Find an agent by its ID
        
        This helper method is useful for migrating from the old ID-based model
        to the new agent-reference model.
        
        Args:
            agent_id: The ID of the agent to find
            agents: List of agents to search in
            
        Returns:
            The agent with the given ID, or None if not found
        """
        for agent in agents:
            if agent.id == agent_id:
                return agent
        return None
    
    def migrate_interaction_to_agent_refs(self, interaction: EconomicInteraction, agents: List[Agent]) -> EconomicInteraction:
        """Migrate an interaction from using agent IDs to using agent references
        
        This is a migration helper for converting old interaction format to new format.
        
        Args:
            interaction: The interaction to migrate
            agents: List of all available agents
            
        Returns:
            The migrated interaction with direct agent references
        """
        # If the interaction already uses agent references, no need to migrate
        if not interaction.participants or all(isinstance(key, Agent) for key in interaction.participants.keys()):
            return interaction
        
        # Migrate participants
        new_participants = {}
        for agent_id, role in interaction.participants.items():
            agent = self.find_agent_by_id(agent_id, agents)
            if agent:
                new_participants[agent] = role
            else:
                logger.warning(f"Could not find agent with ID {agent_id} during migration")
        
        interaction.participants = new_participants
        
        # Migrate outcomes
        for outcome in interaction.outcomes:
            if hasattr(outcome, 'agent_id'):
                # Find the agent
                agent = self.find_agent_by_id(outcome.agent_id, agents)
                if agent:
                    outcome.agent = agent
                    # Delete the old agent_id attribute
                    delattr(outcome, 'agent_id')
                else:
                    logger.warning(f"Could not find agent with ID {outcome.agent_id} during outcome migration")
        
        return interaction