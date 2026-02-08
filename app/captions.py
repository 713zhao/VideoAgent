from __future__ import annotations
from pathlib import Path
from typing import List, Dict, Any
from .utils import ensure_dir

def _fmt_time(seconds: float) -> str:
  # SRT time: HH:MM:SS,mmm
  ms = int(round(seconds * 1000))
  s = ms // 1000
  ms = ms % 1000
  hh = s // 3600
  s = s % 3600
  mm = s // 60
  ss = s % 60
  return f"{hh:02d}:{mm:02d}:{ss:02d},{ms:03d}"

def write_srt(captions: List[Dict[str, Any]], out_dir: Path) -> Path:
  out_dir = ensure_dir(out_dir)
  path = out_dir / "captions.srt"
  lines = []
  for i, cap in enumerate(captions, start=1):
    start = float(cap.get("start_s", 0))
    end = float(cap.get("end_s", start + 3))
    text = str(cap.get("text", "")).strip()
    if not text:
      continue
    lines.append(str(i))
    lines.append(f"{_fmt_time(start)} --> {_fmt_time(end)}")
    lines.append(text)
    lines.append("")
  path.write_text("\n".join(lines), encoding="utf-8")
  return path
