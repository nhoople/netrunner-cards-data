"""Where each card data group lives. The scripts take their paths from here.

`data/` holds four groups, sorted by who uses them:

- `data/rules/`: what the engine runs. One rules file per title, the pool, the
  schema, and the word lists the rules files are checked against.
- `data/print/`: what the card shows. Printed text, printings, and the set,
  set type, cycle, and layout records.

The README's "Layout" section names every folder.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RULES = DATA / "rules"
PRINT = DATA / "print"

SCHEMA_PATH = RULES / "schema.json"
POOL_PATH = RULES / "pool.json"
PRINTED_DIR = PRINT / "printed"
PRINTINGS_DIR = PRINT / "printings"

# The reference vocabularies from the catalog, by file name, in the order
# `build_reference.py` writes them and `validate_cards.py` checks them.
REFERENCE_FILES: dict[str, Path] = {
    "factions.json": RULES / "factions.json",
    "subtypes.json": RULES / "subtypes.json",
    "card-types.json": RULES / "card-types.json",
    "sides.json": RULES / "sides.json",
    "card-set-types.json": PRINT / "card-set-types.json",
    "card-layouts.json": PRINT / "card-layouts.json",
    "ruling-sources.json": DATA / "ruling-sources.json",
    "card-sets.json": PRINT / "card-sets.json",
    "card-cycles.json": PRINT / "card-cycles.json",
}
