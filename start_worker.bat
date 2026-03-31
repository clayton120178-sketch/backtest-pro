@echo off
title BacktestPro Worker
echo ========================================
echo   BacktestPro Worker - Iniciando...
echo ========================================
echo.

cd /d "%~dp0"
python python/worker.py

echo.
echo Worker encerrado. Pressione qualquer tecla para fechar.
pause >nul
