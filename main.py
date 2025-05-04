"""
ProtoNomia Main Entry Point
This module provides the main entry point for the ProtoNomia application.
"""
import argparse
import logging
import os
import sys
import signal
import uvicorn

# Add the current directory to the path for imports
sys.path.insert(0, os.path.abspath("."))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("protonomia.log"),
    ],
)
logger = logging.getLogger(__name__)

# Import the API app
from src.api import app
from src.api.dependencies import get_simulation_manager

def save_all_simulations():
    """Save all active simulations' states to disk."""
    try:
        # Get the simulation manager from the dependency
        simulation_manager = get_simulation_manager()
        
        # Get all active simulations
        sim_ids = simulation_manager.list_simulations()
        logger.info(f"Saving state for {len(sim_ids)} active simulations")
        
        for sim_id in sim_ids:
            try:
                simulation = simulation_manager.get_simulation(sim_id)
                if simulation:
                    simulation._save_state()
                    logger.info(f"Saved state for simulation {sim_id}")
            except Exception as e:
                logger.error(f"Error saving state for simulation {sim_id}: {e}")
    except Exception as e:
        logger.error(f"Could not save simulations: {e}")

def signal_handler(sig, frame):
    """Handle signals (like SIGINT from Ctrl+C) by saving states and exiting gracefully."""
    logger.info("\nReceived shutdown signal, saving simulation states and exiting...")
    save_all_simulations()
    logger.info("All simulation states saved. Shutting down server.")
    sys.exit(0)

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="ProtoNomia Simulation API")
    parser.add_argument(
        "--host", 
        type=str, 
        default="127.0.0.1", 
        help="Host to bind the API server to"
    )
    parser.add_argument(
        "--port", 
        type=int, 
        default=8000, 
        help="Port to bind the API server to"
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level"
    )
    return parser.parse_args()

def setup_signal_handlers():
    """Set up signal handlers for graceful shutdown."""
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    # Handle SIGABRT on Unix-like systems
    if hasattr(signal, 'SIGABRT'):
        signal.signal(signal.SIGABRT, signal_handler)

def run_api_server(host: str, port: int, log_level: str):
    """
    Run the FastAPI server.
    
    Args:
        host: Host to bind to
        port: Port to bind to
        log_level: Logging level
    """
    # Configure logging level
    log_level_num = getattr(logging, log_level.upper())
    logging.getLogger().setLevel(log_level_num)
    
    # Set up signal handlers
    setup_signal_handlers()
    
    # Log startup information
    logger.info(f"Starting ProtoNomia API server on {host}:{port}")
    logger.info("Press Ctrl+C to save all simulation states and exit")
    
    # Run the server with Uvicorn
    # Set reload=False to allow our signal handlers to work properly
    uvicorn.run(
        "src.api:app",
        host=host,
        port=port,
        reload=False,
        log_level=log_level.lower(),
    )

if __name__ == "__main__":
    args = parse_args()
    try:
        run_api_server(args.host, args.port, args.log_level)
    except KeyboardInterrupt:
        # This should not be reached due to signal handler, but just in case
        logger.info("Server stopped by user.")
        save_all_simulations()
    except Exception as e:
        logger.error(f"Error running server: {e}", exc_info=True)
        # Try to save simulations even on error
        try:
            save_all_simulations()
        except Exception as save_error:
            logger.error(f"Error saving simulations during shutdown: {save_error}")
        sys.exit(1) 