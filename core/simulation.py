"""
Core simulation engine for ProtoNomia.
This module contains the main Simulation class that orchestrates the economic simulation.
"""
import random
import logging
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Any

from models.base import (
    Agent, AgentType, AgentFaction, AgentPersonality, ResourceBalance, 
    ResourceType, EconomicInteraction, EconomicInteractionType, 
    InteractionRole, SimulationConfig, SimulationState, 
    NarrativeEvent, NarrativeArc, PopulationControlParams, PopulationEvent
)
from models.actions import AgentAction, ActionType

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
        use_llm: bool = False,
        model_name: str = "gemma:1b",
        narrator_model_name: str = "gemma3:1b",
        mock_llm: bool = False,
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
            mock_llm: Whether to mock LLM responses
            temperature: Controls randomness in LLM generation (0.0-1.0)
            top_p: Nucleus sampling probability threshold (0.0-1.0)
            top_k: Number of highest probability tokens to consider
        """
        self.config = config
        self.use_llm = use_llm
        self.model_name = model_name
        self.narrator_model_name = narrator_model_name
        self.mock_llm = mock_llm
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
        
        # Load modules as needed
        self._load_modules()
    
    def _load_modules(self):
        """Load required modules based on configuration"""
        # Import agent module
        if self.use_llm or self.mock_llm:
            try:
                from agents.llm_agent import LLMAgent
                self.llm_agent = LLMAgent(model_name=self.model_name, mock=self.mock_llm)
                logger.info(f"Loaded LLM agent with model {self.model_name} (mock={self.mock_llm})")
            except ImportError:
                logger.warning("LLM agent module not found, falling back to rule-based agent")
                self.use_llm = False
        
        # Import economic interaction handlers
        try:
            from economics.interactions.ultimatum import UltimatumGameHandler
            self.ultimatum_handler = UltimatumGameHandler()
            logger.info("Loaded UltimatumGameHandler")
        except ImportError:
            self.ultimatum_handler = None
            logger.warning("UltimatumGameHandler not found")
            
        try:
            from economics.interactions.trust import TrustGameHandler
            self.trust_handler = TrustGameHandler()
            logger.info("Loaded TrustGameHandler")
        except ImportError:
            self.trust_handler = None
            logger.warning("TrustGameHandler not found")
            
        # Import narrator - use LLM narrator if use_llm is true
        if self.use_llm or self.mock_llm:
            try:
                from narrative.llm_narrator import LLMNarrator
                self.narrator = LLMNarrator(
                    verbosity=self.config.narrative_verbosity,
                    model_name=self.narrator_model_name,
                    mock_llm=self.mock_llm,
                    temperature=self.temperature,
                    top_p=self.top_p,
                    top_k=self.top_k
                )
                logger.info(f"Loaded LLM Narrator with model {self.narrator_model_name} (mock={self.mock_llm})")
            except ImportError:
                logger.warning("LLM Narrator module not found, falling back to rule-based narrator")
                try:
                    from narrative.narrator import Narrator
                    self.narrator = Narrator(verbosity=self.config.narrative_verbosity)
                    logger.info(f"Loaded rule-based Narrator with verbosity {self.config.narrative_verbosity}")
                except ImportError:
                    self.narrator = None
                    logger.warning("Narrator module not found")
        else:
            # Use rule-based narrator
            try:
                from narrative.narrator import Narrator
                self.narrator = Narrator(verbosity=self.config.narrative_verbosity)
                logger.info(f"Loaded rule-based Narrator with verbosity {self.config.narrative_verbosity}")
            except ImportError:
                self.narrator = None
                logger.warning("Narrator module not found")
        
        # Import population controller
        try:
            from population.controller import PopulationController
            self.population_controller = PopulationController(self.population_params)
            logger.info("Loaded PopulationController")
        except ImportError:
            self.population_controller = None
            logger.warning("PopulationController not found")
    
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
        
        # Create a demo interaction if there are no completed interactions
        if len(self.state.completed_interactions) == 0 and len(self.state.active_agents) >= 2:
            self._create_demo_interaction()
        
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
        faction = random.choice(list(AgentFaction))
        
        # Generate name based on type
        first_names = ["Alice", "Bob", "Charlie", "Diana", "Eliot", "Fatima", "Gabriel", "Hannah", 
                     "Isaac", "Julia", "Kai", "Luna", "Miguel", "Nora", "Oscar", "Priya", 
                     "Quinn", "Rosa", "Santiago", "Tara", "Uriel", "Violet", "Wei", "Xander", 
                     "Yasmin", "Zach"]
        last_names = ["Adams", "Becker", "Chen", "Diaz", "Evans", "Fischer", "Gupta", "Hernandez", 
                    "Ibrahim", "Johnson", "Kim", "Lopez", "Mueller", "Nguyen", "Okafor", 
                    "Patel", "Quinn", "Rodriguez", "Singh", "Thompson", "Ueda", "Vasquez", 
                    "Wang", "Xu", "Yamaguchi", "Zhang"]
        
        if agent_type == AgentType.INDIVIDUAL:
            name = f"{random.choice(first_names)} {random.choice(last_names)}"
        elif agent_type == AgentType.CORPORATION:
            corps = ["MarsTech", "RedPlanet", "AresIndustries", "PhobosEnergy", "DeimosMining", 
                   "OlympusCorp", "VallesMariners", "TerraForming", "CydoniaSystems", "UtopiaLabs"]
            name = f"{random.choice(corps)}"
        elif agent_type == AgentType.COLLECTIVE:
            collectives = ["Mars Citizens Union", "Tharsis Cooperative", "Hellas Basin Commune", 
                         "Olympus Mons Collective", "Valles Network", "Arcadia Alliance", 
                         "Elysium Syndicate", "Isidis Community"]
            name = f"{random.choice(collectives)}"
        elif agent_type == AgentType.GOVERNMENT:
            govs = ["Mars Central Authority", "Tharsis Administration", "Olympus Mons Council", 
                  "Valles Marineris District", "Hellas Regional Government", "Terra-Mars Liaison Office"]
            name = f"{random.choice(govs)}"
        else:  # AI
            ai_names = ["ARIA", "MARS-OS", "OLYMPUS", "PHOBOS", "DEIMOS", "TERRA-LINK", 
                      "RED", "HELLAS", "THARSIS", "ARCADIA"]
            name = f"{random.choice(ai_names)}"
        
        # Create initial resources based on agent type
        resources = []
        
        # All agents have credits
        credit_amount = 0
        if agent_type == AgentType.INDIVIDUAL:
            credit_amount = random.uniform(10.0, 100.0)
        elif agent_type == AgentType.CORPORATION:
            credit_amount = random.uniform(500.0, 5000.0)
        elif agent_type == AgentType.COLLECTIVE:
            credit_amount = random.uniform(200.0, 1000.0)
        elif agent_type == AgentType.GOVERNMENT:
            credit_amount = random.uniform(1000.0, 10000.0)
        else:  # AI
            credit_amount = random.uniform(50.0, 500.0)
        
        resources.append(ResourceBalance(
            resource_type=ResourceType.CREDITS,
            amount=credit_amount
        ))
        
        # Add health for individuals
        if agent_type == AgentType.INDIVIDUAL:
            resources.append(ResourceBalance(
                resource_type=ResourceType.HEALTH,
                amount=random.uniform(0.7, 1.0)
            ))
        
        # Create agent
        return Agent(
            name=name,
            agent_type=agent_type,
            faction=faction,
            personality=personality,
            resources=resources,
            birth_date=self.state.current_date - timedelta(days=random.randint(0, 10000)),
            is_alive=True
        )
    
    def _process_lifecycle_events(self):
        """Process agent lifecycle events like birth, death, etc."""
        if self.population_controller is None:
            # Simple implementation if controller not available
            self._simple_lifecycle_events()
        else:
            # Use population controller
            events = self.population_controller.process_population(
                list(self.agents.values()),
                self.state.current_date,
                self.state.economic_indicators,
                self.config.max_population
            )
            
            # Apply lifecycle events
            for event in events:
                if event.event_type == "birth":
                    agent = self._create_random_agent()
                    self.agents[agent.id] = agent
                    self.state.active_agents.append(agent.id)
                elif event.event_type == "death":
                    if event.agent_id in self.agents:
                        self.agents[event.agent_id].is_alive = False
                        self.agents[event.agent_id].death_date = self.state.current_date
                        self.state.active_agents.remove(event.agent_id)
                        self.state.deceased_agents.append(event.agent_id)
        
        # Update population size
        self.state.population_size = len(self.state.active_agents)
    
    def _simple_lifecycle_events(self):
        """Simple implementation of lifecycle events without controller"""
        # Simple birth process if under max population
        if len(self.state.active_agents) < self.config.max_population:
            for _ in range(max(1, int(len(self.state.active_agents) * 0.01))):
                if random.random() < 0.05:  # 5% chance of birth per tick
                    agent = self._create_random_agent()
                    self.agents[agent.id] = agent
                    self.state.active_agents.append(agent.id)
        
        # Simple death process
        for agent_id in list(self.state.active_agents):
            if agent_id in self.agents:
                agent = self.agents[agent_id]
                # Age-based death probability
                age = agent.calculate_age(self.state.current_date)
                death_prob = min(0.001 + (age / 36500) * 0.1, 0.1)  # Increases with age
                
                if random.random() < death_prob:
                    agent.is_alive = False
                    agent.death_date = self.state.current_date
                    self.state.active_agents.remove(agent_id)
                    self.state.deceased_agents.append(agent_id)
    
    def _process_agent_actions(self):
        """Process agent actions and interactions"""
        # Process active interactions from previous ticks
        self._process_active_interactions()
        
        # Generate and process new actions for each agent
        for agent_id in self.state.active_agents:
            agent = self.agents[agent_id]
            
            # Generate action
            action = self._generate_agent_action(agent)
            
            # Process action
            if action:
                self._process_action(action)
    
    def _generate_agent_action(self, agent: Agent) -> Optional[AgentAction]:
        """Generate an action for the agent"""
        # If using LLM and it's available
        if self.use_llm and hasattr(self, 'llm_agent'):
            # Create decision context
            context = self._create_decision_context(agent)
            
            # Generate action using LLM
            return self.llm_agent.generate_action(agent, context)
        else:
            # Simple rule-based action generation
            return self._generate_rule_based_action(agent)
    
    def _create_decision_context(self, agent: Agent):
        """Create a decision context for the agent"""
        from models.actions import AgentDecisionContext
        
        # Convert resources to dictionary
        resources = {r.resource_type.value: r.amount for r in agent.resources}
        
        # Convert needs to dictionary
        needs = {
            "subsistence": agent.needs.subsistence,
            "security": agent.needs.security,
            "social": agent.needs.social,
            "esteem": agent.needs.esteem,
            "self_actualization": agent.needs.self_actualization
        }
        
        # Get neighbors (nearby agents)
        neighbors = random.sample(
            [a_id for a_id in self.state.active_agents if a_id != agent.id],
            min(3, len(self.state.active_agents) - 1)
        )
        
        # Create pending offers (simplified)
        pending_offers = []
        
        # Create jobs available (simplified)
        jobs_available = [
            {"id": f"job{i}", "type": "generic", "pay": "10 credits", "difficulty": "medium"}
            for i in range(2)
        ]
        
        # Create items for sale (simplified)
        items_for_sale = [
            {"id": f"item{i}", "type": "food", "price": "5 credits", "quality": "good"}
            for i in range(2)
        ]
        
        # Get recent interactions (simplified)
        recent_interactions = []
        
        return AgentDecisionContext(
            agent_id=agent.id,
            name=agent.name,
            resources=resources,
            needs=needs,
            turn=self.state.current_tick,
            max_turns=100000,  # Arbitrary large number
            neighbors=neighbors,
            pending_offers=pending_offers,
            jobs_available=jobs_available,
            items_for_sale=items_for_sale,
            recent_interactions=recent_interactions
        )
    
    def _generate_rule_based_action(self, agent: Agent) -> AgentAction:
        """Generate a rule-based action for the agent"""
        # Simple rule-based action generation
        action_type = random.choice(list(ActionType))
        
        # Create action
        action = AgentAction(
            type=action_type,
            agent_id=agent.id,
            turn=self.state.current_tick,
            timestamp=time.time()
        )
        
        # If REST action, no additional details needed
        if action_type == ActionType.REST:
            pass
        
        # For other actions, we would need to add appropriate details
        # This is a simplified implementation
        
        return action
    
    def _process_action(self, action: AgentAction):
        """Process an agent action"""
        # Handle based on action type
        if action.type == ActionType.REST:
            # For REST, just update agent's needs
            if action.agent_id in self.agents:
                agent = self.agents[action.agent_id]
                # Increase health if available
                for resource in agent.resources:
                    if resource.resource_type == ResourceType.HEALTH and resource.amount < 1.0:
                        resource.amount = min(1.0, resource.amount + 0.1)
        
        elif action.type == ActionType.OFFER:
            # Create interaction based on the offer
            # This is a simplified implementation
            pass
        
        # Other action types would be handled similarly
    
    def _process_active_interactions(self):
        """Process all active interactions"""
        # Process each active interaction
        for interaction_id in list(self.state.active_interactions):
            if interaction_id in self.interactions:
                interaction = self.interactions[interaction_id]
                
                # Process based on interaction type
                if interaction.interaction_type == EconomicInteractionType.ULTIMATUM and self.ultimatum_handler:
                    # Process ultimatum game
                    updated_interaction = self._process_ultimatum_game(interaction)
                    self.interactions[interaction_id] = updated_interaction
                
                elif interaction.interaction_type == EconomicInteractionType.TRUST and self.trust_handler:
                    # Process trust game
                    updated_interaction = self._process_trust_game(interaction)
                    self.interactions[interaction_id] = updated_interaction
                
                # Check if interaction is complete
                if interaction.is_complete:
                    self.state.active_interactions.remove(interaction_id)
                    self.state.completed_interactions.append(interaction_id)
    
    def _process_ultimatum_game(self, interaction: EconomicInteraction) -> EconomicInteraction:
        """Process an Ultimatum Game interaction"""
        # Identify proposer and responder
        proposer_id = next((a_id for a_id, role in interaction.participants.items() 
                          if role == InteractionRole.PROPOSER), None)
        responder_id = next((a_id for a_id, role in interaction.participants.items() 
                           if role == InteractionRole.RESPONDER), None)
        
        if proposer_id is None or responder_id is None:
            interaction.is_complete = True
            return interaction
        
        # Get agents
        if proposer_id not in self.agents or responder_id not in self.agents:
            interaction.is_complete = True
            return interaction
        
        proposer = self.agents[proposer_id]
        responder = self.agents[responder_id]
        
        # Get parameters
        total_amount = interaction.parameters.get("total_amount", 10.0)
        offer_amount = interaction.parameters.get("offer_amount", total_amount / 2)
        currency = interaction.parameters.get("currency", ResourceType.CREDITS)
        
        # Determine responder's acceptance based on personality
        # More fair-minded responders reject unfair offers
        fairness = offer_amount / total_amount
        acceptance_threshold = 1.0 - responder.personality.fairness_preference
        responder_accepts = fairness >= acceptance_threshold
        
        # Execute the interaction
        result = self.ultimatum_handler.execute(
            proposer=proposer,
            responder=responder,
            total_amount=total_amount,
            offer_amount=offer_amount,
            responder_accepts=responder_accepts
        )
        
        # Update the interaction
        interaction.is_complete = True
        interaction.end_time = self.state.current_date
        interaction.outcomes = result.outcomes
        
        return interaction
    
    def _process_trust_game(self, interaction: EconomicInteraction) -> EconomicInteraction:
        """Process a Trust Game interaction"""
        # Identify investor and trustee
        investor_id = next((a_id for a_id, role in interaction.participants.items() 
                          if role == InteractionRole.INVESTOR), None)
        trustee_id = next((a_id for a_id, role in interaction.participants.items() 
                         if role == InteractionRole.TRUSTEE), None)
        
        if investor_id is None or trustee_id is None:
            interaction.is_complete = True
            return interaction
        
        # Get agents
        if investor_id not in self.agents or trustee_id not in self.agents:
            interaction.is_complete = True
            return interaction
        
        investor = self.agents[investor_id]
        trustee = self.agents[trustee_id]
        
        # Get parameters
        investment_amount = interaction.parameters.get("investment_amount", 10.0)
        multiplier = interaction.parameters.get("multiplier", 3.0)
        
        # Determine trustee's reciprocation based on personality
        # More cooperative and fair trustees return more
        trustee_reciprocation = (trustee.personality.cooperativeness + 
                                trustee.personality.fairness_preference) / 2
        return_amount = trustee_reciprocation * investment_amount * multiplier
        
        # Execute the interaction
        result = self.trust_handler.execute(
            investor=investor,
            trustee=trustee,
            investment_amount=investment_amount,
            multiplier=multiplier,
            return_amount=return_amount
        )
        
        # Update the interaction
        interaction.is_complete = True
        interaction.end_time = self.state.current_date
        interaction.outcomes = result.outcomes
        
        return interaction
    
    def _generate_narrative(self):
        """Generate narrative events from significant interactions"""
        if self.narrator is None:
            return
        
        # Get recent completed interactions
        recent_interactions = [
            self.interactions[i_id] for i_id in self.state.completed_interactions[-10:]
            if i_id in self.interactions
        ]
        
        # Generate events from significant interactions
        for interaction in recent_interactions:
            if interaction.narrative_significance > 0.2:  # Only for significant interactions
                event = self.narrator.generate_event_from_interaction(
                    interaction=interaction,
                    agents=[self.agents[a_id] for a_id in interaction.participants.keys() 
                           if a_id in self.agents]
                )
                
                if event:
                    self.narrative_events[event.id] = event
                    self.state.narrative_events.append(event.id)
        
        # Periodically generate daily summaries (simplified)
        if (self.state.current_tick % 10) == 0:  # Every 10 ticks
            # Generate a daily summary
            day = self.state.current_tick // 1  # 1 tick = 1 day
            recent_events = [
                self.narrative_events[e_id] for e_id in self.state.narrative_events[-20:]
                if e_id in self.narrative_events
            ]
            
            self.narrator.generate_daily_summary(
                day=day,
                events=recent_events,
                agents=list(self.agents.values())
            )
    
    def _update_economic_indicators(self):
        """Update economic indicators for the simulation"""
        # Calculate basic economic indicators
        
        # Total wealth
        total_credits = sum(
            r.amount for agent in self.agents.values() 
            for r in agent.resources if r.resource_type == ResourceType.CREDITS
        )
        
        # Wealth distribution (Gini-like measure)
        if len(self.agents) > 1:
            credits_per_agent = [
                next((r.amount for r in agent.resources if r.resource_type == ResourceType.CREDITS), 0)
                for agent in self.agents.values()
            ]
            credits_per_agent.sort()
            n = len(credits_per_agent)
            inequality = sum(i * credits_per_agent[i] for i in range(n)) / (n * sum(credits_per_agent))
        else:
            inequality = 0
        
        # Interaction metrics
        cooperation_rate = 0
        if len(self.state.completed_interactions) > 0:
            # Simplified cooperation metric
            cooperation_rate = random.uniform(0.3, 0.7)  # Placeholder
        
        # Update indicators
        self.state.economic_indicators = {
            "total_credits": total_credits,
            "wealth_inequality": inequality,
            "population": self.state.population_size,
            "cooperation_rate": cooperation_rate,
            "active_interactions": len(self.state.active_interactions),
            "completed_interactions": len(self.state.completed_interactions)
        }
    
    def _create_demo_interaction(self):
        """Create a sample interaction to demonstrate narrative generation"""
        # Only proceed if we have at least 2 agents
        if len(self.state.active_agents) < 2:
            return
            
        # Select two random agents
        agent_ids = random.sample(self.state.active_agents, 2)
        agent1 = self.agents[agent_ids[0]]
        agent2 = self.agents[agent_ids[1]]
        
        # Create an ultimatum game interaction
        interaction = EconomicInteraction(
            interaction_type=EconomicInteractionType.ULTIMATUM,
            participants={
                agent1.id: InteractionRole.PROPOSER,
                agent2.id: InteractionRole.RESPONDER
            },
            parameters={
                "total_amount": 100.0,
                "offer_amount": 30.0,
                "responder_accepts": True,
                "currency": "credits"
            },
            is_complete=True,
            narrative_significance=0.8
        )
        
        # Add to simulation
        self.interactions[interaction.id] = interaction
        self.state.completed_interactions.append(interaction.id)
        
        logger.info(f"Created demo interaction between {agent1.name} and {agent2.name}")