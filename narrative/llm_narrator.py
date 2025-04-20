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
            # First, check if Ollama service is running by checking available models
            tags_url = f"{self.ollama_base_url}/api/tags"
            tags_response = requests.get(tags_url, timeout=5)
            
            if tags_response.status_code != 200:
                logger.warning(f"Failed to retrieve Ollama models. Status code: {tags_response.status_code}")
                self.mock_llm = True
                return
            
            # Check if the specific model is available
            models = tags_response.json().get('models', [])
            model_names = [model['name'] for model in models]
            
            if self.model_name not in model_names:
                logger.warning(f"Model {self.model_name} not found. Available models: {model_names}")
                # Try to use the first available model or fall back to mock
                if model_names:
                    self.model_name = model_names[0]
                    logger.info(f"Switching to available model: {self.model_name}")
                else:
                    logger.warning("No models available. Falling back to mock mode.")
                    self.mock_llm = True
                    return
            
            # Test model generation
            url = f"{self.ollama_base_url}/api/generate"
            response = requests.post(
                url,
                json={
                    "model": self.model_name,
                    "prompt": "Hello, are you working?",
                    "stream": False,
                    "temperature": 0.1,  # Low temperature for consistent response
                    "max_tokens": 10
                },
                timeout=10  # Longer timeout for generation
            )
            
            if response.status_code != 200:
                logger.warning(f"Model generation failed. Status code: {response.status_code}")
                logger.warning(f"Response content: {response.text}")
                self.mock_llm = True
                return
            
            # Verify response structure
            result = response.json()
            if 'response' not in result:
                logger.warning("Invalid response from Ollama. Missing 'response' key.")
                self.mock_llm = True
                return
            
            logger.info(f"Successfully connected to Ollama with model {self.model_name}")
        
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error to Ollama: {e}")
            logger.error("Ensure Ollama service is running and accessible.")
            self.mock_llm = True
        
        except requests.exceptions.Timeout:
            logger.error("Timeout connecting to Ollama. Check network or service availability.")
            self.mock_llm = True
        
        except Exception as e:
            logger.error(f"Unexpected error testing Ollama connection: {e}")
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
            
            logger.debug(f"Generated narrative event: {title}")
            return event
            
        except Exception as e:
            logger.error(f"Error in generate_event_from_interaction: {e}")
            # Create a minimal fallback event to avoid breaking the simulation
            fallback_event = NarrativeEvent(
                timestamp=datetime.now(),
                title="Economic Interaction",
                description="An economic exchange occurred between agents.",
                agents_involved=list(interaction.participants.keys()),
                interaction_id=interaction.id,
                significance=interaction.narrative_significance,
                tags=["fallback", "error_recovery"]
            )
            return fallback_event
    
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
            
            logger.debug(f"Raw LLM response: {response_text[:100]}...")
            
            # Parse the JSON response
            # First, try to find JSON in the response in case the LLM added other text
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}')
            
            if start_idx != -1 and end_idx != -1:
                json_text = response_text[start_idx:end_idx+1]
                logger.debug(f"Extracted JSON: {json_text[:100]}...")
                
                # Try different approaches to parse JSON
                try:
                    # First attempt with standard parsing
                    response_data = json.loads(json_text)
                except json.JSONDecodeError as e:
                    logger.warning(f"Standard JSON parsing failed: {e}")
                    # Try to clean up the JSON text - handle common issues
                    cleaned_json = json_text.replace('\n', ' ').replace('\r', ' ')
                    # Remove any trailing commas before closing braces/brackets
                    cleaned_json = cleaned_json.replace(',}', '}').replace(',]', ']')
                    # Try with more lenient parsing
                    try:
                        import re
                        # Extract only the JSON-like structure
                        pattern = r'\{.*\}'
                        match = re.search(pattern, cleaned_json, re.DOTALL)
                        if match:
                            cleaned_json = match.group(0)
                        response_data = json.loads(cleaned_json)
                        logger.info("Successfully parsed JSON after cleaning")
                    except Exception as e2:
                        logger.error(f"Failed to parse JSON even after cleaning: {e2}")
                        # As a last resort, create a simple structure
                        response_data = {
                            "title": f"Interaction on Mars",
                            "description": "An economic exchange occurred between Martian colonists.",
                            "tags": ["economic", "mars", "interaction"]
                        }
                
                title = response_data.get("title", "")
                description = response_data.get("description", "")
                tags = response_data.get("tags", [])
                
                logger.debug(f"Successfully extracted narrative - Title: {title}")
                return title, description, tags
            else:
                logger.warning(f"Failed to extract JSON from LLM response - no curly braces found")
                # Try to salvage something useful from the response
                lines = response_text.strip().split('\n')
                if len(lines) >= 2:
                    # Try to extract a title and description from the text
                    return lines[0], '\n'.join(lines[1:]), ["generated", "non-json"]
                    
                return "Economic Interaction", response_text, ["fallback"]
                
        except Exception as e:
            logger.error(f"Error generating LLM narrative: {e}")
            logger.error(f"Response that caused the error: {response_text[:200]}")
            return "", "", []
    
    def _call_ollama(self, prompt: str) -> str:
        """Call Ollama API to generate text"""
        try:
            url = f"{self.ollama_base_url}/api/generate"
            start_time = time.time()
            
            logger.debug(f"Calling Ollama API with model {self.model_name}")
            logger.debug(f"Prompt starts with: {prompt[:100]}...")
            
            request_data = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "temperature": self.temperature,
                "top_p": self.top_p,
                "top_k": self.top_k,
                "max_tokens": 500  # Limit response length
            }
            
            logger.debug(f"Request parameters: temp={self.temperature}, top_p={self.top_p}, top_k={self.top_k}")
            
            try:
                response = requests.post(
                    url,
                    json=request_data,
                    timeout=30  # Longer timeout for narrative generation
                )
            except requests.exceptions.ConnectionError:
                logger.error("Connection error when calling Ollama. Ensure service is running.")
                return ""
            except requests.exceptions.Timeout:
                logger.error("Timeout when calling Ollama. Check network or service availability.")
                return ""
            
            generation_time = time.time() - start_time
            logger.debug(f"Ollama response generated in {generation_time:.2f} seconds")
            
            if response.status_code != 200:
                logger.error(f"Ollama API returned status code {response.status_code}")
                logger.error(f"Response content: {response.text[:200]}")
                return ""
            
            try:
                result = response.json()
            except ValueError:
                logger.error("Failed to parse JSON response from Ollama")
                return ""
            
            response_text = result.get("response", "")
            logger.debug(f"Response length: {len(response_text)} characters")
            
            # Additional validation
            if not response_text or len(response_text) < 10:
                logger.warning("Ollama returned an unusually short or empty response")
                return ""
            
            return response_text
        
        except Exception as e:
            logger.error(f"Unexpected error calling Ollama: {e}")
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
        
        :
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