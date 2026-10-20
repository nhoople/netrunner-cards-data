#!/usr/bin/env python3
"""Absorb Revised Core Set (core2) — reprints only; write manifest, no card JSON.

Fetch: python3 scripts/nsg_catalog.py fetch core2
Floor v1.134.0 (Crimson Dust) → paired v1.135.0.
All 132 titles already exist under normalized corpus ids (0 new clears).
Defer tdc.

Ids via nsg_catalog.our_id on the v2 catalog id. Fail closed if any
title cannot be matched to an existing corpus id. Known naive→corpus
mismatches from the title-slug era (kept as manifest documentation):

  doppelg-nger            → doppelganger
  chaos-theory-w-nderkind → chaos-theory-wunderkind
  the-maker-s-eye         → the-makers-eye
  aesop-s-pawnshop        → aesops-pawnshop
  hadrian-s-wall          → hadrians-wall
"""
from __future__ import annotations

import json
from card_layout import manifest_file
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from nsg_catalog import card_type, faction_slug, load_set_cards, our_id, subtype_names
from spin_common import ROOT

WAVE = "revised-core"
PACK = "core2"
EXPECTED = 132

# Historical record of title-slug mismatches, kept in the manifest.
# v2 catalog ids resolve through nsg_catalog.our_id; this map is
# documentation only.
NAIVE_TO_CORPUS: dict[str, str] = {
    "doppelg-nger": "doppelganger",
    "chaos-theory-w-nderkind": "chaos-theory-wunderkind",
    "the-maker-s-eye": "the-makers-eye",
    "aesop-s-pawnshop": "aesops-pawnshop",
    "hadrian-s-wall": "hadrians-wall",
}


def corpus_ids() -> set[str]:
    ids: set[str] = set()
    data = ROOT / "data"
    skip_names = {
        "pool.json",
        "schema.json",
        "nsg-catalog-pin.json",
        "supported-unsupported-allowlist.json",
    }
    for path in data.rglob("*.json"):
        if path.name.startswith("_") or path.name in skip_names:
            continue
        try:
            obj = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict) and isinstance(obj.get("id"), str):
            ids.add(obj["id"])
    return ids


def resolve_id(raw: dict, known: set[str]) -> str:
    cid = our_id(raw["id"])
    if cid in known:
        return cid
    raise SystemExit(
        f"FAIL CLOSED: catalog id {raw['id']!r} resolves to {cid!r} "
        "but no matching corpus id exists"
    )


def main() -> None:
    pack = load_set_cards(PACK)
    assert len(pack) == EXPECTED, f"expected {EXPECTED}, got {len(pack)}"
    known = corpus_ids()
    reprint_ids: list[str] = []
    for raw in pack:
        cid = resolve_id(raw, known)
        reprint_ids.append(cid)

    if len(set(reprint_ids)) != EXPECTED:
        raise SystemExit(
            f"FAIL CLOSED: duplicate resolved ids "
            f"({len(reprint_ids)} titles → {len(set(reprint_ids))} unique)"
        )

    manifest = {
        "pack": WAVE,
        "nrdbPackCode": PACK,
        "count": EXPECTED,
        "written": 0,
        "reprintSkipped": EXPECTED,
        "status": "supported",
        "notes": (
            "Revised Core Set (core2) reprints absorb v1.135.0. "
            "Wrote 0 files; absorbed 132/132 titles as reprints of earlier "
            "waves (0 new clears). Slug mismatches "
            "(Doppelgänger / Wünderkind / Maker's Eye / Aesop's / Hadrian's) "
            "resolve to existing corpus ids via nsg_catalog.our_id. "
            " Defer tdc. CR pin v26.03."
        ),
        "cards": reprint_ids,
        "reprintIdsFromEarlierWaves": sorted(reprint_ids),
        "clears": [],
        "slugMismatchAbsorbs": [
            {"naive": k, "corpusId": v} for k, v in sorted(NAIVE_TO_CORPUS.items())
        ],
    }
    manifest_file(WAVE).write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote 0 card files; reprintSkipped={EXPECTED}")
    print("REPRINTS=" + json.dumps(reprint_ids))
    print("CLEARS=[]")


if __name__ == "__main__":
    main()
