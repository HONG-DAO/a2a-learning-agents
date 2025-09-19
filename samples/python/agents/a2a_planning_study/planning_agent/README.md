# Study Planner Agent (A2A Server)

Personalized study planning agent running as an A2A server (Uvicorn).

## Requirements
- Python 3.13, uv
- Either `GOOGLE_API_KEY` or Vertex AI configuration (`GOOGLE_GENAI_USE_VERTEXAI=TRUE`, `GOOGLE_CLOUD_PROJECT`, `GOOGLE_CLOUD_LOCATION`)

## Environment variables
Create a `.env` file in this folder, for example:
```bash
# Choose one of the two: API key or Vertex AI
GOOGLE_API_KEY="your_api_key_here"
# or
# GOOGLE_GENAI_USE_VERTEXAI=TRUE
# GOOGLE_CLOUD_PROJECT="your_gcp_project"
# GOOGLE_CLOUD_LOCATION=us-central1
```

## Run the server
Default listen address is `localhost:10002`.
```bash
uv run .
```
Optional arguments:
```bash
uv run . -- --host 0.0.0.0 --port 10002 --log-level info
```

## Notes
- Example MCP servers are pre-configured via `langchain_mcp_adapters` (see `__main__.py`).
- The `AgentCard` describes skills/capabilities for the Host Agent to route tasks properly.