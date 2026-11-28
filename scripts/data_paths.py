"""Where each card data group lives. The scripts take their paths from here.

`data/` holds four groups, sorted by who uses them:

- `data/rules/`: what the engine runs. One rules file per title, the pool, the
  schema, and the word lists the rules files are checked against.

The README's "Layout" section names every folder.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RULES = DATA / "rules"

SCHEMA_PATH = RULES / "schema.json"
POOL_PATH = RULES / "pool.json"

# The reference vocabularies from the catalog, by file name, in the order
# `build_reference.py` writes them and `validate_cards.py` checks them.
REFERENCE_FILES: dict[str, Path] = {
    "factions.json": RULES / "factions.json",
    "subtypes.json": RULES / "subtypes.json",
    "card-types.json": RULES / "card-types.json",
    "sides.json": RULES / "sides.json",
    "card-set-types.json": DATA / "card-set-types.json",
    "card-layouts.json": DATA / "card-layouts.json",
    "ruling-sources.json": DATA / "ruling-sources.json",
    "card-sets.json": DATA / "card-sets.json",
    "card-cycles.json": DATA / "card-cycles.json",
}
