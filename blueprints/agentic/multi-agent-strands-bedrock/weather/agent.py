"""Weather agent module for providing weather forecasts and alerts."""

import json
import os
from typing import Dict, List, Optional, Any

from mcp import StdioServerParameters, stdio_client
from mcp.client.streamable_http import streamablehttp_client
from strands import Agent, tool
from strands.models import BedrockModel
from strands.tools.mcp import MCPClient


@tool
def weather_assistant_tool(query: str) -> str:
    """
    Process and respond to weather forecast or alert queries.

    Args:
        query: The user's weather-related question

    Returns:
        A helpful response addressing the user's query
    """
    return weather_assistant(query)


def weather_assistant(query: str) -> str:
    """Process and respond to weather forecast or alert queries."""
    try:
        weather_agent = get_weather_agent()
        response = str(weather_agent(query))
        if response:
            return response
    except Exception as e:
        print(f"Error processing weather query: {str(e)}")
        return "I apologize, but I encountered an error while processing your request. Please try again later."

    return "I apologize, but I couldn't properly analyze your question. Could you please rephrase or provide more context?"


def get_weather_agent() -> Agent:
    """
    Create and return a Weather Agent instance with dynamically loaded MCP tools.

    Returns:
        Agent: A configured weather assistant agent with tools from enabled MCP servers
    """
    model_id = os.getenv("BEDROCK_MODEL_ID", "us.anthropic.claude-3-7-sonnet-20250219-v1:0")
    bedrock_model = BedrockModel(model_id=model_id)

    try:
        # Load and combine tools from all enabled MCP servers
        all_tools = _load_mcp_tools_from_config()

        # Create the weather agent with specific capabilities
        weather_agent = Agent(
            name="Weather Assistant",
            description="Weather Assistant that provides weather forecasts and alerts",
            model=bedrock_model,
            system_prompt="""You are Weather Assistant that helps the user with forecasts or alerts:
- Provide weather forecasts for US cities for the next 3 days if no specific period is mentioned
- When returning forecasts, always include whether the weather is good for outdoor activities for each day
- Provide information about weather alerts for US cities when requested""",
            tools=all_tools,
        )

        return weather_agent

    except Exception as e:
        print(f"Error getting agent: {str(e)}")
        # Return a fallback agent when MCP client fails
        fallback_agent = Agent(
            model=bedrock_model,
            system_prompt="""I am a Weather Assistant, but I'm currently experiencing technical difficulties accessing weather data.
I apologize for the inconvenience. Please try again later or contact support if the issue persists.""",
            tools=[],
        )
        return fallback_agent


def _load_mcp_tools_from_config() -> List[Any]:
    """
    Load MCP tools from all enabled servers defined in mcp.json.

    Returns:
        List[Any]: Combined list of tools from all enabled MCP servers
    """
    config_path = os.path.join(os.path.dirname(__file__), "mcp.json")

    if not os.path.exists(config_path):
        print(f"MCP configuration file not found at {config_path}")
        return []

    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
    except Exception as e:
        print(f"Error reading MCP configuration: {str(e)}")
        return []

    mcp_servers = config.get("mcpServers", {})
    all_tools = []

    for server_name, server_config in mcp_servers.items():
        if server_config.get("disabled", False):
            print(f"Skipping disabled MCP server: {server_name}")
            continue

        try:
            print(f"Loading tools from MCP server: {server_name}")
            mcp_client = _create_mcp_client_from_config(server_name, server_config)
            mcp_client.start()
            tools = mcp_client.list_tools_sync()
            all_tools.extend(tools)
            print(f"Loaded {len(tools)} tools from {server_name}")
        except Exception as e:
            print(f"Error loading tools from MCP server {server_name}: {str(e)}")
            continue

    print(f"Total tools loaded: {len(all_tools)}")
    return all_tools


def _create_mcp_client_from_config(server_name: str, server_config: Dict[str, Any]) -> MCPClient:
    """
    Create an MCP client based on server configuration.

    Args:
        server_name: Name of the MCP server
        server_config: Configuration dictionary for the server

    Returns:
        MCPClient: Configured MCP client

    Raises:
        ValueError: If server configuration is invalid
    """
    # Check if it's a URL-based server (streamable-http)
    if "url" in server_config:
        url = server_config["url"]
        print(f"Creating streamable-http MCP client for {server_name} at {url}")
        return MCPClient(
            lambda: streamablehttp_client(url)
        )

    # Check if it's a command-based server (stdio)
    elif "command" in server_config and "args" in server_config:
        command = server_config["command"]
        args = server_config["args"]
        env = server_config.get("env", {})

        if env:
            print(f"Creating stdio MCP client for {server_name} with command: {command} {' '.join(args)} and env vars: {list(env.keys())}")
        else:
            print(f"Creating stdio MCP client for {server_name} with command: {command} {' '.join(args)}")

        return MCPClient(
            lambda: stdio_client(
                StdioServerParameters(
                    command=command,
                    args=args,
                    env=env if env else None
                )
            )
        )

    else:
        raise ValueError(f"Invalid MCP server configuration for {server_name}: must have either 'url' or both 'command' and 'args'")


def _create_mcp_client() -> MCPClient:
    """
    Create an MCP client based on environment configuration (legacy fallback).

    Returns:
        MCPClient: Configured MCP client
    """
    mcp_server_url = os.getenv("MCP_SERVER_URL")
    if mcp_server_url:
        print(f"Using MCP server streamable http URL: {mcp_server_url}")
        return MCPClient(
            lambda: streamablehttp_client(mcp_server_url)
        )

    mcp_server_location = os.getenv("MCP_SERVER_LOCATION","mcp-servers/weather-mcp-server")
    print(f"Using MCP server stdio from location: {mcp_server_location}")
    return MCPClient(
        lambda: stdio_client(
            StdioServerParameters(
                command="uvx",
                args=["--from", ".", "--directory", mcp_server_location, "mcp-server", "--transport","stdio"]
            )
        )
    )


if __name__ == "__main__":
    weather_assistant("Get the weather for Seattle")
