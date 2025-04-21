"""
LLM-based agent implementation for ProtoNomia.
This module handles the integration with language models for agent decision making.
"""
import json
import logging
import random
import time
from typing import Dict, Optional

from models.base import Agent
from models.actions import (
    ActionType, AgentAction, AgentDecisionContext, 
    OfferAction, NegotiateAction, AcceptRejectAction, WorkAction, BuyAction
)
from llm_utils import OllamaClient
from llm_models import AgentActionResponse

# Initialize logger
logger = logging.getLogger(__name__)


class LLMAgent:
    """
    LLM-based agent implementation for ProtoNomia.
    Uses Ollama with structured outputs to generate agent decisions.
    """
    
    def __init__(
        self, 
        model_name: str = "gemma3:1b", 
        mock: bool = False,
        temperature: float = 0.7,
        top_p: float = 0.9,
        top_k: int = 40,
        max_tokens: int = 300,
        max_retries: int = 3,
        timeout: int = 20
    ):
        """
        Initialize the LLM agent.
        
        Args:
            model_name: Name of the Ollama model to use
            mock: Whether to mock LLM responses
            temperature: Controls randomness in generation
            top_p: Nucleus sampling probability threshold
            top_k: Number of highest probability tokens to consider
            max_tokens: Maximum number of tokens to generate
            max_retries: Maximum number of retries on failure
            timeout: Request timeout in seconds
        """
        self.model_name = model_name
        self.mock = mock
        self.temperature = temperature
        self.top_p = top_p
        self.top_k = top_k
        self.max_tokens = max_tokens
        self.max_retries = max_retries
        self.timeout = timeout
        
        # Create the OllamaClient for structured output generation
        if not self.mock:
            try:
                # Use the OllamaClient that handles all the patching
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
            except Exception as e:
                logger.warning(f"Failed to connect to Ollama: {e}. Falling back to mock mode.")
                self.mock = True
    
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
            "Always respond with a valid action type and necessary details in JSON format."
        )
        
        try:
            # Get structured response
            if self.mock:
                action_response = self._mock_agent_action(agent, context)
            else:
                try:
                    action_response = self.ollama_client.generate_structured_output(
                        prompt=prompt,
                        response_model=AgentActionResponse,
                        system_prompt=system_prompt
                    )
                except Exception as e:
                    logger.error(f"Error generating action with OllamaClient: {e}")
                    # Fall back to mock response if LLM fails
                    logger.warning("Falling back to mock agent action generation")
                    action_response = self._mock_agent_action(agent, context)
            
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
            if action_response.reasoning:
                logger.debug(f"Reasoning: {action_response.reasoning}")
                
            return action
            
        except Exception as e:
            logger.error(f"Error generating action: {e}")
            # Fall back to a REST action on failure
            return AgentAction(
                type=ActionType.REST,
                agent_id=agent.id,
                turn=context.turn,
                timestamp=time.time(),
                extra={"reason": "Error in LLM processing, defaulting to REST"}
            )
    
    def _mock_agent_action(self, agent: Agent, context: AgentDecisionContext) -> AgentActionResponse:
        """
        Generate a mock agent action for testing or fallback.
        
        Args:
            agent: The agent to generate a response for
            context: Decision context for the agent
            
        Returns:
            AgentActionResponse: A structured mock response
        """
        # For mocking, we'll generate a response based on personality and context
        action_type = random.choice(list(ActionType))
        
        # Bias toward certain actions based on personality
        if hasattr(agent, 'personality') and agent.personality:
            if agent.personality.cooperativeness > 0.7:
                # Cooperative agents more likely to OFFER or ACCEPT
                action_type = random.choice([ActionType.OFFER, ActionType.ACCEPT, ActionType.WORK])
            elif agent.personality.risk_tolerance > 0.7:
                # Risk-tolerant agents more likely to BUY or SEARCH_JOB
                action_type = random.choice([ActionType.BUY, ActionType.SEARCH_JOB])
            elif agent.personality.fairness_preference > 0.7:
                # Fair agents more likely to NEGOTIATE
                action_type = random.choice([ActionType.NEGOTIATE, ActionType.OFFER])
        
        # Generate extra data for action
        extra = {}
        if action_type == ActionType.OFFER:
            extra = {
                "what": "10 credits",
                "against_what": "5 digital_goods",
                "to_agent_id": random.choice(context.neighbors) if context.neighbors else None
            }
        elif action_type == ActionType.NEGOTIATE:
            if context.pending_offers:
                extra = {
                    "offer_id": context.pending_offers[0]["id"],
                    "message": "I would like to counter with a better offer."
                }
            else:
                action_type = ActionType.REST  # Default if no offers
        elif action_type == ActionType.ACCEPT or action_type == ActionType.REJECT:
            if context.pending_offers:
                extra = {
                    "offer_id": context.pending_offers[0]["id"]
                }
            else:
                action_type = ActionType.REST  # Default if no offers
        elif action_type == ActionType.WORK:
            if context.jobs_available:
                extra = {
                    "job_id": context.jobs_available[0]["id"]
                }
            else:
                action_type = ActionType.SEARCH_JOB
        elif action_type == ActionType.BUY:
            if context.items_for_sale:
                extra = {
                    "desired_item": context.items_for_sale[0]["id"]
                }
            else:
                action_type = ActionType.REST
        
        # Generate a mock reasoning
        reasoning = f"Mock reasoning for choosing {action_type.value} based on agent personality."
        
        return AgentActionResponse(
            type=action_type.value,
            extra=extra,
            reasoning=reasoning
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
    Format a prompt for the LLM based on the agent and context.
    
    Args:
        agent: The agent to generate a prompt for
        context: Decision context for the agent
        
    Returns:
        str: The formatted prompt
    """
    # Format the agent resources
    resources_str = ", ".join([f"{k}: {v}" for k, v in context.resources.items()])
    
    # Format the agent needs
    needs_str = ", ".join([f"{k}: {v}" for k, v in context.needs.items()])
    
    # Format neighbors
    neighbors_str = ", ".join(context.neighbors) if context.neighbors else "none"
    
    # Format pending offers
    pending_offers_str = ""
    for offer in context.pending_offers:
        pending_offers_str += f"  - Offer {offer['id']} from {offer['from']}: {offer['what']} for {offer['for']}\n"
    
    if not pending_offers_str:
        pending_offers_str = "  none\n"
    
    # Format jobs
    jobs_str = ""
    for job in context.jobs_available:
        jobs_str += f"  - Job {job['id']}: {job['type']} for {job['pay']} (difficulty: {job['difficulty']})\n"
    
    if not jobs_str:
        jobs_str = "  none\n"
    
    # Format items for sale
    items_str = ""
    for item in context.items_for_sale:
        items_str += f"  - Item {item['id']}: {item['type']} for {item['price']} (quality: {item['quality']})\n"
    
    if not items_str:
        items_str = "  none\n"
    
    # Format recent interactions
    interactions_str = ""
    for interaction in context.recent_interactions:
        interactions_str += f"  - Turn {interaction['turn']}: {interaction['type']} with {interaction['with']} ({interaction['outcome']})\n"
    
    if not interactions_str:
        interactions_str = "  none\n"
    
    # Format the available actions
    actions_str = ", ".join([action_type.value for action_type in ActionType])
    
    # Construct prompt (optimized for all models)
    prompt = f"""
You are an agent in a simulated cyberpunk Mars economy in the year 2993. You need to choose an action based on your personality and context.

Your details:
- Name: {agent.name}
- Resources: {resources_str}
- Needs: {needs_str}
- Turn: {context.turn}/{context.max_turns}

Social context:
- Neighbors: {neighbors_str}
- Pending offers:
{pending_offers_str}
- Available jobs:
{jobs_str}
- Items for sale:
{items_str}
- Recent interactions:
{interactions_str}

Personality traits:
- Cooperativeness: {agent.personality.cooperativeness:.2f} (higher values mean more willing to cooperate)
- Risk tolerance: {agent.personality.risk_tolerance:.2f} (higher values mean more willing to take risks)
- Fairness preference: {agent.personality.fairness_preference:.2f} (higher values mean more concerned with fairness)
- Altruism: {agent.personality.altruism:.2f} (higher values mean more selfless)
- Rationality: {agent.personality.rationality:.2f} (higher values mean more logical decision-making)
- Long-term orientation: {agent.personality.long_term_orientation:.2f} (higher values mean more focus on long-term outcomes)

Your possible actions are: {actions_str}

Based on your personality, resources, and social context, what will you do?
Think through your options carefully, then choose the most appropriate action with necessary details.

Examples:
- REST: When you need to recover or there are no good options
- OFFER: When you want to initiate a trade with another agent (requires what, against_what, and to_agent_id)
- NEGOTIATE: When you want to counter an existing offer (requires offer_id and optionally a message)
- ACCEPT/REJECT: When responding to an offer (requires offer_id)
- WORK: When taking a job (requires job_id)
- BUY: When purchasing an item (requires desired_item)
- SEARCH_JOB: When looking for new job opportunities

Response must be a JSON object with 'type', 'extra', and 'reasoning' fields.
"""
    
    return prompt