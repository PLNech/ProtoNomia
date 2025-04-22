"""
Job market interaction handler for ProtoNomia.
"""
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging
import random

from models.base import (
    Agent, EconomicInteraction, InteractionRole,
    InteractionOutcome, InteractionStrategy, ResourceBalance, ResourceType, ActionType
)
from economics.interactions.base import InteractionHandler
from models.economy import JobListing

logger = logging.getLogger(__name__)

class JobMarketHandler(InteractionHandler):
    """Handler for job market interactions"""
    
    interaction_type = ActionType.JOB_APPLICATION
    
    def create_interaction(self, **kwargs) -> EconomicInteraction:
        """Create a new job application interaction
        
        Args:
            employer: The employer agent
            employee: The employee agent applying for the job
            job_listing: The job listing being applied for
            
        Returns:
            A new job application interaction
        """
        employer = kwargs.get("employer")
        employee = kwargs.get("employee")
        job_listing = kwargs.get("job_listing")
        
        if not employer or not employee or not job_listing:
            raise ValueError("Employer, employee, and job_listing are required")
        
        # Create the interaction
        interaction = EconomicInteraction(
            interaction_type=self.interaction_type,
            participants={
                employer: InteractionRole.EMPLOYER,
                employee: InteractionRole.EMPLOYEE
            },
            parameters={
                "job_id": job_listing.id,
                "job_type": job_listing.job_type,
                "salary": job_listing.salary_per_turn,
                "stage": "application",
                "application_successful": None
            },
            narrative_significance=random.uniform(0.3, 0.7)  # Mid-range significance
        )
        
        return interaction
    
    def progress_interaction(self, interaction: EconomicInteraction) -> EconomicInteraction:
        """Progress a job application interaction
        
        Args:
            interaction: The interaction to progress
            
        Returns:
            The updated interaction
        """
        # Check stage
        stage = interaction.parameters.get("stage")
        
        if stage == "application":
            # TODO: Decide acceptance based on employer personality and other factors
            # For simplicity, 70% chance of acceptance in this simplified version
            acceptance = random.random() < 0.7
            
            # Update interaction parameters
            interaction.parameters["application_successful"] = acceptance
            interaction.parameters["stage"] = "complete"
            
            # Complete the interaction
            return self.complete_interaction(interaction)
            
        return interaction
    
    def complete_interaction(self, interaction: EconomicInteraction) -> EconomicInteraction:
        """Complete a job application interaction
        
        Args:
            interaction: The interaction to complete
            
        Returns:
            The completed interaction with outcomes
        """
        # Mark as complete
        interaction.is_complete = True
        interaction.end_time = datetime.now()
        
        # Get employer and employee
        employer = None
        employee = None
        
        for agent, role in interaction.participants.items():
            if role == InteractionRole.EMPLOYER:
                employer = agent
            elif role == InteractionRole.EMPLOYEE:
                employee = agent
        
        if not employer or not employee:
            logger.error("Missing employer or employee in job application interaction")
            return interaction
        
        # Get interaction parameters
        successful = interaction.parameters.get("application_successful", False)
        salary = interaction.parameters.get("salary", 0)
        
        # Create outcomes
        employer_outcome = InteractionOutcome(
            interaction_id=interaction.id,
            agent=employer,
            role=InteractionRole.EMPLOYER,
            resources_before=[],
            resources_after=[],
            utility_change=0,
            description="Employer in job application"
        )
        
        employee_outcome = InteractionOutcome(
            interaction_id=interaction.id,
            agent=employee,
            role=InteractionRole.EMPLOYEE,
            resources_before=[],
            resources_after=[],
            utility_change=10 if successful else -5,  # Positive utility for success, negative for rejection
            description=f"{'Successful' if successful else 'Unsuccessful'} job application"
        )
        
        interaction.outcomes = [employer_outcome, employee_outcome]
        
        return interaction 