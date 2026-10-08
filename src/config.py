from pathlib import Path

# Configuración de la interfaz
APP_TITLE = "YouTube Downloader"
APP_ICON = "📥"

# Configuración de formatos y calidades
VIDEO_FORMAT = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]'
MP3_BITRATE = '192'

# Directorio de descargas temporales (Solo definimos la ruta)
DOWNLOADS_DIR = Path(__file__).parent.parent / "downloads"
