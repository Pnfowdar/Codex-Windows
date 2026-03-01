@echo off
setlocal

set "SYSROOT=%SystemRoot%"
if not defined SYSROOT set "SYSROOT=%WINDIR%"
if not defined SYSROOT set "SYSROOT=C:\Windows"
set "CHOICE_EXE=%SYSROOT%\System32\choice.exe"
set "POWERSHELL_EXE=%SYSROOT%\System32\WindowsPowerShell\v1.0\powershell.exe"

if not exist "%CHOICE_EXE%" (
  echo Missing required executable: %CHOICE_EXE%
  exit /b 1
)
if not exist "%POWERSHELL_EXE%" (
  echo Missing required executable: %POWERSHELL_EXE%
  exit /b 1
)

echo.
echo Select Codex profile:
echo   1^) Personal  ^(%USERPROFILE%\.codex^)
echo   2^) Work      ^(%USERPROFILE%\.codex-work^)
%CHOICE_EXE% /C 12 /N /M "Enter choice [1/2]: "
if errorlevel 255 exit /b %errorlevel%
if errorlevel 2 (
  set "CODEX_HOME=%USERPROFILE%\.codex-work"
) else (
  set "CODEX_HOME=%USERPROFILE%\.codex"
)
if not exist "%CODEX_HOME%" (
  mkdir "%CODEX_HOME%" >nul 2>&1
  if errorlevel 1 (
    echo Failed to create CODEX_HOME directory: %CODEX_HOME%
    exit /b 1
  )
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

set "HAS_REUSE_ARG="
for %%A in (%*) do (
  if /I "%%~A"=="-Reuse" set "HAS_REUSE_ARG=1"
  if /I "%%~A"=="--reuse" set "HAS_REUSE_ARG=1"
)

if defined CLEAN_REBUILD (
  echo Performing clean rebuild of extracted artifacts...
  if exist "%WORKDIR%\extracted" rmdir /s /q "%WORKDIR%\extracted"
  if exist "%WORKDIR%\electron" rmdir /s /q "%WORKDIR%\electron"
  if exist "%WORKDIR%\app" rmdir /s /q "%WORKDIR%\app"
  if exist "%WORKDIR%\native-builds" rmdir /s /q "%WORKDIR%\native-builds"
)

if defined FORCE_REBUILD (
  "%POWERSHELL_EXE%" -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT%" -WorkDir "%WORKDIR%" %*
) else if exist "%WORKDIR%\app" (
  if defined HAS_REUSE_ARG (
    "%POWERSHELL_EXE%" -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT%" -WorkDir "%WORKDIR%" %*
  ) else (
    "%POWERSHELL_EXE%" -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT%" -WorkDir "%WORKDIR%" -Reuse %*
  )
) else (
  "%POWERSHELL_EXE%" -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT%" -WorkDir "%WORKDIR%" %*
)
