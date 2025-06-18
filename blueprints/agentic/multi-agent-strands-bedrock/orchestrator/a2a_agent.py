from strands import Agent, tool
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
from strands.types.tools import ToolUse, ToolResult
WEATHER_TOOL_SPEC = {
    "name": "get_weather",
    "description": "Get detailed weather information for a specific location and time period",
    "inputSchema": {
        "json": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Detailed weather query including location, time period, and specific weather attributes needed"
                }
            },
            "required": ["query"]
        }
    }
}

PROMPT ="""You are a Travel Orchestration Agent designed to create comprehensive travel plans by coordinating with specialized agents. Your primary function is to delegate specific information requests to the appropriate specialized agents and NEVER generate this specialized information yourself.

CORE PRINCIPLES:
1. NEVER invent or fabricate specialized information that should come from other agents
2. ALWAYS use the appropriate tool to query specialized agents for their domain expertise
3. Be extremely clear and specific when formulating requests to other agents
4. Clearly attribute information in your responses to the appropriate specialized agent

WEATHER INFORMATION PROTOCOL:
When ANY weather-related information is needed, you MUST:
1. Use ONLY the get_weather tool to obtain this information
2. NEVER attempt to predict, estimate, or generate weather information yourself
3. Formulate weather queries with extreme specificity:
   - Include precise location (city, region, country)
   - Specify exact time period (dates, season, month)
   - Request specific weather attributes (temperature, precipitation, conditions)
   - Example: "What will the weather be like in Paris, France from June 15-20, 2025? Please provide daily temperature ranges, precipitation chances, and general conditions."
4. Wait for the weather agent's response before proceeding with travel recommendations
5. Clearly attribute all weather information in your final response: "According to the Weather Agent, Paris will experience..."

QUERY FORMULATION GUIDELINES:
1. Location Specificity:
   - Always include full city name AND country
   - Add region/state for clarity when needed
   - Use official location names, not colloquial ones
   - Example: "Kyoto, Japan" not just "Kyoto"

2. Temporal Precision:
   - Specify exact dates when available (YYYY-MM-DD format)
   - Otherwise, use precise season and year
   - For general queries, specify "typical weather" for a specific month/season
   - Example: "August 10-15, 2025" or "typical weather in early August"

3. Information Detail:
   - Request specific weather attributes (temperature ranges, precipitation probability, humidity levels, UV index, etc.)
   - Ask about weather patterns relevant to planned activities
   - Request time-of-day variations when relevant (morning fog, afternoon thunderstorms)
   - Example: "Please provide daily high and low temperatures, precipitation chances, and any weather warnings or patterns that might affect outdoor activities."

RESPONSE FORMATTING:
1. Always structure your final travel plans with clear sections
2. Explicitly attribute ALL weather information to the Weather Agent
3. Use phrases like:
   - "According to the Weather Agent..."
   - "The Weather Agent reports that..."
   - "Based on information from the Weather Agent..."
4. Never blend agent-provided information with your own suggestions without clear attribution
5. If the Weather Agent provides incomplete information, request additional details rather than filling gaps yourself

ERROR HANDLING:
1. If the Weather Agent returns an error or incomplete information:
   - Acknowledge the limitation
   - Do NOT substitute with your own weather predictions
   - Suggest the traveler check weather closer to their trip
   - Example: "The Weather Agent was unable to provide complete weather information for Bali in December. I recommend checking the forecast closer to your travel date."

2. If a location is not found:
   - Check for alternative spellings or nearby locations
   - Ask the user for clarification
   - Do NOT provide weather information for that location

EXAMPLES OF PROPER TOOL USAGE:

CORRECT:
User: "I'm planning a trip to Barcelona in July."
You: [Using get_weather tool] "What is the typical weather in Barcelona, Spain during July? Please provide temperature ranges, precipitation chances, humidity levels, and any common weather patterns that might affect tourism."

INCORRECT:
User: "I'm planning a trip to Barcelona in July."
You: "Barcelona is typically hot and sunny in July with temperatures around 80-90°F."

Remember: Your value comes from coordinating specialized information from expert agents, not from generating this information yourself. Always prioritize accuracy through proper tool usage over generating information independently."""

# def tools: IF A2A, a2a tools, if mcp, mcp tools
    
# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Global variables
PUBLIC_AGENT_CARD_PATH = "/.well-known/agent.json"
WEATHER_URL = f"http://localhost:{os.getenv('WEATHER_A2A_PORT', '9000')}"
remote_connections: Dict[str, A2AClient] = {}
cards: Dict[str, AgentCard] = {}
agents_info: str = ""
# Global HTTP client that stays open
http_client = None

