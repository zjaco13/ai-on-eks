# Weather Agent REST API - Session Management Guide

The Weather Agent REST API now includes comprehensive session management capabilities, allowing for stateful conversations with conversation history and context preservation.

## 🚀 Key Features

- **Session State Management**: Automatic session creation and management using Flask sessions
- **Conversation History**: Persistent conversation history within sessions
- **Context Awareness**: Agent maintains context across multiple requests in the same session
- **Optional API Key Authentication**: Configurable API key protection
- **Session Persistence**: Sessions persist across requests using secure cookies

## 📋 API Endpoints

### Core Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check and feature information |
| `/chat` | POST | Send a message to the weather agent |
| `/chat/history` | GET | Retrieve conversation history for current session |
| `/chat/clear` | POST | Clear conversation history for current session |
| `/session/info` | GET | Get information about the current session |

### Authentication

All endpoints (except `/health`) support optional API key authentication via:
- **Header**: `X-API-Key: your-api-key`
- **Query Parameter**: `?api_key=your-api-key`

## 🔧 Configuration

### Environment Variables

```bash
# Server Configuration
REST_API_HOST=0.0.0.0          # Server host (default: 0.0.0.0)
REST_API_PORT=3000             # Server port (default: 3000)
DEBUG=false                    # Debug mode (default: false)

# Session Configuration
FLASK_SECRET_KEY=your-secret   # Flask session secret (auto-generated if not set)

# Authentication Configuration (Optional)
REQUIRE_API_KEY=false          # Enable API key authentication (default: false)
API_KEY=your-api-key          # API key for authentication (required if REQUIRE_API_KEY=true)

# Bedrock Configuration
BEDROCK_MODEL_ID=us.anthropic.claude-3-7-sonnet-20250219-v1:0
AWS_REGION=us-west-2
```

## 🔄 Session Management Flow

### 1. Session Creation
- First request automatically creates a new session
- Session ID is generated and stored in secure cookie
- Agent instance is created and cached for the session

### 2. Conversation Context
- Each message is stored in session conversation history
- Agent receives context from previous 5 exchanges
- Context helps maintain conversation continuity

### 3. Session Persistence
- Sessions persist across requests using Flask sessions
- Conversation history is maintained in session storage
- Agent instances are cached per session for consistency

## 💻 Usage Examples

### Basic Usage (No API Key)

```python
import requests

# Create a session to maintain cookies
session = requests.Session()
base_url = "http://localhost:3000"

# First chat - creates session
response = session.post(f"{base_url}/chat", json={
    "query": "What's the weather forecast for Seattle?"
})
result = response.json()
print(f"Session ID: {result['session_id']}")
print(f"Response: {result['response']}")

# Follow-up chat - uses same session and context
response = session.post(f"{base_url}/chat", json={
    "query": "Any weather alerts?"  # Agent knows to check Seattle from previous context
})
result = response.json()
print(f"Response: {result['response']}")

# Get conversation history
history = session.get(f"{base_url}/chat/history").json()
print(f"Total exchanges: {history['total_exchanges']}")
```

### With API Key Authentication

```python
import requests

# Set up session with API key
session = requests.Session()
session.headers.update({"X-API-Key": "your-api-key"})

# Use same endpoints as above
response = session.post("http://localhost:3000/chat", json={
    "query": "Are there any weather alerts for Miami?"
})
```

### Using the Test Client

```bash
# Run the comprehensive test suite
python test_rest_api.py
```

## 📊 API Response Formats

### Chat Response
```json
{
    "session_id": "abc123def456",
    "query": "What's the weather forecast for Seattle?",
    "response": "Here's the weather forecast for Seattle...",
    "conversation_length": 2
}
```

### Conversation History Response
```json
{
    "session_id": "abc123def456",
    "conversation_history": [
        {
            "query": "What's the weather forecast for Seattle?",
            "response": "Here's the weather forecast...",
            "timestamp": "1234567890.123"
        }
    ],
    "total_exchanges": 1
}
```

### Session Info Response
```json
{
    "session_id": "abc123def456",
    "conversation_length": 2,
    "has_agent": true,
    "session_data_keys": ["session_id", "conversations"]
}
```

