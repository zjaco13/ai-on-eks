# Multi-Agent Strands Bedrock Orchestrator

This project demonstrates a travel planning assistant that orchestrates information between specialized agents using AWS Bedrock and the Strands framework. The orchestrator agent delegates specific information requests to specialized agents (currently a Weather Agent) and compiles comprehensive travel plans.

## Overview

The Travel Orchestration Agent is designed to:

1. Coordinate with specialized agents to gather domain-specific information
2. Delegate weather-related queries to a dedicated Weather Agent
3. Compile comprehensive travel plans with properly attributed information
4. Follow strict protocols for information delegation and attribution

## Project Structure

- `mcp_agent.py`: Implementation using the Model-Client-Provider (MCP) protocol
- `a2a_agent.py`: Implementation using the Agent-to-Agent (A2A) protocol
- `system.md`: System prompt defining the agent's behavior and protocols
- `main.py`: Simple entry point for the application

## Key Features

- **Specialized Agent Delegation**: Delegates domain-specific queries to specialized agents
- **Weather Information Protocol**: Strict guidelines for obtaining and attributing weather information
- **Configurable System Prompt**: System behavior defined in a separate markdown file for easy updates
- **Multiple Protocol Support**: Supports both MCP and A2A communication protocols

## Weather Agent Limitations

The Weather Agent has the following limitations:
- Can only provide forecasts for locations within the United States
- Can only provide forecasts for the next 7 days
- Cannot provide weather information for international destinations or dates beyond the next week

## Setup and Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up environment variables:
   ```bash
   export BEDROCK_MODEL_ID=us.anthropic.claude-3-7-sonnet-20250219-v1:0
   export WEATHER_MCP_PORT=8080  # For MCP implementation
   export WEATHER_A2A_PORT=9000  # For A2A implementation
   ```

## Usage

### Running the MCP Agent

```bash
python mcp_agent.py
```

### Running the A2A Agent

```bash
python a2a_agent.py
```

### Example Interactions

```
You: I'm planning a trip to Miami next week. What should I pack?
Assistant: I'll help you plan your trip to Miami next week. Let me check the weather forecast to give you appropriate packing recommendations.

[Using get_weather tool] What is the weather forecast for Miami, Florida for the next 7 days? Please provide temperature ranges, precipitation chances, humidity levels, and any common weather patterns that might affect tourism.

According to the Weather Agent, Miami will experience temperatures ranging from 75°F to 88°F next week, with humidity levels around 70-80%. There's a 30% chance of afternoon thunderstorms on Tuesday and Wednesday, but the rest of the week should be mostly sunny. UV index will be high throughout the week.

Based on this forecast, here's what I recommend packing:

Clothing:
- Lightweight, breathable clothing (t-shirts, shorts, sundresses)
- A light jacket or sweater for air-conditioned places
- Swimwear for the beach or pool
- A rain jacket or small umbrella for possible afternoon showers
- Comfortable walking shoes and sandals

Sun Protection:
- Sunscreen (SPF 30+)
- Sunglasses
- Hat with a brim
- Lip balm with SPF

Other Essentials:
- Refillable water bottle
- Insect repellent
- Beach towel if you plan to visit the beaches
- Any medications you regularly take

Would you like more specific recommendations based on any activities you have planned?
```

## Modifying the System Prompt

The system prompt that defines the agent's behavior is stored in `system.md`. You can modify this file to change how the agent interacts with users and specialized agents without having to modify the Python code.

## Architecture

This project demonstrates two different approaches to multi-agent communication:

1. **MCP Protocol**: Uses the Model-Client-Provider protocol for structured communication between agents
2. **A2A Protocol**: Uses the Agent-to-Agent protocol for direct communication between agents

Both implementations achieve the same goal but use different underlying communication mechanisms.

## Extending the System

To add new specialized agents:

1. Create a new agent implementation with the appropriate expertise
2. Update the system prompt in `system.md` to include protocols for interacting with the new agent
3. Add the necessary tool functions to delegate queries to the new agent
4. Update the main agent implementation to register the new tools

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
