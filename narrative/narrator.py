"""
Narrator module for ProtoNomia.
This module handles the generation of narrative events from economic interactions.
"""
import logging
import random
from datetime import datetime
from typing import List, Dict, Optional, Any, Tuple

from models.base import (
    Agent, EconomicInteraction, InteractionRole,
    NarrativeEvent, NarrativeArc, ResourceType, ActionType
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
        for agent, role in interaction.participants.items():
            participant_names[role] = agent.name
        
        # Generate title and description based on interaction type
        title, description, tags = "", "", []
        
        if interaction.interaction_type == ActionType.JOB_APPLICATION:
            title, description, tags = self._generate_job_application_narrative(
                interaction, participant_names, agent_map
            )
        elif interaction.interaction_type == ActionType.JOB_OFFER:
            title, description, tags = self._generate_job_offer_narrative(
                interaction, participant_names, agent_map
            )
        elif interaction.interaction_type == ActionType.GOODS_PURCHASE:
            title, description, tags = self._generate_goods_purchase_narrative(
                interaction, participant_names, agent_map
            )
        elif interaction.interaction_type == ActionType.GOODS_SALE:
            title, description, tags = self._generate_goods_sale_narrative(
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
            agents_involved=[agent for agent in interaction.participants.keys()],
            interaction_id=interaction.id,
            significance=interaction.narrative_significance,
            tags=tags
        )
        
        logger.debug(f"Generated narrative event: {title}")
        return event
    
    def _generate_job_application_narrative(
        self, 
        interaction: EconomicInteraction,
        participant_names: Dict[InteractionRole, str],
        agent_map: Dict[str, Agent]
    ) -> tuple:
        """Generate narrative for a job application interaction"""
        # Extract parameters
        job_type = interaction.parameters.get("job_type", "Unknown")
        salary = interaction.parameters.get("salary", 0)
        successful = interaction.parameters.get("application_successful", False)
        
        # Get agent names
        initiator_name = participant_names.get(InteractionRole.INITIATOR, "Unknown Employer")
        responder_name = participant_names.get(InteractionRole.RESPONDER, "Unknown Applicant")
        
        # Generate title based on the interaction outcome
        if successful:
            title = f"{responder_name} Hired by {initiator_name} as {job_type}"
            tags = ["job_application", "hiring", "employment", "success"]
        else:
            title = f"{responder_name}'s Application for {job_type} at {initiator_name} Rejected"
            tags = ["job_application", "rejection", "unemployment", "failure"]
        
        # Generate description with varying detail based on verbosity
        if self.verbosity >= 4:
            # High verbosity - detailed description
            if successful:
                description = (
                    f"In a successful job negotiation at {self._get_random_location()}, {responder_name} applied for "
                    f"the position of {job_type} at {initiator_name}'s company. After reviewing the application "
                    f"and credentials, {initiator_name} decided to hire {responder_name} at a salary of {salary} "
                    f"credits per turn. Both parties seemed pleased with the arrangement, with {responder_name} "
                    f"expressing enthusiasm about the opportunity and {initiator_name} confident in finding a "
                    f"capable new employee. The position comes with typical Martian employment benefits including "
                    f"oxygen ration supplements and radiation shielding allowance."
                )
            else:
                description = (
                    f"At {self._get_random_location()}, {responder_name} applied for a {job_type} position "
                    f"with {initiator_name}'s company, but was ultimately rejected after consideration. "
                    f"The position, which offered {salary} credits per turn, attracted multiple qualified "
                    f"candidates. {initiator_name} expressed that while {responder_name} had impressive "
                    f"qualifications, they were looking for someone with more specialized experience in Martian "
                    f"operations. {responder_name} appeared disappointed but determined to continue the job search "
                    f"elsewhere in the colony."
                )
        elif self.verbosity >= 2:
            # Medium verbosity - moderate description
            if successful:
                description = (
                    f"{responder_name} applied for a {job_type} position with {initiator_name} and was hired at "
                    f"a salary of {salary} credits per turn. The new employment relationship looks promising "
                    f"for both parties."
                )
            else:
                description = (
                    f"{responder_name} applied for a {job_type} position with {initiator_name} offering {salary} "
                    f"credits per turn, but was rejected. The job search continues."
                )
        else:
            # Low verbosity - minimal description
            if successful:
                description = f"{responder_name} hired as {job_type} by {initiator_name} for {salary} credits."
            else:
                description = f"{responder_name} rejected for {job_type} position by {initiator_name}."
        
        return title, description, tags
    
    def _generate_goods_purchase_narrative(
        self, 
        interaction: EconomicInteraction,
        participant_names: Dict[InteractionRole, str],
        agent_map: Dict[str, Agent]
    ) -> tuple:
        """Generate narrative for a goods purchase interaction"""
        # Extract parameters
        resource_type = interaction.parameters.get("resource_type", ResourceType.CREDITS)
        if isinstance(resource_type, ResourceType):
            resource_name = resource_type.value
        else:
            resource_name = str(resource_type)
            
        purchase_amount = interaction.parameters.get("purchase_amount", 0)
        price_per_unit = interaction.parameters.get("price_per_unit", 0)
        total_price = interaction.parameters.get("total_price", 0)
        successful = interaction.parameters.get("purchase_successful", False)
        
        # Get agent names
        initiator_name = participant_names.get(InteractionRole.INITIATOR, "Unknown Seller")
        responder_name = participant_names.get(InteractionRole.RESPONDER, "Unknown Buyer")
        
        # Generate title based on the interaction outcome
        if successful:
            title = f"{responder_name} Purchases {resource_name} from {initiator_name}"
            tags = ["goods_purchase", "transaction", "commerce", "success"]
        else:
            failure_reason = interaction.parameters.get("failure_reason", "Unknown reason")
            title = f"{responder_name} Fails to Purchase {resource_name} from {initiator_name}"
            tags = ["goods_purchase", "failed_transaction", "commerce", "failure"]
        
        # Generate description with varying detail based on verbosity
        if self.verbosity >= 4:
            # High verbosity - detailed description
            if successful:
                description = (
                    f"At the bustling {self._get_random_location()}, {responder_name} approached {initiator_name}'s "
                    f"market stall with interest in acquiring {resource_name}. After examining the quality and "
                    f"negotiating briefly, they agreed on a price of {price_per_unit} credits per unit. "
                    f"{responder_name} purchased {purchase_amount} units for a total of {total_price} credits. "
                    f"Both parties appeared satisfied with the transaction, with {initiator_name} carefully counting "
                    f"out the credits while {responder_name} inspected their newly acquired goods. A small crowd of "
                    f"onlookers noted the exchange, with some commenting on the fair market value demonstrated."
                )
            else:
                description = (
                    f"At {self._get_random_location()}, {responder_name} attempted to purchase {purchase_amount} units "
                    f"of {resource_name} from {initiator_name} at {price_per_unit} credits per unit. Unfortunately, "
                    f"the transaction could not be completed due to {failure_reason}. {initiator_name} seemed "
                    f"disappointed but understanding, while {responder_name} appeared frustrated by the situation. "
                    f"Other market-goers continued their business around them, such failed transactions being a "
                    f"common enough sight in the Martian economy where resources can be scarce and credits tight."
                )
        elif self.verbosity >= 2:
            # Medium verbosity - moderate description
            if successful:
                description = (
                    f"{responder_name} purchased {purchase_amount} units of {resource_name} from {initiator_name} for "
                    f"{total_price} credits ({price_per_unit} per unit). The transaction was completed successfully "
                    f"at {self._get_random_location()}."
                )
            else:
                description = (
                    f"{responder_name} attempted to purchase {purchase_amount} units of {resource_name} from "
                    f"{initiator_name} for {total_price} credits, but the transaction failed due to {failure_reason}."
                )
        else:
            # Low verbosity - minimal description
            if successful:
                description = f"{responder_name} bought {purchase_amount} {resource_name} from {initiator_name} for {total_price} credits."
            else:
                description = f"{responder_name} failed to buy {resource_name} from {initiator_name}: {failure_reason}."
        
        return title, description, tags
    
    def _generate_job_offer_narrative(
        self, 
        interaction: EconomicInteraction,
        participant_names: Dict[InteractionRole, str],
        agent_map: Dict[str, Agent]
    ) -> tuple:
        """Generate narrative for a job offer interaction"""
        # Extract parameters
        job_type = interaction.parameters.get("job_type", "Unknown")
        salary = interaction.parameters.get("salary", 0)
        max_positions = interaction.parameters.get("max_positions", 1)
        
        # Get agent names
        employer_name = participant_names.get(InteractionRole.EMPLOYER, "Unknown Employer")
        
        # Generate title
        title = f"{employer_name} Posts New {job_type} Position"
        tags = ["job_offer", "employment", "opportunity", "job_market"]
        
        # Generate description based on verbosity
        if self.verbosity >= 4:
            description = (
                f"Economic opportunity has emerged at {self._get_random_location()} as {employer_name} announced "
                f"a new job opening for a {job_type} position. The role offers {salary} credits per turn and "
                f"seeks up to {max_positions} qualified individuals. According to the job listing, this position "
                f"requires specialized skills suitable for Mars' unique working conditions. {employer_name} "
                f"emphasized that candidates should have experience with the colony's systems and be prepared for "
                f"the challenging environment. The announcement generated buzz among job-seekers in the colony, "
                f"particularly those with relevant qualifications looking to secure stable employment."
            )
        elif self.verbosity >= 2:
            description = (
                f"{employer_name} has posted a job opening for a {job_type} position offering {salary} credits "
                f"per turn. The employer is looking to hire up to {max_positions} qualified candidate(s) with "
                f"relevant skills and experience."
            )
        else:
            description = f"{employer_name} offers {job_type} job: {salary} credits, {max_positions} position(s) available."
        
        return title, description, tags
    
    def _generate_goods_sale_narrative(
        self, 
        interaction: EconomicInteraction,
        participant_names: Dict[InteractionRole, str],
        agent_map: Dict[str, Agent]
    ) -> tuple:
        """Generate narrative for a goods sale listing interaction"""
        # Extract parameters
        resource_type = interaction.parameters.get("resource_type", ResourceType.CREDITS)
        if isinstance(resource_type, ResourceType):
            resource_name = resource_type.value
        else:
            resource_name = str(resource_type)
            
        amount = interaction.parameters.get("amount", 0)
        price_per_unit = interaction.parameters.get("price_per_unit", 0)
        
        # Get agent names
        employer_name = participant_names.get(InteractionRole.EMPLOYER, "Unknown Employer")
        
        # Generate title
        title = f"{employer_name} Offers {resource_name} for Sale"
        tags = ["goods_sale", "market_listing", "commerce", "offer"]
        
        # Generate description based on verbosity
        if self.verbosity >= 4:
            description = (
                f"The marketplace at {self._get_random_location()} saw a new addition today as {employer_name} set up "
                f"a display offering {amount} units of {resource_name} for sale. Priced at {price_per_unit} credits "
                f"per unit, the goods attracted attention from various potential buyers examining the quality and "
                f"negotiation potential. {employer_name} appeared confident in the fair pricing, explaining to interested "
                f"parties that the resource is in particularly good condition. Market observers noted that this offering "
                f"could impact local prices for {resource_name}, which have been relatively volatile in the colony's "
                f"developing economy."
            )
        elif self.verbosity >= 2:
            description = (
                f"{employer_name} has listed {amount} units of {resource_name} for sale at {price_per_unit} credits "
                f"per unit. The goods are now available for purchase at {self._get_random_location()}."
            )
        else:
            description = f"{employer_name} selling {amount} {resource_name} for {price_per_unit} credits each."
        
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
            agents_involved=list(set(agent for event in events for agent in event.agents_involved)),
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
                # Add event to summary
                summary += f"### {event.title}\n"
                summary += f"**Protagonists:** {', '.join([agent.name for agent in event.agents_involved])}\n"
                summary += f"{event.description}\n\n"
        else:
            summary += "## A Quiet Day\n\nNo significant events were recorded today.\n\n"
        
        # Add a conclusion
        summary += self._generate_daily_conclusion(day, events)
        
        logger.info(f"Generated daily summary for day {day} with {len(events)} events: {summary}")
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