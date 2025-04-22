import logging
from typing import Type, TypeVar, Optional

import instructor
import requests
from instructor.exceptions import IncompleteOutputException
from openai import OpenAI
from pydantic import BaseModel, ValidationError

from src.llm_models import NarrativeResponse, DailySummaryResponse, example_daily_summary_1, example_daily_summary_2
from src.settings import DEFAULT_LM

# Create TypeVar for the response model
T = TypeVar('T', bound=BaseModel)
logger = logging.getLogger(__name__)


class OllamaClient:
    """
    Client for Ollama API with structured output support using Instructor.
    """

    def __init__(
            self,
            base_url: str = "http://localhost:11434",
            model_name: str = DEFAULT_LM,
            temperature: float = 0.8,
            top_p: float = 0.95,
            top_k: int = 40,
            max_tokens: int = 2 ** 14,
            max_retries: int = 3,
            timeout: int = 30,
            system_prompt: str = ""
    ):
        """
        Initialize the Ollama client.
        
        Args:
            base_url: Base URL for the Ollama API
            model_name: Name of the model to use
            temperature: Controls randomness in generation (0.0-1.0)
            top_p: Nucleus sampling probability threshold (0.0-1.0)
            top_k: Number of highest probability tokens to consider
            max_tokens: Maximum number of tokens to generate
            max_retries: Maximum number of retries on failure
            timeout: Request timeout in seconds
            system_prompt: Default system prompt
        """
        self.base_url = base_url
        self.model_name = model_name
        self.temperature = temperature
        self.top_p = top_p
        self.top_k = top_k
        self.max_tokens = max_tokens
        self.max_retries = max_retries
        self.timeout = timeout
        self.system_prompt = system_prompt
        self.logger = logging.getLogger(__name__)
        self.client = instructor.from_openai(
            OpenAI(
                base_url=f"{base_url}/v1",
                api_key="required_but_unused",
            ),
            mode=instructor.Mode.MD_JSON,
        )

        # Check connection to Ollama
        self.is_connected = self._check_connection()

    def _check_connection(self) -> bool:
        """Check if we can connect to Ollama"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception as e:
            self.logger.warning(f"Failed to connect to Ollama: {e}")
            return False

    # def _retry_with_backoff(self, func, *args, **kwargs):
    #     """Helper method to retry API calls with a simple retry mechanism"""
    #     retries = self.max_retries
    #     last_exception = None

    #     while retries > 0:
    #         try:
    #             return func(*args, **kwargs)
    #         except Exception as e:
    #             last_exception = e
    #             self.logger.warning(f"API call failed, {retries} retries left: {e}")
    #             retries -= 1
    #             if retries > 0:
    #                 time.sleep(2)  # Simple fixed delay

    #     # If we've exhausted retries, raise the last exception
    #     raise last_exception if last_exception else Exception("API call failed after retries")

    def generate_structured(
            self,
            prompt: str,
            response_model: Type[T],
            examples: Optional[list[T]] = None,
            system_prompt: Optional[str] = None,
            temperature: Optional[float] = None,
            max_tokens: Optional[int] = None,
            max_retries: Optional[int] = None
    ) -> T:
        """
        Generate structured output from Ollama using Instructor.
        
        Args:
            prompt: The user prompt
            response_model: Pydantic model for structured response
            examples: Examples of response to give to the LLM
            system_prompt: Optional system prompt override
            temperature: Optional temperature override
            max_tokens: Optional max tokens override
            max_retries: Optional max retries override
            
        Returns:
            An instance of the response_model
        """
        try:
            # Use defaults if parameters not provided
            system = system_prompt if system_prompt is not None else self.system_prompt
            temp = temperature if temperature is not None else self.temperature
            tokens = max_tokens if max_tokens is not None else self.max_tokens
            retries = max_retries if max_retries is not None else self.max_retries

            # Prepare messages
            messages = []
            if system:
                messages.append({"role": "system", "content": system})

            if examples:
                examples_str = "Examples: " + ",".join([e.model_dump_json() for e in examples])
            else:
                examples_str = ""

            format_guidance = f"""Your response must be only valid JSON conforming to this response schema: 
            {response_model.model_json_schema()}
            {examples_str}
            
            IMPORTANT: Make sure all fields have the correct type according to the schema.
            """

            messages.append({"role": "system", "content": format_guidance})
            messages.append({"role": "user", "content": prompt})

            from instructor.exceptions import InstructorRetryException

            try:
                # Use Instructor's create method with structured response and retry mechanism
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    response_model=response_model,
                    temperature=temp,
                    max_tokens=tokens,
                    max_retries=self.max_retries
                )

                logger.debug(f"generate_structured({response_model.__name__}): {response}")
                return response
            except ValidationError as validation_error:
                logger.error(f"ValidationError: {validation_error.errors()}")
                raise

        except InstructorRetryException as e:
                self.logger.error(f"Retry failed after {e.n_attempts} attempts")
                self.logger.error(f"Last completion: {e.last_completion}")
                raise

        except IncompleteOutputException as e:
            self.logger.error(f"Failed to generate structured output: {e}")
            self.logger.error(f"Last output: {e}")

            raise
        except Exception as e:
            self.logger.error(f"Error in generate_structured: {e}")
            raise

    def generate_narrative(
            self,
            prompt: str,
            system_prompt: str
    ) -> NarrativeResponse:
        """
        Generate a narrative response for an interaction.
        
        Args:
            prompt: The prompt for narrative generation
            system_prompt: System prompt for the model
            
        Returns:
            A NarrativeResponse object
        """
        return self.generate_structured(
            prompt=prompt,
            response_model=NarrativeResponse,
            system_prompt=system_prompt
        )

    def generate_daily_summary(
            self,
            prompt: str,
            system_prompt: str
    ) -> DailySummaryResponse:
        """
        Generate a daily summary response.
        
        Args:
            prompt: The prompt for summary generation
            system_prompt: System prompt for the model
            
        Returns:
            A DailySummaryResponse object
        """
        try:
            return self.generate_structured(
                prompt=prompt,
                response_model=DailySummaryResponse,
                examples=[example_daily_summary_1, example_daily_summary_2],
                system_prompt=system_prompt
            )
        except Exception as e:
            self.logger.error(f"Error generating daily summary: {e}")
            raise

    def generate_text(
            self,
            prompt: str,
            system_prompt: Optional[str] = None
    ) -> str:
        """
        Generate simple text output (fallback method).
        
        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt
            
        Returns:
            Generated text as string
        """
        try:
            # Use default system prompt if none provided
            system = system_prompt if system_prompt is not None else self.system_prompt

            # Prepare messages
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})

            # Define the function to call
            def _generate():
                # Use Instructor's create method
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    response_model=None,  # No structured model for plain text
                    temperature=self.temperature,
                    max_tokens=self.max_tokens
                )
                return response.choices[0].message.content or ""

            # Use retry mechanism
            return self._retry_with_backoff(_generate)

        except Exception as e:
            self.logger.error(f"Error generating text: {e}")
            return f"Error generating text: {str(e)}"
