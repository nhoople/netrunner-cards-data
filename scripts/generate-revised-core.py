#!/usr/bin/env python3
"""Absorb Revised Core Set (core2) — reprints only; write manifest, no card JSON.

Fetch: python3 scripts/nrdb_catalog.py fetch core2
Floor v1.134.0 (Crimson Dust) → paired v1.135.0.
All 132 titles already exist under normalized corpus ids (0 new clears).
Never kick mo/mor. Defer tdc.

Slug via spin_common.slugify (apostrophes/umlauts). Fail closed if any
title cannot be matched to an existing corpus id. Known naive→corpus
mismatches (documented for operators who slugify without NFKD/apostrophe
stripping):

  doppelg-nger            → doppelganger
  chaos-theory-w-nderkind → chaos-theory-wunderkind
  the-maker-s-eye         → the-makers-eye
  aesop-s-pawnshop        → aesops-pawnshop
  hadrian-s-wall          → hadrians-wall
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from nrdb_catalog import load_pack_cards
from spin_common import ROOT, slugify

OUT = ROOT / "data" / "revised-core"
WAVE = "revised-core"
PACK = "core2"
EXPECTED = 132

# Safety map for naive slugifiers that keep apostrophes as `-s-` / drop
# combining marks incorrectly. spin_common.slugify already yields the
# right-hand values; this map is fail-closed insurance + documentation.
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
        "nrdb-catalog-pin.json",
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


def resolve_id(title: str, known: set[str]) -> str:
    cid = slugify(title)
    if cid in known:
        return cid
    # Explicit naive→corpus overrides (and slugify already-correct ids).
    mapped = NAIVE_TO_CORPUS.get(cid, cid)
    if mapped in known:
        return mapped
    for naive, corpus in NAIVE_TO_CORPUS.items():
        if slugify(title.replace("'", "").replace("\u2019", "")) == corpus or cid == naive:
            if corpus in known:
                return corpus
    raise SystemExit(
        f"FAIL CLOSED: title {title!r} slugifies to {cid!r} "
        f"(mapped {mapped!r}) but no matching corpus id exists"
    )


def main() -> None:
    pack = sorted(load_pack_cards(PACK), key=lambda c: c.get("position", 0))
    assert len(pack) == EXPECTED, f"expected {EXPECTED}, got {len(pack)}"
    known = corpus_ids()
    reprint_ids: list[str] = []
    for raw in pack:
        cid = resolve_id(raw["title"], known)
        reprint_ids.append(cid)

    if len(set(reprint_ids)) != EXPECTED:
        raise SystemExit(
            f"FAIL CLOSED: duplicate resolved ids "
            f"({len(reprint_ids)} titles → {len(set(reprint_ids))} unique)"
        )

    OUT.mkdir(parents=True, exist_ok=True)
    # Never write card JSON — reprints only.
    for stale in OUT.glob("*.json"):
        if stale.name != "_manifest.json":
            raise SystemExit(f"unexpected card JSON in absorb wave: {stale}")

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
            "resolve to existing corpus ids via spin_common.slugify. "
            "Never kick mo/mor. Defer tdc. CR pin v26.03."
        ),
        "cards": reprint_ids,
        "reprintIdsFromEarlierWaves": sorted(reprint_ids),
        "clears": [],
        "slugMismatchAbsorbs": [
            {"naive": k, "corpusId": v} for k, v in sorted(NAIVE_TO_CORPUS.items())
        ],
    }
    (OUT / "_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote 0 card files; reprintSkipped={EXPECTED}")
    print("REPRINTS=" + json.dumps(reprint_ids))
    print("CLEARS=[]")


if __name__ == "__main__":
    main()
