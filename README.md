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

## PATH/MCP hardening (persistent fix)
Root cause observed:
- On startup, Codex's shell environment import could overwrite `PATH` with temporary `arg0`/Codex-only entries.
- That removed `System32` and common tool locations, causing failures like:
  - `'where.exe' is not recognized`
  - MCP stdio servers or tool discovery failing in-app.

What this repo now does to prevent recurrence:
- Normalizes and repairs process `Path`/`PATH` before launch.
- Auto-injects common Windows tool paths (`System32`, Node, Git, etc.).
- Patches the unpacked app bootstrap (`main-*.js`) so startup shell-env import cannot clobber `PATH`.
  - `PATH/Path` from shell-env is ignored.
  - Launcher baseline `CODEX_BASE_PATH` is restored into `process.env.PATH`.
- Re-applies this patch on each launch/rebuild, so DMG/version updates stay protected.
- Auto-hardens the active profile `config.toml` at launch by setting:
  - `experimental_windows_sandbox = false`
  - `elevated_windows_sandbox = false`
  - `shell_snapshot = false`

Profile consistency:
- `run.cmd` selects profile via `%USERPROFILE%\.codex` (Personal) or `%USERPROFILE%\.codex-work` (Work).
- The hardening runs for whichever profile is selected, so both are covered.

Recommended post-update check:
1. `run.cmd -CleanRebuild`
2. In Codex terminal, run:
   - `where.exe where`
   - `where.exe node`
   - `where.exe npm`
   - `where.exe git`

### Rebuild guarantee
- Yes, rebuilds should keep working.
- `scripts/run.ps1` reapplies PATH hardening and bootstrap patching each run.
- If a future Codex build changes bootstrap structure significantly, update `Update-MainBootstrapPath` in `scripts/run.ps1` to match the new startup block.

## Troubleshooting
Run this inside the Codex app terminal to quickly verify PATH/tool visibility:

```bat
echo %PATH%
where.exe where
where.exe node
where.exe npm
where.exe git
```

Expected:
- `where.exe where` resolves to `C:\Windows\System32\where.exe`
- `where.exe node` / `npm` / `git` return one or more valid paths

If checks fail:
1. Fully close Codex (all windows/processes).
2. Run `run.cmd -CleanRebuild`.
3. Re-run the health check commands above.

## Notes
- This is not an official OpenAI project.
- Do not redistribute OpenAI app binaries or DMG files.
- The Electron version is read from the app's `package.json` to keep ABI compatibility.

## License
MIT (For the scripts only)
