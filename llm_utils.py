"""
Utility functions for LLM interactions in ProtoNomia.

This module provides reusable functions for working with LLM APIs, 
particularly focusing on connecting to and using the Ollama API.
"""
import json
import logging
import time
from typing import Any, Dict, List, Optional, Type, Union
import requests
from pydantic import BaseModel

import instructor

logger = logging.getLogger(__name__)

def test_ollama_connection(ollama_base_url: str, model_name: str, timeout: int = 5) -> tuple:
    """
    Test connection to Ollama API and check if the specified model is available.
    
    Args:
        ollama_base_url: Base URL for the Ollama API
        model_name: Name of the model to check
        timeout: Connection timeout in seconds
        
    Returns:
        Tuple containing (success, selected_model, info) where:
        - success: Boolean indicating if connection is successful and model is available
        - selected_model: The model name that was successfully connected to
        - info: Additional information about the connection
    """
    try:
        # Check if Ollama is running and we can connect
        response = requests.get(f"{ollama_base_url}/api/tags", timeout=timeout)
        response.raise_for_status()
        
        # Parse the response to get available models
        data = response.json()
        models = [model['name'] for model in data.get('models', [])]
        
        # Check if our model is in the list
        if model_name not in models:
            logger.warning(f"Model {model_name} not found in available models: {models}")
            return False, "", {"available_models": models}
            
        logger.info(f"Successfully connected to Ollama with model {model_name}")
        return True, model_name, {"available_models": models}
        
    except requests.ConnectionError:
        logger.error(f"Connection error: Could not connect to Ollama at {ollama_base_url}")
        return False, "", {"error": "connection_error"}
    except requests.Timeout:
        logger.error(f"Timeout error: Connection to {ollama_base_url} timed out after {timeout} seconds")
        return False, "", {"error": "timeout"}
    except requests.HTTPError as e:
        logger.error(f"HTTP error: {e}")
        return False, "", {"error": f"http_error: {e}"}
    except Exception as e:
        logger.error(f"Unexpected error checking Ollama connection: {e}")
        return False, "", {"error": f"unexpected_error: {e}"}


