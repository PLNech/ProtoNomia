"""
Narrator module for ProtoNomia.
This module handles the generation of narrative events from economic interactions.
"""
import logging
import random
from datetime import datetime
from typing import List, Dict, Optional, Any

from models.base import (
    Agent, EconomicInteraction, EconomicInteractionType, InteractionRole, 
    NarrativeEvent, NarrativeArc
)

# Initialize logger
logger = logging.getLogger(__name__)


class Narrator:
    """
    Narrator class for generating narrative events and arcs from economic interactions.
    The narrator creates engaging stories from the events in the simulation.
    """
    
    def __init__(self, verbosity: int = 3):
        """
        Initialize the narrator.
        
        Args:
            verbosity: Level of detail in generated narratives (1-5)
        """
        self.verbosity = max(1, min(5, verbosity))  # Ensure verbosity is between 1 and 5
        logger.info(f"Initialized narrator with verbosity level {self.verbosity}")
    
    def generate_event_from_interaction(
        self, 
        interaction: EconomicInteraction,
        agents: List[Agent]
    ) -> NarrativeEvent:
        """
        Generate a narrative event from an economic interaction.
        
        Args:
            interaction: The economic interaction to generate a narrative from
            agents: List of agents involved in the interaction
            
        Returns:
            NarrativeEvent: The generated narrative event
        """
        # Map agent IDs to agent objects for easier lookup
        agent_map = {agent.id: agent for agent in agents}
        
        # Get participant agent names
        participant_names = {}
        for agent_id, role in interaction.participants.items():
            if agent_id in agent_map:
                participant_names[role] = agent_map[agent_id].name
        
        # Generate title and description based on interaction type
        title, description, tags = "", "", []
        
        if interaction.interaction_type == EconomicInteractionType.ULTIMATUM:
            title, description, tags = self._generate_ultimatum_narrative(
                interaction, participant_names, agent_map
            )
        elif interaction.interaction_type == EconomicInteractionType.TRUST:
            title, description, tags = self._generate_trust_narrative(
                interaction, participant_names, agent_map
            )
        else:
            # Generic fallback for other interaction types
            title, description, tags = self._generate_generic_narrative(
                interaction, participant_names, agent_map
            )
        
        # Create and return the narrative event
        event = NarrativeEvent(
            timestamp=datetime.now(),
            title=title,
            description=description,
            agents_involved=list(interaction.participants.keys()),
            interaction_id=interaction.id,
            significance=interaction.narrative_significance,
            tags=tags
        )
        
        logger.debug(f"Generated narrative event: {title}")
        return event
    
    def _generate_ultimatum_narrative(
        self, 
        interaction: EconomicInteraction,
        participant_names: Dict[InteractionRole, str],
        agent_map: Dict[str, Agent]
    ) -> tuple:
        """Generate narrative for an Ultimatum Game interaction"""
        # Extract parameters
        total_amount = interaction.parameters.get("total_amount", 0)
        offer_amount = interaction.parameters.get("offer_amount", 0)
        responder_accepts = interaction.parameters.get("responder_accepts", False)
        currency = interaction.parameters.get("currency", "credits")
        
        # Get agent names
        proposer_name = participant_names.get(InteractionRole.PROPOSER, "Unknown Proposer")
        responder_name = participant_names.get(InteractionRole.RESPONDER, "Unknown Responder")
        
        # Calculate offer fairness
        fairness = offer_amount / total_amount if total_amount > 0 else 0
        
        # Generate title based on the interaction outcome
        if responder_accepts:
            if fairness < 0.3:
                title = f"{responder_name} Accepts Unfair Deal from {proposer_name}"
                tags = ["unfair_deal", "acceptance", "ultimatum"]
            elif fairness > 0.5:
                title = f"{proposer_name} Makes Fair Offer to {responder_name}"
                tags = ["fair_deal", "cooperation", "ultimatum"]
            else:
                title = f"{proposer_name} and {responder_name} Conclude Deal"
                tags = ["deal", "bargaining", "ultimatum"]
        else:
            if fairness > 0.4:
                title = f"{responder_name} Rejects Reasonable Offer from {proposer_name}"
                tags = ["rejection", "principle", "ultimatum"]
            else:
                title = f"{responder_name} Rejects Unfair Offer from {proposer_name}"
                tags = ["unfair_deal", "rejection", "ultimatum"]
        
        # Generate description with varying detail based on verbosity
        if self.verbosity >= 4:
            # High verbosity - detailed description
            if responder_accepts:
                if fairness < 0.3:
                    description = (
                        f"In a tense negotiation at {self._get_random_location()}, {proposer_name} offered a mere {offer_amount} "
                        f"{currency} of a {total_amount} {currency} pot to {responder_name}. Despite the clearly unfair "
                        f"terms, {responder_name} reluctantly accepted the offer, prioritizing some gain over none. "
                        f"The acceptance surprised onlookers, who whispered about {responder_name}'s desperation "
                        f"or perhaps a hidden debt to {proposer_name}. For their part, {proposer_name} walked away "
                        f"with a satisfied smirk, having secured {total_amount - offer_amount} {currency} "
                        f"from the deal."
                    )
                elif fairness > 0.5:
                    description = (
                        f"In a display of equitable negotiation at {self._get_random_location()}, {proposer_name} "
                        f"offered {offer_amount} {currency} from a total of {total_amount} {currency} to {responder_name}. "
                        f"The fair proposal was quickly accepted, creating a positive atmosphere and potentially "
                        f"strengthening future relations between them. Observers noted how {proposer_name}'s "
                        f"reputation for fairness might serve them well in Mars' tight-knit economic community."
                    )
                else:
                    description = (
                        f"At {self._get_random_location()}, {proposer_name} proposed a split of {total_amount} {currency}, "
                        f"offering {offer_amount} {currency} to {responder_name} and keeping {total_amount - offer_amount} "
                        f"{currency} for themselves. After brief consideration, {responder_name} accepted the terms. "
                        f"The somewhat uneven split raised a few eyebrows, but both parties seemed satisfied with the outcome."
                    )
            else:
                if fairness > 0.4:
                    description = (
                        f"In a surprising turn at {self._get_random_location()}, {responder_name} firmly rejected "
                        f"{proposer_name}'s offer of {offer_amount} {currency} from a {total_amount} {currency} pot. "
                        f"Despite the relatively balanced proposal, {responder_name} stood on principle, preferring "
                        f"to walk away with nothing rather than accept the terms. {proposer_name} appeared visibly "
                        f"frustrated, having miscalculated what would constitute an acceptable offer, and likewise "
                        f"left empty-handed."
                    )
                else:
                    description = (
                        f"At a tense meeting in {self._get_random_location()}, {proposer_name} attempted to impose unfavorable "
                        f"terms on {responder_name}, offering just {offer_amount} {currency} from a {total_amount} {currency} "
                        f"total. {responder_name} didn't hesitate to reject the insulting proposal, leaving {proposer_name} "
                        f"with nothing as well. Observers commented on {proposer_name}'s tactical error in underestimating "
                        f"{responder_name}'s dignity and willingness to sacrifice potential gain to punish unfairness."
                    )
        elif self.verbosity >= 2:
            # Medium verbosity - moderate description
            if responder_accepts:
                description = (
                    f"{proposer_name} offered {responder_name} {offer_amount} {currency} from a total of {total_amount} "
                    f"{currency}. {responder_name} accepted the offer, resulting in {proposer_name} keeping "
                    f"{total_amount - offer_amount} {currency} for themselves."
                )
            else:
                description = (
                    f"{proposer_name} offered {responder_name} {offer_amount} {currency} from a total of {total_amount} "
                    f"{currency}. {responder_name} rejected the offer, so both parties received nothing."
                )
        else:
            # Low verbosity - minimal description
            if responder_accepts:
                description = f"{proposer_name} offered {offer_amount}/{total_amount} {currency} to {responder_name} who accepted."
            else:
                description = f"{proposer_name} offered {offer_amount}/{total_amount} {currency} to {responder_name} who rejected."
        
        return title, description, tags
    
    def _generate_trust_narrative(
        self, 
        interaction: EconomicInteraction,
        participant_names: Dict[InteractionRole, str],
        agent_map: Dict[str, Agent]
    ) -> tuple:
        """Generate narrative for a Trust Game interaction"""
        # Extract parameters
        investment = interaction.parameters.get("investment_amount", 0)
        multiplier = interaction.parameters.get("multiplier", 3.0)
        returned = interaction.parameters.get("return_amount", 0)
        currency = interaction.parameters.get("currency", "credits")
        
        # Get agent names
        investor_name = participant_names.get(InteractionRole.INVESTOR, "Unknown Investor")
        trustee_name = participant_names.get(InteractionRole.TRUSTEE, "Unknown Trustee")
        
        # Calculate multiplied amount and return ratio
        multiplied = investment * multiplier
        return_ratio = returned / multiplied if multiplied > 0 else 0
        
        # Generate title based on the interaction details
        if investment > 5.0 and return_ratio < 0.2:
            title = f"{trustee_name} Betrays {investor_name}'s Trust"
            tags = ["betrayal", "distrust", "high_stakes"]
        elif investment > 5.0 and return_ratio > 0.5:
            title = f"{investor_name} and {trustee_name} Build Mutual Trust"
            tags = ["cooperation", "trust", "reciprocity"]
        elif investment < 2.0 and return_ratio > 0.7:
            title = f"{trustee_name} Shows Unexpected Generosity to {investor_name}"
            tags = ["generosity", "unexpected", "goodwill"]
        elif investment < 2.0:
            title = f"{investor_name} Shows Little Trust in {trustee_name}"
            tags = ["caution", "distrust", "minimal_risk"]
        else:
            title = f"{investor_name} Invests in {trustee_name}"
            tags = ["investment", "trust", "business"]
        
        # Generate description with varying detail based on verbosity
        if self.verbosity >= 4:
            # High verbosity - detailed description
            if investment > 5.0 and return_ratio < 0.2:
                description = (
                    f"In a dramatic display of broken trust at {self._get_random_location()}, {investor_name} took a significant "
                    f"risk by investing {investment} {currency} with {trustee_name}. The investment grew to {multiplied:.1f} "
                    f"{currency} under {trustee_name}'s management, but when the time came to share the profits, "
                    f"{trustee_name} returned a mere {returned:.1f} {currency} to {investor_name}, keeping the lion's share "
                    f"for themselves. The betrayal was met with murmurs throughout the Martian financial community, and "
                    f"{investor_name} was seen later drowning their sorrows at a local establishment, vowing never to "
                    f"trust so freely again."
                )
            elif investment > 5.0 and return_ratio > 0.5:
                description = (
                    f"A model partnership formed at {self._get_random_location()} when {investor_name} placed a substantial "
                    f"investment of {investment} {currency} in {trustee_name}'s hands. When the investment grew to "
                    f"{multiplied:.1f} {currency}, {trustee_name} honored their implicit agreement by returning "
                    f"{returned:.1f} {currency} to {investor_name}, keeping {multiplied - returned:.1f} {currency} "
                    f"for themselves. Observers noted that such demonstrations of mutual trust and fair dealing are "
                    f"what allow Mars' economy to thrive despite the harsh conditions. Both parties were seen later "
                    f"celebrating their successful venture."
                )
            elif investment < 2.0 and return_ratio > 0.7:
                description = (
                    f"In an unexpected turn of events at {self._get_random_location()}, {investor_name} made a token "
                    f"investment of just {investment} {currency} with {trustee_name}, clearly showing limited trust. "
                    f"When the amount grew to {multiplied:.1f} {currency}, {trustee_name} surprised everyone by "
                    f"returning {returned:.1f} {currency} to {investor_name} - a far more generous share than "
                    f"expected given the minimal initial trust. {investor_name} appeared both grateful and somewhat "
                    f"embarrassed, perhaps recognizing they had misjudged {trustee_name}'s character."
                )
            else:
                description = (
                    f"At {self._get_random_location()}, {investor_name} cautiously invested {investment} {currency} with "
                    f"{trustee_name}. The investment grew to {multiplied:.1f} {currency}, from which {trustee_name} "
                    f"returned {returned:.1f} {currency} to {investor_name}. The transaction proceeded without "
                    f"drama, though attentive observers might have noted the careful calculations both parties "
                    f"seemed to be making throughout the exchange."
                )
        elif self.verbosity >= 2:
            # Medium verbosity - moderate description
            description = (
                f"{investor_name} invested {investment} {currency} with {trustee_name}, which grew to "
                f"{multiplied:.1f} {currency}. {trustee_name} then returned {returned:.1f} {currency} to "
                f"{investor_name}, keeping {multiplied - returned:.1f} {currency}."
            )
        else:
            # Low verbosity - minimal description
            description = (
                f"{investor_name} invested {investment}, received {returned:.1f} back from {trustee_name} "
                f"(multiplier: {multiplier})."
            )
        
        return title, description, tags
    
    def _generate_generic_narrative(
        self, 
        interaction: EconomicInteraction,
        participant_names: Dict[InteractionRole, str],
        agent_map: Dict[str, Agent]
    ) -> tuple:
        """Generate a generic narrative for any interaction type"""
        interaction_type = interaction.interaction_type.value.replace('_', ' ').title()
        agent_names = list(participant_names.values())
        
        title = f"{interaction_type} between {' and '.join(agent_names)}"
        
        # Simple description based on verbosity
        if self.verbosity >= 3:
            description = (
                f"A {interaction_type} interaction took place involving {', '.join(agent_names)}. "
                f"This economic exchange occurred at {self._get_random_location()} and had parameters: "
                f"{', '.join([f'{k}: {v}' for k, v in interaction.parameters.items()])}."
            )
        else:
            description = f"{interaction_type} interaction between {' and '.join(agent_names)}."
        
        tags = [interaction.interaction_type.value, "economic_interaction"]
        
        return title, description, tags
    
    def create_arc(
        self, 
        title: str,
        description: str,
        events: List[NarrativeEvent],
        agents: List[Agent]
    ) -> NarrativeArc:
        """
        Create a narrative arc from a series of related events.
        
        Args:
            title: Title of the narrative arc
            description: Description of the narrative arc
            events: List of events in the arc
            agents: List of agents involved in the arc
            
        Returns:
            NarrativeArc: The created narrative arc
        """
        # Create narrative arc
        arc = NarrativeArc(
            title=title,
            description=description,
            events=[event.id for event in events],
            agents_involved=[agent.id for agent in agents],
            start_time=min(event.timestamp for event in events),
            is_complete=False
        )
        
        logger.info(f"Created narrative arc: {title} with {len(events)} events")
        return arc
    
    def generate_daily_summary(self, day: int, events: List[NarrativeEvent], agents: List[Agent]) -> str:
        """
        Generate a daily summary of significant events.
        
        Args:
            day: The day number
            events: List of narrative events for the day
            agents: List of all agents in the simulation
            
        Returns:
            str: A daily summary narrative
        """
        # Sort events by significance
        significant_events = sorted(events, key=lambda e: e.significance, reverse=True)
        
        # Map agent IDs to names
        agent_map = {agent.id: agent.name for agent in agents}
        
        # Start with a header
        summary = f"# Day {day} on Mars\n\n"
        
        # Add a general introduction
        summary += self._generate_daily_intro(day, len(events), len(agents)) + "\n\n"
        
        # Add significant events
        if significant_events:
            summary += "## Notable Events\n\n"
            
            for i, event in enumerate(significant_events[:min(5, len(significant_events))]):
                # Get agent names involved
                agent_names = [agent_map.get(agent_id, "Unknown") for agent_id in event.agents_involved]
                
                # Add event to summary
                summary += f"### {event.title}\n"
                summary += f"{event.description}\n\n"
        else:
            summary += "## A Quiet Day\n\nNo significant events were recorded today.\n\n"
        
        # Add a conclusion
        summary += self._generate_daily_conclusion(day, events)
        
        logger.info(f"Generated daily summary for day {day} with {len(events)} events")
        return summary
    
    def _generate_daily_intro(self, day: int, event_count: int, agent_count: int) -> str:
        """Generate an introduction for the daily summary"""
        intros = [
            f"Day {day} on Mars saw {event_count} notable interactions among the {agent_count} residents of the colony.",
            f"The Martian sun rose over the domes of the colony for the {day}th day, as {agent_count} residents went about their business.",
            f"Life continued in the Mars colony on Day {day}, with {event_count} economic exchanges recorded among the {agent_count} inhabitants.",
            f"The red dust swirled outside the habitats on Day {day}, while inside, {agent_count} colonists engaged in {event_count} economic interactions."
        ]
        return random.choice(intros)
    
    def _generate_daily_conclusion(self, day: int, events: List[NarrativeEvent]) -> str:
        """Generate a conclusion for the daily summary"""
        if events:
            conclusions = [
                "As the Martian night fell, residents returned to their habitats, contemplating the day's events and planning for tomorrow.",
                "Another day concluded on the red planet, with economic ripples from today's events sure to be felt in the days to come.",
                "The colony's economic web grew more complex with today's interactions, shaping the future of Mars society in subtle ways.",
                "With the day's business concluded, the colony's digital networks hummed with analysis of the changing economic landscape."
            ]
        else:
            conclusions = [
                "A peaceful day ended on Mars, with residents enjoying the relative calm before tomorrow's inevitable challenges.",
                "The quiet day gave residents time to maintain their habitats and prepare for future economic opportunities.",
                "Despite the lack of significant events, the underlying currents of the Martian economy continued to evolve.",
                "Sometimes, a day without major upheaval is exactly what a frontier economy needs to build long-term stability."
            ]
        return random.choice(conclusions)
    
    def _get_random_location(self) -> str:
        """Generate a random location in the Mars colony"""
        locations = [
            "Olympus Market",
            "Tharsis Trading Hub",
            "Valles Marineris Exchange",
            "Elysium Commons",
            "Hellas Basin Bazaar",
            "Arcadia Planitia Mall",
            "Utopia Business District",
            "Cydonia Market Square",
            "Syrtis Major Agora",
            "Acidalia Financial Center",
            "Chryse Marketplace",
            "Argyre Commerce Hub",
            "Promethei Terminal",
            "Amazonis Trade Center",
            "Isidis Commerce Zone"
        ]
        return random.choice(locations)