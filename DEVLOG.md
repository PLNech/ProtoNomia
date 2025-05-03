# Development Log

## Cyberpunk Rich Terminal Output Integration - 2025-04-23

### Description
Integrated the Rich library to provide colorful, cyberpunk-styled terminal output. Created a dedicated `Scribe` class to handle all user-facing output formatting with consistent color schemes. The implementation separates debugging logs from narrative/UI logs, enhancing the user experience while maintaining proper logging for debugging purposes.

All agent activities, narratives, and simulation events now render with appropriate colorization:
- Agent names in Neon Pink
- Credits in Neon Green
- Actions in Neon Orange
- Goods in Neon Blue
- Needs (rest/fun/food) in Neon Purple

The UI also includes box drawing characters and emoji indicators to create an immersive Mars colony simulation experience.

### Demand
Let's do a sprint to add rich rendering with colored output to our simulation runs. See these docs: @https://rich.readthedocs.io/en/latest/introduction.html#quick-start  @https://rich.readthedocs.io/en/latest/text.html. The goal is that when we run the simulation with low log-level (WARNING or ERROR only), we see those rich prints that help the user see what the agents do and render any markdown in the narrator summaries.

We want the console user experience to be richer and colored, using cyberpunk neon-like colors to highlight consistently:
- agent names in Neon Pink
- credits in Neon Green
- Actions in Neon Orange
- Goods in Neon Blue
- Needs (rest/fun/food) in Neon Purple

### Files
- [A] src/scribe.py - New component with color definitions and all formatting utilities
- [M] src/simulation.py - Updated to use Scribe for user-facing outputs
- [A] requirements.txt - Added Rich library dependency
- [A] README.md - Added documentation for Rich terminal features
- [A] DEVLOG.md - Created development log

### Bugs
None observed during implementation 

# Frontend Enhancements - 2025-05-03

## Description
Enhanced the ProtoNomia frontend ecosystem with three major improvements:
1. Fixed loader indicators in the headless frontend to match server logs
2. Added OpenAPI documentation with a cyberpunk-themed Swagger UI
3. Created a Gradio-based frontend with real-time simulation metrics visualization

These changes improve the developer experience when using the API and provide richer data visualization options for simulation monitoring.

## Demand
> I see loader in the server logs not in the frontend logs it should be both
> Add and document how to use basic OpenAPI with customized dark mode cyberpunk style swagger UI + readme integration + howto api client generation
> Add a GradIO frontend as @headless.py alternative. leveraging the APIs to show real-time graphs of the simulation: people alive, total inventions, songs/genres/bpms, etc leverage @models.py while being generic and defensive to future-proof breaking changes of models. Abstract both frontends to implement a base class, so we can make changes together and ensure feature parity of these and eventual future other ones.
> Don't hesitate to improve the API, if that makes it more adequate for advanted real-time graphing frontend UIs.
> Make it elegant, modern design with affordant and ergonomic UI.
> Make it data love, nerd graph amateur style, we wanna drown in metadata <3
> add tests as needed to make this robust

## Files
- [M] requirements.txt - Added Gradio, Plotly, and other visualization dependencies
- [A] frontends/frontend_base.py - Created base frontend class
- [M] frontends/headless.py - Updated to inherit from FrontendBase
- [A] frontends/gradio.py - Created Gradio-based frontend with real-time visualization
- [M] api/main.py - Enhanced with custom OpenAPI documentation and cyberpunk Swagger UI
- [A] docs/api.md - Added comprehensive API documentation
- [M] README.md - Updated with frontend and API documentation
- [A] tests/frontends/test_frontend_base.py - Tests for frontend base class
- [A] tests/frontends/test_gradio_frontend.py - Tests for Gradio frontend
- [M] DEVLOG.md - Updated development log

## Bugs
- Fixed SongBook model in models/simulation.py to properly handle history data
- Fixed engine/simulation.py to import GlobalMarket correctly
- Updated models/__init__.py to include MarketListing and ActionLog
- Fixed DELETE endpoint for kill_agent to accept query parameters instead of JSON body
- Updated src/scribe.py to use correct model imports

# Improved Headless Script and Simulation API Enhancements - 2025-05-03

## Description

Enhanced the headless script and simulation API to provide a better experience when running simulations:

