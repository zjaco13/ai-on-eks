from weather_interactive import interactive_agent
from weather_mcp_server import weather_mcp_server


def main_mcp_server():
    """Main entry point for the weather MCP server."""
    print("Starting Weather Agent as MCP Server")
    weather_mcp_server()

if __name__ == "__main__":
    interactive_agent()
