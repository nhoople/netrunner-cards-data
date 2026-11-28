"""Card JSON lives at data/rules/<side>/<type>/<id>.json.

Pack membership stays in data/rules/pool.json. A reprinted title still has one file.
"""

from __future__ import annotations

import json
from pathlib import Path

from data_paths import MANIFESTS_DIR, RULES

STORAGE: dict[str, tuple[str, ...]] = {
    "corp": ("identity", "agenda", "asset", "ice", "operation", "upgrade"),
    "runner": ("identity", "event", "hardware", "program", "resource"),
}


def card_path(card: dict) -> Path:
    side = card.get("side")
    type_ = card.get("type")
    cid = card.get("id")
    if side not in STORAGE or type_ not in STORAGE[side]:
        raise ValueError(f"{cid}: side {side!r} type {type_!r} is not a storage path")
    if not isinstance(cid, str) or not cid:
        raise ValueError(f"card is missing id: {card!r}")
    return RULES / side / type_ / f"{cid}.json"


def write_card(card: dict) -> Path:
    path = card_path(card)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(card, indent=2, ensure_ascii=False) + "\n")
    return path


def card_file(cid: str) -> Path:
    matches = sorted(RULES.glob(f"*/*/{cid}.json"))
    if len(matches) != 1:
        raise FileNotFoundError(f"{cid}: expected one card file, found {matches}")
    return matches[0]


def manifest_file(wave: str) -> Path:
    path = MANIFESTS_DIR / f"{wave}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path
