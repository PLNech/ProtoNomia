"""
LLM-based Narrator module for ProtoNomia.
This module uses Ollama to generate narrative events from economic interactions.
"""
import logging
from typing import List, Dict
from datetime import datetime

from models.base import (
    Agent, EconomicInteraction, EconomicInteractionType, InteractionRole,
    NarrativeEvent
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

            # Get participant agent names
            participant_names = {}
            for agent_id, role in interaction.participants.items():
                if agent_id in agent_map:
                    participant_names[role] = agent_map[agent_id].name

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
                agents_involved=list(interaction.participants,
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
                agents_involved=list(interaction.participants.keys()),
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
            # FIXME: Consider fallback to a simple summary in case of error
            return f"# Day {day} on Mars\n\n" + \
                f"Today, {len(events)} events occurred in the Mars colony.\n\n" + \
                f"The simulation has {len(agents)} active agents."

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

        # Get participant names
        proposer_name = participant_names.get(InteractionRole.PROPOSER, "Agent1")
        responder_name = participant_names.get(InteractionRole.RESPONDER, "Agent2")

        # Create the prompt based on the interaction type
        prompt = (
            f"As the narrator for the Mars colony in the year 2993, describe a meaningful economic interaction "
            f"that reveals character traits and advances relationships through authentic dialogue and vivid details.\n\n"
            f"Interaction Type: {interaction_type}\n"
            f"Participants: {proposer_name} (Proposer) and {responder_name} (Responder)\n"
        )

        # Add specific details based on interaction type
        if interaction.interaction_type == EconomicInteractionType.ULTIMATUM:
            offer = parameters.get('offer_amount', 0)
            total = parameters.get('total_amount', 100)
            accepted = parameters.get('responder_accepts', False)
            prompt += (
                f"Core Event: {proposer_name} offered {responder_name} {offer} credits out of a total of {total} credits. "
                f"The offer was {'accepted' if accepted else 'rejected'} by {responder_name}.\n\n"
                f"Consider what this reveals about power dynamics, negotiation styles, and the personal history between them. "
                f"What motivated this particular offer? What consequences might this have for their future interactions?\n"
            )
        elif interaction.interaction_type == EconomicInteractionType.TRUST:
            investment = parameters.get('investment', 0)
            multiplier = parameters.get('multiplier', 3)
            returned = parameters.get('returned', 0)
            prompt += (
                f"Core Event: {proposer_name} invested {investment} credits with {responder_name}. "
                f"The investment grew by a factor of {multiplier} to {investment * multiplier} credits. "
                f"{responder_name} returned {returned} credits to {proposer_name}.\n\n"
                f"Consider the emotional stakes, prior experiences that built or eroded trust, and how this "
                f"exchange affects the community's perception of both parties. Is this part of a pattern or an unusual event?\n"
            )
        elif interaction.interaction_type == EconomicInteractionType.PUBLIC_GOODS:
            contributions = parameters.get('contributions', {})
            total_contribution = parameters.get('total_contribution', 0)
            multiplier = parameters.get('multiplier', 2)
            total_return = parameters.get('total_return', 0)
            individual_returns = parameters.get('individual_returns', {})

            # Format the contributions string
            contributions_str = ", ".join([f"{agent_map.get(agent_id, agent_id)}: {amount}"
                                           for agent_id, amount in contributions.items()])
            returns_str = ", ".join([f"{agent_map.get(agent_id, agent_id)}: {amount}"
                                     for agent_id, amount in individual_returns.items()])

            prompt += (
                f"Core Event: Several colonists participated in a public goods game with these contributions: {contributions_str}\n"
                f"The total contribution was {total_contribution} credits, which was multiplied by {multiplier}.\n"
                f"The final pot of {total_return} credits was distributed as follows: {returns_str}\n\n"
                f"Consider how this community effort reflects faction tensions, resource disparities, or shifting alliances. "
                f"How do different contribution levels reveal each character's priorities and values? "
                f"Are there free-riders or exceptionally generous contributors?\n"
            )
        else:
            # Generic prompt for other interaction types
            prompt += (
                f"Core Event: An economic exchange between {proposer_name} and {responder_name} with these details: "
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

        # Add setting elements for immersive world-building
        prompt += "\n**Martian Setting Elements (include at least one):**\n"
        prompt += "- The thin Martian atmosphere requiring life support systems for outdoor activities\n"
        prompt += "- Limited resources creating tension between survival needs and luxury goods\n"
        prompt += "- Faction dynamics between Earth corporations, Mars natives, and independent groups\n"
        prompt += "- Technological adaptations unique to Mars' gravity, dust, and radiation challenges\n"
        prompt += "- Cultural traditions that have evolved specifically on Mars over generations\n"

        # Add instructions for the desired output format with improved narrative guidance
        prompt += "\n**Narrative Guidance:**\n"
        prompt += "1. Create a catchy, thematic title that captures the core economic tension or relationship\n"
        prompt += ("2. Write a detailed scene with dialogue showing this interaction "
                   "through character actions and reactions\n")
        prompt += "3. Include specific environmental details that ground this exchange in the Martian setting\n"
        prompt += "4. Connect this event to broader themes of survival, community, or adaptation on Mars\n"
        prompt += "5. Add relevant tags (keywords) categorizing this event (economics, conflict, collaboration, etc.)\n"

        # Adjust level of detail based on verbosity
        detail_level = "vivid and emotionally nuanced" if self.verbosity >= 4 \
            else "concise but character-driven" if self.verbosity <= 2 else "balanced and meaningful"
        prompt += f"\nGenerate a {detail_level} narrative in JSON format with title, description, and tags fields."

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

        # Add event information
        if events:
            prompt += "**Key Events to Incorporate:**\n\n"

            # Sort events by significance
            sorted_events = sorted(events, key=lambda e: e.significance, reverse=True)

            # Include the top events based on verbosity
            max_events = min(len(sorted_events), self.verbosity * 3)
            for i, event in enumerate(sorted_events[:max_events]):
                prompt += f"Event {i + 1}: {event.title}\n"
                prompt += f"Description: {event.description}\n"
                prompt += f"Agents involved: {', '.join(event.agents_involved)}\n"
                prompt += f"Tags: {', '.join(event.tags)}\n"
                prompt += f"Significance level: {event.significance:.1f}/1.0\n\n"
        else:
            prompt += ("No significant events occurred today. Focus on the atmospheric conditions, "
                       "routine maintenance, or contemplative moments in the colony.\n\n")

        # Add basic population statistics
        agent_types = {}
        factions = {}
        for agent in agents:
            agent_type = agent.agent_type.value
            if agent_type in agent_types:
                agent_types[agent_type] += 1
            else:
                agent_types[agent_type] = 1

            faction = agent.faction.value if hasattr(agent, 'faction') else "Unknown"
            if faction in factions:
                factions[faction] += 1
            else:
                factions[faction] = 1

        prompt += "**Colony Demographics:**\n"
        prompt += "Population by type:\n"
        for agent_type, count in agent_types.items():
            prompt += f"- {agent_type}: {count}\n"

        prompt += "\nPopulation by faction:\n"
        for faction, count in factions.items():
            prompt += f"- {faction}: {count}\n"

        # Add potential narrative themes
        prompt += "\n**Potential Narrative Themes (incorporate at least one):**\n"
        prompt += "- Adaptation and survival in the harsh Martian environment\n"
        prompt += "- Economic tensions between different factions or social classes\n"
        prompt += "- Technological innovation and scientific discovery\n"
        prompt += "- Community building and cultural development on Mars\n"
        prompt += "- Individual ambitions versus collective needs\n"
        prompt += "- The impact of resource scarcity on social structures\n"

        # Add instructions for the desired output format with improved narrative guidance
        prompt += "\n**Summary Structure:**\n"
        prompt += "1. Create an engaging headline that captures the day's most important theme or development\n"
        prompt += "2. Write an opening paragraph establishing the general mood and atmosphere in the colony\n"
        prompt += "3. Weave the key events together into a cohesive narrative (not just a list of separate events)\n"
        prompt += "4. Include at least one specific character moment that humanizes the economic data\n"
        prompt += "5. Conclude with emerging trends, patterns, or tensions building in the colony\n"

        # Adjust level of detail based on verbosity
        detail_level = "richly detailed and character-focused" if self.verbosity >= 4 \
            else "concise but thematically unified" if self.verbosity <= 2 \
            else "balanced with both overview and specific moments"
        prompt += f"\nGenerate a {detail_level} summary."

        return prompt
