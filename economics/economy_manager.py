"""
Economy manager for ProtoNomia.
Handles the economic markets and employment relationships.
"""
import logging
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple

from models.actions import (
    ActionType, AgentAction, HireAction, FireAction, ApplyAction,
    ListGoodsAction, RetractAction, PurchaseAction
)
from models.base import (
    Agent, ResourceType, ResourceBalance, EconomicInteraction,
    EconomicInteractionType, InteractionRole, InteractionOutcome
)
from models.economy import (
    EconomyState, GoodsMarket, JobMarket, GoodsListing, JobListing,
    ListingType, EmploymentManager, Listing
)
from economics.interactions import InteractionRegistry

# Initialize logger
logger = logging.getLogger(__name__)

class EconomyManager:
    """
    Manager for the economic aspects of the simulation.
    Handles markets, employment, and economic interactions.
    """
    
    def __init__(self):
        """Initialize the economy manager."""
        self.state = EconomyState()
        self.interaction_registry = InteractionRegistry()
        logger.info("Initialized EconomyManager")
    
    def process_action(self, action: AgentAction, agents: Dict[str, Agent]) -> Tuple[bool, str]:
        """
        Process an economic action from an agent.
        
        Args:
            action: The action to process
            agents: Dictionary of all agents in the simulation
            
        Returns:
            Tuple of (success, message)
        """
        agent_id = action.agent_id
        agent = agents.get(agent_id)
        
        if not agent:
            return False, f"Agent {agent_id} not found"
        
        # Process different action types
        if action.type == ActionType.HIRE:
            return self._process_hire_action(action, agent)
            
        elif action.type == ActionType.FIRE:
            return self._process_fire_action(action, agent)
            
        elif action.type == ActionType.APPLY:
            return self._process_apply_action(action, agent)
            
        elif action.type == ActionType.LIST_GOODS:
            return self._process_list_goods_action(action, agent)
            
        elif action.type == ActionType.RETRACT:
            return self._process_retract_action(action, agent)
            
        elif action.type == ActionType.PURCHASE:
            return self._process_purchase_action(action, agent, agents)
            
        elif action.type == ActionType.WORK:
            return self._process_work_action(action, agent)
        
        # Other economic actions can be processed here
        
        return False, f"Action type {action.type} not supported by EconomyManager"
    
    def _process_hire_action(self, action: AgentAction, agent: Agent) -> Tuple[bool, str]:
        """Process a HIRE action."""
        if not action.hire_details:
            return False, "No hire details provided"
        
        details = action.hire_details
        
        # Create a job listing
        job_listing = JobListing(
            listing_type=ListingType.JOB_OFFER,
            creator_id=agent.id,
            job_type=details.job_type,
            salary_per_turn=details.salary_per_turn,
            salary_resource_type=ResourceType.CREDITS,  # Default to credits
            requirements=details.requirements,
            description=details.description,
            max_employees=details.max_employees
        )
        
        # Add the listing to the job market
        self.state.job_market.add_listing(job_listing)
        
        return True, f"Created job listing {job_listing.id}"
    
    def _process_fire_action(self, action: AgentAction, agent: Agent) -> Tuple[bool, str]:
        """Process a FIRE action."""
        if not action.fire_details:
            return False, "No fire details provided"
        
        details = action.fire_details
        job_id = details.job_id
        employee_id = details.employee_id
        
        # Check if the job listing exists and belongs to the agent
        job_listing = self.state.job_market.listings.get(job_id)
        if not job_listing:
            return False, f"Job listing {job_id} not found"
        
        if not isinstance(job_listing, JobListing):
            return False, f"Listing {job_id} is not a job listing"
        
        if job_listing.creator_id != agent.id:
            return False, f"Job listing {job_id} does not belong to agent {agent.id}"
        
        # Remove the employee from the job
        if self.state.job_market.remove_employee_from_job(job_id, employee_id):
            # Also remove from employment manager
            self.state.employment_manager.unassign_job(employee_id)
            return True, f"Fired employee {employee_id} from job {job_id}"
        
        return False, f"Employee {employee_id} not found in job {job_id}"
    
    def _process_apply_action(self, action: AgentAction, agent: Agent) -> Tuple[bool, str]:
        """Process an APPLY action."""
        if not action.apply_details:
            return False, "No apply details provided"
        
        details = action.apply_details
        listing_id = details.listing_id
        
        # Check if the listing exists
        listing = self.state.job_market.listings.get(listing_id)
        if not listing:
            return False, f"Listing {listing_id} not found"
        
        if not isinstance(listing, JobListing):
            return False, f"Listing {listing_id} is not a job listing"
        
        if not listing.active:
            return False, f"Listing {listing_id} is no longer active"
        
        # Check if the job has space for more employees
        if len(listing.current_employees) >= listing.max_employees:
            return False, f"Job {listing_id} is already at maximum capacity"
        
        # Check if the agent is already employed for this job
        if agent.id in listing.current_employees:
            return False, f"Agent {agent.id} is already employed for job {listing_id}"
        
        # Add the agent as an employee
        if self.state.job_market.add_employee_to_job(listing_id, agent.id):
            # Also update the employment manager
            self.state.employment_manager.assign_job(agent.id, listing_id)
            return True, f"Agent {agent.id} applied successfully for job {listing_id}"
        
        return False, f"Failed to add agent {agent.id} as employee for job {listing_id}"
    
    def _process_list_goods_action(self, action: AgentAction, agent: Agent) -> Tuple[bool, str]:
        """Process a LIST_GOODS action."""
        if not action.list_goods_details:
            return False, "No list goods details provided"
        
        details = action.list_goods_details
        
        try:
            # Determine listing type
            listing_type = ListingType.GOODS_OFFER if details.is_offer else ListingType.GOODS_REQUEST
            
            # Parse resource type
            try:
                resource_type = ResourceType(details.resource_type)
            except ValueError:
                return False, f"Invalid resource type: {details.resource_type}"
            
            # Create a goods listing
            goods_listing = GoodsListing(
                listing_type=listing_type,
                creator_id=agent.id,
                resource_type=resource_type,
                amount=details.amount,
                price_per_unit=details.price_per_unit,
                price_resource_type=ResourceType.CREDITS,  # Default to credits
                description=details.description
            )
            
            # Add the listing to the goods market
            self.state.goods_market.add_listing(goods_listing)
            
            return True, f"Created goods listing {goods_listing.id}"
            
        except Exception as e:
            return False, f"Failed to create goods listing: {str(e)}"
    
    def _process_retract_action(self, action: AgentAction, agent: Agent) -> Tuple[bool, str]:
        """Process a RETRACT action."""
        if not action.retract_details:
            return False, "No retract details provided"
        
        details = action.retract_details
        listing_id = details.listing_id
        
        # Check both markets for the listing
        goods_listing = self.state.goods_market.listings.get(listing_id)
        job_listing = self.state.job_market.listings.get(listing_id)
        
        listing = goods_listing or job_listing
        if not listing:
            return False, f"Listing {listing_id} not found"
        
        # Check if the listing belongs to the agent
        if listing.creator_id != agent.id:
            return False, f"Listing {listing_id} does not belong to agent {agent.id}"
        
        # Deactivate the listing (instead of removing it)
        if goods_listing:
            self.state.goods_market.deactivate_listing(listing_id)
        else:
            self.state.job_market.deactivate_listing(listing_id)
        
        return True, f"Retracted listing {listing_id}"
    
    def _process_purchase_action(self, action: AgentAction, agent: Agent, agents: Dict[str, Agent]) -> Tuple[bool, str]:
        """Process a PURCHASE action."""
        if not action.purchase_details:
            return False, "No purchase details provided"
        
        details = action.purchase_details
        listing_id = details.listing_id
        purchase_amount = details.amount
        
        # Check if the listing exists
        listing = self.state.goods_market.listings.get(listing_id)
        if not listing:
            return False, f"Listing {listing_id} not found"
        
        if not isinstance(listing, GoodsListing):
            return False, f"Listing {listing_id} is not a goods listing"
        
        if not listing.active:
            return False, f"Listing {listing_id} is no longer active"
        
        if listing.listing_type != ListingType.GOODS_OFFER:
            return False, f"Listing {listing_id} is not an offer, cannot purchase from it"
        
        if purchase_amount <= 0:
            return False, "Purchase amount must be positive"
        
        if purchase_amount > listing.amount:
            return False, f"Not enough goods available: requested {purchase_amount}, available {listing.amount}"
        
        # Get the seller agent
        seller = agents.get(listing.creator_id)
        if not seller:
            return False, f"Seller agent {listing.creator_id} not found"
        
        # Calculate total price
        total_price = purchase_amount * listing.price_per_unit
        
        # Check if buyer has enough resources to pay
        buyer_credits = 0
        for resource in agent.resources:
            if resource.resource_type == listing.price_resource_type:
                buyer_credits = resource.amount
                break
        
        if buyer_credits < total_price:
            return False, f"Insufficient funds: required {total_price}, available {buyer_credits}"
        
        # Transfer resources
        self._transfer_resources(
            from_agent=agent,
            to_agent=seller,
            resource_type=listing.price_resource_type,
            amount=total_price
        )
        
        self._transfer_resources(
            from_agent=seller,
            to_agent=agent,
            resource_type=listing.resource_type,
            amount=purchase_amount
        )
        
        # Update the listing amount
        listing.amount -= purchase_amount
        
        # If the listing is now empty, deactivate it
        if listing.amount <= 0:
            self.state.goods_market.deactivate_listing(listing_id)
        
        return True, f"Purchased {purchase_amount} of {listing.resource_type} for {total_price}"
    
    def _process_work_action(self, action: AgentAction, agent: Agent) -> Tuple[bool, str]:
        """Process a WORK action."""
        if not action.work_details:
            return False, "No work details provided"
        
        job_id = action.work_details.job_id
        
        # Check if the agent is assigned to this job
        assigned_job_id = self.state.employment_manager.get_employee_job(agent.id)
        if not assigned_job_id:
            return False, f"Agent {agent.id} is not employed"
        
        if assigned_job_id != job_id:
            return False, f"Agent {agent.id} is not assigned to job {job_id}"
        
        # Don't actually do anything here, just verify the agent is assigned
        # Salary payment will be handled by the pay_salaries method
        return True, f"Agent {agent.id} worked at job {job_id}"
    
    def pay_salaries(self, agents: Dict[str, Agent]) -> List[str]:
        """
        Pay salaries to all employed agents.
        
        Args:
            agents: Dictionary of all agents in the simulation
            
        Returns:
            List of messages describing salary payments
        """
        messages = []
        
        # Get all job listings
        for job_id, listing in self.state.job_market.listings.items():
            if not isinstance(listing, JobListing) or not listing.active:
                continue
            
            # Get the employer
            employer = agents.get(listing.creator_id)
            if not employer:
                messages.append(f"Warning: Employer {listing.creator_id} not found for job {job_id}")
                continue
            
            # Calculate total salary cost
            total_salary = listing.salary_per_turn * len(listing.current_employees)
            
            # Check if employer has enough resources to pay
            employer_resources = 0
            for resource in employer.resources:
                if resource.resource_type == listing.salary_resource_type:
                    employer_resources = resource.amount
                    break
            
            if employer_resources < total_salary:
                messages.append(f"Warning: Employer {employer.name} ({employer.id}) cannot afford to pay salaries")
                # TODO: Handle bankruptcy, fire employees, etc.
                continue
            
            # Pay each employee
            for employee_id in listing.current_employees:
                employee = agents.get(employee_id)
                if not employee:
                    messages.append(f"Warning: Employee {employee_id} not found")
                    continue
                
                # Transfer salary
                self._transfer_resources(
                    from_agent=employer,
                    to_agent=employee,
                    resource_type=listing.salary_resource_type,
                    amount=listing.salary_per_turn
                )
                
                messages.append(
                    f"Employer {employer.name} paid {listing.salary_per_turn} {listing.salary_resource_type} "
                    f"to employee {employee.name}"
                )
        
        return messages
    
    def _transfer_resources(self, from_agent: Agent, to_agent: Agent, resource_type: ResourceType, amount: float) -> None:
        """
        Transfer resources from one agent to another.
        
        Args:
            from_agent: Agent giving resources
            to_agent: Agent receiving resources
            resource_type: Type of resource to transfer
            amount: Amount to transfer
        """
        # Deduct from sender
        from_resource = None
        for resource in from_agent.resources:
            if resource.resource_type == resource_type:
                from_resource = resource
                break
        
        if from_resource:
            from_resource.amount -= amount
        else:
            from_agent.resources.append(ResourceBalance(
                resource_type=resource_type,
                amount=-amount
            ))
        
        # Add to receiver
        to_resource = None
        for resource in to_agent.resources:
            if resource.resource_type == resource_type:
                to_resource = resource
                break
        
        if to_resource:
            to_resource.amount += amount
        else:
            to_agent.resources.append(ResourceBalance(
                resource_type=resource_type,
                amount=amount
            ))
    
    def get_goods_listings_for_agent(self, agent_id: str) -> List[Dict[str, Any]]:
        """
        Get formatted goods listings for an agent's decision context.
        
        Args:
            agent_id: ID of the agent
            
        Returns:
            List of formatted goods listings
        """
        listings = []
        for listing_id, listing in self.state.goods_market.listings.items():
            if not listing.active or not isinstance(listing, GoodsListing):
                continue
            
            listings.append({
                "id": listing.id,
                "type": "offer" if listing.listing_type == ListingType.GOODS_OFFER else "request",
                "resource_type": listing.resource_type.value,
                "amount": listing.amount,
                "price_per_unit": listing.price_per_unit,
                "price_resource_type": listing.price_resource_type.value,
                "creator_id": listing.creator_id,
                "is_own": listing.creator_id == agent_id
            })
        
        return listings
    
    def get_job_listings_for_agent(self, agent_id: str) -> List[Dict[str, Any]]:
        """
        Get formatted job listings for an agent's decision context.
        
        Args:
            agent_id: ID of the agent
            
        Returns:
            List of formatted job listings
        """
        listings = []
        for listing_id, listing in self.state.job_market.listings.items():
            if not listing.active or not isinstance(listing, JobListing):
                continue
            
            listings.append({
                "id": listing.id,
                "job_type": listing.job_type,
                "salary_per_turn": listing.salary_per_turn,
                "salary_resource_type": listing.salary_resource_type.value,
                "requirements": listing.requirements,
                "creator_id": listing.creator_id,
                "is_own": listing.creator_id == agent_id,
                "employees": listing.current_employees,
                "max_employees": listing.max_employees,
                "has_openings": len(listing.current_employees) < listing.max_employees
            })
        
        return listings
    
    def create_random_economic_interaction(self, active_agents: List[str], agents: Dict[str, Agent]) -> Optional[EconomicInteraction]:
        """
        Create a random economic interaction between two agents.
        
        Args:
            active_agents: List of active agent IDs
            agents: Dictionary of all agents
            
        Returns:
            An economic interaction or None if not possible
        """
        if len(active_agents) < 2:
            return None
        
        # Select two random agents
        agent_ids = random.sample(active_agents, 2)
        
        # Select a random interaction type
        interaction_types = list(self.interaction_registry.handlers.keys())
        if not interaction_types:
            return None
        
        interaction_type = random.choice(interaction_types)
        
        # Get the handler
        handler = self.interaction_registry.handlers.get(interaction_type)
        if not handler:
            return None
        
        # Create parameters for the interaction
        parameters = {}
        
        if interaction_type == EconomicInteractionType.ULTIMATUM:
            parameters = {
                "resource_type": ResourceType.CREDITS,
                "total_amount": random.uniform(10, 100),
                "proposed_amount": random.uniform(1, 50),
                "stage": "proposal"
            }
        
        elif interaction_type == EconomicInteractionType.TRUST:
            parameters = {
                "resource_type": ResourceType.CREDITS,
                "initial_amount": random.uniform(10, 100),
                "invested_amount": random.uniform(5, 50),
                "multiplier": random.uniform(1.5, 3.0),
                "stage": "investment"
            }
        
        elif interaction_type == EconomicInteractionType.PUBLIC_GOODS:
            parameters = {
                "resource_type": ResourceType.CREDITS,
                "pool_multiplier": random.uniform(1.5, 2.5),
                "contribution_cap": random.uniform(10, 50),
                "stage": "contribution"
            }
        
        # Create roles based on interaction type
        initiator_role = InteractionRole.INITIATOR
        responder_role = InteractionRole.RESPONDER
        
        # Create the interaction
        interaction = EconomicInteraction(
            interaction_type=interaction_type,
            participants={
                agent_ids[0]: initiator_role,
                agent_ids[1]: responder_role
            },
            parameters=parameters,
            is_complete=False,
            narrative_significance=random.uniform(0.1, 1.0)
        )
        
        return interaction
    
    def process_interaction(self, interaction: EconomicInteraction, agents: Dict[str, Agent]) -> EconomicInteraction:
        """
        Process an economic interaction.
        
        Args:
            interaction: The interaction to process
            agents: Dictionary of all agents
            
        Returns:
            The updated interaction
        """
        # Get the handler for this interaction type
        handler = self.interaction_registry.handlers.get(interaction.interaction_type)
        if not handler:
            # Mark as complete if no handler
            interaction.is_complete = True
            interaction.end_time = datetime.now()
            return interaction
        
        # Process the interaction
        try:
            processed_interaction = handler.process(interaction, agents)
            
            # If the interaction is now complete, set the end time
            if processed_interaction.is_complete and not processed_interaction.end_time:
                processed_interaction.end_time = datetime.now()
            
            return processed_interaction
        
        except Exception as e:
            logger.error(f"Error processing interaction {interaction.id}: {e}")
            # Mark as complete to avoid further processing
            interaction.is_complete = True
            interaction.end_time = datetime.now()
            return interaction
    
    def update_listings(self, current_turn: int) -> None:
        """
        Update listings, removing expired ones.
        
        Args:
            current_turn: Current simulation turn
        """
        # Update goods market listings
        for listing_id, listing in list(self.state.goods_market.listings.items()):
            if listing.expiry_turn and listing.expiry_turn <= current_turn:
                self.state.goods_market.deactivate_listing(listing_id)
        
        # Update job market listings
        for listing_id, listing in list(self.state.job_market.listings.items()):
            if listing.expiry_turn and listing.expiry_turn <= current_turn:
                self.state.job_market.deactivate_listing(listing_id)
    
    def generate_market_report(self) -> Dict[str, Any]:
        """
        Generate a report on the current state of the markets.
        
        Returns:
            Dictionary with market statistics
        """
        # Get active listings counts
        active_goods_offers = len([l for l in self.state.goods_market.listings.values() 
                                if l.active and l.listing_type == ListingType.GOODS_OFFER])
        
        active_goods_requests = len([l for l in self.state.goods_market.listings.values() 
                                   if l.active and l.listing_type == ListingType.GOODS_REQUEST])
        
        active_job_offers = len([l for l in self.state.job_market.listings.values() 
                               if l.active and l.listing_type == ListingType.JOB_OFFER])
        
        # Calculate average prices by resource type
        resource_prices = {}
        for listing in self.state.goods_market.listings.values():
            if not listing.active or not isinstance(listing, GoodsListing):
                continue
            
            resource_type = listing.resource_type.value
            if resource_type not in resource_prices:
                resource_prices[resource_type] = {"sum": 0, "count": 0}
            
            resource_prices[resource_type]["sum"] += listing.price_per_unit
            resource_prices[resource_type]["count"] += 1
        
        avg_prices = {
            resource_type: data["sum"] / data["count"] if data["count"] > 0 else 0
            for resource_type, data in resource_prices.items()
        }
        
        # Calculate average salary by job type
        job_salaries = {}
        for listing in self.state.job_market.listings.values():
            if not listing.active or not isinstance(listing, JobListing):
                continue
            
            job_type = listing.job_type
            if job_type not in job_salaries:
                job_salaries[job_type] = {"sum": 0, "count": 0}
            
            job_salaries[job_type]["sum"] += listing.salary_per_turn
            job_salaries[job_type]["count"] += 1
        
        avg_salaries = {
            job_type: data["sum"] / data["count"] if data["count"] > 0 else 0
            for job_type, data in job_salaries.items()
        }
        
        # Calculate employment statistics
        total_jobs = len(self.state.job_market.listings)
        total_employees = sum(len(listing.current_employees) 
                             for listing in self.state.job_market.listings.values() 
                             if isinstance(listing, JobListing))
        
        return {
            "active_goods_offers": active_goods_offers,
            "active_goods_requests": active_goods_requests,
            "active_job_offers": active_job_offers,
            "avg_resource_prices": avg_prices,
            "avg_job_salaries": avg_salaries,
            "total_jobs": total_jobs,
            "total_employees": total_employees,
            "employment_ratio": total_employees / total_jobs if total_jobs > 0 else 0
        } 