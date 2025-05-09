"""
LLM-based agent implementation for ProtoNomia.
This module handles the integration with language models for agent decision making.
"""

from src.models.simulation import *
from src.generators import generate_thoughts
from src.llm_utils import OllamaClient
from src.scribe import Scribe
from src.settings import DEFAULT_LM, LLM_MAX_RETRIES

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
            max_retries: int = LLM_MAX_RETRIES,
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
            "You are a citizen on Mars in our 2993 settlement. "
            f"Based on your personality ({agent.personality.text}) and context, choose the most appropriate action. "
            "Consider your needs, resources, and available options when making your decision. "
            "10 credits is enough to survive a day. 100 credits you're fine. 1000 you're good. "
            "5k+ you could never WORK and mostly COMPOSE or THINK, you'd just need to HARVEST/CRAFT/BUY/SELL sometimes. "
            "Assess your needs: e.g. rest=0.2 I MUST REST OR DIE, rest=0.4 I should REST, "
            "rest=0.6 don't really need to rest, rest>=0.8 it's pretty useless to rest I'd not win much,"
            "if all your needs are met, try to craft something unique with a cool name, or to buy and sell smart. "
            "Your response MUST be valid JSON with a 'type' field for the action type and an 'extras' field "
            "containing any additional information needed for the action in a proper JSON object format. "
            "IMPORTANT: Make sure 'extras' is a JSON object/dictionary, not a string or any other type. "
            "If you have no extras data, use an empty object: 'extras': {}"
        )

        try:
            # Show status indicator while generating the response
            with Scribe.status(f"Querying LLM for {agent.name}'s next action..."):
                # Generate structured action response
                action: AgentActionResponse = self.ollama_client.generate_structured(
                    prompt=prompt,
                    response_model=AgentActionResponse,
                    system_prompt=system_prompt
                )

            logger.info(f"[{simulation_state.day}] Generated action for {agent.name}: {action.type}")
            return action

        except Exception as e:
            logger.error(f"Error generating action for {agent.name}: {e}")
            # Make sure to stop any status if there's an exception
            Scribe.stop_status()
            # Fallback to a random action if LLM fails
            fallback_action = self._fallback_action(agent)
            return fallback_action

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
                extras={},
                reasoning="[FALLBACK ACTION] Taking a rest to recover energy"
            )
        elif random_type == ActionType.WORK:
            return AgentActionResponse(
                type=random_type,
                extras={},
                reasoning="[FALLBACK ACTION] Working to earn credits for survival"
            )
        elif random_type == ActionType.HARVEST:
            return AgentActionResponse(
                type=random_type,
                extras={},
                reasoning="[FALLBACK ACTION] Harvesting mushrooms for food"
            )
        elif random_type == ActionType.CRAFT:
            return AgentActionResponse(
                type=random_type,
                extras={"materials": random.randint(10, 50)},
                reasoning="[FALLBACK ACTION] Crafting an item"
            )
        elif random_type == ActionType.BUY:
            return AgentActionResponse(
                type=random_type,
                extras={"listingId": "random"},
                reasoning="[FALLBACK ACTION] Buying something from the market"
            )
        elif random_type == ActionType.SELL:
            return AgentActionResponse(
                type=random_type,
                extras={"goodName": "Martian TV", "price": random.randint(50, 150)},
                reasoning="[FALLBACK ACTION] Selling an item"
            )
        elif random_type == ActionType.THINK:
            return AgentActionResponse(
                type=random_type,
                reasoning="[FALLBACK ACTION] Pondering about civilization...",
                extras={"thoughts": generate_thoughts(), "themes": "cached"}
            )

        # Default fallback is REST
        return AgentActionResponse(
            type=ActionType.REST,
            extras={},
            reasoning="[FALLBACK ACTION] Default fallback - resting"
        )


def format_credits(net_worth: float) -> str:
    """Format net worth as a number with commas and analysis of urgency."""
    if net_worth < 10:
        return f"{net_worth:,} - starving if you don't WORK"
    elif net_worth < 100:
        return f"{net_worth:,} - you'll have to WORK in the next few days"
    elif net_worth < 1000:
        return f"{net_worth:,} - you're doing fine, no need to WORK anytime soon"
    else:
        return f"{net_worth:,} - you're very rich, WORK would be obscene, all needs can be met with credits!"


