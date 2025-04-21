# ProtoNomia Documentation

ProtoNomia is a multi-agent economic simulation set in a Mars colony in the year 2993, designed to assess, illustrate, and benchmark various economic theory principles.

## Architecture

The codebase is organized into several key modules:

- **models**: Core data models for the simulation
- **core**: Main simulation engine
- **agents**: Agent implementation and decision making
- **economics**: Economic interaction handlers
- **population**: Population controller for agent lifecycle
- **narrative**: Narrative generation

## Key Components

### Simulation

The `Simulation` class in `core/simulation.py` is the central controller for the simulation. It:
- Manages agents and their lifecycle
- Coordinates economic interactions
- Generates narrative events
- Tracks economic indicators

### Agents

Agents can use either rule-based or LLM-based decision making:
- `LLMAgent` uses Ollama to generate agent decisions based on their context
- Rule-based decisions are made directly in the Simulation class

### Economic Interactions

The simulation implements several game theory interactions:
- Ultimatum Game: Tests fairness and strategic decision making
- Trust Game: Tests trust and reciprocity
- Public Goods Game: Tests cooperation in collective action problems

Each interaction is handled by a dedicated handler class in `economics/interactions/`.

### Narrative Generation

The simulation can generate narrative descriptions of events:
- `Narrator`: Basic rule-based narrator
- `LLMNarrator`: LLM-powered narrator that generates more creative narratives

## Running the Simulation

### Prerequisites

- Python 3.10+
- Required libraries (install with `pip install -r requirements.txt`)
- Ollama service running (for LLM functionality)

### Headless Mode

Run the simulation in headless (non-interactive) mode:

```bash
python headless.py --ticks 100 --initial-population 20
```

#### Key Parameters

- `--use-llm`: Enable LLM-based agent and narrative generation
- `--model-name`: LLM model for agent decisions (default: gemma3:1b)
- `--narrator-model-name`: LLM model for narration (default: gemma3:1b)
- `--initial-population`: Initial population size (default: 20)
- `--ticks`: Number of simulation steps (default: 100)
- `--interactions`: Economic interaction types to enable

### Without LLM Integration

The simulation can run with rule-based agents and narration:

```bash
python headless.py --ticks 100
```

### With LLM Integration

To use LLM-based agents and narration, ensure Ollama is running:

```bash
python headless.py --ticks 100 --use-llm --model-name gemma3:1b
```

## Testing

### Unit Tests

Run tests that don't require LLM integration:

```bash
pytest tests/unit/
```

### LLM Integration Tests

Run tests that require LLM integration (Ollama must be running):

```bash
RUN_LLM_TESTS=1 pytest tests/llm/
```

### All Tests

Run all tests, including LLM integration if enabled:

```bash
RUN_LLM_TESTS=1 pytest
``` 