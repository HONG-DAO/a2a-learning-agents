# A2A Planning Study — Multi-Agent Sample

> ⚠️ This demo is for demonstration purposes only and is not intended for production use.

This sample showcases a multi-agent system built with A2A: a Host Agent (ADK) orchestrates two Remote Agents (A2A servers):
- Study Planner Agent: creates personalized study plans
- Exercise Generator Agent: generates exercises/solutions aligned with the plan

The Host Agent provides a Gradio UI for chat-based testing. Both remote agents run as A2A servers (Uvicorn) and are invoked by the Host over HTTP.

### Architecture & A2A flow

- The Host Agent (ADK) receives the user request and routes it to the appropriate Remote Agent (or both sequentially).
- Each Remote Agent exposes an `AgentCard` and the A2A API, processes the task, and returns results to the Host.
- Flow diagram (draw.io): see `assets/a2a_planning_flow.drawio` (export PNG/SVG to embed if needed).

### Prerequisites

- Python 3.13
- uv (package manager): see `https://docs.astral.sh/uv/getting-started/installation/`
- Node.js (optional, if you want to run example MCP servers)

Environment setup (pick one):

1) Using Google API key
```bash
GOOGLE_API_KEY="your_api_key_here"
```

2) Using Vertex AI
```bash
GOOGLE_GENAI_USE_VERTEXAI=TRUE
GOOGLE_CLOUD_PROJECT="your_gcp_project"
GOOGLE_CLOUD_LOCATION=us-central1
```

Host Agent variables (remote agent addresses):
```bash
PLANNING_AGENT_URL=http://localhost:10002
EXERCISE_AGENT_URL=http://localhost:10003
```

### How to run

Open 3 separate terminals:

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

After launching, open the UI at: `http://localhost:8083`

### Example prompts
- "Create a 4-week TOEIC study plan with 2 hours per day"
- "Generate a set of medium-level Python recursion exercises"

### References
- `https://github.com/google/a2a-python`
- `https://google.github.io/adk-docs/`

### Security note
When integrating A2A into real applications, treat all data from external agents as untrusted. Always validate/sanitize inputs (AgentCard, messages, artifacts, etc.), manage secrets securely, and guard against prompt injection.