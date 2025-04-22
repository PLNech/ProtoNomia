#!/usr/bin/env python3
import argparse
import json
import logging
import sys
import time
from datetime import datetime

from core.simulation import Simulation
# Import ProtoNomia modules
from models.base import (
    SimulationConfig, ActionType
)
from settings import DEFAULT_LM

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('simulation.log')
    ]
)
logger = logging.getLogger(__name__)


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Run ProtoNomia simulation in headless mode')
    
    # Basic simulation parameters
    parser.add_argument('--initial-population', type=int, default=20,
                        help='Initial population size (default: 20)')
    parser.add_argument('--max-population', type=int, default=100,
                        help='Maximum population size (default: 100)')
    parser.add_argument('--seed', type=int,
                        help='Random seed for reproducibility')
    parser.add_argument('--ticks', type=int, default=100,
                        help='Number of simulation ticks to run (default: 100)')
    parser.add_argument('--timeout', type=float,
                        help='Maximum runtime in seconds')
    
    # Resource and economy parameters
    parser.add_argument('--resource-scarcity', type=float, default=0.5,
                        help='Resource scarcity level (0.0-1.0, default: 0.5)')
    parser.add_argument('--terra-mars-trade-ratio', type=float, default=0.6,
                        help='Terra-Mars trade ratio (0.0-1.0, default: 0.6)')
    
    # Interaction parameters
    parser.add_argument('--interactions', type=str, nargs='+',
                        choices=[e.value for e in ActionType],
                        default=['WORK', 'APPLY', 'HIRE', 'LIST_GOODS', 'BUY'],
                        help='Enabled economic interactions (default: WORK APPLY HIRE LIST_GOODS BUY)')
    
    # Population control parameters
    parser.add_argument('--birth-rate', type=float, default=0.01,
                        help='Base birth rate (default: 0.01)')
    parser.add_argument('--death-rate', type=float, default=0.005,
                        help='Base death rate (default: 0.005)')
    
    # Output parameters
    parser.add_argument('--output', type=str,
                        help='Output file for simulation results (JSON)')
    parser.add_argument('--verbosity', type=int, default=3, choices=range(1, 6),
                        help='Narrative verbosity level (1-5, default: 3)')
    parser.add_argument('--log-level', type=str, default='DEBUG',
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        help='Logging level (default: INFO)')
    
    # LLM configuration for agents
    parser.add_argument('--use-llm', action='store_true', default=True,
                        help='Use LLM for agent decision making and narrative generation')
    parser.add_argument('--model-name', type=str, default=DEFAULT_LM,
                        help='LLM model name to use with Ollama for agents (default: gemma:1b)')
    
    # LLM configuration for narrator
    parser.add_argument('--narrator-model-name', type=str, default=DEFAULT_LM,
                        help=f'LLM model name to use with Ollama for narrator (default: {DEFAULT_LM})')
    parser.add_argument('--temperature', type=float, default=0.8,
                        help='Temperature for LLM generation (0.0-1.0, default: 0.8)')
    parser.add_argument('--top-p', type=float, default=0.95,
                        help='Top-p (nucleus sampling) for LLM generation (0.0-1.0, default: 0.95)')
    parser.add_argument('--top-k', type=int, default=40,
                        help='Top-k tokens to consider for LLM generation (default: 40)')
    
    return parser.parse_args()


def run_simulation(args):
    """Run the simulation with the given arguments"""
    # Configure simulation
    logger.info("Configuring simulation...")
    
    # Convert interaction strings to enum values
    enabled_interactions = [
        ActionType(interaction) for interaction in args.interactions
    ]
    
    # Create simulation configuration
    config = SimulationConfig(
        name="ProtoNomia Headless",
        seed=args.seed,
        start_date=datetime(2993, 1, 1),  # Start in the year 2993
        initial_population=args.initial_population,
        max_population=args.max_population,
        resource_scarcity=args.resource_scarcity,
        terra_mars_trade_ratio=args.terra_mars_trade_ratio,
        enabled_interaction_types=enabled_interactions,
        narrative_verbosity=args.verbosity
    )
    
    # Create and initialize simulation
    logger.info(f"Initializing simulation with population {args.initial_population}")
    simulation = Simulation(
        config=config, 
        use_llm=args.use_llm, 
        model_name=args.model_name,
        narrator_model_name=args.narrator_model_name,
        temperature=args.temperature,
        top_p=args.top_p,
        top_k=args.top_k
    )
    
    simulation.initialize()
    
    # Set up timeout if specified
    end_time = None
    if args.timeout:
        end_time = time.time() + args.timeout
        logger.info(f"Simulation will time out after {args.timeout} seconds")
    
    # Run simulation for specified number of ticks or until timeout
    logger.info(f"Running simulation for {args.ticks} ticks...")
    results = []
    
    for tick in range(args.ticks):
        tick_start_time = time.time()
        
        # Check for timeout
        if end_time and time.time() >= end_time:
            logger.info(f"Simulation timed out after {args.timeout} seconds")
            break
        
        # Run one simulation tick
        state = simulation.step()
        
        # Collect metrics
        metrics = {
            "tick": tick,
            "population": state.population_size,
            "active_interactions": len(state.active_interactions),
            "completed_interactions": len(state.completed_interactions),
            "narrative_events": len(state.narrative_events),
            "economic_indicators": state.economic_indicators,
            "tick_duration": time.time() - tick_start_time
        }
        results.append(metrics)
        
        # Log progress
        if tick % 10 == 0 or tick == args.ticks - 1:
            logger.info(f"Tick {tick}/{args.ticks} - Population: {state.population_size}")
    
    # Save results if output file specified
    if args.output:
        with open(args.output, 'w') as f:
            json.dump({
                "config": config.dict(),
                "metrics": results,
                "final_state": {
                    "population": state.population_size,
                    "total_interactions": len(state.completed_interactions),
                    "total_events": len(state.narrative_events)
                }
            }, f, indent=2, default=str)
        logger.info(f"Results saved to {args.output}")
    
    # Print summary
    logger.info("Simulation complete")
    logger.info(f"Final population: {state.population_size}")
    logger.info(f"Total interactions: {len(state.completed_interactions)}")
    logger.info(f"Total narrative events: {len(state.narrative_events)}")
    
    return simulation.state


if __name__ == "__main__":
    # Parse command line arguments
    args = parse_args()
    
    # Set logging level
    logger.setLevel(getattr(logging, args.log_level))
    
    try:
        # Run simulation
        final_state = run_simulation(args)
        sys.exit(0)
    except KeyboardInterrupt:
        logger.info("Simulation interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error running simulation: {e}", exc_info=True)
        sys.exit(1) 