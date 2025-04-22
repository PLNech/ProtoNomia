"""
Tests for the simplified economic interactions in ProtoNomia.
"""
import pytest
from datetime import datetime
import random

from models.base import (
    Agent, AgentType, AgentFaction, AgentPersonality, ResourceBalance, ResourceType,
    EconomicInteraction, ActionType, InteractionRole, InteractionOutcome
)
from economics.interactions.job_market import JobMarketHandler
from economics.interactions.goods_market import GoodsMarketHandler
from economics.interactions.registry import InteractionRegistry
from models.economy import JobListing, GoodsListing, ListingType

@pytest.fixture
def agent_employer():
    """Create an employer agent for testing"""
    return Agent(
        id="employer_1",
        name="Test Employer",
        agent_type=AgentType.INDIVIDUAL,
        faction=AgentFaction.MARS_NATIVE,
        personality=AgentPersonality(
            cooperativeness=0.6,
            risk_tolerance=0.6,
            fairness_preference=0.5,
            altruism=0.4,
            rationality=0.8,
            long_term_orientation=0.7
        ),
        resources=[
            ResourceBalance(
                resource_type=ResourceType.CREDITS,
                amount=1000.0
            )
        ],
        is_alive=True
    )

@pytest.fixture
def agent_employee():
    """Create an employee agent for testing"""
    return Agent(
        id="employee_1",
        name="Test Employee",
        agent_type=AgentType.INDIVIDUAL,
        faction=AgentFaction.MARS_NATIVE,
        personality=AgentPersonality(
            cooperativeness=0.7,
            risk_tolerance=0.5,
            fairness_preference=0.6,
            altruism=0.5,
            rationality=0.7,
            long_term_orientation=0.6
        ),
        resources=[
            ResourceBalance(
                resource_type=ResourceType.CREDITS,
                amount=500.0
            )
        ],
        is_alive=True
    )

@pytest.fixture
def job_listing():
    """Create a job listing for testing"""
    return JobListing(
        listing_type=ListingType.JOB_OFFER,
        creator_id="employer_1",
        job_type="Engineer",
        salary_per_turn=50.0,
        requirements="Technical skills required",
        max_employees=3
    )

@pytest.fixture
def goods_listing():
    """Create a goods listing for testing"""
    return GoodsListing(
        listing_type=ListingType.GOODS_OFFER,
        creator_id="employer_1",
        resource_type=ResourceType.FOOD,
        amount=20.0,
        price_per_unit=10.0
    )

@pytest.fixture
def interaction_registry():
    """Create an interaction registry for testing"""
    return InteractionRegistry()

class TestJobMarketInteraction:
    """Tests for job market interactions"""
    
    def test_job_application_creation(self, agent_employer, agent_employee, job_listing):
        """Test creating a job application interaction"""
        # Create the handler
        handler = JobMarketHandler()
        
        # Create the interaction
        interaction = handler.create_interaction(
            employer=agent_employer,
            employee=agent_employee,
            job_listing=job_listing
        )
        
        # Check interaction properties
        assert interaction.interaction_type == ActionType.APPLY
        assert len(interaction.participants) == 2
        assert agent_employer in interaction.participants
        assert agent_employee in interaction.participants
        assert interaction.participants[agent_employer] == InteractionRole.EMPLOYER
        assert interaction.participants[agent_employee] == InteractionRole.EMPLOYEE
        assert interaction.is_complete == False
        assert interaction.parameters["job_type"] == "Engineer"
        assert interaction.parameters["salary"] == 50.0
        assert interaction.parameters["stage"] == "application"
        
    def test_job_application_progresses(self, agent_employer, agent_employee, job_listing):
        """Test that a job application interaction progresses properly"""
        # Create the handler
        handler = JobMarketHandler()
        
        # Set a seed to make the test deterministic
        random.seed(42)
        
        # Create the interaction
        interaction = handler.create_interaction(
            employer=agent_employer,
            employee=agent_employee,
            job_listing=job_listing
        )
        
        # Progress the interaction
        updated_interaction = handler.progress_interaction(interaction)
        
        # Check that the interaction is complete
        assert updated_interaction.is_complete == True
        assert updated_interaction.end_time is not None
        assert updated_interaction.parameters["stage"] == "complete"
        assert "application_successful" in updated_interaction.parameters
        
        # Check that outcomes were created
        assert len(updated_interaction.outcomes) == 2
        
        # Find employer and employee outcomes
        employer_outcome = next(o for o in updated_interaction.outcomes if o.agent == agent_employer)
        employee_outcome = next(o for o in updated_interaction.outcomes if o.agent == agent_employee)
        
        # Check outcomes based on result
        success = updated_interaction.parameters["application_successful"]
        if success:
            assert employee_outcome.utility_change > 0
        else:
            assert employee_outcome.utility_change < 0

