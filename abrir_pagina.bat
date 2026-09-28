@echo off
title SOLARILUXURY x CENTRAL CEE — Servidor Local
chcp 65001 >nul
cd /d "%~dp0"

echo ==============================================================
echo         SOLARILUXURY x CENTRAL CEE — ARCHIVE 2026
echo ==============================================================
echo.

:: Detectar ejecutable de Python
where python >nul 2>nul
if %errorlevel% equ 0 (
    set "PY_CMD=python"
) else (
    if exist "C:\Users\avalo\AppData\Local\Programs\Python\Python312\python.exe" (
        set "PY_CMD=C:\Users\avalo\AppData\Local\Programs\Python\Python312\python.exe"
    ) else (
        echo [ERROR] No se encontro Python instalado en el sistema.
        echo Por favor instala Python o agregalo al PATH.
        pause
        exit /b 1
    )
)

echo [1/2] Iniciando servidor Django...
echo [2/2] Abriendo tu navegador en http://127.0.0.1:8000/ ...
echo.
echo --------------------------------------------------------------
echo   TIENDA LOCAL:    http://127.0.0.1:8000/
echo   PANEL ADMIN:     http://127.0.0.1:8000/admin/
echo   USUARIO ADMIN:   admin
echo   CLAVE ADMIN:     Solariluxury2026!
echo --------------------------------------------------------------
echo.
echo Presiona Ctrl + C o cierra esta ventana para detener el servidor.
echo ==============================================================
echo.

:: Abrir el navegador tras 1.5 segundos cuando Django este listo
start /b "" cmd /c "timeout /t 2 /nobreak >nul & start http://127.0.0.1:8000/"

:: Iniciar Django Server
"%PY_CMD%" mi_proyecto\manage.py runserver 127.0.0.1:8000
