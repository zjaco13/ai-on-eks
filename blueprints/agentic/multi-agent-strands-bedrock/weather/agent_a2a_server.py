from strands import Agent
from multiagent.a2a import A2AAgent
from agent import get_weather_agent as get_agent

def weather_a2a_server():
    strands_agent = get_agent()
    strands_a2a_agent = A2AAgent(agent=strands_agent, name="Weather Agent", description="Weather Agent for forecast and alert")
    strands_a2a_agent.serve()


if __name__ == "__main__":
    weather_a2a_server()
