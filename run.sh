#!/usr/bin/env bash
# Arranque rápido en Linux/macOS.
# Uso: ./run.sh   (o: bash run.sh)
set -e
cd "$(dirname "$0")"

if [ ! -d ".venv" ]; then
  echo "→ Creando entorno virtual..."
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate

echo "→ Instalando dependencias..."
pip install --upgrade pip -q
pip install -r requirements.txt -q

echo "→ Iniciando la app en http://localhost:8501"
streamlit run app.py
