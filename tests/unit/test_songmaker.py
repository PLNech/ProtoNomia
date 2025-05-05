import unittest
import random
import pytest
from typing import List, Dict, Set
from src.engine.songmaker.models.genre_graph import GenreGraph, GenreNode
from src.engine.songmaker.generators.title_generator import TitleGenerator
from src.engine.songmaker.generators.description_generator import DescriptionGenerator
from src.models.simulation import Song

class TestGenreGraph(unittest.TestCase):
    """Test the genre graph functionality"""
    
    def setUp(self):
        """Set up a genre graph for testing"""
        self.graph = GenreGraph()
        
        # Clear existing nodes to start fresh
        self.graph.nodes = {}
        self.graph.clusters = {}
        
        # Add test genres
        self.graph.add_genre("Techno", "electronic", {"energy": 0.8, "experimental": 0.5})
        self.graph.add_genre("Ambient", "electronic", {"energy": 0.2, "experimental": 0.6})
        self.graph.add_genre("House", "electronic", {"energy": 0.7, "experimental": 0.3})
        
        # Add some connections
        self.graph.nodes["Techno"].add_connection("Ambient", 0.4)
        self.graph.nodes["Techno"].add_connection("House", 0.6)
        self.graph.nodes["Ambient"].add_connection("Techno", 0.5)
        self.graph.nodes["House"].add_connection("Techno", 0.7)
        
        # Normalize connections
        for node in self.graph.nodes.values():
            node.normalize_connections()
    
    def test_add_genre(self):
        """Test adding a genre to the graph"""
        # Add a new genre
        genre_node = self.graph.add_genre("Synthwave", "electronic", {"energy": 0.6, "experimental": 0.4})
        
        # Check it was added correctly
        self.assertIn("Synthwave", self.graph.nodes)
        self.assertEqual(genre_node.name, "Synthwave")
        self.assertEqual(genre_node.cluster, "electronic")
        self.assertAlmostEqual(genre_node.attributes["energy"], 0.6)
        self.assertAlmostEqual(genre_node.attributes["experimental"], 0.4)
        self.assertIn("Synthwave", self.graph.clusters["electronic"])
    
    def test_get_next_genre(self):
        """Test getting the next genre using Markov transition"""
        # Set current genre
        self.graph.current_genre = "Techno"
        
        # Get next genre multiple times
        next_genres = []
        for _ in range(10):
            next_genres.append(self.graph.get_next_genre())
        
        # Since this is probabilistic, just check we're getting valid genres
        for genre in next_genres:
            self.assertIn(genre, self.graph.nodes)
        
        # Check history is being updated
        self.assertEqual(len(self.graph.history), 10)
    
    def test_create_genre_fusion(self):
        """Test creating a fusion genre"""
        # Force a specific history for testing
        self.graph.history = ["Techno", "Ambient"]
        
        # Create fusion
        fusion_name, fusion_attrs = self.graph.create_genre_fusion()
        
        # Check a fusion was created
        self.assertIsNotNone(fusion_name)
        self.assertGreater(len(fusion_name), 0)
        self.assertIsInstance(fusion_attrs, dict)
        
        # Check the new genre was added to the graph
        self.assertIn(fusion_name, self.graph.nodes)
        
        # Check connections were made to parent genres
        self.assertIn("Techno", self.graph.nodes[fusion_name].connections)
        self.assertIn("Ambient", self.graph.nodes[fusion_name].connections)
        self.assertIn(fusion_name, self.graph.nodes["Techno"].connections)
        self.assertIn(fusion_name, self.graph.nodes["Ambient"].connections)

class TestTitleGenerator(unittest.TestCase):
    """Test the title generator functionality"""
    
    def setUp(self):
        """Set up a title generator for testing"""
        self.generator = TitleGenerator()
        random.seed(42)  # For reproducible tests
    
    def test_generate_title(self):
        """Test generating a title without a style bias"""
        # Generate multiple titles
        titles = [self.generator.generate_title() for _ in range(5)]
        
        # Check titles were generated
        for title in titles:
            self.assertIsInstance(title, str)
            self.assertGreater(len(title), 0)
        
        # Check we got different titles
        self.assertGreater(len(set(titles)), 1)
    
    def test_generate_title_with_style(self):
        """Test generating a title with a style bias"""
        # Generate titles with different style biases
        cyberpunk_title = self.generator.generate_title("cyberpunk")
        vaporwave_title = self.generator.generate_title("vaporwave")
        minimal_title = self.generator.generate_title("minimal")
        
        # Check titles were generated
        self.assertIsInstance(cyberpunk_title, str)
        self.assertGreater(len(cyberpunk_title), 0)
        self.assertIsInstance(vaporwave_title, str)
        self.assertGreater(len(vaporwave_title), 0)
        self.assertIsInstance(minimal_title, str)
        self.assertGreater(len(minimal_title), 0)

