from __future__ import annotations
import hashlib
import os
import shutil
from pathlib import Path
from typing import Optional
from datetime import datetime, timedelta

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

def cleanup_old_outputs(root: str | Path, retain_days: int = 30, keep_latest: bool = True) -> None:
  """
  Remove dated output subdirectories older than `retain_days` days.

  - Assumes dated folders are named like YYYY-MM-DD (common output layout).
  - Will not remove the `latest` folder when `keep_latest` is True.
  - Silently ignores files that cannot be deleted.
  """
  root_p = Path(root)
  if not root_p.exists() or not root_p.is_dir():
    return

  cutoff = datetime.now() - timedelta(days=retain_days)

  for child in root_p.iterdir():
    # Skip non-directories
    if not child.is_dir():
      continue
    if keep_latest and child.name == "latest":
      continue

    # Try parse directory name as date YYYY-MM-DD
    try:
      dir_date = datetime.strptime(child.name, "%Y-%m-%d")
    except Exception:
      # Fallback: use modification time
      try:
        mtime = datetime.fromtimestamp(child.stat().st_mtime)
        dir_date = mtime
      except Exception:
        # Can't determine date -> skip
        continue

    if dir_date < cutoff:
      try:
        shutil.rmtree(child)
        print(f"🧹 Removed old output: {child}")
      except Exception as e:
        print(f"⚠️ Failed to remove {child}: {e}")
