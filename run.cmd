@echo off
setlocal

echo.
echo Select Codex profile:
echo   1^) Personal  ^(%USERPROFILE%\.codex^)
echo   2^) Work      ^(%USERPROFILE%\.codex-work^)
choice /C 12 /N /M "Enter choice [1/2]: "
if errorlevel 2 (
  set "CODEX_HOME=%USERPROFILE%\.codex-work"
) else (
  set "CODEX_HOME=%USERPROFILE%\.codex"
)
echo Using CODEX_HOME=%CODEX_HOME%
echo.

set "SCRIPT=%~dp0scripts\run.ps1"
if not exist "%SCRIPT%" (
  echo Missing %SCRIPT%
  exit /b 1
)

set "WORKDIR=%~dp0work"
set "FORCE_REBUILD="
set "CLEAN_REBUILD="

if /I "%~1"=="-Rebuild" (
  set "FORCE_REBUILD=1"
  shift
)
if /I "%~1"=="--rebuild" (
  set "FORCE_REBUILD=1"
  shift
)
if /I "%~1"=="-CleanRebuild" (
  set "FORCE_REBUILD=1"
  set "CLEAN_REBUILD=1"
  shift
)
if /I "%~1"=="--clean-rebuild" (
  set "FORCE_REBUILD=1"
  set "CLEAN_REBUILD=1"
  shift
)

if defined CLEAN_REBUILD (
  echo Performing clean rebuild of extracted artifacts...
  if exist "%WORKDIR%\extracted" rmdir /s /q "%WORKDIR%\extracted"
  if exist "%WORKDIR%\electron" rmdir /s /q "%WORKDIR%\electron"
  if exist "%WORKDIR%\app" rmdir /s /q "%WORKDIR%\app"
  if exist "%WORKDIR%\native-builds" rmdir /s /q "%WORKDIR%\native-builds"
)

if defined FORCE_REBUILD (
  powershell -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT%" -WorkDir "%WORKDIR%" %*
) else if exist "%WORKDIR%\app" (
  powershell -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT%" -WorkDir "%WORKDIR%" -Reuse %*
) else (
  powershell -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT%" -WorkDir "%WORKDIR%" %*
)
