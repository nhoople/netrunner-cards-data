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

from build_printings import pack_code_for
from build_rulings import known_ids
from card_layout import card_file
from nsg_catalog import fetch_catalog_archive, load_v2_cards, our_id, subtype_names

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


def printed_face(raw: dict, fallback_title: str) -> dict:
    """One stored face record from a v2 card or face record.

    The face title is optional upstream (SYNC's back face keeps the front
    name, and most flip faces carry only stripped_title); fall back to the
    stripped title, then to the card's title.
    """
    record = {
        "title": raw.get("title") or raw.get("stripped_title") or fallback_title,
        "strippedTitle": raw.get("stripped_title") or fallback_title,
        "text": raw.get("text") if isinstance(raw.get("text"), str) else "",
        "strippedText": raw.get("stripped_text") if isinstance(raw.get("stripped_text"), str) else "",
    }
    subtypes = subtype_names(raw)
    if subtypes:
        record["subtypes"] = subtypes
    if raw.get("base_link") is not None:
        record["link"] = raw["base_link"]
    return record


def rules_unique(rules: dict) -> bool:
    """Whether a rules file encodes uniqueness the way the engine reads it."""
    if rules.get("unique") is True:
        return True
    return any(
        isinstance(ability.get("declaration"), dict)
        and ability["declaration"].get("field") == "unique"
        and ability["declaration"].get("value") is True
        for ability in rules.get("abilities") or []
        if isinstance(ability, dict)
    )


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
    for catalog_id, card in sorted(load_v2_cards().items()):
        card_id = our_id(catalog_id)
        if card_id not in known:
            continue
        limit = card.get("deck_limit")
        if type(limit) is not int:
            errors.append(f"{card_id}: catalog deck_limit {limit!r}")
        else:
            limits[card_id] = limit
        text = card.get("text") if isinstance(card.get("text"), str) else ""
        stripped = card.get("stripped_text") if isinstance(card.get("stripped_text"), str) else ""
        stripped_title = (
            card.get("stripped_title") if isinstance(card.get("stripped_title"), str) else ""
        )
        record = {
            "cardId": card_id,
            "text": text,
            "strippedText": stripped,
            "strippedTitle": stripped_title,
        }
        if isinstance(card.get("attribution"), str) and card["attribution"]:
            record["attribution"] = card["attribution"]
        if isinstance(card.get("layout_id"), str) and card["layout_id"]:
            record["layoutId"] = card["layout_id"]
        # v2/cards carries every face of a double-sided identity: the card
        # record is the front face and `faces` lists the remaining faces.
        # Stored faces keep the front face first.
        extra_faces = card.get("faces")
        if isinstance(extra_faces, list) and extra_faces:
            record["faces"] = [printed_face(card, stripped_title)] + [
                printed_face(face, stripped_title) for face in extra_faces
            ]
        printed[card_id] = record

        # Fail closed when a source fact the rules file must encode drifts
        # from what is stored, so a catalog refresh cannot silently drop it.
        rules = load_json(card_file(card_id))
        if bool(card.get("is_unique")) != rules_unique(rules):
            errors.append(
                f"{card_id}: catalog is_unique {card.get('is_unique')!r} is not "
                "encoded in the rules file (CR 10.3.1d)"
            )
        if (rules.get("subtypes") or []) != subtype_names(card):
            errors.append(f"{card_id}: stored subtypes differ from the catalog")
        if card.get("card_type_id") not in ("corp_identity", "runner_identity"):
            expected_influence = card.get("influence_cost")
            stored_influence = rules.get("influence")
            if expected_influence is None and stored_influence is not None:
                errors.append(f"{card_id}: rules store influence but the catalog has no bar")
            elif expected_influence is not None and (stored_influence or 0) != expected_influence:
                errors.append(
                    f"{card_id}: stored influence {stored_influence!r} != "
                    f"catalog influence_cost {expected_influence!r}"
                )

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

    mapping = {
        catalog_id: our_id(catalog_id)
        for catalog_id in load_v2_cards()
        if our_id(catalog_id) in known
    }
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
