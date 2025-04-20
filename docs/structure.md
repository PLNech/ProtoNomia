```
protonomia/
├── README.md                   # Project documentation
├── requirements.txt            # Python dependencies
├── setup.py                    # Setup script
├── start_backend.sh            # Backend startup script
├── start_frontend.sh           # Frontend startup script
│
├── core/                       # Simulation core
│   ├── __init__.py
│   ├── config.py               # Simulation configuration
│   ├── event_system.py         # Event dispatching system
│   └── simulation.py           # Main simulation engine
│
├── models/                     # Data models
│   ├── __init__.py
│   ├── actions.py              # Agent action models
│   └── base.py                 # Core entity models
│
├── agents/                     # Agent implementation
│   ├── __init__.py
│   ├── behavior.py             # Decision-making framework
│   ├── lifecycle.py            # Birth, aging, death mechanics
│   ├── llm_agent.py            # LLM-based agent controller
│   ├── personality.py          # Personality traits system
│   └── relationships.py        # Inter-agent relationships
│
├── economics/                  # Economic systems
│   ├── __init__.py
│   ├── market.py               # Market simulation
│   ├── trade.py                # Mars-Terra trade system
│   └── interactions/           # Economic game implementations
│       ├── __init__.py
│       ├── ultimatum.py        # Ultimatum game
│       ├── trust.py            # Trust game
│       └── public_goods.py     # Public goods game
│
├── narrative/                  # Narrative generation
│   ├── __init__.py
│   ├── events.py               # Event processing
│   ├── narrator.py             # Narrative generator
│   └── templates.py            # Story templates
│
├── population/                 # Population dynamics
│   ├── __init__.py
│   └── controller.py           # Population control mechanisms
│
├── api/                        # API endpoints
│   ├── __init__.py
│   ├── main.py                 # FastAPI setup
│   ├── routes/                 # API endpoints
│   │   ├── __init__.py
│   │   ├── agents.py           # Agent endpoints
│   │   ├── economy.py          # Economy endpoints
│   │   ├── narrative.py        # Narrative endpoints
│   │   └── simulation.py       # Simulation control endpoints
│   └── websockets.py           # Real-time communication
│
└── frontend/                   # Next.js frontend
    └── protonomia-ui/
        ├── package.json
        ├── next.config.js
        ├── tailwind.config.js
        ├── public/
        │   └── assets/         # Static assets
        └── src/
            ├── pages/
            │   ├── index.tsx             # Home page
            │   ├── dashboard.tsx         # Dashboard
            │   ├── agents.tsx            # Agents view
            │   ├── agents/[id].tsx       # Agent details
            │   ├── economy.tsx           # Economy view
            │   └── narrative.tsx         # Narrative view
            ├── components/
            │   ├── dashboard/            # Dashboard components
            │   ├── visualization/        # Charts and graphs
            │   ├── narrative/            # Story display
            │   └── simulation/           # Simulation controls
            ├── hooks/
            │   ├── useSimulation.ts      # Simulation control hooks
            │   ├── useWebSocket.ts       # Real-time data hooks
            │   └── useAgents.ts          # Agent data hooks
            └── styles/
                └── globals.css           # Global styles
```