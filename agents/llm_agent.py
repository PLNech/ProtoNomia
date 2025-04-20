"""
LLM-based agent implementation for ProtoNomia.
This module handles the integration with language models for agent decision making.
"""
import json
import logging
import random
import re
import time
import requests
from typing import Dict, List, Optional, Any, Tuple

from models.base import Agent
from models.actions import (
    ActionType, AgentAction, AgentDecisionContext, LLMAgentActionResponse,
    OfferAction, NegotiateAction, AcceptRejectAction, WorkAction, BuyAction
)

# Initialize logger
logger = logging.getLogger(__name__)


class LLMAgent:
    """
    LLM-based agent implementation for ProtoNomia.
    Uses Ollama or mocked responses to generate agent decisions.
    """
    
    def __init__(self, model_name: str = "gemma:4b", mock: bool = False):
        """
        Initialize the LLM agent.
        
        Args:
            model_name: Name of the Ollama model to use
            mock: Whether to mock LLM responses
        """
        self.model_name = model_name
        self.mock = mock
        self.ollama_endpoint = "http://localhost:11434/api/generate"
        
        # Test Ollama connection if not in mock mode
        if not self.mock:
            try:
                self._test_ollama_connection()
                logger.info(f"Successfully connected to Ollama with model {model_name}")
            except Exception as e:
                logger.warning(f"Failed to connect to Ollama: {e}. Falling back to mock mode.")
                self.mock = True
    
    def _test_ollama_connection(self):
        """Test the connection to Ollama"""
        response = requests.post(
            self.ollama_endpoint,
            json={
                "model": self.model_name,
                "prompt": "Test connection. Respond with: CONNECTION_OK",
                "stream": False
            },
            timeout=5
        )
        response.raise_for_status()
        if "CONNECTION_OK" not in response.json().get("response", ""):
            raise Exception("Failed to validate Ollama response")
    
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
        
        try:
            # Get LLM response
            if self.mock:
                response_data = self._mock_llm_response(agent, context)
            else:
                response_data = self._call_ollama(prompt)
            
            # Parse the action from the response
            action_response = self._parse_action_response(response_data)
            
            # Create AgentAction from LLMAgentActionResponse
            action = self._create_agent_action(action_response, agent.id, context.turn)
            
            logger.debug(f"Generated action for agent {agent.id}: {action.type}")
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
    
    def _call_ollama(self, prompt: str) -> str:
        """
        Call the Ollama API to generate a response.
        
        Args:
            prompt: The prompt to send to the model
            
        Returns:
            str: The generated response
        """
        try:
            response = requests.post(
                self.ollama_endpoint,
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9
                    }
                },
                timeout=5
            )
            response.raise_for_status()
            return response.json().get("response", "")
        except requests.exceptions.RequestException as e:
            logger.error(f"Error calling Ollama: {e}")
            raise
    
    def _mock_llm_response(self, agent: Agent, context: AgentDecisionContext) -> str:
        """
        Generate a mock LLM response for testing.
        
        Args:
            agent: The agent to generate a response for
            context: Decision context for the agent
            
        Returns:
            str: A mocked response
        """
        # For mocking, we'll generate a response based on personality and context
        action_type = random.choice(list(ActionType))
        
        # Bias toward certain actions based on personality
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
        
        # Format the mock response like the LLM would return
        return f"CHOICE: {{'type': '{action_type.value}', 'extra': {json.dumps(extra)}}}"
    
    def _parse_action_response(self, response: str) -> LLMAgentActionResponse:
        """
        Parse the LLM response into a structured action.
        
        Args:
            response: The raw response from the LLM
            
        Returns:
            LLMAgentActionResponse: The parsed action
        """
        try:
            # Extract the action from the response using regex
            match = re.search(r"CHOICE:\s*({.*})", response)
            if not match:
                logger.warning(f"Could not parse LLM response: {response}")
                return LLMAgentActionResponse(type=ActionType.REST)
            
            action_json = match.group(1)
            action_data = json.loads(action_json.replace("'", "\""))
            
            # Extract action type and extra data
            action_type_str = action_data.get('type', 'REST')
            action_type = ActionType(action_type_str)
            extra = action_data.get('extra', {})
            
            return LLMAgentActionResponse(type=action_type, extra=extra)
            
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Error parsing action response: {e}")
            return LLMAgentActionResponse(type=ActionType.REST)
    
    def _create_agent_action(self, response: LLMAgentActionResponse, agent_id: str, turn: int) -> AgentAction:
        """
        Convert an LLMAgentActionResponse to an AgentAction with the appropriate details.
        
        Args:
            response: The parsed LLM response
            agent_id: The ID of the agent
            turn: The current turn
            
        Returns:
            AgentAction: The complete agent action
        """
        action = AgentAction(
            type=response.type,
            agent_id=agent_id,
            turn=turn,
            timestamp=time.time(),
            extra=response.extra
        )
        
        # Fill in action-specific details based on type
        if response.type == ActionType.OFFER:
            action.offer_details = OfferAction(
                what=response.extra.get("what", ""),
                against_what=response.extra.get("against_what", ""),
                to_agent_id=response.extra.get("to_agent_id")
            )
        elif response.type == ActionType.NEGOTIATE:
            action.negotiate_details = NegotiateAction(
                offer_id=response.extra.get("offer_id", ""),
                message=response.extra.get("message", "")
            )
        elif response.type in [ActionType.ACCEPT, ActionType.REJECT]:
            action.accept_reject_details = AcceptRejectAction(
                offer_id=response.extra.get("offer_id", "")
            )
        elif response.type == ActionType.WORK:
            action.work_details = WorkAction(
                job_id=response.extra.get("job_id", "")
            )
        elif response.type == ActionType.BUY:
            action.buy_details = BuyAction(
                desired_item=response.extra.get("desired_item", "")
            )
        
        return action


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
    
    # Construct prompt (optimized for gemma models)
    prompt = f"""
You are an agent in a simulated cyberpunk Mars economy in the year 2993. Respond with only your chosen action.

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
- Cooperativeness: {agent.personality.cooperativeness:.2f}
- Risk tolerance: {agent.personality.risk_tolerance:.2f}
- Fairness preference: {agent.personality.fairness_preference:.2f}
- Altruism: {agent.personality.altruism:.2f}
- Rationality: {agent.personality.rationality:.2f}
- Long-term orientation: {agent.personality.long_term_orientation:.2f}

Your possible actions are: {actions_str}

Based on your personality, resources, and social context, what will you do?
Think through your options carefully, then respond with CHOICE: followed by a JSON object with 'type' (one of the actions above) and 'extra' (any additional details).

Examples:
For REST: CHOICE: {{'type': 'REST', 'extra': {{'reason': 'I need to recover energy'}}}}
For OFFER: CHOICE: {{'type': 'OFFER', 'extra': {{'what': '10 credits', 'against_what': '5 digital_goods', 'to_agent_id': 'agent1'}}}}
For BUY: CHOICE: {{'type': 'BUY', 'extra': {{'desired_item': 'item1'}}}}

Your response (ONLY include your CHOICE, nothing else):
"""
    
    return prompt