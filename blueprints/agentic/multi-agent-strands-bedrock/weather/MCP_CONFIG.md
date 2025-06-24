# MCP Configuration Guide

The Weather Agent now supports dynamic loading of MCP (Model Context Protocol) tools from multiple servers using the `mcp.json` configuration file.

## Configuration File Structure

The `mcp.json` file defines multiple MCP servers that the agent can connect to:

```json
{
  "mcpServers": {
    "server-name": {
      "disabled": false,
      "timeout": 60000,
      "url": "http://server:8080/mcp"  // For HTTP servers
    },
    "another-server": {
      "disabled": false,
      "timeout": 60000,
      "command": "python",             // For stdio servers
      "args": ["-m", "package", "--transport", "stdio"],
      "env": {                         // Optional environment variables
        "LOG_LEVEL": "DEBUG",
        "CONFIG_PATH": "/path/to/config"
      }
    }
  }
}
```

## Server Configuration Options

### HTTP/Streamable-HTTP Servers
For MCP servers that expose an HTTP endpoint:

```json
{
  "server-name": {
    "disabled": false,
    "timeout": 60000,
    "url": "http://localhost:8080/mcp"
  }
}
```

### Stdio Servers
For MCP servers that communicate via stdin/stdout:

```json
{
  "server-name": {
    "disabled": false,
    "timeout": 60000,
    "command": "uvx",
    "args": [
      "--from", ".",
      "--directory","mcp-servers/my-server",
      "mcp-server",
      "--transport", "stdio"
    ],
    "env": {
      "DEBUG": "1",
      "LOG_LEVEL": "INFO",
      "CUSTOM_VAR": "value"
    }
  }
}
```

## Configuration Properties

- **disabled**: Set to `true` to skip loading this server
- **timeout**: Connection timeout in milliseconds
- **url**: HTTP endpoint for streamable-http transport
- **command**: Executable command for stdio transport
- **args**: Command line arguments for stdio transport
- **env**: (Optional) Environment variables to pass to stdio servers

## Environment Variables Support

For stdio-based MCP servers, you can specify custom environment variables using the `env` property:

```json
{
  "my-mcp-server": {
    "disabled": false,
    "timeout": 60000,
    "command": "python",
    "args": ["-m", "my_mcp_server"],
    "env": {
      "FASTMCP_LOG_LEVEL": "ERROR",
      "DATABASE_URL": "sqlite:///data.db",
      "API_KEY": "your-api-key",
      "DEBUG": "1"
    }
  }
}
```

### Common Environment Variables

Different MCP servers may use different environment variables. Here are some common examples:

- **Logging**: `LOG_LEVEL`, `DEBUG`, `FASTMCP_LOG_LEVEL`
- **Configuration**: `CONFIG_PATH`, `SETTINGS_FILE`
- **API Keys**: `API_KEY`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`
- **Database**: `DATABASE_URL`, `DB_HOST`, `DB_PORT`
- **Paths**: `DATA_DIR`, `CACHE_DIR`, `TEMP_DIR`

## How It Works

1. The agent reads `mcp.json` on startup
2. For each enabled server, it creates an appropriate MCP client:
   - **HTTP servers**: Uses `streamablehttp_client(url)`
   - **Stdio servers**: Uses `stdio_client(StdioServerParameters(command, args, env))`
3. Environment variables (if specified) are passed to the stdio server process
4. Connects to each server and retrieves available tools
5. Combines all tools from all servers into a single tool list
6. Creates the Weather Agent with the combined tool set

## Adding New MCP Servers

To add a new MCP server:

1. Add a new entry to the `mcpServers` object in `mcp.json`
2. Configure the appropriate connection method (URL or command/args)
3. Add any required environment variables for stdio servers
4. Set `disabled: false` to enable the server
5. Restart the agent to load the new tools

## Example: Adding Multiple Servers with Environment Variables

```json
{
  "mcpServers": {
    "weather-local": {
      "disabled": false,
      "timeout": 60000,
      "command": "uvx",
      "args": ["--directory", "mcp-servers/weather", "mcp-server"],
      "env": {
        "WEATHER_API_KEY": "your-weather-api-key",
        "LOG_LEVEL": "INFO"
      }
    },
    "calendar-remote": {
      "disabled": false,
      "timeout": 30000,
      "url": "http://calendar-service:8080/mcp"
    },
    "database-tools": {
      "disabled": false,
      "timeout": 45000,
      "command": "python",
      "args": ["-m", "db_mcp_server", "--transport", "stdio"],
      "env": {
        "DATABASE_URL": "postgresql://user:pass@localhost/db",
        "FASTMCP_LOG_LEVEL": "ERROR"
      }
    },
    "ai-assistant": {
      "disabled": false,
      "timeout": 60000,
      "command": "node",
      "args": ["ai-mcp-server.js"],
      "env": {
        "OPENAI_API_KEY": "sk-...",
        "MODEL": "gpt-4",
        "DEBUG": "true"
      }
    },
    "experimental-server": {
      "disabled": true,
      "timeout": 30000,
      "url": "http://experimental:8080/mcp"
    }
  }
}
```

## Troubleshooting

### Server Connection Issues
- Check that HTTP servers are accessible at the specified URL
- Verify that stdio commands and arguments are correct
- Ensure all required dependencies are installed
- Check that environment variables are properly set

### Environment Variable Issues
- Verify that environment variable names are correct
- Check that sensitive values (API keys) are properly configured
- Ensure the MCP server supports the environment variables you're setting
- Use logging environment variables to debug server startup issues

### Tool Loading Errors
- Check the agent logs for specific error messages
- Verify that MCP servers are properly implementing the MCP protocol
- Test individual servers independently before adding to configuration
- Check server logs if environment variables enable logging

### Performance Considerations
- Set appropriate timeouts for each server
- Disable unused servers to improve startup time
- Consider the total number of tools when adding multiple servers
- Be mindful of environment variables that might affect performance

## Security Considerations

When using environment variables:

1. **API Keys**: Store sensitive values securely, consider using environment variable substitution
2. **File Paths**: Ensure paths are accessible and secure
3. **Database URLs**: Use secure connection strings
4. **Logging**: Be careful not to log sensitive information

## Migration from Environment Variables

The old environment variable approach (`MCP_SERVER_URL`, `MCP_SERVER_LOCATION`) is still supported as a fallback, but the `mcp.json` configuration is recommended for:

- Multiple server support
- Better configuration management
- Easier server enable/disable
- More flexible connection options
- Environment variable management per server
