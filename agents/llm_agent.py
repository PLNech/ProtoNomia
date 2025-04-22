"""
LLM-based agent implementation for ProtoNomia.
This module handles the integration with language models for agent decision making.
"""
import logging
import time

from llm_models import AgentActionResponse
from llm_utils import OllamaClient
from models.base import Agent, ActionType, OfferAction, NegotiateAction, AcceptRejectAction, WorkAction, BuyAction, \
    AgentDecisionContext, AgentAction
from settings import DEFAULT_LM

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

    def generate_action(self, agent: Agent, context: AgentDecisionContext) -> AgentAction:
        """
        Generate an action for the agent using the LLM.
        
        Args:
            agent: The agent to generate an action for
            context: Decision context for the agent
            
        Returns:
            AgentAction: The generated action
        """
        # Format prompt
        prompt = format_prompt(agent, context)
        system_prompt = (
            "You are an AI assistant helping Mars colonists make economic decisions. "
            "Based on the agent's personality and context, choose the most appropriate action. "
            "Your response must be valid JSON with a 'type' field for the action type and an 'extra' field "
            "containing any additional information needed for the action. "
            "For example: {\"type\": \"BUY\", \"extra\": {\"desired_item\": \"Food Pack\"}} "
            "or {\"type\": \"SEARCH_JOB\", \"extra\": {\"reason\": \"I need a reliable income source\"}}. "
            "The 'reason' or 'explanation' field in 'extra' is very helpful."
        )

        try:
            # Get structured response using Ollama
            action_response = self.ollama_client.generate_structured(
                prompt=prompt,
                response_model=AgentActionResponse,
                system_prompt=system_prompt
            )

            # Convert the structured response to an AgentAction
            action_type_str = action_response.type

            # Validate the action type
            try:
                action_type = ActionType(action_type_str)
            except ValueError:
                logger.warning(f"Invalid action type '{action_type_str}', defaulting to REST")
                action_type = ActionType.REST

            # Create the agent action with the processed data
            action = AgentAction(
                type=action_type,
                agent_id=agent.id,
                turn=context.turn,
                timestamp=time.time(),
                extra=action_response.extra or {}
            )

            # Fill in action-specific details based on type
            self._fill_action_details(action)

            logger.debug(f"Generated action for agent {agent.id}: {action.type}")
            logger.debug(f"Reasoning: {action_response.reasoning}")

            return action

        except Exception as e:
            logger.error(f"Error generating action: {e}")
            
            # Attempt to extract useful information even from invalid responses
            try:
                # If we can extract some kind of type information, use it instead of defaulting to REST
                if "last_completion" in str(e) and "content" in str(e):
                    import re
                    import json
                    
                    # Extract the JSON content from the error message
                    match = re.search(r'content=\'(.*?)\'', str(e))
                    if match:
                        content = match.group(1)
                        try:
                            # Try to parse it as JSON
                            data = json.loads(content)
                            if "type" in data and data["type"] in [t.value for t in ActionType]:
                                # We have a valid action type, create action with it
                                return AgentAction(
                                    type=ActionType(data["type"]),
                                    agent_id=agent.id,
                                    turn=context.turn,
                                    timestamp=time.time(),
                                    extra=data.get("extra", {})
                                )
                        except:
                            pass
                
            except Exception as inner_e:
                logger.debug(f"Failed to extract data from error: {inner_e}")
            
            # Fall back to a REST action on failure
            return AgentAction(
                type=ActionType.REST,
                agent_id=agent.id,
                turn=context.turn,
                timestamp=time.time(),
                extra={"reason": f"Error in LLM processing, defaulting to REST: {str(e)[:100]}"}
            )

    def _fill_action_details(self, action: AgentAction) -> None:
        """
        Fill in the action-specific details based on the action type.
        
        Args:
            action: The agent action to fill in details for
        """
        try:
            extra = action.extra or {}

            if action.type == ActionType.OFFER:
                action.offer_details = OfferAction(
                    what=extra.get("what", ""),
                    against_what=extra.get("against_what", ""),
                    to_agent_id=extra.get("to_agent_id")
                )
            elif action.type == ActionType.NEGOTIATE:
                action.negotiate_details = NegotiateAction(
                    offer_id=extra.get("offer_id", ""),
                    message=extra.get("message", "")
                )
            elif action.type in [ActionType.ACCEPT, ActionType.REJECT]:
                action.accept_reject_details = AcceptRejectAction(
                    offer_id=extra.get("offer_id", "")
                )
            elif action.type == ActionType.WORK:
                action.work_details = WorkAction(
                    job_id=extra.get("job_id", "")
                )
            elif action.type == ActionType.BUY:
                action.buy_details = BuyAction(
                    desired_item=extra.get("desired_item", "")
                )
        except Exception as e:
            logger.error(f"Error filling action details: {e}")


