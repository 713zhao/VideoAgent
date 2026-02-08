from __future__ import annotations
import subprocess
from pathlib import Path
from typing import Optional
import shlex

from .config import VideoCfg
from .utils import ensure_dir, which

def _require_ffmpeg() -> str:
  ff = which("ffmpeg")
  if not ff:
    raise RuntimeError("ffmpeg not found in PATH. Install FFmpeg and try again.")
  return ff

def render_video(cfg: VideoCfg, voice_path: Path, srt_path: Path, out_dir: Path, title: str = "") -> Path:
  out_dir = ensure_dir(out_dir)
  ffmpeg = _require_ffmpeg()

  w, h, fps = cfg.width, cfg.height, cfg.fps
  out_mp4 = out_dir / "final.mp4"

  # Background video source: image loop or solid color
  inputs = []
  filters = []

  if cfg.background_image:
    bg = Path(cfg.background_image).expanduser().resolve()
    if not bg.exists():
      raise RuntimeError(f"background_image not found: {bg}")
    inputs += ["-loop", "1", "-i", str(bg)]
    bg_src = "[0:v]"
  else:
    # Create a solid color source using lavfi
    inputs += ["-f", "lavfi", "-i", f"color=c={cfg.background_color}:s={w}x{h}:r={fps}"]
    bg_src = "[0:v]"

  # Audio input (voiceover). If empty file, we generate silence.
  if voice_path.exists() and voice_path.stat().st_size > 0:
    inputs += ["-i", str(voice_path)]
    audio_src = "1:a"
  else:
    # silence
    inputs += ["-f", "lavfi", "-i", f"anullsrc=r=44100:cl=stereo"]
    audio_src = "1:a"

  # Optional background music
  music_index = None
  if cfg.background_music:
    music = Path(cfg.background_music).expanduser().resolve()
    if not music.exists():
      raise RuntimeError(f"background_music not found: {music}")
    inputs += ["-i", str(music)]
    music_index = 2

  # Subtitle styling: use force_style for libass
  # font can be empty to use default. marginV controls bottom padding.
  font = cfg.captions.font.replace("'", "")
  style_parts = [
    f"Fontsize={cfg.captions.font_size}",
    f"MarginV={cfg.captions.margin_v}",
    "Outline=2",
    "Shadow=1",
    "Alignment=2"  # bottom-center
  ]
  if font:
    style_parts.append(f"Fontname={font}")

  force_style = ",".join(style_parts)
  srt = Path(srt_path).resolve()
  vf = f"subtitles='{str(srt).replace('\\', '/')}':force_style='{force_style}'"

  # Build audio filter if music is present
  audio_filters = []
  map_audio = []
  if music_index is not None:
    # lower music volume and mix with voice
    audio_filters.append(f"[{music_index}:a]volume={cfg.background_music_volume}[bgm]")
    audio_filters.append(f"[1:a][bgm]amix=inputs=2:duration=longest:dropout_transition=2[aout]")
    map_audio = ["-map", "[aout]"]
  else:
    map_audio = ["-map", "1:a"]

  cmd = [ffmpeg]
  cmd += inputs
  cmd += [
    "-vf", vf,
    "-r", str(fps),
    "-pix_fmt", "yuv420p",
    "-c:v", "libx264",
    "-preset", "veryfast",
    "-crf", "22",
  ]

  if audio_filters:
    cmd += ["-filter_complex", ";".join(audio_filters)]
  cmd += map_audio
  cmd += [
    "-shortest",
    str(out_mp4)
  ]

  # Run
  proc = subprocess.run(cmd, capture_output=True, text=True)
  if proc.returncode != 0:
    raise RuntimeError("FFmpeg failed:\n" + proc.stderr[-4000:])

  return out_mp4
