# Exercise Generator Agent (A2A Server)

Agent that generates programming exercises/solutions based on context and learning goals.

## Requirements
- Python 3.12, uv
- `GOOGLE_API_KEY` or equivalent Vertex AI configuration

## Environment variables
Create `.env` in this folder, for example:
```bash
GOOGLE_API_KEY="your_api_key_here"
# or use Vertex AI
# GOOGLE_GENAI_USE_VERTEXAI=TRUE
# GOOGLE_CLOUD_PROJECT="your_gcp_project"
# GOOGLE_CLOUD_LOCATION=us-central1
```

## Run the server
Default listen address is `localhost:10003`.
```bash
uv run .
```
You can specify arguments:
```bash
uv run . -- --host 0.0.0.0 --port 10003 --log-level info
```

## Notes
- The server initializes `ExerciseGeneratorAgentExecutor` and publishes an `AgentCard` for routing from the Host Agent.
