"""Extracción de audio con FFmpeg (conversión nativa de pistas)."""

from __future__ import annotations

import logging
import shutil
import subprocess
from pathlib import Path

from . import config

log = logging.getLogger(__name__)


class FFmpegError(Exception):
    """FFmpeg no está disponible o la conversión falló."""


def check_ffmpeg() -> str:
    """Verifica que FFmpeg esté instalado y devuelve su versión.

    Lanza FFmpegError si no se encuentra en el PATH.
    """
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise FFmpegError(
            "FFmpeg no está instalado o no está en el PATH. "
            "Instálalo: https://ffmpeg.org/download.html "
            "(en Ubuntu/Debian: sudo apt install ffmpeg)."
        )
    try:
        out = subprocess.run(
            [ffmpeg, "-version"], capture_output=True, text=True, timeout=10
        )
        first_line = out.stdout.splitlines()[0] if out.stdout else "ffmpeg"
    except (OSError, subprocess.SubprocessError):
        first_line = "ffmpeg"
    log.info("FFmpeg detectado: %s", first_line)
    return first_line


def extract_audio_from_video(video_path: Path | str, output_path: Path | str | None = None) -> Path:
    """Extrae la pista de audio de un video y la guarda como MP3.

    Si ya descargaste el MP4 y luego quieres transcribir, esta función evita
    descargar el audio de nuevo: convierte el archivo local directamente.
    """
    video_path = Path(video_path)
    if not video_path.exists():
        raise FFmpegError(f"El archivo de video no existe: {video_path}")

    check_ffmpeg()
    mp3_path = Path(output_path) if output_path else video_path.with_suffix(".mp3")

    cmd = [
        "ffmpeg",
        "-y",                       # sobrescribe sin preguntar
        "-i", str(video_path),
        "-vn",                      # sin video: solo audio
        "-acodec", "libmp3lame",
        "-b:a", f"{config.MP3_BITRATE}k",
        str(mp3_path),
    ]
    log.info("Convirtiendo a MP3: %s", " ".join(cmd))
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
    except subprocess.TimeoutExpired as exc:
        raise FFmpegError("La conversión con FFmpeg excedió el tiempo límite.") from exc
    except OSError as exc:
        raise FFmpegError(f"No se pudo ejecutar FFmpeg: {exc}") from exc

    if result.returncode != 0 or not mp3_path.exists():
        tail = (result.stderr or "")[-800:]
        raise FFmpegError(f"FFmpeg falló al convertir el audio.\n{tail}")

    log.info("Audio extraído: %s", mp3_path)
    return mp3_path
