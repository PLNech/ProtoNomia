# ProtoNomia API Documentation

## Overview

ProtoNomia provides a RESTful API for creating and managing Mars settlement simulations. The API allows you to create simulations, add and control agents, and observe the economic interactions within the simulated colony.

## Base URL

All API endpoints are relative to the base URL:

```
http://localhost:8000
```

## Authentication

Currently, the API does not require authentication. This may change in future versions.

## API Endpoints

### Simulation Endpoints

#### Start a Simulation

Creates a new simulation with specified parameters.

**Endpoint:** `POST /simulation/start`

**Request Body:**

```json
{
  "num_agents": 5,        // Number of agents to start with
  "max_days": 30,         // Maximum days to run the simulation
  "starting_credits": 100, // Optional: Starting credits for each agent
  "model_name": "gemma3:4b", // LLM model to use for agent reasoning
  "temperature": 0.7,     // Model temperature for creativity
  "output_dir": "output"  // Directory to store output files
}
```

**Response:**

```json
{
  "simulation_id": "b9d03d97-680e-4928-b71b-257cba4bd8fd",
  "num_agents": 5,
  "status": "created"
}
```

#### Get Simulation Details

Retrieves detailed information about a specific simulation.

**Endpoint:** `GET /simulation/detail/{simulation_id}`

**Parameters:**
- `simulation_id`: ID of the simulation to retrieve

**Response:**

```json
{
  "simulation_id": "b9d03d97-680e-4928-b71b-257cba4bd8fd",
  "state": {
    "day": 1,
    "agents": [...],
    "market": {...},
    "actions": [...],
    "inventions": {...},
    "songs": {...}
  }
}
```

#### Run Simulation

Advance the simulation by a specified number of days.

**Endpoint:** `POST /simulation/run/{simulation_id}`

**Parameters:**
- `simulation_id`: ID of the simulation to run
- `days` (query parameter, default: 1): Number of days to advance the simulation

**Response:**

```json
{
  "simulation_id": "b9d03d97-680e-4928-b71b-257cba4bd8fd",
  "days_processed": 1,
  "current_day": 2
}
```

#### Get Simulation Status

Retrieves information about the current status of a specific simulation.

**Endpoint:** `GET /simulation/status/{simulation_id}`

**Parameters:**
- `simulation_id`: ID of the simulation to retrieve status

**Response:**

```json
{
  "simulation_id": "d102106e-bc18-41ec-9aee-b803d787131b",
  "day": 5,
  "agents_count": 4,
  "dead_agents_count": 0,
  "market_listings_count": 2,
  "inventions_count": 3,
  "ideas_count": 2,
  "songs_count": 1,
  "current_stage": "agent_day",
  "current_agent_id": "550e8400-e29b-41d4-a716-446655440000",
  "current_agent_name": "Dr. Nebula Martin Alpha",
  "night_activities_today": 0
}
```

### Simulation Stages

The `current_stage` field can have the following values:

- `initialization`: Setting up the simulation environment
- `agent_day`: Processing day actions for agents one at a time
- `narrator`: Generating the narrative for the day
- `agent_night`: Processing night activities for agents one at a time

When the simulation is in the `agent_day` or `agent_night` stage, the `current_agent_id` and `current_agent_name` fields indicate which agent is currently being processed.

### Night Activities Information

The `night_activities_today` field indicates how many agents have completed their night activities for the current day.

Night activities are automatically processed during the simulation run and include:

- Dinner (food consumption)
- Music listening
- Social interactions (chat)

Detailed night activity information can be found in the simulation detail endpoint:

```
GET /simulation/detail/{simulation_id}
```

The response includes a `night_activities` field containing a list of night activities for each day.

### Agent Endpoints

#### Add an Agent

Adds a new agent to an existing simulation.

**Endpoint:** `POST /agent/add`

**Request Body:**

```json
{
  "simulation_id": "b9d03d97-680e-4928-b71b-257cba4bd8fd",
  "name": "Councilor Zhang Wei",      // Optional: Name will be generated if not provided
  "personality": "inventive, curious", // Optional: Personality traits
  "starting_credits": 200             // Optional: Starting credits
}
```

**Response:**

```json
{
  "agent_id": "agent_6",
  "name": "Councilor Zhang Wei",
  "simulation_id": "b9d03d97-680e-4928-b71b-257cba4bd8fd"
}
```

#### Get Agent Status

Retrieves information about a specific agent.

**Endpoint:** `GET /agent/status`