def format_need(need: float) -> str:
    """Format a need value as a percentage and analysis of urgency."""
    if need < 0.2:
        return f"{need:.2%}: MUST BE ADDRESSED IMMEDIATELY!"
    elif need < 0.4:
        return f"{need:.2%}: SHOULD BE ADDRESSED SOON!"
    elif need < 0.6:
        return f"{need:.2%}: good for today."
    elif need < 0.8:
        return f"{need:.2%}: doing well."
    elif need < 0.9:
        return f"{need:.2%}: doing great."
    else:
        return f"{need:.2%}: amazing!"


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
    prompt = f"# MARS SETTLEMENT DAY {simulation_state.day}\n\n"
    prompt += f"## YOUR PROFILE\n"
    prompt += f"Name: {agent.name}\n"
    prompt += f"Age: {agent.age_days} days\n"
    prompt += f"Personality: {agent.personality.text}\n"
    prompt += f"Credits: {format_credits(agent.credits)}\n\n"

    if agent.history:
        recent_history = agent.history[-agent.memory:]
        prompt += f"Your personal journal includes {len(recent_history)} recent history entries:\n"
        for (i, entry) in enumerate(recent_history):
            credits_score, needs, goods, action = entry
            prompt += f"Entry {i}: {credits_score} credits, needs: {repr(needs)}, goods={goods} -> you chose to: {action.type} (extras={action.extras} / reasoning={action.reasoning}\n"
        prompt += "DO YOUR BEST TO THINK AND ACT LONG TERM BASED ON YOUR MEMORY\n"

    # Format agent needs
    prompt += f"## YOUR NEEDS\n"
    # percentage would help agent better understand their needs.
    prompt += f"Food: {format_need(agent.needs.food)}%\n"
    prompt += f"Rest: {format_need(agent.needs.rest)}%\n"
    prompt += f"Fun: {format_need(agent.needs.fun)}%\n\n"

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
    market_listings = [l for l in simulation_state.market.listings if agent.name != l.seller_id]
    if not market_listings:
        prompt += "The market has no listings at the moment. You may make big bucks if you CRAFT & SELL something!\n\n"
    else:
        for listing in market_listings:
            seller = next((a for a in simulation_state.agents if a.id == listing.seller_id), None)
            seller_name = seller.name if seller else "Unknown"
            prompt += f"-[ID={listing.id}] {listing.good.name} ({listing.good.type.value}, quality: {listing.good.quality:.2f}) for {listing.price} credits from {seller_name} ({listing.seller_id})\n"
        prompt += "\n"

    # Format inventions
    prompt += f"## EXISTING INVENTIONS\n"
    if not simulation_state.inventions:
        prompt += "Nobody CRAFTED anything yet! Great times for innovators!\n\n"
    else:
        for i, inventions in enumerate(simulation_state.inventions.values()):
            day_count = simulation_state.count_inventions(i)
            prompt += f"Day {i}: {day_count} inventions:\n"
            if day_count:
                for j, invention in enumerate(inventions):
                    agent, good = invention
                    prompt += f"{i}. {good.name} ({good.type.value}, quality: {good.quality:.2f}) by {agent.name}\n"
        prompt += "\n"

    # Format available actions
    prompt += f"## AVAILABLE ACTIONS\n"
    prompt += f"1. REST - Recover some rest (0.2)\n"
    prompt += f"2. WORK - Earn 100 credits at the settlement job\n"
    prompt += f"3. HARVEST - Gather mushrooms from the settlement farm\n"
    prompt += (f"4. CRAFT - Create a new item (you can give it a 'name', "
               f"choose 1 'goodType' within {GoodType.all()} else will be at random, "
               f"and optional 'materials' amount in credits to improve quality. Adding credits as you can, "
               f"even few, can make your craft better!)\n")

    if agent.goods:
        prompt += (f"5. SELL - Sell one of your goods ({','.join([str(g) for g in agent.goods])}) on the market. "
                   f"When you have several FUN or REST items, it's a great idea to SELL the worst one."
                   f"If there's no market, you could be a marketmaker and set very high prices!!!\n"
                   f"SELL orders MUST include a extras.price")

    if market_listings:
        prompt += (f"6. BUY - Purchase an item from the market, "
                   f"current listings: {','.join(str(l) for l in market_listings)}\n")

    prompt += f"7. THINK - Spend the day creatively thinking about inventions, culture, philosophy, etc.\n"
    prompt += (f"8. COMPOSE - Create some music to elevate your mood, channel your creative feelings, "
               f"entertain your fellow citizens, or to try to reach eternal posterity as a musical shooting star!\n"
               f"Current music genres: {','.join(simulation_state.songs.genres if simulation_state.songs.genres else [])} "
               f"- but feel free to create a variant or invent a totally new one :D")

    # Task description
    prompt += (
        f"\n## TASK\n"
        f"Based on your profile, resources, needs, and available actions, decide what to do next.\n"
        f"Think step by step about what would be the most beneficial course of action "
        f"considering your personality traits and current situation.\n"
        f"Action descriptions: {', '.join([f'{x.value}: {y}' for (x, y) in ACTION_DESCRIPTIONS.items()])}"
        f"Return your choice in this format:\n\n"
    )

    # Add more explicit formatting instructions, reasoning always first
    prompt += (
        f"```json\n"
        f"{{\n"
        f'  "reasoning": "Why you chose this action",\n'
        # TODO: Add unit test ensuring this type comment stays in sync with list of ActionTypes
        f'  "type": "ACTION_TYPE", // REST, WORK, HARVEST, CRAFT, SELL, BUY, or THINK\n'
        f'  "extras": {{}} // An object with extra information, may be empty {{}}\n'
        f"}}\n```\n\n"
    )

    # Add examples based on action type
    prompt += (
        f"## EXAMPLES\n"
        f'For REST: {{ "reasoning": "I need to recover my energy", "type": "REST", "extras": {{}} }}\n\n'
        f'For WORK: {{ "reasoning": "I need to earn credits", "type": "WORK", "extras": {{}} }}\n\n'
        f'For HARVEST: {{ "reasoning": "I need food", "type": "HARVEST", "extras": {{}} }}\n\n'
        f'For CRAFT: {{ "reasoning": "I want to create something valuable", "type": "CRAFT", '
        f'"extras": {{ "materials": 50, "name": "Red soil planter", "goodType": "FUN" }} }}\n\n'
        f'For THINK: {{ "reasoning": "I\'m feeling good, let\'s spend the day reflecting.", "type": "THINK", '
        f'"extras": {{ "thoughts": "I wonder if I\'m alive or just feel like it", "theme": "existentialism" }} }}\n\n'
        f'For COMPOSE: {{ "reasoning": "I\'m bored, let\'s get grooving!", "type": "COMPOSE", '
        f'"extras": {{ "title": "Robot Rock", "genre": "Techno", "bpm": 120, "tags":["groovy", "off-beat", "guitar"],'
        f'"description": "fast paced french touch revival" }} }}\n\n'
    )
    # TODO: Add unit test ensuring the examples stay in sync with list of ActionTypes

    if agent.goods:
        prompt += (
            f'For SELL: {{ "reasoning": "I want to sell my third good, the \"{agent.goods[0].name}\", '
            f'to use its credits for materials and craft something way better.", '
            f'"type": "SELL", "extras": {{ "goodName": "{agent.goods[0].name}", "price": 1000 }} }}\n\n')

    if market_listings:
        prompt += (f'For BUY: {{ "reasoning": "I need the \"V60 CoffeeBot\" and I can afford it.", '
                   f'"type": "BUY", "extras": {{ "listingId": "YOUR_LISTING_ID" }} }}\n\n')

    # Add a critical reminder
    prompt += (
        f"IMPORTANT: Your response must be valid JSON with 'reasoning', 'type', and 'extras' fields.\n"
        f"The 'extras' field MUST be a JSON object (not a string or other type), even if empty: {{}}\n"
    )

    return prompt
