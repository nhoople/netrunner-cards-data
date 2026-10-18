#!/usr/bin/env python3
"""Validate card JSON under data/ against data/schema.json and pool consistency.

Usage: python3 scripts/validate-cards.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from card_layout import STORAGE
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
SCHEMA = json.loads((DATA / "schema.json").read_text())
POOL = json.loads((DATA / "pool.json").read_text())
ALLOWLIST_PATH = DATA / "supported-unsupported-allowlist.json"


def load_unsupported_allowlist() -> dict[str, str]:
    """Card ids allowed to keep non-empty unsupported under status=supported."""
    if not ALLOWLIST_PATH.is_file():
        return {}
    raw = json.loads(ALLOWLIST_PATH.read_text())
    cards = raw.get("cards") or {}
    if not isinstance(cards, dict):
        raise SystemExit(
            f"{ALLOWLIST_PATH.relative_to(ROOT)}: 'cards' must be an object"
        )
    return {str(k): str(v) for k, v in cards.items()}


CLASSES = {"static", "paid", "conditional", "play", "subroutine"}
CLASS_RULE = {
    "static": "9.3.7a",
    "paid": "9.3.7b",
    "conditional": "9.3.7c",
    "play": "9.3.7d",
    "subroutine": "9.3.7e",
}
FLAG_WORDS = {"access", "interface", "interrupt", "persistent", "once_per_turn"}
FLAG_RULE = {
    "access": "9.3.6b",
    "interface": "9.3.6c",
    "interrupt": "9.3.6d",
    "persistent": "9.3.6e",
    "once_per_turn": "9.3.6g",
}
RESTRICTION_TARGETS = {
    "play",
    "rez",
    "score",
    "steal",
    "steal_from_protecting_server",
    "trash",
}


def check_abilities(path: Path, raw: dict) -> int:
    """CR 9.3 shape. A card with no abilities array is still on the old hooks."""
    abilities = raw.get("abilities")
    if abilities is None:
        return 0
    errors = 0
    if not isinstance(abilities, list):
        print(f"{path}: abilities is not an array")
        return 1
    for index, ability in enumerate(abilities):
        where = f"{path} abilities[{index}]"
        if not isinstance(ability, dict):
            print(f"{where}: not an object")
            errors += 1
            continue
        kind = ability.get("class")
        if kind not in CLASSES:
            print(f"{where}: class {kind!r} is not a CR 9.3 ability")
            errors += 1
            continue
        if kind == "static" and ability.get("instructions") is not None:
            print(f"{where}: a static ability cannot contain instructions")
            errors += 1
        if kind == "static" and not ability.get("declaration") and not ability.get("restrictions"):
            print(f"{where}: a static ability needs a declaration or a restriction")
            errors += 1
        if kind == "paid" and not isinstance(ability.get("cost"), dict):
            print(f"{where}: a paid ability needs a cost")
            errors += 1
        if kind == "paid" and not ability.get("instructions"):
            print(f"{where}: a paid ability needs instructions")
            errors += 1
        if kind == "conditional" and not ability.get("trigger"):
            print(f"{where}: a conditional ability needs a trigger")
            errors += 1
        if kind == "conditional" and not ability.get("instructions"):
            print(f"{where}: a conditional ability needs an instruction")
            errors += 1
        if kind in {"play", "subroutine"} and not ability.get("instructions"):
            print(f"{where}: a {kind} ability needs instructions")
            errors += 1
        if ability.get("rule") != CLASS_RULE[kind]:
            print(f"{where}: rule must be {CLASS_RULE[kind]} (CR 9.3.7)")
            errors += 1
        flag_err = _check_flag(ability, where)
        if flag_err:
            print(flag_err)
            errors += 1
        if ability.get("host") is not None and kind != "conditional":
            print(f"{where}: host belongs on a conditional ability")
            errors += 1
        host_ability = ability.get("hostAbility")
        if host_ability is not None:
            if kind != "conditional" or not ability.get("host"):
                print(f"{where}: hostAbility needs a hosted conditional ability")
                errors += 1
            elif not any(
                isinstance(other, dict) and other.get("id") == host_ability
                for other in abilities
                if isinstance(abilities, list)
            ):
                print(f"{where}: hostAbility {host_ability!r} is not an ability on this card")
                errors += 1
        for restriction in ability.get("restrictions") or []:
            if not isinstance(restriction, dict) or restriction.get("appliesTo") not in RESTRICTION_TARGETS:
                print(f"{where}: restriction appliesTo is unknown")
                errors += 1
    return errors


def _flag_list(flag: object) -> list[object] | None:
    if flag is None:
        return []
    if isinstance(flag, list):
        return flag
    if isinstance(flag, (str, dict)):
        return [flag]
    return None


def _check_flag(ability: dict, where: str) -> str | None:
    items = _flag_list(ability.get("flag"))
    if items is None:
        return f"{where}: flag is unknown"
    seen: set[str] = set()
    threats = 0
    expected: list[str] = []
    for item in items:
        if isinstance(item, str):
            if item not in FLAG_WORDS or item in seen:
                return f"{where}: flag is unknown"
            seen.add(item)
            expected.append(FLAG_RULE[item])
            continue
        if (
            isinstance(item, dict)
            and set(item) == {"threat"}
            and isinstance(item.get("threat"), (int, float))
            and item["threat"] >= 0
        ):
            threats += 1
            if threats > 1:
                return f"{where}: flag is unknown"
            expected.append("9.3.6f")
            continue
        return f"{where}: flag is unknown"
    actual = ability.get("flagRule")
    if not expected:
        if actual is not None:
            return f"{where}: flagRule does not match flag"
        return None
    got = actual if isinstance(actual, list) else [actual]
    if got != expected:
        return f"{where}: flagRule must be {expected}"
    return None


def storage_dirs() -> list[Path]:
    dirs: list[Path] = []
    for side, types in STORAGE.items():
        for type_ in types:
            dirs.append(DATA / side / type_)
    return dirs


def main() -> int:
    validator = Draft202012Validator(SCHEMA)
    errors = 0
    card_ids: dict[str, Path] = {}

    for directory in storage_dirs():
        if not directory.is_dir():
            print(f"storage directory missing: {directory.relative_to(ROOT)}")
            errors += 1
            continue
        side, type_ = directory.parts[-2:]
        for path in sorted(directory.glob("*.json")):
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
            if raw.get("side") != side or raw.get("type") != type_:
                print(
                    f"{path.relative_to(ROOT)}: side/type "
                    f"{raw.get('side')}/{raw.get('type')} != path {side}/{type_}"
                )
                errors += 1
            if cid in card_ids:
                print(f"duplicate id {cid!r}: {card_ids[cid]} and {path}")
                errors += 1
            card_ids[cid] = path
            wave = raw.get("wave")
            waves = POOL.get("waves") or {}
            if wave and (wave not in waves or cid not in (waves[wave].get("cards") or [])):
                print(f"{path.relative_to(ROOT)}: wave {wave!r} does not list {cid}")
                errors += 1
            errors += check_abilities(path, raw)

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
        listed = waves[name].get("cards") or []
        missing_anywhere = [c for c in listed if c not in card_ids]
        if missing_anywhere:
            print(f"{name}: pool cards with no file: {missing_anywhere}")
            errors += 1

    listed_anywhere = {cid for wave in waves.values() for cid in (wave.get("cards") or [])}
    unlisted = [cid for cid in sorted(card_ids) if cid not in listed_anywhere]
    if unlisted:
        print(f"card files missing from every pool wave: {unlisted}")
        errors += 1

    # supported ⇒ empty unsupported unless explicitly allowlisted.
    allow = load_unsupported_allowlist()
    for name, wave in waves.items():
        if wave.get("status") != "supported":
            continue
        for cid in wave.get("cards") or []:
            path = card_ids.get(cid)
            if path is None:
                continue
            notes = json.loads(path.read_text()).get("unsupported") or []
            if not notes:
                continue
            if cid in allow and str(allow[cid]).strip():
                continue
            print(
                f"{name}/{cid}: status=supported but unsupported={notes!r}; "
                f"clear the card or add a reason under "
                f"{ALLOWLIST_PATH.relative_to(ROOT)} cards.{cid}"
            )
            errors += 1

    if errors:
        print(f"FAILED with {errors} error(s)")
        return 1
    print(
        f"OK: {len(card_ids)} cards across {len(storage_dirs())} side/type dirs; "
        f"pool corpusOrder={corpus}; "
        f"supported empty-unsupported invariant ok "
        f"(allowlist={len(allow)})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
