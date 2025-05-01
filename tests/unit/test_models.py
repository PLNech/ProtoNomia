"""
Unit tests for the models module.
"""
import unittest

from src.models import (
    Agent, AgentPersonality, AgentNeeds, Good, GoodType,
    GlobalMarket
)


class TestModels(unittest.TestCase):
    """Test cases for the models module."""

    def test_agent_creation(self):
        """Test creating an agent."""
        agent = Agent(
            name="Test Agent", 
            personality=AgentPersonality(text="Cautious")
        )
        self.assertEqual(agent.name, "Test Agent")
        self.assertEqual(agent.personality.text, "Cautious")
        self.assertEqual(agent.credits, 0)
        self.assertEqual(agent.needs.food, 1.0)
        self.assertEqual(agent.needs.rest, 1.0)
        self.assertEqual(agent.needs.fun, 1.0)
        self.assertEqual(len(agent.goods), 0)
        self.assertTrue(agent.is_alive)
        self.assertIsNone(agent.death_day)

    def test_agent_needs(self):
        """Test agent needs validation."""
        needs = AgentNeeds(food=0.5, rest=0.7, fun=0.3)
        self.assertEqual(needs.food, 0.5)
        self.assertEqual(needs.rest, 0.7)
        self.assertEqual(needs.fun, 0.3)
        
        # Test bounds
        needs = AgentNeeds(food=1.5, rest=-0.1, fun=2.0)
        self.assertEqual(needs.food, 1.0)  # Clamped to max
        self.assertEqual(needs.rest, 0.0)  # Clamped to min
        self.assertEqual(needs.fun, 1.0)   # Clamped to max

    def test_good_creation(self):
        """Test creating a good."""
        good = Good(type=GoodType.FOOD, quality=0.75, name="Test Food")
        self.assertEqual(good.type, GoodType.FOOD)
        self.assertEqual(good.quality, 0.75)
        self.assertEqual(good.name, "Test Food")
        
        # Test quality bounds
        good = Good(type=GoodType.FUN, quality=1.5)
        self.assertEqual(good.quality, 1.0)  # Clamped to max

    def test_market_operations(self):
        """Test market operations."""
        market = GlobalMarket()
        self.assertEqual(len(market.listings), 0)
        
        # Add a listing
        good = Good(type=GoodType.FOOD, quality=0.5, name="Test Food")
        listing = market.add_listing(
            seller_id="agent_1",
            good=good,
            price=100,
            day=1
        )
        
        self.assertEqual(len(market.listings), 1)
        self.assertEqual(market.listings[0].seller_id, "agent_1")
        self.assertEqual(market.listings[0].good.name, "Test Food")
        self.assertEqual(market.listings[0].price, 100)
        
        # Get listings
        all_listings = market.get_listings()
        self.assertEqual(len(all_listings), 1)
        
        food_listings = market.get_listings(filter_type=GoodType.FOOD)
        self.assertEqual(len(food_listings), 1)
        
        fun_listings = market.get_listings(filter_type=GoodType.FUN)
        self.assertEqual(len(fun_listings), 0)
        
        # Remove a listing
        removed = market.remove_listing(listing.id)
        self.assertTrue(removed)
        self.assertEqual(len(market.listings), 0)


if __name__ == '__main__':
    unittest.main() 