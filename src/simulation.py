"""
ProtoNomia Simulation Core
This module contains the main simulation logic for ProtoNomia.
"""
import json
import logging
import os
import random
import time
import uuid
from copy import deepcopy
from typing import List, Optional, Dict, Any

import click
from pydantic import ValidationError

from src.agent import LLMAgent
from src.generators import generate_personality, generate_mars_craft_options
from src.models import (Agent, AgentPersonality, ActionType, AgentNeeds, Good, GoodType, SimulationState,
                        AgentActionResponse, AgentAction, History, MarketListing)
from src.narrator import Narrator
from src.scribe import Scribe
from src.settings import DEFAULT_LM, LLM_MAX_RETRIES

# Initialize logger
logger = logging.getLogger(__name__)


class Simulation:
    """
    The main simulation class for ProtoNomia.
    Handles the simulation state, agent actions, and progression of time.
    """

    def __init__(
            self,
            num_agents: int = 5,
            max_days: int = 30,
            starting_credits: Optional[int] = None,
            model_name: str = DEFAULT_LM,
            output_dir: str = "../output",
            temperature: float = 0.7,
            top_p: float = 0.9,
            top_k: int = 40,
            max_retries: int = 3,
            retry_delay: int = 30
    ):
        """
        Initialize the simulation with the specified parameters.

        Args:
            num_agents: Number of agents to populate the simulation
            max_days: Maximum number of days to run the simulation
            model_name: Name of the LLM model to use
            output_dir: Directory to store simulation output
            temperature: Model temperature
            top_p: Top-p sampling parameter
            top_k: Top-k sampling parameter
            max_retries: Maximum retries for agent actions
            retry_delay: Delay in seconds between retries
        """
        self.num_agents = num_agents
        self.max_days = max_days
        self.model_name = model_name
        self.output_dir = output_dir
        self.temperature = temperature
        self.top_p = top_p
        self.top_k = top_k
        self.state: SimulationState = self._setup_initial_state(starting_credits=starting_credits)
        self.history: History = History()
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        # Initialize the scribe for rich text output
        self.scribe = Scribe()

        # Initialize the LLM agent for all agent decision making
        self.llm_agent = LLMAgent(
            model_name=model_name,
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
            max_retries=max_retries
        )

        # Initialize the narrator for generating narrative descriptions
        self.narrator = Narrator(
            model_name=model_name,
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
            max_retries=max_retries
        )

        self._craft_options = generate_mars_craft_options()

        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        logger.info(f"Initialized simulation with {num_agents} agents for {max_days} days using model {model_name}")

    def _create_agent(self, name: str = None, id=f"{uuid.uuid4()}", age_days=random.randint(30, 100),
                      personality_str: str = None,
                      needs: AgentNeeds = AgentNeeds(food=random.uniform(0.6, 0.9), rest=random.uniform(0.6, 0.9),
                                                     fun=random.uniform(0.5, 0.8)), starting_credits=None,
                      goods=None) -> Agent:
        if starting_credits is None:
            starting_credits = random.uniform(2000, 500000)
            if random.random() < 0.9:
                starting_credits /= 10
                if random.random() < 0.9:
                    starting_credits /= 10
        if not goods:
            goods = self._generate_starting_goods()
        if not name:
            name = self.generate_name()
        if not personality_str:
            personality_str = generate_personality()

        new_agent = Agent(id=id, name=name, age_days=age_days,
                          personality=AgentPersonality(personality=personality_str), credits=starting_credits,
                          needs=needs,
                          goods=goods)
        return new_agent

    def _add_agent(self, agent: Agent):
        self.state.agents.append(agent)

    def _setup_initial_state(self, starting_credits: Optional[int] = None) -> SimulationState:
        """
        Set up the initial simulation state with agents and market.

        Returns:
            SimulationState: The initialized simulation state
        """
        # Create initial set of agents
        agents = []

        for i in range(self.num_agents):
            # Create agent with random personality and starting credits
            agents.append(self._create_agent(starting_credits=starting_credits))

        # Create initial simulation state
        state = SimulationState(
            day=1,
            agents=agents,
            market=self._setup_market(),
        )
        return state

    def _generate_starting_goods(self) -> List[Good]:
        """
        Generate starting goods for a new agent.

        Returns:
            List[Good]: A list of goods for the agent
        """
        goods = []
        # 50% chance to have a food item
        if random.random() < 0.5:
            goods.append(Good(
                name="Martian Mushrooms",
                type=GoodType.FOOD,
                quality=random.uniform(0.3, 0.8)
            ))

        # 30% chance to have entertainment
        if random.random() < 0.3:
            goods.append(Good(
                name="Basic TV",
                type=GoodType.FUN,
                quality=random.uniform(0.2, 0.6)
            ))

        # 20% chance to have a rest item
        if random.random() < 0.2:
            goods.append(Good(
                name="Pillow",
                type=GoodType.REST,
                quality=random.uniform(0.4, 0.7)
            ))

        return goods

    def _setup_market(self) -> Dict:
        """
        Set up the initial market for the simulation.

        Returns:
            Dict: The market data structure
        """
        # Simple market structure with listings
        return {
            "listings": []
        }

    def run(self) -> None:
        """
        Run the simulation for the specified number of days.
        This is the main loop that advances time and processes agent actions.
        """
        logger.info(f"Starting simulation with {len(self.state.agents)} agents")
        # Display rich welcome message
        self.scribe.simulation_start(len(self.state.agents), self.max_days)

        # Main simulation loop
        while self.state.day <= self.max_days:
            # Process each day of the simulation
            self._process_day()

            # Save the current state
            self._save_state()
            self.history.add(self.state)
            self._save_history()

            # Move to the next day
            self.state.day += 1

        logger.info(f"Simulation completed after {self.max_days} days")
        # Display rich completion message
        self.scribe.simulation_end(self.max_days)

    def _process_day(self) -> None:
        """
        Process a single day in the simulation.
        This includes agent actions, market updates, and narratives.
        """
        logger.info(f"===== Day {self.state.day} =====")
        # Display rich day header
        self.scribe.day_header(self.state.day)

        # Decay agent needs at the start of the day
        self._decay_agent_needs()

        # Prepare for new inventions and ideas
        self.state.inventions[self.state.day] = []
        self.state.ideas[self.state.day] = []

        # Process agent actions
        agent_actions = self._process_agent_actions()

        # Generate daily narrative
        self._generate_daily_narrative(agent_actions)

        # Check for any dead agents and remove them
        self._check_agent_status()

    def _decay_agent_needs(self) -> None:
        """
        Reduce agent needs at the start of each day.
        """
        for agent in self.state.agents:
            # Reduce food and rest needs
            agent.needs.food = max(0, agent.needs.food - random.uniform(0.01, 0.02))
            agent.needs.rest = max(0, agent.needs.rest - random.uniform(0.01, 0.015))
            agent.needs.fun = max(0, agent.needs.fun - random.uniform(0.05, 0.1))

            # Log critically low needs
            if agent.needs.food < 0.2:
                logger.warning(f"{agent.name} has critically low food: {agent.needs.food:.2f}")
                food_items: list[Good] = [g for g in agent.goods if g.type == GoodType.FOOD]
                if food_items:
                    highest_quality = max(i.quality for i in food_items)
                    highest_food = [f for f in food_items if f.quality == highest_quality][0]
                    agent.items.remove(highest_food)
                    agent.needs.food += highest_quality
                    self.scribe.agent_eat(agent.name, highest_food.name, agent.needs.food, highest_quality)
                    logger.info(f"{agent.name} ate their {highest_food.name}, now at {agent.need.food}")
            if agent.needs.rest < 0.2:
                logger.warning(f"{agent.name} has critically low rest: {agent.needs.rest:.2f}")

    def _process_agent_actions(self) -> list[tuple[Agent, AgentAction]]:
        """
        Process actions for all agents.

        Returns:
            List[AgentAction]: List of agent actions taken
        """
        agent_actions = []

        for agent in self.state.agents:
            action = None
            retries = 0

            # Try to generate an action with retries
            while action is None and retries < self.max_retries:
                try:
                    # Generate action using LLM
                    logger.info(f"Generating action for {agent.name}")

                    # Get LLM response for agent action
                    response: AgentActionResponse = self.llm_agent.generate_action(agent, self.state)
                    logger.debug(f"Got a response: {type(response)} -> {response}")
                    self.scribe.agent_action(agent, response)
                    logger.info(f"{agent.name} performed action: {response.type}")

                    # Execute the action
                    action = self._execute_agent_action(agent, response)
                    logger.debug(f"Executed action: {type(action)} -> {action}")

                    # If successful, add to list of actions
                    if action:
                        agent_actions.append((agent, action))
                        agent.record(response)
                except ValidationError as validation_error:
                    logger.error(f"ValidationError: {validation_error.errors()}")
                    raise
                except Exception as e:
                    retries += 1
                    logger.error(
                        f"Error processing action for {agent.name} (attempt {retries}/{self.max_retries}): {e}")

                    if retries < self.max_retries:
                        logger.info(f"Retrying in {self.retry_delay} seconds...")
                        time.sleep(self.retry_delay)
                    else:
                        logger.error(f"Failed to generate action for {agent.name} after {self.max_retries} attempts")

                        # Use fallback action
                        try:
                            fallback_response: AgentActionResponse = self.llm_agent._fallback_action(agent)
                            action = self._execute_agent_action(agent, fallback_response)
                            if action:
                                agent_actions.append((agent, action))
                                # Use rich output for user-facing log
                                self.scribe.agent_action(agent, action)
                                logger.info(f"{agent.name} performed fallback action: {action.type}")
                                agent.record(fallback_response)
                        except Exception as fallback_error:
                            logger.error(f"Even fallback action failed for {agent.name}: {fallback_error}")
        return agent_actions

    def _execute_agent_action(self, agent: Agent, action_response: AgentActionResponse) -> AgentAction:
        """
        Execute an agent action and update the simulation state.

        Args:
            agent: The agent performing the action
            action_response: The action response from the LLM

        Returns:
            Optional[AgentAction]: The executed action or None if failed
        """
        action_type = action_response.type
        extras = action_response.extras or {}
        reasoning = action_response.reasoning or ""  # TODO: This is not clean, surely we can improve models

        logger.info(f"Agent {agent.name} chose action {action_type} with reasoning: {reasoning}")

        # Create a record of this action
        agent_action = AgentAction(
            agent_id=agent.id,
            day=self.state.day,
            type=action_type,
            extras=extras,
            reasoning=reasoning
        )

        # Execute the appropriate action based on type
        if action_type == ActionType.REST:
            self._execute_rest(agent)
        elif action_type == ActionType.WORK:
            self._execute_work(agent)
        elif action_type == ActionType.HARVEST:
            self._execute_harvest(agent)
        elif action_type == ActionType.CRAFT:
            self._execute_craft(agent, extras.get("goodType"), extras.get("name"), extras.get("materials"))
        elif action_type == ActionType.SELL:
            # Check if extras contains the required fields
            if "goodIndex" in extras and "price" in extras:
                good_index = extras.get("goodIndex")
                price = extras.get("price", 100)
                self._execute_sell(agent, good_index, price)
            else:
                logger.error(f"Missing required 'goodIndex' and 'price' fields for SELL action: {extras}")
        elif action_type == ActionType.BUY:
            # Check if extras contains the required fields
            if "listing_id" in extras:
                listing_id = extras.get("listing_id")
                self._execute_buy(agent, listing_id)
            else:
                logger.error(f"Missing required field 'listing_id' for BUY action: {extras}")
        elif action_type == ActionType.THINK:
            self._execute_think(agent, extras)
        else:
            logger.error(f"Unknown action type: {action_type}")

        return agent_action

    def _execute_rest(self, agent: Agent) -> None:
        """
        Execute REST action for an agent.

        Args:
            agent: The agent resting
        """
        # Increase rest by a fixed amount
        rest_amount = 0.5
        agent.needs.rest = min(1.0, agent.needs.rest + rest_amount)
        # Slightly increase fun
        agent.needs.fun = min(1.0, agent.needs.fun + 0.05)
        self.scribe.agent_rest(agent.name, agent.needs.rest, rest_amount)
        logger.info(f"{agent.name} rested and recovered energy. New rest: {agent.needs.rest:.2f}")

    def _execute_think(self, agent: Agent, extras: dict[str, Any]) -> None:
        """
        Execute REST action for an agent.

        Args:
            agent: The agent resting
        """
        # Increase rest by a small amount
        rest_amount = 0.1
        agent.needs.rest = min(1.0, agent.needs.rest + rest_amount)
        # Increase fun by random amount
        agent.needs.fun = min(1.0, agent.needs.fun + random.uniform(0.05, 0.5))

        thoughts: str = extras.get("thoughts", extras.get("thinking", json.dumps(extras) if extras else ""))
        self.state.ideas[self.state.day].append((agent, thoughts))
        self.scribe.agent_think(agent.name, thoughts, extras)
        logger.info(f"{agent.name} spent the day thinking: {thoughts}{extras}")

    def _execute_work(self, agent: Agent) -> None:
        """
        Execute WORK action for an agent.

        Args:
            agent: The agent working
        """
        # Fixed income for now
        income = 100
        agent.credits += income
        # Decrease rest due to work
        agent.needs.rest = max(0, agent.needs.rest - 0.1)
        # Slightly decrease fun from working
        agent.needs.fun = max(0, agent.needs.fun - 0.05)
        # Use rich output for user-facing log
        self.scribe.agent_work(agent.name, income, agent.credits)
        logger.info(f"{agent.name} worked and earned {income} credits. New credits: {agent.credits}")

    def _execute_harvest(self, agent: Agent) -> None:
        """
        Execute HARVEST action for an agent.

        Args:
            agent: The agent harvesting
        """
        # Create a food item with random quality
        quality = random.uniform(0.3, 0.9)
        food = Good(
            name="Martian Mushrooms",
            type=GoodType.FOOD,
            quality=quality
        )
        agent.goods.append(food)

        # Increase food by consuming some right away
        agent.needs.food = min(1.0, agent.needs.food + 0.15)
        # Decrease rest due to physical activity
        agent.needs.rest = max(0, agent.needs.rest - 0.1)
        # Use rich output for user-facing log
        self.scribe.agent_harvest(agent.name, food.name, quality, agent.needs.food)
        logger.info(
            f"{agent.name} harvested mushrooms (quality: {quality:.2f}). "
            f"New food level: {agent.needs.food:.2f}"
        )

    def _execute_craft(self, agent: Agent, good_type: GoodType, name: str = None, materials_cost: int = 0) -> None:
        """
        Execute CRAFT action for an agent.

        Args:
            agent: The agent crafting
            materials_cost: Amount to spend on materials
        """
        # Validate materials cost
        if materials_cost < 0:
            materials_cost = 0
        if materials_cost > agent.credits:
            logger.warning(f"Agent {agent.name} tried to spend {materials_cost} but has only {agent.credits}. "
                           f"Going all in with cost={agent.credits}!")
            materials_cost = agent.credits

        # Deduct the cost
        agent.credits -= materials_cost

        # Quality influenced by materials and a random factor
        base_quality = 0.3
        materials_quality = materials_cost / 200  # Max 0.5 from materials
        random_quality = random.uniform(0, 0.2)
        quality = min(1.0, base_quality + materials_quality + random_quality)

        # Create and add the item
        item = Good(
            name=name,
            type=good_type,
            quality=quality
        )
        agent.goods.append(item)
        self.state.inventions[self.state.day].append((agent, item))

        # Decrease rest and food, increase fun slightly
        agent.needs.rest = max(0, agent.needs.rest - 0.1)
        agent.needs.food = max(0, agent.needs.food - 0.05)
        agent.needs.fun = min(1.0, agent.needs.fun + 0.1)

        # Use rich output for user-facing log
        self.scribe.agent_craft(agent.name, item.name, item.type.value, quality, materials_cost)
        logger.info(
            f"{agent.name} crafted {item.name} ({item.type.value}, quality: {quality:.2f}) "
            f"using {materials_cost} credits worth of materials."
        )

    def _execute_sell(self, agent: Agent, good_index: int, price: int) -> None:
        """
        Execute SELL action for an agent.

        Args:
            agent: The agent selling
            good_index: Index of the good in the agent's inventory
            price: Asking price for the good
        """
        # Validate good index
        if good_index < 0 or good_index >= len(agent.goods):
            logger.error(f"Invalid good index {good_index} for {agent.name} with {len(agent.goods)} goods")
            return

        # Validate price
        if price <= 0:
            logger.error(f"Invalid price {price} set by {agent.name}")
            return

        # Get the good and create a listing
        good = agent.goods.pop(good_index)
        listing = {
            "id": str(uuid.uuid4()),
            "seller_id": agent.id,
            "good": good,
            "price": price,
            "created_at": time.time()
        }
        listing = MarketListing(**listing)

        # Add to market listings
        self.state.market.listings.append(listing)

        # Slightly decrease food and rest, increase fun
        agent.needs.food = max(0, agent.needs.food - 0.05)
        agent.needs.rest = max(0, agent.needs.rest - 0.05)
        agent.needs.fun = min(1.0, agent.needs.fun + 0.1)

        # Use rich output for user-facing log
        self.scribe.agent_sell(agent.name, good.name, good.type.value, good.quality, price)
        logger.info(
            f"{agent.name} listed {good.name} ({good.type.value}, quality: {good.quality:.2f}) "
            f"for sale at {price} credits"
        )

    def _execute_buy(self, agent: Agent, listing_id: str) -> None:
        """
        Execute BUY action for an agent.

        Args:
            agent: The agent buying
            listing_id: ID of the market listing to buy
        """
        # Find the listing
        listing_index = -1
        listing = None
        for i, lst in enumerate(self.state.market["listings"]):
            if lst["id"] == listing_id:
                listing_index = i
                listing = lst
                break

        # Handle "random" listing ID (choose an affordable one if possible)
        if listing_id == "random":
            affordable_listings = []
            for i, lst in enumerate(self.state.market["listings"]):
                if lst["price"] <= agent.credits:
                    affordable_listings.append((i, lst))

            if affordable_listings:
                listing_index, listing = random.choice(affordable_listings)
            elif self.state.market["listings"]:
                # Just pick a random one if none are affordable
                listing_index = random.randint(0, len(self.state.market["listings"]) - 1)
                listing = self.state.market["listings"][listing_index]

        # Validate listing exists
        if listing is None:
            logger.error(f"No listing found with ID {listing_id} for {agent.name} to buy")
            return

        # Check if agent has enough credits
        if agent.credits < listing["price"]:
            logger.error(
                f"{agent.name} cannot afford {listing['good'].name} at {listing['price']} credits "
                f"(has {agent.credits})"
            )
            return

        # Check if agent is buying their own listing
        if listing["seller_id"] == agent.id:
            logger.error(f"{agent.name} attempted to buy their own listing")
            return

        # Process the purchase
        agent.credits -= listing["price"]
        agent.goods.append(listing["good"])

        # Find the seller and give them the credits
        for seller in self.state.agents:
            if seller.id == listing["seller_id"]:
                seller.credits += listing["price"]
                # Use rich output for user-facing log
                self.scribe.agent_sale(seller.name, listing["price"])
                logger.info(f"{seller.name} received {listing['price']} credits from sale")
                break

        # Remove the listing from the market
        self.state.market["listings"].pop(listing_index)

        # Update agent needs based on what they bought
        good_type = listing["good"].type
        if good_type == GoodType.FOOD:
            # Consuming some of the food
            agent.needs.food = min(1.0, agent.needs.food + 0.2)
        elif good_type == GoodType.FUN:
            # Luxury increases fun
            agent.needs.fun = min(1.0, agent.needs.fun + 0.25)

        # Slightly decrease rest from shopping
        agent.needs.rest = max(0, agent.needs.rest - 0.05)

        # Use rich output for user-facing log
        self.scribe.agent_buy(
            agent.name,
            listing["good"].name,
            listing["good"].type.value,
            listing["good"].quality,
            listing["price"]
        )
        logger.info(
            f"{agent.name} bought {listing['good'].name} ({listing['good'].type.value}, "
            f"quality: {listing['good'].quality:.2f}) for {listing['price']} credits"
        )

    def _generate_daily_narrative(self, agent_actions: list[tuple[Agent, AgentAction]]) -> None:
        """
        Generate a narrative description of the day's events.

        Args:
            agent_actions: List of (agent, agent actions) taken during the day
        """
        # Generate the narrative using the Narrator
        try:
            narrative = self.narrator.generate_daily_summary(self.state)
            # Use rich markdown formatting for the narrative
            self.scribe.narrative_title(narrative.title)
            self.scribe.narrative_content(narrative.content, self.state)

            logger.info(f"Day {self.state.day} Narrative: {narrative.title}\n{narrative.content}")

            # Save narrative to file
            narrative_file = os.path.join(self.output_dir, f"day_{self.state.day}_narrative.txt")
            with open(narrative_file, 'w') as f:
                f.write(f"# {narrative.title}\n\n")
                f.write(narrative.content)

            # Try to generate a daily summary
            try:
                summary = self.narrator.generate_daily_summary(self.state)
                logger.info(f"Generated daily summary for day {self.state.day}")

                # Save summary to file
                summary_file = os.path.join(self.output_dir, f"day_{self.state.day}_summary.txt")
                with open(summary_file, 'w') as f:
                    f.write(f"# Day {self.state.day} Summary\n\n")
                    f.write(summary.content)

            except Exception as e:
                logger.error(f"Failed to generate daily summary: {e}")

        except Exception as e:
            logger.error(f"Failed to generate narrative: {e}")

    def _check_agent_status(self) -> None:
        """
        Check the status of all agents and handle any dead agents.
        """
        # Check for agents with critical needs
        agents_to_remove = []
        for agent in self.state.agents:
            # Agent is dead if food reaches 0
            if agent.needs.food <= 0:
                # Use rich output for user-facing log
                self.scribe.agent_death(agent.name, "starvation")
                logger.warning(f"{agent.name} has died due to starvation")
                agents_to_remove.append(agent)

        # Remove dead agents
        for agent in agents_to_remove:
            self.state.agents.remove(agent)

            # Add any goods to the market at a discount
            for good in agent.goods:
                base_price = int(good.quality * 100)
                discounted_price = int(base_price * 0.7)  # 30% discount

                listing = {
                    "id": str(uuid.uuid4()),
                    "seller_id": "settlement",  # Settlement selling deceased agent's goods
                    "good": good,
                    "price": discounted_price,
                    "created_at": time.time()
                }
                self.state.market["listings"].append(listing)
                # Use rich output for user-facing log
                self.scribe.deceased_good_added(good.name, agent.name, discounted_price)
                logger.info(f"Added {good.name} from deceased {agent.name} to market for {discounted_price} credits")

    def _save_history(self) -> None:
        """
        Save the current simulation state to a file.
        """
        # Save to file
        history_file = os.path.join(self.output_dir, f"history.json")
        with open(history_file, 'w') as f:
            f.write(self.history.model_dump_json(indent=0))

        logger.info(f"Saved simulation state for day {self.state.day}")

    def _save_state(self) -> None:
        """
        Save the current simulation state to a file.
        """
        state_file = os.path.join(self.output_dir, f"day_{self.state.day}_state.json")
        with open(state_file, 'w') as f:
            json.dump(self.state.model_dump_json(), f, indent=2)

        logger.info(f"Saved simulation state for day {self.state.day}")

    def generate_name(self) -> str:
        """
        Generates a new, unique name.
        Combines diverse, global, and futuristic names representing human and transhuman identities.
        """
        # Diverse first names from various cultural backgrounds, including futuristic and AI-inspired names
        first_names = [
            # Human names from different cultures
            "Aisha", "Carlos", "Elena", "Hiroshi", "Kwame", "Maria", "Nikolai", "Priya", "Sanjay", "Zara",
            # Futuristic/Sci-fi inspired names
            "Nova", "Orion", "Aria", "Zephyr", "Kai", "Luna", "Phoenix", "Stellar", "Cosmo", "Nebula",
            # AI/Transhuman inspired names
            "Cipher", "Echo", "Nexus", "Quantum", "Synth", "Vector", "Pixel", "Cipher", "Datastream", "Neuron"
        ]

        # Last names with a mix of cultural, scientific, and futuristic themes
        last_names = [
            # Traditional surnames
            "Rodriguez", "Chen", "Okonkwo", "Singh", "Kim", "Petrov", "Martinez", "Hassan", "Mueller", "Nakamura",
            # Scientific/Technological surnames
            "Quantum", "Starr", "Nova", "Circuit", "Fusion", "Horizon", "Neutron", "Cosmos", "Binary", "Pulse",
            # Mars/Space-themed surnames
            "Armstrong", "Aldrin", "Bradbury", "Clarke", "Sagan", "Musk", "Tsiolkovsky", "Glenn", "Gagarin", "Kepler"
        ]

        # Try to generate a unique name
        all_names = []
        for first_name in first_names:
            for last_name in last_names:
                name = f"{first_name} {last_name}"
                all_names.append(name)

        # Shuffle the names
        random.shuffle(all_names)

        # Try to generate a unique name
        for name in all_names:
            if not hasattr(self, 'state') or name not in [a.name for a in self.state.agents]:
                return name

        # Fallback with a numbered citizen name if all combinations are used
        base_name = "Citizen"
        counter = 1
        while any(a.name == f"{base_name} {counter}" for a in self.state.agents):
            counter += 1
        return f"{base_name} {counter}"


