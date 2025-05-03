# Development Plan: Simulation Stages and Night Phase

## Overview
Add a new concept of "Stage" to the simulation to track the current state, and implement a night phase where agents can listen to music, chat with others, and have dinner.

## Tasks

### 1. Add Stage Model
- [x] Create a new `SimulationStage` enum in models/simulation.py
- [x] Define stages: INITIALIZATION, AGENT_DAY, AGENT_NIGHT, NARRATOR
- [x] Update `SimulationState` to include:
  - [x] current_stage field
  - [x] current_agent_id field (the agent we're waiting for action)
  - [x] awaiting_action field (what type of action we're waiting for)

### 2. Add Night Activities Models
- [x] Create `NightActivity` model with:
  - [x] song_choice (reference to existing song)
  - [x] chat_recipients (list of agent IDs)
  - [x] chat_message (message content)
- [x] Add storage for night activities in SimulationState
- [x] Modify Agent model to track food consumption/dinner

### 3. Update Simulation Engine
- [x] Modify `process_day` to handle different stages
- [x] Implement `process_night` method
- [x] Implement dinner logic (consuming FOOD items)
- [x] Add night activity generation/processing
- [x] Update the main simulation loop to include night phase

### 4. Update API
- [x] Modify simulation status endpoint to include stage information
- [x] Add new endpoint for night actions
- [x] Update simulation next/run endpoint to handle stages

### 5. Update Headless Frontend
- [x] Enhance frontend to display current stage
- [x] Add display for agent night activities
- [x] Update status indicators to show waiting state
- [x] Display dinner/food consumption

### 6. Update Scribe
- [x] Add methods to display night activities
- [x] Add visualization for dinner/food consumption
- [x] Enhance narrative to include night events

### 7. Testing
- [x] Update existing tests to account for stages
- [x] Add tests for night activities
- [x] Test stage transitions

### 8. Documentation
- [x] Update DEVLOG with changes
- [x] Update README with new simulation features
- [x] Document new API endpoints

## Implementation Notes
- The stage progression should be: INITIALIZATION → AGENT_DAY (for each agent) → NARRATOR → AGENT_NIGHT (for each agent) → next day
- The night phase should happen after the narrator summarizes the day
- Agent dinner logic: process food items in decreasing quality order until agent's food need is satisfied (max 1.0)
- Night activities should be mandatory for all agents 