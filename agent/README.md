# VideoAgent Agent

This folder contains a minimal agent wrapper for VideoAgent.

- `agent_cli.py` — local CLI wrapper that calls `app.main.run_once` and prints JSON results. Intended for same-host invocation by OpenClaw via command execution.
- `agent_server.py` — small FastAPI server exposing `/health` and `/run` (bind to 127.0.0.1 or a unix socket for local-only access). Protect with `VIDEOAGENT_API_KEY`.
- `Dockerfile.agent` — simple image to run the FastAPI agent.

Usage examples

CLI (same-host):
```
python agent/agent_cli.py --config config.yaml
```

HTTP (local-only):
```
VIDEOAGENT_API_KEY=xxx uvicorn agent.agent_server:app --host 127.0.0.1 --port 8000
curl -H "x-api-key: xxx" -d '{"config":"config.yaml"}' http://127.0.0.1:8000/run
```

Security notes

- Do not commit secrets. Use OpenClaw secret injection or environment variables.
- Prefer CLI or unix-domain socket for same-host integrations to avoid network exposure.
