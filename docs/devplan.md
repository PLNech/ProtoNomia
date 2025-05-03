# ProtoNomia Development Plan: API + Frontend Implementation

## Overview
Convert the existing ProtoNomia simulation into a headless engine with a FastAPI REST API and separate frontend(s).

## Project Structure Changes
```
protonomia/
├── api/
│   ├── __init__.py
│   ├── main.py          # FastAPI app entry point
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── simulation.py # Simulation endpoints
│   │   └── agent.py     # Agent endpoints
│   └── models.py        # API-specific Pydantic models
├── engine/
│   ├── __init__.py
│   ├── simulation.py    # Refactored simulation engine (headless)
│   └── state.py         # State management
├── models/
│   ├── __init__.py
│   ├── agent.py         # Agent models moved from src/models
│   └── simulation.py    # Simulation models moved from src/models
├── src/                  # Original code (to be refactored)
├── frontends/
│   ├── headless.py      # CLI frontend using API
│   └── web/             # Future web frontend
├── tests/
│   ├── unit/            # Existing unit tests
│   ├── api/             # New API tests
│   │   ├── __init__.py
│   │   ├── test_simulation_routes.py
│   │   └── test_agent_routes.py
│   └── ...
└── main.py              # New entry point that runs API server
```

## Detailed Implementation Steps

### 1. Initial Setup
- [x] Create development plan (this document)
- [ ] Create the new folder structure
- [ ] Modify imports in existing files as needed

### 2. Model Refactoring
- [ ] Move and refactor Pydantic models from src/models.py to models/
- [ ] Ensure backward compatibility for existing code
- [ ] Create new API-specific models in api/models.py

### 3. Simulation Engine Refactoring
- [ ] Refactor simulation.py to be a headless engine
- [ ] Extract UI/output logic from simulation to separate scribe
- [ ] Ensure simulation can run without UI dependencies

### 4. FastAPI Implementation
- [ ] Create FastAPI app in api/main.py
- [ ] Implement simulation routes
  - [ ] POST /simulation/start - Start new simulation
  - [ ] GET /simulation/status - Get current status
- [ ] Implement agent routes
  - [ ] POST /agent/add - Add new agent
  - [ ] DELETE /agent/kill - Kill an agent
  - [ ] GET /agent/status - Get agent status
  - [ ] PUT /agent/update - Update agent

### 5. Headless Frontend Implementation
- [ ] Create frontends/headless.py that:
  - [ ] Uses API to start simulation
  - [ ] Polls status and outputs exactly like current CLI
  - [ ] Matches output in example-run.txt

### 6. Testing
- [ ] Create FastAPI test fixtures
- [ ] Implement API endpoint tests
- [ ] Ensure existing tests still pass
- [ ] Update any broken tests

### 7. Documentation
- [ ] Update README with new architecture
- [ ] Document API endpoints using FastAPI docs
- [ ] Add examples of using the API

## API Endpoints Specification

### Simulation Endpoints

#### POST /simulation/start
- Parameters:
  - num_agents: int
  - max_days: int
  - starting_credits: Optional[int]
  - model_name: str
  - temperature: float
  - output_dir: str
- Returns:
  - simulation_id: str
  - status: str

#### GET /simulation/status
- Parameters:
  - simulation_id: str
- Returns:
  - Complete simulation state including:
    - day: int
    - agents: list of agents
    - market: market state
    - history: previous days
    - inventions, thoughts, music, etc.

### Agent Endpoints

#### POST /agent/add
- Parameters:
  - simulation_id: str
  - agent_data: Agent model
- Returns:
  - agent_id: str
  - status: str

#### DELETE /agent/kill
- Parameters:
  - simulation_id: str
  - agent_id: str or agent_name: str
- Returns:
  - status: str
  - message: str

#### GET /agent/status
- Parameters:
  - simulation_id: str
  - agent_id: str or agent_name: str
- Returns:
  - Complete agent state
  - History of actions, thoughts, inventions

#### PUT /agent/update
- Parameters:
  - simulation_id: str
  - agent_id: str
  - updates: partial Agent model
- Returns:
  - updated: bool
  - agent: updated Agent model

## Implementation Notes
- Use Pydantic for all data validation and serialization
- Implement proper error handling with appropriate HTTP status codes
- Ensure API is RESTful with consistent behavior
- Make API extensible for future types of goods/actions/needs
- Document all endpoints with OpenAPI (Swagger) 