@click.command(context_settings=dict(help_option_names=["-h", "--help"]))
@click.option('-n', '--agents', default=5, help='Number of agents in the simulation')
@click.option('-d', '--days', default=30, help='Number of days to run the simulation')
@click.option('-c', '--credits', default=None, help='Number of credits each agent starts with (default: random wealth)')
@click.option('-m', '--model', default=DEFAULT_LM, help='LLM model to use')
@click.option('-o', '--output', default='output', help='Output directory')
@click.option('-t', '--temperature', default=0.7, help='LLM temperature')
@click.option('-l', '--log-level', default='ERROR', help='Logging level (DEBUG, INFO, WARNING, ERROR)')
def main(agents, days, credits, model, output, temperature, log_level):
    """Run the ProtoNomia economic simulation."""
    # Configure logging
    log_level = getattr(logging, log_level.upper())
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            # logging.FileHandler(os.path.join(output, 'simulation.log'))
        ]
    )

    # Create and run the simulation
    sim = Simulation(
        num_agents=agents,
        max_days=days,
        starting_credits=credits,
        model_name=model,
        output_dir=output,
        temperature=temperature,
        max_retries=LLM_MAX_RETRIES,
        retry_delay=5
    )
    sim.run()

    # Print completion message
    click.echo(f"Simulation completed after {days} days. Output saved to {output}/")


if __name__ == "__main__":
    main()
