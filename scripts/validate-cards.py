#!/usr/bin/env python3
"""Validate card JSON under data/ against data/schema.json and pool consistency.

Usage: python3 scripts/validate-cards.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
SCHEMA = json.loads((DATA / "schema.json").read_text())
POOL = json.loads((DATA / "pool.json").read_text())

# Manifests are pack metadata, not card defs.
SKIP_NAMES = {"_manifest.json"}


def wave_dirs() -> list[Path]:
    return sorted(
        p for p in DATA.iterdir() if p.is_dir() and not p.name.startswith(".")
    )


def main() -> int:
    validator = Draft202012Validator(SCHEMA)
    errors = 0
    card_ids: dict[str, Path] = {}

    for wave_dir in wave_dirs():
        for path in sorted(wave_dir.glob("*.json")):
            if path.name in SKIP_NAMES:
                continue
            raw = json.loads(path.read_text())
            for err in sorted(validator.iter_errors(raw), key=lambda e: list(e.path)):
                print(f"{path.relative_to(ROOT)}: {err.message}")
                errors += 1
            cid = raw.get("id")
            if not cid:
                print(f"{path}: missing id")
                errors += 1
                continue
            if cid != path.stem:
                print(f"{path}: id {cid!r} != filename stem {path.stem!r}")
                errors += 1
            if cid in card_ids:
                print(f"duplicate id {cid!r}: {card_ids[cid]} and {path}")
                errors += 1
            card_ids[cid] = path
            wave = raw.get("wave")
            if wave and wave != wave_dir.name:
                print(f"{path}: wave {wave!r} != directory {wave_dir.name!r}")
                errors += 1

    corpus = POOL.get("corpusOrder") or []
    waves = POOL.get("waves") or {}
    for name in corpus:
        if name == "next-release":
            print("pool.json still has placeholder corpusOrder entry 'next-release'")
            errors += 1
            continue
        if name not in waves:
            print(f"corpusOrder entry {name!r} missing from waves")
            errors += 1
            continue
        wave = waves[name]
        listed = wave.get("cards") or []
        wave_dir = DATA / name
        if not wave_dir.is_dir():
            print(f"wave directory missing: {wave_dir}")
            errors += 1
            continue
        on_disk = sorted(
            p.stem for p in wave_dir.glob("*.json") if p.name not in SKIP_NAMES
        )
        # Pool may list reprints that live in another wave dir — only require
        # that every on-disk card appears in the pool list for that wave when
        # the wave owns its files 1:1 (midnight-sun / gateway written counts).
        missing_from_pool = [c for c in on_disk if c not in listed]
        if missing_from_pool:
            print(f"{name}: on-disk cards not in pool: {missing_from_pool}")
            errors += 1
        missing_files = [c for c in listed if c not in on_disk and c not in card_ids]
        # Reprints may live in another wave; allow if present anywhere.
        missing_anywhere = [c for c in listed if c not in card_ids]
        if missing_anywhere:
            print(f"{name}: pool cards with no file: {missing_anywhere}")
            errors += 1

    if errors:
        print(f"FAILED with {errors} error(s)")
        return 1
    print(
        f"OK: {len(card_ids)} cards across {len(wave_dirs())} waves; "
        f"pool corpusOrder={corpus}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
