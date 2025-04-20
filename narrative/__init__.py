"""Narrative generation module for ProtoNomia"""

from narrative.narrator import Narrator
try:
    from narrative.llm_narrator import LLMNarrator
    HAS_LLM_NARRATOR = True
except ImportError:
    HAS_LLM_NARRATOR = False

__all__ = ['Narrator']
if HAS_LLM_NARRATOR:
    __all__.append('LLMNarrator') 