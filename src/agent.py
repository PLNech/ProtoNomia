"""
LLM-based agent implementation for ProtoNomia.
This module handles the integration with language models for agent decision making.
"""
import logging
import random

from src.llm_utils import OllamaClient
from src.models import Agent, ActionType, AgentActionResponse, SimulationState
from src.settings import DEFAULT_LM

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
            timeout: int = 30
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

    def generate_action(self, agent: Agent, simulation_state: SimulationState) -> AgentActionResponse:
        """
        Generate an action for the agent using the LLM.

        Args:
            agent: The agent to generate an action for
            simulation_state: Current state of the simulation

        Returns:
            AgentAction: The generated action usable by the Simulation.
        """
        # Format prompt
        prompt = format_prompt(agent, simulation_state)
        system_prompt = (
            "You are an AI assistant helping Mars colonists make economic decisions. "
            "Based on the agent's personality and context, choose the most appropriate action. "
            "Consider the agent's needs, resources, and available options when making your decision. "
            "Your response MUST be valid JSON with a 'type' field for the action type and an 'extra' field "
            "containing any additional information needed for the action in a proper JSON object format. "
            "IMPORTANT: Make sure 'extra' is a JSON object/dictionary, not a string or any other type. "
            "If you have no extra data, use an empty object: 'extra': {}"
        )
        
        try:
            # Generate structured action response
            action = self.ollama_client.generate_structured(
                prompt=prompt,
                response_model=AgentActionResponse,
                system_prompt=system_prompt
            )
            
            logger.info(f"Generated action for {agent.name}: {action.type}")
            return action
            
        except Exception as e:
            logger.error(f"Error generating action for {agent.name}: {e}")
            # Fallback to a random action if LLM fails
            return self._fallback_action(agent)
            
    def _fallback_action(self, agent: Agent = None) -> AgentActionResponse:
        """Generate a fallback random action when LLM fails"""
        # The actions with the highest priority for survival are REST, WORK, and HARVEST
        # We prioritize these in our fallback to help agents survive
        action_types = [ActionType.REST, ActionType.WORK, ActionType.HARVEST]
        
        # If the agent has extremely low food, prioritize HARVEST
        if agent and agent.needs.food < 0.3:
            random_type = ActionType.HARVEST
        # If the agent has extremely low rest, prioritize REST
        elif agent and agent.needs.rest < 0.3:
            random_type = ActionType.REST
        # Otherwise choose from the survival actions
        else:
            random_type = random.choice(action_types)
        
        if random_type == ActionType.REST:
            return AgentActionResponse(
                type=random_type,
                extra={},
                reasoning="[FALLBACK ACTION] Taking a rest to recover energy"
            )
        elif random_type == ActionType.WORK:
            return AgentActionResponse(
                type=random_type,
                extra={},
                reasoning="[FALLBACK ACTION] Working to earn credits for survival"
            )
        elif random_type == ActionType.HARVEST:
            return AgentActionResponse(
                type=random_type,
                extra={},
                reasoning="[FALLBACK ACTION] Harvesting mushrooms for food"
            )
        elif random_type == ActionType.CRAFT:
            return AgentActionResponse(
                type=random_type,
                extra={"materials": random.randint(10, 50)},
                reasoning="[FALLBACK ACTION] Crafting an item"
            )
        elif random_type == ActionType.BUY:
            return AgentActionResponse(
                type=random_type,
                extra={"listing_id": "random"},
                reasoning="[FALLBACK ACTION] Buying something from the market"
            )
        elif random_type == ActionType.SELL:
            return AgentActionResponse(
                type=random_type,
                extra={"good_index": 0, "price": random.randint(50, 150)},
                reasoning="[FALLBACK ACTION] Selling an item"
            )
        
        # Default fallback is REST
        return AgentActionResponse(
            type=ActionType.REST,
            extra={},
            reasoning="[FALLBACK ACTION] Default fallback - resting"
        )


