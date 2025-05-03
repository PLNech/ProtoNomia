# ProtoNomia 🌃🏢🪐🪙🫧

Mars colony economic simulation with LLM-powered agents.

----
![image](https://github.com/user-attachments/assets/097827eb-556b-46b2-bfb7-5d81198f64a1)
_Cosmo inventing a new moss-based statue while Zara created a relatively tastier Nutrient Paste._

![image](https://github.com/user-attachments/assets/f645f1b6-f686-4ab6-88e6-d4432d0e6624)
_Birth of a Market_

----

## Features

- Agent-based economic simulation set on Mars
- LLM-powered decision making and narrative generation
- Rich colored terminal output for immersive experience
- RESTful API for programmatic access to simulations
- Interactive UI with real-time visualization
- Fully configurable simulation parameters
- Stage-based simulation with day and night cycles
- Agent night activities including dinner, music, and social interaction

## Installation

1. Clone the repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Make sure you have Ollama installed and running locally

## Usage

### CLI Mode (Original)

Run a simulation with default parameters:

```bash
python main.py
```

Customize your simulation:

```bash
python main.py --agents 10 --days 50 --model gemma3:1b --log-level WARNING
```

### API Server Mode

Run the API server:

```bash
python -m api.main
```

The API server will start at http://127.0.0.1:8000 with a cyberpunk-themed Swagger UI available at http://127.0.0.1:8000/docs.

### Headless Frontend (API Client)

Run a simulation using the API:

```bash
PYTHONPATH=`pwd` python frontends/headless.py --agents 5 --days 30 --model gemma3:4b
```

### Gradio Frontend (Data Visualization)

Launch the interactive Gradio dashboard:

```bash
PYTHONPATH=`pwd` python frontends/gradio.py
```

This will open a browser window with real-time visualization of simulation metrics.

## Command Line Options

### Main CLI

- `--agents`: Number of agents in the simulation (default: 5)
- `--days`: Number of days to run the simulation (default: 30)
- `--credits`: Starting credits for each agent (default: random)
- `--model`: LLM model to use (default: gemma3:1b)
- `--output`: Output directory (default: output/)
- `--temperature`: LLM temperature (default: 0.7)
- `--log-level`: Logging level (default: INFO)

### Headless Frontend

- `--agents`: Number of agents in the simulation (default: 5)
- `--days`: Number of days to run the simulation (default: 30)
- `--credits`: Starting credits for each agent (default: random)
- `--model`: LLM model to use (default: gemma3:4b)
- `--api-url`: URL of the API server (default: http://127.0.0.1:8000)
- `--log-level`: Logging level (default: INFO)

### Gradio Frontend

- `--api-url`: URL of the API server (default: http://127.0.0.1:8000)
- `--log-level`: Logging level (default: INFO)
- `--share`: Create a public share link (default: false)

## Rich Terminal Output

ProtoNomia features immersive cyberpunk-themed colored output in your terminal:

- Agent names in Neon Pink
- Credits in Neon Green
- Actions in Neon Orange
- Goods in Neon Blue
- Needs (rest/fun/food) in Neon Purple

To enjoy the full visual experience, run with warning or error log level:

```bash
python main.py --log-level WARNING
```

## API Documentation

ProtoNomia provides a RESTful API for programmatic access to simulations.

### Key Endpoints

- `POST /simulation/start`: Create a new simulation
- `GET /simulation/detail/{simulation_id}`: Get details of a simulation
- `POST /simulation/run/{simulation_id}`: Run a simulation for a day
- `POST /agent/add`: Add a new agent to a simulation
- `GET /agent/status`: Get an agent's status
- `PUT /agent/update`: Update an agent's properties
- `DELETE /agent/kill`: Remove an agent from a simulation

For complete API documentation:
- Swagger UI: http://127.0.0.1:8000/docs
- OpenAPI Schema: http://127.0.0.1:8000/openapi.json
- Detailed Docs: [docs/api.md](docs/api.md)

### Client Code Generation

You can generate client libraries for the API using OpenAPI tools:

```bash
npm install @openapitools/openapi-generator-cli -g

# Generate a Python client
openapi-generator-cli generate -i http://localhost:8000/openapi.json -g python -o ./python-client

# Generate a JavaScript client
openapi-generator-cli generate -i http://localhost:8000/openapi.json -g javascript -o ./js-client
```

## Data Visualization

The Gradio dashboard provides real-time visualization of:

- **Overview**: Population, economy, actions, creative output
- **Agents**: Individual needs, credits, goods, actions
- **Market**: Listings by type, quality distribution
- **Creations**: Inventions and songs
- **Narrative**: Daily story and word cloud of themes
- **Thoughts**: Agent thought analysis

## Testing

Run the tests:

```bash
PYTHONPATH=`pwd` pytest tests/
```

Run API-specific tests:

```bash
PYTHONPATH=`pwd` pytest tests/api/
```

Run frontend tests:

```bash
PYTHONPATH=`pwd` pytest tests/frontends/
```

## Architecture

ProtoNomia follows a clean architecture with:

- **Models**: Core domain models in `models/`
- **Engine**: Simulation engine in `engine/`
- **API**: RESTful API in `api/`
- **Frontends**: User interfaces in `frontends/`
- **Tests**: Comprehensive test suite in `tests/`

## Simulation Stages

ProtoNomia now uses a stage-based approach to track the simulation status:

1. **Initialization**: Setting up the simulation environment
2. **Agent Day**: Processing each agent's day actions one by one
3. **Narrator**: Generating a narrative for the day's events
4. **Agent Night**: Processing night activities for each agent

The API exposes the current stage and active agent in the status endpoint. The headless frontend displays detailed stage information during simulation runs.

For detailed documentation on simulation stages, see [docs/simulation_stages.md](docs/simulation_stages.md).

## Night Activities

Agents now participate in night activities after their day actions:

- **Dinner**: Consuming food items in quality order to satisfy hunger
- **Music**: Listening to songs created by other agents
- **Social**: Chatting with 1-3 other agents with conversation topics

Night activities impact agent needs and create more interesting social dynamics in the simulation.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
