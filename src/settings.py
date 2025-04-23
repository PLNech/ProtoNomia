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
