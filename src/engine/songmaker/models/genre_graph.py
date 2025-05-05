"""
Genre Graph Model for the Song Generator.
Provides a graph-based representation of music genres with Markov chain transitions.
"""
import random
import json
import numpy as np
from typing import Dict, List, Set, Tuple, Optional, Any
from pathlib import Path


class GenreNode:
    """Represents a single genre node in the genre graph."""
    
    def __init__(self, name: str, cluster: str = "electronic", 
                 attributes: Optional[Dict[str, float]] = None):
        """
        Initialize a genre node.
        
        Args:
            name: The name of the genre
            cluster: The broader cluster/category this genre belongs to
            attributes: Dictionary of genre attributes (e.g. energy, tempo, experimental)
                        with values between 0-1
        """
        self.name = name
        self.cluster = cluster
        self.attributes = attributes or {
            "energy": random.random(),
            "experimental": random.random(),
            "electronic": random.random(),
            "acoustic": random.random(),
            "darkness": random.random(),
            "complexity": random.random()
        }
        self.connections: Dict[str, float] = {}  # Maps genre name to transition probability
    
    def add_connection(self, genre_name: str, weight: float = 1.0):
        """Add or update a connection to another genre."""
        self.connections[genre_name] = weight
    
    def remove_connection(self, genre_name: str):
        """Remove a connection to another genre if it exists."""
        if genre_name in self.connections:
            del self.connections[genre_name]
    
    def normalize_connections(self):
        """Normalize connection weights to form a valid probability distribution."""
        total_weight = sum(self.connections.values())
        if total_weight > 0:
            for genre in self.connections:
                self.connections[genre] /= total_weight
    
    def get_next_genre(self) -> str:
        """Use the Markov model to select the next genre based on transition probabilities."""
        if not self.connections:
            return self.name  # No connections, stay in the same genre
        
        genres = list(self.connections.keys())
        probabilities = list(self.connections.values())
        return random.choices(genres, weights=probabilities, k=1)[0]
    
    def similarity(self, other: 'GenreNode') -> float:
        """Calculate similarity between two genres based on their attributes."""
        if not self.attributes or not other.attributes:
            return 0.0
        
        # Only compare attributes that both genres have
        common_attrs = set(self.attributes.keys()) & set(other.attributes.keys())
        if not common_attrs:
            return 0.0
        
        # Calculate Euclidean distance for common attributes
        distance = sum((self.attributes[attr] - other.attributes[attr])**2 
                       for attr in common_attrs)
        distance = distance ** 0.5  # Square root for Euclidean distance
        
        # Convert distance to similarity (1 = identical, 0 = completely different)
        max_possible_distance = (len(common_attrs) ** 0.5)  # Max distance if all attributes differ by 1.0
        similarity = 1 - (distance / max_possible_distance)
        
        return similarity
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "cluster": self.cluster,
            "attributes": self.attributes,
            "connections": self.connections
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GenreNode':
        """Create a GenreNode from a dictionary."""
        node = cls(name=data["name"], cluster=data["cluster"], attributes=data["attributes"])
        node.connections = data.get("connections", {})
        return node
    
    def __str__(self) -> str:
        return f"Genre({self.name}, {self.cluster})"
    
    def __repr__(self) -> str:
        return self.__str__()


