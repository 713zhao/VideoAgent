from __future__ import annotations
from pathlib import Path
from typing import Optional
import asyncio

from .config import TTSCfg
from .utils import ensure_dir

async def _edge_tts_async(text: str, out_path: Path, voice: str, rate: str, volume: str) -> None:
  import edge_tts
  import ssl
  import aiohttp
  
  # Create SSL context that doesn't verify certificates (for corporate networks)
  ssl_context = ssl.create_default_context()
  ssl_context.check_hostname = False
  ssl_context.verify_mode = ssl.CERT_NONE
  
  # Create aiohttp connector with custom SSL context
  connector = aiohttp.TCPConnector(ssl=ssl_context)
  
  async with aiohttp.ClientSession(connector=connector) as session:
    communicate = edge_tts.Communicate(text=text, voice=voice, rate=rate, volume=volume)
    # Monkey patch the session into edge_tts
    communicate.session = session
    await communicate.save(str(out_path))

def synthesize(cfg: TTSCfg, text: str, out_dir: Path) -> Path:
  out_dir = ensure_dir(out_dir)
  fmt = cfg.audio_format
  out_path = out_dir / f"voice.{fmt}"

  if cfg.backend == "none":
    # Create empty placeholder (silence will be handled by ffmpeg)
    out_path.write_bytes(b"")
    return out_path

  if cfg.backend == "edge_tts":
    e = cfg.edge_tts
    asyncio.run(_edge_tts_async(text=text, out_path=out_path, voice=e.voice, rate=e.rate, volume=e.volume))
    return out_path

  if cfg.backend == "pyttsx3":
    import pyttsx3
    engine = pyttsx3.init()
    engine.setProperty('rate', cfg.pyttsx3.rate)
    # pyttsx3 doesn't reliably export mp3; use wav for best results
    if fmt != "wav":
      raise RuntimeError("pyttsx3 backend requires audio_format: wav")
    engine.save_to_file(text, str(out_path))
    engine.runAndWait()
    return out_path

  raise RuntimeError(f"Unknown TTS backend: {cfg.backend}")
