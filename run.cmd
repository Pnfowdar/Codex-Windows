@echo off
setlocal

echo.
echo Select Codex profile:
echo   1^) Personal  ^(C:\Users\pnfow\.codex^)
echo   2^) Work      ^(C:\Users\pnfow\.codex-work^)
choice /C 12 /N /M "Enter choice [1/2]: "
if errorlevel 2 (
  set "CODEX_HOME=C:\Users\pnfow\.codex-work"
) else (
  set "CODEX_HOME=C:\Users\pnfow\.codex"
)
echo Using CODEX_HOME=%CODEX_HOME%
echo.

set "SCRIPT=%~dp0scripts\run.ps1"
if not exist "%SCRIPT%" (
  echo Missing %SCRIPT%
  exit /b 1
)

set "WORKDIR=%~dp0work"

if exist "%WORKDIR%\app" (
  powershell -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT%" -WorkDir "%WORKDIR%" -Reuse %*
) else (
  powershell -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT%" -WorkDir "%WORKDIR%" %*
)
