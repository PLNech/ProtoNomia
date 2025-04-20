# ProtoNomia: Cyberpunk Mars Economic Simulation

ProtoNomia is an economic game theory simulation set in a cyberpunk Mars colony in the year 2993. The project combines multi-agent reinforcement learning with narrative generation to create an engaging simulation of economic interactions.

![ProtoNomia Dashboard](readme_assets/dashboard.png)

## Overview

ProtoNomia simulates a Mars colony with various economic agents (individuals, corporations, collectives) that interact through classic economic games such as the Ultimatum Game, Trust Game, and Public Goods Game. Each agent is powered by an LLM (Large Language Model) to make decisions based on their personality, resources, and social context.

Key features:
- Agent-based simulation with LLM-powered decision-making
- Implementation of multiple economic game theory interactions
- Realistic agent lifecycle (birth, aging, death) with population dynamics
- Narrative generation from agent interactions
- Real-time visualization and analytics
- Cyberpunk Mars setting for an engaging narrative context

## Project Structure

```
protonomia/
├── core/                    # Simulation engine
├── models/                  # Data models
├── agents/                  # Agent implementation
├── economics/               # Economic interactions
├── narrative/               # Narrative generation
├── population/              # Population dynamics
├── api/                     # API endpoints
└── frontend/                # Next.js frontend
```

## Setup Instructions

### Prerequisites

- Python 3.9+
- Node.js 18+
- Ollama (for running local LLMs)

### Backend Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/protonomia.git
   cd protonomia
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up Ollama with the required models:
   ```bash
   # Install Ollama from https://ollama.ai
   ollama pull gemma:1b  # or any other model you want to use
   ```

5. Start the backend API server:
   ```bash
   cd api
   uvicorn main:app --reload
   ```

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend/protonomia-ui
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm run dev
   ```

4. Access the application at http://localhost:3000

## Using the Simulation

1. Start a new simulation from the homepage
2. Configure parameters like population size, resource scarcity, etc.
3. Watch the simulation unfold on the dashboard
4. Explore agent details, economic data, and narrative events

## Implemented Economic Interactions

ProtoNomia implements the following economic games:

1. **Ultimatum Game**: Tests fairness norms and bargaining behavior
2. **Trust Game**: Measures trust and reciprocity between agents
3. **Public Goods Game**: Examines cooperation and free-riding in public resource contributions

Additional games marked as TODOs for future implementation:
- Cournot Competition
- Bertrand Competition
- Principal-Agent Contracts
- And more...

## LLM Integration

ProtoNomia uses local LLMs via Ollama to power agent decision-making and narrative generation. The system supports:

- Agent decision-making through structured prompts
- Narrative generation for events and stories
- Background generation for agent personalities

Customize models by changing the configuration at startup.

## Development

### Adding New Economic Interactions

To add a new economic interaction:

1. Create a new interaction handler in `economics/interactions/`
2. Register the handler in `InteractionRegistry`
3. Update the agent controller to handle the new interaction type

### Extending Agent Capabilities

To enhance agent capabilities:

1. Update the `Agent` model in `models/base.py`
2. Extend the agent controller prompt in `agents/llm_agent.py`
3. Update the agent state preparation logic

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Based on research from experimental economics literature
- Inspired by agent-based modeling approaches
- Cyberpunk Mars setting influenced by various science fiction works

## TODO

- [ ] Implement additional economic interactions
- [ ] Add more sophisticated population dynamics
- [ ] Enhance narrative generation with story arcs
- [ ] Implement agent learning over time
- [ ] Add coalition formation mechanics
- [ ] Improve visualization with network graphs
- [ ] Implement replay and history mechanics