from __future__ import annotations
import hashlib
import os
import shutil
from pathlib import Path
from typing import Optional

def ensure_dir(path: str | Path) -> Path:
  p = Path(path)
  p.mkdir(parents=True, exist_ok=True)
  return p

def sha256_file(path: str | Path) -> str:
  h = hashlib.sha256()
  with open(path, "rb") as f:
    for chunk in iter(lambda: f.read(1024 * 1024), b""):
      h.update(chunk)
  return h.hexdigest()

def copytree_overwrite(src: Path, dst: Path) -> None:
  if dst.exists():
    shutil.rmtree(dst)
  shutil.copytree(src, dst)

def which(exe: str) -> Optional[str]:
  # Cross-platform "which"
  paths = os.environ.get("PATH", "").split(os.pathsep)
  exts = [""]
  if os.name == "nt":
    exts = os.environ.get("PATHEXT", "").split(os.pathsep) or [".EXE", ".BAT", ".CMD"]
  for p in paths:
    for ext in exts:
      cand = Path(p) / (exe + ext)
      if cand.exists() and cand.is_file():
        return str(cand)
  return None
