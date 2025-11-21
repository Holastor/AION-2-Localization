@echo off
CHCP 65001 > nul
setlocal

echo.
echo =======================================================
echo     Запуск PowerShell-обновлятора...
echo =======================================================
echo.

:: PowerShell запускается с параметрами:
PowerShell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0AION2_Updater.ps1"

endlocal
goto :EOF