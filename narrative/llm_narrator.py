"""
LLM-based Narrator module for ProtoNomia.
This module uses Ollama to generate narrative events from economic interactions.
"""
import logging
import json
import time
import requests
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime

from models.base import (
    Agent, EconomicInteraction, EconomicInteractionType, InteractionRole, 
    NarrativeEvent, NarrativeArc
)
from narrative.narrator import Narrator

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
        
        # Test Ollama connection if not using mocks
        if not self.mock_llm:
            self._test_ollama_connection()
    
    def _test_ollama_connection(self):
        """Test the connection to Ollama"""
        try:
            url = f"{self.ollama_base_url}/api/generate"
            response = requests.post(
                url,
                json={
                    "model": self.model_name,
                    "prompt": "Hello, are you working?",
                    "stream": False
                },
                timeout=5
            )
            response.raise_for_status()
            logger.info(f"Successfully connected to Ollama with model {self.model_name}")
        except Exception as e:
            logger.warning(f"Failed to connect to Ollama: {e}")
            logger.warning("Narrative generation will continue with mock responses")
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
        # Map agent IDs to agent objects for easier lookup
        agent_map = {agent.id: agent for agent in agents}
        
        # Get participant agent names
        participant_names = {}
        for agent_id, role in interaction.participants.items():
            if agent_id in agent_map:
                participant_names[role] = agent_map[agent_id].name
        
        # Create a prompt for the LLM
        prompt = self._create_interaction_prompt(interaction, participant_names, agent_map)
        
        # Generate the narrative using LLM
        title, description, tags = self._generate_llm_narrative(prompt, interaction.interaction_type)
        
        # If LLM fails, fall back to rule-based generation
        if not title or not description:
            logger.warning("LLM narrative generation failed, falling back to rule-based generation")
            if interaction.interaction_type == EconomicInteractionType.ULTIMATUM:
                title, description, tags = self._generate_ultimatum_narrative(
                    interaction, participant_names, agent_map
                )
            elif interaction.interaction_type == EconomicInteractionType.TRUST:
                title, description, tags = self._generate_trust_narrative(
                    interaction, participant_names, agent_map
                )
            else:
                title, description, tags = self._generate_generic_narrative(
                    interaction, participant_names, agent_map
                )
        
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
        
        logger.debug(f"Generated LLM narrative event: {title}")
        return event
    
    def _create_interaction_prompt(
        self, 
        interaction: EconomicInteraction,
        participant_names: Dict[InteractionRole, str],
        agent_map: Dict[str, Agent]
    ) -> str:
        """Create a prompt for the LLM based on the interaction"""
        interaction_type = interaction.interaction_type.value.replace('_', ' ').title()
        
        # Base prompt with scenario details
        prompt = (
            f"Please generate a narrative for an economic interaction on Mars in the year 2993.\n\n"
            f"Interaction type: {interaction_type}\n"
            f"Participants:\n"
        )
        
        # Add participants with details
        for agent_id, role in interaction.participants.items():
            if agent_id in agent_map:
                agent = agent_map[agent_id]
                prompt += (
                    f"- {agent.name} (Role: {role.value}, Type: {agent.agent_type.value}, "
                    f"Faction: {agent.faction.value})\n"
                )
        
        # Add interaction parameters
        prompt += "\nInteraction parameters:\n"
        for key, value in interaction.parameters.items():
            prompt += f"- {key}: {value}\n"
        
        # Add narrative significance
        prompt += f"\nNarrative significance (0.0-1.0): {interaction.narrative_significance}\n"
        
        # Add verbosity instruction
        if self.verbosity >= 4:
            prompt += "\nPlease provide a detailed and vivid narrative with character motivations and environmental details."
        elif self.verbosity >= 2:
            prompt += "\nPlease provide a moderately detailed narrative focusing on the key events."
        else:
            prompt += "\nPlease provide a brief, concise narrative focusing only on essential details."
        
        # Request specific output format
        prompt += (
            "\n\nPlease respond in the following JSON format:\n"
            "{\n"
            '  "title": "A catchy title for this event",\n'
            '  "description": "The narrative description of the event",\n'
            '  "tags": ["tag1", "tag2", "tag3"]\n'
            "}\n"
        )
        
        return prompt
    
    def _generate_llm_narrative(
        self, 
        prompt: str,
        interaction_type: EconomicInteractionType
    ) -> Tuple[str, str, List[str]]:
        """Generate a narrative using the LLM"""
        try:
            if self.mock_llm:
                response_text = self._get_mock_narrative(interaction_type)
            else:
                response_text = self._call_ollama(prompt)
            
            # Parse the JSON response
            # First, try to find JSON in the response in case the LLM added other text
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}')
            
            if start_idx != -1 and end_idx != -1:
                json_text = response_text[start_idx:end_idx+1]
                response_data = json.loads(json_text)
                
                title = response_data.get("title", "")
                description = response_data.get("description", "")
                tags = response_data.get("tags", [])
                
                return title, description, tags
            else:
                logger.warning("Failed to extract JSON from LLM response")
                return "", "", []
                
        except Exception as e:
            logger.error(f"Error generating LLM narrative: {e}")
            return "", "", []
    
    def _call_ollama(self, prompt: str) -> str:
        """Call Ollama API to generate text"""
        try:
            url = f"{self.ollama_base_url}/api/generate"
            start_time = time.time()
            
            response = requests.post(
                url,
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "temperature": self.temperature,
                    "top_p": self.top_p,
                    "top_k": self.top_k
                },
                timeout=30  # Longer timeout for narrative generation
            )
            
            response.raise_for_status()
            generation_time = time.time() - start_time
            logger.debug(f"Ollama response generated in {generation_time:.2f} seconds")
            
            result = response.json()
            return result.get("response", "")
        
        except Exception as e:
            logger.error(f"Error calling Ollama: {e}")
            return ""
    
    def _get_mock_narrative(self, interaction_type: EconomicInteractionType) -> str:
        """Get a mock narrative response when not using Ollama"""
        if interaction_type == EconomicInteractionType.ULTIMATUM:
            return json.dumps({
                "title": "Tense Ultimatum Negotiation in Mars Dome",
                "description": "Alice offered Bob 30 credits out of a 100 credit pot. After careful consideration, Bob accepted the offer, though clearly dissatisfied with the terms. The transaction was completed quickly, with Alice walking away with a significant profit while Bob seemed to be calculating whether the deal was worth the loss of social capital.",
                "tags": ["ultimatum", "negotiation", "economic_exchange"]
            })
        elif interaction_type == EconomicInteractionType.TRUST:
            return json.dumps({
                "title": "Trust Betrayed in Olympus Market",
                "description": "Charlie invested 50 credits with Delta Corporation, which was multiplied to 150 credits through their advanced resource processing. However, Delta returned only 20 credits to Charlie, keeping the lion's share of the profits. The betrayal has not gone unnoticed by other potential investors in the marketplace.",
                "tags": ["trust", "betrayal", "investment"]
            })
        else:
            return json.dumps({
                "title": "Economic Exchange on Mars Colony",
                "description": "A standard economic interaction took place between the participants. Resources were exchanged according to the prevailing market conditions on Mars.",
                "tags": ["economic", "exchange", "standard"]
            })
    
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
        
        # Try to generate the summary with LLM
        try:
            if self.mock_llm:
                summary = self._get_mock_daily_summary(day, len(events))
            else:
                summary = self._call_ollama(prompt)
            
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
        # Map agent IDs to agent objects for easier lookup
        # We don't have agents list here, so we can only use the interaction data
        participant_names = {}
        agent_map = {}
        
        # Create a prompt for the LLM
        prompt = self._create_interaction_prompt(interaction, participant_names, agent_map)
        
        if self.mock_llm:
            return self._get_mock_narrative(interaction.interaction_type)
        elif self.test_mode:
            # When in test mode, use the _mock_generate method which can be overridden in tests
            return self._mock_generate(prompt)
        else:
            return self._call_ollama(prompt) 