import random
import logging
import json
from typing import Dict, List, Optional, Any, Tuple, Set
from datetime import datetime, timedelta
import instructor
from openai import OpenAI

from ..models.base import (
    Agent, EconomicInteraction, EconomicInteractionType, 
    NarrativeEvent, NarrativeArc, SimulationState
)
from ..models.actions import AgentAction, ActionType

logger = logging.getLogger(__name__)

class NarrativeGenerator:
    """Generates narrative content from simulation events"""
    
    def __init__(
        self, 
        ollama_base_url: str = "http://localhost:11434/v1",
        model_name: str = "gemma:1b",
        temperature: float = 0.8,
        verbosity: int = 3,
        cyberpunk_flavor: float = 0.7
    ):
        """Initialize the narrative generator
        
        Args:
            ollama_base_url: Base URL for Ollama API
            model_name: Name of the model to use
            temperature: Temperature for LLM generation (0.0-1.0)
            verbosity: Level of narrative detail (1-5)
            cyberpunk_flavor: How strongly to emphasize cyberpunk elements (0.0-1.0)
        """
        self.model_name = model_name
        self.temperature = temperature
        self.verbosity = verbosity
        self.cyberpunk_flavor = cyberpunk_flavor
        
        # Initialize OpenAI-compatible client with Instructor
        self.client = instructor.from_openai(
            OpenAI(
                base_url=ollama_base_url,
                api_key="ollama",  # Required but unused
            ),
            mode=instructor.Mode.JSON
        )
        
        # Track active narrative arcs
        self.active_arcs: Dict[str, NarrativeArc] = {}
        
        # Track agent backgrounds
        self.agent_backgrounds: Dict[str, str] = {}
        
        # Recent events for context
        self.recent_events: List[NarrativeEvent] = []
        
        # Track interesting relationships
        self.interesting_relationships: Set[Tuple[str, str]] = set()
    
    def _generate_event_description(
        self, 
        interaction: Optional[EconomicInteraction] = None,
        action: Optional[AgentAction] = None,
        agents: Dict[str, Agent] = {}
    ) -> str:
        """Generate a narrative description of an event using the LLM
        
        Args:
            interaction: The economic interaction (if applicable)
            action: The agent action (if applicable)
            agents: Dictionary of agent_id -> Agent for context
            
        Returns:
            A narrative description of the event
        """
        # Build the prompt based on what we're describing
        prompt = "Generate a brief cyberpunk Mars narrative description of this event:\n\n"
        
        if interaction:
            prompt += self._build_interaction_prompt(interaction, agents)
        elif action:
            prompt += self._build_action_prompt(action, agents)
        else:
            return "An unremarkable event occurred."
        
        # Add cyberpunk flavor instruction
        if self.cyberpunk_flavor > 0.5:
            prompt += "\nUse strong cyberpunk language, themes, and imagery in your description."
        
        # Add verbosity instruction
        if self.verbosity == 1:
            prompt += "\nKeep it extremely brief, just 1-2 sentences."
        elif self.verbosity == 2:
            prompt += "\nKeep it brief, 2-3 sentences."
        elif self.verbosity == 3:
            prompt += "\nProvide a moderate amount of detail, 3-4 sentences."
        elif self.verbosity == 4:
            prompt += "\nProvide good detail, 4-6 sentences."
        elif self.verbosity >= 5:
            prompt += "\nProvide rich detail, 6-8 sentences."
        
        try:
            # Call the LLM for narrative generation
            messages = [
                {"role": "system", "content": "You are a cyberpunk narrative generator for a Mars economy simulation. Generate vivid, engaging narrative descriptions of events in a cyberpunk Mars colony in the year 2993."},
                {"role": "user", "content": prompt}
            ]
            
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=self.temperature,
                max_tokens=250
            )
            
            description = response.choices[0].message.content.strip()
            
            # Remove any quotes the LLM might add
            if description.startswith('"') and description.endswith('"'):
                description = description[1:-1]
            
            return description
            
        except Exception as e:
            logger.error(f"Error generating narrative description: {str(e)}")
            
            # Fallback descriptions
            if interaction:
                return self._generate_fallback_interaction_description(interaction, agents)
            elif action:
                return self._generate_fallback_action_description(action, agents)
            else:
                return "An event occurred in the Mars colony."
    
    def _build_interaction_prompt(self, interaction: EconomicInteraction, agents: Dict[str, Agent]) -> str:
        """Build a prompt for describing an economic interaction
        
        Args:
            interaction: The economic interaction
            agents: Dictionary of agent_id -> Agent for context
            
        Returns:
            A prompt for the LLM
        """
        # Base information
        prompt = f"Interaction type: {interaction.interaction_type.value}\n"
        
        # Add participant information
        participant_info = []
        for agent_id, role in interaction.participants.items():
            if agent_id in agents:
                agent = agents[agent_id]
                participant_info.append(f"{agent.name} ({role.value}, {agent.faction.value})")
            else:
                participant_info.append(f"Unknown agent ({role.value})")
        
        prompt += f"Participants: {', '.join(participant_info)}\n"
        
        # Add outcome information
        if interaction.is_complete and interaction.outcomes:
            outcome_info = []
            for outcome in interaction.outcomes:
                agent_id = outcome.agent_id
                agent_name = agents[agent_id].name if agent_id in agents else "Unknown agent"
                
                # Calculate resource changes
                resource_changes = []
                for before in outcome.resources_before:
                    # Find matching "after" resource
                    after = next((a for a in outcome.resources_after if a.resource_type == before.resource_type), None)
                    if after:
                        change = after.amount - before.amount
                        if abs(change) > 0.01:  # Only report meaningful changes
                            direction = "gained" if change > 0 else "lost"
                            resource_changes.append(f"{direction} {abs(change):.2f} {before.resource_type.value}")
                
                # Add strategy if available
                strategy_info = ""
                if outcome.strategy_used:
                    strategy_info = f" using {outcome.strategy_used.strategy_type} strategy"
                
                outcome_str = f"{agent_name}{strategy_info} {', '.join(resource_changes)}"
                outcome_info.append(outcome_str)
            
            prompt += f"Outcomes: {'. '.join(outcome_info)}\n"
        
        # Add specific interaction details based on type
        params = interaction.parameters
        if interaction.interaction_type == EconomicInteractionType.ULTIMATUM:
            prompt += f"Details: A {params.get('total_amount', '?')} {params.get('resource_type', '?')} ultimatum with {params.get('proposed_amount', '?')} offered. "
            prompt += f"The offer was {'accepted' if params.get('response', False) else 'rejected'}.\n"
        
        elif interaction.interaction_type == EconomicInteractionType.TRUST:
            prompt += f"Details: Initial investment of {params.get('invested_amount', '?')} {params.get('resource_type', '?')}, "
            prompt += f"multiplied to {params.get('multiplied_amount', '?')}, with {params.get('returned_amount', '?')} returned.\n"
        
        elif interaction.interaction_type == EconomicInteractionType.PUBLIC_GOODS:
            contributions = params.get('contributions', {})
            avg_contribution = sum(contributions.values()) / len(contributions) if contributions else 0
            prompt += f"Details: {len(contributions)} agents contributed to a public good, average contribution {avg_contribution:.2f}.\n"
        
        # Add narrative significance
        prompt += f"Narrative significance: {interaction.narrative_significance:.2f} (0-1 scale)\n"
        
        return prompt
    
    def _build_action_prompt(self, action: AgentAction, agents: Dict[str, Agent]) -> str:
        """Build a prompt for describing an agent action
        
        Args:
            action: The agent action
            agents: Dictionary of agent_id -> Agent for context
            
        Returns:
            A prompt for the LLM
        """
        # Get the agent
        agent = agents.get(action.agent_id, None)
        agent_name = agent.name if agent else "Unknown agent"
        agent_faction = agent.faction.value if agent else "unknown faction"
        
        # Base information
        prompt = f"Action type: {action.action_type.value}\n"
        prompt += f"Agent: {agent_name} ({agent_faction})\n"
        
        # Add agent's reasoning if available
        if action.reasoning:
            prompt += f"Agent's reasoning: {action.reasoning}\n"
        
        # Add action-specific details
        if action.action_type == ActionType.REST:
            prompt += "Details: The agent decided to rest and recover.\n"
        
        elif action.action_type == ActionType.OFFER and action.offer_data:
            target_id = action.offer_data.target_agent_id
            target_name = agents[target_id].name if target_id in agents else "another agent"
            prompt += f"Details: Offered {action.offer_data.offer_amount} {action.offer_data.offer_resource_type} "
            prompt += f"to {target_name} in exchange for {action.offer_data.request_amount} {action.offer_data.request_resource_type}.\n"
        
        elif action.action_type == ActionType.SEARCH_JOB:
            prompt += "Details: The agent is searching for employment.\n"
            
        elif action.action_type == ActionType.WORK and action.work_data:
            prompt += f"Details: Working on job {action.work_data.job_id} with effort level {action.work_data.effort_level}.\n"
            
        elif action.action_type == ActionType.BUY and action.buy_data:
            prompt += f"Details: Attempting to buy {action.buy_data.quantity} {action.buy_data.item_type}"
            if action.buy_data.max_price:
                prompt += f" for at most {action.buy_data.max_price} per unit"
            if action.buy_data.seller_id:
                seller_name = agents[action.buy_data.seller_id].name if action.buy_data.seller_id in agents else "a specific seller"
                prompt += f" from {seller_name}"
            prompt += ".\n"
            
        elif action.action_type == ActionType.ACCEPT and action.accept_data:
            prompt += f"Details: Accepted offer {action.accept_data.offer_id}.\n"
            
        elif action.action_type == ActionType.REJECT and action.reject_data:
            prompt += f"Details: Rejected offer {action.reject_data.offer_id}"
            if action.reject_data.reason:
                prompt += f" because: {action.reject_data.reason}"
            prompt += ".\n"
        
        return prompt
    
    def _generate_fallback_interaction_description(self, interaction: EconomicInteraction, agents: Dict[str, Agent]) -> str:
        """Generate a fallback description for an interaction when LLM fails
        
        Args:
            interaction: The economic interaction
            agents: Dictionary of agent_id -> Agent for context
            
        Returns:
            A fallback description
        """
        # Extract participant names
        participant_names = []
        for agent_id in interaction.participants:
            if agent_id in agents:
                participant_names.append(agents[agent_id].name)
            else:
                participant_names.append("an unknown agent")
        
        # Basic description based on interaction type
        if interaction.interaction_type == EconomicInteractionType.ULTIMATUM:
            description = f"{participant_names[0]} made an ultimatum offer to {participant_names[1]}."
            if interaction.is_complete:
                response = interaction.parameters.get("response", None)
                if response is True:
                    description += f" The offer was accepted."
                elif response is False:
                    description += f" The offer was rejected."
            
        elif interaction.interaction_type == EconomicInteractionType.TRUST:
            description = f"{participant_names[0]} initiated a trust exchange with {participant_names[1]}."
            if interaction.is_complete:
                returned = interaction.parameters.get("returned_amount", 0)
                invested = interaction.parameters.get("invested_amount", 0)
                if returned >= invested:
                    description += f" Trust was honored with a positive return."
                else:
                    description += f" Trust was broken when the return was less than expected."
            
        elif interaction.interaction_type == EconomicInteractionType.PUBLIC_GOODS:
            description = f"{', '.join(participant_names[:-1])}, and {participant_names[-1]} participated in a public goods game."
            
        else:
            description = f"{', '.join(participant_names)} engaged in a {interaction.interaction_type.value} interaction."
        
        return description
    
    def _generate_fallback_action_description(self, action: AgentAction, agents: Dict[str, Agent]) -> str:
        """Generate a fallback description for an action when LLM fails
        
        Args:
            action: The agent action
            agents: Dictionary of agent_id -> Agent for context
            
        Returns:
            A fallback description
        """
        # Get agent name
        agent_name = agents[action.agent_id].name if action.agent_id in agents else "An agent"
        
        # Basic description based on action type
        if action.action_type == ActionType.REST:
            return f"{agent_name} decided to rest and recover energy."
            
        elif action.action_type == ActionType.OFFER:
            target_id = action.offer_data.target_agent_id if action.offer_data else None
            target_name = agents[target_id].name if target_id and target_id in agents else "another agent"
            return f"{agent_name} made an offer to {target_name}."
            
        elif action.action_type == ActionType.NEGOTIATE:
            return f"{agent_name} attempted to negotiate an existing offer."
            
        elif action.action_type == ActionType.ACCEPT:
            return f"{agent_name} accepted an offer."
            
        elif action.action_type == ActionType.REJECT:
            return f"{agent_name} rejected an offer."
            
        elif action.action_type == ActionType.SEARCH_JOB:
            return f"{agent_name} searched for employment."
            
        elif action.action_type == ActionType.WORK:
            return f"{agent_name} performed work at their job."
            
        elif action.action_type == ActionType.BUY:
            item = action.buy_data.item_type if action.buy_data else "goods"
            return f"{agent_name} attempted to purchase {item}."
            
        else:
            return f"{agent_name} performed a {action.action_type.value} action."
    
    def generate_agent_background(self, agent: Agent) -> str:
        """Generate a background story for a new agent
        
        Args:
            agent: The agent to generate a background for
            
        Returns:
            A narrative background for the agent
        """
        # Check if we already have a background for this agent
        if agent.id in self.agent_backgrounds:
            return self.agent_backgrounds[agent.id]
        
        # Build the prompt for agent background
        prompt = f"Generate a brief cyberpunk Mars background story for this character:\n\n"
        prompt += f"Name: {agent.name}\n"
        prompt += f"Faction: {agent.faction.value}\n"
        prompt += f"Personality: "
        
        # Add personality traits
        traits = []
        if agent.personality.cooperativeness > 0.7:
            traits.append("highly cooperative")
        elif agent.personality.cooperativeness < 0.3:
            traits.append("uncooperative")
        
        if agent.personality.risk_tolerance > 0.7:
            traits.append("risk-taking")
        elif agent.personality.risk_tolerance < 0.3:
            traits.append("risk-averse")
        
        if agent.personality.fairness_preference > 0.7:
            traits.append("strongly values fairness")
        elif agent.personality.fairness_preference < 0.3:
            traits.append("unconcerned with fairness")
        
        if agent.personality.altruism > 0.7:
            traits.append("altruistic")
        elif agent.personality.altruism < 0.3:
            traits.append("selfish")
        
        if agent.personality.rationality > 0.7:
            traits.append("highly rational")
        elif agent.personality.rationality < 0.3:
            traits.append("impulsive")
        
        if agent.personality.long_term_orientation > 0.7:
            traits.append("future-focused")
        elif agent.personality.long_term_orientation < 0.3:
            traits.append("present-focused")
        
        prompt += ", ".join(traits) + "\n"
        
        # Add notable skills
        if agent.skills:
            top_skills = sorted(agent.skills.items(), key=lambda x: x[1], reverse=True)[:3]
            prompt += f"Top Skills: {', '.join([skill for skill, level in top_skills])}\n"
        
        # Add cyberpunk flavor instruction
        prompt += "\nWrite a 3-5 sentence cyberpunk-style background that explains how they ended up on Mars and their current situation. Include interesting details about their past and motivations."
        
        try:
            # Call the LLM for background generation
            messages = [
                {"role": "system", "content": "You are a cyberpunk character background generator for a Mars colony simulation set in 2993. Create evocative, memorable character backgrounds with cyberpunk themes and technology."},
                {"role": "user", "content": prompt}
            ]
            
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=self.temperature,
                max_tokens=200
            )
            
            background = response.choices[0].message.content.strip()
            
            # Remove any quotes the LLM might add
            if background.startswith('"') and background.endswith('"'):
                background = background[1:-1]
            
            # Store the background for future reference
            self.agent_backgrounds[agent.id] = background
            
            return background
            
        except Exception as e:
            logger.error(f"Error generating agent background: {str(e)}")
            
            # Generate a fallback background
            faction_backgrounds = {
                AgentFaction.TERRA_CORP: f"{agent.name} is a corporate representative sent from Earth to oversee Terra Corp interests on Mars.",
                AgentFaction.MARS_NATIVE: f"{agent.name} was born and raised in the domes of Mars, never having visited Earth.",
                AgentFaction.INDEPENDENT: f"{agent.name} came to Mars seeking freedom from Earth's control and now operates as an independent contractor.",
                AgentFaction.GOVERNMENT: f"{agent.name} works for the Mars Colonial Authority, maintaining order in the settlements.",
                AgentFaction.UNDERGROUND: f"{agent.name} operates in the shadows of Mars society, involved in various underground activities."
            }
            
            background = faction_backgrounds.get(agent.faction, f"{agent.name} is a resident of Mars in the year 2993.")
            self.agent_backgrounds[agent.id] = background
            
            return background
    
    def generate_narrative_event(
        self, 
        interaction: Optional[EconomicInteraction] = None,
        action: Optional[AgentAction] = None,
        agents: Dict[str, Agent] = {},
        timestamp: Optional[datetime] = None
    ) -> NarrativeEvent:
        """Generate a narrative event from an interaction or action
        
        Args:
            interaction: The economic interaction (if applicable)
            action: The agent action (if applicable)
            agents: Dictionary of agent_id -> Agent for context
            timestamp: Event timestamp (defaults to now)
            
        Returns:
            A NarrativeEvent object
        """
        if not timestamp:
            timestamp = datetime.now()
        
        # Determine agents involved
        agents_involved = []
        if interaction:
            agents_involved = list(interaction.participants.keys())
            event_title = f"{interaction.interaction_type.value.title()} Interaction"
            interaction_id = interaction.id
            # Set significance based on interaction's narrative_significance
            significance = interaction.narrative_significance
        elif action:
            agents_involved = [action.agent_id]
            event_title = f"{action.action_type.value.title()} Action"
            interaction_id = None
            # Set significance based on action type
            action_significance = {
                ActionType.REST: 0.1,
                ActionType.OFFER: 0.5,
                ActionType.NEGOTIATE: 0.6,
                ActionType.ACCEPT: 0.5,
                ActionType.REJECT: 0.6,
                ActionType.SEARCH_JOB: 0.3,
                ActionType.WORK: 0.2,
                ActionType.BUY: 0.3,
                ActionType.SELL: 0.3,
                ActionType.MOVE: 0.4,
                ActionType.LEARN: 0.3,
                ActionType.SOCIALIZE: 0.4,
                ActionType.INVEST: 0.5,
                ActionType.DONATE: 0.6,
                ActionType.PRODUCE: 0.3,
                ActionType.CONSUME: 0.2,
                ActionType.STEAL: 0.8,
                ActionType.SABOTAGE: 0.9,
                ActionType.FORM_COALITION: 0.7
            }
            significance = action_significance.get(action.action_type, 0.3)
        else:
            event_title = "Simulation Event"
            interaction_id = None
            significance = 0.2
        
        # Get agent names for the title
        agent_names = []
        for agent_id in agents_involved:
            if agent_id in agents:
                agent_names.append(agents[agent_id].name)
        
        if agent_names:
            if len(agent_names) == 1:
                event_title = f"{agent_names[0]}'s {event_title}"
            elif len(agent_names) == 2:
                event_title = f"{agent_names[0]} and {agent_names[1]}'s {event_title}"
            else:
                event_title = f"{agent_names[0]} et al.'s {event_title}"
        
        # Generate description
        description = self._generate_event_description(interaction, action, agents)
        
        # Create tags
        tags = []
        if interaction:
            tags.append(interaction.interaction_type.value)
            if interaction.is_complete:
                tags.append("completed")
        elif action:
            tags.append(action.action_type.value)
        
        for agent_id in agents_involved:
            if agent_id in agents:
                tags.append(agents[agent_id].faction.value)
        
        # Create the event
        event = NarrativeEvent(
            timestamp=timestamp,
            title=event_title,
            description=description,
            agents_involved=agents_involved,
            interaction_id=interaction_id,
            significance=significance,
            tags=tags
        )
        
        # Add to recent events
        self.recent_events.append(event)
        if len(self.recent_events) > 20:  # Keep only last 20 events
            self.recent_events.pop(0)
        
        return event
    
    def check_for_new_arcs(self, event: NarrativeEvent, agents: Dict[str, Agent]) -> Optional[NarrativeArc]:
        """Check if a new narrative arc should be created based on this event
        
        Args:
            event: The newly created event
            agents: Dictionary of agent_id -> Agent for context
            
        Returns:
            A new NarrativeArc if one should be created, None otherwise
        """
        # Look for patterns in recent events that might suggest a narrative arc
        
        # Example: If the same agents have interacted multiple times recently
        agent_pairs = {}
        for recent_event in self.recent_events[-10:]:  # Look at last 10 events
            if len(recent_event.agents_involved) == 2:
                pair = tuple(sorted(recent_event.agents_involved))
                agent_pairs[pair] = agent_pairs.get(pair, 0) + 1
        
        # If any pair has interacted 3+ times, consider creating an arc
        for pair, count in agent_pairs.items():
            if count >= 3 and pair not in self.interesting_relationships:
                self.interesting_relationships.add(pair)
                
                # Get agent names
                agent1 = agents.get(pair[0], None)
                agent2 = agents.get(pair[1], None)
                
                if agent1 and agent2:
                    # Create a new arc
                    arc_title = f"Developing Relationship: {agent1.name} & {agent2.name}"
                    arc = NarrativeArc(
                        title=arc_title,
                        description=f"A pattern of interactions between {agent1.name} and {agent2.name} suggests an evolving relationship.",
                        events=[e.id for e in self.recent_events if set(pair).issubset(set(e.agents_involved))],
                        agents_involved=list(pair),
                        start_time=self.recent_events[-1].timestamp
                    )
                    
                    # Add to active arcs
                    self.active_arcs[arc.id] = arc
                    
                    return arc
        
        # Example: Check for economic pattern arcs
        # TODO: Implement more sophisticated arc detection
        
        return None
    
    def update_active_arcs(self, event: NarrativeEvent) -> List[NarrativeArc]:
        """Update active narrative arcs with a new event
        
        Args:
            event: The newly created event
            
        Returns:
            List of updated arcs
        """
        updated_arcs = []
        
        for arc_id, arc in list(self.active_arcs.items()):
            # Check if this event should be part of this arc
            if set(arc.agents_involved).intersection(set(event.agents_involved)):
                # Add the event to the arc
                arc.events.append(event.id)
                updated_arcs.append(arc)
                
                # Check if the arc should be completed
                if len(arc.events) >= 10:  # Arbitrary limit
                    arc.is_complete = True
                    arc.end_time = event.timestamp
                    # Remove from active arcs
                    self.active_arcs.pop(arc_id, None)
        
        return updated_arcs
    
    def get_narrative_summary(self, time_period: str = "day") -> str:
        """Generate a summary of recent narrative events
        
        Args:
            time_period: The time period to summarize ("day", "week", "month")
            
        Returns:
            A narrative summary
        """
        if not self.recent_events:
            return "No notable events have occurred recently."
        
        # Build a prompt for the summary
        prompt = f"Generate a cyberpunk narrative summary of these recent events on Mars:\n\n"
        
        # Add recent events
        for i, event in enumerate(self.recent_events[-10:]):  # Last 10 events
            prompt += f"Event {i+1}: {event.title}\n{event.description}\n\n"
        
        # Add time period instructions
        prompt += f"\nCreate a compelling {time_period}ly summary that connects these events into a coherent narrative. Use vivid cyberpunk language and imagery about Mars in 2993."
        
        try:
            # Call the LLM for summary generation
            messages = [
                {"role": "system", "content": "You are a cyberpunk narrative generator for a Mars economy simulation. Create compelling, evocative summaries that capture the essence of life on Mars in 2993."},
                {"role": "user", "content": prompt}
            ]
            
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=self.temperature,
                max_tokens=500
            )
            
            summary = response.choices[0].message.content.strip()
            return summary
            
        except Exception as e:
            logger.error(f"Error generating narrative summary: {str(e)}")
            
            # Generate a fallback summary
            event_titles = [e.title for e in self.recent_events[-5:]]
            return f"Recent notable events on Mars include: {'; '.join(event_titles)}."

# Factory function to create a narrative generator
def create_narrative_generator(
    ollama_base_url: str = "http://localhost:11434/v1",
    model_name: str = "gemma:1b",
    temperature: float = 0.8,
    verbosity: int = 3,
    cyberpunk_flavor: float = 0.7
) -> NarrativeGenerator:
    """Create a narrative generator
    
    Args:
        ollama_base_url: Base URL for Ollama API
        model_name: Name of the model to use
        temperature: Temperature for LLM generation (0.0-1.0)
        verbosity: Level of narrative detail (1-5)
        cyberpunk_flavor: How strongly to emphasize cyberpunk elements (0.0-1.0)
        
    Returns:
        A narrative generator
    """
    return NarrativeGenerator(
        ollama_base_url=ollama_base_url,
        model_name=model_name,
        temperature=temperature,
        verbosity=verbosity,
        cyberpunk_flavor=cyberpunk_flavor
    )