class TestDescriptionGenerator(unittest.TestCase):
    """Test the description generator functionality"""
    
    def setUp(self):
        """Set up a description generator for testing"""
        self.generator = DescriptionGenerator()
        random.seed(42)  # For reproducible tests
    
    def test_generate_description(self):
        """Test generating a description based on genre and tags"""
        # Generate descriptions for different genres and tags
        desc1 = self.generator.generate_description("Techno", ["electronic", "dark", "rhythmic"])
        desc2 = self.generator.generate_description("Ambient", ["atmospheric", "ethereal", "spacious"])
        desc3 = self.generator.generate_description("Synthwave", ["retro", "80s", "nostalgic"])
        
        # Check descriptions were generated
        self.assertIsInstance(desc1, str)
        self.assertGreater(len(desc1), 50)  # Ensure reasonably long description
        self.assertIsInstance(desc2, str)
        self.assertGreater(len(desc2), 50)
        self.assertIsInstance(desc3, str)
        self.assertGreater(len(desc3), 50)
        
        # Check they're different
        self.assertNotEqual(desc1, desc2)
        self.assertNotEqual(desc1, desc3)
        self.assertNotEqual(desc2, desc3)
    
    def test_genre_pattern_selection(self):
        """Test that appropriate patterns are selected for different genres"""
        # Test exact match
        pattern1 = self.generator._get_genre_pattern("Techno")
        self.assertEqual(pattern1["style"], "electronic")
        self.assertEqual(pattern1["mood"], "dark")
        
        # Test partial match
        pattern2 = self.generator._get_genre_pattern("Neo-Techno")
        self.assertEqual(pattern2["style"], "electronic")
        
        # Test default pattern for unknown genre
        pattern3 = self.generator._get_genre_pattern("CompletelyUnknownGenre")
        self.assertEqual(pattern3, self.generator.default_pattern)
    
    def test_themed_description(self):
        """Test generating a themed description"""
        # Generate descriptions with different themes
        desc1 = self.generator.generate_themed_description("cyberpunk")
        desc2 = self.generator.generate_themed_description("ambient")
        desc3 = self.generator.generate_themed_description("retro")
        
        # Check descriptions were generated
        self.assertIsInstance(desc1, str)
        self.assertGreater(len(desc1), 50)
        self.assertIsInstance(desc2, str)
        self.assertGreater(len(desc2), 50)
        self.assertIsInstance(desc3, str)
        self.assertGreater(len(desc3), 50)
        
        # Check they're different
        self.assertNotEqual(desc1, desc2)
        self.assertNotEqual(desc1, desc3)
        self.assertNotEqual(desc2, desc3)

@pytest.mark.integration
def test_song_generation_integration():
    """Test the integration of components for song generation"""
    # Initialize components
    graph = GenreGraph()
    title_gen = TitleGenerator()
    desc_gen = DescriptionGenerator()
    
    # Generate genre, title, and description
    genre = graph.get_next_genre()
    style_bias = "cyberpunk" if "cyber" in genre.lower() else None
    title = title_gen.generate_title(style_bias)
    
    # Generate tags
    available_tags = ["electronic", "future", "cyber", "neon", "digital", "synth"]
    tags = random.sample(available_tags, 3)
    
    # Generate description and BPM
    description = desc_gen.generate_description(genre, tags)
    bpm = random.randint(60, 180)
    
    # Create a song
    song = Song(
        title=title,
        genre=genre,
        bpm=bpm,
        tags=tags,
        description=description
    )
    
    # Check song was created correctly
    assert song.title == title
    assert song.genre == genre
    assert song.bpm == bpm
    assert song.tags == tags
    assert song.description == description

if __name__ == "__main__":
    unittest.main() 