"""
Tests for the economy module, including markets and economic actions.
"""
import pytest
from datetime import datetime

from models.base import (
    Agent, AgentType, AgentFaction, AgentPersonality, ResourceBalance, ResourceType, ActionType, HireAction, FireAction,
    ApplyAction, ListGoodsAction, RetractAction, PurchaseAction, AgentAction
)
from models.economy import (
    Listing, GoodsListing, JobListing, ListingType, GoodsMarket, JobMarket, EconomyState
)
from economics.economy_manager import EconomyManager


@pytest.fixture
def test_agent():
    """Create a test agent for the economy tests"""
    return Agent(
        id="agent_1",
        name="Test Agent",
        agent_type=AgentType.INDIVIDUAL,
        faction=AgentFaction.MARS_NATIVE,
        personality=AgentPersonality(
            cooperativeness=0.7,
            risk_tolerance=0.6,
            fairness_preference=0.5,
            altruism=0.3,
            rationality=0.8,
            long_term_orientation=0.7
        ),
        resources=[
            ResourceBalance(
                resource_type=ResourceType.CREDITS,
                amount=1000.0
            ),
            ResourceBalance(
                resource_type=ResourceType.FOOD,
                amount=50.0
            ),
            ResourceBalance(
                resource_type=ResourceType.WATER,
                amount=30.0
            )
        ]
    )


@pytest.fixture
def test_employer():
    """Create a test employer agent"""
    return Agent(
        id="agent_2",
        name="Employer Corp",
        agent_type=AgentType.CORPORATION,
        faction=AgentFaction.TERRA_CORP,
        personality=AgentPersonality(
            cooperativeness=0.5,
            risk_tolerance=0.7,
            fairness_preference=0.4,
            altruism=0.2,
            rationality=0.9,
            long_term_orientation=0.8
        ),
        resources=[
            ResourceBalance(
                resource_type=ResourceType.CREDITS,
                amount=10000.0
            ),
            ResourceBalance(
                resource_type=ResourceType.PHYSICAL_GOODS,
                amount=500.0
            )
        ]
    )


@pytest.fixture
def economy_manager():
    """Create a new economy manager for testing"""
    return EconomyManager()


class TestMarketModels:
    """Tests for the market models (GoodsListing, JobListing, etc.)"""
    
    def test_goods_listing_creation(self):
        """Test creating a goods listing"""
        # Create an offer listing
        offer_listing = GoodsListing(
            listing_type=ListingType.GOODS_OFFER,
            creator_id="agent_1",
            resource_type=ResourceType.FOOD,
            amount=10.0,
            price_per_unit=5.0
        )
        
        assert offer_listing.listing_type == ListingType.GOODS_OFFER
        assert offer_listing.resource_type == ResourceType.FOOD
        assert offer_listing.amount == 10.0
        assert offer_listing.price_per_unit == 5.0
        assert offer_listing.active == True
        
        # Create a request listing
        request_listing = GoodsListing(
            listing_type=ListingType.GOODS_REQUEST,
            creator_id="agent_1",
            resource_type=ResourceType.WATER,
            amount=-5.0,  # Negative for requests
            price_per_unit=3.0
        )
        
        assert request_listing.listing_type == ListingType.GOODS_REQUEST
        assert request_listing.resource_type == ResourceType.WATER
        assert request_listing.amount == -5.0
        assert request_listing.price_per_unit == 3.0
    
    def test_job_listing_creation(self):
        """Test creating a job listing"""
        job_listing = JobListing(
            listing_type=ListingType.JOB_OFFER,
            creator_id="agent_2",
            job_type="Engineer",
            salary_per_turn=100.0,
            requirements="Python programming experience",
            max_employees=2
        )
        
        assert job_listing.listing_type == ListingType.JOB_OFFER
        assert job_listing.job_type == "Engineer"
        assert job_listing.salary_per_turn == 100.0
        assert job_listing.requirements == "Python programming experience"
        assert job_listing.max_employees == 2
        assert len(job_listing.current_employees) == 0
    
    def test_market_management(self):
        """Test managing listings in a market"""
        market = GoodsMarket()
        
        # Create a listing
        listing = GoodsListing(
            listing_type=ListingType.GOODS_OFFER,
            creator_id="agent_1",
            resource_type=ResourceType.FOOD,
            amount=10.0,
            price_per_unit=5.0
        )
        
        # Add listing to market
        market.add_listing(listing)
        assert listing.id in market.listings
        
        # Get active listings
        active_listings = market.get_active_listings()
        assert len(active_listings) == 1
        assert active_listings[0].id == listing.id
        
        # Deactivate listing
        market.deactivate_listing(listing.id)
        assert market.listings[listing.id].active == False
        
        # Get active listings again
        active_listings = market.get_active_listings()
        assert len(active_listings) == 0
        
        # Remove listing
        market.remove_listing(listing.id)
        assert listing.id not in market.listings


