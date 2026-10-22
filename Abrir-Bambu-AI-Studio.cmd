@echo off
if not exist "%~dp0.venv\Scripts\pythonw.exe" (
    echo Primeiro instale: uv sync --locked --extra cadquery --extra desktop
    pause
    exit /b 1
)
pushd "%~dp0"
start "Bambu AI Studio" "%~dp0.venv\Scripts\pythonw.exe" -m bambu_ai.desktop.app
popd
