#!/usr/bin/env python3
"""Copy deck limits, printed text, and format legality from the pinned catalog.

Deck limit is one number per title, written onto the rules file. The printed
sentence lives in data/printed/. Formats, card pools, restrictions, and
rotations are separate documents. Pack release date, cycle, and size are
added to each wave in pool.json.

Usage: python3 scripts/build_catalog_facts.py
"""
from __future__ import annotations

import json
from pathlib import Path

from build_printings import ABSORBED, pack_code_for, resolve_id
from build_rulings import known_ids, nsg_id_for_titles
from card_layout import card_file
from nsg_catalog import fetch_catalog_archive, load_pack_cards

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

# Booster and reprint sets whose titles already live on a corpus wave.
ABSORBED_CODES = {
    "mor": "magnum-opus",
    "urbp": "uprising",
    "msbp": "midnight-sun",
}


def partition_card_ids(nsg_ids: list, mapping: dict[str, str]) -> tuple[list[str], list[str]]:
    mapped: list[str] = []
    unmapped: list[str] = []
    for nsg_id in nsg_ids:
        card_id = mapping.get(nsg_id)
        if card_id is None:
            unmapped.append(nsg_id)
        else:
            mapped.append(card_id)
    return mapped, unmapped


def legacy_to_wave() -> dict[str, str]:
    found: dict[str, str] = {}
    for path in (DATA / "manifests").glob("*.json"):
        manifest = json.loads(path.read_text(encoding="utf-8"))
        code = manifest.get("nrdbPackCode")
        wave = manifest.get("pack")
        if isinstance(code, str) and isinstance(wave, str):
            found[code] = wave
    found["su21"] = "system-update-2021"
    return found


def wave_for_set(card_set: dict, codes: dict[str, str]) -> str | None:
    legacy = card_set.get("legacy_code")
    if not isinstance(legacy, str):
        return None
    return codes.get(legacy) or ABSORBED_CODES.get(legacy)


def insert_deck_limit(text: str, limit: int) -> str:
    """Add deckLimit after the id line without rewriting the rest of the file."""
    lines = text.splitlines(keepends=True)
    rewritten: list[str] = []
    inserted = False
    for line in lines:
        if line.startswith('  "deckLimit":'):
            continue
        rewritten.append(line)
        if not inserted and line.startswith('  "id":'):
            rewritten.append(f'  "deckLimit": {limit},\n')
            inserted = True
    if not inserted:
        raise ValueError("card file has no id line")
    return "".join(rewritten)


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, document: dict | list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def restriction_document(raw: dict, mapping: dict[str, str]) -> dict:
    document = {
        "id": raw["id"],
        "name": raw["name"],
        "formatId": raw["format_id"],
        "dateStart": raw["date_start"],
    }
    unmapped: list[str] = []
    for source, dest in (("banned", "banned"), ("restricted", "restricted")):
        if source not in raw:
            continue
        mapped, missed = partition_card_ids(raw[source], mapping)
        document[dest] = mapped
        unmapped.extend(missed)
    for source, dest in (
        ("points", "points"),
        ("global_penalty", "globalPenalty"),
        ("universal_faction_cost", "universalFactionCost"),
    ):
        if source not in raw:
            continue
        grouped: dict[str, list[str]] = {}
        for cost, nsg_ids in raw[source].items():
            mapped, missed = partition_card_ids(nsg_ids, mapping)
            grouped[str(cost)] = mapped
            unmapped.extend(missed)
        document[dest] = grouped
    if "subtypes" in raw:
        document["subtypes"] = raw["subtypes"]
    if "point_limit" in raw:
        document["pointLimit"] = raw["point_limit"]
    if "max_3_point_agendas" in raw:
        document["max3PointAgendas"] = raw["max_3_point_agendas"]
    if unmapped:
        document["unmappedCardIds"] = sorted(set(unmapped))
    return document


