# AI Agent Technical Reference - Weather Agent Project

> **For AI Agents Only**: This file contains technical implementation details for AI assistants.
> **Humans should refer to README.md** for complete deployment instructions and tutorials.

## 🎯 Project State Summary

**Current Status**: Production-ready triple-protocol AI agent with EKS deployment capability
**Key Achievement**: Single container serving MCP (port 8080), A2A (port 9000), and REST API (port 3000) protocols concurrently

## 🏗️ Technical Architecture

### Core Implementation
- **Triple Server**: ThreadPoolExecutor-based concurrent MCP/A2A/REST API servers in `main.py`
- **Default Transport**: streamable-http (changed from stdio for container compatibility)
- **Multi-Architecture**: AMD64/ARM64 support via docker buildx
- **Security**: EKS Pod Identity for Bedrock access (no credential storage)

### File Structure (AI Agent Reference)
```
weather/
├── agent.py                 # Core weather agent logic
├── agent_mcp_server.py      # MCP server (port 8080)
├── agent_a2a_server.py      # A2A server (port 9000)
├── agent_restapi.py         # REST API server (port 3000)
├── main.py                  # Entry points + triple server orchestrator
├── test_mcp_client.py       # MCP protocol test client
├── test_a2a_client.py       # A2A protocol test client
├── test_rest_api.py         # REST API test client
├── Dockerfile               # Multi-arch container (agent)
├── helm/                    # Kubernetes deployment charts
├── mcp-servers/             # MCP tool definitions
│   └── weather-mcp-server/  # Weather MCP server
├── pyproject.toml          # Entry points configuration
├── README.md               # Human-readable deployment tutorial
└── AmazonQ.md              # This file - AI Agent technical reference
```

## 🔧 Critical Technical Decisions (AI Context)

### 1. Triple Server Architecture
- **Implementation**: `servers()` using ThreadPoolExecutor with 3 workers
- **Rationale**: Reuses existing server code without duplication
- **Entry Point**: `agent` (default Docker CMD)

### 2. Transport Protocol Change
- **Change**: `agent_mcp_server.py` default from `stdio` → `streamable-http`
- **Impact**: Eliminates need for CLI args in container deployment
- **Compatibility**: Maintains stdio support via `--transport stdio`

### 3. REST API Integration
- **Implementation**: Flask-based REST API in `agent_restapi.py`
- **Integration**: Uses existing `weather_assistant()` function from `agent.py`
- **Endpoints**: `/health`, `/chat`

### 4. Multi-Architecture Build Strategy
- **Issue Resolved**: `exec format error` on mixed EKS node types
- **Solution**: `docker buildx --platform linux/amd64,linux/arm64`
- **Verification**: `docker manifest inspect <image>`

## 🚀 Entry Points Configuration

```python
# pyproject.toml [project.scripts]
"mcp-server"  = "main:main_mcp_server"    # MCP only
"a2a-server"  = "main:main_a2a_server"    # A2A only
"rest-api"    = "main:main_rest_api"      # REST API only
"interactive" = "main:main_interactive"    # CLI mode
"agent" = "main:servers"    # All three servers (DEFAULT)
```

```dockerfile
# Dockerfile
CMD ["agent"]
```

## 🐳 Container Environment

### Required Environment Variables
```bash
MCP_PORT=8080                                                    # MCP server port
A2A_PORT=9000                                                    # A2A server port
REST_API_PORT=3000                                               # REST API server port
BEDROCK_MODEL_ID=us.anthropic.claude-3-7-sonnet-20250219-v1:0  # Bedrock model
AWS_REGION=us-west-2                                            # AWS region
```

### Build Commands (AI Reference)
```bash
# Multi-arch build and push
docker buildx build --platform linux/amd64,linux/arm64 -t ${ECR_REPO_URI}:latest --push .

# Local testing
docker build -t weather-agent .
docker run -p 8080:8080 -p 9000:9000 -p 3000:3000 -e AWS_REGION=us-west-2 weather-agent
```

## 🔍 AI Agent Troubleshooting Database

### Issue: Architecture Mismatch
- **Symptom**: `exec format error` in pod logs
- **Root Cause**: Single-arch image on incompatible node
- **Fix**: Verify multi-arch with `docker manifest inspect`
- **Prevention**: Always use `--platform linux/amd64,linux/arm64`

