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
- Fully configurable simulation parameters

## Installation

1. Clone the repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Make sure you have Ollama installed and running locally

## Usage

Run a simulation with default parameters:

```bash
python src/simulation.py
```

Customize your simulation:

```bash
python src/simulation.py --agents 10 --days 50 --model gemma3:1b --log-level WARNING
```

### Command Line Options

- `--agents`: Number of agents in the simulation (default: 5)
- `--days`: Number of days to run the simulation (default: 30)
- `--credits`: Starting credits for each agent (default: random)
- `--model`: LLM model to use (default: gemma3:1b)
- `--output`: Output directory (default: output/)
- `--temperature`: LLM temperature (default: 0.7)
- `--log-level`: Logging level (default: INFO)

## Rich Terminal Output

ProtoNomia features immersive cyberpunk-themed colored output in your terminal:

- Agent names in Neon Pink
- Credits in Neon Green
- Actions in Neon Orange
- Goods in Neon Blue
- Needs (rest/fun/food) in Neon Purple

To enjoy the full visual experience, run with warning or error log level:

```bash
python src/simulation.py --log-level WARNING
``` 
