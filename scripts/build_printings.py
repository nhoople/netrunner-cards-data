#!/usr/bin/env python3
"""Write data/printings/<code>.json from the pinned Null Signal catalog.

One record per printing in a corpus pack. A reprinted title gets one record
for each pack that printed it. The rules file stays one per title.

Usage: python3 scripts/build_printings.py
"""
from __future__ import annotations

import json
import re
import sys
import unicodedata
from pathlib import Path

from nsg_catalog import load_pack_cards
from spin_common import slugify

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = DATA / "printings"

# Booster and reprint packs whose titles were absorbed into a corpus wave.
ABSORBED = {
    "uprising": ("urbp",),
    "midnight-sun": ("msbp",),
    "magnum-opus": ("mor",),
}

# spin_common.slugify already resolves these. Kept for a naive slug that does not.
NAIVE_TO_CORPUS = {
    "doppelg-nger": "doppelganger",
    "chaos-theory-w-nderkind": "chaos-theory-wunderkind",
    "the-maker-s-eye": "the-makers-eye",
    "aesop-s-pawnshop": "aesops-pawnshop",
    "hadrian-s-wall": "hadrians-wall",
}


def pack_code_for(wave: str) -> str:
    if wave == "system-update-2021":
        return "su21"
    manifest = json.loads((DATA / "manifests" / f"{wave}.json").read_text(encoding="utf-8"))
    code = manifest.get("nrdbPackCode")
    if not isinstance(code, str) or not code:
        raise SystemExit(f"{wave}: manifest is missing nrdbPackCode")
    return code


def legacy_slug(title: str) -> str:
    """Apostrophes become hyphens. Some corpus ids were minted that way."""
    t = title.replace("™", "").replace("®", "").replace("©", "")
    t = unicodedata.normalize("NFKD", t)
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = t.lower()
    t = t.replace("“", "").replace("”", "").replace('"', "")
    t = t.replace(".", "-").replace(":", " ").replace("!", "").replace("*", "")
    t = t.replace("(", " ").replace(")", " ")
    t = re.sub(r"[^a-z0-9]+", "-", t)
    return t.strip("-")


def resolve_id(title: str, known: set[str]) -> str | None:
    cid = slugify(title)
    if cid in known:
        return cid
    mapped = NAIVE_TO_CORPUS.get(cid)
    if mapped in known:
        return mapped
    older = legacy_slug(title)
    if older in known:
        return older
    return None


def record(card: dict, card_id: str, wave: str) -> dict:
    printing = {
        "code": str(card["code"]),
        "cardId": card_id,
        "pack": wave,
    }
    flavor = card.get("flavor")
    illustrator = card.get("illustrator")
    if isinstance(flavor, str) and flavor.strip():
        printing["flavor"] = flavor
    if isinstance(illustrator, str) and illustrator.strip():
        printing["illustrator"] = illustrator
    quantity = card.get("quantity")
    position = card.get("position")
    if isinstance(quantity, int):
        printing["quantity"] = quantity
    if isinstance(position, int):
        printing["position"] = position
    return printing


def main() -> int:
    pool = json.loads((DATA / "pool.json").read_text(encoding="utf-8"))
    known: set[str] = set()
    for wave in pool["waves"].values():
        known.update(wave.get("cards") or [])

    written: dict[str, dict] = {}
    errors: list[str] = []

    for wave in pool["corpusOrder"]:
        listed = set(pool["waves"][wave]["cards"])
        primary = pack_code_for(wave)
        seen_in_primary: set[str] = set()
        for pack_code in (primary, *ABSORBED.get(wave, ())):
            for card in load_pack_cards(pack_code):
                title = card.get("title")
                code = card.get("code")
                if not isinstance(title, str) or not isinstance(code, str):
                    errors.append(f"{pack_code}: card missing title or code")
                    continue
                card_id = resolve_id(title, known)
                if card_id is None or card_id not in listed:
                    if pack_code == primary:
                        errors.append(
                            f"{wave}/{pack_code}: {title!r} ({code}) "
                            f"resolved to {card_id!r}, which this pack does not list"
                        )
                    continue
                if pack_code == primary:
                    seen_in_primary.add(card_id)
                code = str(code)
                if code in written and written[code]["cardId"] != card_id:
                    errors.append(f"code {code} used by {written[code]['cardId']} and {card_id}")
                    continue
                written[code] = record(card, card_id, wave)
        missing = sorted(listed - seen_in_primary)
        if missing:
            errors.append(f"{wave}: pool cards missing from {primary}: {missing}")

    if errors:
        print("\n".join(errors))
        print(f"FAILED with {len(errors)} error(s)")
        return 1

    if OUT.exists():
        for path in OUT.glob("*.json"):
            path.unlink()
    OUT.mkdir(parents=True, exist_ok=True)
    for code in sorted(written):
        path = OUT / f"{code}.json"
        path.write_text(json.dumps(written[code], indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {len(written)} printings to {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