### Issue: Health Check Failures
- **Symptom**: Pod CrashLoopBackOff, health check timeouts
- **Root Cause**: Wrong transport or port configuration
- **Fix**: Ensure streamable-http transport and correct ports (8080/9000)
- **Debug**: Check `kubectl logs deployment/weather-agent`

### Issue: Single Protocol Access
- **Symptom**: Only MCP or A2A accessible, not both
- **Root Cause**: Wrong entry point in Dockerfile
- **Fix**: Ensure `CMD ["agent"]`
- **Verification**: Test both `curl localhost:8080` and `curl localhost:9000`

### Issue: REST API Not Responding
- **Symptom**: REST API endpoints return 404 or connection refused
- **Root Cause**: Flask dependency missing or wrong port configuration
- **Fix**: Ensure Flask is installed and REST_API_PORT=3000
- **Verification**: Test `curl localhost:3000/health`

### Issue: Mermaid Diagram Rendering
- **Symptom**: "Unsupported markdown: list" in GitHub
- **Root Cause**: Numbered arrows or HTML tags in diagram
- **Fix**: Use plain text labels, avoid `1.`, `2.`, `<br/>` tags

## 🧪 Test Client Architecture (AI Reference)

### Test Client Design Pattern
All three test clients follow a consistent architecture:

```python
# Common pattern across all test clients
async def wait_for_server(base_url: str, timeout: int = 30):
    """Wait for server availability with timeout"""

async def test_protocol(base_url: str):
    """Main test function with numbered tests"""
    print(f"Testing Protocol at {base_url}")
    print("=" * 50)

    # Test 1: Basic connectivity
    # Test 2: Protocol handshake
    # Test 3-N: Functionality tests

    print("=" * 50)
    print("Protocol testing completed!")

def main():
    """Entry point with server checking"""
```

### MCP Test Client (`test_mcp_client.py`)
- **Protocol**: StreamableHTTP with SSE
- **Tests**: 6 tests (0-5)
- **Key Features**: Session initialization, tool discovery, tool execution
- **Connection**: `streamablehttp_client()` with proper tuple unpacking

### A2A Test Client (`test_a2a_client.py`)
- **Protocol**: HTTP with JSON-RPC
- **Tests**: 6 tests (1-6)
- **Key Features**: Agent card discovery, client initialization, message sending
- **Connection**: `A2ACardResolver` and `A2AClient`

### REST API Test Client (`test_rest_api.py`)
- **Protocol**: HTTP REST
- **Tests**: 4 tests (1-4)
- **Key Features**: Health checks, chat endpoints, error handling
- **Connection**: Standard `requests` library

### Test Output Consistency
```
Testing [Protocol] at [URL]
==================================================
1. Testing [feature]...
✅ [Feature] successful
   [Details]

2. Testing [feature]...
✅ [Feature] successful
   [Details]
==================================================
[Protocol] testing completed!
```

## 🧪 Triple Protocol Test Suite

### Professional Test Clients
All three test clients provide consistent user experience:
- **Server Readiness**: Automatic availability checking with timeouts
- **Structured Output**: Numbered tests with ✅/❌ indicators
- **Comprehensive Coverage**: Protocol-specific functionality testing
- **Error Handling**: Graceful failure handling and clear messages
- **Response Formatting**: Clean preview of responses with truncation

### MCP Test Client (`test_mcp_client.py`)
```bash
# Tests: 6 comprehensive MCP protocol tests (0-5)
uv run test_mcp_client.py
```
**Test Coverage:**
- HTTP connectivity and SSE validation
- MCP session initialization and protocol negotiation
- Tool discovery with parameter enumeration
- Weather forecast tool execution
- Weather alert tool execution
- Complex multi-city weather comparisons

### A2A Test Client (`test_a2a_client.py`)
```bash
# Tests: 6 comprehensive A2A protocol tests (1-6)
uv run test_a2a_client.py
```
**Test Coverage:**
- Agent card discovery and capabilities
- A2A client initialization and connection
- Weather forecast queries with formatted responses
- Weather alert queries with response validation
- Invalid message format handling
- Full response display with markdown rendering

### REST API Test Client (`test_rest_api.py`)
```bash
# Tests: 4 comprehensive REST API tests (1-4)
uv run test_rest_api.py
```
**Test Coverage:**
- Health check endpoint validation
- Chat endpoint with weather queries
- 404 error handling for invalid endpoints
- 400 error handling for malformed requests

