# Amazon Q CLI - Weather Agent Project Summary

## 🎯 Project Overview

This is a **Weather Agent** built with **Strands Agents**, **MCP (Model Context Protocol)**, and **A2A (Agent to Agent)** protocols, designed for deployment on Amazon EKS with Amazon Bedrock integration.

### Key Achievement
Successfully implemented a **dual-server architecture** where a single container runs both MCP and A2A servers concurrently on different ports (8080 and 9000).

## 🏗️ Architecture Summary

### Core Components
- **Weather Agent**: AI-powered assistant using Claude 3.7 Sonnet via Amazon Bedrock
- **MCP Server**: Port 8080, streamable-http transport (default)
- **A2A Server**: Port 9000, agent-to-agent communication
- **EKS Deployment**: Multi-architecture support (AMD64/ARM64)
- **Pod Identity**: Secure Bedrock access without credentials

### File Structure
```
weather/
├── agent.py                 # Core weather agent logic
├── agent_mcp_server.py      # MCP server (port 8080)
├── agent_a2a_server.py      # A2A server (port 9000)
├── main.py                  # Entry points + dual server orchestrator
├── Dockerfile               # Multi-arch container (weather-agent-dual-server)
├── helm/                    # Kubernetes deployment charts
├── weather-mcp-server/      # MCP tool definitions
├── pyproject.toml          # Entry points configuration
└── README.md               # Complete EKS deployment tutorial
```

## 🔧 Key Technical Decisions Made

### 1. Dual Server Implementation
**Problem**: User wanted single container to serve both MCP and A2A protocols
**Solution**: Extended `main.py` with `main_dual_server()` function using ThreadPoolExecutor
**Why**: Least intrusive, no code duplication, reuses existing server implementations

### 2. Default Transport Change
**Problem**: Docker containers needed streamable-http by default
**Solution**: Changed default in `agent_mcp_server.py` from `stdio` to `streamable-http`
**Why**: Eliminates need for command-line arguments in container deployment

### 3. Multi-Architecture Build Issues
**Problem**: `exec format error` - image built for ARM64 but scheduled on AMD64 node
**Solution**: Proper multi-architecture build with `docker buildx --platform linux/amd64,linux/arm64`
**Why**: EKS auto mode provisions both architecture types

### 4. Mermaid Diagram Fixes
**Problem**: "Unsupported markdown: list" errors in GitHub rendering
**Solution**: Removed numbered arrows (1., 2., 3.) and HTML `<br/>` tags
**Why**: GitHub's Mermaid parser interprets numbers as markdown lists

## 🚀 Entry Points Available

```bash
# Defined in pyproject.toml
weather-agent-mcp-server     # MCP only (port 8080, streamable-http default)
weather-agent-a2a-server     # A2A only (port 9000)
weather-agent-interactive    # CLI mode
weather-agent-dual-server    # Both servers (CURRENT DOCKER DEFAULT)
```

## 🐳 Container Configuration

### Current Dockerfile CMD
```dockerfile
CMD ["weather-agent-dual-server"]
```

### Environment Variables
```bash
MCP_PORT=8080          # MCP server port
A2A_PORT=9000          # A2A server port
BEDROCK_MODEL_ID=us.anthropic.claude-3-7-sonnet-20250219-v1:0
AWS_REGION=us-west-2
```

## ☸️ EKS Deployment Status

### Current State
- **EKS Cluster**: `agents-on-eks` (created with auto mode)
- **Container Registry**: ECR with multi-architecture images
- **IAM Configuration**: Pod Identity role for Bedrock access
- **Helm Chart**: Ready for deployment in `helm/` directory

### Deployment Commands
```bash
# Build and push multi-arch image
docker buildx build --platform linux/amd64,linux/arm64 -t ${ECR_REPO_URI}:latest --push .

# Deploy with Helm
helm upgrade weather-agent helm --install \
  --set serviceAccount.name=weather-agent \
  --set image.repository=${ECR_REPO_URI} \
  --set image.tag=latest

# Access services
kubectl port-forward service/weather-agent 8080:8080 9000:9000
```

