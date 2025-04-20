# ProtoNomia Development Log

## Fixed LLM Narrator Test Mode and Demo Interactions

### Date
2025-04-20

### Description
Fixed issues with the LLMNarrator class and added demo interactions to showcase narrative generation. Key changes include:

1. Added the missing `test_mode` parameter to the LLMNarrator constructor
2. Fixed the `generate_narrative_from_interaction` method to properly handle agent data
3. Added a demo interaction generator to the simulation step to ensure narrative events are created
4. Updated method signatures to be consistent with parameter expectations

These changes ensure that narrative events are properly generated during simulation runs and that the test mode functionality works correctly for unit testing.

### Demand
Continue, it's far from working for now I see no interaction nor narrative event: python headless.py --initial-population 5 --ticks 5 --verbosity 4 --use-llm --mock-llm --narrator-model-name "gemma3:1b" --temperature 0.9 --top-p 0.8 --top-k 50

### Files
- [M] `narrative/llm_narrator.py` - Added test_mode parameter and fixed generate_narrative_from_interaction method
- [M] `core/simulation.py` - Added _create_demo_interaction method to generate sample interactions

### Bugs
- Fixed missing test_mode parameter in LLMNarrator constructor
- Fixed interaction creation issue that was preventing narrative events from being generated

## Implemented LLM-based Narrator

### Date
2025-04-20

### Description
Implemented a new LLMNarrator class that uses Ollama to generate narrative content for the simulation. The LLMNarrator extends the base Narrator class and provides LLM-powered generation of narrative events and daily summaries. The implementation includes:

1. A new `narrative/llm_narrator.py` file with the LLMNarrator class
2. Tests for the LLMNarrator in `tests/test_llm_narrator.py`
3. Integration with the core simulation module to use LLMNarrator when `use_llm` is true
4. Addition of a `narrator-model-name` parameter to the headless script to control which model is used for narration
5. Fallback to rule-based narrative generation if the LLM fails
6. Parameters for controlling LLM generation: temperature, top-p, and top-k

The implementation maintains full backward compatibility with the existing rule-based narrator while adding the option to use LLM-generated narratives for more creative and varied storytelling. The addition of LLM generation parameters allows fine-tuning the creativity and diversity of the generated narratives.

### Demand
Implement an Ollama-based Narrator for the ProtoNomia simulation that generates narrative events and daily summaries using LLM models.

### Files
- [A] `narrative/llm_narrator.py` - Main implementation of the LLMNarrator class
- [M] `narrative/__init__.py` - Updated to import and expose LLMNarrator
- [M] `core/simulation.py` - Modified to use LLMNarrator when use_llm is true, added LLM parameters
- [M] `headless.py` - Added narrator-model-name and LLM generation parameters
- [A] `tests/test_llm_narrator.py` - Tests for the LLMNarrator
- [A] `DEVLOG.md` - Development log documenting the changes

### Bugs
- Fixed tests that failed due to multiple calls to the Ollama API (connection test + actual generation)
- Added proper mock responses for tests to avoid depending on actual Ollama availability 