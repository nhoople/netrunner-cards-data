"""Where each card data group lives. The scripts take their paths from here.

`data/` holds four groups, sorted by who uses them:

- `data/rules/`: what the engine runs. One rules file per title, the pool, the
  schema, and the word lists the rules files are checked against.
- `data/print/`: what the card shows. Printed text, printings, and the set,
  set type, cycle, and layout records.
- `data/formats/`: which cards are legal where. Formats, card pools,
  restrictions, and rotations.
- `data/rulings/`: verified rulings, one file per title, and the ruling
  sources.

The dataset's own bookkeeping sits outside `data/`, in `bookkeeping/`: the
per-wave manifests the generators write, the supported-but-unsupported
allowlist, and the catalog pin.

The README's "Layout" section names every folder.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RULES = DATA / "rules"
PRINT = DATA / "print"
FORMATS = DATA / "formats"
RULINGS = DATA / "rulings"
BOOKKEEPING = ROOT / "bookkeeping"

SCHEMA_PATH = RULES / "schema.json"
POOL_PATH = RULES / "pool.json"
PRINTED_DIR = PRINT / "printed"
PRINTINGS_DIR = PRINT / "printings"
FORMATS_DIR = FORMATS / "formats"
CARD_POOLS_DIR = FORMATS / "card-pools"
RESTRICTIONS_DIR = FORMATS / "restrictions"
ROTATIONS_PATH = FORMATS / "rotations.json"
RULINGS_DIR = RULINGS / "rulings"
MANIFESTS_DIR = BOOKKEEPING / "manifests"
ALLOWLIST_PATH = BOOKKEEPING / "supported-unsupported-allowlist.json"
CATALOG_PIN_PATH = BOOKKEEPING / "nsg-catalog-pin.json"

# The reference vocabularies from the catalog, by file name, in the order
# `build_reference.py` writes them and `validate_cards.py` checks them.
REFERENCE_FILES: dict[str, Path] = {
    "factions.json": RULES / "factions.json",
    "subtypes.json": RULES / "subtypes.json",
    "card-types.json": RULES / "card-types.json",
    "sides.json": RULES / "sides.json",
    "card-set-types.json": PRINT / "card-set-types.json",
    "card-layouts.json": PRINT / "card-layouts.json",
    "ruling-sources.json": RULINGS / "ruling-sources.json",
    "card-sets.json": PRINT / "card-sets.json",
    "card-cycles.json": PRINT / "card-cycles.json",
}