class TestGoodsMarketInteraction:
    """Tests for goods market interactions"""
    
    def test_goods_purchase_creation(self, agent_employer, agent_employee, goods_listing):
        """Test creating a goods purchase interaction"""
        # Create the handler
        handler = GoodsMarketHandler()
        
        # Create the interaction
        interaction = handler.create_interaction(
            seller=agent_employer,
            buyer=agent_employee,
            goods_listing=goods_listing,
            purchase_amount=5.0
        )
        
        # Check interaction properties
        assert interaction.interaction_type == ActionType.BUY
        assert len(interaction.participants) == 2
        assert agent_employer in interaction.participants
        assert agent_employee in interaction.participants
        assert interaction.participants[agent_employer] == InteractionRole.SELLER
        assert interaction.participants[agent_employee] == InteractionRole.BUYER
        assert interaction.is_complete == False
        assert interaction.parameters["purchase_amount"] == 5.0
        assert interaction.parameters["price_per_unit"] == 10.0
        assert interaction.parameters["total_price"] == 50.0
        assert interaction.parameters["stage"] == "purchase"
        
    def test_goods_purchase_succeeds(self, agent_employer, agent_employee, goods_listing):
        """Test that a goods purchase interaction succeeds properly"""
        # Create the handler
        handler = GoodsMarketHandler()
        
        # Ensure the buyer has enough credits
        buyer_credits = next(r for r in agent_employee.resources if r.resource_type == ResourceType.CREDITS)
        buyer_credits.amount = 200.0
        
        # Record initial balances
        seller_initial_credits = next(r.amount for r in agent_employer.resources if r.resource_type == ResourceType.CREDITS)
        buyer_initial_credits = buyer_credits.amount
        
        # Create the interaction
        interaction = handler.create_interaction(
            seller=agent_employer,
            buyer=agent_employee,
            goods_listing=goods_listing,
            purchase_amount=5.0
        )
        
        # Progress the interaction
        updated_interaction = handler.progress_interaction(interaction)
        
        # Check that the interaction is complete
        assert updated_interaction.is_complete == True
        assert updated_interaction.parameters["stage"] == "complete"
        assert updated_interaction.parameters["purchase_successful"] == True
        
        # Check that resources were transferred
        seller_final_credits = next(r.amount for r in agent_employer.resources if r.resource_type == ResourceType.CREDITS)
        buyer_final_credits = next(r.amount for r in agent_employee.resources if r.resource_type == ResourceType.CREDITS)
        
        total_price = updated_interaction.parameters["total_price"]
        assert seller_final_credits == seller_initial_credits + total_price
        assert buyer_final_credits == buyer_initial_credits - total_price
        
        # Check that buyer received the goods
        buyer_food = next((r.amount for r in agent_employee.resources if r.resource_type == ResourceType.FOOD), 0)
        assert buyer_food == 5.0
        
    def test_goods_purchase_fails_insufficient_funds(self, agent_employer, agent_employee, goods_listing):
        """Test that a goods purchase interaction fails with insufficient funds"""
        # Create the handler
        handler = GoodsMarketHandler()
        
        # Ensure the buyer doesn't have enough credits
        buyer_credits = next(r for r in agent_employee.resources if r.resource_type == ResourceType.CREDITS)
        buyer_credits.amount = 10.0  # Not enough for a 5 unit purchase at 10 credits per unit
        
        # Record initial balances
        seller_initial_credits = next(r.amount for r in agent_employer.resources if r.resource_type == ResourceType.CREDITS)
        buyer_initial_credits = buyer_credits.amount
        
        # Create the interaction
        interaction = handler.create_interaction(
            seller=agent_employer,
            buyer=agent_employee,
            goods_listing=goods_listing,
            purchase_amount=5.0
        )
        
        # Progress the interaction
        updated_interaction = handler.progress_interaction(interaction)
        
        # Check that the interaction is complete
        assert updated_interaction.is_complete == True
        assert updated_interaction.parameters["stage"] == "complete"
        assert updated_interaction.parameters["purchase_successful"] == False
        assert updated_interaction.parameters["failure_reason"] == "Insufficient funds"
        
        # Check that resources were not transferred
        seller_final_credits = next(r.amount for r in agent_employer.resources if r.resource_type == ResourceType.CREDITS)
        buyer_final_credits = next(r.amount for r in agent_employee.resources if r.resource_type == ResourceType.CREDITS)
        
        assert seller_final_credits == seller_initial_credits
        assert buyer_final_credits == buyer_initial_credits
        
        # Check that buyer did not receive the goods
        buyer_food = next((r.amount for r in agent_employee.resources if r.resource_type == ResourceType.FOOD), 0)
        assert buyer_food == 0.0

def test_interaction_registry(interaction_registry, agent_employer, agent_employee, job_listing, goods_listing):
    """Test the interaction registry with the simplified interactions"""
    # Check that the registry has the appropriate handlers
    assert ActionType.APPLY in interaction_registry.handlers
    assert ActionType.BUY in interaction_registry.handlers
    
    # Test creating a job application interaction
    job_interaction = interaction_registry.create_interaction(
        interaction_type=ActionType.APPLY,
        employer=agent_employer,
        employee=agent_employee,
        job_listing=job_listing
    )
    
    assert job_interaction.interaction_type == ActionType.APPLY
    
    # Test creating a goods purchase interaction
    goods_interaction = interaction_registry.create_interaction(
        interaction_type=ActionType.BUY,
        seller=agent_employer,
        buyer=agent_employee,
        goods_listing=goods_listing,
        purchase_amount=3.0
    )
    
    assert goods_interaction.interaction_type == ActionType.BUY
    
    # Test processing an interaction
    processed_interaction = interaction_registry.process_interaction(job_interaction)
    assert processed_interaction.is_complete
    assert len(processed_interaction.outcomes) > 0 