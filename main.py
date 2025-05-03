"""
ProtoNomia Main Entry Point
This module provides the main entry point for the ProtoNomia application.
"""
import argparse
import logging
import os
import sys
import uvicorn
from typing import Optional

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
    
    # Import the API app
    from api import app
    
    # Run the server
    uvicorn.run(
        "api:app",
        host=host,
        port=port,
        reload=True,
        log_level=log_level.lower(),
    )

if __name__ == "__main__":
    args = parse_args()
    try:
        run_api_server(args.host, args.port, args.log_level)
    except KeyboardInterrupt:
        logger.info("Server stopped by user.")
    except Exception as e:
        logger.error(f"Error running server: {e}", exc_info=True)
        sys.exit(1) 