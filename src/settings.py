"""
ProtoNomia settings module.
"""

# Default Language Model to use
DEFAULT_LM = "gemma3:4b"  # Can be changed to gemma:7b or other available Ollama models

# LLM API settings
OLLAMA_BASE_URL = "http://localhost:11434"
LLM_TIMEOUT = 30  # seconds
LLM_MAX_RETRIES = 10
