@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
set "POWERSHELL=%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe"

"%POWERSHELL%" -NoProfile -ExecutionPolicy Bypass -STA -File "%SCRIPT_DIR%install_plugin_gui.ps1"

if errorlevel 1 (
  echo.
  echo KiCad AI Agent installer failed. Please copy this window output when reporting the issue.
  pause
)

endlocal
