import os

from mcp import StdioServerParameters, stdio_client
from strands import Agent, tool
from strands.models import BedrockModel
from strands.tools.mcp import MCPClient

@tool
def weather_assistant_tool(query: str) -> str:
    """
    Process and respond Weather forecast or alerts

    Args:
        query: The user's question

    Returns:
        A helpful response addressing user query
    """
    return weather_assistant(query)


def weather_assistant(query: str) -> str:
    """
    Process and respond Weather forecast or alerts

    Args:
        query: The user's question

    Returns:
        A helpful response addressing user query
    """
    #model_id = "us.anthropic.claude-3-5-haiku-20241022-v1:0"
    model_id = os.getenv("BEDROCK_MODEL_ID", "us.anthropic.claude-3-7-sonnet-20250219-v1:0")
    bedrock_model = BedrockModel(model_id=model_id)

    response = str()

    try:
        env = {}
        if os.getenv("BEDROCK_LOG_GROUP_NAME") is not None:
            env["BEDROCK_LOG_GROUP_NAME"] = os.getenv("BEDROCK_LOG_GROUP_NAME")

        stdio_mcp_client = MCPClient(
            lambda: stdio_client(
            StdioServerParameters(
                command="uvx",
                args=["--from",".","--directory","weather-mcp-server","weather-mcp"]
            )
        ))

        with stdio_mcp_client:

            tools = stdio_mcp_client.list_tools_sync()
            # Create the research agent with specific capabilities
            weather_agent = Agent(
                model=bedrock_model,
                system_prompt="""You are Weather Assistant helps the user with:
                - weather forecast an US City for next 3 days, if not specify
                - alerts given an US City
                """,
                tools=tools,
            )
            response = str(weather_agent(query))
            print("\n\n")

        if len(response) > 0:
            return response

        return "I apologize, but I couldn't properly analyze your question. Could you please rephrase or provide more context?"

    except Exception as e:
        return f"Error processing your query: {str(e)}"


if __name__ == "__main__":
  weather_assistant("Get the weather for Seattle")
