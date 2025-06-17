import logging
import sys

from interactive import interactive_agent
from mcp_server import weather_mcp_server
from a2a_server import weather_a2a_server

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
    force=True,
)

def main_mcp_server():
    """Main entry point for the weather MCP server."""
    logging.info("Starting Weather Agent as MCP Server")
    weather_mcp_server()

def main_a2a_server():
    """Main entry point for the weather A2A server."""
    logging.info("Starting Weather Agent as A2A Server")
    weather_a2a_server()

def main_interactive():
    """Main entry point for the weather agent."""
    logging.info("Starting Weather Agent as Interactive Agent")
    interactive_agent()

if __name__ == "__main__":
    main_interactive()
