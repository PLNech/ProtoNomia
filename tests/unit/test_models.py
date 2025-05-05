"""
Unit tests for the models module.
"""
import unittest

from src.models import (
    Agent, AgentPersonality, AgentNeeds, Good, GoodType,
    GlobalMarket, Song, SongBook
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


class TestSongGenerator(unittest.TestCase):
    """Test the Song model and SongBook functionality used by the Song Generator."""
    
    def setUp(self):
        """Set up test data."""
        self.dummy_agent = Agent(
            name="Test Agent",
            age=30,
            personality=AgentPersonality(),
            needs=AgentNeeds()
        )
        
    def test_song_creation(self):
        """Test creating a Song object with different parameters."""
        # Test with minimal parameters
        song1 = Song(title="Test Song")
        self.assertEqual(song1.title, "Test Song")
        self.assertEqual(song1.genre, "Electronica")  # Default genre
        self.assertEqual(song1.bpm, 113)  # Default BPM
        self.assertEqual(song1.tags, [])  # Default empty tags
        
        # Test with all parameters
        song2 = Song(
            title="Full Song",
            genre="Cyberpunk",
            bpm=140,
            tags=["neon", "synth", "futuristic"],
            description="A test song with all parameters"
        )
        self.assertEqual(song2.title, "Full Song")
        self.assertEqual(song2.genre, "Cyberpunk")
        self.assertEqual(song2.bpm, 140)
        self.assertEqual(song2.tags, ["neon", "synth", "futuristic"])
        self.assertEqual(song2.description, "A test song with all parameters")
        
    def test_songbook_functionality(self):
        """Test the SongBook's ability to store songs by day."""
        songbook = SongBook()
        
        # Add songs for different days
        song1 = Song(title="Day 1 Song", genre="Ambient")
        song2 = Song(title="Day 2 Song", genre="Techno")
        song3 = Song(title="Day 2 Song 2", genre="Synthwave")
        
        songbook.add_song(self.dummy_agent, song1, 1)
        songbook.add_song(self.dummy_agent, song2, 2)
        songbook.add_song(self.dummy_agent, song3, 2)
        
        # Test length
        self.assertEqual(len(songbook), 3)
        
        # Test getting songs by day
        day1_songs = songbook.day(1)
        day2_songs = songbook.day(2)
        
        self.assertEqual(len(day1_songs), 1)
        self.assertEqual(len(day2_songs), 2)
        self.assertEqual(day1_songs[0].song.title, "Day 1 Song")
        self.assertEqual(day2_songs[0].song.title, "Day 2 Song")
        self.assertEqual(day2_songs[1].song.title, "Day 2 Song 2")
        
        # Test genres are tracked
        self.assertIn("Ambient", songbook.genres)
        self.assertIn("Techno", songbook.genres)
        self.assertIn("Synthwave", songbook.genres)
        self.assertEqual(len(songbook.genres), 3)
        
        # Test non-existent day returns empty list
        self.assertEqual(songbook.day(999), [])
        
    def test_song_string_representation(self):
        """Test the string representation of a Song object."""
        # Test without tags and description
        song1 = Song(title="Basic Song", genre="Techno", bpm=120)
        expected_str1 = "'Basic Song' (Techno, 120 BPM)"
        self.assertEqual(str(song1), expected_str1)
        
        # Test with tags but no description
        song2 = Song(
            title="Tagged Song", 
            genre="Ambient", 
            bpm=90, 
            tags=["chill", "relaxing"]
        )
        expected_str2 = "'Tagged Song' (Ambient, 90 BPM) [chill, relaxing]"
        self.assertEqual(str(song2), expected_str2)
        
        # Test with tags and description
        song3 = Song(
            title="Full Song", 
            genre="Synthwave", 
            bpm=110,
            tags=["retro", "80s", "synth"],
            description="A nostalgic synthwave track"
        )
        expected_str3 = "'Full Song' (Synthwave, 110 BPM) [retro, 80s, synth] - A nostalgic synthwave track"
        self.assertEqual(str(song3), expected_str3)


if __name__ == '__main__':
    unittest.main() 