# A2A Planning Study — Multi-Agent Sample

> ⚠️ This repository contains a demo for exploration/education and is not intended for production use.

This sample demonstrates a multi-agent system built with A2A. A Host Agent (ADK) orchestrates two Remote Agents (A2A servers):
- Study Planner Agent: creates personalized study plans
- Exercise Generator Agent: generates exercises and solutions aligned with the plan

The Host Agent provides a Gradio-based chat UI. Both remote agents run as A2A servers (Uvicorn) and are invoked by the Host over HTTP.

### Architecture & Flow

- The Host Agent (ADK) receives the user request and routes it to the appropriate Remote Agent (or both sequentially).
- Each Remote Agent exposes an `AgentCard` and the A2A API, processes the task, and returns results to the Host.
- Flow diagram: see `/home/hongdao/A2A-samples/samples/python/agents/a2a_planning_study/assets/a2a_planning_flow.drawio`.

## Prerequisites

- Python 3.13
- uv (package manager): `https://docs.astral.sh/uv/getting-started/installation/`
- Node.js (optional, only if you run example MCP servers)

### Environment variables

Choose one of the following setups for models:

1) Using Google API key
```bash
export GOOGLE_API_KEY="your_api_key_here"
```

2) Using Vertex AI
```bash
export GOOGLE_GENAI_USE_VERTEXAI=TRUE
export GOOGLE_CLOUD_PROJECT="your_gcp_project"
export GOOGLE_CLOUD_LOCATION=us-central1
```

Remote agent addresses for the Host Agent:
```bash
export PLANNING_AGENT_URL=http://localhost:10002
export EXERCISE_AGENT_URL=http://localhost:10003
```

## How to run

Open 3 separate terminals and run the following commands.

1) Study Planner Agent (A2A Server, port 10002):
```bash
cd /home/hongdao/A2A-samples/samples/python/agents/a2a_planning_study/planning_agent
uv run .
```

2) Exercise Generator Agent (A2A Server, port 10003):
```bash
cd /home/hongdao/A2A-samples/samples/python/agents/a2a_planning_study/exercise_agent
uv run .
```

3) Host Agent UI (Gradio, port 8083):
```bash
cd /home/hongdao/A2A-samples/samples/python/agents/a2a_planning_study/host_agent
uv run .
```

Open the UI at: `http://localhost:8083`

### Example prompts

- "Create a 4-week TOEIC study plan with 2 hours per day"
- "Generate a set of medium-level Python recursion exercises"

## References

- `https://github.com/google/a2a-python`
- `https://google.github.io/adk-docs/`

## Security note

When integrating A2A into real applications, treat all data from external agents as untrusted. Always validate and sanitize inputs (AgentCard, messages, artifacts, task statuses), manage secrets securely, and guard against prompt injection.