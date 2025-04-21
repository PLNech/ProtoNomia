"""
LLM-based Narrator module for ProtoNomia.
This module uses Ollama to generate narrative events from economic interactions.
"""
import logging
from typing import List, Dict, Any, Tuple
from datetime import datetime

from models.base import (
    Agent, EconomicInteraction, EconomicInteractionType, InteractionRole,
    NarrativeEvent, InteractionOutcome, ResourceType
)
from narrative.narrator import Narrator
from llm_utils import OllamaClient
from settings import DEFAULT_LM

# Initialize logger
logger = logging.getLogger(__name__)


class LLMNarrator(Narrator):
    """
    LLM-powered Narrator that uses Ollama to generate narrative events and
    arcs from economic interactions.
    """

    def __init__(
            self,
            verbosity: int = 3,
            model_name: str = DEFAULT_LM,
            ollama_base_url: str = "http://localhost:11434",
            temperature: float = 0.8,
            top_p: float = 0.95,
            top_k: int = 40,
            timeout: int = 30,
            max_retries: int = 5
    ):
        """
        Initialize the LLM Narrator.
        """
        super().__init__(verbosity)
        self.model_name = model_name
        self.ollama_base_url = ollama_base_url
        self.temperature = temperature
        self.top_p = top_p
        self.top_k = top_k
        self.timeout = timeout
        self.max_retries = max_retries
        self.market_report: Dict[str, Any] = {}  # Store the latest market report

        logger.info(f"Initializing LLM Narrator with model {model_name}")

        # Create the OllamaClient for structured output generation
        self.ollama_client = OllamaClient(
            base_url=ollama_base_url,
            model_name=model_name,
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
            max_tokens=2**14,
            max_retries=max_retries,
            timeout=timeout
        )
        logger.info(f"Successfully connected to Ollama with model {model_name}")

    def generate_event_from_interaction(
            self,
            interaction: EconomicInteraction,
            agents: List[Agent]
    ) -> NarrativeEvent:
        """
        Generate a narrative event from an economic interaction using LLM.
        """
        try:
            # Map agent IDs to agent objects for easier lookup
            agent_map = {agent.id: agent for agent in agents}
            agent_names = {agent.id: agent.name for agent in agents}

            # Get participant agent names
            participant_names = {}
            for agent_id, role in interaction.participants.items():
                if agent_id in agent_map:
                    participant_names[role] = agent_names[agent_id]

            # Create a prompt for the LLM
            prompt = self._create_interaction_prompt(interaction, participant_names, agent_map)

            system_prompt = (
                "You are a creative narrator for a Mars colony simulation in the year 2993. "
                "Your role is to transform economic data into memorable character-driven stories that reveal personalities, "
                "motivations, and the unique challenges of Martian life. Focus on making each interaction feel consequential "
                "and emotionally resonant, while maintaining scientific plausibility and thematic consistency."
            )

            # Generate the narrative using structured output
            narrative_response = self.ollama_client.generate_narrative(
                prompt=prompt,
                system_prompt=system_prompt
            )

            # Create and return the narrative event
            event = NarrativeEvent(
                timestamp=datetime.now(),
                title=narrative_response.title,
                description=narrative_response.description,
                agents_involved=[agent_map[agent_id] for agent_id in interaction.participants.keys()],
                interaction_id=interaction.id,
                significance=interaction.narrative_significance,
                tags=narrative_response.tags
            )

            logger.debug(f"Generated narrative event: {narrative_response.title}")
            return event

        except Exception as e:
            logger.error(f"Error generating narrative event: {e}")
            # Fallback to a simple event in case of error
            return NarrativeEvent(
                timestamp=datetime.now(),
                title="Economic Interaction",
                description="An economic interaction occurred between agents.",
                agents_involved=[agent_map[agent_id] for agent_id in interaction.participants.keys()],
                interaction_id=interaction.id,
                significance=interaction.narrative_significance,
                tags=["fallback", "error_recovery"]
            )

    def generate_daily_summary(self, day: int, events: List[NarrativeEvent], agents: List[Agent]) -> str:
        """
        Generate a daily summary of events for the simulation.
        """
        try:
            # Create a prompt for the daily summary
            prompt = self._create_daily_summary_prompt(day, events, agents)

            system_prompt = (
                "You are a creative historian chronicling the emerging society on Mars in the year 2993. "
                "Your daily summaries should not just list events, but trace how individual actions and economic decisions "
                "are collectively shaping Mars' future. Identify patterns, tensions, and developments that would not be obvious "
                "from isolated events. Balance factual reporting with evocative prose that captures the challenges and triumphs "
                "of this frontier society."
            )

            # Generate the daily summary using structured output
            summary_response = self.ollama_client.generate_daily_summary(
                prompt=prompt,
                system_prompt=system_prompt
            )

            # Format the final summary with the headline as the main title
            formatted_summary = (f"# {summary_response.headline}\n\n{summary_response.summary}\n\n"
                                 f"Emerging Trends:{summary_response.emerging_trends or None}")

            return formatted_summary

        except Exception as e:
            logger.error(f"Error generating daily summary: {e}")
            raise

    def update_market_report(self, market_report: Dict[str, Any]) -> None:
        """
        Update the stored market report data.
        
        Args:
            market_report: The latest market report from the economy manager
        """
        self.market_report = market_report

    def _extract_economic_outcomes(self, interaction: EconomicInteraction) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Extract economic outcomes from an interaction for narrative purposes.
        
        Args:
            interaction: The economic interaction
            
        Returns:
            A tuple of (resources_exchanged, strategies_used)
        """
        resources_exchanged = {}
        strategies_used = {}
        
        # Process the outcomes if they exist
        if interaction.outcomes:
            for outcome in interaction.outcomes:
                # Extract resource changes
                resource_change = 0.0
                resource_type = None
                
                # Calculate the net change in resources
                if outcome.resources_before and outcome.resources_after:
                    for before in outcome.resources_before:
                        for after in outcome.resources_after:
                            if before.resource_type == after.resource_type:
                                change = after.amount - before.amount
                                if abs(change) > abs(resource_change):
                                    resource_change = change
                                    resource_type = before.resource_type.value
                
                if resource_type:
                    # Format: agent_role -> {resource_type: change}
                    role_name = outcome.role.value
                    resources_exchanged[role_name] = {
                        "resource_type": resource_type,
                        "change": resource_change,
                        "utility_change": outcome.utility_change
                    }
                
                # Extract strategy information
                if outcome.strategy_used:
                    role_name = outcome.role.value
                    strategies_used[role_name] = {
                        "type": outcome.strategy_used.strategy_type,
                        "parameters": outcome.strategy_used.parameters
                    }
        
        return resources_exchanged, strategies_used

    def _create_interaction_prompt(
            self,
            interaction: EconomicInteraction,
            participant_names: Dict[InteractionRole, str],
            agent_map: Dict[str, Agent]
    ) -> str:
        """Create a prompt for the interaction narrative generation"""
        # Get interaction type and parameters
        interaction_type = interaction.interaction_type.value
        parameters = interaction.parameters
        
        # Extract economic outcomes for narrative hooks
        resources_exchanged, strategies_used = self._extract_economic_outcomes(interaction)

        # Get participant names and IDs
        participant_ids = {}
        for agent_id, role in interaction.participants.items():
            role_name = role.value
            participant_ids[role_name] = agent_id

        # Create the prompt based on the interaction type
        prompt = (
            f"As the narrator for the Mars colony in the year 2993, describe a meaningful economic interaction "
            f"that reveals character traits and advances relationships through authentic dialogue and vivid details.\n\n"
            f"Interaction Type: {interaction_type}\n"
            f"Participants: "
        )
        
        # Add participants with their roles
        participants_list = []
        for role, name in participant_names.items():
            participants_list.append(f"{name} ({role.value})")
        
        prompt += ", ".join(participants_list) + "\n\n"
        
        # Add specific details based on interaction type
        if interaction.interaction_type == EconomicInteractionType.ULTIMATUM:
            # Get values from parameters or outcomes (if available)
            total_amount = parameters.get('total_amount', 100)
            proposed_amount = parameters.get('proposed_amount')
            acceptance = parameters.get('response')
            resource_type = parameters.get('resource_type', ResourceType.CREDITS).value
            
            proposer_name = participant_names.get(InteractionRole.PROPOSER, "Proposer")
            responder_name = participant_names.get(InteractionRole.RESPONDER, "Responder")
            
            # Add economic outcomes if available
            proposer_outcome = resources_exchanged.get('proposer', {})
            responder_outcome = resources_exchanged.get('responder', {})
            
            proposer_strategy = strategies_used.get('proposer', {}).get('type', 'unknown')
            responder_strategy = strategies_used.get('responder', {}).get('type', 'unknown')
            
            prompt += (
                f"Core Event: {proposer_name} offered {responder_name} {proposed_amount} {resource_type} "
                f"out of a total of {total_amount} {resource_type}. "
                f"The offer was {'accepted' if acceptance else 'rejected'} by {responder_name}.\n\n"
            )
            
            # Add economic outcomes
            if proposer_outcome and responder_outcome:
                prompt += (
                    f"Economic Outcome: {proposer_name} {'gained' if proposer_outcome.get('utility_change', 0) > 0 else 'lost'} "
                    f"{abs(proposer_outcome.get('utility_change', 0))} utility "
                    f"while {responder_name} {'gained' if responder_outcome.get('utility_change', 0) > 0 else 'lost'} "
                    f"{abs(responder_outcome.get('utility_change', 0))} utility.\n\n"
                )
                
                prompt += (
                    f"Strategies: {proposer_name} employed a '{proposer_strategy}' approach, "
                    f"while {responder_name} responded with a '{responder_strategy}' strategy.\n\n"
                )
            
            prompt += (
                f"Consider what this reveals about power dynamics, negotiation styles, and the personal history between them. "
                f"What motivated this particular offer? What consequences might this have for their future interactions?\n"
            )
        elif interaction.interaction_type == EconomicInteractionType.TRUST:
            # Get values from parameters or outcomes
            initial_amount = parameters.get('initial_amount', 100)
            invested_amount = parameters.get('invested_amount', 0)
            multiplier = parameters.get('multiplier', 3)
            returned_amount = parameters.get('returned_amount', 0)
            resource_type = parameters.get('resource_type', ResourceType.CREDITS).value
            
            investor_name = participant_names.get(InteractionRole.INVESTOR, "Investor")
            trustee_name = participant_names.get(InteractionRole.TRUSTEE, "Trustee")
            
            multiplied_amount = invested_amount * multiplier if invested_amount is not None else 0
            
            # Add economic outcomes if available
            investor_outcome = resources_exchanged.get('investor', {})
            trustee_outcome = resources_exchanged.get('trustee', {})
            
            investor_strategy = strategies_used.get('investor', {}).get('type', 'unknown')
            trustee_strategy = strategies_used.get('trustee', {}).get('type', 'unknown')
            
            prompt += (
                f"Core Event: {investor_name} invested {invested_amount} {resource_type} with {trustee_name}. "
                f"The investment grew by a factor of {multiplier} to {multiplied_amount} {resource_type}. "
                f"{trustee_name} returned {returned_amount} {resource_type} to {investor_name}.\n\n"
            )
            
            # Add economic outcomes
            if investor_outcome and trustee_outcome:
                prompt += (
                    f"Economic Outcome: {investor_name} {'gained' if investor_outcome.get('utility_change', 0) > 0 else 'lost'} "
                    f"{abs(investor_outcome.get('utility_change', 0))} utility "
                    f"while {trustee_name} {'gained' if trustee_outcome.get('utility_change', 0) > 0 else 'lost'} "
                    f"{abs(trustee_outcome.get('utility_change', 0))} utility.\n\n"
                )
                
                prompt += (
                    f"Strategies: {investor_name} exhibited a '{investor_strategy}' approach to investing, "
                    f"while {trustee_name} demonstrated a '{trustee_strategy}' approach to trustworthiness.\n\n"
                )
            
            prompt += (
                f"Consider the emotional stakes, prior experiences that built or eroded trust, and how this "
                f"exchange affects the community's perception of both parties. Is this part of a pattern or an unusual event?\n"
            )
        elif interaction.interaction_type == EconomicInteractionType.PUBLIC_GOODS:
            # Get values from parameters or outcomes
            endowment = parameters.get('endowment', 100)
            multiplier = parameters.get('multiplier', 2.0)
            contributions = parameters.get('contributions', {})
            resource_type = parameters.get('resource_type', ResourceType.CREDITS).value
            
            # Format the contributions for the prompt
            contribution_text = []
            for agent_id, amount in contributions.items():
                if agent_id in agent_map:
                    contribution_text.append(f"{agent_map[agent_id].name}: {amount} {resource_type}")
            
            contributions_str = ", ".join(contribution_text) if contribution_text else "No contributions"
            
            total_contribution = sum(contributions.values()) if contributions else 0
            multiplied_pool = total_contribution * multiplier
            num_participants = len(interaction.participants)
            individual_return = multiplied_pool / num_participants if num_participants > 0 else 0
            
            prompt += (
                f"Core Event: A public goods game where each participant received an endowment of {endowment} {resource_type}.\n"
                f"Contributions: {contributions_str}\n"
                f"The combined pool of {total_contribution} {resource_type} was multiplied by {multiplier} to {multiplied_pool} {resource_type}.\n"
                f"Each participant received {individual_return} {resource_type} from the common pool.\n\n"
            )
            
            # Add strategies for each participant
            strategies_text = []
            for agent_id, role in interaction.participants.items():
                role_name = role.value
                if role_name in strategies_used and agent_id in agent_map:
                    strategy = strategies_used[role_name].get('type', 'unknown')
                    strategies_text.append(f"{agent_map[agent_id].name}: {strategy}")
            
            if strategies_text:
                prompt += f"Strategies: {', '.join(strategies_text)}\n\n"
            
            prompt += (
                f"Consider how this reveals group dynamics, cooperation vs. self-interest, and the emerging social norms "
                f"in the Mars colony. How does the shared environment of Mars influence collective decision-making?\n"
            )
        else:
            # Generic prompt for other interaction types
            prompt += (
                f"Core Event: An economic exchange with these details: "
                f"{', '.join([f'{k}: {v}' for k, v in parameters.items()])}\n\n"
                f"Consider the broader context - is this transaction routine or unusual? "
                f"What environmental or sociopolitical factors on Mars influenced this exchange?\n"
            )

        # Add personality traits if available
        prompt += "\n**Character Background:**\n"
        for role, name in participant_names.items():
            agent_id = next((id for id, r in interaction.participants.items() if r == role), None)
            if agent_id and agent_id in agent_map:
                agent = agent_map[agent_id]
                if hasattr(agent, 'personality'):
                    personality = agent.personality
                    traits = ', '.join([f"{trait}: {getattr(personality, trait, 0)}" for trait in [
                        'cooperativeness', 'risk_tolerance', 'fairness_preference',
                        'altruism', 'rationality', 'long_term_orientation'
                    ] if hasattr(personality, trait)])

                    faction = agent.faction.value if hasattr(agent, 'faction') else "Unknown"
                    agent_type = agent.agent_type.value if hasattr(agent, 'agent_type') else "Unknown"

                    prompt += f"- {name}: A {faction} {agent_type} with these traits: {traits}\n"

                    # Add specific character interpretation prompts
                    if hasattr(personality, 'cooperativeness') and getattr(personality, 'cooperativeness', 0) > 0.7:
                        prompt += f"  {name} typically seeks harmony and collaborative solutions.\n"
                    elif hasattr(personality, 'cooperativeness') and getattr(personality, 'cooperativeness', 0) < 0.3:
                        prompt += f"  {name} often acts independently, sometimes at others' expense.\n"

                    if hasattr(personality, 'risk_tolerance') and getattr(personality, 'risk_tolerance', 0) > 0.7:
                        prompt += f"  {name} embraces uncertainty and bold ventures in this harsh Martian frontier.\n"
                    elif hasattr(personality, 'risk_tolerance') and getattr(personality, 'risk_tolerance', 0) < 0.3:
                        prompt += f"  {name} carefully calculates each move in the precarious Martian environment.\n"
                    
                    # Add resource information
                    if hasattr(agent, 'resources') and agent.resources:
                        resources_str = ', '.join([f"{r.resource_type.value}: {r.amount}" for r in agent.resources])
                        prompt += f"  {name}'s current resources: {resources_str}\n"

        # Add setting elements for immersive world-building
        prompt += "\n**Martian Setting Elements (include at least one):**\n"
        prompt += "- The thin Martian atmosphere requiring life support systems for outdoor activities\n"
        prompt += "- The challenges of resource scarcity in the isolated Mars colony\n"
        prompt += "- The different cultural perspectives between Earth-born (Terra Corp) and Mars-born colonists\n"
        prompt += "- The advanced technology that enables survival in the harsh Martian environment\n"
        prompt += "- The psychological effects of living in close quarters far from Earth\n"
        prompt += "- The unique Martian landscape: rust-colored dust, harsh winds, distant mountains\n"

        return prompt

    def _create_daily_summary_prompt(self, day: int, events: List[NarrativeEvent], agents: List[Agent]) -> str:
        """Create a prompt for the daily summary generation"""
        # Basic information
        prompt = (
            f"As the narrator chronicling life on Mars in the year 2993, create a compelling daily summary that weaves "
            f"individual events into a cohesive narrative showing how the colony evolves over time.\n\n"
            f"Day: {day} of the Mars colony simulation\n"
            f"Colony Population: {len(agents)} active colonists\n"
            f"Significant Events: {len(events)} notable interactions occurred today\n\n"
        )

        # Add economic market report if available
        if self.market_report:
            prompt += "**Economic Market Status:**\n"
            # Add key market metrics
            if 'active_goods_offers' in self.market_report:
                prompt += f"- Active goods offerings: {self.market_report['active_goods_offers']}\n"
            if 'active_goods_requests' in self.market_report:
                prompt += f"- Active goods requests: {self.market_report['active_goods_requests']}\n"
            if 'active_job_offers' in self.market_report:
                prompt += f"- Active job listings: {self.market_report['active_job_offers']}\n"
            if 'total_employees' in self.market_report:
                prompt += f"- Employed colonists: {self.market_report['total_employees']}\n"
            
            # Add resource prices if available
            if 'avg_resource_prices' in self.market_report and self.market_report['avg_resource_prices']:
                prompt += "\nAverage Resource Prices:\n"
                for resource, price in self.market_report['avg_resource_prices'].items():
                    if price > 0:
                        prompt += f"- {resource}: {price:.1f} credits\n"
            
            # Add job salaries if available
            if 'avg_job_salaries' in self.market_report and self.market_report['avg_job_salaries']:
                prompt += "\nAverage Job Salaries:\n"
                for job_type, salary in self.market_report['avg_job_salaries'].items():
                    if salary > 0:
                        prompt += f"- {job_type}: {salary:.1f} credits per turn\n"
            
            prompt += "\n"

        # Add event information
        if events:
            prompt += "**Key Events to Incorporate:**\n\n"

            # Sort events by significance
            sorted_events: list[NarrativeEvent] = sorted(events, key=lambda e: e.significance, reverse=True)

            # Include the top events based on verbosity
            max_events = min(len(sorted_events), self.verbosity * 3)
            for i, event in enumerate(sorted_events[:max_events]):
                involved = ', '.join(repr(e) for e in event.agents_involved) if event.agents_involved else None
                prompt += f"Event {i + 1}: {event.title}\n"
                prompt += f"Description: {event.description}\n"
                prompt += f"Agents involved: {involved}\n"
                prompt += f"Tags: {', '.join(event.tags)}\n"
                prompt += f"Significance level: {event.significance:.1f}/1.0\n\n"
        else:
            prompt += ("No significant events occurred today. Focus on the atmospheric conditions, "
                       "routine maintenance, or contemplative moments in the colony.\n\n")

        # Add basic population statistics
        agent_types = {}
        factions = {}
        for agent in agents:
            if agent.agent_type.value in agent_types:
                agent_types[agent.agent_type.value] += 1
            else:
                agent_types[agent.agent_type.value] = 1

            if agent.faction.value in factions:
                factions[agent.faction.value] += 1
            else:
                factions[agent.faction.value] = 1

        prompt += "**Population Demographics:**\n"
        for agent_type, count in agent_types.items():
            prompt += f"- {agent_type.capitalize()}: {count} ({count / len(agents) * 100:.1f}%)\n"
        prompt += "\n"

        prompt += "**Political Factions:**\n"
        for faction, count in factions.items():
            prompt += f"- {faction.replace('_', ' ').title()}: {count} ({count / len(agents) * 100:.1f}%)\n"
        prompt += "\n"

        # Add narrative guidance
        prompt += (
            "**Narrative Guidance:**\n"
            "- Connect individual events to show how they contribute to larger patterns and emerging dynamics\n"
            "- Reflect on how economic conditions affect social relations among different factions\n"
            "- Consider if political alliances or tensions are forming based on faction demographics\n"
            "- Notice how resource distributions are affecting different agent types and social classes\n"
            "- Include atmospheric details that give a sense of what daily life feels like on Mars\n"
            "- Identify 2-3 emerging trends that may shape future colony developments\n"
        )

        return prompt