class GenreGraph:
    """
    A graph representation of music genres with Markov chain transitions.
    Allows for genre evolution, fusion, and discovery based on current position in the genre space.
    """
    
    def __init__(self):
        """Initialize an empty genre graph."""
        self.nodes: Dict[str, GenreNode] = {}  # Maps genre name to GenreNode
        self.clusters: Dict[str, List[str]] = {}  # Maps cluster name to list of genre names
        
        # Current state for Markov traversal
        self.current_genre: Optional[str] = None
        
        # Parameters that control genre generation
        self.jump_probability = 0.15  # Probability of random jump vs. following connections
        self.exploration_factor = 0.2  # Controls tendency to explore new connections
        self.fusion_probability = 0.25  # Probability of creating fusion genres
        
        # History of visited genres for trend analysis
        self.history: List[str] = []
        self.history_max_size = 50
        
        # Initialize with core genres
        self._initialize_core_genres()
    
    def _initialize_core_genres(self):
        """Initialize the graph with core electronic music genres."""
        # Core electronic genres
        core_genres = [
            ("Techno", "electronic", {"energy": 0.8, "experimental": 0.5, "electronic": 0.9, "darkness": 0.6}),
            ("House", "electronic", {"energy": 0.7, "experimental": 0.3, "electronic": 0.9, "darkness": 0.3}),
            ("Ambient", "electronic", {"energy": 0.2, "experimental": 0.6, "electronic": 0.8, "darkness": 0.4}),
            ("Drum and Bass", "electronic", {"energy": 0.9, "experimental": 0.5, "electronic": 0.9, "darkness": 0.5}),
            ("Synthwave", "electronic", {"energy": 0.6, "experimental": 0.4, "electronic": 0.9, "darkness": 0.5}),
            ("Vaporwave", "electronic", {"energy": 0.3, "experimental": 0.7, "electronic": 0.8, "darkness": 0.4}),
            ("Dubstep", "electronic", {"energy": 0.8, "experimental": 0.6, "electronic": 0.9, "darkness": 0.7}),
            ("Trance", "electronic", {"energy": 0.7, "experimental": 0.4, "electronic": 0.9, "darkness": 0.3}),
            ("IDM", "electronic", {"energy": 0.6, "experimental": 0.9, "electronic": 0.9, "darkness": 0.5}),
            ("Lo-Fi", "electronic", {"energy": 0.3, "experimental": 0.5, "electronic": 0.7, "darkness": 0.4})
        ]
        
        # Add core genres to the graph
        for name, cluster, attributes in core_genres:
            self.add_genre(name, cluster, attributes)
        
        # Connect related genres
        self._create_initial_connections()
        
        # Set a random starting genre
        if self.nodes:
            self.current_genre = random.choice(list(self.nodes.keys()))
            self.history.append(self.current_genre)
    
    def _create_initial_connections(self):
        """Create initial connections between core genres based on similarity."""
        genres = list(self.nodes.keys())
        
        for i, genre1 in enumerate(genres):
            for genre2 in genres[i+1:]:
                node1 = self.nodes[genre1]
                node2 = self.nodes[genre2]
                
                similarity = node1.similarity(node2)
                
                # Only connect somewhat similar genres
                if similarity > 0.5:
                    # Bidirectional connection with strength based on similarity
                    node1.add_connection(genre2, similarity)
                    node2.add_connection(genre1, similarity)
        
        # Normalize all connections
        for node in self.nodes.values():
            node.normalize_connections()
    
    def add_genre(self, name: str, cluster: str = "electronic", 
                  attributes: Optional[Dict[str, float]] = None) -> GenreNode:
        """
        Add a new genre to the graph.
        
        Args:
            name: The name of the genre
            cluster: The broader cluster/category this genre belongs to
            attributes: Dictionary of genre attributes with values between 0-1
            
        Returns:
            The created GenreNode
        """
        # Add the genre node
        node = GenreNode(name, cluster, attributes)
        self.nodes[name] = node
        
        # Update cluster tracking
        if cluster not in self.clusters:
            self.clusters[cluster] = []
        self.clusters[cluster].append(name)
        
        return node
    
    def add_connections_for_new_genre(self, genre_name: str):
        """
        Add connections for a newly added genre based on similarity.
        
        Args:
            genre_name: The name of the genre to add connections for
        """
        if genre_name not in self.nodes:
            return
        
        new_node = self.nodes[genre_name]
        
        # Connect to similar genres
        for other_name, other_node in self.nodes.items():
            if other_name == genre_name:
                continue
            
            similarity = new_node.similarity(other_node)
            
            # Only connect somewhat similar genres
            if similarity > 0.5:
                # Bidirectional connection with strength based on similarity
                new_node.add_connection(other_name, similarity)
                other_node.add_connection(genre_name, similarity * 0.8)  # Slightly less likely to go to new genre
        
        # Normalize connections
        new_node.normalize_connections()
        for node in self.nodes.values():
            node.normalize_connections()
    
    def get_next_genre(self) -> str:
        """
        Get the next genre using the Markov model.
        
        Returns:
            The name of the next genre
        """
        if not self.nodes:
            return ""
        
        if not self.current_genre or self.current_genre not in self.nodes:
            self.current_genre = random.choice(list(self.nodes.keys()))
        
        current_node = self.nodes[self.current_genre]
        
        # Random jump with low probability
        if random.random() < self.jump_probability:
            next_genre = random.choice(list(self.nodes.keys()))
        else:
            # Follow connections with high probability
            next_genre = current_node.get_next_genre()
        
        # Update current state
        self.current_genre = next_genre
        
        # Update history
        self.history.append(next_genre)
        if len(self.history) > self.history_max_size:
            self.history.pop(0)
        
        return next_genre
    
    def create_genre_fusion(self) -> Tuple[str, Dict[str, float]]:
        """
        Create a fusion of two genres to discover a new genre.
        
        Returns:
            A tuple of (new_genre_name, attributes)
        """
        if len(self.nodes) < 2:
            return ("", {})
        
        # Select two genres to fuse
        if len(self.history) >= 2:
            # Prefer recent genres from history
            source_genres = random.sample(self.history[-10:], 2)
        else:
            # Random selection if history is insufficient
            source_genres = random.sample(list(self.nodes.keys()), 2)
        
        genre1 = source_genres[0]
        genre2 = source_genres[1]
        
        node1 = self.nodes[genre1]
        node2 = self.nodes[genre2]
        
        # Fusion components
        prefixes = ["Neo", "Future", "Post", "Nu", "Deep", "Hyper", "Vapor", "Glitch", "Dark", "Cosmic", "Synth", "Micro"]
        suffixes = ["wave", "step", "core", "tech", "funk", "house", "beat", "pop", "tronica", "hop", "bass", "style"]
        connectors = ["", "-", " ", "/"]
        
        # Pick different name generation strategies
        strategy = random.choice([1, 2, 3, 4])
        
        if strategy == 1:
            # Prefix + one of the genres (e.g., "Neo Techno")
            prefix = random.choice(prefixes)
            base = random.choice([genre1, genre2])
            fusion_name = f"{prefix} {base}"
        
        elif strategy == 2:
            # Simple Combination (e.g., "Techno House")
            g1 = genre1.split()[0] if " " in genre1 else genre1
            g2 = genre2.split()[0] if " " in genre2 else genre2
            connector = random.choice(connectors)
            fusion_name = f"{g1}{connector}{g2}"
        
        elif strategy == 3:
            # Root + Suffix (e.g., "Techwave")
            g1_root = genre1.split()[0] if " " in genre1 else genre1
            # Remove existing suffixes if present
            for suffix in suffixes:
                if g1_root.lower().endswith(suffix.lower()):
                    g1_root = g1_root[:-len(suffix)]
            fusion_name = f"{g1_root}{random.choice(suffixes)}"
        
        else:
            # Complex Fusion (e.g., "Dark Ambient Techno")
            prefix = random.choice(prefixes)
            g1 = genre1.split()[0] if " " in genre1 else genre1
            g2 = genre2.split()[0] if " " in genre2 else genre2
            fusion_name = f"{prefix} {g1} {g2}"
        
        # Combine attributes
        mix_ratio = random.random()  # How much of genre1 vs genre2
        fused_attributes = {}
        
        # Merge attributes from both genres
        all_attrs = set(node1.attributes.keys()) | set(node2.attributes.keys())
        for attr in all_attrs:
            val1 = node1.attributes.get(attr, 0.5)
            val2 = node2.attributes.get(attr, 0.5)
            # Weighted average with some randomness
            fused_attributes[attr] = (val1 * mix_ratio + val2 * (1 - mix_ratio)) * (0.8 + 0.4 * random.random())
            # Clamp to valid range
            fused_attributes[attr] = max(0.0, min(1.0, fused_attributes[attr]))
        
        # Add a touch of randomness to make it unique
        if "experimental" in fused_attributes:
            fused_attributes["experimental"] += random.random() * 0.2
            fused_attributes["experimental"] = min(1.0, fused_attributes["experimental"])
        
        # Determine cluster (use most prominent parent cluster)
        cluster1 = node1.cluster
        cluster2 = node2.cluster
        fusion_cluster = cluster1 if random.random() < 0.5 else cluster2
        
        # Create the new genre
        new_node = self.add_genre(fusion_name, fusion_cluster, fused_attributes)
        
        # Connect to parent genres with strong connections
        new_node.add_connection(genre1, 0.7)
        new_node.add_connection(genre2, 0.7)
        self.nodes[genre1].add_connection(fusion_name, 0.3)
        self.nodes[genre2].add_connection(fusion_name, 0.3)
        
        # Add connections to other similar genres
        self.add_connections_for_new_genre(fusion_name)
        
        return (fusion_name, fused_attributes)
    
    def get_genre_attributes(self, genre_name: str) -> Dict[str, float]:
        """Get the attributes of a genre."""
        if genre_name in self.nodes:
            return self.nodes[genre_name].attributes
        return {}
    
    def save_to_file(self, filepath: str = "genre_graph.json"):
        """Save the genre graph to a JSON file."""
        data = {
            "nodes": {name: node.to_dict() for name, node in self.nodes.items()},
            "clusters": self.clusters,
            "current_genre": self.current_genre,
            "parameters": {
                "jump_probability": self.jump_probability,
                "exploration_factor": self.exploration_factor,
                "fusion_probability": self.fusion_probability
            }
        }
        
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
    
    def load_from_file(self, filepath: str = "genre_graph.json") -> bool:
        """
        Load the genre graph from a JSON file.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if not Path(filepath).exists():
                return False
            
            with open(filepath, "r") as f:
                data = json.load(f)
            
            # Load nodes
            self.nodes = {}
            for name, node_data in data["nodes"].items():
                self.nodes[name] = GenreNode.from_dict(node_data)
            
            # Load clusters
            self.clusters = data["clusters"]
            
            # Load current state
            self.current_genre = data.get("current_genre")
            
            # Load parameters
            params = data.get("parameters", {})
            self.jump_probability = params.get("jump_probability", self.jump_probability)
            self.exploration_factor = params.get("exploration_factor", self.exploration_factor)
            self.fusion_probability = params.get("fusion_probability", self.fusion_probability)
            
            return True
        except Exception as e:
            print(f"Error loading genre graph: {e}")
            return False
    
    def get_all_genres(self) -> List[str]:
        """Get a list of all genre names."""
        return list(self.nodes.keys())
    
    def get_genres_by_cluster(self, cluster: str) -> List[str]:
        """Get all genres in a specific cluster."""
        return self.clusters.get(cluster, [])
    
    def get_similar_genres(self, genre_name: str, threshold: float = 0.6) -> List[Tuple[str, float]]:
        """
        Get genres similar to the specified genre.
        
        Args:
            genre_name: The reference genre name
            threshold: Minimum similarity threshold (0-1)
            
        Returns:
            List of (genre_name, similarity) tuples sorted by similarity
        """
        if genre_name not in self.nodes:
            return []
        
        reference = self.nodes[genre_name]
        similar = []
        
        for name, node in self.nodes.items():
            if name == genre_name:
                continue
            
            similarity = reference.similarity(node)
            if similarity >= threshold:
                similar.append((name, similarity))
        
        # Sort by similarity (highest first)
        similar.sort(key=lambda x: x[1], reverse=True)
        return similar
    
    def __len__(self) -> int:
        return len(self.nodes)


# Create a singleton instance
genre_graph = GenreGraph() 