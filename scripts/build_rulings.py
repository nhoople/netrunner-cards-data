#!/usr/bin/env python3
"""Write data/rulings/<cardId>.json from the pinned Null Signal catalog.

The catalog stores a NetrunnerDB ruling snapshot at v2/rulings/. Only
rulings the rules team has verified are kept. A ruling explains the current
text. It does not replace the rules file.

Usage: python3 scripts/build_rulings.py
"""
from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

from build_printings import resolve_id
from card_layout import STORAGE
from nsg_catalog import fetch_rulings, load_pack_cards, load_pin

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = DATA / "rulings"

APOSTROPHE = re.compile(
    r"['\u2018\u2019\u201B\u2039\u203A\u275B\u275C\uFF07\u300C\u300D]"
)


def text_to_id(title: str) -> str:
    """Same id the catalog uses for v2/rulings/<id>.json."""
    text = APOSTROPHE.sub("", title.lower())
    text = unicodedata.normalize("NFD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    return "_".join(part for part in re.split(r"[^a-z0-9]+", text) if part)


def ruling_record(raw: dict) -> dict:
    if not isinstance(raw, dict):
        raise ValueError("ruling is not an object")
    record = {
        "dateUpdate": raw["date_update"],
        "rulesTeamVerified": raw["nsg_rules_team_verified"],
    }
    if "text_ruling" in raw:
        record["text"] = raw["text_ruling"]
    else:
        record["question"] = raw["question"]
        record["answer"] = raw["answer"]
    return record


def verified_rulings(raw_list: list[dict]) -> list[dict]:
    return [ruling_record(raw) for raw in raw_list if raw.get("nsg_rules_team_verified") is True]


def known_ids() -> set[str]:
    found: set[str] = set()
    for side, types in STORAGE.items():
        for type_ in types:
            directory = DATA / side / type_
            if not directory.is_dir():
                continue
            found.update(path.stem for path in directory.glob("*.json"))
    return found


def nsg_id_for_titles(known: set[str]) -> dict[str, str]:
    """Map a catalog ruling filename to the corpus card id."""
    pin = load_pin()
    cache = ROOT / pin["cacheDir"] / pin["ref"] / "pack"
    codes = sorted(path.stem for path in cache.glob("*.json"))
    found: dict[str, str] = {}
    for code in codes:
        for card in load_pack_cards(code):
            title = card.get("title")
            if not isinstance(title, str):
                continue
            card_id = resolve_id(title, known)
            if card_id is None:
                continue
            nsg_id = text_to_id(title)
            previous = found.get(nsg_id)
            if previous is not None and previous != card_id:
                raise SystemExit(f"{nsg_id} maps to both {previous} and {card_id}")
            found[nsg_id] = card_id
    return found


def main() -> int:
    known = known_ids()
    by_nsg_id = nsg_id_for_titles(known)
    source = fetch_rulings()
    OUT.mkdir(parents=True, exist_ok=True)
    for stale in OUT.glob("*.json"):
        stale.unlink()

    written = 0
    skipped = 0
    unverified = 0
    for path in sorted(source.glob("*.json")):
        raw_list = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(raw_list, list) or not raw_list:
            raise SystemExit(f"{path.name}: expected a non-empty ruling list")
        nsg_ids = {raw.get("card_id") for raw in raw_list}
        if len(nsg_ids) != 1 or not isinstance(next(iter(nsg_ids)), str):
            raise SystemExit(f"{path.name}: rulings do not share one card_id")
        nsg_id = next(iter(nsg_ids))
        card_id = by_nsg_id.get(nsg_id)
        if card_id is None:
            skipped += 1
            continue
        rulings = verified_rulings(raw_list)
        if not rulings:
            unverified += 1
            continue
        dest = OUT / f"{card_id}.json"
        if dest.exists():
            raise SystemExit(f"{path.name}: {card_id} already has rulings from another file")
        document = {"cardId": card_id, "rulings": rulings}
        dest.write_text(
            json.dumps(document, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        written += 1
    print(
        f"Wrote {written} ruling files to {OUT.relative_to(ROOT)}; "
        f"skipped {unverified} with no verified ruling and {skipped} outside the corpus"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
