#!/usr/bin/env python3
"""Write the v2 reference vocabularies under data/.

Factions, subtypes, card types, sides, set types, layouts, and ruling
sources. Ids are written in corpus form: factions and subtypes use the
spelling stored on card files (haas-bioroid, code gate). Other ids keep
the catalog spelling.

Usage: python3 scripts/build_reference.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from nsg_catalog import load_v2_reference

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


def write_json(path: Path, document: list) -> None:
    path.write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def factions() -> list[dict]:
    found = []
    for raw in load_v2_reference("factions.json"):
        record = {
            "id": str(raw["id"]).replace("_", "-"),
            "name": raw["name"],
            "sideId": raw["side_id"],
            "color": raw["color"],
            "isMini": raw["is_mini"],
        }
        if raw.get("description"):
            record["description"] = raw["description"]
        found.append(record)
    return found


def subtypes() -> list[dict]:
    # Stored spelling is the vocabulary name lowercased: 'code gate', 'g-mod'.
    return [
        {"id": str(raw["name"]).lower(), "name": raw["name"]}
        for raw in load_v2_reference("card_subtypes.json")
    ]


def card_types() -> list[dict]:
    return [
        {"id": raw["id"], "name": raw["name"], "sideId": raw["side_id"]}
        for raw in load_v2_reference("card_types.json")
    ]


def sides() -> list[dict]:
    return [
        {"id": raw["id"], "name": raw["name"]}
        for raw in load_v2_reference("sides.json")
    ]


def card_set_types() -> list[dict]:
    return [
        {"id": raw["id"], "name": raw["name"], "description": raw["description"]}
        for raw in load_v2_reference("card_set_types.json")
    ]


def card_layouts() -> list[dict]:
    return [
        {"id": raw["id"], "name": raw["name"], "description": raw["description"]}
        for raw in load_v2_reference("card_layouts.json")
    ]


def ruling_sources() -> list[dict]:
    found = []
    for raw in load_v2_reference("ruling_sources.json"):
        record = {"id": raw["id"], "name": raw["name"]}
        if raw.get("url"):
            record["url"] = raw["url"]
        found.append(record)
    return found


BUILDERS = {
    "factions.json": factions,
    "subtypes.json": subtypes,
    "card-types.json": card_types,
    "sides.json": sides,
    "card-set-types.json": card_set_types,
    "card-layouts.json": card_layouts,
    "ruling-sources.json": ruling_sources,
}


def main() -> int:
    for name, build in BUILDERS.items():
        records = build()
        write_json(DATA / name, records)
        print(f"Wrote {len(records)} records to data/{name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
