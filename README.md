# 🎬 YouTube Downloader — Dashboard para compartir

Herramienta web interactiva: se pega una URL de YouTube, la app la procesa
y el archivo (MP4 en alta definición o MP3) se descarga al equipo local.

Pensada para compartirse con un enlace público: sin cuentas, sin API keys,
sin instalación para quien la usa.

## ✨ Cómo funciona (para quien la usa)

1. Abre el enlace que te compartan.
2. Pega la URL del video de YouTube.
3. Pulsa **⬇️ Descargar Video MP4** o **🎵 Descargar Audio MP3**.
4. Espera a que termine y pulsa **💾 Descargar a tu equipo**.

## 📁 Estructura del proyecto

```
youtube-downloader-dashboard/
├── app.py                  # Interfaz web (Streamlit)
├── requirements.txt        # Dependencias Python (streamlit + yt-dlp)
├── packages.txt            # Paquete del sistema para la nube (ffmpeg)
├── run.sh / run.bat        # Arranque rápido local
├── src/
│   ├── config.py           # Constantes: formatos, rutas
│   ├── youtube.py          # Regex de video ID + descargas con yt-dlp
│   └── audio.py            # Extracción de audio con FFmpeg
├── tests/
│   └── test_youtube.py     # Pruebas del extractor de video ID
└── downloads/              # Carpeta temporal de trabajo (se crea sola)
```

## 🚀 Opción 1: Uso local (en tu computadora)

Requisitos: **Python 3.10+** y **FFmpeg** instalado.

```bash
cd youtube-downloader-dashboard
./run.sh        # Linux/macOS   (o: run.bat en Windows)
```

Abre http://localhost:8501.

## 🌐 Opción 2: Publicarla gratis para compartir el enlace

La forma más simple es **Streamlit Community Cloud** (gratis):

1. **Sube el proyecto a GitHub**
   - Crea un repositorio nuevo en https://github.com/new (puede ser público).
   - Sube todos los archivos de esta carpeta (incluye `packages.txt`,
     que instala FFmpeg automáticamente en la nube).

2. **Despliégala**
   - Entra a https://share.streamlit.io e inicia sesión con GitHub.
   - Pulsa **"Create app"** → **"Deploy a public app from GitHub"**.
   - Selecciona tu repositorio, rama `main` y archivo `app.py`.
   - Pulsa **Deploy** y espera 2–3 minutos.

3. **Comparte el enlace**
   - Te dará una URL pública tipo `https://tu-app.streamlit.app`.
   - Compártela con quien quieras: abre en cualquier navegador, sin instalar nada.

### Alternativa: Hugging Face Spaces

También gratis: crea un Space de tipo **Streamlit** en
https://huggingface.co/spaces, sube los archivos y listo.

## ⚠️ Limitación honesta que debes conocer

YouTube bloquea con frecuencia las direcciones IP de las nubes gratuitas
(Streamlit Cloud, Hugging Face, etc.), por lo que `yt-dlp` a veces falla ahí
con errores de "sign in" o 403. Si eso pasa, las opciones son:

- **Usarla en local** (Opción 1): desde tu casa funciona sin bloqueos y
  puedes compartirla en tu red WiFi con
  `streamlit run app.py --server.address 0.0.0.0`.
- **Un VPS económico** (unos $5/mes): misma app, IP propia, sin bloqueos.

## ⚙️ Personalización

Todo lo ajustable vive en `src/config.py` (`VIDEO_FORMAT`, `MP3_BITRATE`).

## ⚠️ Nota legal

Descargar videos puede violar los Términos de Servicio de YouTube. Úsala solo
con contenido propio, con licencia adecuada o donde tengas derecho a hacerlo.
