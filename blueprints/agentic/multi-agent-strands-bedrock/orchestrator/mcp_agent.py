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

# System prompt
PROMPT = """You are a Travel Orchestration Agent designed to create comprehensive travel plans by coordinating with specialized agents. Your primary function is to delegate specific information requests to the appropriate specialized agents and NEVER generate this specialized information yourself.

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

weather_client = MCPClient(lambda: streamablehttp_client(WEATHER_URL))

# Initialize MCP clients
def init_mcp_clients():
    global mcp_clients

    logger.info("Initializing MCP clients")

    # Create Weather MCP client
    try:
        weather_client = MCPClient(lambda: streamablehttp_client(WEATHER_URL))
        mcp_clients["Weather"] = weather_client
        logger.info(f"Successfully created MCP client for Weather at {WEATHER_URL}")
    except Exception as e:
        logger.error(f"Error creating MCP client for Weather: {e}", exc_info=True)
        print(f"Error: Failed to create MCP client for Weather: {e}")

    # Add more MCP clients as needed

    if mcp_clients:
        logger.info(f"Successfully initialized {len(mcp_clients)} MCP clients")
    else:
        logger.warning("No MCP clients were successfully initialized")

# Get available tools from MCP servers
def get_available_tools():
    tools_info = {}

    for name, client in mcp_clients.items():
        try:
            tools = client.list_tools_sync()
            tools_info[name] = [tool.tool_name for tool in tools]
            logger.info(f"Available tools from {name}: {tools_info[name]}")
        except Exception as e:
            logger.error(f"Error getting tools from {name}: {e}", exc_info=True)

    return tools_info

def parse_mcp_response(response):
    """Parse response from MCP tool call"""
    try:
        # If response is already a string, return it directly
        if isinstance(response, str):
            return response

        # If response is a dictionary, try to extract text content
        if isinstance(response, dict):
            # Check for common response patterns
            if "result" in response:
                result = response["result"]
                # Handle string result
                if isinstance(result, str):
                    return result
                # Handle dictionary result
                elif isinstance(result, dict):
                    if "text" in result:
                        return result["text"]
                    elif "content" in result:
                        return result["content"]
                    elif "message" in result:
                        return result["message"]

            # Check for content directly in response
            if "text" in response:
                return response["text"]
            elif "content" in response:
                return response["content"]
            elif "message" in response:
                return response["message"]

        # If response is JSON string, parse it and try again
        if isinstance(response, str) and (response.startswith('{') or response.startswith('[')):
            try:
                parsed = json.loads(response)
                return parse_mcp_response(parsed)
            except json.JSONDecodeError:
                pass

        # If we can't parse it in a structured way, convert to string
        return str(response)
    except Exception as e:
        logger.error(f"Error parsing MCP response: {e}", exc_info=True)
        return f"Error parsing response: {str(e)}"

@tool
def get_weather(task: str) -> str:
    """Send a message to the Weather MCP server to get accurate weather information

    Args:
        task: The weather query including location, time period, and specific weather attributes needed
    Returns:
        Weather information from the Weather MCP server
    """
    with weather_client as client:
        tools = client.list_tools_sync()

        # Look for a tool that can handle weather queries
        weather_tool = None
        for tool in tools:
            if "weather" in tool.tool_name.lower() or "forecast" in tool.tool_name.lower():
                weather_tool = tool.tool_name
                break

        if not weather_tool:
            logger.warning("No suitable weather tool found in Weather MCP server")
            weather_tool = tools[0].tool_name if tools else None

        if not weather_tool:
            return "Error: No tools available in the Weather service"

        logger.info(f"Using tool '{weather_tool}' to get weather information")

        raw_result = client.call_tool_sync(weather_tool, task)
        logger.info("Weather information successfully retrieved")
        logger.info(f"Raw result: {raw_result}")

        # Parse the response to extract text content
        result = parse_mcp_response(raw_result)
        logger.info("Successfully parsed weather information")
        logger.info(f"Parsed result (truncated): {result[:100]}..." if len(result) > 100 else result)

        return result

    try:
        if "Weather" not in mcp_clients:
            logger.error("Weather MCP client not available")
            return "Error: Weather service is not available"

        # Find the appropriate tool in the Weather MCP server
        client = mcp_clients["Weather"]
        tools = client.list_tools_sync()

        # Look for a tool that can handle weather queries
        weather_tool = None
        for tool in tools:
            if "weather" in tool.tool_name.lower() or "forecast" in tool.tool_name.lower():
                weather_tool = tool.tool_name
                break

        if not weather_tool:
            logger.warning("No suitable weather tool found in Weather MCP server")
            weather_tool = tools[0].tool_name if tools else None

        if not weather_tool:
            return "Error: No tools available in the Weather service"

        logger.info(f"Using tool '{weather_tool}' to get weather information")

        raw_result = client.call_tool_sync(weather_tool, task)
        logger.info("Weather information successfully retrieved")
        logger.debug(f"Raw result: {raw_result}")

        # Parse the response to extract text content
        result = parse_mcp_response(raw_result)
        logger.info("Successfully parsed weather information")
        logger.debug(f"Parsed result (truncated): {result[:100]}..." if len(result) > 100 else result)

        return result
    except Exception as e:
        logger.error(f"Error getting weather information: {e}", exc_info=True)
        return f"Error retrieving weather information: {str(e)}"

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

def main():
    logger.info("Starting Travel Planning Assistant")

    try:
        # Initialize MCP clients
        #init_mcp_clients()

        # Get available tools
        available_tools = get_available_tools()
        logger.info(f"Available tools: {available_tools}")

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

if __name__ == "__main__":
    logger.info("Application starting")
    # Run the main function
    try:
        main()
        logger.info("Application completed successfully")
    except Exception as e:
        logger.critical(f"Unhandled exception in main application: {e}", exc_info=True)
        print(f"Critical error: {str(e)}")
