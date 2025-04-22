"""
ProtoNomia settings module.
"""

# Default Language Model to use
DEFAULT_LM = "gemma3:1b"  # Can be changed to gemma:7b or other available Ollama models

# LLM API settings
OLLAMA_BASE_URL = "http://localhost:11434"
LLM_TIMEOUT = 30  # seconds
LLM_MAX_RETRIES = 3

# Simulation settings
DEFAULT_MAX_DAYS = 10
DEFAULT_POPULATION = 5
DEFAULT_RESOURCE_SCARCITY = 0.1  # How quickly resources deplete (0.1-1.0)

PERSONALITIES = [
    "Adventurous, curious and helpful",
    "Cautious, detail-oriented and reserved",
    "Friendly, enthusiastic and impulsive",
    "Analytical, resourceful and introspective",
    "Compassionate, creative and adaptable",
    "Ambitious, meticulous and persistent",
    "Easygoing, optimistic and sociable",
    "Innovative, independent and logical",
    "Patient, reliable and methodical",
    "Visionary, charismatic and determined"
]
