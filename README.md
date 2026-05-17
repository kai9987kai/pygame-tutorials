# pygame-tutorials

Pygame tutorial snapshots plus an advanced research-informed version of the final game.

The original lesson files stay in `Game/` as historical tutorial steps. The current playable version is:

```text
Game/Tutorial #11.py
```

## Quick Start

```powershell
pip install -r requirements.txt
python "Game\Tutorial #11.py"
```

`Tutorial #11.py` loads image and audio assets relative to its own file, so it can be launched from the repository root.

## Controls

| Action | Input |
| --- | --- |
| Start | Enter or Space |
| Move | Arrow keys or WASD |
| Shoot | Space |
| Dash | Shift or X |
| Pause | P or Escape |
| Toggle audio | M |
| Toggle high contrast | C |
| Toggle assist mode | F |
| Retry after game over | R |

## Current Features

- Sprite-group structure for bullets, enemies, pickups, and collision handling.
- Framerate-independent movement using `dt`.
- Adaptive waves that scale enemy count, health, speed, and archetype mix from score, streak, survival time, accuracy, objectives, assist mode, and recent damage.
- Enemy archetypes: raider, runner, brute, and warden, each with distinct speed, health, reward tuning, and HUD labels.
- Dash movement with a cooldown bar.
- Wave objectives, objective rewards, combo scoring, and visible challenge tiers.
- Pickups for shield, rapid fire, and healing.
- Immediate feedback through particles, floating score text, hit effects, cooldown UI, and screen shake.
- Start, pause, and game-over states.
- Persistent high score saved to `Game/save_data.json`.
- Accessibility options: audio toggle, assist mode, high-contrast HUD/cues, and pickups/enemy types labeled by symbol as well as color.

## Project Layout

```text
.
|-- Game/
|   |-- Tutorial #3.py ... Tutorial #11.py
|   |-- *.png
|   |-- *.mp3
|   `-- bg.jpg
|-- README.md
|-- CONTRIBUTING.md
|-- SECURITY.md
|-- requirements.txt
`-- .gitignore
```

## Verification

Run these checks before sharing changes:

```powershell
python -m py_compile "Game\Tutorial #11.py"
python "Game\Tutorial #11.py" --self-test
```

The self-test uses Pygame's dummy display/audio drivers and verifies that assets load, the game updates, and frames render without opening an interactive window.

## Research and Docs Used

- Adaptive game-based learning reviews report that adaptive games can improve performance, self-confidence, motivation, engagement, and interest, so Tutorial #11 uses a simple transparent adaptive wave director: https://www.frontiersin.org/journals/computer-science/articles/10.3389/fcomp.2023.1062350/full
- A 2024 systematic review found points, storylines, and feedback are common serious-game elements, and highlighted immediate feedback as motivating, so the upgrade emphasizes scoring, wave framing, and rapid visual feedback: https://link.springer.com/article/10.1007/s10459-024-10327-1
- Microsoft's Xbox Accessibility Guidelines emphasize contrast for text, HUD, health meters, and visual cues, so the upgrade includes a high-contrast toggle and avoids color-only pickup identification: https://learn.microsoft.com/en-us/gaming/accessibility/xbox-accessibility-guidelines/102
- A 2025 experience-driven adaptation review highlights telemetry, player modeling, and content adaptation, while noting rule-based systems remain practical and interpretable; the upgrade uses transparent telemetry instead of opaque AI: https://arxiv.org/abs/2505.01351
- A 2024 accessibility study argues for subtitles/visual clarity, difficulty settings, and control options as baseline features; the upgrade adds assist mode, dash controls, labels, and visual feedback channels: https://journals.sagepub.com/doi/abs/10.1177/15554120231222580
- 2024 dynamic-difficulty research cautions that no single DDA strategy works universally, so the upgrade combines adaptive waves with player-controlled assist instead of forcing one hidden difficulty curve: https://www.mdpi.com/2813-2084/3/2/12
- Pygame's current docs recommend `Clock.tick()` with delta time and document sprite groups/collision helpers, which informed the new update loop and collision structure: https://www.pygame.org/docs/
