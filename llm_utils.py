"""
Utility functions for LLM interactions in ProtoNomia.
Provides common functionality for Ollama API calls and connection testing.
"""
import json
import logging
import re
import time
from typing import List, Tuple, Type, TypeVar

import instructor
import requests
from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential

from llm_models import NarrativeResponse, DailySummaryResponse

# Initialize logger
logger = logging.getLogger(__name__)

# Type variable for generic model typing
T = TypeVar('T', bound=BaseModel)


def test_ollama_connection(
    ollama_base_url: str, 
    model_name: str, 
    timeout: int = 10
) -> Tuple[bool, str, List[str]]:
    """
    Test the connection to Ollama and validate model availability.
    
    Args:
        ollama_base_url: Base URL for Ollama API
        model_name: Name of the model to use
        timeout: Connection timeout in seconds
    
    Returns:
        Tuple of (connection_success, selected_model, available_models)
    """
    try:
        # Check available models
        tags_url = f"{ollama_base_url}/api/tags"
        tags_response = requests.get(tags_url, timeout=timeout)
        
        if tags_response.status_code != 200:
            logger.warning(f"Failed to retrieve Ollama models. Status code: {tags_response.status_code}")
            return False, "", []
        
        # Check if the specific model is available
        models = tags_response.json().get('models', [])
        model_names = [model['name'] for model in models]
        
        # If specified model not found, use first available or fail
        if model_name not in model_names:
            logger.warning(f"Model {model_name} not found. Available models: {model_names}")
            selected_model = model_names[0] if model_names else ""
        else:
            selected_model = model_name
        
        # Test model generation
        url = f"{ollama_base_url}/api/generate"
        response = requests.post(
            url,
            json={
                "model": selected_model,
                "prompt": "Hello, are you working?",
                "stream": False,
                "temperature": 0.1,
                "max_tokens": 10
            },
            timeout=timeout
        )
        
        if response.status_code != 200:
            logger.warning(f"Model generation failed. Status code: {response.status_code}")
            return False, selected_model, model_names
        
        # Verify response structure
        result = response.json()
        if 'response' not in result:
            logger.warning("Invalid response from Ollama. Missing 'response' key.")
            return False, selected_model, model_names
        
        logger.info(f"Successfully connected to Ollama with model {selected_model}")
        return True, selected_model, model_names
    
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Connection error to Ollama: {e}")
        return False, "", []
    
    except requests.exceptions.Timeout:
        logger.error("Timeout connecting to Ollama. Check network or service availability.")
        return False, "", []
    
    except Exception as e:
        logger.error(f"Unexpected error testing Ollama connection: {e}")
        return False, "", []


