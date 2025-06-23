# AI Agent Technical Reference - Weather Agent Project

> **For AI Agents Only**: This file contains technical implementation details for AI assistants.
> **Humans should refer to README.md** for complete deployment instructions and tutorials.

## 🎯 Project State Summary

**Current Status**: Production-ready dual-protocol AI agent with EKS deployment capability
**Key Achievement**: Single container serving both MCP (port 8080) and A2A (port 9000) protocols concurrently

## 🏗️ Technical Architecture

### Core Implementation
- **Dual Server**: ThreadPoolExecutor-based concurrent MCP/A2A servers in `main.py`
- **Default Transport**: streamable-http (changed from stdio for container compatibility)
- **Multi-Architecture**: AMD64/ARM64 support via docker buildx
- **Security**: EKS Pod Identity for Bedrock access (no credential storage)

### File Structure (AI Agent Reference)
```
weather/
├── agent.py                 # Core weather agent logic
├── agent_mcp_server.py      # MCP server (port 8080)
├── agent_a2a_server.py      # A2A server (port 9000)
├── main.py                  # Entry points + dual server orchestrator
├── Dockerfile               # Multi-arch container (agent)
├── helm/                    # Kubernetes deployment charts
├── weather-mcp-server/      # MCP tool definitions
├── pyproject.toml          # Entry points configuration
├── README.md               # Human-readable deployment tutorial
└── AmazonQ.md              # This file - AI Agent technical reference
```

## 🔧 Critical Technical Decisions (AI Context)

### 1. Multi Server Architecture
- **Implementation**: `server()` using ThreadPoolExecutor
- **Rationale**: Reuses existing server code without duplication
- **Entry Point**: `agent` (default Docker CMD)

### 2. Transport Protocol Change
- **Change**: `agent_mcp_server.py` default from `stdio` → `streamable-http`
- **Impact**: Eliminates need for CLI args in container deployment
- **Compatibility**: Maintains stdio support via `--transport stdio`

### 3. Multi-Architecture Build Strategy
- **Issue Resolved**: `exec format error` on mixed EKS node types
- **Solution**: `docker buildx --platform linux/amd64,linux/arm64`
- **Verification**: `docker manifest inspect <image>`

## 🚀 Entry Points Configuration

```python
# pyproject.toml [project.scripts]
"mcp-server"  = "main:main_mcp_server"    # MCP only
"a2a-server"  = "main:main_a2a_server"    # A2A only
"interactive" = "main:main_interactive"    # CLI mode
"agent" = "main:servers"    # Both servers (DEFAULT)
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
BEDROCK_MODEL_ID=us.anthropic.claude-3-7-sonnet-20250219-v1:0  # Bedrock model
AWS_REGION=us-west-2                                            # AWS region
```

### Build Commands (AI Reference)
```bash
# Multi-arch build and push
docker buildx build --platform linux/amd64,linux/arm64 -t ${ECR_REPO_URI}:latest --push .

# Local testing
docker build -t weather-agent .
docker run -p 8080:8080 -p 9000:9000 -e AWS_REGION=us-west-2 weather-agent
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

### Issue: Mermaid Diagram Rendering
- **Symptom**: "Unsupported markdown: list" in GitHub
- **Root Cause**: Numbered arrows or HTML tags in diagram
- **Fix**: Use plain text labels, avoid `1.`, `2.`, `<br/>` tags

## 📋 AI Agent Quick Commands

### Development Testing
```bash
# Test dual server locally
uv run agent

# Test individual protocols
uv run mcp-server --transport stdio
uv run a2a-server

# Protocol verification
npx @modelcontextprotocol/inspector  # MCP: http://localhost:8080
uv run test_a2a_client.py            # A2A: http://localhost:9000
```

### EKS Operations
```bash
# Deployment status
kubectl get pods -l app.kubernetes.io/instance=weather-agent
kubectl logs deployment/weather-agent

# Debug commands
kubectl describe pod <pod-name>
kubectl get events --sort-by=.metadata.creationTimestamp

# Port forwarding
kubectl port-forward service/weather-agent 8080:8080 9000:9000
```

## 🎯 AI Agent Workflow Guidelines

### Before Making Changes
1. Read both AmazonQ.md (this file) and README.md
2. Identify which documentation sections will be affected
3. Note current entry points and configuration

### During Implementation
1. Test changes locally with `agent`
2. Verify both protocols work (MCP:8080, A2A:9000)
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
- Port numbers (8080 for MCP, 9000 for A2A)
- Environment variables (BEDROCK_MODEL_ID, AWS_REGION, etc.)
- Resource names (cluster, IAM roles, ECR repositories)

### Common AI Agent Mistakes to Avoid
1. **Updating only one file** - Always update both
2. **Inconsistent commands** - Test all examples
3. **Outdated entry points** - Check pyproject.toml references
4. **Missing environment variables** - Document all required vars
5. **Broken container builds** - Verify multi-arch support

---

**AI Agent Status**: This project is production-ready with comprehensive dual-protocol support and EKS deployment capability. All technical implementation details are documented above for AI Agent reference.
