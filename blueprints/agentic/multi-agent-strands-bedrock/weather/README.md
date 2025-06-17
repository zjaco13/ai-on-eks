# Weather Agent

A weather assistant built with Strands Agents and MCP (Model Context Protocol) for providing weather forecasts and alerts.

## Features

- Weather forecasts and alerts
- Interactive weather assistant
- MCP server integration

## Usage

```bash
# Install dependencies
uv sync

# Run as mcp server
uvx --no-cache --from . --directory . weather-agent-mcp-server --transport streamable-http

# Run interactive mode
uvx --no-cache --from . --directory . weather-agent-interactive
```
