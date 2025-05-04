# Development Log

# FastAPI Dependency Injection Pattern - 2025-05-04

## Description

Refactored the ProtoNomia API to use proper FastAPI dependency injection pattern:

1. Fixed API Module Imports:
   - Updated `main.py` to correctly import the API module using the full path `src.api:app`
   - Fixed import circular dependencies in the API module

2. Implemented Proper Dependency Injection:
   - Created a new `dependencies.py` module with proper dependency injection pattern
   - Added `get_simulation_manager()` dependency function to provide the simulation manager
   - Updated all routes to use dependency injection instead of direct imports

3. Fixed SimulationManager Implementation:
   - Added missing `deepcopy` import to fix runtime errors
   - Improved type hints for the simulation manager
   - Ensured proper singleton implementation

4. Enhanced API Server:
   - Updated routing to use dependency injection across all endpoints
   - Added proper error handling and graceful shutdown
   - Added missing save/load simulation endpoints

## Demand

Fix this error when I run our simulation:
```
ERROR: Error loading ASGI app. Could not import module "api".
```
Provide the manager as a dependency proper @FastAPI way.

## Files

- [M] main.py - Fixed API module import and simulation manager handling
- [A] src/api/dependencies.py - Added proper dependency injection
- [M] src/api/simulation_manager.py - Fixed missing deepcopy import and improved implementation
- [M] src/api/routes/simulation.py - Updated to use dependency injection
- [M] src/api/routes/agent.py - Updated to use dependency injection
- [M] DEVLOG.md - Added this entry

## Bugs

- Fixed "Could not import module 'api'" error by using the correct module path
- Fixed AttributeError in simulation_manager by implementing proper dependency injection
- Fixed missing deepcopy import causing runtime errors
- Ensured proper singleton implementation of the simulation manager

# Letter System for Night Activities - 2025-05-20

## Description

Enhanced the night activities system by replacing the simple chat mechanism with a structured letter system for agent communications:

1. Implemented Letter Model:
   - Added a new `Letter` model with recipient_name, title, and message fields
   - Updated NightActivity to use a list of Letter objects instead of separate chat_recipients and chat_message
   - Enhanced NightActionResponse to use the new Letter model for night activity generation

2. Modified Agent Night Interactions:
   - Agents now write personalized letters to other agents
   - Each letter has a specific recipient, title, and message content
   - Multiple letters can be sent to different recipients
   - Letters provide more structured social interactions between agents

3. Updated the Engine:
   - Modified _process_agent_night_activities to generate letters
   - Fixed a syntax error in agent.py format_prompt function
   - Enhanced night activity logging to show letter details

4. Added Testing:
   - Created test_letter_creation method in TestNightActivities
   - Enhanced existing night activities tests to use the letter model
   - Added verification that letter recipients exist

## Demand

Night response should be not separately chat recipients and chat message, but rather an optional list of letters: a Letter being recipient_name: str and title:str and message:str all required.

## Files

- [M] models/simulation.py - Added Letter model and updated NightActivity and NightActionResponse models
- [M] models/__init__.py - Added Letter to imports and __all__
- [M] engine/simulation.py - Updated _process_agent_night_activities to use letter model
- [M] src/agent.py - Fixed syntax error in format_prompt
- [M] tests/unit/test_simulation_stage.py - Added test_letter_creation method
- [M] docs/simulation_stages.md - Updated social interaction section to reflect letter system
- [M] DEVLOG.md - Added this entry

## Bugs

- Fixed unterminated string literal in agent.py's format_prompt function
- Updated night activity processing to correctly handle the new letter structure
- Ensured backward compatibility with existing code that might expect chat data

# Simulation Stages and Night Activities - 2025-05-04

## Description

Enhanced the ProtoNomia simulation with the concept of simulation stages and added a new night phase with social activities:

1. Added Simulation Stages:
   - INITIALIZATION: Initial setup of the simulation
   - AGENT_DAY: Processing day actions for agents (one at a time)
   - NARRATOR: Generating the narrative for the day
   - AGENT_NIGHT: Processing night activities for agents (one at a time)

2. Enhanced API to expose stage information:
   - Modified simulation status endpoints to include stage information
   - Added current agent tracking in simulation state
   - Enhanced status response with detailed stage metadata
   - Unified processing flow across all endpoints

3. Implemented Night Activities:
   - Added dinner logic - agents consume FOOD items in descending quality order
   - Implemented song listening - agents choose songs to listen to
   - Added agent chat system - agents chat with 1-3 others
   - Created NightActivity model to track all night events

4. Updated Headless Frontend:
   - Enhanced frontend to display current simulation stage
   - Added visualization of waiting state and current agent
   - Implemented display of night activities
   - Added dinner/food consumption visualization

## Demand

API should return Stage in status of the current simulation. Add that concept as a new class in the models. Stage can be: Initialization (creation of world), AgentDay (waiting for a specific agent's action), AgentNight (waiting for an agent's night choices), and Narrator (waiting for narrator). And you can see which agent we're waiting for.

In headless script, show "processing day x... waiting for agent x action... agent X chose Work ... consequences now waiting for agent y action... etc."

Add night as a separate stage of the simulation. Each agent must choose:
- 1 song to listen to
- Name of 1-3 persons to chat to (max based on existing other people in simulation)
- Short message to send

Also, add 'dinner' in that step: if any FOOD item ordered decreasing could be eaten (add its quality to food without going over 1.00), eat it, then check food again until not hungry or no adequate food.

## Files

- [M] models/simulation.py - Added SimulationStage enum and NightActivity model
- [M] engine/simulation.py - Implemented stage-based simulation and night phase
- [M] api/models.py - Enhanced SimulationStatusResponse with stage information
- [M] api/routes/simulation.py - Updated endpoints to include stage information
- [M] frontends/headless.py - Added stage display and night activities visualization
- [A] docs/dev_plan_stage_and_night.md - Created development plan
- [M] DEVLOG.md - Added this entry

## Bugs

- Fixed agent action handling when day actions are processed one at a time
- Fixed night activities tracking and display
- Ensured proper stage transitions throughout the simulation
- Enhanced error handling when processing agent actions
- Fixed food consumption logic during dinner phase 