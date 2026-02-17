# Codex DMG -> Windows

This repository provides a **Windows-only runner** that extracts the macOS Codex DMG and runs the Electron app on Windows. It unpacks `app.asar`, swaps mac-only native modules for Windows builds, and launches the app with a compatible Electron runtime. It **does not** ship OpenAI binaries or assets; you must supply your own DMG and install the Codex CLI.

## Requirements
- Windows 10/11
- Node.js
- 7-Zip (`7z` in PATH)
- If 7-Zip is not installed, the runner will try `winget` or download a portable copy
- Codex CLI installed (`npm i -g @openai/codex`)

## Quick Start
1. Place your DMG in the repo root (default name `Codex.dmg`).
2. Run:

```powershell
.\scripts\run.ps1
```

Or explicitly:

```powershell
.\scripts\run.ps1 -DmgPath .\Codex.dmg
```

Or use the shortcut launcher:

```cmd
run.cmd
```

The script will:
- Extract the DMG to `work/`
- Build a Windows-ready app directory
- Auto-detect `codex.exe`
- Launch Codex

## Launcher behavior
- `run.cmd` uses profile directories under your current Windows user home:
  - Personal: `%USERPROFILE%\\.codex`
  - Work: `%USERPROFILE%\\.codex-work`
- If `work\\app` already exists, `run.cmd` automatically launches with `-Reuse`.
- To force a fresh extract/rebuild from `run.cmd`, use: `run.cmd -Rebuild`
- To force a true clean rebuild (delete extracted/app/native-build artifacts first), use: `run.cmd -CleanRebuild`
- Electron logging is quiet by default. To troubleshoot startup issues, run with `-EnableLogging`.

## Codex CLI selection (important for config.toml and MCP)
- The runner prefers standalone/global Codex CLI installs over Windsurf-bundled binaries.
- If global CLI is missing, it can still fall back to bundled paths when available on PATH.
- You can always force a specific CLI with:
  - `run.cmd -CodexCliPath "C:\\path\\to\\codex.exe"`
  - or set `CODEX_CLI_PATH` before launch.

Recommended recovery command after app updates:
1. `npm i -g @openai/codex`
2. `run.cmd -CleanRebuild -CodexCliPath "%APPDATA%\\npm\\node_modules\\@openai\\codex\\vendor\\x86_64-pc-windows-msvc\\codex\\codex.exe"`

## PATH / tool detection troubleshooting
If Codex reports tools like `git`, `ruff`, `python`, or `node` as "not on PATH", use the latest scripts in this repo.

The runner now normalizes and augments PATH before launching Electron by:
- Merging process + machine + user PATH entries
- Adding common user tool locations (pyenv shims/bin, fnm multishell node dir, cargo, go, WindowsApps, Python Scripts)
- Ensuring Git is available from standard install locations

This is specifically to prevent PATH regressions between shell sessions and launcher upgrades.

## Notes
- This is not an official OpenAI project.
- Do not redistribute OpenAI app binaries or DMG files.
- The Electron version is read from the app's `package.json` to keep ABI compatibility.

## License
MIT (For the scripts only)
