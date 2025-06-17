import logging
import sys

from agent_interactive import interactive_agent
from agent_mcp_server import weather_mcp_server as mcp_server_agent
from agent_a2a_server import weather_a2a_server as a2a_server_agent

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
    force=True,
)

def main_mcp_server():
    """Main entry point for the MCP server."""
    logging.info("Starting MCP Server")
    mcp_server_agent()

def main_a2a_server():
    """Main entry point for A2A server."""
    logging.info("Starting A2A Server")
    a2a_server_agent()

def main_interactive():
    """Main entry point for Interactive Agent."""
    logging.info("Starting Interactive Agent")
    interactive_agent()

if __name__ == "__main__":
    main_interactive()
