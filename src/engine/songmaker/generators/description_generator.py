"""
Description Generator for Song Generator

Provides a sophisticated description generation system that creates contextual, 
varied descriptions for songs based on their genre and tags.
"""
import random
from typing import List, Dict, Optional, Tuple, Any

class DescriptionGenerator:
    """
    Advanced description generator that creates varied, contextual song descriptions
    based on genre and tags.
    """
    
    def __init__(self):
        """Initialize the description generator with various components for description creation."""
        # Components for description generation
        self.mood_descriptors = {
            "general": [
                "A haunting", "A pulsating", "An uplifting", "A melancholic", "An energetic",
                "A dreamy", "A rhythmic", "A hypnotic", "A powerful", "A soothing",
                "A chaotic", "A serene", "An atmospheric", "A driving", "A gentle"
            ],
            "dark": [
                "A distorted", "A gritty", "An ominous", "A brooding", "A tense",
                "A shadowy", "A menacing", "A mysterious", "A foreboding", "A dark"
            ],
            "light": [
                "A shimmering", "A vibrant", "A luminous", "A radiant", "A sparkling",
                "A glistening", "A brilliant", "A bright", "A crystalline", "A gleaming"
            ]
        }
        
        self.style_descriptors = {
            "electronic": [
                "futuristic", "electronic", "digital", "synthetic", "processed", 
                "programmed", "sequenced", "calculated", "quantized", "coded"
            ],
            "experimental": [
                "experimental", "avant-garde", "boundary-pushing", "innovative", "exploratory",
                "pioneering", "unconventional", "trailblazing", "groundbreaking", "cutting-edge"
            ],
            "ambient": [
                "ambient", "atmospheric", "spacious", "expansive", "textural",
                "enveloping", "immersive", "environmental", "panoramic", "ethereal"
            ],
            "cyberpunk": [
                "cyberpunk", "neo-noir", "dystopian", "tech-noir", "post-industrial",
                "cyber-dystopian", "neon-soaked", "chrome-plated", "retrofuturistic", "high-tech"
            ],
            "retro": [
                "retro", "nostalgic", "vintage", "throwback", "classic",
                "old-school", "revivalist", "period", "retrospective", "time-honored"
            ]
        }
        
        self.sound_elements = {
            "electronic": [
                "synth sequences", "drum patterns", "bass lines", "arpeggios", "pads",
                "modulations", "filters", "envelopes", "oscillations", "waveforms"
            ],
            "ambient": [
                "ambient textures", "field recordings", "drones", "soundscapes", "atmospheric layers",
                "reverberations", "spatial effects", "environmental sounds", "background noises", "aural textures"
            ],
            "rhythmic": [
                "rhythmic patterns", "beats", "percussion", "grooves", "tempos",
                "time signatures", "polyrhythms", "pulses", "meters", "cadences"
            ],
            "melodic": [
                "melodies", "harmonies", "chord progressions", "tonal shifts", "key changes",
                "scales", "modes", "intervals", "motifs", "themes"
            ],
            "textural": [
                "textures", "layers", "densities", "fabrics", "weaves",
                "timbres", "tones", "colors", "shades", "granularities"
            ],
            "digital": [
                "digital artifacts", "bit-crushing", "glitches", "compression", "quantization",
                "sample-rate reduction", "aliasing", "clipping", "distortion", "noise"
            ]
        }
        
        self.musical_journeys = {
            "urban": [
                "takes the listener on a journey through neon-lit streets",
                "captures the essence of midnight in the metropolis",
                "pulses with the heartbeat of the underground",
                "evokes the feeling of cruising through a digital landscape",
                "paints a vivid soundscape of virtual reality"
            ],
            "emotional": [
                "explores the boundaries between analog and digital",
                "creates an immersive atmosphere of future nostalgia",
                "merges synthetic and organic elements seamlessly",
                "builds a sonic architecture of light and shadow",
                "distills complex emotions into pure sonic energy"
            ],
            "technical": [
                "deconstructs conventional structures into something new",
                "balances tension and release with precision",
                "transforms everyday sounds into hypnotic rhythms",
                "weaves intricate patterns of sound and silence",
                "creates a dialogue between human and machine"
            ],
            "cultural": [
                "channels the spirit of cyberpunk literature",
                "reimagines retro sounds through a modern lens",
                "blends cultural influences into a futuristic fusion",
                "builds momentum through carefully crafted progression",
                "invites the listener into a world of sonic imagination"
            ]
        }
        
        self.emotional_impacts = {
            "nostalgic": [
                "leaving a lasting impression of melancholic hope",
                "evoking nostalgia for a time that never existed",
                "channeling the emotional essence of retrofuturism",
                "creating a bittersweet longing for lost futures",
                "recalling memories of times yet to come"
            ],
            "energetic": [
                "delivering a powerful surge of energy and emotion",
                "creating an invigorating sonic experience",
                "charging the atmosphere with dynamic intensity",
                "propelling the listener into motion",
                "generating an irresistible kinetic pulse"
            ],
            "contemplative": [
                "inspiring a sense of wonder and possibility",
                "triggering both introspection and movement",
                "conveying complex emotions through sound alone",
                "transporting the listener to another dimension",
                "offering a moment of peaceful reflection"
            ],
            "immersive": [
                "creating an emotional resonance that lingers",
                "crafting a perfect moment of musical catharsis",
                "generating an atmosphere of mysterious anticipation",
                "providing an escape from everyday reality",
                "establishing a complete alternate reality through sound"
            ]
        }
        
        # Genre-specific patterns
        self.genre_patterns = {
            "Techno": {
                "mood": "dark",
                "style": "electronic",
                "sound": ["rhythmic", "electronic"],
                "journey": "urban",
                "impact": "energetic"
            },
            "House": {
                "mood": "general",
                "style": "electronic",
                "sound": ["rhythmic", "melodic"],
                "journey": "urban",
                "impact": "energetic"
            },
            "Ambient": {
                "mood": "light",
                "style": "ambient",
                "sound": ["ambient", "textural"],
                "journey": "emotional",
                "impact": "contemplative"
            },
            "Synthwave": {
                "mood": "general",
                "style": "retro",
                "sound": ["melodic", "electronic"],
                "journey": "cultural",
                "impact": "nostalgic"
            },
            "Vaporwave": {
                "mood": "light",
                "style": "retro",
                "sound": ["ambient", "digital"],
                "journey": "cultural",
                "impact": "nostalgic"
            },
            "Cyberpunk": {
                "mood": "dark",
                "style": "cyberpunk",
                "sound": ["electronic", "digital"],
                "journey": "urban",
                "impact": "immersive"
            },
            "IDM": {
                "mood": "general",
                "style": "experimental",
                "sound": ["electronic", "rhythmic"],
                "journey": "technical",
                "impact": "contemplative"
            },
            "Drum and Bass": {
                "mood": "dark",
                "style": "electronic",
                "sound": ["rhythmic", "electronic"],
                "journey": "urban",
                "impact": "energetic"
            },
            "Trance": {
                "mood": "light",
                "style": "electronic",
                "sound": ["melodic", "electronic"],
                "journey": "emotional",
                "impact": "immersive"
            },
            "Lo-Fi": {
                "mood": "general",
                "style": "retro",
                "sound": ["textural", "digital"],
                "journey": "emotional",
                "impact": "contemplative"
            }
        }
        
        # Default pattern for unknown genres
        self.default_pattern = {
            "mood": "general",
            "style": "electronic",
            "sound": ["electronic", "textural"],
            "journey": "emotional",
            "impact": "immersive"
        }
        
    def _get_genre_pattern(self, genre: str) -> Dict[str, Any]:
        """
        Get a genre pattern for the given genre. If the exact genre isn't found,
        try to match with a known genre by checking if it contains a known genre name.
        """
        # Try exact match
        if genre in self.genre_patterns:
            return self.genre_patterns[genre]
        
        # Try partial match
        for known_genre, pattern in self.genre_patterns.items():
            if known_genre.lower() in genre.lower() or genre.lower() in known_genre.lower():
                return pattern
        
        # Default pattern if no match
        return self.default_pattern
    
    def _adjust_pattern_for_tags(self, pattern: Dict[str, Any], tags: List[str]) -> Dict[str, Any]:
        """Adjust genre pattern based on tags to make description more contextual."""
        adjusted_pattern = pattern.copy()
        
        # Mood adjustments
        if any(tag in ["dark", "gritty", "gloomy", "apocalyptic", "dystopian", "noir"] for tag in tags):
            adjusted_pattern["mood"] = "dark"
        elif any(tag in ["bright", "uplifting", "light", "happy", "cheerful", "optimistic"] for tag in tags):
            adjusted_pattern["mood"] = "light"
            
        # Style adjustments  
        if any(tag in ["experimental", "avant-garde", "abstract", "unconventional"] for tag in tags):
            adjusted_pattern["style"] = "experimental"
        elif any(tag in ["ambient", "atmospheric", "spacious", "ethereal"] for tag in tags):
            adjusted_pattern["style"] = "ambient"
        elif any(tag in ["retro", "vintage", "nostalgic", "80s", "90s"] for tag in tags):
            adjusted_pattern["style"] = "retro"
        elif any(tag in ["cyberpunk", "futuristic", "dystopian", "neon", "tech-noir"] for tag in tags):
            adjusted_pattern["style"] = "cyberpunk"
            
        # Journey adjustments
        if any(tag in ["emotional", "introspective", "reflective", "deep"] for tag in tags):
            adjusted_pattern["journey"] = "emotional"
        elif any(tag in ["urban", "city", "street", "metropolitan", "industrial"] for tag in tags):
            adjusted_pattern["journey"] = "urban"
        elif any(tag in ["technical", "complex", "intricate", "precise", "detailed"] for tag in tags):
            adjusted_pattern["journey"] = "technical"
            
        # Impact adjustments
        if any(tag in ["nostalgic", "memory", "remembrance", "throwback"] for tag in tags):
            adjusted_pattern["impact"] = "nostalgic"
        elif any(tag in ["energetic", "powerful", "intense", "driving", "dynamic"] for tag in tags):
            adjusted_pattern["impact"] = "energetic"
        elif any(tag in ["contemplative", "thoughtful", "philosophical", "meditative"] for tag in tags):
            adjusted_pattern["impact"] = "contemplative"
        elif any(tag in ["immersive", "absorbing", "enveloping", "engaging"] for tag in tags):
            adjusted_pattern["impact"] = "immersive"
            
        # Sound element adjustments
        sound_elements = []
        if any(tag in ["rhythmic", "beat", "percussion", "drums", "groove"] for tag in tags):
            sound_elements.append("rhythmic")
        if any(tag in ["melodic", "harmonic", "tuneful", "musical"] for tag in tags):
            sound_elements.append("melodic")
        if any(tag in ["ambient", "atmospheric", "textural", "soundscape"] for tag in tags):
            sound_elements.append("ambient")
        if any(tag in ["glitch", "digital", "electronic", "processed"] for tag in tags):
            sound_elements.append("digital")
            
        if sound_elements:
            adjusted_pattern["sound"] = sound_elements
            
        return adjusted_pattern
    
    def generate_description(self, genre: str, tags: List[str]) -> str:
        """
        Generate a rich, contextual description for a song based on its genre and tags.
        
        Args:
            genre: The song's genre
            tags: List of tags associated with the song
            
        Returns:
            A generated description
        """
        # Get base pattern for genre
        pattern = self._get_genre_pattern(genre)
        
        # Adjust pattern based on tags
        pattern = self._adjust_pattern_for_tags(pattern, tags)
        
        # Select components based on pattern
        mood = random.choice(self.mood_descriptors[pattern["mood"]])
        style = random.choice(self.style_descriptors[pattern["style"]])
        
        # Get two different sound elements
        sound_categories = pattern["sound"]
        if len(sound_categories) < 2:
            sound_categories = sound_categories + ["electronic"]
        
        sound_cat1, sound_cat2 = random.sample(sound_categories, 2)
        sound1 = random.choice(self.sound_elements[sound_cat1])
        sound2 = random.choice(self.sound_elements[sound_cat2])
        
        journey = random.choice(self.musical_journeys[pattern["journey"]])
        impact = random.choice(self.emotional_impacts[pattern["impact"]])
        
        # Construct the description
        description = (
            f"{mood} {style} track that blends {sound1} "
            f"with {sound2}. The composition {journey}, "
            f"{impact}."
        )
        
        return description
    
    def generate_themed_description(self, theme: str) -> str:
        """
        Generate a description with a specific theme.
        
        Args:
            theme: The theme to target (e.g., 'cyberpunk', 'ambient', 'retro')
            
        Returns:
            A themed description
        """
        # Map theme to appropriate patterns
        if theme.lower() == "cyberpunk":
            pattern = {
                "mood": "dark",
                "style": "cyberpunk",
                "sound": ["electronic", "digital"],
                "journey": "urban",
                "impact": "immersive"
            }
        elif theme.lower() == "ambient":
            pattern = {
                "mood": "light",
                "style": "ambient",
                "sound": ["ambient", "textural"],
                "journey": "emotional",
                "impact": "contemplative"
            }
        elif theme.lower() in ["retro", "vaporwave", "synthwave"]:
            pattern = {
                "mood": "general",
                "style": "retro",
                "sound": ["melodic", "electronic"],
                "journey": "cultural",
                "impact": "nostalgic"
            }
        elif theme.lower() in ["techno", "industrial"]:
            pattern = {
                "mood": "dark",
                "style": "electronic",
                "sound": ["rhythmic", "electronic"],
                "journey": "urban",
                "impact": "energetic"
            }
        else:
            # Default pattern for unknown themes
            pattern = self.default_pattern
        
        # Select components based on pattern
        mood = random.choice(self.mood_descriptors[pattern["mood"]])
        style = random.choice(self.style_descriptors[pattern["style"]])
        
        # Get two different sound elements
        sound_categories = pattern["sound"]
        if len(sound_categories) < 2:
            sound_categories = sound_categories + ["electronic"]
        
        sound_cat1, sound_cat2 = random.sample(sound_categories, 2)
        sound1 = random.choice(self.sound_elements[sound_cat1])
        sound2 = random.choice(self.sound_elements[sound_cat2])
        
        journey = random.choice(self.musical_journeys[pattern["journey"]])
        impact = random.choice(self.emotional_impacts[pattern["impact"]])
        
        # Construct the description
        description = (
            f"{mood} {style} track that blends {sound1} "
            f"with {sound2}. The composition {journey}, "
            f"{impact}."
        )
        
        return description


# Create singleton instance
description_generator = DescriptionGenerator()


if __name__ == "__main__":
    # Test generation
    print("Techno description:")
    print(description_generator.generate_description("Techno", ["dark", "electronic", "rhythmic"]))
    
    print("\nAmbient description:")
    print(description_generator.generate_description("Ambient", ["light", "ambient", "textural"]))
    
    print("\nSynthwave description:")
    print(description_generator.generate_description("Synthwave", ["retro", "melodic", "electronic"]))
    
    print("\nVaporwave description:")
    print(description_generator.generate_description("Vaporwave", ["light", "retro", "ambient"]))
    
    print("\nCyberpunk description:")
    print(description_generator.generate_description("Cyberpunk", ["dark", "cyberpunk", "electronic"]))
    
    print("\nThemed description:")
    print(description_generator.generate_themed_description("cyberpunk")) 