class OllamaClient:
    """
    Client for interacting with Ollama API with Instructor integration.
    Provides structured output parsing and automatic retries.
    """
    
    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model_name: str = "gemma3:1b",
        temperature: float = 0.8,
        top_p: float = 0.95,
        top_k: int = 40,
        max_tokens: int = 500,
        max_retries: int = 3,
        timeout: int = 30
    ):
        """
        Initialize the Ollama client with Instructor integration.
        
        Args:
            base_url: Base URL for Ollama API
            model_name: Name of the model to use
            temperature: Controls randomness in generation
            top_p: Nucleus sampling probability threshold
            top_k: Number of highest probability tokens to consider
            max_tokens: Maximum number of tokens to generate
            max_retries: Maximum number of retries on failure
            timeout: Request timeout in seconds
        """
        self.base_url = base_url
        self.model_name = model_name
        self.temperature = temperature
        self.top_p = top_p
        self.top_k = top_k
        self.max_tokens = max_tokens
        self.max_retries = max_retries
        self.timeout = timeout
        
        # Create a mock OpenAI-compatible client for Ollama
        self.client = self._create_ollama_client()
        
        # Patch the client with instructor for structured outputs
        self.instructor_client = instructor.from_openai(
            self.client, 
            mode=instructor.Mode.JSON_SCHEMA,
            max_retries=max_retries
        )
        
        logger.info(f"Initialized OllamaClient with model {model_name}")
    
    def _create_ollama_client(self):
        """
        Create a client that mimics the OpenAI client interface but calls Ollama.
        This allows us to use instructor with Ollama.
        """
        # Define a minimal OpenAI-compatible client for Ollama
        class OllamaCompatClient:
            def __init__(self, base_url, model, temperature, top_p, top_k, max_tokens, timeout):
                self.base_url = base_url
                self.model = model
                self.temperature = temperature
                self.top_p = top_p
                self.top_k = top_k
                self.max_tokens = max_tokens
                self.timeout = timeout
                
                # Create a ChatCompletions class to mimic OpenAI's structure
                class ChatCompletions:
                    def __init__(self, parent):
                        self.parent = parent
                    
                    def create(self, messages, model=None, temperature=None, max_tokens=None, response_model=None, **kwargs):
                        """
                        Create chat completions using Ollama.
                        This mimics OpenAI's chat completions API but calls Ollama.
                        
                        If response_model is provided, instructor will handle parsing the response.
                        """
                        # Use provided values or fall back to defaults
                        model = model or self.parent.model
                        temperature = temperature or self.parent.temperature
                        max_tokens = max_tokens or self.parent.max_tokens
                        
                        # Construct the prompt from messages
                        prompt = ""
                        for msg in messages:
                            role = msg["role"]
                            content = msg["content"]
                            if role == "system":
                                prompt += f"System: {content}\n\n"
                            elif role == "user":
                                prompt += f"User: {content}\n\n"
                            elif role == "assistant":
                                prompt += f"Assistant: {content}\n\n"
                            # Add more roles as needed
                        
                        prompt += "Assistant: "
                        
                        # If using instructor with response_model, add JSON instructions
                        if response_model:
                            prompt += "\nPlease respond with valid JSON according to the provided schema.\n"
                        
                        # Log the prompt for debugging
                        logger.debug(f"Calling Ollama with prompt: {prompt[:200]}...")
                        
                        # Call Ollama API
                        url = f"{self.parent.base_url}/api/generate"
                        start_time = time.time()
                        
                        try:
                            response = requests.post(
                                url,
                                json={
                                    "model": model,
                                    "prompt": prompt,
                                    "stream": False,
                                    "temperature": temperature,
                                    "top_p": self.parent.top_p,
                                    "top_k": self.parent.top_k,
                                    "max_tokens": max_tokens
                                },
                                timeout=self.parent.timeout
                            )
                            
                            generation_time = time.time() - start_time
                            logger.debug(f"Ollama response generated in {generation_time:.2f} seconds")
                            
                            if response.status_code != 200:
                                logger.error(f"Ollama API returned status code {response.status_code}")
                                logger.error(f"Response content: {response.text[:200]}")
                                raise Exception(f"Ollama API error: {response.status_code}")
                            
                            result = response.json()
                            response_text = result.get("response", "")
                            
                            # Additional validation
                            if not response_text:
                                logger.warning("Ollama returned an empty response")
                                raise Exception("Empty response from Ollama")
                            
                            # Create a minimal response that mimics OpenAI format
                            # This is what instructor will use to parse the response
                            return {
                                "model": model,
                                "choices": [
                                    {
                                        "message": {
                                            "role": "assistant",
                                            "content": response_text
                                        },
                                        "index": 0,
                                        "finish_reason": "stop"
                                    }
                                ]
                            }
                        
                        except Exception as e:
                            logger.error(f"Error calling Ollama: {e}")
                            raise
                
                # Add the ChatCompletions class to the client
                self.chat = ChatCompletions(self)
        
        # Instantiate and return the client
        return OllamaCompatClient(
            self.base_url,
            self.model_name,
            self.temperature,
            self.top_p,
            self.top_k,
            self.max_tokens,
            self.timeout
        )
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def generate_structured_output(self, prompt: str, response_model: Type[T], system_prompt: str = None) -> T:
        """
        Generate a structured response using the specified model.
        
        Args:
            prompt: The user prompt
            response_model: Pydantic model class for the expected response structure
            system_prompt: Optional system prompt to provide context
            
        Returns:
            An instance of the specified response_model
        """
        messages = []
        
        # Add system prompt if provided
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        # Add user prompt
        messages.append({"role": "user", "content": prompt})
        
        try:
            logger.debug(f"Generating structured output with model {self.model_name}")
            logger.debug(f"Response model: {response_model.__name__}")
            
            # Use instructor to generate and parse the response
            result = self.instructor_client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                response_model=response_model
            )
            
            logger.debug(f"Successfully generated structured output: {result.model_dump_json()[:200]}...")
            return result
        
        except Exception as e:
            logger.error(f"Error generating structured output: {e}")
            raise

    def generate_narrative(self, prompt: str, system_prompt: str = None) -> NarrativeResponse:
        """
        Generate a narrative response using the NarrativeResponse model.
        
        Args:
            prompt: The prompt describing the interaction
            system_prompt: Optional system prompt for context
            
        Returns:
            NarrativeResponse object with title, description, and tags
        """
        return self.generate_structured_output(prompt, NarrativeResponse, system_prompt)
    
    def generate_daily_summary(self, prompt: str, system_prompt: str = None) -> DailySummaryResponse:
        """
        Generate a daily summary using the DailySummaryResponse model.
        
        Args:
            prompt: The prompt describing the day's events
            system_prompt: Optional system prompt for context
            
        Returns:
            DailySummaryResponse object with the summary
        """
        return self.generate_structured_output(prompt, DailySummaryResponse, system_prompt)

