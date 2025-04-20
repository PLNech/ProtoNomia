"""
LLM-based Narrator module for ProtoNomia.
This module uses Ollama to generate narrative events from economic interactions.
"""
import logging
import json
from typing import List, Dict, Optional, Any, Tuple
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
        mock_llm: bool = False,
        ollama_base_url: str = "http://localhost:11434",
        temperature: float = 0.8,
        top_p: float = 0.95,
        top_k: int = 40,
        test_mode: bool = False
    ):
        """
        Initialize the LLM Narrator.
        
        Args:
            verbosity: Level of detail in generated narratives (1-5)
            model_name: Name of the Ollama model to use
            mock_llm: Whether to use mock responses instead of calling Ollama
            ollama_base_url: Base URL for the Ollama API
            temperature: Controls randomness in generation (0.0-1.0)
            top_p: Nucleus sampling probability threshold (0.0-1.0)
            top_k: Number of highest probability tokens to consider
            test_mode: Whether to use test mode for overriding in tests
        """
        super().__init__(verbosity)
        self.model_name = model_name
        self.mock_llm = mock_llm
        self.ollama_base_url = ollama_base_url
        self.temperature = temperature
        self.top_p = top_p
        self.top_k = top_k
        self.test_mode = test_mode
        logger.info(f"Initialized LLM Narrator with model {model_name}, mock={mock_llm}")
        
        # Create the OllamaClient for structured output generation
        if not self.mock_llm:
            self.ollama_client = OllamaClient(
                base_url=ollama_base_url,
                model_name=model_name,
                temperature=temperature,
                top_p=top_p,
                top_k=top_k
            )
            # Test connection
            self._test_ollama_connection()
    
    def _test_ollama_connection(self):
        """Test the connection to Ollama"""
        try:
            # Create a simple test prompt to check if the client works
            test_prompt = "Generate a one-sentence test narrative about Mars."
            system_prompt = "You are a narrator for a Mars colony simulation."
            
            # Attempt to generate a structured response
            self.ollama_client.generate_narrative(
                prompt=test_prompt,
                system_prompt=system_prompt
            )
            
            logger.info(f"Successfully connected to Ollama with model {self.model_name}")
        except Exception as e:
            logger.error(f"Error connecting to Ollama: {e}")
            logger.warning("Falling back to mock mode due to connection error")
            self.mock_llm = True
    
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
            if self.mock_llm:
                # Use mock data for testing
                title, description, tags = self._get_mock_narrative_parts(interaction.interaction_type)
            elif self.test_mode:
                # When in test mode, use the _mock_generate method which can be overridden in tests
                mock_response = self._mock_generate(prompt)
                title, description, tags = self._parse_mock_response(mock_response)
            else:
                # Use OllamaClient with structured output
                try:
                    narrative_response = self.ollama_client.generate_narrative(
                        prompt=prompt,
                        system_prompt=system_prompt
                    )
                    title = narrative_response.title
                    description = narrative_response.description
                    tags = narrative_response.tags
                except Exception as e:
                    logger.error(f"Error generating narrative with OllamaClient: {e}")
                    # Fall back to rule-based generation
                    logger.warning("Falling back to rule-based narrative generation")
                    title, description, tags = self._get_mock_narrative_parts(interaction.interaction_type)
            
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
        # Get interaction type and results
        interaction_type = interaction.interaction_type.value
        results = interaction.results
        
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
            offer = results.get('offer', 0)
            total = results.get('total', 100)
            accepted = results.get('accepted', False)
            prompt += (
                f"Details: {initiator_name} offered {responder_name} {offer} credits out of a total of {total} credits. "
                f"The offer was {'accepted' if accepted else 'rejected'} by {responder_name}.\n"
            )
        elif interaction.interaction_type == EconomicInteractionType.TRUST:
            investment = results.get('investment', 0)
            multiplier = results.get('multiplier', 3)
            returned = results.get('returned', 0)
            prompt += (
                f"Details: {initiator_name} invested {investment} credits with {responder_name}. "
                f"The investment grew by a factor of {multiplier} to {investment * multiplier} credits. "
                f"{responder_name} returned {returned} credits to {initiator_name}.\n"
            )
        
        # Add personality traits if available
        for role, name in participant_names.items():
            agent_id = next((id for id, r in interaction.participants.items() if r == role), None)
            if agent_id and agent_id in agent_map:
                agent = agent_map[agent_id]
                if hasattr(agent, 'personality_traits') and agent.personality_traits:
                    traits = ', '.join([f"{trait}: {value}" for trait, value in agent.personality_traits.items()])
                    prompt += f"{name}'s personality traits: {traits}\n"
        
        # Add instructions for the desired output format
        prompt += "\nPlease generate a creative narrative for this interaction with the following elements:\n"
        
        # Adjust level of detail based on verbosity
        detail_level = "detailed and vivid" if self.verbosity >= 4 else "concise" if self.verbosity <= 2 else "balanced"
        prompt += f"- Create a {detail_level} narrative that captures the interaction\n"
        
        return prompt
    
    def _get_mock_narrative_parts(self, interaction_type: EconomicInteractionType) -> Tuple[str, str, List[str]]:
        """Get a mock narrative when not using Ollama, returning parts directly"""
        if interaction_type == EconomicInteractionType.ULTIMATUM:
            return (
                "Tense Ultimatum Negotiation in Mars Dome",
                "Alice offered Bob 30 credits out of a 100 credit pot. After careful consideration, Bob accepted the offer, though clearly dissatisfied with the terms. The transaction was completed quickly, with Alice walking away with a significant profit while Bob seemed to be calculating whether the deal was worth the loss of social capital.",
                ["ultimatum", "negotiation", "economic_exchange"]
            )
        elif interaction_type == EconomicInteractionType.TRUST:
            return (
                "Trust Betrayed in Olympus Market",
                "Charlie invested 50 credits with Delta Corporation, which was multiplied to 150 credits through their advanced resource processing. However, Delta returned only 20 credits to Charlie, keeping the lion's share of the profits. The betrayal has not gone unnoticed by other potential investors in the marketplace.",
                ["trust", "betrayal", "investment"]
            )
        else:
            return (
                "Economic Exchange on Mars Colony",
                "A standard economic interaction took place between the participants. Resources were exchanged according to the prevailing market conditions on Mars.",
                ["economic", "exchange", "standard"]
            )
    
    def _parse_mock_response(self, response_text: str) -> Tuple[str, str, List[str]]:
        """Parse a mock response text into title, description, and tags"""
        try:
            # Try to parse as JSON first
            if '{' in response_text and '}' in response_text:
                start_idx = response_text.find('{')
                end_idx = response_text.rfind('}')
                json_text = response_text[start_idx:end_idx+1]
                data = json.loads(json_text)
                return (
                    data.get('title', 'Mock Narrative'),
                    data.get('description', 'This is a mock narrative description.'),
                    data.get('tags', ['mock', 'test'])
                )
            # Otherwise, use simple parsing
            lines = response_text.strip().split('\n')
            if len(lines) >= 2:
                return lines[0], '\n'.join(lines[1:]), ["mock", "test"]
            return 'Mock Narrative', response_text, ["mock", "test"]
        except Exception:
            return 'Mock Narrative', 'This is a mock narrative description.', ["mock", "test"]
    
    def _mock_generate(self, prompt: str) -> str:
        """
        Method for testing that allows customization of mock responses.
        This method is intended to be overridden in tests to provide specific mock responses.
        
        Args:
            prompt: The input prompt
            
        Returns:
            str: A mock response
        """
        # By default, this returns a generic response that can be customized in tests
        return "This is a mock response from the LLM narrator."
    
    def generate_daily_summary(self, day: int, events: List[NarrativeEvent], agents: List[Agent]) -> str:
        """
        Generate a daily summary of significant events using LLM.
        
        Args:
            day: The day number
            events: List of narrative events for the day
            agents: List of all agents in the simulation
            
        Returns:
            str: A daily summary narrative
        """
        # If no events, use the parent implementation
        if not events:
            return super().generate_daily_summary(day, events, agents)
        
        # Create a prompt for the daily summary
        prompt = self._create_daily_summary_prompt(day, events, agents)
        system_prompt = "You are a creative science fiction narrator summarizing daily events on a Mars colony."
        
        # Try to generate the summary with LLM
        try:
            if self.mock_llm:
                summary = self._get_mock_daily_summary(day, len(events))
            elif self.test_mode:
                # For testing
                summary = self._mock_generate(prompt)
            else:
                # Use OllamaClient with structured output
                try:
                    summary_response = self.ollama_client.generate_daily_summary(
                        prompt=prompt,
                        system_prompt=system_prompt
                    )
                    summary = summary_response.summary
                except Exception as e:
                    logger.error(f"Error generating daily summary with OllamaClient: {e}")
                    # Fall back to mock summary
                    summary = self._get_mock_daily_summary(day, len(events))
            
            if summary:
                return summary
        except Exception as e:
            logger.error(f"Error generating LLM daily summary: {e}")
        
        # Fall back to rule-based summary if LLM fails
        logger.warning("Falling back to rule-based daily summary")
        return super().generate_daily_summary(day, events, agents)
    
    def _create_daily_summary_prompt(self, day: int, events: List[NarrativeEvent], agents: List[Agent]) -> str:
        """Create a prompt for the daily summary"""
        # Sort events by significance
        significant_events = sorted(events, key=lambda e: e.significance, reverse=True)
        
        # Map agent IDs to names
        agent_map = {agent.id: agent.name for agent in agents}
        
        # Create the prompt
        prompt = (
            f"Please write a daily summary for Day {day} on a Mars colony in the year 2993.\n\n"
            f"There are {len(agents)} colonists and {len(events)} significant events occurred today.\n\n"
        )
        
        # Add the most significant events
        prompt += "Here are the most notable events:\n\n"
        
        for i, event in enumerate(significant_events[:min(5, len(significant_events))]):
            # Get agent names involved
            agent_names = [agent_map.get(agent_id, "Unknown") for agent_id in event.agents_involved]
            
            prompt += (
                f"Event {i+1}: {event.title}\n"
                f"Participants: {', '.join(agent_names)}\n"
                f"Description: {event.description}\n"
                f"Significance: {event.significance}\n\n"
            )
        
        # Instructions for formatting
        prompt += (
            f"Please write a creative daily summary in Markdown format with the following sections:\n"
            f"1. A title 'Day {day} on Mars'\n"
            f"2. An introduction paragraph about the general state of the Mars colony\n"
            f"3. A 'Notable Events' section with subsections for the most significant events\n"
            f"4. A conclusion paragraph reflecting on the day and looking toward the future\n\n"
            f"Be creative and engaging, using a narrative style appropriate for a science fiction story."
        )
        
        # Adjust verbosity based on the setting
        if self.verbosity >= 4:
            prompt += "\n\nPlease provide a detailed and vivid summary with rich descriptions and character motivations."
        elif self.verbosity <= 2:
            prompt += "\n\nPlease keep the summary concise and focused on key events."
        
        return prompt
    
    def _get_mock_daily_summary(self, day: int, event_count: int) -> str:
        """Get a mock daily summary when not using Ollama"""
        return (
            f"# Day {day} on Mars\n\n"
            f"The red dust swirled outside the habitats as {event_count} notable events shaped the economy of the Mars colony today.\n\n"
            f"## Notable Events\n\n"
            f"### Tense Negotiation at Olympus Market\n"
            f"Two colonists engaged in a heated bargaining session over limited water rights, eventually reaching a compromise that left neither fully satisfied but both able to continue operations.\n\n"
            f"### Trust Betrayed at Tharsis Trading Hub\n"
            f"A significant investment opportunity turned sour when a trustee failed to return fair profits to their investor, causing ripples of caution throughout the financial community.\n\n"
            f"As another Martian day comes to a close, the colonists retreat to their habitats to plan for tomorrow's opportunities and challenges in this harsh but promising frontier."
        )

    def generate_narrative_from_interaction(self, interaction: EconomicInteraction) -> str:
        """
        Generate a narrative from an economic interaction.
        
        Args:
            interaction: The economic interaction to generate a narrative from.
            
        Returns:
            A JSON-formatted string containing the narrative.
        """
        # Create a prompt for the LLM
        prompt = f"Generate a narrative for a {interaction.interaction_type.value} interaction between Mars colonists."
        
        if self.mock_llm:
            # Get the mock narrative as a JSON string
            mock_title, mock_desc, mock_tags = self._get_mock_narrative_parts(interaction.interaction_type)
            return json.dumps({
                "title": mock_title,
                "description": mock_desc,
                "tags": mock_tags
            })
        elif self.test_mode:
            # When in test mode, use the _mock_generate method which can be overridden in tests
            return self._mock_generate(prompt)
        else:
            try:
                # Use OllamaClient with structured output
                narrative_response = self.ollama_client.generate_narrative(prompt=prompt)
                
                # Convert to JSON string for backward compatibility
                return json.dumps({
                    "title": narrative_response.title,
                    "description": narrative_response.description,
                    "tags": narrative_response.tags
                })
            except Exception as e:
                logger.error(f"Error generating narrative: {e}")
                # Fall back to mock narrative
                mock_title, mock_desc, mock_tags = self._get_mock_narrative_parts(interaction.interaction_type)
                return json.dumps({
                    "title": mock_title,
                    "description": mock_desc,
                    "tags": mock_tags
                }) 