"""
Narrator module for ProtoNomia.
This module uses Ollama to generate narrative events from economic interactions.
"""
import logging
import random
from copy import deepcopy

from src.agent import format_need
from src.llm_utils import OllamaClient
from src.models import (
    ActionType, SimulationState,
    DailySummaryResponse, AgentActionResponse, AgentAction, Good
)
from src.models import Agent, ActionLog
from src.scribe import Scribe
from src.settings import DEFAULT_LM

# Initialize logger
logger = logging.getLogger(__name__)


class Narrator:
    """
    LLM-powered Narrator that uses Ollama to generate narrative events and
    arcs from economic interactions.
    """

    def __init__(
            self,
            model_name: str = DEFAULT_LM,
            ollama_base_url: str = "http://localhost:11434",
            temperature: float = 0.8,
            top_p: float = 0.95,
            top_k: int = 40,
            timeout: int = 30,
            max_retries: int = 3
    ):
        """
        Initialize the Narrator.
        """
        self.model_name = model_name
        self.ollama_base_url = ollama_base_url
        self.temperature = temperature
        self.top_p = top_p
        self.top_k = top_k
        self.timeout = timeout
        self.max_retries = max_retries

        logger.info(f"Initializing Narrator with model {model_name}")

        # Create the OllamaClient for structured output generation
        self.ollama_client = OllamaClient(
            base_url=ollama_base_url,
            model_name=model_name,
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
            max_tokens=2 ** 14,
            max_retries=max_retries,
            timeout=timeout
        )
        logger.info(f"Successfully connected to Ollama with model {model_name}")

    def generate_daily_summary(self, state: SimulationState) -> DailySummaryResponse:
        """
        Generate a narrative summary for the day's events.
        
        Args:
            state: The current simulation state
            
        Returns:
            DailySummaryResponse: Structured narrative summary
        """
        # Format summary prompt using the day's events
        prompt = self._format_summary_prompt(state)

        system_prompt = (
            "You are a talented storyteller on Mars, chronicling the daily lives of citizens. "
            "Create engaging, vivid 50-100 words day summaries that highlight economic interactions, conflicts, "
            "and character development. Focus on how the citizens' needs, desires, thoughts, and actions shape "
            "the emerging Martian economy and culture. Use crisp language and evocative science fiction imagery.\n"
            "NEVER INVENT CHARACTERS NOT IN THE AGENTS LIST: when you have only 1 or 0 agent, make it contemplative.\n"
            "DON'T BREAK CHARACTER: NEVER MENTION FLOAT VALUES AND COUNTERS, ONLY IN-GAME SUBJECTIVE IMPRESSIONS\n"
        )

        try:
            # Show status indicator while generating the narrative
            with Scribe.status(f"Generating narrative for Day {state.day}...", spinner="aesthetic"):
                # Generate structured daily summary
                summary = self.ollama_client.generate_daily_summary(
                    prompt=prompt,
                    system_prompt=system_prompt
                )
            return summary
        except Exception as e:
            logger.error(f"Error generating daily summary: {e}")
            # Make sure to stop any status if there's an exception
            Scribe.stop_status()
            # Create fallback summary
            return self._generate_fallback_summary(state)

    def _format_summary_prompt(self, state: SimulationState) -> str:
        """
        Format the prompt for daily summary generation.
        
        Args:
            state: The current simulation state
            
        Returns:
            str: Formatted prompt
        """
        # Basic information
        prompt = f"# MARS SETTLEMENT: DAY {state.day}\n\n"

        # Agents
        prompt += f"## AGENTS\n"
        for agent in state.agents:
            prompt += f"- {agent.name}: "
            prompt += f"Credits: {agent.credits}, "
            prompt += f"Needs: Food={format_need(agent.needs.food)}, Rest={agent.needs.rest:.2f}, Fun={agent.needs.fun:.2f}\n"
        prompt += "\n"

        # Day's actions
        if state.actions:
            prompt += f"## TODAY'S ACTIONS\n"
            log: ActionLog
            for log in state.today_actions:
                action_desc = self._describe_action(log.action, log.agent)
                reasoning = log.action.reasoning or ""
                prompt += f"- {log.agent.name}: {action_desc}{reasoning}\n"
            prompt += "\n"

        # Day's actions
        today_crafts = state.inventions[state.day]
        if len(today_crafts):
            prompt += f"## TODAY'S {len(today_crafts)} INVENTION{'S' if len(today_crafts) > 1 else ''}\n"
            good: Good
            agent: Agent
            for agent, good in today_crafts:
                prompt += f"- {good.name} ({good.type} of quality {good.quality}) invented by {agent.name}\n"
            prompt += "Make sure to comment if some are complementary, opposed, or ripoffs.\n"

        # Market activity
        prompt += f"## MARKET ACTIVITY\n"
        if state.market.listings:
            for listing in state.market.listings:
                seller = next((a for a in state.agents if a.id == listing.seller_id), None)
                seller_name = seller.name if seller else "Unknown"
                prompt += f"- {seller_name} is selling {listing.good.name} (Quality: {listing.good.quality:.2f}) for {listing.price} credits\n"
        else:
            prompt += "The market had no active listings today.\n"
        prompt += "\n"

        # Day's ideas
        today_thoughts = state.ideas[state.day]
        if len(today_thoughts):
            prompt += f"## TODAY'S {len(today_thoughts)} IDEA{'S' if len(today_thoughts) > 1 else ''}\n"
            prompt += "\n".join(f"{agent.name}: \"{idea}\"" for (agent, idea) in today_thoughts)

        if state.songs.genres:
            logger.debug(f"Music genres so far: {state.songs.genres}")
        # Day's songs
        today_songs = state.songs.day(state.day)
        logger.debug(f"Songs of the day : {len(today_songs)} songs.")
        if today_songs:
            prompt += f"## TODAY'S {len(today_songs)} SONG{'S' if len(today_songs) > 1 else ''}\n"
            prompt += "\n".join(f"{agent.name}: \"{song}\"" for (agent, song) in today_songs)
        else:
            prompt += "## TODAY'S SONGS: NONE! It could be rad to be the one to COMPOSE one ;)"

        # Deaths or critical events
        if state.dead_agents:
            today_deaths = [a for a in state.dead_agents if a.death_day == state.day]
            if today_deaths:
                prompt += f"## DEATHS\n"
                for agent in today_deaths:
                    needs_desc = []
                    if agent.needs.food <= 0:
                        needs_desc.append("starvation")
                    if agent.needs.rest <= 0:
                        needs_desc.append("exhaustion")

                    cause = " and ".join(needs_desc) if needs_desc else "unknown causes"
                    prompt += f"- {agent.name} died from {cause}\n"
                prompt += "\n"

        # Task description
        prompt += (
            "## TASK\n"
            "Based on this information, create a narrative summary of Day {state.day} on Mars. "
            "Focus on agent character interactions, economic decisions, and how needs influence behavior. "
            "Highlight interesting moments, conflicts, and insights into the settlement's development.\n"
            "Be careful to only mention events/interactions/motivations that are really in agent action/reasoning logs."
        )

        return prompt

    def _describe_action(self, action: (AgentAction | AgentActionResponse), agent: Agent) -> str:
        """Create a human-readable description of an agent action"""
        if action.type == ActionType.REST:
            return "took time to rest and recover"

        elif action.type == ActionType.WORK:
            return "worked at the settlement job to earn credits"

        elif action.type == ActionType.HARVEST:
            return "harvested mushrooms from the settlement farm"

        elif action.type == ActionType.CRAFT:
            materials = action.extras.get("materials", 0)
            if materials > 0:
                return f"crafted a new item, investing {materials} credits in materials"
            return "crafted a new item"

        elif action.type == ActionType.SELL:
            good_index = action.extras.get("goodIndex", 0)
            price = action.extras.get("price", 0)

            if 0 <= good_index < len(agent.goods):
                good_name = agent.goods[good_index].name
                return f"put {good_name} up for sale at {price} credits"
            return f"tried to sell an item for {price} credits"

        elif action.type == ActionType.BUY:
            listing_id = action.extras.get("listingId", "")
            return f"attempted to buy item {listing_id} from the market"

        elif action.type == ActionType.THINK:
            thoughts = action.get("thoughts", "")
            extras = deepcopy(action.get("extras", ""))
            del extras["thoughts"]
            extras = f"({extras}" if len(extras) else ""
            return f"spent the day thinking: \"_{thoughts}_{extras}\""

        return f"performed an unknown action ({action.type})"

    def _generate_fallback_summary(self, state: SimulationState) -> DailySummaryResponse:
        """Create a fallback summary when LLM generation fails"""
        day_titles = [
            "Red Dust and Credits [FALLBACK]",
            "Martian Marketplace Moves [FALLBACK]",
            "Settlement Commerce Continues [FALLBACK]",
            "Survival and Scarcity [FALLBACK]",
            "Mushrooms and Matters [FALLBACK]",
            "Another Sol, Another Dollar [FALLBACK]",
            "Martian Market Matters [FALLBACK]"
        ]

        # Get agent with lowest needs
        agents_by_need = sorted(state.agents, key=lambda a: min(a.needs.food, a.needs.rest, a.needs.fun))
        struggling_agent = agents_by_need[0] if agents_by_need else None

        # Get agent with most credits
        wealthy_agent = max(state.agents, key=lambda a: a.credits) if state.agents else None

        summary_text = f"[FALLBACK NARRATIVE] Day {state.day} on Mars saw the settlement continuing their economic activities. "

        if struggling_agent:
            lowest_need = min(struggling_agent.needs.food, struggling_agent.needs.rest, struggling_agent.needs.fun)
            need_type = "food" if lowest_need == struggling_agent.needs.food else "rest" if lowest_need == struggling_agent.needs.rest else "fun"
            summary_text += f"{struggling_agent.name} struggled with low {need_type} levels. "

        if wealthy_agent:
            summary_text += f"{wealthy_agent.name} has accumulated the most credits at {wealthy_agent.credits}. "

        # Add market info
        market_size = len(state.market.listings)
        if market_size > 0:
            summary_text += f"The market had {market_size} active listings. "
        else:
            summary_text += "The market remained quiet with no new listings. "

        # Add deaths if any
        today_deaths = [a for a in state.dead_agents if a.death_day == state.day]
        if today_deaths:
            death_names = [a.name for a in today_deaths]
            summary_text += f"Tragically, {', '.join(death_names)} did not survive the day. "

        return DailySummaryResponse(
            title=random.choice(day_titles),
            content=summary_text,
        )
