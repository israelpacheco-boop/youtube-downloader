@echo off
REM Arranque rapido en Windows.
REM Uso: doble clic en run.bat o ejecutarlo desde cmd.
cd /d "%~dp0"

if not exist ".venv" (
  echo -^> Creando entorno virtual...
  python -m venv .venv
)
call .venv\Scripts\activate.bat

echo -^> Instalando dependencias...
python -m pip install --upgrade pip -q
pip install -r requirements.txt -q

echo -^> Iniciando la app en http://localhost:8501
streamlit run app.py