### Test Suite Execution
```bash
# Start triple server
uv run agent

# Run all tests (in separate terminals)
uv run test_mcp_client.py     # Port 8080
uv run test_a2a_client.py     # Port 9000
uv run test_rest_api.py       # Port 3000
```

### Development Testing
```bash
# Test triple server locally
uv run agent

# Test individual protocols
uv run mcp-server --transport stdio
uv run a2a-server
uv run rest-api

# Protocol verification
uv run test_mcp_client.py            # MCP: http://localhost:8080/mcp
uv run test_a2a_client.py            # A2A: http://localhost:9000
uv run test_rest_api.py              # REST API: http://localhost:3000

# Alternative MCP Inspector
npx @modelcontextprotocol/inspector  # MCP: http://localhost:8080/mcp

```

### EKS Operations
```bash
# Deployment status
kubectl get pods -l app.kubernetes.io/instance=weather-agent
kubectl logs deployment/weather-agent

# Debug commands
kubectl describe pod <pod-name>
kubectl get events --sort-by=.metadata.creationTimestamp

# Port forwarding for testing
kubectl port-forward service/weather-agent 8080:8080 9000:9000 3000:3000

# Test all protocols
uv run test_mcp_client.py     # MCP Protocol validation
uv run test_a2a_client.py     # A2A Protocol validation
uv run test_rest_api.py       # REST API validation
```

## 🎯 AI Agent Workflow Guidelines

### Before Making Changes
1. Read both AmazonQ.md (this file) and README.md
2. Identify which documentation sections will be affected
3. Note current entry points and configuration

### During Implementation
1. Test changes locally with `agent`
2. Verify all protocols work (MCP:8080, A2A:9000, REST:3000)
3. Update entry points if pyproject.toml changes
4. Test multi-architecture builds if Dockerfile changes

### After Changes
1. Update technical details in AmazonQ.md
2. Update user instructions in README.md
3. Verify all command examples work
4. Test container build and deployment

## 🔗 Key Resources (AI Reference)

- **EKS Cluster**: `agents-on-eks` (us-west-2)
- **ECR Repository**: `agents-on-eks/weather-agent`
- **Bedrock Model**: `us.anthropic.claude-3-7-sonnet-20250219-v1:0`
- **MCP Inspector**: `npx @modelcontextprotocol/inspector`
- **A2A Test Client**: `uv run test_a2a_client.py`
- **REST API Test Client**: `uv run test_rest_api.py`

---

## 🤖 AI Agent Documentation Maintenance Protocol

### CRITICAL: Dual Documentation Strategy

**AmazonQ.md (This File)**:
- Technical implementation details
- Troubleshooting database
- Quick command reference
- Architecture decisions
- AI Agent workflow guidance

**README.md**:
- Complete human-readable tutorial
- Step-by-step deployment instructions
- Prerequisites and explanations
- Architecture diagrams
- User-facing documentation

### Synchronization Requirements

When making changes, AI Agents MUST update both files:

#### AmazonQ.md Updates:
- [ ] Entry points table if pyproject.toml changes
- [ ] Docker CMD if Dockerfile changes
- [ ] Quick commands with new entry points
- [ ] Technical decisions for architectural changes
- [ ] Troubleshooting database for new issues
- [ ] File structure if files added/renamed

#### README.md Updates:
- [ ] Command examples with new entry points
- [ ] Environment variables if added/changed
- [ ] Deployment steps if process changes
- [ ] Prerequisites if tools/versions change
- [ ] Architecture diagram if structure changes
- [ ] Troubleshooting table for user-facing issues

### Critical Consistency Points
These MUST be identical across both files:
- Entry point names (`mcp-server`, `a2a-server`, etc.)
- Port numbers (8080 for MCP, 9000 for A2A, 3000 for REST API)
- Environment variables (BEDROCK_MODEL_ID, AWS_REGION, etc.)
- Resource names (cluster, IAM roles, ECR repositories)

### Common AI Agent Mistakes to Avoid
1. **Updating only one file** - Always update both
2. **Inconsistent commands** - Test all examples
3. **Outdated entry points** - Check pyproject.toml references
4. **Missing environment variables** - Document all required vars
5. **Broken container builds** - Verify multi-arch support

---

**AI Agent Status**: This project is production-ready with comprehensive triple-protocol support and EKS deployment capability. All technical implementation details are documented above for AI Agent reference.

