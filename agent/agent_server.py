from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
import os
import asyncio
from typing import Optional

from app.main import run_once

app = FastAPI()

API_KEY = os.environ.get("VIDEOAGENT_API_KEY")


class RunPayload(BaseModel):
  config: Optional[str] = "config.yaml"
  dry_run: Optional[bool] = False


def check_auth(request: Request):
  if not API_KEY:
    return
  key = request.headers.get("x-api-key")
  if key != API_KEY:
    raise HTTPException(status_code=401, detail="unauthorized")


@app.get("/health")
async def health():
  return {"status": "ok"}


@app.post("/run")
async def run(request: Request, payload: RunPayload):
  check_auth(request)
  # Run the blocking pipeline in a thread to avoid blocking the event loop
  try:
    out = await asyncio.to_thread(run_once, payload.config)
    return {"status": "ok", "output": str(out) if out else None}
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
  import uvicorn
  host = os.environ.get("VIDEOAGENT_HOST", "127.0.0.1")
  port = int(os.environ.get("VIDEOAGENT_PORT", "8000"))
  uvicorn.run(app, host=host, port=port)
