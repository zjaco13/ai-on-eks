from strands import Agent, tool
import logging
import json
from typing import Any, Dict
from uuid import uuid4
import os
import asyncio

from rich.console import Console
from mcp.client.streamable_http import streamablehttp_client
from strands.tools.mcp import MCPClient
from strands.models import BedrockModel

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Global variables
WEATHER_URL = f"http://localhost:{os.getenv('WEATHER_MCP_PORT', '8080')}/mcp"
mcp_clients: Dict[str, MCPClient] = {}

# Load system prompt from file
def load_system_prompt():
    try:
        with open("system.md", "r") as file:
            return file.read()
    except Exception as e:
        logger.error(f"Error loading system prompt from file: {e}")
        raise RuntimeError(f"Failed to load system prompt from system.md: {e}")

# System prompt
PROMPT = load_system_prompt()

# Get available tools from MCP servers

def main():
    logger.info("Starting Travel Planning Assistant")
    mcp_clients["Weather"] = MCPClient(lambda url=WEATHER_URL: streamablehttp_client(url))
    model_id = os.getenv("BEDROCK_MODEL_ID", "us.anthropic.claude-3-7-sonnet-20250219-v1:0")
    try:
        bedrock_model = BedrockModel(model_id=model_id)
        logger.info("Successfully initialized Bedrock model")

        travel_agent = Agent(
            model=bedrock_model,
            system_prompt=PROMPT,
        )
        with mcp_clients["Weather"] as weather_client:
            weather_tools = weather_client.list_tools_sync()
            logger.info(f"tools: {weather_tools}")
            travel_agent.tool_registry.process_tools(weather_tools)

            logger.info("Travel agent successfully created with system prompt and weather tool")

            # Interactive session
            console = Console()
            console.print("[bold green]Travel Planning Assistant[/bold green]")
            console.print("Ask about travel plans, weather, etc. Type 'exit' to quit.")
            logger.info("Starting interactive session")

            while True:
                user_input = input("\nYou: ")
                if user_input.lower() in ["exit", "quit"]:
                    logger.info("User requested to exit")
                    break

                # Process the user input with the agent
                logger.info(f"Processing user input: '{user_input}'")
                try:
                    response = travel_agent(user_input)
                    logger.info("Successfully generated response")
                    console.print(f"\n[bold blue]Assistant:[/bold blue] {response}")
                except Exception as e:
                    logger.error(f"Error generating response: {e}", exc_info=True)
                    console.print(f"\n[bold red]Error:[/bold red] Failed to generate response: {str(e)}")

            logger.info("Interactive session ended")
    except Exception as e:
        logger.error(f"Error creating travel agent: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    logger.info("Application starting")
    # Run the main function
    try:
        main()
        logger.info("Application completed successfully")
    except Exception as e:
        logger.critical(f"Unhandled exception in main application: {e}", exc_info=True)
        print(f"Critical error: {str(e)}")
