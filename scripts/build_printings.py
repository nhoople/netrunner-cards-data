#!/usr/bin/env python3
"""Write data/printings/<code>.json from the pinned Null Signal catalog.

One record per printing in a corpus set, taken from v2/printings. A
reprinted title gets one record for each set that printed it. The rules
file stays one per title.

Usage: python3 scripts/build_printings.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from nsg_catalog import load_card_sets, load_v2_printings, our_id

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = DATA / "printings"

# Booster and reprint sets whose titles were absorbed into a corpus wave.
ABSORBED = {
    "urbp": "uprising",
    "msbp": "midnight-sun",
    "mor": "magnum-opus",
}


def pack_code_for(wave: str) -> str:
    if wave == "system-update-2021":
        return "su21"
    manifest = json.loads((DATA / "manifests" / f"{wave}.json").read_text(encoding="utf-8"))
    code = manifest.get("nrdbPackCode")
    if not isinstance(code, str) or not code:
        raise SystemExit(f"{wave}: manifest is missing nrdbPackCode")
    return code


def legacy_to_wave() -> dict[str, str]:
    """Map a catalog legacy pack code to the corpus wave that stores its titles."""
    found = dict(ABSORBED)
    for path in (DATA / "manifests").glob("*.json"):
        manifest = json.loads(path.read_text(encoding="utf-8"))
        code = manifest.get("nrdbPackCode")
        wave = manifest.get("pack")
        if isinstance(code, str) and isinstance(wave, str):
            found[code] = wave
    found["su21"] = "system-update-2021"
    return found


def record(printing: dict, card_id: str, wave: str) -> dict:
    record = {
        "code": str(printing["id"]),
        "cardId": card_id,
        "pack": wave,
    }
    flavor = printing.get("flavor")
    illustrator = printing.get("illustrator")
    if isinstance(flavor, str) and flavor.strip():
        record["flavor"] = flavor
    if isinstance(illustrator, str) and illustrator.strip():
        record["illustrator"] = illustrator
    quantity = printing.get("quantity")
    position = printing.get("position")
    if isinstance(quantity, int):
        record["quantity"] = quantity
    if isinstance(position, int):
        record["position"] = position
    released_by = printing.get("released_by")
    if isinstance(released_by, str) and released_by:
        record["releasedBy"] = released_by.replace("_", "-")
    layout_id = printing.get("layout_id")
    if isinstance(layout_id, str) and layout_id:
        record["layoutId"] = layout_id
    copy_quantity = printing.get("copy_quantity")
    if isinstance(copy_quantity, int):
        record["copyQuantity"] = copy_quantity
    faces = printing.get("faces")
    if isinstance(faces, list) and faces:
        record["faces"] = [
            {
                key: face.get("copy_quantity") if key == "copyQuantity" else face.get(key)
                for key in ("flavor", "copyQuantity")
                if face.get("copy_quantity" if key == "copyQuantity" else key) is not None
            }
            for face in faces
            if isinstance(face, dict)
        ]
    return record


def main() -> int:
    pool = json.loads((DATA / "pool.json").read_text(encoding="utf-8"))
    listed = {
        wave: set(pool["waves"][wave].get("cards") or [])
        for wave in pool["corpusOrder"]
    }
    codes = legacy_to_wave()
    sets = load_card_sets()
    wave_by_set: dict[str, str] = {}
    primary_set_by_wave: dict[str, str] = {}
    for card_set in sets:
        legacy = card_set.get("legacy_code")
        if isinstance(legacy, str) and legacy in codes:
            wave_by_set[str(card_set["id"])] = codes[legacy]
    errors: list[str] = []
    for wave in pool["corpusOrder"]:
        primary = pack_code_for(wave)
        matches = [s for s in sets if s.get("legacy_code") == primary]
        if len(matches) != 1:
            errors.append(f"{wave}: expected one v2 set with legacy_code {primary!r}")
            continue
        primary_set_by_wave[wave] = str(matches[0]["id"])

    written: dict[str, dict] = {}
    seen_in_primary: dict[str, set[str]] = {wave: set() for wave in listed}

    for printing in load_v2_printings():
        set_id = printing.get("card_set_id")
        wave = wave_by_set.get(set_id) if isinstance(set_id, str) else None
        if wave is None or wave not in listed:
            continue
        catalog_id = printing.get("card_id")
        if not isinstance(catalog_id, str):
            errors.append(f"{set_id}: printing {printing.get('id')!r} has no card_id")
            continue
        card_id = our_id(catalog_id)
        if card_id not in listed[wave]:
            if set_id == primary_set_by_wave.get(wave):
                errors.append(
                    f"{wave}/{set_id}: {catalog_id!r} ({printing.get('id')}) "
                    "is printed in the primary set but not listed in pool.json"
                )
            continue
        if set_id == primary_set_by_wave.get(wave):
            seen_in_primary[wave].add(card_id)
        code = str(printing["id"])
        if code in written and written[code]["cardId"] != card_id:
            errors.append(f"code {code} used by {written[code]['cardId']} and {card_id}")
            continue
        written[code] = record(printing, card_id, wave)

    for wave, cards in listed.items():
        missing = sorted(cards - seen_in_primary[wave])
        if missing:
            errors.append(f"{wave}: pool cards missing from the primary set: {missing}")

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