## 🧪 Testing

### Comprehensive Test Suite

The updated test suite includes 9 comprehensive tests:

```bash
# Run all tests
uv run test_rest_api.py

# Tests include:
# 1. Health check endpoint
# 2. First chat request (session creation)
# 3. Second chat request (context awareness - asks "Any weather alerts?" expecting agent to remember Seattle)
# 4. Conversation history retrieval
# 5. Session info endpoint
# 6. Clear conversation history
# 7. Verify history was cleared
# 8. Invalid endpoint (404 handling)
# 9. Invalid request body (400 handling)
```

### Example Client Demo

```bash
# Run the comprehensive test suite
uv run test_rest_api.py

# Demonstrates:
# - Session creation and management
# - Conversation context preservation
# - History retrieval and clearing
# - Error handling and validation
```

## 🔒 Security Considerations

### Session Security
- Sessions use secure, randomly generated secret keys
- Session cookies are HTTP-only to prevent XSS attacks
- Session data is server-side only (not exposed to client)

### API Key Authentication
- Optional API key authentication for production use
- Keys can be provided via headers or query parameters
- Failed authentication returns 401 Unauthorized

### Production Recommendations
```bash
# Set secure session configuration for production
export FLASK_SECRET_KEY="your-long-random-secret-key"
export REQUIRE_API_KEY=true
export API_KEY="your-secure-api-key"

# Use HTTPS in production for secure cookie transmission
```

## 🚀 Deployment

### Local Development
```bash
# Start without API key
uv run rest-api

# Start with API key authentication
export REQUIRE_API_KEY=true
export API_KEY=test-key-12345
uv run rest-api
```

### Container Deployment
```bash
# Build and run with session management
docker build -t weather-agent .
docker run -p 3000:3000 \
  -e FLASK_SECRET_KEY=your-secret-key \
  -e REQUIRE_API_KEY=true \
  -e API_KEY=your-api-key \
  weather-agent rest-api
```

### Kubernetes Deployment
The session management works seamlessly with the existing Kubernetes deployment. Sessions are maintained per pod, so consider:

- **Sticky Sessions**: Use session affinity if running multiple replicas
- **Session Storage**: Consider external session storage (Redis) for multi-pod deployments
- **Secret Management**: Use Kubernetes secrets for API keys and session secrets

## 🔧 Advanced Configuration

### Session Limits
- Conversation history is limited to last 20 exchanges per session
- Context window uses last 5 exchanges for agent prompts
- Sessions expire after 1 hour of inactivity

### Customization
```python
# Modify session configuration in agent_restapi.py
self.app.config.update(
    SESSION_COOKIE_SECURE=True,     # Enable for HTTPS
    SESSION_COOKIE_HTTPONLY=True,   # Prevent XSS
    SESSION_COOKIE_SAMESITE='Lax',  # CSRF protection
    PERMANENT_SESSION_LIFETIME=7200  # 2 hours
)
```

## 📈 Monitoring and Logging

The API provides detailed logging for:
- Session creation and management
- Agent instantiation per session
- Conversation history operations
- Authentication attempts
- Error conditions

Monitor these logs for:
- Session usage patterns
- Authentication failures
- Performance bottlenecks
- Error rates

## 🤝 Integration Examples

### Web Frontend Integration
```javascript
// JavaScript example for web frontend
class WeatherAPIClient {
    constructor(baseUrl, apiKey = null) {
        this.baseUrl = baseUrl;
        this.apiKey = apiKey;
    }

    async chat(query) {
        const headers = {'Content-Type': 'application/json'};
        if (this.apiKey) {
            headers['X-API-Key'] = this.apiKey;
        }

        const response = await fetch(`${this.baseUrl}/chat`, {
            method: 'POST',
            headers: headers,
            credentials: 'include', // Important for session cookies
            body: JSON.stringify({query})
        });

        return response.json();
    }
}
```

### Mobile App Integration
- Use session cookies or implement custom session management
- Store session ID locally and include in requests
- Handle authentication tokens securely

This session management implementation follows the Strands Agents documentation patterns and provides a robust foundation for stateful weather agent interactions.