1. Added new API endpoints:
   - `/simulation/reset/{simulation_id}` - Resets a simulation to its initial state
   - `/simulation/next/{simulation_id}` - Advances a simulation by a single day (simplified version of run endpoint)

2. Improved headless frontend:
   - Added graceful shutdown with Ctrl+C that properly saves state
   - Implemented simulation reset functionality
   - Enhanced command-line options for better control
   - Modified to use the new "next" API endpoint for step-by-step progression
   - Fixed narrative file path handling
   - Enhanced action display to show detailed agent actions and their consequences
   - Added colored output for better visualization of simulation progress
   - Added detailed display of agent reasoning and action outcomes

3. Enhanced error handling:
   - Added validation for API responses
   - Improved signal handling to save simulation states before exit
   - Added proper shutdown sequence for API server
   - Fixed syntax errors in agent prompt formatting

## Demand

"Fix the GUI" and then "forget gui let's focus on headless script experience first we can come back to gui later.
Right now I have to launch api and script separately, its ok
but headless script should:
- call /simulation/reset/ with given or default sim_id on launch
- then run the number of days
simulation now runs step by step on demand, you call /simulation/next to have it advance to next day, it replies with OK and then you can check /status to see what agent/narrator is currently awaited / what actions are chosen so far / what narrator says once complete it shows final day state with all inventions/songs/etc
also the main.py when I ctrl+c it doesn't work! I should always be able to stop simulation. on signal it must always run _save_state and quit."

plus "ok now you must also print in headless script the actions as in the api... It should include each day action choice as scribe prints it" and include "is executing action" and resulting action consequences.

## Files

- [A] api/routes/simulation.py - Added reset and next endpoints
- [M] frontends/headless.py - Enhanced with detailed action display and consequences
- [M] main.py - Added proper signal handling for graceful shutdown
- [M] src/agent.py - Fixed syntax error in agent prompt formatting
- [M] DEVLOG.md - Updated with new changes

## Bugs

- Fixed the unterminated string literal in src/agent.py that was preventing the API server from starting
- Fixed API server signal handling to ensure proper shutdown on Ctrl+C
- Fixed the headless frontend to correctly process and display action consequences
- Improved error detection and reporting in the headless script

# API Implementation - 2023-07-26

## Description
Refactored ProtoNomia to separate the simulation engine from the UI and created a FastAPI-based REST API with comprehensive endpoints for simulation and agent management. Implemented a headless CLI frontend that uses the API to run simulations with output matching the original CLI.

## Demand
> MAIN GOAL: MAKE OUR PROJECT AN API + FRONTENDS
> - Refactor @simulation.py to be an engine that runs headless separate from scribe
> - Extract ./headless.py a first frontend that prints EXACTLY as currently simulation.py run, but which works by running our serv aside, then calling our API!
> - The API must be a FastAPI architecture leveraging pydantic Models for typing and modern approach, see docs @FastAPI 
> - API must expose following endpoints:
> - /simulation/start with params to start one 
> - /simulation/status to print current status
> - /agent/add create a new agent, with agent model as json payload
> - /agent/kill by name xor by id kill agent
> - /agent/status info about a specific agent
> - /agent/update change anything of an agent: credit, needs, etc
> - make them REST proper, smart, generic, leverage models to dont repeat yourself

## Files
- [A] ./docs/devplan.md - Development plan for the API implementation
- [A] models/__init__.py - Initialization file for the models package
- [A] models/agent.py - Refactored Agent models
- [A] models/simulation.py - Refactored Simulation models
- [A] engine/__init__.py - Initialization file for the engine package
- [A] engine/simulation.py - Refactored simulation engine (headless)
- [A] api/__init__.py - Initialization file for the API package
- [A] api/main.py - FastAPI application
- [A] api/models.py - API-specific Pydantic models
- [A] api/simulation_manager.py - Singleton manager for simulation instances
- [A] api/routes/__init__.py - Initialization file for the routes package
- [A] api/routes/simulation.py - Simulation routes
- [A] api/routes/agent.py - Agent routes
- [A] frontends/__init__.py - Initialization file for the frontends package
- [A] frontends/headless.py - Headless CLI frontend using the API
- [A] main.py - Main entry point for the API server
- [A] tests/api/test_simulation_routes.py - Tests for simulation routes
- [A] tests/api/test_agent_routes.py - Tests for agent routes
- [A] DEVLOG.md - Development log

## Bugs
None identified during implementation. 