import random
import logging
from typing import Dict, List, Optional, Tuple, Set
from datetime import datetime, timedelta
import uuid

from ..models.base import (
    Agent, AgentType, AgentFaction, AgentPersonality, AgentNeeds,
    ResourceType, ResourceBalance, PopulationEvent, PopulationControlParams
)

logger = logging.getLogger(__name__)

class PopulationController:
    """Controller for managing population dynamics in the simulation"""
    
    def __init__(
        self, 
        params: Optional[PopulationControlParams] = None,
        resource_scarcity: float = 0.5
    ):
        """Initialize the population controller
        
        Args:
            params: Population control parameters
            resource_scarcity: Resource scarcity level (0.0-1.0) affecting birth/death rates
        """
        self.params = params if params else PopulationControlParams()
        self.resource_scarcity = resource_scarcity
        self.recent_deaths: List[Tuple[str, str]] = []  # (agent_id, reason)
        self.recent_births: List[Tuple[str, List[str]]] = []  # (agent_id, parent_ids)
        self.population_events: Dict[str, PopulationEvent] = {}
    
    def _adjust_rates_for_scarcity(self):
        """Adjust birth and death rates based on resource scarcity"""
        # Higher scarcity = lower birth rate, higher death rate
        scarcity_factor = self.resource_scarcity * 2  # 0-2 range
        
        # Birth rate goes down with scarcity
        birth_adjustment = -0.005 * scarcity_factor
        adjusted_birth_rate = max(0.001, self.params.birth_rate + birth_adjustment)
        
        # Death rate goes up with scarcity
        death_adjustment = 0.005 * scarcity_factor
        adjusted_death_rate = min(0.05, self.params.death_rate + death_adjustment)
        
        # Other rates adjust too but less dramatically
        immigration_adjustment = -0.001 * scarcity_factor
        adjusted_immigration_rate = max(0.0001, self.params.immigration_rate + immigration_adjustment)
        
        emigration_adjustment = 0.001 * scarcity_factor
        adjusted_emigration_rate = min(0.01, self.params.emigration_rate + emigration_adjustment)
        
        return {
            "birth_rate": adjusted_birth_rate,
            "death_rate": adjusted_death_rate,
            "immigration_rate": adjusted_immigration_rate,
            "emigration_rate": adjusted_emigration_rate
        }
    
    def _adjust_rates_for_population_size(self, current_population: int, max_population: int):
        """Adjust rates based on current population relative to maximum"""
        # Calculate population ratio (0-1)
        population_ratio = min(1.0, current_population / max_population if max_population > 0 else 0)
        
        # As population approaches max, birth rate decreases and emigration increases
        pop_adjustment = population_ratio ** 2  # Squared for more dramatic effect near capacity
        
        birth_adjustment = -0.01 * pop_adjustment
        emigration_adjustment = 0.005 * pop_adjustment
        
        return {
            "birth_adjustment": birth_adjustment,
            "emigration_adjustment": emigration_adjustment
        }
    
    def process_lifecycle_events(
        self, 
        agents: Dict[str, Agent], 
        current_date: datetime,
        max_population: int
    ) -> Tuple[List[PopulationEvent], List[Agent]]:
        """Process lifecycle events for all agents
        
        Args:
            agents: Dictionary of agent_id -> Agent
            current_date: Current simulation date
            max_population: Maximum population size
            
        Returns:
            Tuple of (new population events, new agents created)
        """
        # Clear recent events
        self.recent_deaths = []
        self.recent_births = []
        
        # Get adjusted rates
        adjusted_rates = self._adjust_rates_for_scarcity()
        pop_adjustments = self._adjust_rates_for_population_size(len(agents), max_population)
        
        # Final rates
        birth_rate = max(0.001, adjusted_rates["birth_rate"] + pop_adjustments["birth_adjustment"])
        death_rate = adjusted_rates["death_rate"]
        immigration_rate = adjusted_rates["immigration_rate"] * (1 - pop_adjustments["birth_adjustment"]) 
        emigration_rate = adjusted_rates["emigration_rate"] + pop_adjustments["emigration_adjustment"]
        
        # Process deaths
        death_events = self._process_deaths(agents, current_date, death_rate)
        
        # Process births
        current_population = len([a for a in agents.values() if a.is_alive])
        population_capacity = max_population - current_population
        
        birth_events = []
        new_agents = []
        
        if population_capacity > 0:
            birth_events, new_birth_agents = self._process_births(
                agents, current_date, birth_rate, min(10, population_capacity)
            )
            new_agents.extend(new_birth_agents)
            
            # Process immigration
            immigration_events, new_immigration_agents = self._process_immigration(
                current_date, immigration_rate, min(5, population_capacity - len(new_birth_agents))
            )
            birth_events.extend(immigration_events)
            new_agents.extend(new_immigration_agents)
        
        # Process emigration
        emigration_events = self._process_emigration(agents, current_date, emigration_rate)
        
        # Combine all events
        all_events = death_events + birth_events + emigration_events
        
        # Store events
        for event in all_events:
            self.population_events[event.id] = event
        
        return all_events, new_agents
    
    def _process_deaths(
        self, 
        agents: Dict[str, Agent], 
        current_date: datetime,
        death_rate: float
    ) -> List[PopulationEvent]:
        """Process agent deaths
        
        Args:
            agents: Dictionary of agent_id -> Agent
            current_date: Current simulation date
            death_rate: Adjusted death rate
            
        Returns:
            List of death events
        """
        death_events = []
        
        for agent_id, agent in agents.items():
            if not agent.is_alive:
                continue
            
            # Update agent age
            agent.age_days = agent.calculate_age(current_date)
            
            # Base death probability
            base_probability = death_rate
            
            # Adjust for age
            age_factor = min(1.0, (agent.age_days / self.params.max_age_days) ** 2)
            age_adjustment = age_factor * 0.1  # up to +10% chance for very old agents
            
            # Adjust for critical needs
            needs_adjustment = 0.0
            if agent.needs.subsistence < 0.1:
                needs_adjustment += 0.05
            if agent.needs.security < 0.1:
                needs_adjustment += 0.02
            
            # Adjust for critical resources
            resource_adjustment = 0.0
            oxygen = next((r.amount for r in agent.resources if r.resource_type == ResourceType.OXYGEN), 0)
            water = next((r.amount for r in agent.resources if r.resource_type == ResourceType.WATER), 0)
            
            if oxygen < 5:
                resource_adjustment += 0.1
            if water < 5:
                resource_adjustment += 0.08
            
            # Calculate final death probability
            death_probability = base_probability + age_adjustment + needs_adjustment + resource_adjustment
            
            # Check for death
            if random.random() < death_probability:
                # Determine cause of death
                if agent.age_days >= self.params.max_age_days:
                    reason = "Old age"
                elif oxygen < 5:
                    reason = "Oxygen deprivation"
                elif water < 5:
                    reason = "Dehydration"
                elif agent.needs.subsistence < 0.1:
                    reason = "Malnutrition"
                else:
                    causes = ["Accident", "Illness", "Unknown causes"]
                    reason = random.choice(causes)
                
                # Update agent
                agent.is_alive = False
                agent.death_date = current_date
                
                # Create event
                event = PopulationEvent(
                    event_type="death",
                    agent_id=agent.id,
                    timestamp=current_date,
                    reason=reason
                )
                death_events.append(event)
                
                # Record for narrative purposes
                self.recent_deaths.append((agent.id, reason))
                
                logger.info(f"Agent {agent.name} ({agent.id}) has died. Reason: {reason}")
        
        return death_events
    
    def _process_births(
        self, 
        agents: Dict[str, Agent], 
        current_date: datetime,
        birth_rate: float,
        max_births: int
    ) -> Tuple[List[PopulationEvent], List[Agent]]:
        """Process agent births
        
        Args:
            agents: Dictionary of agent_id -> Agent
            current_date: Current simulation date
            birth_rate: Adjusted birth rate
            max_births: Maximum number of births to allow
            
        Returns:
            Tuple of (birth events, new agents)
        """
        birth_events = []
        new_agents = []
        
        # For MVP, model births as random events rather than detailed reproduction simulation
        living_agents = [a for a in agents.values() if a.is_alive]
        
        # Only individuals can give birth
        potential_parents = [a for a in living_agents if a.agent_type == AgentType.INDIVIDUAL]
        
        # Filter to those of reproductive age (arbitrary range for simulation)
        reproductive_agents = [a for a in potential_parents if 5000 <= a.age_days <= 20000]
        
        # Determine number of births based on birth rate and agent count
        num_potential_births = len(reproductive_agents)
        avg_births = birth_rate * num_potential_births
        
        # Add randomness (Poisson-like distribution)
        num_births = min(max_births, round(random.normalvariate(avg_births, avg_births / 2)))
        
        # Process each birth
        for _ in range(num_births):
            if not reproductive_agents:
                break
                
            # Select parent(s)
            parent = random.choice(reproductive_agents)
            
            # For simplicity, sometimes choose a second parent
            parents = [parent]
            if random.random() < 0.8:  # 80% chance of two parents
                potential_partners = [a for a in reproductive_agents if a != parent]
                if potential_partners:
                    second_parent = random.choice(potential_partners)
                    parents.append(second_parent)
            
            # Generate child agent
            child_agent = self._generate_child_agent(parents, current_date)
            
            # Add to results
            new_agents.append(child_agent)
            
            # Create event
            event = PopulationEvent(
                event_type="birth",
                agent_id=child_agent.id,
                timestamp=current_date,
                reason="Natural birth",
                related_agents=[p.id for p in parents]
            )
            birth_events.append(event)
            
            # Record for narrative purposes
            self.recent_births.append((child_agent.id, [p.id for p in parents]))
            
            logger.info(f"New agent {child_agent.name} born to {', '.join([p.name for p in parents])}")
        
        return birth_events, new_agents
    
    def _generate_child_agent(self, parents: List[Agent], current_date: datetime) -> Agent:
        """Generate a new agent as a child of parent agent(s)
        
        Args:
            parents: List of parent agents (1 or 2)
            current_date: Current simulation date
            
        Returns:
            New child agent
        """
        # For simplicity, child inherits traits from parents with some randomness
        parent = parents[0]
        
        # Generate name (for MVP just use a pattern)
        first_names = ["Zara", "Declan", "Nova", "Kyron", "Elara", "Orion", "Vega", "Talos", 
                      "Lyra", "Ceres", "Rigel", "Phoebe", "Atlas", "Nereid", "Zephyr", "Io"]
                      
        last_names = ["Chen", "Rodriguez", "Patel", "Kim", "Zhang", "Novak", "Okafor", "Singh",
                     "Takahashi", "Volkov", "Dubois", "Gonzalez", "Nkosi", "Ivanova", "Santos", "Reyes"]
        
        if len(parents) == 2:
            # Child might inherit last name from either parent
            parent_last = parents[1].name.split(" ")[-1] if " " in parents[1].name else None
            if parent_last and parent_last in last_names:
                last_name = parent_last
            else:
                last_name = random.choice(last_names)
        else:
            # Single parent, either inherit or random
            parent_last = parent.name.split(" ")[-1] if " " in parent.name else None
            if parent_last and parent_last in last_names and random.random() < 0.8:
                last_name = parent_last
            else:
                last_name = random.choice(last_names)
        
        name = f"{random.choice(first_names)} {last_name}"
        
        # Inherit faction with high probability
        if len(parents) == 2 and parents[0].faction == parents[1].faction:
            faction = parents[0].faction
        else:
            # Either inherit from one parent or possibly be different
            if random.random() < 0.8:
                faction = parent.faction
            else:
                factions = list(AgentFaction)
                factions.remove(parent.faction)
                faction = random.choice(factions)
        
        # Inherit personality with variation
        if len(parents) == 2:
            # Average parents' traits with randomness
            personality = AgentPersonality(
                cooperativeness=min(1.0, max(0.0, (parents[0].personality.cooperativeness + parents[1].personality.cooperativeness) / 2 + random.uniform(-0.2, 0.2))),
                risk_tolerance=min(1.0, max(0.0, (parents[0].personality.risk_tolerance + parents[1].personality.risk_tolerance) / 2 + random.uniform(-0.2, 0.2))),
                fairness_preference=min(1.0, max(0.0, (parents[0].personality.fairness_preference + parents[1].personality.fairness_preference) / 2 + random.uniform(-0.2, 0.2))),
                altruism=min(1.0, max(0.0, (parents[0].personality.altruism + parents[1].personality.altruism) / 2 + random.uniform(-0.2, 0.2))),
                rationality=min(1.0, max(0.0, (parents[0].personality.rationality + parents[1].personality.rationality) / 2 + random.uniform(-0.2, 0.2))),
                long_term_orientation=min(1.0, max(0.0, (parents[0].personality.long_term_orientation + parents[1].personality.long_term_orientation) / 2 + random.uniform(-0.2, 0.2)))
            )
        else:
            # Inherit from single parent with more variation
            personality = AgentPersonality(
                cooperativeness=min(1.0, max(0.0, parent.personality.cooperativeness + random.uniform(-0.3, 0.3))),
                risk_tolerance=min(1.0, max(0.0, parent.personality.risk_tolerance + random.uniform(-0.3, 0.3))),
                fairness_preference=min(1.0, max(0.0, parent.personality.fairness_preference + random.uniform(-0.3, 0.3))),
                altruism=min(1.0, max(0.0, parent.personality.altruism + random.uniform(-0.3, 0.3))),
                rationality=min(1.0, max(0.0, parent.personality.rationality + random.uniform(-0.3, 0.3))),
                long_term_orientation=min(1.0, max(0.0, parent.personality.long_term_orientation + random.uniform(-0.3, 0.3)))
            )
        
        # Basic starting resources (less than adults)
        resources = [
            ResourceBalance(
                resource_type=ResourceType.CREDITS,
                amount=50,  # Start with small amount
                last_updated=current_date
            ),
            ResourceBalance(
                resource_type=ResourceType.OXYGEN,
                amount=random.uniform(70, 100),
                last_updated=current_date
            ),
            ResourceBalance(
                resource_type=ResourceType.WATER,
                amount=random.uniform(70, 100),
                last_updated=current_date
            )
        ]
        
        # Basic skills - might inherit some from parents
        skills = {}
        if len(parents) > 0:
            # Chance to inherit some skills from parents
            for parent in parents:
                if parent.skills:
                    potential_skills = list(parent.skills.items())
                    if potential_skills:
                        # Inherit up to 2 skills from each parent
                        num_skills = random.randint(0, min(2, len(potential_skills)))
                        inherited_skills = random.sample(potential_skills, num_skills)
                        
                        for skill, level in inherited_skills:
                            # Inherit at lower level
                            skills[skill] = level * random.uniform(0.1, 0.3)
        
        # Create agent
        return Agent(
            name=name,
            agent_type=AgentType.INDIVIDUAL,  # Children are always individuals
            faction=faction,
            age_days=0,  # Start at age 0
            birth_date=current_date,
            personality=personality,
            resources=resources,
            location=parent.location,  # Born in same location as parent
            skills=skills
        )
    
    def _process_immigration(
        self, 
        current_date: datetime,
        immigration_rate: float,
        max_immigrants: int
    ) -> Tuple[List[PopulationEvent], List[Agent]]:
        """Process immigration of new agents
        
        Args:
            current_date: Current simulation date
            immigration_rate: Adjusted immigration rate
            max_immigrants: Maximum number of immigrants to allow
            
        Returns:
            Tuple of (immigration events, new agents)
        """
        events = []
        new_agents = []
        
        # Determine number of immigrants
        base_immigrants = immigration_rate * 100  # Base number scaled from rate
        num_immigrants = min(max_immigrants, round(random.normalvariate(base_immigrants, base_immigrants / 3)))
        
        # Generate immigrant agents
        for _ in range(num_immigrants):
            # Generate a new agent with more randomness than birth
            new_agent = self._generate_immigrant_agent(current_date)
            new_agents.append(new_agent)
            
            # Create event
            event = PopulationEvent(
                event_type="immigration",
                agent_id=new_agent.id,
                timestamp=current_date,
                reason=f"Arrived from {random.choice(['Terra', 'Phobos Colony', 'Luna', 'Europa', 'Ganymede'])}"
            )
            events.append(event)
            
            logger.info(f"New immigrant {new_agent.name} arrived")
        
        return events, new_agents
    
    def _generate_immigrant_agent(self, current_date: datetime) -> Agent:
        """Generate a new agent as an immigrant
        
        Args:
            current_date: Current simulation date
            
        Returns:
            New immigrant agent
        """
        # Faction distribution for immigrants
        faction_weights = {
            AgentFaction.TERRA_CORP: 0.4,    # Most immigrants are from Terra Corps
            AgentFaction.MARS_NATIVE: 0.05,  # Few Mars natives return via immigration
            AgentFaction.INDEPENDENT: 0.3,   # Many independents
            AgentFaction.GOVERNMENT: 0.15,   # Some government agents
            AgentFaction.UNDERGROUND: 0.1    # Few underground
        }
        
        # Agent type distribution
        type_weights = {
            AgentType.INDIVIDUAL: 0.8,
            AgentType.CORPORATION: 0.1,
            AgentType.COLLECTIVE: 0.05,
            AgentType.GOVERNMENT: 0.03,
            AgentType.AI: 0.02
        }
        
        # Select type and faction
        agent_type = random.choices(list(type_weights.keys()), 
                                  weights=list(type_weights.values()))[0]
        
        agent_faction = random.choices(list(faction_weights.keys()),
                                     weights=list(faction_weights.values()))[0]
        
        # Generate name
        if agent_type == AgentType.INDIVIDUAL:
            first_names = ["Zara", "Declan", "Nova", "Kyron", "Elara", "Orion", "Vega", "Talos", 
                          "Lyra", "Ceres", "Rigel", "Phoebe", "Atlas", "Nereid", "Zephyr", "Io"]
            last_names = ["Chen", "Rodriguez", "Patel", "Kim", "Zhang", "Novak", "Okafor", "Singh",
                         "Takahashi", "Volkov", "Dubois", "Gonzalez", "Nkosi", "Ivanova", "Santos", "Reyes"]
            name = f"{random.choice(first_names)} {random.choice(last_names)}"
        else:
            corp_prefixes = ["Neo", "Quantum", "Cyber", "Tera", "Hyper", "Omni", "Cryo", "Fusion", 
                           "Helios", "Novum", "Orb", "Pulse", "Red", "Synth", "Vortex", "Zenith"]
            corp_suffixes = ["Tech", "Dynamics", "Systems", "Corp", "Industries", "Innovations", 
                           "Solutions", "Consortium", "Collective", "Network", "Coalition", "Enterprises"]
            name = f"{random.choice(corp_prefixes)}{random.choice(corp_suffixes)}"
        
        # Generate personality
        personality = AgentPersonality(
            cooperativeness=random.uniform(0.1, 0.9),
            risk_tolerance=random.uniform(0.1, 0.9),
            fairness_preference=random.uniform(0.1, 0.9),
            altruism=random.uniform(0.1, 0.9),
            rationality=random.uniform(0.1, 0.9),
            long_term_orientation=random.uniform(0.1, 0.9)
        )
        
        # Generate age (biased toward younger for immigrants)
        age_in_days = int(random.expovariate(1/500) * 365)  # Average a bit more than 1 year
        birth_date = current_date - timedelta(days=age_in_days)
        
        # Generate resources
        resources = []
        
        # All agents get some credits - immigrants often bring wealth
        base_credits = 1500  # More than native newborns
        credits_modifier = {
            AgentType.INDIVIDUAL: 1.0,
            AgentType.CORPORATION: 7.0,
            AgentType.COLLECTIVE: 4.0,
            AgentType.GOVERNMENT: 12.0,
            AgentType.AI: 0.7
        }
        faction_modifier = {
            AgentFaction.TERRA_CORP: 2.0,
            AgentFaction.MARS_NATIVE: 0.9,
            AgentFaction.INDEPENDENT: 1.2,
            AgentFaction.GOVERNMENT: 1.5,
            AgentFaction.UNDERGROUND: 0.7
        }
        
        credits = base_credits * credits_modifier.get(agent_type, 1.0) * faction_modifier.get(agent_faction, 1.0)
        credits *= random.uniform(0.7, 1.3)  # Add some randomness
        
        resources.append(ResourceBalance(
            resource_type=ResourceType.CREDITS,
            amount=credits,
            last_updated=current_date
        ))
        
        # Add some basic needs resources
        resources.append(ResourceBalance(
            resource_type=ResourceType.OXYGEN,
            amount=random.uniform(70, 100),
            last_updated=current_date
        ))
        
        resources.append(ResourceBalance(
            resource_type=ResourceType.WATER,
            amount=random.uniform(70, 100),
            last_updated=current_date
        ))
        
        # Add some reputation
        resources.append(ResourceBalance(
            resource_type=ResourceType.REPUTATION,
            amount=random.uniform(10, 100),
            last_updated=current_date
        ))
        
        # Add random other resources based on agent type
        if agent_type == AgentType.CORPORATION:
            # Corporations have digital goods and physical goods
            resources.append(ResourceBalance(
                resource_type=ResourceType.DIGITAL_GOODS,
                amount=random.uniform(100, 500),
                last_updated=current_date
            ))
            resources.append(ResourceBalance(
                resource_type=ResourceType.PHYSICAL_GOODS,
                amount=random.uniform(50, 300),
                last_updated=current_date
            ))
        elif agent_type == AgentType.GOVERNMENT:
            # Government has influence
            resources.append(ResourceBalance(
                resource_type=ResourceType.INFLUENCE,
                amount=random.uniform(100, 500),
                last_updated=current_date
            ))
        
        # Generate skills
        possible_skills = [
            "Programming", "Engineering", "Medicine", "Agriculture", "Mining",
            "Trading", "Leadership", "Manufacturing", "Entertainment", "Education",
            "Security", "Terraforming", "Astrogation", "Hacking", "Biotech",
            "Negotiation", "Research", "Artistry", "Logistics", "Espionage"
        ]
        
        skills = {}
        num_skills = random.randint(1, 5)
        for _ in range(num_skills):
            skill = random.choice(possible_skills)
            skills[skill] = random.uniform(0.3, 0.9)  # Immigrants often have developed skills
        
        # Common locations for arrival
        arrival_locations = [
            "Mars Central", "Olympus City", "Phobos Station"
        ]
        
        return Agent(
            name=name,
            agent_type=agent_type,
            faction=agent_faction,
            age_days=age_in_days,
            birth_date=birth_date,
            personality=personality,
            resources=resources,
            location=random.choice(arrival_locations),
            skills=skills
        )
    
    def _process_emigration(
        self, 
        agents: Dict[str, Agent], 
        current_date: datetime,
        emigration_rate: float
    ) -> List[PopulationEvent]:
        """Process emigration of existing agents
        
        Args:
            agents: Dictionary of agent_id -> Agent
            current_date: Current simulation date
            emigration_rate: Adjusted emigration rate
            
        Returns:
            List of emigration events
        """
        emigration_events = []
        
        # Process each living agent for potential emigration
        for agent_id, agent in agents.items():
            if not agent.is_alive:
                continue
            
            # Base emigration chance
            base_chance = emigration_rate
            
            # Adjust for agent type - corporations less likely to leave
            type_factor = {
                AgentType.INDIVIDUAL: 1.0,
                AgentType.CORPORATION: 0.2,
                AgentType.COLLECTIVE: 0.4,
                AgentType.GOVERNMENT: 0.3,
                AgentType.AI: 0.8
            }.get(agent.agent_type, 1.0)
            
            # Adjust for faction - underground more likely to leave during tough times
            faction_factor = {
                AgentFaction.TERRA_CORP: 1.2,  # More likely to return to Terra
                AgentFaction.MARS_NATIVE: 0.3,  # Less likely to leave home
                AgentFaction.INDEPENDENT: 1.0,
                AgentFaction.GOVERNMENT: 0.5,
                AgentFaction.UNDERGROUND: 1.5
            }.get(agent.faction, 1.0)
            
            # Adjust for needs - more likely to leave if needs aren't met
            needs_factor = 1.0
            if agent.needs.subsistence < 0.3 or agent.needs.security < 0.3:
                needs_factor = 2.0
            
            # Calculate final chance
            emigration_chance = base_chance * type_factor * faction_factor * needs_factor
            
            # Check for emigration
            if random.random() < emigration_chance:
                # Determine reason
                if agent.needs.subsistence < 0.3:
                    reason = "Seeking better living conditions"
                elif agent.needs.security < 0.3:
                    reason = "Security concerns"
                elif agent.faction == AgentFaction.TERRA_CORP:
                    reason = "Recalled to Terra headquarters"
                else:
                    reasons = [
                        "Better opportunities elsewhere", 
                        "Family obligations", 
                        "New assignment", 
                        "Personal reasons"
                    ]
                    reason = random.choice(reasons)
                
                # Update agent
                agent.is_alive = False  # Represents leaving the simulation
                agent.death_date = current_date  # Reuse this field for emigration date
                
                # Create event
                event = PopulationEvent(
                    event_type="emigration",
                    agent_id=agent.id,
                    timestamp=current_date,
                    reason=reason
                )
                emigration_events.append(event)
                
                logger.info(f"Agent {agent.name} ({agent.id}) has emigrated. Reason: {reason}")
        
        return emigration_events
    
    def get_population_statistics(self, agents: Dict[str, Agent]) -> Dict[str, Any]:
        """Get statistics about the current population
        
        Args:
            agents: Dictionary of agent_id -> Agent
            
        Returns:
            Dictionary of population statistics
        """
        # Count living agents
        living_agents = [a for a in agents.values() if a.is_alive]
        
        # Count by faction
        faction_counts = {}
        for faction in AgentFaction:
            faction_counts[faction.value] = len([a for a in living_agents if a.faction == faction])
        
        # Count by type
        type_counts = {}
        for agent_type in AgentType:
            type_counts[agent_type.value] = len([a for a in living_agents if a.agent_type == agent_type])
        
        # Age demographics
        age_groups = {
            "0-5 years": 0,      # 0-1825 days
            "5-15 years": 0,     # 1826-5475 days
            "15-30 years": 0,    # 5476-10950 days
            "30-50 years": 0,    # 10951-18250 days
            "50+ years": 0       # 18251+ days
        }
        
        for agent in living_agents:
            if agent.age_days <= 1825:
                age_groups["0-5 years"] += 1
            elif agent.age_days <= 5475:
                age_groups["5-15 years"] += 1
            elif agent.age_days <= 10950:
                age_groups["15-30 years"] += 1
            elif agent.age_days <= 18250:
                age_groups["30-50 years"] += 1
            else:
                age_groups["50+ years"] += 1
        
        # Recent events
        recent_events = {
            "births": len(self.recent_births),
            "deaths": len(self.recent_deaths)
        }
        
        # Calculate adjusted rates
        adjusted_rates = self._adjust_rates_for_scarcity()
        
        return {
            "total_population": len(living_agents),
            "deceased": len(agents) - len(living_agents),
            "by_faction": faction_counts,
            "by_type": type_counts,
            "by_age": age_groups,
            "recent_events": recent_events,
            "current_rates": adjusted_rates
        }