def parse_llm_json_response(
    response_text: str, 
    default_title: str = "Economic Interaction", 
    default_description: str = "An economic exchange occurred between agents.",
    default_tags: List[str] = ["fallback", "error_recovery"]
) -> Tuple[str, str, List[str]]:
    """
    Parse JSON response from LLM, handling various edge cases.
    
    Args:
        response_text: Raw text response from LLM
        default_title: Fallback title if parsing fails
        default_description: Fallback description if parsing fails
        default_tags: Fallback tags if parsing fails
    
    Returns:
        Tuple of (title, description, tags)
    """
    try:
        # First, try to find JSON in the response
        start_idx = response_text.find('{')
        end_idx = response_text.rfind('}')
        
        if start_idx != -1 and end_idx != -1:
            json_text = response_text[start_idx:end_idx+1]
            
            # Try different approaches to parse JSON
            try:
                # First attempt with standard parsing
                response_data = json.loads(json_text)
            except json.JSONDecodeError:
                # Try to clean up the JSON text
                cleaned_json = json_text.replace('\n', ' ').replace('\r', ' ')
                cleaned_json = cleaned_json.replace(',}', '}').replace(',]', ']')
                
                try:
                    # Extract only the JSON-like structure
                    pattern = r'\{.*\}'
                    match = re.search(pattern, cleaned_json, re.DOTALL)
                    if match:
                        cleaned_json = match.group(0)
                    response_data = json.loads(cleaned_json)
                except Exception:
                    # Last resort fallback
                    return default_title, default_description, default_tags
            
            title = response_data.get("title", default_title)
            description = response_data.get("description", default_description)
            tags = response_data.get("tags", default_tags)
            
            return title, description, tags
        else:
            # Try to salvage something useful from the response
            lines = response_text.strip().split('\n')
            if len(lines) >= 2:
                return lines[0], '\n'.join(lines[1:]), ["generated", "non-json"]
            
            return default_title, response_text, ["fallback"]
    
    except Exception:
        return default_title, default_description, default_tags 