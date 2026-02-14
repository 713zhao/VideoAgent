#!/usr/bin/env python3
import argparse
import json
import sys
import os
import fcntl
from pathlib import Path

from app.main import run_once


def acquire_lock(lockfile_path: str):
  lockfile = open(lockfile_path, "w")
  try:
    fcntl.flock(lockfile.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
  except BlockingIOError:
    print(f"Another run is in progress (lock: {lockfile_path}). Exiting.")
    sys.exit(2)
  return lockfile


def main():
  ap = argparse.ArgumentParser(prog="videoagent-cli")
  ap.add_argument("--config", default=os.environ.get("VIDEOAGENT_CONFIG", "config.yaml"), help="Path to config YAML")
  ap.add_argument("--lockfile", default=os.environ.get("VIDEOAGENT_LOCKFILE", "/tmp/videoagent.lock"))
  ap.add_argument("--dry-run", action="store_true", help="Do a dry run (no publishing/upload) if supported)")
  args = ap.parse_args()

  # Acquire a simple filesystem lock to avoid concurrent runs
  lock = acquire_lock(args.lockfile)

  try:
    # Call the existing pipeline entrypoint
    out = run_once(args.config)
    result = {"status": "ok", "output": str(out) if out else None}
  except SystemExit as e:
    result = {"status": "error", "code": int(e.code) if isinstance(e.code, int) else 1}
  except Exception as e:
    result = {"status": "error", "message": str(e)}
  finally:
    try:
      fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
      lock.close()
    except Exception:
      pass

  print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
  main()
