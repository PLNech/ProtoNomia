"""
ProtoNomia Simulation Engine
This module contains the main simulation logic for ProtoNomia, refactored to run headless.
"""
import json
import logging
import os
import random
import string
import time
import uuid
from copy import deepcopy
from typing import List, Optional, Dict, Any, Tuple

from pydantic import ValidationError

from src.models import (
    Agent, AgentPersonality, ActionType, AgentNeeds, Good, GoodType, GlobalMarket, SimulationState,
    AgentActionResponse, AgentAction, History, Song, SimulationStage, NightActivity, Letter
)
from src.agent import LLMAgent
from src.generators import generate_personality, generate_mars_craft_options
from src.narrator import Narrator
from src.settings import DEFAULT_LM

# Initialize logger
logger = logging.getLogger(__name__)


class SimulationEngine:
    """
    The main simulation engine for ProtoNomia.
    Handles the simulation state, agent actions, and progression of time.
    """

    def __init__(
            self,
            simulation_id: Optional[str] = None,
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
            simulation_id: Unique identifier for this simulation
            num_agents: Number of agents to populate the simulation
            max_days: Maximum number of days to run the simulation
            starting_credits: Optional starting credits for agents
            model_name: Name of the LLM model to use
            output_dir: Directory to store simulation output
            temperature: Model temperature
            top_p: Top-p sampling parameter
            top_k: Top-k sampling parameter
            max_retries: Maximum retries for agent actions
            retry_delay: Delay in seconds between retries
        """
        self.simulation_id = simulation_id or str(uuid.uuid4())
        self.num_agents = num_agents
        self.max_days = max_days
        self.model_name = model_name
        self.output_dir = output_dir
        self.temperature = temperature
        self.top_p = top_p
        self.top_k = top_k
        self.starting_credits = starting_credits
        self.state: SimulationState = SimulationState()
        self.history: History = History()
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
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
        
    def create_agent(self, name: str = None, id: str = None, age_days: int = None,
                    personality_str: str = None, needs: AgentNeeds = None, 
                    starting_credits: Optional[int] = None, goods: List[Good] = None) -> Agent:
        """
        Create a new agent with the specified parameters or random values.

        Args:
            name: Agent name (random if None)
            id: Agent ID (random UUID if None)
            age_days: Agent age in days (random 30-100 if None)
            personality_str: Personality string (random if None)
            needs: Agent needs (random if None)
            starting_credits: Starting credits (random if None)
            goods: Initial goods (random if None)

        Returns:
            Agent: The newly created agent
        """
        # Use defaults for any unspecified parameters
        if id is None:
            id = str(uuid.uuid4())
        if age_days is None:
            age_days = random.randint(30, 100)
        if needs is None:
            needs = AgentNeeds(
                food=random.uniform(0.6, 0.9),
                rest=random.uniform(0.6, 0.9),
                fun=random.uniform(0.5, 0.8)
            )
        if starting_credits is None:
            starting_credits = self.starting_credits or self._generate_random_credits()
        if goods is None:
            goods = self._generate_starting_goods()
        if name is None:
            name = self._generate_name()
        if personality_str is None:
            personality_str = generate_personality()

        # Create the agent
        new_agent = Agent(
            id=id,
            name=name,
            age_days=age_days,
            personality=AgentPersonality(text=personality_str),
            credits=starting_credits,
            needs=needs,
            goods=goods
        )
        logger.info(f"Generated agent {name}: {personality_str}, needs: {needs}, goods: {goods}")
        return new_agent

    def add_agent(self, agent: Agent) -> None:
        """
        Add an agent to the simulation.

        Args:
            agent: The agent to add
        """
        self.state.agents.append(agent)
        logger.info(f"Added agent {agent.name} to simulation")

    def setup_initial_state(self) -> SimulationState:
        """
        Set up the initial simulation state with agents and market.

        Returns:
            SimulationState: The initialized simulation state
        """
        # Create initial set of agents
        agents = []
        for i in range(self.num_agents):
            # Create agent with random personality and starting credits
            agents.append(self.create_agent(starting_credits=self.starting_credits))

        # Create initial simulation state
        self.state = SimulationState(
            day=1,
            agents=agents,
            market=self._setup_market(),
        )
        return self.state

    def _generate_random_credits(self) -> float:
        """
        Generate a random amount of starting credits with a realistic distribution.

        Returns:
            float: Random credit amount
        """
        credits = random.uniform(2000, 500000)
        if random.random() < 0.9:
            credits /= 10
            if random.random() < 0.9:
                credits /= 10
        return credits

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

    def _setup_market(self) -> GlobalMarket:
        """
        Set up the initial market for the simulation.

        Returns:
            GlobalMarket: The market data structure
        """
        # Simple market structure with listings
        return GlobalMarket()
    
    def _generate_name(self) -> str:
        """
        Generates a new, unique name.
        Combines diverse, global, and futuristic names representing human and transhuman identities.
        """
        # Diverse first names from various cultural backgrounds, including futuristic and AI-inspired names
        first_names = [
            # Human names from different cultures
            "Aisha", "Carlos", "Elena", "Hiroshi", "Kwame", "Maria", "Nikolai", "Priya", "Sanjay", "Zara",
            "Liam", "Olivia", "Noah", "Emma", "Ethan", "Ava", "Mason", "Sophia", "William", "Isabella",
            "Yuki", "Ravi", "Fatima", "Jamal", "Ingrid", "Dmitri", "Amara", "Mateo", "Zoe", "Kai",
            # Futuristic/Sci-fi inspired names
            "Nova", "Orion", "Aria", "Zephyr", "Kai", "Luna", "Phoenix", "Stellar", "Cosmo", "Nebula",
            "Aether", "Cygnus", "Lyra", "Vega", "Atlas", "Andromeda", "Sirius", "Celeste", "Zenith", "Astro",
            # AI/Transhuman inspired names
            "Cipher", "Echo", "Nexus", "Quantum", "Synth", "Vector", "Pixel", "Cipher", "Datastream", "Neuron",
            "Binary", "Cortex", "Matrix", "Nano", "Qubit", "Axiom", "Cypher", "Helix", "Omega", "Zen"
        ]

        # Last names with a mix of cultural, scientific, and futuristic themes
        last_names = [
            # Traditional surnames
            "Rodriguez", "Chen", "Okonkwo", "Singh", "Kim", "Petrov", "Martinez", "Hassan", "Mueller", "Nakamura",
            "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Wilson", "Taylor",
            "Anderson", "Thomas", "Jackson", "White", "Harris", "Martin", "Thompson", "Moore", "Young", "Allen",
            # Scientific/Technological surnames
            "Quantum", "Starr", "Nova", "Circuit", "Fusion", "Horizon", "Neutron", "Cosmos", "Binary", "Pulse",
            "Tesla", "Edison", "Curie", "Darwin", "Hawking", "Bohr", "Feynman", "Planck", "Heisenberg", "Schrodinger",
            # Mars/Space-themed surnames
            "Armstrong", "Aldrin", "Bradbury", "Clarke", "Sagan", "Musk", "Tsiolkovsky", "Glenn", "Gagarin", "Kepler",
            "Hubble", "Curiosity", "Opportunity", "Perseverance", "Voyager", "Cassini", "Huygens", "Galileo", "Copernicus", "Tycho"
        ]

        # Optional titles or prefixes
        titles = [
            "", "Dr.", "Prof.", "Cmdr.", "Capt.", "Lt.", "Sgt.", "Adm.", "Gen.", "Ambassador",
            "Councilor", "Elder", "Overseer", "Architect", "Innovator", "Pioneer", "Visionary"
        ]

        # Optional suffixes
        suffixes = [
            "", "Jr.", "Sr.", "III", "IV", "V", "PhD", "MD", "Esq.", "AI",
            "Prime", "Alpha", "Omega", "Zero", "Infinity", "Nexus", "Core"
        ]

        def generate_unique_name():
            title = random.choice(titles)
            first = random.choice(first_names)
            last = random.choice(last_names)
            suffix = random.choice(suffixes)
            
            # Randomly decide to use a middle initial
            if random.random() < 0.3:
                middle_initial = random.choice(string.ascii_uppercase) + "."
                name = f"{title} {first} {middle_initial} {last} {suffix}".strip()
            else:
                name = f"{title} {first} {last} {suffix}".strip()
            
            return name

        # Try to generate a unique name
        max_attempts = 100
        for _ in range(max_attempts):
            name = generate_unique_name()
            if not any(a.name == name for a in self.state.agents):
                return name

        # Fallback with a numbered citizen name if all combinations are used
        base_name = "Citizen"
        counter = 1
        while any(a.name == f"{base_name} {counter}" for a in self.state.agents):
            counter += 1
        return f"{base_name} {counter}"

    def run(self) -> SimulationState:
        """
        Run the simulation for the specified number of days.
        This is the main loop that advances time and processes agent actions.

        Returns:
            SimulationState: The final simulation state
        """
        logger.info(f"Starting simulation with {self.num_agents} agents")
        
        # Set up initial state if not already set up
        if not self.state.agents:
            self.setup_initial_state()

        # Main simulation loop
        while self.state.day <= self.max_days:
            # Process day and night phases
            self.process_day()
            
            # Process night activities after the day is complete
            self.process_night()

            # Save the current state to history
            self.history.add(deepcopy(self.state))

            # Save state to file
            self._save_state()

            # Move to the next day
            self.state.day += 1

        logger.info(f"Simulation completed after {self.max_days} days")
        return self.state

    def process_day(self) -> None:
        """
        Process a single day in the simulation.
        This handles each stage of the day: initialization, agent actions, and narrative.
        """
        logger.info(f"===== Day {self.state.day} =====")

        # Set the simulation stage to INITIALIZATION
        self.state.current_stage = SimulationStage.INITIALIZATION
        self.state.current_agent_id = None
        
        # Decay agent needs at the start of the day
        self._decay_agent_needs()
        
        # Process agent actions in stages
        agent_actions = self._process_day_stages()
        
        # Check for any dead agents and remove them
        self._check_agent_status()

    def _process_day_stages(self) -> List[Tuple[Agent, AgentAction]]:
        """
        Process each stage of the day simulation.
        
        Returns:
            List[Tuple[Agent, AgentAction]]: List of agent actions taken
        """
        agent_actions = []
        
        # Set stage to AGENT_DAY for agent actions
        self.state.current_stage = SimulationStage.AGENT_DAY
        
        # Process each agent's action one at a time
        while True:
            # Get the next agent that needs to act
            next_agent = self.state.get_next_agent_for_day()
            if not next_agent:
                # All agents have acted, move to narrative stage
                break
            
            # Set the current agent
            self.state.current_agent_id = next_agent.id
            logger.info(f"Processing day action for {next_agent.name}")
            
            try:
                # Generate and execute action for this agent
                action = self._process_agent_day_action(next_agent)
                if action:
                    agent_actions.append((next_agent, action))
            except Exception as e:
                logger.error(f"Error processing day action for {next_agent.name}: {e}")
        
        # All agents have acted, move to narrative stage
        self.state.current_stage = SimulationStage.NARRATOR
        self.state.current_agent_id = None
        
        # Generate the daily narrative
        self._generate_daily_narrative(agent_actions)
        
        return agent_actions

    def _process_agent_day_action(self, agent: Agent) -> Optional[AgentAction]:
        """
        Process a single agent's day action.
        
        Args:
            agent: The agent to process
            
        Returns:
            Optional[AgentAction]: The executed action or None if failed
        """
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
                
                logger.info(f"{agent.name} chose action {response.type}")
                
                # Execute the action
                action = self._execute_agent_action(agent, response)
                logger.debug(f"Executed action: {type(action)} -> {action}")
                
                # Record the action
                if action:
                    agent.record(response)
                    return action
                
            except ValidationError as validation_error:
                logger.error(f"ValidationError: {validation_error.errors()}")
                raise
            except Exception as e:
                retries += 1
                logger.error(
                    f"Error processing action for {agent.name} (attempt {retries}/{self.max_retries}): {type(e)} - {str(e)}")
                
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
                            agent.record(fallback_response)
                            return action
                    except Exception as fallback_error:
                        logger.error(f"Even fallback action failed for {agent.name}: {fallback_error}")
        
        return None

    def process_night(self) -> None:
        """
        Process night activities for all agents.
        This includes eating dinner, listening to music, and chatting with others.
        """
        logger.info(f"===== Night {self.state.day} =====")
        
        # Set the stage to AGENT_NIGHT
        self.state.current_stage = SimulationStage.AGENT_NIGHT
        
        # Process each agent's night activities one at a time
        while True:
            # Get the next agent that needs to complete night activities
            next_agent = self.state.get_next_agent_for_night()
            if not next_agent:
                # All agents have completed night activities
                break
            
            # Set the current agent
            self.state.current_agent_id = next_agent.id
            logger.info(f"Processing night activities for {next_agent.name}")
            
            try:
                # Process dinner for this agent
                self._process_agent_dinner(next_agent)
                
                # Process night activities for this agent
                self._process_agent_night_activities(next_agent)
            except Exception as e:
                logger.error(f"Error processing night activities for {next_agent.name}: {e}")
        
        # Reset stage and agent
        self.state.current_stage = SimulationStage.INITIALIZATION
        self.state.current_agent_id = None

    def _process_agent_dinner(self, agent: Agent) -> None:
        """
        Process dinner for an agent by consuming food items.
        
        Args:
            agent: The agent to process dinner for
        """
        logger.info(f"Processing dinner for {agent.name}")
        
        # Get a list of food items the agent has
        food_items = [good for good in agent.goods if good.type == GoodType.FOOD]
        
        # If the agent has food needs and food items, consume them
        if agent.needs.food < 0.95 and food_items:
            # Sort food items by quality (highest first)
            food_items.sort(key=lambda x: x.quality, reverse=True)
            
            # Consumed food items
            consumed_food = []
            
            # Consume food items until needs are met or no more items
            for food in food_items:
                # Check if needs are already met
                if agent.needs.food >= 0.95:
                    break
                
                # Remove the food item from the agent's inventory
                agent.goods.remove(food)
                
                # Add its quality to food need (max 1.0)
                current_food = agent.needs.food
                agent.needs.food = min(1.0, agent.needs.food + food.quality)
                
                # Add to consumed food
                consumed_food.append(food)
                
                # Log the consumption
                logger.info(f"{agent.name} ate {food.name} (quality: {food.quality:.2f}) - Food level: {current_food:.2f} -> {agent.needs.food:.2f}")
            
            # Create a night activity record for dinner
            if consumed_food:
                activity = NightActivity(
                    agent_id=agent.id,
                    day=self.state.day,
                    dinner_consumed=consumed_food
                )
                self.state.add_night_activity(activity)
        else:
            logger.info(f"{agent.name} did not eat dinner (food need: {agent.needs.food:.2f}, food items: {len(food_items)})")

    def _process_agent_night_activities(self, agent: Agent) -> None:
        """
        Process night activities (listening to music, chatting) for an agent.
        
        Args:
            agent: The agent to process night activities for
        """
        logger.info(f"Processing night activities for {agent.name}")
        
        # Create a basic night activity
        activity = NightActivity(
            agent_id=agent.id,
            day=self.state.day
        )
        
        # TODO: Implement LLM-based night activity generation
        # For now, use a simple implementation
        
        # Choose a song to listen to (if any exist)
        all_songs = []
        for day, entries in self.state.songs.history_data.items():
            for entry in entries:
                all_songs.append((entry.song, entry.agent))
        
        if all_songs:
            # Choose a random song
            chosen_song, song_agent = random.choice(all_songs)
            activity.song_choice_id = chosen_song.title
            logger.info(f"{agent.name} listened to '{chosen_song.title}' by {song_agent.name}")
            
            # Increase fun slightly
            agent.needs.fun = min(1.0, agent.needs.fun + 0.1)
        
        # Choose agents to chat with (1-3 agents, but not more than available)
        other_agents = [a for a in self.state.agents if a.id != agent.id]
        chat_count = min(len(other_agents), random.randint(1, 3))
        
        if chat_count > 0:
            # Choose random agents to chat with
            chat_agents = random.sample(other_agents, chat_count)
            
            # Generate letter for each recipient
            for recipient in chat_agents:
                # Generate a simple letter
                topics = ["the weather on Mars", "the latest settlement news", "philosophical questions", 
                         "funny stories", "plans for tomorrow", "favorite songs", "their day's activities"]
                topic = random.choice(topics)
                
                letter = Letter(
                    recipient_name=recipient.name,
                    title=f"Thoughts about {topic}",
                    message=f"Hey {recipient.name}, I've been thinking about {topic} lately. What's your take on it?"
                )
                
                # Add letter to night activity
                activity.letters.append(letter)
                
                # Log the letter
                logger.info(f"{agent.name} sent a letter to {recipient.name} about {topic}")
                
                # Increase fun for both participants
                agent.needs.fun = min(1.0, agent.needs.fun + 0.05)
                recipient.needs.fun = min(1.0, recipient.needs.fun + 0.05)
            
            # Log overall social activity
            if activity.letters:
                recipient_names = [letter.recipient_name for letter in activity.letters]
                logger.info(f"{agent.name} wrote letters to {', '.join(recipient_names)}")
        
        # Save the night activity
        self.state.add_night_activity(activity)

    def _decay_agent_needs(self) -> None:
        """
        Reduce agent needs at the start of each day.
        """
        for agent in self.state.agents:
            # Reduce food, rest, and fun needs
            agent.needs.food = max(0, agent.needs.food - random.uniform(0.01, 0.02))
            agent.needs.rest = max(0, agent.needs.rest - random.uniform(0.01, 0.015))
            agent.needs.fun = max(0, agent.needs.fun - random.uniform(0.05, 0.1))

            # Log critically low needs
            if agent.needs.food < 0.2:
                logger.warning(f"{agent.name} has critically low food: {agent.needs.food:.2f}")
                food_items: List[Good] = [g for g in agent.goods if g.type == GoodType.FOOD]
                if food_items:
                    highest_quality = max(i.quality for i in food_items)
                    highest_food = [f for f in food_items if f.quality == highest_quality][0]
                    agent.goods.remove(highest_food)
                    agent.needs.food += highest_quality
                    logger.info(f"{agent.name} ate their {highest_food.name}, now at {agent.needs.food}")
            if agent.needs.rest < 0.2:
                logger.warning(f"{agent.name} has critically low rest: {agent.needs.rest:.2f}")

    def _process_agent_actions(self) -> List[Tuple[Agent, AgentAction]]:
        """
        Process actions for all agents.

        Returns:
            List[Tuple[Agent, AgentAction]]: List of agent actions taken
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
                    
                    logger.info(f"{agent.name} chose action {response.type}")

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
                        f"Error processing action for {agent.name} (attempt {retries}/{self.max_retries}): {type(e)} - {str(e)}")

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
        reasoning = action_response.reasoning or ""

        logger.info(f"Agent {agent.name} is executing action {action_type} with reasoning: {reasoning}")

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
            if "goodName" in extras and "price" in extras:
                good_name = extras.get("goodName")
                price = extras.get("price", 100)
                self._execute_sell(agent, good_name, price)
            else:
                logger.error(f"Missing required 'goodName' and 'price' fields for SELL action: {extras}")
        elif action_type == ActionType.BUY:
            # Check if extras contains the required fields
            if "listingId" in extras:
                listing_id = extras.get("listingId")
                self._execute_buy(agent, listing_id)
            else:
                logger.error(f"Missing required field 'listingId' for BUY action: {extras}")
        elif action_type == ActionType.THINK:
            self._execute_think(agent, extras)
        elif action_type == ActionType.COMPOSE:
            self._execute_compose(agent, extras)
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
        logger.info(f"{agent.name} rested and recovered energy. New rest: {agent.needs.rest:.2f}")

    def _execute_think(self, agent: Agent, extras: Dict[str, Any]) -> None:
        """
        Execute THINK action for an agent.

        Args:
            agent: The agent thinking
            extras: Extra data for the think action
        """
        # Increase rest by a small amount
        rest_amount = 0.1
        agent.needs.rest = min(1.0, agent.needs.rest + rest_amount)
        # Increase fun by random amount
        agent.needs.fun = min(1.0, agent.needs.fun + random.uniform(0.05, 0.5))

        thoughts: str = extras.get("thoughts", extras.get("thinking", json.dumps(extras) if extras else ""))
        self.state.ideas[self.state.day].append((agent, thoughts))
        logger.info(f"{agent.name} spent the day thinking: {thoughts}")

    def _execute_compose(self, agent: Agent, extras: Dict[str, Any]) -> None:
        """
        Execute COMPOSE action for an agent.

        Args:
            agent: The agent composing
            extras: Extra data for the compose action
        """
        # Increase rest by a small amount
        rest_amount = 0.1
        agent.needs.rest = min(1.0, agent.needs.rest + rest_amount)
        # Increase fun by random medium-large amount
        agent.needs.fun = min(1.0, agent.needs.fun + random.uniform(0.25, 1))
        logger.info("Executing compose...")
        song: Song = Song(**extras)
        logger.info("Created song.")
        self.state.songs.add_song(agent, song, self.state.day)
        logger.info(f"{agent.name} created a new song: {song}")

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
        logger.info(
            f"{agent.name} harvested mushrooms (quality: {quality:.2f}). "
            f"New food level: {agent.needs.food:.2f}"
        )

    def _execute_craft(self, agent: Agent, good_type: GoodType, name: str = None, materials_cost: int = 0) -> None:
        """
        Execute CRAFT action for an agent.

        Args:
            agent: The agent crafting
            good_type: Type of good to craft
            name: Name of the crafted good
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

        logger.info(
            f"{agent.name} crafted {item.name} ({item.type.value}, quality: {quality:.2f}) "
            f"using {materials_cost} credits worth of materials."
        )

    def _execute_sell(self, agent: Agent, good_name: str = "random", price: int = 0) -> None:
        """
        Execute SELL action for an agent.

        Args:
            agent: The agent selling
            good_name: The name of the good to sell
            price: Asking price for the good
        """
        # Validate good name
        if not good_name or good_name == "random":
            if agent.goods:
                good = random.choice(agent.goods)
                good_name = good.name
            else:
                logger.error(f"Agent {agent.name} has no goods to sell")
                return

        # Validate price
        if price <= 0:
            logger.error(f"Invalid negative price {price} set by {agent.name} - listing for free!")
            price = 0

        try:
            # Find closest match with up to 2 char typo tolerance using Levenshtein distance
            good_name_lower = str(good_name).lower()
            min_distance = float('inf')
            good_index = -1
            
            for i, good in enumerate(agent.goods):
                distance = sum(1 for a, b in zip(good_name_lower, str(good.name).lower()) if a != b)
                distance += abs(len(good_name_lower) - len(str(good.name).lower()))
                if distance <= 2 and distance < min_distance:
                    min_distance = distance
                    good_index = i
            
            if good_index == -1:
                raise ValueError(f"No close match found for {good_name}")
                
            good: Good = agent.goods[good_index]

            # Add to market and remove from agent's inventory
            self.state.market.add_listing(agent.id, good, price, self.state.day)
            agent.goods.pop(good_index)

            # Slightly decrease food and rest, increase fun
            agent.needs.food = max(0, agent.needs.food - 0.05)
            agent.needs.rest = max(0, agent.needs.rest - 0.05)
            agent.needs.fun = min(1.0, agent.needs.fun + 0.1)

            logger.info(
                f"{agent.name} listed {good.name} ({good.type.value}, quality: {good.quality:.2f}) "
                f"for sale at {price} credits"
            )
        except ValueError:
            logger.error(f"Failed to find {good_name} in {agent.name}'s goods: {agent.goods}")

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
        for i, lst in enumerate(self.state.market.listings):
            if lst.id == listing_id:
                listing_index = i
                listing = lst
                break

        # Handle "random" listing ID (choose an affordable one if possible)
        if listing_id == "random":
            affordable_listings = []
            for i, lst in enumerate(self.state.market.listings):
                if lst.price <= agent.credits:
                    affordable_listings.append((i, lst))

            if affordable_listings:
                listing_index, listing = random.choice(affordable_listings)
            elif self.state.market.listings:
                # Just pick a random one if none are affordable
                listing_index = random.randint(0, len(self.state.market.listings) - 1)
                listing = self.state.market.listings[listing_index]

        # Validate listing exists
        if listing is None:
            logger.error(f"No listing found with ID {listing_id} for {agent.name} to buy")
            return

        # Check if agent has enough credits
        if agent.credits < listing.price:
            logger.error(
                f"{agent.name} cannot afford {listing.good.name} at {listing.price} credits "
                f"(has {agent.credits})"
            )
            return

        # Check if agent is buying their own listing
        if listing.seller_id == agent.id:
            logger.error(f"{agent.name} attempted to buy their own listing")
            return

        # Process the purchase
        agent.credits -= listing.price
        agent.goods.append(listing.good)

        # Find the seller and give them the credits
        for seller in self.state.agents:
            if seller.id == listing.seller_id:
                seller.credits += listing.price
                logger.info(f"{seller.name} received {listing.price} credits from sale")
                break

        # Remove the listing from the market
        self.state.market.listings.pop(listing_index)

        # Update agent needs based on what they bought
        good_type = listing.good.type
        if good_type == GoodType.FOOD:
            # Consuming some of the food
            agent.needs.food = min(1.0, agent.needs.food + 0.2)
        elif good_type == GoodType.FUN:
            # Luxury increases fun
            agent.needs.fun = min(1.0, agent.needs.fun + 0.25)

        # Slightly decrease rest from shopping
        agent.needs.rest = max(0, agent.needs.rest - 0.05)

        logger.info(
            f"{agent.name} bought {listing.good.name} ({listing.good.type.value}, "
            f"quality: {listing.good.quality:.2f}) for {listing.price} credits"
        )

    def _generate_daily_narrative(self, agent_actions: List[Tuple[Agent, AgentAction]]) -> None:
        """
        Generate a narrative description of the day's events.

        Args:
            agent_actions: List of (agent, agent actions) taken during the day
        """
        # Generate the narrative using the Narrator
        try:
            narrative = self.narrator.generate_daily_summary(self.state)
            logger.info(f"Day {self.state.day} Narrative: {narrative.title}\n{narrative.content}")

            # Save narrative to file
            narrative_file = os.path.join(self.output_dir, f"day_{self.state.day}_narrative.txt")
            with open(narrative_file, 'w') as f:
                f.write(f"# {narrative.title}\n\n")
                f.write(narrative.content)
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
                logger.warning(f"{agent.name} has died due to starvation")
                agents_to_remove.append(agent)

        # Remove dead agents
        for agent in agents_to_remove:
            self.state.agents.remove(agent)
            agent.is_alive = False
            agent.death_day = self.state.day
            self.state.dead_agents.append(agent)

            # Add any goods to the market at a discount
            for good in agent.goods:
                base_price = int(good.quality * 100)
                discounted_price = int(base_price * 0.7)  # 30% discount

                self.state.market.add_listing("settlement", good, discounted_price, self.state.day)
                logger.info(f"Added {good.name} from deceased {agent.name} to market for {discounted_price} credits")

    def _save_state(self) -> None:
        """
        Save the current simulation state to a file.
        """
        # Save to file
        state_file = os.path.join(self.output_dir, f"day_{self.state.day}_state.json")
        with open(state_file, 'w') as f:
            f.write(self.state.model_dump_json(indent=2))

        logger.info(f"Saved simulation state for day {self.state.day}")
        
    def get_agent_by_id(self, agent_id: str) -> Optional[Agent]:
        """
        Get an agent by ID.
        
        Args:
            agent_id: The ID of the agent to get
            
        Returns:
            Optional[Agent]: The agent or None if not found
        """
        for agent in self.state.agents:
            if agent.id == agent_id:
                return agent
        for agent in self.state.dead_agents:
            if agent.id == agent_id:
                return agent
        return None
    
    def get_agent_by_name(self, agent_name: str) -> Optional[Agent]:
        """
        Get an agent by name.
        
        Args:
            agent_name: The name of the agent to get
            
        Returns:
            Optional[Agent]: The agent or None if not found
        """
        for agent in self.state.agents:
            if agent.name == agent_name:
                return agent
        for agent in self.state.dead_agents:
            if agent.name == agent_name:
                return agent
        return None
    
    def kill_agent(self, agent: Agent) -> bool:
        """
        Kill an agent.
        
        Args:
            agent: The agent to kill
            
        Returns:
            bool: True if the agent was successfully killed
        """
        if agent in self.state.agents:
            self.state.agents.remove(agent)
            agent.is_alive = False
            agent.death_day = self.state.day
            self.state.dead_agents.append(agent)
            
            # Add any goods to the market at a discount
            for good in agent.goods:
                base_price = int(good.quality * 100)
                discounted_price = int(base_price * 0.7)  # 30% discount

                self.state.market.add_listing("settlement", good, discounted_price, self.state.day)
                logger.info(f"Added {good.name} from deceased {agent.name} to market for {discounted_price} credits")
            
            return True
        return False
    
    def update_agent(self, agent: Agent, updates: Dict[str, Any]) -> bool:
        """
        Update an agent with the given updates.
        
        Args:
            agent: The agent to update
            updates: Dictionary of updates to apply
            
        Returns:
            bool: True if the agent was successfully updated
        """
        if agent not in self.state.agents and agent not in self.state.dead_agents:
            return False
        
        # Apply updates
        if "credits" in updates:
            agent.credits = float(updates["credits"])
        
        if "needs" in updates:
            needs_updates = updates["needs"]
            if "food" in needs_updates:
                agent.needs.food = float(needs_updates["food"])
            if "rest" in needs_updates:
                agent.needs.rest = float(needs_updates["rest"])
            if "fun" in needs_updates:
                agent.needs.fun = float(needs_updates["fun"])
        
        if "goods" in updates:
            # Replace goods (should be a list of Good objects)
            agent.goods = [Good(**good) if isinstance(good, dict) else good for good in updates["goods"]]
            
        return True