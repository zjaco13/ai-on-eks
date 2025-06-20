"""Main entry point for the Weather Agent application."""

import asyncio
import logging
import os
import signal
import sys
import threading
from concurrent.futures import ThreadPoolExecutor

from agent_a2a_server import weather_a2a_server as a2a_server_agent
from agent_interactive import interactive_agent
from agent_mcp_server import weather_mcp_server as mcp_server_agent

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if os.getenv('DEBUG') == '1' else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
    force=True,
)

logger = logging.getLogger(__name__)


def main_mcp_server():
    """Start the MCP server."""
    logging.info("Starting MCP Server")
    mcp_server_agent()


def main_a2a_server():
    """Start the A2A server."""
    logging.info("Starting A2A Server")
    a2a_server_agent()


def main_interactive():
    """Start the interactive command-line interface."""
    logging.info("Starting Interactive Agent")
    interactive_agent()


def main_dual_server():
    """Start both MCP and A2A servers concurrently."""
    logger.info("Starting Weather Agent Dual Server...")
    logger.info(f"MCP Server will run on port {os.getenv('MCP_PORT', '8080')} with streamable-http transport")
    logger.info(f"A2A Server will run on port {os.getenv('A2A_PORT', '9000')}")

    # Event to coordinate shutdown
    shutdown_event = threading.Event()

    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, initiating shutdown...")
        shutdown_event.set()

    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Use ThreadPoolExecutor to run both servers
    with ThreadPoolExecutor(max_workers=2) as executor:
        try:
            # Submit both server functions to the thread pool
            mcp_future = executor.submit(main_mcp_server)
            a2a_future = executor.submit(main_a2a_server)

            logger.info("Both servers started successfully!")

            # Wait for shutdown signal
            shutdown_event.wait()

        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt, shutting down...")
        except Exception as e:
            logger.error(f"Error running dual server: {e}")
        finally:
            logger.info("Shutting down dual server...")


if __name__ == "__main__":
    main_interactive()
