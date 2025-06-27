import logging
import json
from typing import Any, List, Dict
from uuid import uuid4
import os
import asyncio

import httpx
from rich.console import Console
from a2a.client import A2ACardResolver, A2AClient
from a2a.types import (
    AgentCard,
    MessageSendParams,
    SendMessageRequest,
)
from strands.models import BedrockModel

from strands import Agent, tool

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load system prompt from file
def load_system_prompt():
    try:
        with open("system.md", "r") as file:
            return file.read()
    except Exception as e:
        logger.error(f"Error loading system prompt from file: {e}")
        raise RuntimeError(f"Failed to load system prompt from system.md: {e}")

PROMPT = load_system_prompt()

# def tools: IF A2A, a2a tools, if mcp, mcp tools
    
# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Global variables
PUBLIC_AGENT_CARD_PATH = "/.well-known/agent.json"
WEATHER_URL = f"http://localhost:{os.getenv('WEATHER_A2A_PORT', '9000')}"

async def send_message(message: str):
    async with httpx.AsyncClient(timeout=120) as httpx_client:
        # Initialize A2ACardResolver
        resolver = A2ACardResolver(
            httpx_client=httpx_client,
            base_url=WEATHER_URL,
        )

        # Fetch Public Agent Card and Initialize Client
        agent_card: AgentCard | None = None

        try:
            logger.info("Attempting to fetch public agent card from: {} {}", WEATHER_URL, PUBLIC_AGENT_CARD_PATH)
            agent_card = await resolver.get_agent_card()  # Fetches from default public path
            logger.info("Successfully fetched public agent card:")
            logger.info(agent_card.model_dump_json(indent=2, exclude_none=True))
        except Exception as e:
            logger.exception("Critical error fetching public agent card")
            raise RuntimeError("Failed to fetch the public agent card. Cannot continue.") from e

        client = A2AClient(httpx_client=httpx_client, agent_card=agent_card)
        logger.info("A2AClient initialized.")

        send_message_payload: dict[str, Any] = {
            "message": {
                "role": "user",
                "parts": [{"kind": "text", "text": message}],
                "messageId": uuid4().hex,
            },
        }
        request = SendMessageRequest(id=str(uuid4()), params=MessageSendParams(**send_message_payload))

        # Handle streaming response
        response = await client.send_message(request)
        return str(response)

@tool
def get_weather(query: str) -> str:
    """Get weather information for a location and date range."""
    logger.info(f"Weather query: {query}")
    # Use a dedicated event loop for this call
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        # Run with a timeout
        return loop.run_until_complete(
            asyncio.wait_for(
                send_message(query),
                timeout=120.0  # 2 minute timeout
            )
        )
    except asyncio.TimeoutError:
        logger.error("Weather query timed out after 120 seconds")
        return "Weather information request timed out. Please try again or check with a weather service directly."
    except Exception as e:
        logger.error(f"Error in get_weather: {e}")
        return f"Error retrieving weather information: {str(e)}"
    finally:
        loop.close()

def main():
    logger.info("Starting Travel Planning Assistant")
    try:
        # Get the agent
        model_id = os.getenv("BEDROCK_MODEL_ID", "us.anthropic.claude-3-7-sonnet-20250219-v1:0")
        bedrock_model = BedrockModel(model_id=model_id)
        logger.info("Successfully initialized Bedrock model")

        travel_agent = Agent(
            model=bedrock_model,
            system_prompt=PROMPT,
            tools=[get_weather]
        )

        logger.info("Travel agent successfully created with system prompt and weather tool")
        logger.info("Creating travel agent")
        logger.info("Travel agent created successfully")

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
        logger.error(f"Error in main function: {e}", exc_info=True)
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