## 🔍 Troubleshooting Guide for AI Agents

### Common Issues Encountered

#### 1. Architecture Mismatch
**Symptom**: `exec format error` in pod logs
**Cause**: Single-architecture image on wrong node type
**Solution**: Verify multi-arch build with `docker manifest inspect`

#### 2. Health Check Failures
**Symptom**: Pod in CrashLoopBackOff, health check errors
**Cause**: Incorrect port configuration or missing transport args
**Solution**: Check MCP server is using streamable-http and correct ports

#### 3. Mermaid Rendering Issues
**Symptom**: "Unsupported markdown: list" in GitHub
**Cause**: Numbered arrows or HTML tags in diagram
**Solution**: Use plain text labels without numbers or `<br/>` tags

#### 4. Container Not Starting Both Servers
**Symptom**: Only one protocol accessible
**Cause**: Using wrong entry point
**Solution**: Ensure Dockerfile uses `weather-agent-dual-server`

## 📋 Quick Commands for AI Agents

### Local Development
```bash
# Test dual server locally
uv run weather-agent-dual-server

# Test individual servers
uv run weather-agent-mcp-server --transport stdio  # For local testing
uv run weather-agent-a2a-server

# Test MCP connection
npx @modelcontextprotocol/inspector
# Use: streamable-http with http://localhost:8080

# Test A2A connection
uv run test_a2a_client.py
```

### Container Testing
```bash
# Build and test locally
docker build -t weather-agent .
docker run -p 8080:8080 -p 9000:9000 \
  -e AWS_REGION=us-west-2 \
  -e BEDROCK_MODEL_ID=us.anthropic.claude-3-7-sonnet-20250219-v1:0 \
  weather-agent
```

### EKS Operations
```bash
# Check cluster status
kubectl get nodes
kubectl get pods -l app.kubernetes.io/instance=weather-agent

# View logs
kubectl logs deployment/weather-agent

# Debug pod issues
kubectl describe pod <pod-name>
kubectl get events --sort-by=.metadata.creationTimestamp
```

## 🎯 Next Steps for AI Agents

### When Continuing This Project

1. **Check Current State**: Verify EKS cluster and deployment status
2. **Review Logs**: Check both MCP and A2A server logs for issues
3. **Test Connectivity**: Ensure both ports (8080, 9000) are accessible
4. **Monitor Resources**: Check pod resource usage and scaling needs

### When Extending Functionality

1. **Add New Tools**: Extend `weather-mcp-server/` directory
2. **Update Agent Logic**: Modify `agent.py` for new capabilities
3. **Test Both Protocols**: Ensure changes work with both MCP and A2A
4. **Update Documentation**: Keep README.md tutorial current

### When Troubleshooting

1. **Start with Logs**: `kubectl logs deployment/weather-agent`
2. **Check Architecture**: Verify multi-arch image if deployment issues
3. **Test Locally First**: Use `weather-agent-dual-server` locally
4. **Validate Configuration**: Ensure environment variables are correct

## 🔗 Key Resources

- **MCP Inspector**: `npx @modelcontextprotocol/inspector`
- **A2A Test Client**: `uv run test_a2a_client.py`
- **EKS Cluster**: `agents-on-eks` in `us-west-2`
- **Container Registry**: ECR `agents-on-eks/weather-agent`
- **Bedrock Model**: `us.anthropic.claude-3-7-sonnet-20250219-v1:0`

## 💡 AI Agent Tips

1. **Always check both protocols** when making changes
2. **Use multi-architecture builds** for EKS compatibility
3. **Test locally before deploying** to catch issues early
4. **Monitor both ports** (8080, 9000) for connectivity
5. **Keep Mermaid diagrams simple** to avoid rendering issues
6. **Use environment variables** for configuration flexibility

---

**This project successfully demonstrates a production-ready, dual-protocol AI agent deployment on Amazon EKS with comprehensive tooling and documentation.**
