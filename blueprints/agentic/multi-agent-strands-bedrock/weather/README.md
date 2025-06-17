# Weather Agent

A weather assistant built with Strands Agents, MCP (Model Context Protocol), and A2A (Agent to Agent) for providing weather forecasts and alerts.

## Features

- Weather forecasts and alerts
- Interactive Weather Agent
- MCP server for Weather Agent as MCP Tool
- A2A server exposing the Weather Agent

## Usage

# Install dependencies
```bash
uv sync
```


# Run interactive mode
```bash
uv run interactive.py

# or

uvx --no-cache --from . --directory . weather-agent-interactive
```

# Run as mcp server
```bash
uv run mcp_server.py

# or

uvx --no-cache --from . --directory . weather-agent-mcp-server --transport streamable-http
```

# Run as a2a server
```bash
uv run a2a_server.py

# or

uvx --no-cache --from . --directory . weather-agent-a2a-server
```

# Run the a2a client
```bash
uv run a2a_client.py
```
