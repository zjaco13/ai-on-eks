from strands import Agent, tool
from .weather import weather_assistant
from .itinerary import itinerary_assistant

# Define the orchestrator system prompt with clear tool selection guidance
MAIN_SYSTEM_PROMPT = """
You are a travel planning assistant that routes queries to specialized agents:
- For weather questions -> use the weather_assistant tool
- For itinerary questions -> use the itenrary_assistant tool
- For simple questions not requiring specialized knowledge → Answer directly

Always select the most appropriate tool based on the user's query.
"""

@tool
def trip_planning_assistant(query: str) -> str:

    orchestrator = Agent(
        system_prompt=MAIN_SYSTEM_PROMPT,
        callback_handler=None,
        tools=[weather_assistant, itinerary_assistant]
    )
    response = orchestrator(query)
    text_resp = str(response)

    if len(text_resp) > 0:
        return text_resp
    return "I apologize, I could not perform your request."
