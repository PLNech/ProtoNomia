"""
Utility functions for LLM interactions in ProtoNomia.
Provides common functionality for Ollama API calls and connection testing.
"""
import json
import logging
import re
import time
import requests
from typing import Dict, List, Optional, Tuple, Any

# Initialize logger
logger = logging.getLogger(__name__)

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

def call_ollama(
    ollama_base_url: str, 
    model_name: str, 
    prompt: str, 
    temperature: float = 0.8, 
    top_p: float = 0.95, 
    top_k: int = 40, 
    max_tokens: int = 500,
    timeout: int = 30
) -> str:
    """
    Call Ollama API to generate text.
    
    Args:
        ollama_base_url: Base URL for Ollama API
        model_name: Name of the model to use
        prompt: Input prompt for text generation
        temperature: Controls randomness in generation
        top_p: Nucleus sampling probability threshold
        top_k: Number of highest probability tokens to consider
        max_tokens: Maximum number of tokens to generate
        timeout: Request timeout in seconds
    
    Returns:
        Generated text response
    """
    try:
        url = f"{ollama_base_url}/api/generate"
        start_time = time.time()
        
        logger.debug(f"Calling Ollama API with model {model_name}")
        logger.debug(f"Prompt starts with: {prompt[:100]}...")
        
        request_data = {
            "model": model_name,
            "prompt": prompt,
            "stream": False,
            "temperature": temperature,
            "top_p": top_p,
            "top_k": top_k,
            "max_tokens": max_tokens
        }
        
        logger.debug(f"Request parameters: temp={temperature}, top_p={top_p}, top_k={top_k}")
        
        try:
            response = requests.post(
                url,
                json=request_data,
                timeout=timeout
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