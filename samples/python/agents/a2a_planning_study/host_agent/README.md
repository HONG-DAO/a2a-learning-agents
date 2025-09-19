# Host Agent (ADK + Gradio UI)

Chat UI built with ADK. The Host Agent routes tasks to Remote Agents over A2A.

## Requirements
- Python 3.13, uv
- Environment variables pointing to Remote Agents

## Environment variables
Create `.env` in this folder:
```bash
# Model auth (API key or Vertex AI)
GOOGLE_API_KEY="your_api_key_here"
# or
# GOOGLE_GENAI_USE_VERTEXAI=TRUE
# GOOGLE_CLOUD_PROJECT="your_gcp_project"
# GOOGLE_CLOUD_LOCATION=us-central1

# Remote Agents addresses
PLANNING_AGENT_URL=http://localhost:10002
EXERCISE_AGENT_URL=http://localhost:10003
```

## Run the UI
```bash
uv run .
```
Gradio UI default: `http://localhost:8083`.

## Flow
- User submits a request; the Routing Agent decides whether to call the Study Planner or the Exercise Generator.
- Results from Remote Agents are returned and displayed in the UI (including Tool Calls/Responses if applicable).