class OllamaClient:
    """
    Client for interacting with Ollama API with support for structured outputs via Instructor.
    
    This client handles:
    - Connection to the Ollama API
    - Regular (unstructured) text generation
    - Structured output generation using Pydantic models
    - Retries with exponential backoff
    """
    
    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model_name: str = "llama2",
        temperature: float = 0.7,
        top_p: float = 0.95,
        top_k: int = 40,
        max_tokens: int = 1024,
        max_retries: int = 3,
        timeout: int = 30,
        system_prompt: Optional[str] = None
    ):
        """
        Initialize the Ollama client.
        
        Args:
            base_url: Base URL for the Ollama API
            model_name: Name of the Ollama model to use
            temperature: Sampling temperature (higher = more creative)
            top_p: Nucleus sampling probability threshold
            top_k: Number of highest probability tokens to consider
            max_tokens: Maximum number of tokens to generate
            max_retries: Maximum number of retries on failure
            timeout: Request timeout in seconds
            system_prompt: Default system prompt to use for all requests
        """
        self.base_url = base_url
        self.model = model_name
        self.temperature = temperature
        self.top_p = top_p
        self.top_k = top_k
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.max_retries = max_retries
        self.system_prompt = system_prompt
        
        # Create an instructor client for structured outputs
        # Note: We'll use direct requests instead of instructor for now
        # to avoid compatibility issues
        self.instructor_available = False
        try:
            import instructor
            self.instructor_available = True
        except ImportError:
            logger.warning("Instructor package not available. Structured output will be limited.")
        
        # Test connection on initialization
        self.is_connected, self.selected_model, self.info = test_ollama_connection(base_url, model_name, timeout=5)
        if not self.is_connected:
            logger.warning(f"Failed to connect to Ollama at {base_url} with model {model_name}")
    
    def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Generate unstructured text from the Ollama model.
        
        Args:
            prompt: The user prompt to send to the model
            system_prompt: Optional system prompt that overrides the default
            temperature: Sampling temperature (higher = more creative, lower = more deterministic)
            max_tokens: Maximum number of tokens to generate
            
        Returns:
            Generated text as a string
            
        Raises:
            ConnectionError: If connection to Ollama fails
            TimeoutError: If request times out
            ValueError: For other API errors
        """
        if not self.is_connected:
            raise ConnectionError(f"Not connected to Ollama at {self.base_url}")
        
        # Use instance system prompt if none provided
        system = system_prompt if system_prompt is not None else self.system_prompt
        
        # Use instance defaults for other parameters if none provided
        temp = temperature if temperature is not None else self.temperature
        tokens = max_tokens if max_tokens is not None else self.max_tokens
        
        # Prepare request
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "temperature": temp,
            "max_tokens": tokens,
            "top_p": self.top_p,
            "top_k": self.top_k
        }
        
        # Add system prompt if available
        if system:
            payload["system"] = system
            
        # Attempt with retries
        for attempt in range(self.max_retries):
            try:
                response = requests.post(url, json=payload, timeout=self.timeout)
                response.raise_for_status()
                
                # Extract and return generated text
                data = response.json()
                return data.get("response", "")
                
            except (requests.RequestException, json.JSONDecodeError) as e:
                logger.warning(f"Attempt {attempt+1}/{self.max_retries} failed: {str(e)}")
                
                if attempt < self.max_retries - 1:
                    # Exponential backoff
                    wait_time = 2 ** attempt
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"All {self.max_retries} attempts failed")
                    raise ValueError(f"Failed to generate text after {self.max_retries} attempts: {str(e)}")
        
        # This should not be reached due to the exception in the loop
        raise RuntimeError("Unexpected error in generate_text")
    
    def generate_structured(
        self,
        prompt: str,
        response_model: Type[BaseModel],
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        validation_context: Optional[Dict[str, Any]] = None
    ) -> BaseModel:
        """
        Generate structured output from the Ollama model using Instructor.
        
        Args:
            prompt: The user prompt to send to the model
            response_model: Pydantic model class defining the expected response structure
            system_prompt: Optional system prompt that overrides the default
            temperature: Optional temperature that overrides the default
            max_tokens: Optional max tokens that overrides the default
            validation_context: Optional context data for model validation
            
        Returns:
            Instance of the provided response_model with structured data
            
        Raises:
            ConnectionError: If connection to Ollama fails
            TimeoutError: If request times out
            ValueError: For other API errors or if structured output generation fails
        """
        if not self.is_connected:
            raise ConnectionError(f"Not connected to Ollama at {self.base_url}")
        
        # Use instance defaults if none provided
        system = system_prompt if system_prompt is not None else self.system_prompt
        temp = temperature if temperature is not None else self.temperature
        tokens = max_tokens if max_tokens is not None else self.max_tokens
        
        # Attempt with retries
        for attempt in range(self.max_retries):
            try:
                if self.instructor_available:
                    # Use instructor for structured output if available
                    try:
                        # Build messages list for instructor
                        messages = []
                        if system:
                            messages.append({"role": "system", "content": system})
                        messages.append({"role": "user", "content": prompt})
                        
                        # Use instructor to patch the requests library and create a client
                        import instructor
                        import json
                        import requests
                        
                        # Enhanced prompt to encourage structured output
                        formatted_prompt = f"{prompt}\n\nPlease respond in JSON format that matches the following structure:\n{response_model.model_json_schema()}"
                        
                        # Make the request to Ollama
                        url = f"{self.base_url}/api/chat"
                        payload = {
                            "model": self.model,
                            "messages": messages,
                            "temperature": temp,
                            "max_tokens": tokens,
                            "top_p": self.top_p,
                            "top_k": self.top_k,
                            "format": "json"  # Request JSON format explicitly
                        }
                        
                        response = requests.post(url, json=payload, timeout=self.timeout)
                        response.raise_for_status()
                        
                        # Extract generated text
                        data = response.json()
                        result_text = data.get("message", {}).get("content", "")
                        
                        # Parse the JSON response
                        try:
                            # Try to parse the JSON
                            json_start = result_text.find('{')
                            json_end = result_text.rfind('}') + 1
                            if json_start >= 0 and json_end > json_start:
                                json_text = result_text[json_start:json_end]
                                # Parse and validate with Pydantic
                                parsed_data = json.loads(json_text)
                                return response_model.model_validate(parsed_data, context=validation_context)
                            else:
                                raise ValueError(f"No valid JSON found in response: {result_text}")
                        except (json.JSONDecodeError, ValueError) as e:
                            logger.warning(f"Failed to parse JSON response: {e}")
                            logger.debug(f"Response content: {result_text}")
                            raise ValueError(f"Invalid JSON response: {e}")
                    except Exception as e:
                        logger.warning(f"Instructor error: {e}")
                        # Fall back to manual JSON parsing
                        raise e
                else:
                    # Without instructor, we'll parse JSON manually
                    # Build messages list
                    messages = []
                    if system:
                        messages.append({"role": "system", "content": system})
                    messages.append({"role": "user", "content": prompt})
                    
                    # Make request directly
                    url = f"{self.base_url}/api/chat"
                    payload = {
                        "model": self.model,
                        "messages": messages,
                        "temperature": temp,
                        "max_tokens": tokens,
                        "top_p": self.top_p,
                        "top_k": self.top_k,
                        "format": "json"  # Request JSON format explicitly
                    }
                    
                    response = requests.post(url, json=payload, timeout=self.timeout)
                    response.raise_for_status()
                    
                    # Extract generated text
                    data = response.json()
                    result_text = data.get("message", {}).get("content", "")
                    
                    # Parse the JSON response
                    try:
                        # Try to parse the JSON
                        json_start = result_text.find('{')
                        json_end = result_text.rfind('}') + 1
                        if json_start >= 0 and json_end > json_start:
                            json_text = result_text[json_start:json_end]
                            # Parse and validate with Pydantic
                            parsed_data = json.loads(json_text)
                            return response_model.model_validate(parsed_data, context=validation_context)
                        else:
                            raise ValueError(f"No valid JSON found in response: {result_text}")
                    except (json.JSONDecodeError, ValueError) as e:
                        logger.warning(f"Failed to parse JSON response: {e}")
                        logger.debug(f"Response content: {result_text}")
                        raise ValueError(f"Invalid JSON response: {e}")
                
            except Exception as e:
                logger.warning(f"Attempt {attempt+1}/{self.max_retries} failed: {str(e)}")
                
                if attempt < self.max_retries - 1:
                    # Exponential backoff
                    wait_time = 2 ** attempt
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"All {self.max_retries} attempts failed")
                    raise ValueError(f"Failed to generate structured output after {self.max_retries} attempts: {str(e)}")
        
        # This should not be reached due to the exception in the loop
        raise RuntimeError("Unexpected error in generate_structured")
    
    def generate_narrative(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> 'NarrativeResponse':
        """
        Generate a narrative with title, description, and tags using the Ollama model.
        
        Args:
            prompt: The prompt describing the narrative to generate
            system_prompt: Optional system prompt that overrides the default
            temperature: Optional temperature that overrides the default
            max_tokens: Optional max tokens that overrides the default
            
        Returns:
            NarrativeResponse with validated title, description, and tags
            
        Raises:
            ValueError: If narrative generation fails or validation fails
        """
        from llm_models import NarrativeResponse
        
        if system_prompt is None:
            default_narrative_prompt = (
                "You are a creative narrator for a Mars colony simulation. "
                "Generate engaging narratives about economic interactions between colonists "
                "with a title, detailed description, and relevant tags."
            )
            system_prompt = default_narrative_prompt
        
        enhanced_prompt = (
            f"{prompt}\n\n"
            "Respond with a structured JSON object containing:\n"
            "1. title: A catchy, attention-grabbing title that summarizes the event\n"
            "2. description: A detailed, vivid description of what happened\n"
            "3. tags: A list of relevant keywords (3-5 tags recommended)\n\n"
            "Make sure your narrative is creative, engaging, and appropriate for the Mars colony setting."
        )
        
        # Use the unified structured output generation
        return self.generate_structured(
            prompt=enhanced_prompt,
            response_model=NarrativeResponse,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens
        )
    
    def generate_daily_summary(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> 'DailySummaryResponse':
        """
        Generate a daily summary for the Mars colony using the Ollama model.
        
        Args:
            prompt: The prompt containing information about the day's events
            system_prompt: Optional system prompt that overrides the default
            temperature: Optional temperature that overrides the default
            max_tokens: Optional max tokens that overrides the default
            
        Returns:
            DailySummaryResponse with a validated summary in Markdown format
            
        Raises:
            ValueError: If summary generation fails or validation fails
        """
        from llm_models import DailySummaryResponse
        
        if system_prompt is None:
            default_summary_prompt = (
                "You are a creative science fiction narrator summarizing "
                "daily events on a Mars colony. Create engaging, well-structured "
                "summaries that highlight the most significant events and their impact."
            )
            system_prompt = default_summary_prompt
        
        enhanced_prompt = (
            f"{prompt}\n\n"
            "Respond with a well-structured Markdown summary that includes:\n"
            "1. A day title with heading\n"
            "2. An introduction paragraph about the general state of the colony\n"
            "3. Section headings for notable events with descriptions\n"
            "4. A conclusion reflecting on the day's significance\n\n"
            "Make sure your summary is engaging, consistent with science fiction themes, "
            "and formatted properly with Markdown syntax."
        )
        
        # Use the unified structured output generation
        return self.generate_structured(
            prompt=enhanced_prompt,
            response_model=DailySummaryResponse,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens if max_tokens else 2000  # Daily summaries might need more tokens
        )
    
    def generate_structured_output(
        self,
        prompt: str,
        response_model: Type[BaseModel],
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> BaseModel:
        """
        Alias for generate_structured to maintain backward compatibility.
        
        This method exists to avoid breaking existing code that may call 
        generate_structured_output instead of generate_structured.
        """
        return self.generate_structured(
            prompt=prompt,
            response_model=response_model,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens
        )
    
    def is_connected_to_ollama(self) -> bool:
        """
        Check if the client is connected to Ollama.
        
        Returns:
            True if connected, False otherwise
        """
        return self.is_connected