# App Review and 10x Roadmap

## What changed in this pass

- Added a Basics Coding Coach directly above the left-side editor. It gives one tiny step at a time, shows exactly where to work, inserts safe starter code, and runs the mission check from the same panel.
- Reworked the Basics mission copy for younger readers. The wording is short, concrete, and action-first.
- Fixed false-positive mission validation in Basics. Several missions could previously pass because the starter code already had comments, `def`, or `for` loops.
- Updated mission seeding so existing databases receive mission copy and validation improvements, not just brand-new databases.
- Fixed the mission loading error fallback to target the actual overlay element.

## Roadmap Execution Update

- Shipped a visual mission roadmap inside the mission drawer, plus a Today’s Focus button that jumps younger learners to the next useful mission.
- Shipped read-aloud for mission details and Coding Coach steps using browser speech synthesis.
- Shipped Coding Coach modes: Help Place It and Type Myself.
- Shipped inline syntax rescue cards for indentation, missing symbols, missing pairs, and name mistakes.
- Shipped a mission-complete celebration modal with concept reinforcement.
- Shipped concept badges for mission lists and mission detail screens.
- Shipped a lightweight teacher/focus affordance through Today’s Focus.
- Shipped pair-mode labels for Solo, Driver, and Navigator.
- Shipped sandbox mode that pauses auto-save while kids experiment.
- Shipped sound feedback with a mute toggle.
- Shipped shareable project snapshots with canvas image, mission progress, concept, and code preview.
- Upgraded Minecraft 2D with creative/survival mode, a larger block palette, crafting, day/night, caves, biome hints, wandering mobs, TNT, torches, world save/load, and a quest tracker.

## Repo Review

The repo already has a strong foundation: a simple Flask app, persistent saves, version history, mission progress, an admin view, and a fun set of games. The biggest product gap is not the games themselves; it is the learning bridge between "read a mission" and "change code confidently." For a 7- or 9-year-old, raw code plus a modal is still too abstract. The app needs more visible scaffolding, fewer hidden rules, and more immediate cause-and-effect.

The main technical risk is that most product behavior lives in `app.py` and `templates/game.html`. That makes the app easy to scan today, but harder to grow. The next big upgrade should split seed data, validation rules, and frontend mission coaching into smaller modules.

## 15 Ways To Make The App Better

1. Done: visual mission map in the mission drawer.
2. Done: read-aloud mission and coach instructions.
3. Done: Type Myself and Help Place It coach modes.
4. Done: inline syntax rescue cards.
5. Done: celebration screen with concept reinforcement.
6. Done: concept badges.
7. First pass done: Today’s Focus for adult-directed next steps.
8. First pass done: Solo, Driver, and Navigator pair-mode labels.
9. Done: sandbox mode that pauses auto-save.
10. First pass done: sound feedback with mute toggle.
11. Done: Minecraft 2D now has creative/survival, block palette, crafting, day/night, caves, biome hints, mobs, TNT, torches, and saved worlds.
12. Done: Minecraft quest tracker.
13. First pass done: Coding Coach reveals each Basics mission step-by-step.
14. Done: project snapshots.
15. First pass done: rendered-page JavaScript smoke check added to verification workflow.

## Next Engineering Moves

- Move game templates and missions out of `app.py` into structured seed files.
- Move the game page JavaScript into a static module so it can be tested and linted.
- Add mission validation tests for every Basics mission.
- Add Playwright smoke tests that start a mission, insert coach code, run, and validate.
