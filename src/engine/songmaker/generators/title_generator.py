"""
Title Generator for Song Generator

Provides a sophisticated title generation system with various styles, themes, and 
formatting options to create unique and varied song titles.
"""
import random
import re
import string
from typing import List, Dict, Tuple, Optional, Callable, Any

class TitleGenerator:
    """
    Advanced title generator that creates varied, stylized song titles
    using different templates, themes, and formatting techniques.
    """
    
    def __init__(self):
        """Initialize the title generator with various components for title creation."""
        # Core word collections for title generation
        self.nouns = {
            "tech": [
                "data", "code", "system", "network", "algorithm", "circuit", "interface", 
                "pixel", "binary", "vector", "matrix", "signal", "frequency", "protocol",
                "server", "mainframe", "terminal", "cascade", "node", "grid", "sector",
                "core", "portal", "cipher", "loop", "function", "array", "buffer", "cache",
                "quantum", "mirror", "chrome", "steel", "glass", "pulse", "byte", "stream"
            ],
            "urban": [
                "city", "street", "skyline", "alley", "tower", "bridge", "subway", "highway",
                "district", "zone", "block", "avenue", "station", "downtown", "horizon", 
                "rooftop", "concrete", "skyscraper", "metro", "crowd", "traffic", "neon",
                "light", "shadow", "silhouette", "building", "intersection", "billboard"
            ],
            "nature": [
                "ocean", "rain", "storm", "sky", "cloud", "wind", "mountain", "river", "forest",
                "star", "moon", "sun", "dawn", "dusk", "twilight", "aurora", "horizon",
                "crystal", "frost", "ice", "mist", "vapor", "wave", "current", "flow"
            ],
            "emotion": [
                "dream", "hope", "fear", "love", "sorrow", "joy", "rage", "ecstasy", "serenity",
                "isolation", "tension", "desire", "regret", "euphoria", "nostalgia", "anxiety",
                "melancholy", "bliss", "tranquility", "despair", "wonder", "solitude"
            ],
            "abstract": [
                "echo", "void", "infinity", "eternity", "reality", "illusion", "dimension",
                "memory", "truth", "fate", "vision", "paradigm", "enigma", "paradox", "entropy",
                "symmetry", "synchronicity", "threshold", "abyss", "space", "time", "moment",
                "reflection", "ghost", "shadow", "whisper", "silence", "static", "pulse", "wave"
            ],
            "cyberpunk": [
                "android", "cyborg", "neural", "synth", "virtual", "digital", "cyber", "tech",
                "net", "wire", "hack", "glitch", "hologram", "simulation", "dystopia", "utopia",
                "megacorp", "upload", "download", "encryption", "decryption", "implant", "augment"
            ]
        }
        
        self.adjectives = {
            "tech": [
                "digital", "virtual", "electronic", "binary", "quantum", "neural", "synthetic",
                "cybernetic", "holographic", "automated", "algorithmic", "encoded", "encrypted",
                "modular", "technical", "futuristic", "mechanical", "systematic", "augmented"
            ],
            "emotional": [
                "dreamy", "ethereal", "melancholic", "euphoric", "nostalgic", "surreal", "lonely",
                "forgotten", "lost", "distant", "broken", "haunted", "serene", "tranquil", "chaotic",
                "turbulent", "peaceful", "feverish", "cold", "warm", "hollow", "empty", "full"
            ],
            "atmospheric": [
                "hazy", "misty", "foggy", "rainy", "stormy", "cloudy", "sunny", "shimmering",
                "glowing", "pulsing", "vibrating", "resonating", "echoing", "fading", "frozen",
                "flowing", "drifting", "floating", "submerged", "crystalline", "luminous", "dark"
            ],
            "temporal": [
                "eternal", "endless", "infinite", "momentary", "fleeting", "ephemeral", "persistent",
                "ancient", "future", "past", "present", "timeless", "cyclical", "recurring", "constant",
                "evolving", "static", "dynamic", "suspended", "accelerated", "delayed", "immediate"
            ],
            "cyberpunk": [
                "neon", "chrome", "synthetic", "artificial", "augmented", "virtual", "wired",
                "wireless", "encrypted", "decoded", "hacked", "modded", "retrofitted", "urban",
                "industrial", "corporate", "subversive", "underground", "glitched", "corrupted"
            ]
        }
        
        self.verbs = {
            "motion": [
                "drift", "float", "flow", "fade", "dissolve", "resonate", "pulse", "vibrate", 
                "oscillate", "synchronize", "converge", "diverge", "accelerate", "decelerate",
                "orbit", "spiral", "cascade", "collapse", "expand", "contract", "shatter", "merge"
            ],
            "perception": [
                "see", "hear", "feel", "sense", "perceive", "remember", "forget", "imagine",
                "dream", "envision", "recognize", "discover", "observe", "witness", "experience"
            ],
            "digital": [
                "download", "upload", "connect", "disconnect", "sync", "process", "compute",
                "encode", "decode", "encrypt", "decrypt", "compile", "debug", "execute", "hack",
                "glitch", "simulate", "render", "buffer", "stream", "scan", "parse", "initialize"
            ]
        }
        
        # Prepositions and connectors for phrase building
        self.prepositions = [
            "in", "of", "through", "beyond", "beneath", "within", "without", "across", 
            "between", "among", "during", "before", "after", "above", "below", "beside", 
            "against", "along", "around", "toward", "into", "onto", "upon", "via"
        ]
        
        self.articles = ["the", "a", "an"]
        
        # Template patterns for title construction
        self.templates = [
            # Simple patterns
            lambda: f"{self._adj()} {self._noun()}",
            lambda: f"{self._adj()} {self._noun()} {self._noun()}",
            lambda: f"{self._noun()} {self._noun()}",
            lambda: f"{self._noun()} {self._prep()} {self._adj()} {self._noun()}",
            lambda: f"{self._noun()} {self._prep()} {self._article()} {self._noun()}",
            
            # With verbs
            lambda: f"{self._verb('ing')} {self._noun()}",
            lambda: f"{self._verb('ing')} {self._prep()} {self._article()} {self._adj()} {self._noun()}",
            lambda: f"{self._verb()} {self._article()} {self._noun()}",
            
            # Poetic structures
            lambda: f"{self._adj()} {self._adj()} {self._noun()}",
            lambda: f"{self._adj()} {self._noun()} {self._prep()} {self._noun()}",
            
            # Themed patterns
            lambda: f"{self._theme_pair('tech')}",
            lambda: f"{self._theme_pair('urban')}",
            lambda: f"{self._theme_pair('emotion')}",
            lambda: f"{self._theme_pair('cyberpunk')}",
            
            # Special formats
            lambda: f"{self._acronym()}",
            lambda: f"{self._numbered_title()}",
            lambda: f"{self._emoji_title()}",
            lambda: f"{self._vaporwave_spaced_title()}",
            lambda: f"{self._symbol_separated_title()}",
        ]
        
        # Formatting styles
        self.formatting_styles = [
            self._standard_case,
            self._title_case,
            self._lowercase_style,
            self._uppercase_style,
            self._vaporwave_spacing,
            self._replace_letters_with_symbols,
            self._alternating_case,
            self._camel_case,
            self._snake_case,
            self._no_vowels,
        ]
        
        # Symbols and special characters
        self.symbols = [".", "_", "-", ":", ";", "/", "\\", "|", "+", "*", "=", "&", "%", "#", "@", "!"]
        self.special_chars = ["★", "☆", "◆", "◇", "○", "●", "□", "■", "▲", "△", "▼", "▽", "✧", "✦", "♪", "♫", "☾", "☽", "♥", "♡"]
        self.emojis = ["🌌", "✨", "🔮", "💫", "🌙", "🌃", "🏙️", "🌆", "🌇", "🌉", "🌁", "🌊", "💿", "📀", "📻", "📡", "💾", "🖥️", "💎", "⚡"]
        
        # Load custom wordlists if available (for future extensibility)
        self._load_custom_wordlists()
    
    def _load_custom_wordlists(self):
        """Load additional words from custom files if available."""
        # This can be implemented to load from external files for extensibility
        pass
    
    # Word selection helpers
    def _noun(self, category: Optional[str] = None) -> str:
        """Get a random noun, optionally from a specific category."""
        if category and category in self.nouns:
            return random.choice(self.nouns[category])
        category = random.choice(list(self.nouns.keys()))
        return random.choice(self.nouns[category])
    
    def _adj(self, category: Optional[str] = None) -> str:
        """Get a random adjective, optionally from a specific category."""
        if category and category in self.adjectives:
            return random.choice(self.adjectives[category])
        category = random.choice(list(self.adjectives.keys()))
        return random.choice(self.adjectives[category])
    
    def _verb(self, form: str = "") -> str:
        """
        Get a random verb, optionally in a specific form.
        
        Args:
            form: Verb form to return ("ing" for gerund, "ed" for past tense, etc.)
        """
        category = random.choice(list(self.verbs.keys()))
        verb = random.choice(self.verbs[category])
        
        if form == "ing":
            # Handle basic conjugation for -ing form
            if verb.endswith("e"):
                return verb[:-1] + "ing"
            return verb + "ing"
        elif form == "ed":
            # Handle basic conjugation for past tense
            if verb.endswith("e"):
                return verb + "d"
            return verb + "ed"
        
        return verb
    
    def _prep(self) -> str:
        """Get a random preposition."""
        return random.choice(self.prepositions)
    
    def _article(self) -> str:
        """Get a random article."""
        return random.choice(self.articles)
    
    def _symbol(self) -> str:
        """Get a random symbol."""
        return random.choice(self.symbols)
    
    def _special_char(self) -> str:
        """Get a random special character."""
        return random.choice(self.special_chars)
    
    def _emoji(self) -> str:
        """Get a random emoji."""
        return random.choice(self.emojis)
    
    # Themed pattern helpers
    def _theme_pair(self, theme: str) -> str:
        """Create a themed adjective + noun pair."""
        if theme in self.adjectives and theme in self.nouns:
            adj = random.choice(self.adjectives[theme])
            noun = random.choice(self.nouns[theme])
            return f"{adj} {noun}"
        return f"{self._adj()} {self._noun()}"
    
    # Special title format helpers
    def _acronym(self) -> str:
        """Generate an acronym title (A.N.O.T.H.E.R. D.A.Y.)."""
        words = []
        length = random.randint(2, 5)
        
        for _ in range(length):
            noun_cat = random.choice(list(self.nouns.keys()))
            noun = random.choice(self.nouns[noun_cat]).upper()
            words.append(".".join(list(noun[0])) + ".")
        
        return " ".join(words)
    
    def _numbered_title(self) -> str:
        """Generate a title with a number (e.g., 'Sector 7', 'Tokyo-3')."""
        noun = self._noun()
        number = random.randint(1, 99)
        connector = random.choice(["", " ", "-", "_", "."])
        return f"{noun}{connector}{number}"
    
    def _emoji_title(self) -> str:
        """Generate a title with emojis."""
        title = f"{self._adj()} {self._noun()}"
        emoji1 = self._emoji()
        emoji2 = self._emoji()
        placement = random.choice(["prefix", "suffix", "both", "surround"])
        
        if placement == "prefix":
            return f"{emoji1} {title}"
        elif placement == "suffix":
            return f"{title} {emoji1}"
        elif placement == "both":
            return f"{emoji1} {title} {emoji2}"
        else:  # surround
            return f"{emoji1} {title} {emoji1}"
    
    def _vaporwave_spaced_title(self) -> str:
        """Generate a vaporwave-style spaced out title."""
        words = [self._adj(), self._noun()]
        return " ".join([" ".join(word) for word in words])
    
    def _symbol_separated_title(self) -> str:
        """Generate a title with symbols between words."""
        words = [self._adj(), self._noun()]
        symbol = self._symbol()
        return f" {symbol} ".join(words)
    
    # Text formatting style helpers
    def _standard_case(self, text: str) -> str:
        """Standard capitalization (first letter uppercase)."""
        if not text:
            return text
        return text[0].upper() + text[1:]
    
    def _title_case(self, text: str) -> str:
        """Title Case (Each Word Capitalized)."""
        return " ".join(word.capitalize() for word in text.split())
    
    def _lowercase_style(self, text: str) -> str:
        """all lowercase aesthetics."""
        return text.lower()
    
    def _uppercase_style(self, text: str) -> str:
        """ALL UPPERCASE STYLE."""
        return text.upper()
    
    def _vaporwave_spacing(self, text: str) -> str:
        """v a p o r w a v e  s p a c i n g."""
        return " ".join(text)
    
    def _replace_letters_with_symbols(self, text: str) -> str:
        """R3pl4c3 l3tt3rs w1th symb0ls."""
        replacements = {"a": "4", "e": "3", "i": "1", "o": "0", "s": "5", "t": "7"}
        result = ""
        for char in text:
            if char.lower() in replacements and random.random() < 0.7:  # 70% chance to replace
                result += replacements[char.lower()]
            else:
                result += char
        return result
    
    def _alternating_case(self, text: str) -> str:
        """AlTeRnAtInG cAsE."""
        result = ""
        for i, char in enumerate(text):
            if i % 2 == 0:
                result += char.upper()
            else:
                result += char.lower()
        return result
    
    def _camel_case(self, text: str) -> str:
        """camelCaseStyle."""
        words = text.split()
        if not words:
            return ""
        result = words[0].lower()
        for word in words[1:]:
            if word:
                result += word[0].upper() + word[1:].lower()
        return result
    
    def _snake_case(self, text: str) -> str:
        """snake_case_style."""
        return "_".join(text.lower().split())
    
    def _no_vowels(self, text: str) -> str:
        """Rmv vwls frm txt."""
        return re.sub(r'[aeiouAEIOU]', '', text)
    
    def generate_title(self, style_bias: Optional[str] = None) -> str:
        """
        Generate a song title with optional style bias.
        
        Args:
            style_bias: Optional bias towards a particular style
                        ("cyberpunk", "vaporwave", "minimal", "emotional", etc.)
        
        Returns:
            A generated song title
        """
        # Select a template based on style bias if provided
        if style_bias == "cyberpunk":
            template = random.choice([
                lambda: f"{self._adj('cyberpunk')} {self._noun('cyberpunk')}",
                lambda: f"{self._adj('cyberpunk')} {self._noun('tech')}",
                lambda: f"{self._noun('tech')} {self._prep()} {self._adj('cyberpunk')} {self._noun('urban')}"
            ])
        elif style_bias == "vaporwave":
            template = random.choice([
                lambda: self._vaporwave_spaced_title(),
                lambda: f"{self._adj('emotional')} {self._noun('abstract')}"
            ])
        elif style_bias == "minimal":
            template = random.choice([
                lambda: f"{self._noun()}",
                lambda: f"{self._adj()}",
                lambda: f"{self._verb('ing')}"
            ])
        elif style_bias == "emotional":
            template = random.choice([
                lambda: f"{self._adj('emotional')} {self._noun('emotion')}",
                lambda: f"{self._adj('emotional')} {self._noun('abstract')}"
            ])
        else:
            # Random selection from all templates
            template = random.choice(self.templates)
        
        # Generate base title
        base_title = template()
        
        # Apply formatting
        # Weighted selection based on style bias
        if style_bias == "vaporwave":
            format_funcs = [self._vaporwave_spacing, self._uppercase_style, self._alternating_case]
        elif style_bias == "cyberpunk":
            format_funcs = [self._replace_letters_with_symbols, self._snake_case, self._uppercase_style]
        else:
            # Random selection with preferences
            weights = [0.4, 0.2, 0.1, 0.05, 0.05, 0.05, 0.05, 0.05, 0.025, 0.025]  # Weights for each style
            format_funcs = random.choices(self.formatting_styles, weights=weights, k=1)[0]
        
        # Apply the chosen formatting
        if isinstance(format_funcs, list):
            formatting_func = random.choice(format_funcs)
        else:
            formatting_func = format_funcs
        
        formatted_title = formatting_func(base_title)
        
        # Sometimes add special decorators
        if random.random() < 0.2:  # 20% chance
            if random.random() < 0.5:
                formatted_title = f"{self._special_char()} {formatted_title} {self._special_char()}"
            else:
                formatted_title = f"{formatted_title} {self._special_char()}"
        
        return formatted_title


# Create singleton instance
title_generator = TitleGenerator()


if __name__ == "__main__":
    # Test generation
    print("Random titles:")
    for _ in range(10):
        print(title_generator.generate_title())
    
    print("\nCyberpunk style:")
    for _ in range(5):
        print(title_generator.generate_title("cyberpunk"))
    
    print("\nVaporwave style:")
    for _ in range(5):
        print(title_generator.generate_title("vaporwave")) 