# Initialize agents
async def init_agents(agent_addresses: List[str]):
    global remote_connections, cards, agents_info, http_client

    logger.info(f"Initializing connections to {len(agent_addresses)} agents")

    # Create a persistent HTTP client
    timeout = httpx.Timeout(60.0)
    http_client = httpx.AsyncClient(timeout=timeout)

    for address in agent_addresses:
        logger.info(f"Attempting to connect to agent at: {address}")
        resolver = A2ACardResolver(http_client, address)
        try:
            logger.debug(f"Fetching agent card from {address}")
            card = await resolver.get_agent_card()
            logger.info(f"Successfully retrieved agent card for: {card.name}")

            # Create A2A client with the persistent HTTP client
            remote_connections[card.name] = A2AClient(http_client, card, address)
            cards[card.name] = card
            logger.info(f"Successfully established connection to agent: {card.name}")

        except httpx.ConnectError as e:
            logger.error(f"Connection error when connecting to {address}: {e}")
            print(f"Error: Failed to get Agent Card from {address}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error when initializing connection to {address}: {e}", exc_info=True)
            print(f"Error: Failed to initialize connection for {address}: {e}")

    agent_info = [
        json.dumps({"name": card.name, "description": card.description}) for card in cards.values()
    ]
    agents_info = "\n".join(agent_info) if agent_info else "No agents found"

    if agent_info:
        logger.info(f"Successfully connected to {len(agent_info)} agents")
        for agent_data in agent_info:
            logger.info(f"Connected agent: {agent_data}")
    else:
        logger.warning("No agents were successfully connected")

@tool
def get_weather(task: str) -> str:
    """Send a message to another AI Agent that can query the Weather API for accurate information asking for specific weather information for the location given by the user

    Args:
        task: The message to send to the Weather AI Agent
    Returns:
        A helpful response addressing the query from the agent
    """
    try:
        # Use the current event loop with nest_asyncio
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(send_message("Weather Agent", task))
        logger.info("Weather information successfully retrieved")
        return result
    except Exception as e:
        logger.error(f"Error getting weather information: {e}", exc_info=True)
        return f"Error retrieving weather information: {str(e)}"

async def send_message(agent_name: str, task: str):
    """Send a task to another agent"""
    logger.info(f"Sending message to agent '{agent_name}': '{task[:50]}...'")

    if agent_name not in remote_connections:
        logger.error(f"Agent '{agent_name}' not found in remote connections")
        raise ValueError(f"Agent {agent_name} not found")

    client = remote_connections[agent_name]
    if not client:
        logger.error(f"Client not available for agent '{agent_name}'")
        raise ValueError(f"Client not available for agent {agent_name}")

    id = str(uuid4())
    logger.debug(f"Generated message ID: {id}")

    payload = {
        "message": {
            "role": "user",
            "parts": [{"kind": "text", "text": task}],
            "messageId": id,
        },
    }

    message = SendMessageRequest(id=id, params=MessageSendParams.model_validate(payload))

    logger.debug(f"Sending request to {agent_name}")
    try:
        response = await client.send_message(message)
        logger.info(f"Received response from {agent_name}")

        # Process and return the response
        response_dict = json.loads(response.model_dump_json())
        logger.debug(f"Response structure: {list(response_dict.keys())}")

        # Extract text from response
        if "result" in response_dict and "parts" in response_dict["result"]:
            for part in response_dict["result"]["parts"]:
                if part.get("kind") == "text" and "text" in part:
                    text_content = part["text"]
                    logger.info(f"Successfully extracted text content from {agent_name} response")
                    logger.debug(f"Text content (truncated): {text_content[:100]}..." if len(text_content) > 100 else text_content)
                    return text_content

        logger.warning(f"No text content found in response from {agent_name}")
        return "No response received from weather agent"
    except Exception as e:
        logger.error(f"Error sending message to {agent_name}: {e}", exc_info=True)
        raise

def get_agent() -> Agent:
    logger.info("Creating travel agent with Bedrock model")
    model_id = os.getenv("BEDROCK_MODEL_ID", "us.anthropic.claude-3-7-sonnet-20250219-v1:0")
    logger.info(f"Using Bedrock model: {model_id}")

    try:
        bedrock_model = BedrockModel(model_id=model_id)
        logger.info("Successfully initialized Bedrock model")

        travel_agent = Agent(
            model=bedrock_model,
            system_prompt=PROMPT,
            tools=[get_weather]
        )
        logger.info("Travel agent successfully created with system prompt and weather tool")
        return travel_agent
    except Exception as e:
        logger.error(f"Error creating travel agent: {e}", exc_info=True)
        raise

async def async_main():
    logger.info("Starting Travel Planning Assistant")

    try:
        # Initialize connections
        await init_agents([WEATHER_URL])

        # Get the agent
        logger.info("Creating travel agent")
        agent = get_agent()
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
                response = agent(user_input)
                logger.info("Successfully generated response")
                console.print(f"\n[bold blue]Assistant:[/bold blue] {response}")
            except Exception as e:
                logger.error(f"Error generating response: {e}", exc_info=True)
                console.print(f"\n[bold red]Error:[/bold red] Failed to generate response: {str(e)}")

        logger.info("Interactive session ended")
    except Exception as e:
        logger.error(f"Error in main function: {e}", exc_info=True)
        print(f"Error: {str(e)}")
    finally:
        # Clean up the HTTP client
        if http_client:
            await http_client.aclose()
            logger.info("HTTP client closed")

def main():
    logger.info("Application starting")
    # Run the async main function
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(async_main())
        logger.info("Application completed successfully")
    except Exception as e:
        logger.critical(f"Unhandled exception in main application: {e}", exc_info=True)
        print(f"Critical error: {str(e)}")

if __name__ == "__main__":
    main()
