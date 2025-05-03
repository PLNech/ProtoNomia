# Simulation Stages and Night Activities

## Overview

ProtoNomia simulation now uses a stage-based approach to track the current status of the simulation. This allows for better monitoring and visualization of the simulation process, especially when running in headless or API-driven mode.

## Simulation Stages

The simulation cycle is divided into the following stages:

1. **INITIALIZATION**: Initial setup of the simulation environment, creating agents, setting initial state.
2. **AGENT_DAY**: Processing day actions for agents one at a time. During this stage, the simulation waits for each agent to choose and execute their day action.
3. **NARRATOR**: Generating the narrative for the day based on all agent actions.
4. **AGENT_NIGHT**: Processing night activities for agents one at a time, including dinner, music listening, and social interaction.

## API Stage Information

When using the API, you can query the current simulation stage through the status endpoint:

```bash
GET /simulation/status/{simulation_id}
```

The response includes the following stage-related fields:

```json
{
  "simulation_id": "...",
  "current_stage": "agent_day",
  "current_agent_id": "...",
  "current_agent_name": "Dr. Nebula Martin Alpha",
  "night_activities_today": 0,
  ...
}
```

These fields indicate:
- Which stage the simulation is currently in
- Which agent is currently being processed (if applicable)
- How many night activities have been processed for the current day

## Night Activities

The simulation now includes a night phase where agents engage in the following activities:

### Dinner
- Agents automatically consume FOOD items in decreasing quality order
- Each food item's quality is added to the agent's food need (capped at 1.0)
- Agents stop eating when their food need reaches 0.95 or when they run out of food

### Music Listening
- Agents choose a song to listen to from the available songs in the simulation
- Listening to music increases an agent's fun need

### Social Interaction
- Agents write letters to 1-3 other agents in the simulation
- Each letter has a recipient, title, and message content
- Letter exchanges improve relationship dynamics and increase fun for all participants
- Letter topics vary based on agent personalities and current events
- The letter system enables more structured and personal interactions between agents

## Headless Frontend Display

The headless frontend now displays detailed information about the current simulation stage and night activities:

- Shows which agent the simulation is waiting for
- Displays agent action choices and reasoning
- Shows action consequences in detail
- Visualizes night activities including:
  - Dinner consumption with food items and quality
  - Song listening choices
  - Chat interactions between agents

## Implementation Details

The stage-based simulation improves error handling and makes the simulation more observable:

- Each stage transition is clearly logged
- The simulation state records which agent is currently active
- Agent actions and night activities are processed one at a time
- All night activities are tracked and can be queried through the API

This provides a more detailed and accurate representation of the simulation's internal state at any given time. 