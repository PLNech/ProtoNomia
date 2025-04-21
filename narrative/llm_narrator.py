"""
LLM-based Narrator module for ProtoNomia.
This module uses Ollama to generate narrative events from economic interactions.
"""
import logging
from typing import List, Dict
from datetime import datetime

from models.base import (
    Agent, EconomicInteraction, EconomicInteractionType, InteractionRole, 
    NarrativeEvent, NarrativeArc
)
from narrative.narrator import Narrator
from llm_utils import OllamaClient
from llm_models import NarrativeResponse, DailySummaryResponse

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
        model_name: str = "gemma3:1b", 
        ollama_base_url: str = "http://localhost:11434",
        temperature: float = 0.8,
        top_p: float = 0.95,
        top_k: int = 40,
        timeout: int = 30,
        max_retries: int = 3
    ):
        """
        Initialize the LLM Narrator.
        
        Args:
            verbosity: Level of detail in generated narratives (1-5)
            model_name: Name of the Ollama model to use
            ollama_base_url: Base URL for the Ollama API
            temperature: Controls randomness in generation (0.0-1.0)
            top_p: Nucleus sampling probability threshold (0.0-1.0)
            top_k: Number of highest probability tokens to consider
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries on failure
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
            max_tokens=1000,
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
        
        Args:
            interaction: The economic interaction to generate a narrative from
            agents: List of agents involved in the interaction
            
        Returns:
            NarrativeEvent: The generated narrative event
        """
        try:
            # Map agent IDs to agent objects for easier lookup
            agent_map = {agent.id: agent for agent in agents}
            
            # Get participant agent names
            participant_names = {}
            for agent_id, role in interaction.participants.items():
                if agent_id in agent_map:
                    participant_names[role] = agent_map[agent_id].name
            
            # Log some diagnostic information
            logger.debug(f"Generating narrative for interaction: {interaction.id}")
            logger.debug(f"Interaction type: {interaction.interaction_type.value}")
            logger.debug(f"Participants: {list(participant_names.values())}")
            
            # Create a prompt for the LLM
            prompt = self._create_interaction_prompt(interaction, participant_names, agent_map)
            system_prompt = "You are a creative narrator for a Mars colony simulation, describing economic interactions between colonists."
            
            # Generate the narrative using structured output
            narrative_response = self.ollama_client.generate_narrative(
                prompt=prompt,
                system_prompt=system_prompt
            )
            title = narrative_response.title
            description = narrative_response.description
            tags = narrative_response.tags
            
            # Create and return the narrative event
            event = NarrativeEvent(
                timestamp=datetime.now(),
                title=title,
                description=description,
                agents_involved=list(interaction.participants.keys()),
                interaction_id=interaction.id,
                significance=interaction.narrative_significance,
                tags=tags
            )
            
            logger.debug(f"Generated narrative event: {title}")
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
        initiator_name = participant_names.get(InteractionRole.INITIATOR, "Agent1")
        responder_name = participant_names.get(InteractionRole.RESPONDER, "Agent2")
        
        # Create the prompt based on the interaction type
        prompt = (
            f"Please generate a narrative for the following economic interaction on Mars in the year 2993:\n\n"
            f"Interaction Type: {interaction_type}\n"
            f"Participants: {initiator_name} (Initiator) and {responder_name} (Responder)\n"
        )
        
        # Add specific details based on interaction type
        if interaction.interaction_type == EconomicInteractionType.ULTIMATUM:
            offer = parameters.get('offer_amount', 0)
            total = parameters.get('total_amount', 100)
            accepted = parameters.get('responder_accepts', False)
            prompt += (
                f"Details: {initiator_name} offered {responder_name} {offer} credits out of a total of {total} credits. "
                f"The offer was {'accepted' if accepted else 'rejected'} by {responder_name}.\n"
            )
        elif interaction.interaction_type == EconomicInteractionType.TRUST:
            investment = parameters.get('investment', 0)
            multiplier = parameters.get('multiplier', 3)
            returned = parameters.get('returned', 0)
            prompt += (
                f"Details: {initiator_name} invested {investment} credits with {responder_name}. "
                f"The investment grew by a factor of {multiplier} to {investment * multiplier} credits. "
                f"{responder_name} returned {returned} credits to {initiator_name}.\n"
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
                f"Details: This is a public goods game with multiple participants.\n"
                f"Each agent contributed the following amounts: {contributions_str}\n"
                f"The total contribution was {total_contribution} credits, which was multiplied by {multiplier}.\n"
                f"The final pot of {total_return} credits was distributed as follows: {returns_str}\n"
            )
        else:
            # Generic prompt for other interaction types
            prompt += (
                f"Details: The interaction involves economic exchange between {initiator_name} and {responder_name}. "
                f"Parameters: {', '.join([f'{k}: {v}' for k, v in parameters.items()])}\n"
            )
        
        # Add personality traits if available
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
                    prompt += f"{name}'s personality traits: {traits}\n"
        
        # Add instructions for the desired output format
        prompt += "\nPlease generate a creative narrative for this interaction with the following elements:\n"
        prompt += "- Create a catchy title for this event\n"
        prompt += "- Write a detailed description of what happened during the interaction\n"
        prompt += "- Add relevant tags (keywords) that categorize this event\n"
        
        # Adjust level of detail based on verbosity
        detail_level = "detailed and vivid" if self.verbosity >= 4 else "concise" if self.verbosity <= 2 else "balanced"
        prompt += f"\nGenerate a {detail_level} narrative in JSON format with title, description, and tags fields."
        
        return prompt
    
    def generate_daily_summary(self, day: int, events: List[NarrativeEvent], agents: List[Agent]) -> str:
        """
        Generate a daily summary of events for the simulation.
        
        Args:
            day: The current day of the simulation
            events: List of narrative events for the day
            agents: List of all agents in the simulation
            
        Returns:
            str: A daily summary in markdown format
        """
        try:
            # Create a prompt for the daily summary
            prompt = self._create_daily_summary_prompt(day, events, agents)
            system_prompt = "You are a creative narrator for a Mars colony simulation, creating a daily summary of events."
            
            # Generate the daily summary using Ollama
            summary_response = self.ollama_client.generate_daily_summary(
                prompt=prompt,
                system_prompt=system_prompt
            )
            
            return summary_response.summary
            
        except Exception as e:
            logger.error(f"Error generating daily summary: {e}")
            # Fallback to a simple summary in case of error
            return f"# Day {day} on Mars\n\n" + \
                  f"Today, {len(events)} events occurred in the Mars colony.\n\n" + \
                  f"The simulation has {len(agents)} active agents."
    
    def _create_daily_summary_prompt(self, day: int, events: List[NarrativeEvent], agents: List[Agent]) -> str:
        """Create a prompt for the daily summary generation"""
        # Basic information
        prompt = (
            f"Please generate a daily summary for Day {day} of the Mars colony simulation in the year 2993.\n\n"
            f"There are {len(agents)} active agents in the colony.\n"
            f"Today, {len(events)} significant events occurred.\n\n"
        )
        
        # Add event information
        if events:
            prompt += "Here are the key events of the day:\n\n"
            
            # Sort events by significance
            sorted_events = sorted(events, key=lambda e: e.significance, reverse=True)
            
            # Include the top events based on verbosity
            max_events = min(len(sorted_events), self.verbosity * 3)
            for i, event in enumerate(sorted_events[:max_events]):
                prompt += f"Event {i+1}: {event.title}\n"
                prompt += f"Description: {event.description}\n"
                prompt += f"Agents involved: {', '.join(event.agents_involved)}\n"
                prompt += f"Tags: {', '.join(event.tags)}\n\n"
        else:
            prompt += "No significant events occurred today.\n\n"
        
        # Add basic population statistics
        agent_types = {}
        for agent in agents:
            agent_type = agent.agent_type.value
            if agent_type in agent_types:
                agent_types[agent_type] += 1
            else:
                agent_types[agent_type] = 1
        
        prompt += "Population statistics:\n"
        for agent_type, count in agent_types.items():
            prompt += f"- {agent_type}: {count}\n"
        
        # Add instructions for the desired output format
        prompt += "\nPlease generate a creative daily summary with the following elements:\n"
        prompt += "- A headline for the day\n"
        prompt += "- A narrative overview of the day's events\n"
        prompt += "- Highlights of the most significant interactions\n"
        prompt += "- Emerging trends or patterns\n"
        
        # Adjust level of detail based on verbosity
        detail_level = "detailed and comprehensive" if self.verbosity >= 4 else "brief" if self.verbosity <= 2 else "moderate"
        prompt += f"\nGenerate a {detail_level} summary in Markdown format with headings, paragraphs, and sections."
        
        return prompt
    
    def generate_narrative_from_interaction(self, interaction: EconomicInteraction) -> str:
        """
        Legacy method to generate a simple narrative from an interaction.
        
        Args:
            interaction: The economic interaction to generate a narrative from
            
        Returns:
            str: A narrative description of the interaction
        """
        # This method is kept for backward compatibility
        try:
            # Create a simplified prompt
            prompt = f"Generate a narrative for an {interaction.interaction_type.value} interaction in a Mars colony."
            
            # Generate narrative using OllamaClient
            return self.ollama_client.generate_text(prompt=prompt)
            
        except Exception as e:
            logger.error(f"Error generating simplified narrative: {e}")
            return f"An {interaction.interaction_type.value} interaction occurred." 