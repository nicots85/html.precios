@echo off
echo ================================================
echo   TechnoStore - Servidor Local
echo ================================================
echo.
echo Iniciando servidor en http://localhost:8081
echo.
echo Abre tu navegador y visita:
echo   http://localhost:8081/index.html
echo.
echo Presiona Ctrl+C para detener el servidor
echo ================================================
echo.

python -m http.server 8081
