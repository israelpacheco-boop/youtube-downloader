"""Utilidades para trabajar con URLs y descargas de YouTube (yt-dlp)."""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

import yt_dlp

from . import config

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Excepciones propias
# ---------------------------------------------------------------------------
class YouTubeError(Exception):
    """Error base de este módulo."""


class InvalidURLError(YouTubeError):
    """La URL no contiene un ID de video válido."""


class DownloadError(YouTubeError):
    """Fallo durante la descarga (red, video privado, etc.)."""


# ---------------------------------------------------------------------------
# Extracción del ID del video
# ---------------------------------------------------------------------------
# Cubre: watch?v=, youtu.be/, /shorts/, /embed/, /live/, /v/ y URLs con
# parámetros residuales (?list=, &t=, ?si=, etc.). El ID de YouTube tiene
# siempre 11 caracteres alfanuméricos más "-" y "_".
_VIDEO_ID_PATTERNS = [
    re.compile(r"(?:v=|/v/|/vi/|/embed/|/live/|/shorts/)([A-Za-z0-9_-]{11})"),
    re.compile(r"youtu\.be/([A-Za-z0-9_-]{11})"),
]


def extract_video_id(url: str) -> str:
    """Aísla el ID de 11 caracteres de una URL de YouTube.

    Descarta parámetros residuales de listas de reproducción (?list=),
    canales o marcas de tiempo (?t=). Lanza InvalidURLError si no hay ID.
    """
    url = (url or "").strip()
    for pattern in _VIDEO_ID_PATTERNS:
        match = pattern.search(url)
        if match:
            return match.group(1)
    raise InvalidURLError(
        "No se encontró un ID de video válido en la URL. "
        "Usa un enlace tipo https://www.youtube.com/watch?v=XXXXXXXXXXX "
        "o https://youtu.be/XXXXXXXXXXX"
    )


def canonical_url(video_id: str) -> str:
    """URL canónica del video (evita arrastrar parámetros de listas)."""
    return f"https://www.youtube.com/watch?v={video_id}"


def sanitize_filename(name: str, max_length: int = 80) -> str:
    """Limpia un título para usarlo como nombre de archivo seguro."""
    cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "", name or "").strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned[:max_length].rstrip(" .") or "video"


# ---------------------------------------------------------------------------
# yt-dlp
# ---------------------------------------------------------------------------
class _QuietLogger:
    """Logger mínimo: los errores suben a nuestro logging, lo demás se ignora."""

    def debug(self, msg: str) -> None:  # noqa: D102
        pass

    def warning(self, msg: str) -> None:
        log.warning("yt-dlp: %s", msg)

    def error(self, msg: str) -> None:
        log.error("yt-dlp: %s", msg)


def _base_opts(outtmpl: str) -> dict[str, Any]:
    """Opciones comunes: un solo video, sin listas, con reintentos de red."""
    return {
        "noplaylist": config.YTDLP_NO_PLAYLIST,  # fuerza UN solo video
        "outtmpl": outtmpl,
        "logger": _QuietLogger(),
        "quiet": True,
        "no_warnings": True,
        "retries": 5,               # reintentos ante fallas de red
        "fragment_retries": 5,
        "socket_timeout": 30,
    }


def get_video_info(url: str) -> dict[str, Any]:
    """Devuelve título, duración y miniatura sin descargar nada.

    Útil para validar la URL y mostrar una vista previa en la UI.
    """
    video_id = extract_video_id(url)
    opts = _base_opts(outtmpl="%(title)s.%(ext)s")
    opts["skip_download"] = True
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(canonical_url(video_id), download=False)
    except yt_dlp.utils.DownloadError as exc:
        raise DownloadError(_friendly_download_error(exc)) from exc
    return {
        "video_id": video_id,
        "title": info.get("title", video_id),
        "duration": info.get("duration"),
        "thumbnail": info.get("thumbnail"),
        "uploader": info.get("uploader"),
    }


def download_video(url: str, downloads_dir: Path | None = None) -> Path:
    """Descarga el video completo en MP4 (alta definición, hasta 1080p).

    Devuelve la ruta del archivo descargado.
    """
    video_id = extract_video_id(url)
    target = Path(downloads_dir or config.DOWNLOADS_DIR)
    target.mkdir(parents=True, exist_ok=True)

    outtmpl = str(target / "%(title)s [%(id)s].%(ext)s")
    opts = _base_opts(outtmpl)
    opts.update(
        {
            "format": config.VIDEO_FORMAT,
            "merge_output_format": "mp4",  # une video+audio en un MP4 limpio
        }
    )
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(canonical_url(video_id), download=True)
            filename = ydl.prepare_filename(info)
    except yt_dlp.utils.DownloadError as exc:
        raise DownloadError(_friendly_download_error(exc)) from exc
    except OSError as exc:
        raise DownloadError(f"No se pudo escribir el archivo: {exc}") from exc

    path = Path(filename)
    if not path.exists():  # el merge puede cambiar la extensión final
        candidates = sorted(target.glob(f"*{video_id}.mp4"))
        if not candidates:
            raise DownloadError("La descarga terminó pero no se encontró el MP4.")
        path = candidates[-1]
    log.info("Video descargado: %s", path)
    return path


def download_audio(url: str, downloads_dir: Path | None = None) -> Path:
    """Descarga solo el audio y lo convierte a MP3 vía FFmpeg.

    Devuelve la ruta del archivo .mp3 generado.
    """
    video_id = extract_video_id(url)
    target = Path(downloads_dir or config.DOWNLOADS_DIR)
    target.mkdir(parents=True, exist_ok=True)

    outtmpl = str(target / "%(title)s [%(id)s].%(ext)s")
    opts = _base_opts(outtmpl)
    opts.update(
        {
            "format": config.AUDIO_FORMAT,
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": config.MP3_BITRATE,
                }
            ],
        }
    )
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(canonical_url(video_id), download=True)
            base = Path(ydl.prepare_filename(info)).with_suffix("")
    except yt_dlp.utils.DownloadError as exc:
        raise DownloadError(_friendly_download_error(exc)) from exc
    except OSError as exc:
        raise DownloadError(f"No se pudo escribir el archivo: {exc}") from exc

    mp3_path = base.with_suffix(".mp3")
    if not mp3_path.exists():
        candidates = sorted(target.glob(f"*{video_id}.mp3"))
        if not candidates:
            raise DownloadError(
                "La descarga terminó pero no se generó el MP3. "
                "Verifica que FFmpeg esté instalado y en el PATH."
            )
        mp3_path = candidates[-1]
    log.info("Audio descargado: %s", mp3_path)
    return mp3_path


def _friendly_download_error(exc: Exception) -> str:
    """Traduce errores técnicos de yt-dlp a mensajes legibles."""
    msg = str(exc)
    lowered = msg.lower()
    if "private" in lowered:
        return "El video es privado y no se puede descargar."
    if "age" in lowered and "confirm" in lowered:
        return "El video tiene restricción de edad y requiere iniciar sesión."
    if "not available" in lowered or "removed" in lowered:
        return "El video no está disponible (eliminado o bloqueado por región)."
    if "timed out" in lowered or "connection" in lowered or "network" in lowered:
        return f"Falla de red durante la descarga: {msg}"
    if "ffmpeg" in lowered:
        return (
            "FFmpeg falló o no está instalado. "
            "Instálalo y asegúrate de que esté en el PATH del sistema."
        )
    return f"Error al descargar: {msg}"
