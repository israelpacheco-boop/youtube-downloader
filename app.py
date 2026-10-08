"""Interfaz web (Streamlit) de la herramienta.

Panel con:
  1. Barra de entrada para la URL de YouTube.
  2. Dos botones de acción: Descargar Video MP4 / Descargar Audio MP3.
  3. Vista previa y descarga de los archivos generados.

Versión simplificada: sin dependencias de APIs externas (sin Gemini).
Solo Python + yt-dlp + FFmpeg.
"""

from __future__ import annotations

import logging
from pathlib import Path

import streamlit as st

from src import config
from src.audio import check_ffmpeg, FFmpegError
from src.youtube import (
    DownloadError,
    InvalidURLError,
    download_audio,
    download_video,
    extract_video_id,
    get_video_info,
)

# ---------------------------------------------------------------------------
# Configuración básica
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("app")

st.set_page_config(page_title=config.APP_TITLE, page_icon=config.APP_ICON, layout="wide")

config.DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Estado de la sesión
# ---------------------------------------------------------------------------
for key, default in {
    "video_info": None,
    "last_video": None,
    "last_audio": None,
}.items():
    st.session_state.setdefault(key, default)


# ---------------------------------------------------------------------------
# Encabezado
# ---------------------------------------------------------------------------
st.title(f"{config.APP_ICON} Descargador de Videos")
st.caption(
    "Pega el enlace de un video de YouTube, espera a que se procese "
    "y descárgalo a tu equipo. ¡Así de fácil! ✨"
)

# Diagnóstico rápido del entorno (FFmpeg)
with st.expander("🔧 Estado del sistema", expanded=False):
    try:
        version = check_ffmpeg()
        st.success(f"FFmpeg disponible: {version.splitlines()[0]}")
    except FFmpegError as exc:
        st.error(str(exc))
    st.info(f"Carpeta de descargas: `{config.DOWNLOADS_DIR}`")

# ---------------------------------------------------------------------------
# Entrada de URL
# ---------------------------------------------------------------------------
url = st.text_input(
    "URL de YouTube",
    placeholder="https://www.youtube.com/watch?v=...  (también acepta shorts, youtu.be y listas)",
)

video_info = None
if url:
    try:
        video_id = extract_video_id(url)
        with st.spinner("Obteniendo información del video..."):
            video_info = get_video_info(url)
        st.session_state.video_info = video_info

        col_a, col_b = st.columns([1, 3])
        with col_a:
            if video_info.get("thumbnail"):
                st.image(video_info["thumbnail"], use_container_width=True)
        with col_b:
            st.subheader(video_info["title"])
            meta = []
            if video_info.get("uploader"):
                meta.append(f"📺 {video_info['uploader']}")
            if video_info.get("duration"):
                mins, secs = divmod(video_info["duration"], 60)
                meta.append(f"⏱️ {mins}:{secs:02d}")
            if meta:
                st.caption(" · ".join(meta))
    except (InvalidURLError, DownloadError) as exc:
        st.session_state.video_info = None
        st.error(str(exc))

# ---------------------------------------------------------------------------
# Botones de acción
# ---------------------------------------------------------------------------
st.divider()
col1, col2 = st.columns(2)

with col1:
    btn_video = st.button(
        "⬇️ Descargar Video MP4", use_container_width=True, disabled=not url
    )
with col2:
    btn_audio = st.button(
        "🎵 Descargar Audio MP3", use_container_width=True, disabled=not url
    )

# --- Acción 1: descargar video ---------------------------------------------
if btn_video:
    st.session_state.last_video = None
    try:
        with st.status("Descargando video en alta definición...", expanded=True) as status:
            path = download_video(url)
            status.update(label="✅ Video descargado", state="complete")
        st.session_state.last_video = str(path)
        st.success(f"Video guardado: `{path.name}`")
        st.video(str(path))
        with open(path, "rb") as fh:
            st.download_button(
                "💾 Descargar MP4 a tu equipo",
                data=fh,
                file_name=path.name,
                mime="video/mp4",
            )
    except (InvalidURLError, DownloadError, FFmpegError) as exc:
        log.exception("Fallo al descargar el video")
        st.error(str(exc))

# --- Acción 2: descargar audio ----------------------------------------------
if btn_audio:
    st.session_state.last_audio = None
    try:
        with st.status("Descargando y convirtiendo a MP3...", expanded=True) as status:
            path = download_audio(url)
            status.update(label="✅ Audio descargado", state="complete")
        st.session_state.last_audio = str(path)
        st.success(f"Audio guardado: `{path.name}`")
        st.audio(str(path))
        with open(path, "rb") as fh:
            st.download_button(
                "💾 Descargar MP3 a tu equipo",
                data=fh,
                file_name=path.name,
                mime="audio/mpeg",
            )
    except (InvalidURLError, DownloadError, FFmpegError) as exc:
        log.exception("Fallo al descargar el audio")
        st.error(str(exc))

# ---------------------------------------------------------------------------
# Archivos en la carpeta de descargas
# ---------------------------------------------------------------------------
with st.expander("📁 Archivos descargados en esta sesión", expanded=False):
    files = sorted(
        config.DOWNLOADS_DIR.iterdir(),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if not files:
        st.caption("Aún no hay archivos. La carpeta `downloads/` se llena automáticamente.")
    else:
        for f in files[:20]:
            size_mb = f.stat().st_size / (1024 * 1024)
            st.caption(f"• `{f.name}` — {size_mb:.1f} MB")
