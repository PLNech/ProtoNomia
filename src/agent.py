"""
LLM-based agent implementation for ProtoNomia.
This module handles the integration with language models for agent decision making.
"""
import logging
import time

from llm_utils import OllamaClient
from models import Agent, ActionType
from settings import DEFAULT_LM
from src.models import AgentActionResponse

# Initialize logger
logger = logging.getLogger(__name__)


class LLMAgent:
    """
    LLM-based agent implementation for ProtoNomia.
    Uses Ollama with structured outputs to generate agent decisions.
    """

    def __init__(
            self,
            model_name: str = DEFAULT_LM,
            temperature: float = 0.7,
            top_p: float = 0.9,
            top_k: int = 40,
            max_tokens: int = 2048,
            max_retries: int = 3,
            timeout: int = 20
    ):
        """
        Initialize the LLM agent.

        Args:
            model_name: Name of the Ollama model to use
            temperature: Controls randomness in generation
            top_p: Nucleus sampling probability threshold
            top_k: Number of highest probability tokens to consider
            max_tokens: Maximum number of tokens to generate
            max_retries: Maximum number of retries on failure
            timeout: Request timeout in seconds
        """
        self.model_name = model_name
        self.temperature = temperature
        self.top_p = top_p
        self.top_k = top_k
        self.max_tokens = max_tokens
        self.max_retries = max_retries
        self.timeout = timeout

        # Create the OllamaClient for structured output generation
        self.ollama_client = OllamaClient(
            base_url="http://localhost:11434",
            model_name=model_name,
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
            max_tokens=max_tokens,
            max_retries=max_retries,
            timeout=timeout
        )
        logger.info(f"Successfully initialized LLMAgent with model {model_name}")

    def generate_action(self, agent: Agent, context: str) -> AgentActionResponse:
        """
        Generate an action for the agent using the LLM.

        Args:
            agent: The agent to generate an action for
            context: Decision context for the agent

        Returns:
            AgentAction: The generated action usable by the Simulation.
        """
        # Format prompt
        prompt = format_prompt(agent, context)
        system_prompt = (
            "You are an AI assistant helping Mars colonists make economic decisions. "
            "Based on the agent's personality and context, choose the most appropriate action. "
            "Your response must be valid JSON with a 'type' field for the action type and an 'extra' field "
            "containing any additional information needed for the action. "
            "For example: TODO ADD EXAMPLE"
        )
        # TODO USE self.ollama_client.generate_structured(
        #         prompt=prompt,
        #         response_model=AgentActionResponse,
        #         system_prompt=system_prompt
        #     )
        # return action
        raise NotImplementedError("FIXME")

def format_prompt(agent: Agent, context: str) -> str:
    """
    Format the prompt for agent decision making.

    Args:
        agent: The agent making the decision.
        context: The decision context.

    Returns:
        str: Formatted prompt for the LLM that includes all useful info from the situation and agent
        for a LLM to then take a logical decision as this agent.
    """
    prompt = ""
    # TODO Format basic agent information
    # TODO Add info about current needs
    # TODO Add current resources information
    # TODO Add info from context
    # TODO Add info of available actions
    # TODO Add request for action e.g.
    # prompt += (
    #     f"\n### TASK\n"
    #     f"Based on your profile, resources, needs, and available actions, decide what to do next.\n"
    #     f"Think step by step about what would be the most beneficial course of action considering your personality traits and current situation.\n"
    #     f"Return your choice in this format:\n\n"
    # )
    # Add examples
    # prompt += (
    #     f"\n### EXAMPLES\n"
    # )
    #
    return prompt