def format_prompt(agent: Agent, context: AgentDecisionContext) -> str:
    """
    Format the prompt for agent decision making.
    
    Args:
        agent: The agent making the decision
        context: The decision context
        
    Returns:
        str: Formatted prompt for the LLM
    """
    # Format basic agent information
    prompt = (
        f"You are an agent in a simulated economy on Mars in the year 2993.\n\n"
        f"### YOUR PROFILE\n"
        f"- Name: {agent.name}\n"
        f"- Age: {agent.age_days} years\n"
        f"- Type: {agent.agent_type.value}\n"
        f"- Faction: {agent.faction.value if agent.faction else 'None'}\n"
    )

    # Add personality traits if available
    if hasattr(agent, 'personality') and agent.personality:
        prompt += "- Personality traits:\n"
        for trait_name in [
            'cooperativeness', 'risk_tolerance', 'fairness_preference',
            'altruism', 'rationality', 'long_term_orientation'
        ]:
            trait_value = getattr(agent.personality, trait_name, None)
            if trait_value is not None:
                prompt += f"  - {trait_name}: {trait_value:.2f}\n"

    # Add resource information
    prompt += "\n### YOUR RESOURCES\n"
    if hasattr(agent, 'resources') and agent.resources:
        for resource in agent.resources:
            prompt += f"- {resource.resource_type}: {resource.amount}\n"
    else:
        prompt += "- No resources\n"

    # Add job information
    prompt += f"\n- Current job: {agent.job if hasattr(agent, 'job') and agent.job else 'None'}\n"

    # Add needs information (rest, hunger, etc.)
    prompt += "\n### YOUR NEEDS: {agent.needs}\n"

    # Add social context
    prompt += "\n### SOCIAL CONTEXT\n"
    if context.neighbors:
        prompt += f"- Your neighbors: {', '.join(neighbor for neighbor in context.neighbors)}\n"
    else:
        prompt += "- You have no neighbors nearby\n"

    # Add pending offers
    if context.pending_offers:
        prompt += "\n### PENDING OFFERS\n"
        for i, offer in enumerate(context.pending_offers):
            prompt += (
                f"- Offer {i + 1} (ID: {offer['id']}):\n"
                f"  - From: {offer['from_agent']}\n"
                f"  - What: {offer['what']}\n"
                f"  - Against what: {offer['against_what']}\n"
                f"  - Status: {offer['status']}\n"
            )

    # Add available jobs
    if context.jobs_available:
        prompt += "\n### AVAILABLE JOBS\n"
        for i, job in enumerate(context.jobs_available):
            prompt += (
                f"- Job {i + 1} (ID: {job['id']}):\n"
                f"  - Title: {job['title']}\n"
                f"  - Salary: {job['salary']}\n"
                f"  - Duration: {job['duration']}\n"
            )

    # Add items for sale
    if context.items_for_sale:
        prompt += "\n### ITEMS FOR SALE\n"
        for i, item in enumerate(context.items_for_sale):
            prompt += (
                f"- Item {i + 1} (ID: {item['id']}):\n"
                f"  - Name: {item['name']}\n"
                f"  - Price: {item['price']}\n"
                f"  - Seller: {item['seller']}\n"
            )

    # Add turn information
    prompt += f"\n### TURN INFORMATION\n"
    prompt += f"- Current turn: {context.turn}/{context.max_turns}\n"

    # Add available actions
    prompt += (
        f"\n### AVAILABLE ACTIONS\n"
        f"- REST: recover energy\n"
        f"- OFFER(what:str, against_what:str, to_agent_id:str): make an offer to another agent\n"
        f"- NEGOTIATE(offer_id:str, message:str): negotiate an offer\n"
        f"- ACCEPT(offer_id:str): accept an offer\n"
        f"- REJECT(offer_id:str): reject an offer\n"
        f"- SEARCH_JOB(): look for a job\n"
        f"- WORK(job_id:str): work at a job\n"
        f"- BUY(desired_item:str): buy an item\n"
    )

    # Add request for action
    prompt += (
        f"\n### TASK\n"
        f"Based on your profile, resources, needs, and available actions, decide what to do next.\n"
        f"Think step by step about what would be the most beneficial course of action considering your personality traits and current situation.\n"
        f"Return your choice in this format:\n\n"
        f"Reasoning: <briefly explain your reasoning>\nCHOICE: {{'type': '<ACTION_TYPE>', 'extra': {{<additional parameters needed for the action>}}}}\n"
    )

    # Add examples
    prompt += (
        f"\n### EXAMPLES\n"
        f"Example 1:\nReasoning: I'm low on energy and need to recover.\nCHOICE: {{'type': 'REST', 'extra': {{'reason': 'need to recover energy'}}}}\n\n"
        f"Example 2:\nReasoning: I want to make a trade with agent12.\nCHOICE: {{'type': 'OFFER', 'extra': {{'what': '10 credits', 'against_what': '5 food', 'to_agent_id': 'agent12'}}}}\n\n"
        f"Example 3:\nReasoning: I need money so I'll look for a job.\nCHOICE: {{'type': 'SEARCH_JOB', 'extra': {{'reason': 'need income'}}}}\n\n"
        f"Example 4:\nReasoning: The offer from agent5 seems fair.\nCHOICE: {{'type': 'ACCEPT', 'extra': {{'offer_id': 'offer123'}}}}\n"
    )

    return prompt
