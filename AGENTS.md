# Agent notes

This is the card definitions dataset of the Netrunner project. Full instructions for coding agents are in the project repo's [`CLAUDE.md`](https://github.com/nhoople/netrunner/blob/main/CLAUDE.md), and the git and release process is in [`docs/git-hygiene.md`](https://github.com/nhoople/netrunner/blob/main/docs/git-hygiene.md).

- The four repositories stay separate: `netrunner-engine`, `netrunner-cards-data`, `netrunner-comprehensive-rules-data`, and `netrunner-game`. The game and the engine consume the others by release tag, not by `master` and not as workspace packages. Do not recommend merging them, an npm workspace, or Turborepo unless asked to change that release model.
- Card definitions belong here, not in the engine. Effect IR kind names follow the verb rules in the engine's `src/effects/primitiveNames.ts`.
- Setup: `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt -r requirements-dev.txt`.
- Before committing, add or update a test for the behavior and run `.venv/bin/ruff format scripts tests && .venv/bin/python scripts/validate_cards.py && .venv/bin/python tests/test_validate_cards.py && .venv/bin/python tests/test_nsg_catalog.py && .venv/bin/python tests/test_check_labels.py && .venv/bin/python tests/test_layout_map.py && .venv/bin/python scripts/check_labels.py --report` (the CI `validate` job, which checks formatting with `ruff format --check scripts tests`).
- `scripts/check_labels.py` compares ability labels with `data/printed/` and keeps a shrink-only baseline in `scripts/baselines/labels.json`. When a change adds a label or fixes its wording, regenerate it with `python3 scripts/check_labels.py --write` and commit the result.
- The README's "Layout" section lists every folder. A new folder needs a row there, or `tests/test_layout_map.py` fails.
- Work on a `claude/<descriptive-name>` branch and merge by pull request; `master` takes no direct push.