class TestEconomyManager:
    """Tests for the EconomyManager class"""
    
    def test_list_goods_action(self, economy_manager, test_agent):
        """Test listing goods through the economy manager"""
        # Create a LIST_GOODS action
        action = AgentAction(
            type=ActionType.LIST_GOODS,
            agent_id=test_agent.id,
            turn=1,
            timestamp=datetime.now().timestamp(),
            list_goods_details=ListGoodsAction(
                is_offer=True,
                resource_type=ResourceType.FOOD.value,
                amount=5.0,
                price_per_unit=10.0,
                description="Fresh Mars-grown food"
            )
        )
        
        # Process the action
        success, message = economy_manager.process_action(action, {test_agent.id: test_agent})
        
        # Check results
        assert success == True
        
        # Check that a listing was created
        goods_market = economy_manager.state.goods_market
        assert len(goods_market.get_active_listings()) == 1
        
        listing = goods_market.get_active_listings()[0]
        assert isinstance(listing, GoodsListing)
        assert listing.listing_type == ListingType.GOODS_OFFER
        assert listing.resource_type == ResourceType.FOOD
        assert listing.amount == 5.0
        assert listing.price_per_unit == 10.0
    
    def test_hire_action(self, economy_manager, test_employer):
        """Test creating a job listing through the economy manager"""
        # Create a HIRE action
        action = AgentAction(
            type=ActionType.HIRE,
            agent_id=test_employer.id,
            turn=1,
            timestamp=datetime.now().timestamp(),
            hire_details=HireAction(
                job_type="Engineer",
                salary_per_turn=150.0,
                requirements="Programming skills required",
                max_employees=2,
                description="Software engineering position"
            )
        )
        
        # Process the action
        success, message = economy_manager.process_action(action, {test_employer.id: test_employer})
        
        # Check results
        assert success == True
        
        # Check that a job listing was created
        job_market = economy_manager.state.job_market
        assert len(job_market.get_active_listings()) == 1
        
        listing = job_market.get_active_listings()[0]
        assert isinstance(listing, JobListing)
        assert listing.listing_type == ListingType.JOB_OFFER
        assert listing.job_type == "Engineer"
        assert listing.salary_per_turn == 150.0
        assert listing.max_employees == 2
        assert len(listing.current_employees) == 0
    
    def test_apply_action(self, economy_manager, test_agent, test_employer):
        """Test applying for a job through the economy manager"""
        # First create a job listing
        hire_action = AgentAction(
            type=ActionType.HIRE,
            agent_id=test_employer.id,
            turn=1,
            timestamp=datetime.now().timestamp(),
            hire_details=HireAction(
                job_type="Engineer",
                salary_per_turn=150.0,
                requirements="Programming skills required",
                max_employees=2
            )
        )
        
        success, message = economy_manager.process_action(hire_action, 
                                                        {test_employer.id: test_employer, 
                                                         test_agent.id: test_agent})
        assert success == True
        
        # Get the job listing ID
        job_listing = economy_manager.state.job_market.get_active_listings()[0]
        
        # Now apply for the job
        apply_action = AgentAction(
            type=ActionType.APPLY,
            agent_id=test_agent.id,
            turn=2,
            timestamp=datetime.now().timestamp(),
            apply_details=ApplyAction(
                listing_id=job_listing.id
            )
        )
        
        success, message = economy_manager.process_action(apply_action, 
                                                        {test_employer.id: test_employer, 
                                                         test_agent.id: test_agent})
        
        # Check results
        assert success == True
        
        # Check that the agent was added to the job listing
        updated_listing = economy_manager.state.job_market.listings[job_listing.id]
        assert test_agent.id in updated_listing.current_employees
        
        # Check that the employment manager has the correct assignment
        assert economy_manager.state.employment_manager.get_employee_job(test_agent.id) == job_listing.id
    
    def test_purchase_action(self, economy_manager, test_agent, test_employer):
        """Test purchasing goods through the economy manager"""
        # First create a goods listing
        list_action = AgentAction(
            type=ActionType.LIST_GOODS,
            agent_id=test_employer.id,
            turn=1,
            timestamp=datetime.now().timestamp(),
            list_goods_details=ListGoodsAction(
                is_offer=True,
                resource_type=ResourceType.PHYSICAL_GOODS.value,
                amount=20.0,
                price_per_unit=15.0,
                description="Physical goods for sale"
            )
        )
        
        success, message = economy_manager.process_action(list_action, 
                                                        {test_employer.id: test_employer, 
                                                         test_agent.id: test_agent})
        assert success == True
        
        # Get the goods listing ID
        goods_listing = economy_manager.state.goods_market.get_active_listings()[0]
        
        # Record initial resources
        employer_initial_goods = next((r.amount for r in test_employer.resources 
                                     if r.resource_type == ResourceType.PHYSICAL_GOODS), 0)
        employer_initial_credits = next((r.amount for r in test_employer.resources 
                                       if r.resource_type == ResourceType.CREDITS), 0)
        agent_initial_goods = next((r.amount for r in test_agent.resources 
                                  if r.resource_type == ResourceType.PHYSICAL_GOODS), 0)
        agent_initial_credits = next((r.amount for r in test_agent.resources 
                                    if r.resource_type == ResourceType.CREDITS), 0)
        
        # Now purchase some goods
        purchase_action = AgentAction(
            type=ActionType.PURCHASE,
            agent_id=test_agent.id,
            turn=2,
            timestamp=datetime.now().timestamp(),
            purchase_details=PurchaseAction(
                listing_id=goods_listing.id,
                amount=5.0
            )
        )
        
        success, message = economy_manager.process_action(purchase_action, 
                                                        {test_employer.id: test_employer, 
                                                         test_agent.id: test_agent})
        
        # Check results
        assert success == True
        
        # Check that the goods were transferred and payment was made
        purchase_cost = 5.0 * 15.0  # amount * price_per_unit
        
        # Employer should have less goods and more credits
        employer_final_goods = next((r.amount for r in test_employer.resources 
                                   if r.resource_type == ResourceType.PHYSICAL_GOODS), 0)
        employer_final_credits = next((r.amount for r in test_employer.resources 
                                     if r.resource_type == ResourceType.CREDITS), 0)
        
        assert employer_final_goods == employer_initial_goods - 5.0
        assert employer_final_credits == employer_initial_credits + purchase_cost
        
        # Agent should have more goods and less credits
        agent_final_goods = next((r.amount for r in test_agent.resources 
                                if r.resource_type == ResourceType.PHYSICAL_GOODS), 0)
        agent_final_credits = next((r.amount for r in test_agent.resources 
                                  if r.resource_type == ResourceType.CREDITS), 0)
        
        assert agent_final_goods == agent_initial_goods + 5.0
        assert agent_final_credits == agent_initial_credits - purchase_cost
        
        # Check that the listing amount was updated
        updated_listing = economy_manager.state.goods_market.listings[goods_listing.id]
        assert updated_listing.amount == 15.0  # 20.0 - 5.0
    
    def test_salary_payment(self, economy_manager, test_agent, test_employer):
        """Test salary payment process"""
        # First create a job and hire the test agent
        hire_action = AgentAction(
            type=ActionType.HIRE,
            agent_id=test_employer.id,
            turn=1,
            timestamp=datetime.now().timestamp(),
            hire_details=HireAction(
                job_type="Engineer",
                salary_per_turn=100.0,
                requirements="Programming skills required",
                max_employees=1
            )
        )
        
        success, _ = economy_manager.process_action(hire_action, 
                                                 {test_employer.id: test_employer, 
                                                  test_agent.id: test_agent})
        assert success == True
        
        job_listing = economy_manager.state.job_market.get_active_listings()[0]
        
        apply_action = AgentAction(
            type=ActionType.APPLY,
            agent_id=test_agent.id,
            turn=2,
            timestamp=datetime.now().timestamp(),
            apply_details=ApplyAction(
                listing_id=job_listing.id
            )
        )
        
        success, _ = economy_manager.process_action(apply_action, 
                                                 {test_employer.id: test_employer, 
                                                  test_agent.id: test_agent})
        assert success == True
        
        # Record initial resources
        employer_initial_credits = next((r.amount for r in test_employer.resources 
                                       if r.resource_type == ResourceType.CREDITS), 0)
        agent_initial_credits = next((r.amount for r in test_agent.resources 
                                    if r.resource_type == ResourceType.CREDITS), 0)
        
        # Pay salaries
        messages = economy_manager.pay_salaries({test_employer.id: test_employer, 
                                              test_agent.id: test_agent})
        
        # Check that a salary was paid
        assert len(messages) == 1
        
        # Check resource transfers
        employer_final_credits = next((r.amount for r in test_employer.resources 
                                     if r.resource_type == ResourceType.CREDITS), 0)
        agent_final_credits = next((r.amount for r in test_agent.resources 
                                  if r.resource_type == ResourceType.CREDITS), 0)
        
        # Employer should have paid 100 credits
        assert employer_final_credits == employer_initial_credits - 100.0
        
        # Agent should have received 100 credits
        assert agent_final_credits == agent_initial_credits + 100.0
    
    def test_market_report(self, economy_manager, test_agent, test_employer):
        """Test generating a market report"""
        # First create some listings
        # Job listing
        hire_action = AgentAction(
            type=ActionType.HIRE,
            agent_id=test_employer.id,
            turn=1,
            timestamp=datetime.now().timestamp(),
            hire_details=HireAction(
                job_type="Engineer",
                salary_per_turn=120.0,
                requirements="Programming skills required",
                max_employees=2
            )
        )
        
        success, _ = economy_manager.process_action(hire_action, 
                                                 {test_employer.id: test_employer, 
                                                  test_agent.id: test_agent})
        
        # Goods listing
        list_action = AgentAction(
            type=ActionType.LIST_GOODS,
            agent_id=test_employer.id,
            turn=1,
            timestamp=datetime.now().timestamp(),
            list_goods_details=ListGoodsAction(
                is_offer=True,
                resource_type=ResourceType.PHYSICAL_GOODS.value,
                amount=30.0,
                price_per_unit=25.0,
                description="Physical goods for sale"
            )
        )
        
        success, _ = economy_manager.process_action(list_action, 
                                                 {test_employer.id: test_employer, 
                                                  test_agent.id: test_agent})
        
        # Generate market report
        report = economy_manager.generate_market_report()
        
        # Check report contents
        assert "active_goods_offers" in report
        assert "active_job_offers" in report
        assert "avg_resource_prices" in report
        assert "avg_job_salaries" in report
        
        assert report["active_goods_offers"] == 1
        assert report["active_job_offers"] == 1
        
        # Check that price data is correct
        assert ResourceType.PHYSICAL_GOODS.value in report["avg_resource_prices"]
        assert report["avg_resource_prices"][ResourceType.PHYSICAL_GOODS.value] == 25.0
        
        # Check that salary data is correct
        assert "Engineer" in report["avg_job_salaries"]
        assert report["avg_job_salaries"]["Engineer"] == 120.0 