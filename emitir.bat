@echo off
rem ===========================================================================
rem  Control de planos - emision
rem
rem  Se usa de dos formas:
rem    1. Arrastrando el PDF ploteado sobre este fichero.
rem    2. Haciendo doble clic: pedira la ruta del PDF.
rem
rem  No hace falta saber nada de Python ni tener permisos de administrador.
rem ===========================================================================

chcp 65001 >nul 2>&1
setlocal
set "RAIZ=%~dp0"
set "PYTHONIOENCODING=utf-8"
set "PY=%RAIZ%.venv\Scripts\python.exe"

if not exist "%PY%" (
    echo.
    echo   No se encuentra el entorno virtual del proyecto.
    echo   Falta: %PY%
    echo.
    echo   Para crearlo, abre una consola en esta carpeta y ejecuta:
    echo.
    echo       python -m venv .venv
    echo       .venv\Scripts\python.exe -m pip install -e .
    echo.
    pause
    exit /b 1
)

"%PY%" -m control_planos.cli %*
set "SALIDA=%ERRORLEVEL%"

echo.
if not "%SALIDA%"=="0" (
    echo   No se ha emitido nada. Revisa el mensaje de arriba.
    echo.
)
pause
exit /b %SALIDA%