**Query Parameters:**
- `simulation_id`: ID of the simulation
- `agent_id`: ID of the agent (either agent_id or agent_name must be provided)
- `agent_name`: Name of the agent (either agent_id or agent_name must be provided)

**Response:**

```json
{
  "id": "agent_1",
  "name": "Councilor Zhang Wei",
  "credits": 150.0,
  "needs": {
    "food": 0.8,
    "rest": 0.6,
    "fun": 0.7
  },
  "goods": [...],
  "is_alive": true
}
```

#### Update an Agent

Updates properties of an existing agent.

**Endpoint:** `PUT /agent/update`

**Request Body:**

```json
{
  "simulation_id": "b9d03d97-680e-4928-b71b-257cba4bd8fd",
  "agent_id": "agent_1",
  "updates": {
    "credits": 300,
    "needs": {
      "food": 1.0
    }
  }
}
```

**Response:**

```json
{
  "agent_id": "agent_1",
  "name": "Councilor Zhang Wei",
  "updated": ["credits", "needs.food"]
}
```

#### Kill an Agent

Removes an agent from the simulation.

**Endpoint:** `DELETE /agent/kill`

**Query Parameters:**
- `simulation_id`: ID of the simulation
- `agent_id`: ID of the agent (either agent_id or agent_name must be provided)
- `agent_name`: Name of the agent (either agent_id or agent_name must be provided)

**Response:**

```json
{
  "success": true,
  "agent_id": "agent_1",
  "agent_name": "Councilor Zhang Wei"
}
```

## Data Models

### Agent

```json
{
  "id": "agent_1",
  "name": "Councilor Zhang Wei",
  "age_days": 2,
  "death_day": null,
  "is_alive": true,
  "personality": {
    "text": "inventive [openness-high], systematic [conscientiousness-high], quiet [extraversion-low], empathetic [agreeableness-high], steady [neuroticism-low], humorous, tech-savvy, minimalist"
  },
  "credits": 150.0,
  "needs": {
    "food": 0.8,
    "rest": 0.6,
    "fun": 0.7
  },
  "goods": [
    {
      "type": "FOOD",
      "quality": 0.5,
      "name": "Martian Mushrooms"
    }
  ],
  "history": []
}
```

### Good

```json
{
  "type": "FOOD", // One of: FOOD, REST, FUN
  "quality": 0.75, // 0.0-1.0 scale
  "name": "Martian Mushrooms"
}
```

### Market Listing

```json
{
  "id": "listing_1",
  "seller_id": "agent_1",
  "good": {
    "type": "FOOD",
    "quality": 0.75,
    "name": "Martian Mushrooms"
  },
  "price": 50.0,
  "listed_on_day": 1
}
```

### Action

```json
{
  "agent_id": "agent_1",
  "type": "CRAFT", // One of: REST, WORK, BUY, SELL, HARVEST, CRAFT, THINK, COMPOSE
  "extras": {
    "goodType": "FOOD",
    "name": "Synthetic Protein Bars",
    "materials": 50
  },
  "reasoning": "I need to create food to sell for profit.",
  "day": 2
}
```

## Client Code Generation

You can generate client code libraries for your preferred programming language using OpenAPI tools.

### Using OpenAPI Generator

1. First, get the OpenAPI specification from the `/openapi.json` endpoint.
2. Then use the OpenAPI Generator:

```bash
# Install the generator
npm install @openapitools/openapi-generator-cli -g

# Generate a Python client
openapi-generator-cli generate -i http://localhost:8000/openapi.json -g python -o ./python-client

# Generate a JavaScript client
openapi-generator-cli generate -i http://localhost:8000/openapi.json -g javascript -o ./js-client
```

### Supported Languages

OpenAPI Generator supports many languages including:
- Python
- JavaScript/TypeScript
- Java
- C#
- Go
- Rust
- Ruby
- And many more

## Error Handling

The API uses standard HTTP status codes to indicate success or failure:

- `200 OK`: The request was successful
- `400 Bad Request`: The request was invalid
- `404 Not Found`: The resource was not found
- `500 Internal Server Error`: An error occurred on the server

Error responses will include a detail message:

```json
{
  "detail": "Agent not found with ID agent_100"
}
```

## Rate Limiting

Currently, the API does not implement rate limiting. This may change in future versions.

## Versioning

The current API version is v1.0.0. The API version is included in the response of the `/` endpoint.

## Further Resources

- [ProtoNomia GitHub Repository](https://github.com/yourusername/protonomia)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic Documentation](https://docs.pydantic.dev/) 