def main() -> int:
    catalog = fetch_catalog_archive()
    known = known_ids()
    codes = legacy_to_wave()
    card_sets = load_json(catalog / "v2" / "card_sets.json")
    set_wave = {card_set["id"]: wave_for_set(card_set, codes) for card_set in card_sets}
    pool = load_json(DATA / "pool.json")
    errors: list[str] = []

    limits: dict[str, int] = {}
    printed: dict[str, dict] = {}
    for wave in pool["corpusOrder"]:
        listed = set(pool["waves"][wave]["cards"])
        for pack_code in (pack_code_for(wave), *ABSORBED.get(wave, ())):
            for card in load_pack_cards(pack_code):
                title = card.get("title")
                if not isinstance(title, str):
                    continue
                card_id = resolve_id(title, known)
                if card_id is None or card_id not in listed:
                    continue
                limit = card.get("deck_limit")
                if not isinstance(limit, int):
                    errors.append(f"{card_id}: catalog deck_limit {limit!r}")
                elif card_id in limits and limits[card_id] != limit:
                    errors.append(f"{card_id}: deck limit {limits[card_id]} and {limit}")
                else:
                    limits[card_id] = limit
                text = card.get("text") if isinstance(card.get("text"), str) else ""
                stripped = card.get("stripped_text") if isinstance(card.get("stripped_text"), str) else ""
                record = {"cardId": card_id, "text": text, "strippedText": stripped}
                previous = printed.get(card_id)
                if previous is not None and previous != record:
                    errors.append(f"{card_id}: printed text differs across printings")
                else:
                    printed[card_id] = record

    missing_limits = sorted(known - set(limits))
    if missing_limits:
        errors.append(f"no deck limit for {missing_limits}")
    if errors:
        print("\n".join(errors))
        print(f"FAILED with {len(errors)} error(s)")
        return 1

    for card_id, limit in sorted(limits.items()):
        path = card_file(card_id)
        path.write_text(insert_deck_limit(path.read_text(encoding="utf-8"), limit), encoding="utf-8")

    printed_dir = DATA / "printed"
    if printed_dir.exists():
        for stale in printed_dir.glob("*.json"):
            stale.unlink()
    for card_id, record in sorted(printed.items()):
        write_json(printed_dir / f"{card_id}.json", record)

    for wave_name in pool["corpusOrder"]:
        primary = pack_code_for(wave_name)
        match = next(card_set for card_set in card_sets if card_set.get("legacy_code") == primary)
        wave = pool["waves"][wave_name]
        updated = {}
        for key, value in wave.items():
            updated[key] = value
            if key == "status":
                updated["dateRelease"] = match["date_release"]
                updated["cycle"] = match["card_cycle_id"].replace("_", "-")
                updated["size"] = match["size"]
        pool["waves"][wave_name] = updated
    (DATA / "pool.json").write_text(
        json.dumps(pool, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )

    mapping = nsg_id_for_titles(known)
    pools_dir = DATA / "card-pools"
    if pools_dir.exists():
        for stale in pools_dir.glob("*.json"):
            stale.unlink()
    for path in sorted((catalog / "v2" / "card_pools").glob("*.json")):
        for raw in load_json(path):
            waves: list[str] = []
            outside: list[str] = []
            for set_id in raw.get("card_set_ids") or []:
                wave_name = set_wave.get(set_id)
                if wave_name is None:
                    outside.append(set_id)
                elif wave_name not in waves:
                    waves.append(wave_name)
            document = {
                "id": raw["id"],
                "name": raw["name"],
                "formatId": raw["format_id"],
                "cycles": [cycle.replace("_", "-") for cycle in raw.get("card_cycle_ids") or []],
                "waves": waves,
            }
            if outside:
                document["outsideSets"] = outside
            write_json(pools_dir / f"{raw['id']}.json", document)

    formats_dir = DATA / "formats"
    if formats_dir.exists():
        for stale in formats_dir.glob("*.json"):
            stale.unlink()
    for path in sorted((catalog / "v2" / "formats").glob("*.json")):
        raw = load_json(path)
        snapshots = []
        for snapshot in raw["snapshots"]:
            entry = {
                "id": snapshot["id"],
                "dateStart": snapshot["date_start"],
                "cardPoolId": snapshot["card_pool_id"],
            }
            if snapshot.get("restriction_id"):
                entry["restrictionId"] = snapshot["restriction_id"]
            if snapshot.get("active") is True:
                entry["active"] = True
            snapshots.append(entry)
        write_json(formats_dir / f"{raw['id']}.json", {
            "id": raw["id"],
            "name": raw["name"],
            "snapshots": snapshots,
        })

    restrictions_dir = DATA / "restrictions"
    if restrictions_dir.exists():
        for stale in restrictions_dir.glob("*.json"):
            stale.unlink()
    seen_restrictions: set[str] = set()
    for path in sorted((catalog / "v2" / "restrictions").rglob("*.json")):
        raw = load_json(path)
        restriction_id = raw["id"]
        if restriction_id in seen_restrictions:
            raise SystemExit(f"duplicate restriction id {restriction_id}")
        seen_restrictions.add(restriction_id)
        write_json(restrictions_dir / f"{restriction_id}.json", restriction_document(raw, mapping))

    rotations = []
    for raw in load_json(catalog / "rotations.json"):
        tokens = set(raw["rotated"])
        waves: list[str] = []
        for card_set in card_sets:
            cycle = card_set["card_cycle_id"].replace("_", "-")
            set_id = card_set["id"].replace("_", "-")
            if card_set.get("legacy_code") in tokens or cycle in tokens or set_id in tokens:
                wave_name = set_wave.get(card_set["id"])
                if wave_name and wave_name not in waves:
                    waves.append(wave_name)
        rotations.append({
            "id": raw["code"],
            "name": raw["name"],
            "dateStart": raw["date_start"],
            "cycles": raw["rotated"],
            "waves": waves,
        })
    write_json(DATA / "rotations.json", rotations)

    print(
        f"Deck limits on {len(limits)} cards; "
        f"{len(printed)} printed texts; "
        f"{len(list(formats_dir.glob('*.json')))} formats; "
        f"{len(list(pools_dir.glob('*.json')))} card pools; "
        f"{len(seen_restrictions)} restrictions; "
        f"{len(rotations)} rotations"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
