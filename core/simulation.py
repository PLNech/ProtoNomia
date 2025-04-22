"""
Core simulation engine for ProtoNomia.
This module contains the main Simulation class that orchestrates the economic simulation.
"""
import logging
import random
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, Any, List, Tuple

# Import required modules
from agents.llm_agent import LLMAgent
from economics.economy_manager import EconomyManager
from economics.interactions.job_market import JobMarketHandler
from economics.interactions.goods_market import GoodsMarketHandler
from models.base import (
    Agent, AgentType, AgentFaction, AgentPersonality, ResourceBalance,
    ResourceType, EconomicInteraction,
    InteractionRole, SimulationConfig, SimulationState,
    NarrativeEvent, NarrativeArc, PopulationControlParams, AgentNeeds, ActionType, AgentDecisionContext, AgentAction
)
from models.economy import GoodsListing, JobListing, ListingType
from narrative.narrator import Narrator
from population.controller import PopulationController
from settings import DEFAULT_LM

# Initialize logger
logger = logging.getLogger(__name__)


class Simulation:
    """
    Main simulation engine for ProtoNomia.
    Handles the core simulation logic, including agent lifecycle, economic interactions,
    and narrative generation.
    """

    def __init__(
            self,
            config: SimulationConfig,
            use_llm: bool = True,
            model_name: str = DEFAULT_LM,
            narrator_model_name: str = DEFAULT_LM,
            temperature: float = 0.8,
            top_p: float = 0.95,
            top_k: int = 40
    ):
        """
        Initialize a new simulation.
        
        Args:
            config: Simulation configuration parameters
            use_llm: Whether to use LLM for agent decision making
            model_name: Name of the LLM model to use with Ollama for agents
            narrator_model_name: Name of the LLM model to use with Ollama for narration
            temperature: Controls randomness in LLM generation (0.0-1.0)
            top_p: Nucleus sampling probability threshold (0.0-1.0)
            top_k: Number of highest probability tokens to consider
        """
        self.config = config
        self.use_llm = use_llm
        self.model_name = model_name
        self.narrator_model_name = narrator_model_name
        self.temperature = temperature
        self.top_p = top_p
        self.top_k = top_k

        # Initialize agents, interactions, and other state variables
        self.agents: Dict[str, Agent] = {}
        self.interactions: Dict[str, EconomicInteraction] = {}
        self.narrative_events: Dict[str, NarrativeEvent] = {}
        self.narrative_arcs: Dict[str, NarrativeArc] = {}

        # Set up population control
        self.population_params = PopulationControlParams(
            birth_rate=0.01,
            death_rate=0.005,
            immigration_rate=0.002,
            emigration_rate=0.001,
            resource_sensitivity=0.5,
            max_age_days=36500  # 100 years in days
        )

        # Set random seed if provided
        if config.seed is not None:
            random.seed(config.seed)

        # Create initial simulation state
        self.state = SimulationState(
            config=config,
            current_date=config.start_date,
            current_tick=0,
            population_size=0,
            active_agents=[],
            deceased_agents=[],
            active_interactions=[],
            completed_interactions=[],
            narrative_events=[],
            narrative_arcs=[],
            economic_indicators={}
        )

        # Initialize required modules
        self._initialize_modules()

    def _initialize_modules(self):
        """Initialize all required modules for the simulation"""
        # Initialize the economy manager
        self.economy_manager = EconomyManager()
        logger.info("Initialized EconomyManager")

        # Initialize the population controller
        self.population_controller = PopulationController(self.population_params)
        logger.info("Initialized PopulationController")

        # Initialize agent module based on use_llm setting
        if self.use_llm:
            # Use LLM for agent decision making
            self.llm_agent = LLMAgent(
                model_name=self.model_name,
                temperature=self.temperature,
                top_p=self.top_p,
                top_k=self.top_k
            )
            logger.info(f"Initialized LLM agent with model {self.model_name}")

            # Use LLM for narrative generation
            logger.info(f"Initializing Narrator with model {self.narrator_model_name}")
            self.narrator = Narrator(
                verbosity=self.config.narrative_verbosity,
                model_name=self.narrator_model_name,
                temperature=self.temperature,
                top_p=self.top_p,
                top_k=self.top_k
            )
            logger.info(f"Initialized Narrator with model {self.narrator_model_name}")
        else:
            # Use rule-based agent decision making but still use the LLM-based narrator
            logger.info("Initializing Narrator")
            self.narrator = Narrator(
                verbosity=self.config.narrative_verbosity,
                model_name=self.narrator_model_name,
                temperature=self.temperature,
                top_p=self.top_p,
                top_k=self.top_k
            )
            logger.info(f"Initialized Narrator with verbosity {self.config.narrative_verbosity}")

            # No LLM agent needed for rule-based simulation
            self.llm_agent = None
            logger.info("Using rule-based agent decision making")

    def initialize(self):
        """Initialize the simulation by creating the initial population"""
        logger.info(f"Initializing simulation with {self.config.initial_population} agents")

        # Create initial agents
        for i in range(self.config.initial_population):
            agent = self._create_random_agent()
            self.agents[agent.id] = agent
            self.state.active_agents.append(agent.id)

        # Update state
        self.state.population_size = len(self.state.active_agents)
        self.state.current_tick = 0

        # Initialize economic indicators
        self._update_economic_indicators()

        logger.info(f"Simulation initialized with {self.state.population_size} agents")
        return self.state

    def step(self) -> SimulationState:
        """
        Execute one simulation step.
        
        Returns:
            SimulationState: The updated simulation state
        """
        tick_start = time.time()
        logger.debug(f"Starting simulation tick {self.state.current_tick}")

        # Advance time (1 day per tick)
        self.state.current_date += timedelta(days=1)
        self.state.current_tick += 1

        # Execute lifecycle events (births, deaths, etc.)
        self._process_lifecycle_events()

        # Process agent actions and interactions
        self._process_agent_actions()

        # Process economic activities
        self._process_economy()

        # Generate narrative events
        self._generate_narrative()

        # Update economic indicators
        self._update_economic_indicators()

        logger.debug(f"Completed tick {self.state.current_tick} in {time.time() - tick_start:.2f}s")
        return self.state

    def _create_random_agent(self) -> Agent:
        """Create a random agent for the simulation"""
        # Generate random personality traits
        personality = AgentPersonality(
            cooperativeness=random.uniform(0.1, 0.9),
            risk_tolerance=random.uniform(0.1, 0.9),
            fairness_preference=random.uniform(0.1, 0.9),
            altruism=random.uniform(0.1, 0.9),
            rationality=random.uniform(0.1, 0.9),
            long_term_orientation=random.uniform(0.1, 0.9)
        )

        # Choose random agent type (mostly individuals)
        agent_type_weights = [
            (AgentType.INDIVIDUAL, 0.8),
            (AgentType.CORPORATION, 0.1),
            (AgentType.COLLECTIVE, 0.05),
            (AgentType.GOVERNMENT, 0.03),
            (AgentType.AI, 0.02)
        ]
        agent_type = random.choices(
            [t[0] for t in agent_type_weights],
            weights=[t[1] for t in agent_type_weights],
            k=1
        )[0]

        # Choose random faction
        faction_weights = [
            (AgentFaction.TERRA_CORP, 0.3),
            (AgentFaction.MARS_NATIVE, 0.4),
            (AgentFaction.INDEPENDENT, 0.2),
            (AgentFaction.GOVERNMENT, 0.05),
            (AgentFaction.UNDERGROUND, 0.05)
        ]
        faction = random.choices(
            [f[0] for f in faction_weights],
            weights=[f[1] for f in faction_weights],
            k=1
        )[0]

        # Generate a name based on type and faction
        name = self._generate_agent_name(agent_type, faction)

        # Generate resources
        resources = [
            ResourceBalance(
                resource_type=ResourceType.CREDITS,
                amount=random.randint(100, 1000000)
            ),
            ResourceBalance(
                resource_type=ResourceType.PHYSICAL_GOODS,
                amount=random.randint(10, 100)
            ),
            ResourceBalance(
                resource_type=ResourceType.WATER,
                amount=random.randint(10, 100)
            ),
            ResourceBalance(
                resource_type=ResourceType.DIGITAL_GOODS,
                amount=random.randint(0, 50)
            )
        ]

        # Create the agent
        agent = Agent(
            id=f"agent_{len(self.agents) + 1}",
            name=name,
            agent_type=agent_type,
            faction=faction,
            personality=personality,
            birth_date=self.state.current_date - timedelta(days=random.randint(18 * 365, 65 * 365)),
            resources=resources,
            needs=AgentNeeds(
                subsistence=random.uniform(0.7, 1.0),
                security=random.uniform(0.5, 1.0),
                social=random.uniform(0.5, 1.0),
                esteem=random.uniform(0.5, 1.0),
                self_actualization=random.uniform(0.5, 1.0)
            ),
            location="Olympus Mons District"
        )

        return agent

    def _generate_agent_name(self, agent_type: AgentType, faction: AgentFaction) -> str:
        """Generate a name for an agent based on its type and faction"""
        if agent_type == AgentType.INDIVIDUAL:
            # Human name
            first_names = ["Alice", "Bob", "Charlie", "Diana", "Ethan", "Freya", "Gabriel",
                           "Hannah", "Isaac", "Julia", "Kai", "Luna", "Marco", "Nora",
                           "Orion", "Piper", "Quinn", "Ren", "Sasha", "Theo", "Uma",
                           "Victor", "Willow", "Xander", "Yuna", "Zane"]
            last_names = ["Smith", "Johnson", "Williams", "Jones", "Brown", "Davis", "Miller",
                          "Wilson", "Moore", "Taylor", "Anderson", "Thomas", "Jackson", "White",
                          "Harris", "Martin", "Thompson", "Garcia", "Martinez", "Robinson", "Clark",
                          "Rodriguez", "Lewis", "Lee", "Walker", "Hall", "Allen", "Young", "King"]

            # Add some faction influence to names
            if faction == AgentFaction.MARS_NATIVE:
                last_names.extend(["Olympus", "Ares", "Tharsis", "Mariner", "Valles", "Phobos", "Deimos"])
            elif faction == AgentFaction.TERRA_CORP:
                last_names.extend(["Earth", "Terra", "Luna", "Sol", "Pacific", "Atlantic", "Ridge"])
            elif faction == AgentFaction.UNDERGROUND:
                last_names.extend(["Weyland", "Tyrell", "Rosen", "Tessier", "Ashpool", "Zaibatsu"])

            return f"{random.choice(first_names)} {random.choice(last_names)}"

        elif agent_type == AgentType.CORPORATION:
            # Corporate name
            prefixes = ["Mars", "Red", "Olympus", "Tharsis", "Ares", "Deimos", "Phobos", "Terra",
                        "Cyber", "Quantum", "Stellar", "Neo", "Alpha", "Horizon", "Prime", "Apex"]
            suffixes = ["Corp", "Industries", "Dynamics", "Systems", "Tech", "Solutions", "Enterprises",
                        "Holdings", "Robotics", "AI", "Mining", "Exports", "Labs", "Ventures", "Collective"]

            return f"{random.choice(prefixes)} {random.choice(suffixes)}"

        elif agent_type == AgentType.COLLECTIVE:
            # Collective name
            adjectives = ["United", "Allied", "Autonomous", "Free", "Democratic", "Independent",
                          "Progressive", "Sustainable", "Cooperative", "Mutual", "Communal"]
            nouns = ["Workers", "Miners", "Farmers", "Engineers", "Colonists", "Citizens",
                     "Settlers", "Technicians", "Artisans", "Traders", "Hackers", "Pioneers"]

            return f"{random.choice(adjectives)} {random.choice(nouns)} Collective"

        elif agent_type == AgentType.GOVERNMENT:
            # Government name
            prefixes = ["Bureau of", "Ministry of", "Department of", "Office of", "Agency for",
                        "Commission on", "Authority for", "Division of"]
            domains = ["Colonial Affairs", "Resource Management", "Economic Development",
                       "Infrastructure", "Public Safety", "Health & Medicine", "Scientific Research",
                       "Educational Standards", "Interplanetary Relations", "Trade Regulation"]

            return f"{random.choice(prefixes)} {random.choice(domains)}"

        elif agent_type == AgentType.AI:
            # AI name
            prefixes = ["ARES", "OLYMPUS", "MARS", "TERRA", "CYDONIA", "PHOBOS", "DEIMOS",
                        "HELLAS", "ELYSIUM", "VALLES"]
            suffixes = ["OS", "AI", "MIND", "CORE", "NET", "MATRIX", "SYSTEM", "PROTOCOL",
                        "SENTINEL", "GUARDIAN", "NODE", "NEXUS", "PRIME", "ALPHA", "OMEGA"]

            return f"{random.choice(prefixes)}-{random.choice(suffixes)}"

        else:
            # Generic name
            return f"Agent {len(self.agents) + 1}"

    def _process_lifecycle_events(self):
        """Process agent lifecycle events (births, deaths, etc.)"""
        if self.population_controller:
            # Use the population controller to handle lifecycle events
            population_events, new_agents = self.population_controller.process_lifecycle_events(
                agents=self.agents,
                current_date=self.state.current_date,
                max_population=self.config.max_population
            )

            # Add any new agents from the controller
            for agent in new_agents:
                self.agents[agent.id] = agent
                self.state.active_agents.append(agent.id)
                logger.debug(f"New agent added: {agent.name} ({agent.id})")

            # Process population events
            for event in population_events:
                if event.event_type == "death":
                    # Mark agent as deceased
                    if event.agent_id in self.state.active_agents:
                        self.state.active_agents.remove(event.agent_id)
                        self.state.deceased_agents.append(event.agent_id)
                        logger.debug(f"Agent died: {self.agents[event.agent_id].name} ({event.agent_id})")
        else:
            # Simple lifecycle events without the controller
            self._simple_lifecycle_events()

    def _simple_lifecycle_events(self):
        """Simple lifecycle events when population controller is not available"""
        # Simple birth logic - add new agents if below population target
        if (len(self.state.active_agents) < self.config.max_population and
                random.random() < 0.05):  # 5% chance of birth per tick
            agent = self._create_random_agent()
            self.agents[agent.id] = agent
            self.state.active_agents.append(agent.id)
            logger.debug(f"New agent born: {agent.name} ({agent.id})")

        # Simple death logic - randomly remove agents
        if len(self.state.active_agents) > 0 and random.random() < 0.01:  # 1% chance of death per tick
            agent_id = random.choice(self.state.active_agents)
            self.state.active_agents.remove(agent_id)
            self.state.deceased_agents.append(agent_id)
            logger.debug(f"Agent died: {self.agents[agent_id].name} ({agent_id})")

    def _process_agent_actions(self):
        """Process agent actions for the current tick"""
        # For each active agent, generate and process an action
        for agent_id in self.state.active_agents:
            agent = self.agents[agent_id]

            # Generate an action for the agent
            action = self._generate_agent_action(agent)

            # Process the action if one was generated
            if action:
                self._process_action(action)

    def _process_economy(self):
        """Process economic activities and update market listings."""
        # Process active economic interactions
        self._process_active_interactions()
        
        # Update market listings based on current turn
        self.economy_manager.update_listings(self.state.current_tick)
        
        # Generate a market report for economic indicators
        market_report = self.economy_manager.generate_market_report()
        
        # Update economic indicators
        self.state.economic_indicators.update({
            "job_listings": market_report.get("active_job_offers", 0),
            "goods_listings": market_report.get("active_goods_offers", 0) + market_report.get("active_goods_requests", 0)
        })
        
        # If we have a LLM narrator, provide it with the market report
        if hasattr(self.narrator, 'update_market_report'):
            self.narrator.update_market_report(market_report)
        
        # Create random economic interactions
        if random.random() < 0.3:  # 30% chance each turn
            self._create_random_economic_interaction()

    def _generate_agent_action(self, agent: Agent) -> Optional[AgentAction]:
        """Generate an action for an agent"""
        try:
            # If using LLM, use LLMAgent to generate actions
            if self.use_llm and self.llm_agent:
                context = self._create_decision_context(agent)
                action = self.llm_agent.generate_action(agent, context)
                logger.info(f"Action from {agent.name}: {action}")
                return action
            else:
                # Use rule-based action generation
                return self._generate_rule_based_action(agent)
        except Exception as e:
            logger.error(f"Error generating action for agent {agent.id}: {e}")
            return None

    def _create_decision_context(self, agent: Agent) -> AgentDecisionContext:
        """Create a decision context for an agent"""
        # Get a list of neighbor agents
        neighbors = []
        for other_id in self.state.active_agents:
            if other_id != agent.id:
                neighbors.append(other_id)

        # Limit to a reasonable number of neighbors
        if len(neighbors) > 5:
            neighbors = random.sample(neighbors, 5)

        # Get pending offers for this agent
        pending_offers = []
        for interaction_id in self.state.active_interactions:
            interaction = self.interactions[interaction_id]
            
            # Check for job applications where this agent is the employer
            if interaction.interaction_type == EconomicInteractionType.JOB_APPLICATION:
                if agent in interaction.participants:
                    role = interaction.participants[agent]
                    if role == InteractionRole.EMPLOYER and interaction.parameters.get("stage") == "application":
                        # This is a job application waiting for this employer to respond
                        employee = next((a for a, r in interaction.participants.items() 
                                       if r == InteractionRole.EMPLOYEE), None)
                        if employee:
                            pending_offers.append({
                                "id": interaction.id,
                                "type": "job_application",
                                "from_agent": employee.id,
                                "job_type": interaction.parameters.get("job_type", "Unknown"),
                                "salary": interaction.parameters.get("salary", 0),
                                "status": "pending"
                            })
            
            # Check for goods purchases where this agent is the seller
            elif interaction.interaction_type == EconomicInteractionType.GOODS_PURCHASE:
                if agent in interaction.participants:
                    role = interaction.participants[agent]
                    if role == InteractionRole.SELLER and interaction.parameters.get("stage") == "purchase":
                        # This is a purchase waiting for this seller to respond
                        buyer = next((a for a, r in interaction.participants.items() 
                                    if r == InteractionRole.BUYER), None)
                        if buyer:
                            resource_type = interaction.parameters.get("resource_type", ResourceType.CREDITS)
                            if isinstance(resource_type, ResourceType):
                                resource_name = resource_type.value
                            else:
                                resource_name = str(resource_type)
                                
                            pending_offers.append({
                                "id": interaction.id,
                                "type": "goods_purchase",
                                "from_agent": buyer.id,
                                "resource_type": resource_name,
                                "amount": interaction.parameters.get("purchase_amount", 0),
                                "total_price": interaction.parameters.get("total_price", 0),
                                "status": "pending"
                            })

        # Get goods listings from the economy manager
        goods_listings = self.economy_manager.get_goods_listings_for_agent(agent.id)
        
        # Get job listings from the economy manager
        job_listings = self.economy_manager.get_job_listings_for_agent(agent.id)
        
        # Create market summary
        market_summary = {
            "avg_prices": self.state.economic_indicators.get("avg_resource_prices", {}),
            "avg_salaries": self.state.economic_indicators.get("avg_job_salaries", {}),
            "employment_ratio": self.state.economic_indicators.get("employment_ratio", 0)
        }

        # Create the context
        return AgentDecisionContext(
            turn=self.state.current_tick,
            max_turns=1000,  # Arbitrary large number
            neighbors=neighbors,
            pending_offers=pending_offers,
            jobs_available=job_listings,
            items_for_sale=goods_listings,
            recent_interactions=[],  # Not implemented yet
            goods_listings=goods_listings,
            job_listings=job_listings,
            market_summary=market_summary
        )

    def _generate_rule_based_action(self, agent: Agent) -> AgentAction:
        """Generate a rule-based action for an agent"""
        # Simple rule-based decision making
        action_type = random.choice([
            ActionType.REST, 
            ActionType.LIST_GOODS, 
            ActionType.HIRE, 
            ActionType.APPLY
        ])

        # Create the action with appropriate details based on type
        if action_type == ActionType.LIST_GOODS:
            # Create a random goods listing
            resource_types = [ResourceType.CREDITS, ResourceType.FOOD, ResourceType.WATER, 
                             ResourceType.PHYSICAL_GOODS, ResourceType.DIGITAL_GOODS]
            resource_type = random.choice(resource_types)
            
            action = AgentAction(
                type=action_type,
                agent_id=agent.id,
                turn=self.state.current_tick,
                timestamp=time.time(),
                list_goods_details={
                    "is_offer": True,
                    "resource_type": resource_type.value,
                    "amount": random.uniform(1, 10),
                    "price_per_unit": random.uniform(10, 100),
                    "description": f"Random {resource_type.value} listing"
                }
            )
        
        elif action_type == ActionType.HIRE:
            # Create a random job listing
            job_types = ["Engineer", "Miner", "Farmer", "Trader", "Scientist", "Security"]
            
            action = AgentAction(
                type=action_type,
                agent_id=agent.id,
                turn=self.state.current_tick,
                timestamp=time.time(),
                hire_details={
                    "job_type": random.choice(job_types),
                    "salary_per_turn": random.uniform(50, 200),
                    "requirements": "No special requirements",
                    "max_employees": random.randint(1, 3),
                    "description": "Random job listing"
                }
            )
        
        elif action_type == ActionType.APPLY:
            # Find available job listings
            job_listings = self.economy_manager.get_job_listings_for_agent(agent.id)
            
            if job_listings:
                # Apply to a random job listing
                job_listing = random.choice(job_listings)
                
                action = AgentAction(
                    type=action_type,
                    agent_id=agent.id,
                    turn=self.state.current_tick,
                    timestamp=time.time(),
                    apply_details={
                        "listing_id": job_listing["id"]
                    }
                )
            else:
                # No jobs available, default to REST
                action = AgentAction(
                    type=ActionType.REST,
                    agent_id=agent.id,
                    turn=self.state.current_tick,
                    timestamp=time.time(),
                    extra={"reason": "No jobs available to apply for"}
                )
        
        else:
            # Default REST action
            action = AgentAction(
                type=ActionType.REST,
                agent_id=agent.id,
                turn=self.state.current_tick,
                timestamp=time.time(),
                extra={"reason": "Random rest action"}
            )

        return action

    def _process_action(self, action: AgentAction):
        """Process an agent action"""
        # Log the action
        logger.debug(f"Processing action: {action.type} by agent {action.agent_id}")

        # Process market-related actions through the economy manager
        if action.type in [
            ActionType.HIRE, ActionType.FIRE, ActionType.APPLY, 
            ActionType.LIST_GOODS, ActionType.RETRACT, ActionType.BUY,
            ActionType.WORK
        ]:
            success, message = self.economy_manager.process_action(action, self.agents)
            if success:
                logger.debug(f"Economic action succeeded: {message}")
            else:
                logger.warning(f"Economic action failed: {message}")
            
            return


        # Process active interactions
        self._process_active_interactions()

    def _process_active_interactions(self):
        """Process all active interactions"""
        for interaction_id in list(self.state.active_interactions):
            interaction = self.interactions[interaction_id]
            
            # Process the interaction using the economy manager
            updated_interaction = self.economy_manager.process_interaction(interaction, self.agents)
            self.interactions[interaction_id] = updated_interaction
            
            # Check if the interaction is complete
            if updated_interaction.is_complete:
                # Move to completed interactions
                self.state.active_interactions.remove(interaction_id)
                self.state.completed_interactions.append(interaction_id)
                logger.debug(f"Completed interaction: {interaction_id}")

    def _create_random_economic_interaction(self):
        """Create a random economic interaction between agents"""
        # Select random agents
        if len(self.state.active_agents) < 2:
            return
            
        # Select two random agents
        agent_ids = random.sample(self.state.active_agents, 2)
        agent1 = self.agents[agent_ids[0]]
        agent2 = self.agents[agent_ids[1]]
        
        # Decide what type of interaction to create
        interaction_type = random.choice([
            ActionType.APPLY,
            ActionType.BUY
        ])
        
        # Create the interaction
        if interaction_type == ActionType.APPLY:
            # Decide who is employer and who is employee
            employer = agent1
            employee = agent2
            
            # Create a mock job listing for this interaction
            job_listing = JobListing(
                listing_type=ListingType.JOB_OFFER,
                creator_id=employer.id,
                job_type=random.choice(["Engineer", "Technician", "Scientist", "Manager", "Worker"]),
                salary_per_turn=random.uniform(50.0, 150.0),
                requirements="Experience on Mars required",
                max_employees=2
            )
            
            # Create the job application interaction
            handler = JobMarketHandler()
            interaction = handler.create_interaction(
                employer=employer,
                employee=employee,
                job_listing=job_listing
            )
            
        elif interaction_type == ActionType.BUY:
            # Decide who is seller and who is buyer
            seller = agent1
            buyer = agent2
            
            # Create a mock goods listing for this interaction
            resource_type = random.choice([
                ResourceType.FOOD, 
                ResourceType.WATER,
                ResourceType.OXYGEN,
                ResourceType.PHYSICAL_GOODS
            ])
            
            goods_listing = GoodsListing(
                listing_type=ListingType.GOODS_OFFER,
                creator_id=seller.id,
                resource_type=resource_type,
                amount=random.uniform(5.0, 20.0),
                price_per_unit=random.uniform(5.0, 15.0)
            )
            
            # Create the goods purchase interaction
            handler = GoodsMarketHandler()
            interaction = handler.create_interaction(
                seller=seller,
                buyer=buyer,
                goods_listing=goods_listing,
                purchase_amount=random.uniform(1.0, 5.0)
            )
        
        # Store the interaction
        self.interactions[interaction.id] = interaction
        self.state.active_interactions.append(interaction.id)
        logger.info(f"Created random {interaction_type.value} interaction between {agent1.name} and {agent2.name}")
        
        return interaction

    def _generate_narrative(self):
        """Generate narrative events from interactions"""
        # Check if any completed interactions need narrative events
        for interaction_id in self.state.completed_interactions:
            # Skip if we already have a narrative event for this interaction
            if any(e.interaction_id == interaction_id for e in self.narrative_events.values()):
                continue

            interaction = self.interactions[interaction_id]

            # Use the narrator to generate a narrative event
            if self.narrator:
                event = self.narrator.generate_event_from_interaction(
                    interaction=interaction,
                    agents=[self.agents[agent_id] for agent_id in interaction.participants.keys()
                            if agent_id in self.agents]
                )

                # Store the event
                self.narrative_events[event.id] = event
                self.state.narrative_events.append(event.id)
                logger.info(f"Narrative event: {event.title} - protagonists: {event.agents_involved} - {event.description}")

        # Generate a daily summary if it's a new day
        if self.state.current_tick % 1 == 0 and self.narrator:
            # Get events for the day
            day_events = [self.narrative_events[event_id] for event_id in self.state.narrative_events
                          if event_id not in self.state.narrative_arcs]

            # Generate a summary
            summary = self.narrator.generate_daily_summary(
                day=self.state.current_tick,
                events=day_events,
                agents=[self.agents[agent_id] for agent_id in self.state.active_agents]
            )

            # Create a narrative arc for the day
            arc = NarrativeArc(
                id=f"day_{self.state.current_tick}",
                title=f"Day {self.state.current_tick} on Mars",
                description=summary,
                events=[event.id for event in day_events],
                arc_type="daily_summary",
                start_time=datetime.now(),
                end_time=datetime.now()
            )

            # Store the arc
            self.narrative_arcs[arc.id] = arc
            self.state.narrative_arcs.append(arc.id)
            logger.info(f"Daily summary: {arc.title} - {arc.description}")

    def _update_economic_indicators(self):
        """Update economic indicators based on current state"""
        # Calculate total resources by type
        total_resources = {}
        for resource_type in ResourceType:
            total_resources[resource_type] = sum(
                next((r.amount for r in agent.resources if r.resource_type == resource_type), 0)
                for agent in self.agents.values()
                if agent.id in self.state.active_agents
            )

        # Calculate inequality (Gini coefficient) for credits
        credits = [next((r.amount for r in agent.resources if r.resource_type == ResourceType.CREDITS), 0)
                   for agent in self.agents.values()
                   if agent.id in self.state.active_agents]
        inequality = self._calculate_gini(credits) if credits else 0

        # Calculate average resource holdings
        avg_resources = {
            resource_type: total / len(self.state.active_agents) if len(self.state.active_agents) > 0 else 0
            for resource_type, total in total_resources.items()
        }

        # Calculate interaction rates
        interaction_rate = len(self.state.completed_interactions) / max(1, len(self.state.active_agents))

        # Get market data from the economy manager
        market_report = self.economy_manager.generate_market_report()

        # Store economic indicators
        self.state.economic_indicators.update({
            "total_resources": {k.value: v for k, v in total_resources.items()},
            "avg_resources": {k.value: v for k, v in avg_resources.items()},
            "inequality": inequality,
            "interaction_rate": interaction_rate,
            "population": len(self.state.active_agents),
            "avg_resource_prices": market_report["avg_resource_prices"],
            "avg_job_salaries": market_report["avg_job_salaries"],
            "goods_offers": market_report["active_goods_offers"],
            "goods_requests": market_report["active_goods_requests"],
            "job_offers": market_report["active_job_offers"],
            "employment_ratio": market_report["employment_ratio"]
        })

    def _calculate_gini(self, values) -> float:
        """Calculate the Gini coefficient as a measure of inequality"""
        if not values or all(v == 0 for v in values):
            return 0

        # Sort values
        sorted_values = sorted(values)
        n = len(sorted_values)

        # Calculate Gini coefficient
        cumsum = 0
        for i, value in enumerate(sorted_values):
            cumsum += value * (n - i - 0.5)

        return (2 * cumsum) / (n * sum(sorted_values)) - 1

    def _create_interaction(
            self,
            initiator_id: str,
            responder_id: str,
            interaction_type: ActionType,
            parameters: Dict[str, Any]
    ) -> str:
        """Create a new interaction between agents"""
        # Create the interaction using the simplified roles
        interaction = EconomicInteraction(
            id=f"interaction_{len(self.interactions) + 1}",
            interaction_type=interaction_type,
            participants={
                initiator_id: InteractionRole.INITIATOR,
                responder_id: InteractionRole.RESPONDER
            },
            parameters=parameters,
            start_time=datetime.now(),
            end_time=None,
            is_complete=False,
            narrative_significance=random.uniform(0.1, 1.0)
        )

        # Store the interaction
        self.interactions[interaction.id] = interaction
        self.state.active_interactions.append(interaction.id)

        logger.debug(f"Created interaction: {interaction.id} ({interaction.interaction_type.value})")
        return interaction.id
