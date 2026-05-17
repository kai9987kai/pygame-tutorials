# Contributing

Thanks for improving this Pygame tutorial project. Keep changes small, playable, and easy to understand for learners.

## Setup

```powershell
pip install -r requirements.txt
python "Game\Tutorial #11.py"
```

Use Python 3.12 or another current Python 3 version that supports Pygame 2.6.

## Development Workflow

1. Keep original tutorial snapshots intact unless the change explicitly fixes a historical lesson.
2. Put new gameplay work in `Game/Tutorial #11.py` or a later numbered tutorial file.
3. Load assets through paths relative to the script, not the current shell directory.
4. Prefer Pygame primitives and `pygame.sprite.Group` helpers over custom global collision loops when practical.
5. Keep generated files out of git, including `Game/save_data.json`, cache folders, and runtime logs.

## Code Style

- Use clear class names for gameplay concepts.
- Keep constants near the top of the file.
- Keep comments short and only where they explain non-obvious behavior.
- Avoid hidden difficulty changes: if the game adapts, expose the relevant state in the HUD or docs.
- Preserve accessibility controls when adding new mechanics.

## Gameplay Checklist

Before submitting gameplay changes, confirm:

- The player can start, pause, retry, and quit.
- Movement, shooting, dash, pickups, enemies, and wave transitions still work.
- High contrast mode still labels important cues without relying only on color.
- Assist mode still provides a real reduction in pressure.
- The high score file is generated only at runtime and is not committed.

## Verification

Run:

```powershell
python -m py_compile "Game\Tutorial #11.py"
python "Game\Tutorial #11.py" --self-test
```

For visual changes, also launch the game manually and play at least one full wave.

## Pull Request Notes

Include:

- What changed.
- How it was tested.
- Any new controls or assets.
- Any accessibility impact.
- Any known tradeoffs or follow-up work.