def format_prompt(agent: Agent, simulation_state: SimulationState) -> str:
    """
    Format the prompt for agent decision making.

    Args:
        agent: The agent making the decision.
        simulation_state: The current simulation state.

    Returns:
        str: Formatted prompt for the LLM that includes all useful info from the situation and agent
        for a LLM to then take a logical decision as this agent.
    """
    # Format agent basic information
    prompt = f"# MARS COLONY DAY {simulation_state.day}\n\n"
    prompt += f"## YOUR PROFILE\n"
    prompt += f"Name: {agent.name}\n"
    prompt += f"Age: {agent.age_days} days\n"
    prompt += f"Personality: {agent.personality.personality}\n"
    prompt += f"Credits: {agent.credits}\n\n"
    
    # Format agent needs
    prompt += f"## YOUR NEEDS\n"
    prompt += f"Food: {agent.needs.food:.2f}/1.00\n"
    prompt += f"Rest: {agent.needs.rest:.2f}/1.00\n"
    prompt += f"Fun: {agent.needs.fun:.2f}/1.00\n\n"
    
    # Format inventory
    prompt += f"## YOUR INVENTORY\n"
    if not agent.goods:
        prompt += "You have no items.\n\n"
    else:
        for i, good in enumerate(agent.goods):
            prompt += f"{i}. {good.name} ({good.type.value}, quality: {good.quality:.2f})\n"
        prompt += "\n"
    
    # Format market information
    prompt += f"## MARKET\n"
    market_listings = simulation_state.market.listings
    if not market_listings:
        prompt += "The market has no listings at the moment.\n\n"
    else:
        for listing in market_listings:
            seller = next((a for a in simulation_state.agents if a.id == listing.seller_id), None)
            seller_name = seller.name if seller else "Unknown"
            prompt += f"- {listing.good.name} ({listing.good.type.value}, quality: {listing.good.quality:.2f}) for {listing.price} credits from {seller_name}\n"
        prompt += "\n"
    
    # Format available actions
    prompt += f"## AVAILABLE ACTIONS\n"
    prompt += f"1. REST - Recover some rest (0.2)\n"
    prompt += f"2. WORK - Earn 100 credits at the colony job\n"
    prompt += f"3. HARVEST - Gather mushrooms from the colony farm\n"
    prompt += f"4. CRAFT - Create a new item (can spend credits on materials to improve quality)\n"
    
    if agent.goods:
        prompt += f"5. SELL - Sell one of your items on the market\n"
    
    if market_listings:
        prompt += f"6. BUY - Purchase an item from the market\n"
    
    # Task description
    prompt += (
        f"\n## TASK\n"
        f"Based on your profile, resources, needs, and available actions, decide what to do next.\n"
        f"Think step by step about what would be the most beneficial course of action considering your personality traits and current situation.\n"
        f"Return your choice in this format:\n\n"
    )
    
    # Add more explicit formatting instructions
    prompt += (
        f"```json\n"
        f"{{\n"
        f'  "type": "ACTION_TYPE", // REST, WORK, HARVEST, CRAFT, SELL, or BUY\n'
        f'  "extra": {{}}, // An object with extra information, may be empty {{}}\n'
        f'  "reasoning": "Why you chose this action"\n'
        f"}}\n```\n\n"
    )
    
    # Add examples based on action type
    prompt += (
        f"## EXAMPLES\n"
        f'For REST: {{ "type": "REST", "extra": {{}}, "reasoning": "I need to recover my energy" }}\n\n'
        f'For WORK: {{ "type": "WORK", "extra": {{}}, "reasoning": "I need to earn credits" }}\n\n'
        f'For HARVEST: {{ "type": "HARVEST", "extra": {{}}, "reasoning": "I need food" }}\n\n'
        f'For CRAFT: {{ "type": "CRAFT", "extra": {{ "materials": 50 }}, "reasoning": "I want to create something valuable" }}\n\n'
    )
    
    if agent.goods:
        prompt += f'For SELL: {{ "type": "SELL", "extra": {{ "good_index": 0, "price": 100 }}, "reasoning": "I want to earn credits from my goods" }}\n\n'
    
    if market_listings:
        prompt += f'For BUY: {{ "type": "BUY", "extra": {{ "listing_id": "{market_listings[0].id}" }}, "reasoning": "I need this item" }}\n\n'
    
    # Add a critical reminder
    prompt += (
        f"IMPORTANT: Your response must be valid JSON with 'type', 'extra', and 'reasoning' fields.\n"
        f"The 'extra' field MUST be a JSON object (not a string or other type), even if empty: {{}}\n"
    )
    
    return prompt
