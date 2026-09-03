@echo off
rem ===========================================================================
rem  Control de planos - publicar en la web
rem
rem  Sube a internet las revisiones que se hayan emitido desde la ultima vez.
rem  Hasta que no se ejecuta esto, los QR nuevos no funcionan en obra.
rem
rem  Se usa haciendo doble clic. No hace falta saber nada de git.
rem ===========================================================================

chcp 65001 >nul 2>&1
setlocal
cd /d "%~dp0"

echo.
echo ======================================================================
echo   PUBLICAR EN LA WEB
echo ======================================================================
echo.

rem --- Comprobar que hay algo que publicar ---------------------------------
git diff --quiet -- planos.json
if "%ERRORLEVEL%"=="0" (
    git diff --cached --quiet -- planos.json
    if "%ERRORLEVEL%"=="0" (
        echo   No hay revisiones nuevas por publicar.
        echo.
        echo   El registro no ha cambiado desde la ultima publicacion. Si acabas
        echo   de emitir un plano y sigue saliendo este mensaje, comprueba que
        echo   emitir.bat termino sin errores.
        echo.
        pause
        exit /b 0
    )
)

rem --- Mostrar que se va a publicar ----------------------------------------
echo   Se van a publicar estos cambios del registro:
echo.
git --no-pager diff --stat -- planos.json
echo.
git --no-pager diff -- planos.json | findstr /r /c:"^+ *\"id\"" /c:"^+ *\"rev\"" /c:"^+ *\"denominacion\""
echo.

set /p "SEGUIR=  Publicar ahora? (S/N): "
if /i not "%SEGUIR%"=="S" (
    echo.
    echo   Cancelado. No se ha subido nada.
    echo.
    pause
    exit /b 0
)

rem --- Publicar -------------------------------------------------------------
echo.
echo   Subiendo...
git add planos.json
git commit -m "Registro de planos actualizado" >nul
if not "%ERRORLEVEL%"=="0" (
    echo.
    echo   No se ha podido registrar el cambio. Nada subido.
    pause
    exit /b 1
)

git push
if not "%ERRORLEVEL%"=="0" (
    echo.
    echo   ATENCION: el envio a internet ha fallado.
    echo.
    echo   El cambio esta guardado en tu ordenador pero NO en la web, asi que
    echo   los QR nuevos todavia no funcionan en obra. Vuelve a ejecutar este
    echo   fichero cuando tengas conexion. Si sigue fallando, avisa.
    echo.
    pause
    exit /b 1
)

echo.
echo ======================================================================
echo   PUBLICADO
echo ======================================================================
echo.
echo   La web tarda entre uno y dos minutos en actualizarse. Despues, los
echo   QR de los planos emitidos ya responden en obra.
echo.
echo   Web: https://ines-ingenieros.github.io
echo.
pause
