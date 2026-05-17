# Security Policy

This is a local Pygame tutorial project. It does not run a web server, accept network traffic, or process untrusted remote input by default.

## Supported Versions

Security fixes should target the current playable version:

```text
Game/Tutorial #11.py
```

Older tutorial snapshots are kept mainly for learning history. Fix them only when the issue affects users who run those files directly.

## Reporting a Vulnerability

If you find a security issue:

1. Do not publish exploit steps in a public issue if they could harm other users.
2. Share the affected file, the impact, and a minimal reproduction.
3. Include your Python version, Pygame version, and operating system.
4. If this repository is hosted on GitHub, use private vulnerability reporting when available.

## Local Risk Areas

The main risks for this project are local-file and dependency issues:

- Asset loading: game code should only load expected files from the local `Game/` directory.
- Save data: `Game/save_data.json` should contain simple score data only.
- Dependencies: keep `requirements.txt` minimal and avoid unnecessary packages.
- Runtime logs: do not commit logs that might include local usernames or paths.
- Untrusted assets: do not add downloaded images, audio, or archives without checking license and source.

## Dependency Hygiene

Install dependencies from `requirements.txt`:

```powershell
pip install -r requirements.txt
```

When changing dependencies:

- Prefer well-maintained packages.
- Avoid executing install scripts from unknown sources.
- Document why the dependency is needed.
- Re-run the verification commands in `README.md`.

## Hardening Guidelines

- Keep network access out of the game unless there is a clear feature need.
- Avoid `eval`, dynamic imports from user-controlled strings, and shell execution from gameplay code.
- Keep file writes limited to documented runtime files such as `Game/save_data.json`.
- Validate any future user-editable config before using it.
