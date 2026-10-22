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


def check_printings(card_ids: dict[str, Path], waves: dict) -> int:
    directory = DATA / "printings"
    if not directory.is_dir():
        print("printings directory missing: data/printings")
        return 1
    errors = 0
    seen: dict[str, set[str]] = {}
    for path in sorted(directory.glob("*.json")):
        raw = json.loads(path.read_text(encoding="utf-8"))
        code = raw.get("code")
        card_id = raw.get("cardId")
        pack = raw.get("pack")
        if code != path.stem:
            print(f"{path.relative_to(ROOT)}: code {code!r} != filename")
            errors += 1
        if not isinstance(card_id, str) or card_id not in card_ids:
            print(f"{path.relative_to(ROOT)}: cardId {card_id!r} has no rules file")
            errors += 1
            continue
        wave = waves.get(pack) if isinstance(pack, str) else None
        listed = (wave or {}).get("cards") or []
        if card_id not in listed:
            print(f"{path.relative_to(ROOT)}: pack {pack!r} does not list {card_id}")
            errors += 1
        for field in ("flavor", "illustrator"):
            if field in raw and not isinstance(raw[field], str):
                print(f"{path.relative_to(ROOT)}: {field} is not a string")
                errors += 1
        for field in ("quantity", "position"):
            if type(raw.get(field)) is not int:
                print(f"{path.relative_to(ROOT)}: {field} must be an integer")
                errors += 1
        if not isinstance(raw.get("releasedBy"), str) or not raw["releasedBy"]:
            print(f"{path.relative_to(ROOT)}: releasedBy must be a non-empty string")
            errors += 1
        if "layoutId" in raw and not isinstance(raw["layoutId"], str):
            print(f"{path.relative_to(ROOT)}: layoutId is not a string")
            errors += 1
        if "copyQuantity" in raw and type(raw["copyQuantity"]) is not int:
            print(f"{path.relative_to(ROOT)}: copyQuantity must be an integer")
            errors += 1
        faces = raw.get("faces")
        if faces is not None:
            if not isinstance(faces, list) or not faces:
                print(f"{path.relative_to(ROOT)}: faces must be a non-empty list")
                errors += 1
            else:
                for face in faces:
                    if not isinstance(face, dict) or set(face) - {"flavor", "copyQuantity"}:
                        print(f"{path.relative_to(ROOT)}: face {face!r} is not a flavor/copyQuantity record")
                        errors += 1
                        continue
                    if "flavor" in face and not isinstance(face["flavor"], str):
                        print(f"{path.relative_to(ROOT)}: face flavor is not a string")
                        errors += 1
                    if "copyQuantity" in face and type(face["copyQuantity"]) is not int:
                        print(f"{path.relative_to(ROOT)}: face copyQuantity must be an integer")
                        errors += 1
        if isinstance(pack, str):
            seen.setdefault(card_id, set()).add(pack)
    for name, wave in waves.items():
        for card_id in wave.get("cards") or []:
            if name not in seen.get(card_id, set()):
                print(f"{name}/{card_id}: no printing")
                errors += 1
    return errors


def check_rulings(card_ids: dict[str, Path]) -> int:
    directory = DATA / "rulings"
    if not directory.is_dir():
        print("rulings directory missing: data/rulings")
        return 1
    errors = 0
    for path in sorted(directory.glob("*.json")):
        raw = json.loads(path.read_text(encoding="utf-8"))
        card_id = raw.get("cardId")
        if card_id != path.stem or card_id not in card_ids:
            print(f"{path.relative_to(ROOT)}: cardId {card_id!r} has no rules file")
            errors += 1
            continue
        rulings = raw.get("rulings")
        if not isinstance(rulings, list) or not rulings:
            print(f"{path.relative_to(ROOT)}: rulings must be a non-empty list")
            errors += 1
            continue
        for index, ruling in enumerate(rulings):
            where = f"{path.relative_to(ROOT)} rulings[{index}]"
            if not isinstance(ruling, dict):
                print(f"{where}: not an object")
                errors += 1
                continue
            if not isinstance(ruling.get("dateUpdate"), str) or not ruling["dateUpdate"]:
                print(f"{where}: dateUpdate is missing")
                errors += 1
            if ruling.get("rulesTeamVerified") is not True:
                print(f"{where}: rulesTeamVerified is not true")
                errors += 1
            has_text = isinstance(ruling.get("text"), str) and ruling["text"]
            has_question = isinstance(ruling.get("question"), str) and ruling["question"]
            has_answer = isinstance(ruling.get("answer"), str) and ruling["answer"]
            if has_text == (has_question or has_answer):
                print(f"{where}: needs text, or a question and an answer")
                errors += 1
            allowed = {"dateUpdate", "rulesTeamVerified", "text", "question", "answer"}
            extra = set(ruling) - allowed
            if extra:
                print(f"{where}: unknown fields {sorted(extra)}")
                errors += 1
    return errors


def check_printed(card_ids: dict[str, Path]) -> int:
    directory = DATA / "printed"
    if not directory.is_dir():
        print("printed directory missing: data/printed")
        return 1
    errors = 0
    seen: set[str] = set()
    for path in sorted(directory.glob("*.json")):
        raw = json.loads(path.read_text(encoding="utf-8"))
        card_id = raw.get("cardId")
        if card_id != path.stem or card_id not in card_ids:
            print(f"{path.relative_to(ROOT)}: cardId {card_id!r} has no rules file")
            errors += 1
            continue
        seen.add(card_id)
        for field in ("text", "strippedText", "strippedTitle"):
            if not isinstance(raw.get(field), str):
                print(f"{path.relative_to(ROOT)}: {field} must be a string")
                errors += 1
        stripped = raw.get("strippedText")
        if isinstance(stripped, str) and "<" in stripped:
            print(f"{path.relative_to(ROOT)}: strippedText carries HTML markup")
            errors += 1
        if "attribution" in raw and not isinstance(raw["attribution"], str):
            print(f"{path.relative_to(ROOT)}: attribution must be a string")
            errors += 1
        if "layoutId" in raw and not isinstance(raw["layoutId"], str):
            print(f"{path.relative_to(ROOT)}: layoutId must be a string")
            errors += 1
        faces = raw.get("faces")
        if faces is not None:
            if not isinstance(faces, list) or len(faces) < 2:
                print(f"{path.relative_to(ROOT)}: faces must list at least two faces")
                errors += 1
            else:
                face_fields = {"title", "strippedTitle", "text", "strippedText", "subtypes", "link"}
                for index, face in enumerate(faces):
                    if (
                        not isinstance(face, dict)
                        or not {"text", "strippedText"} <= set(face)
                        or set(face) - face_fields
                    ):
                        print(f"{path.relative_to(ROOT)}: faces[{index}] has unknown or missing fields")
                        errors += 1
                        continue
                    if not isinstance(face["text"], str) or not isinstance(face["strippedText"], str):
                        print(f"{path.relative_to(ROOT)}: faces[{index}] text fields must be strings")
                        errors += 1
                    for field in ("title", "strippedTitle"):
                        if field in face and not isinstance(face[field], str):
                            print(f"{path.relative_to(ROOT)}: faces[{index}] {field} must be a string")
                            errors += 1
                    if "subtypes" in face and (
                        not isinstance(face["subtypes"], list)
                        or not all(isinstance(name, str) for name in face["subtypes"])
                    ):
                        print(f"{path.relative_to(ROOT)}: faces[{index}] subtypes must be strings")
                        errors += 1
                    if "link" in face and type(face["link"]) is not int:
                        print(f"{path.relative_to(ROOT)}: faces[{index}] link must be an integer")
                        errors += 1
                first = faces[0]
                if isinstance(first, dict) and (
                    first.get("text") != raw.get("text")
                    or first.get("strippedText") != raw.get("strippedText")
                ):
                    print(f"{path.relative_to(ROOT)}: faces[0] must repeat the front-face text")
                    errors += 1
    # A printing with extra faces (other than copy-layout printings, whose
    # faces share one text) needs one printed face per printing face, plus
    # the front face at index 0.
    printing_faces: dict[str, int] = {}
    printings_dir = DATA / "printings"
    if printings_dir.is_dir():
        for path in sorted(printings_dir.glob("*.json")):
            raw_printing = json.loads(path.read_text(encoding="utf-8"))
            extra = raw_printing.get("faces")
            if isinstance(extra, list) and raw_printing.get("layoutId") != "copy":
                card_id = raw_printing.get("cardId")
                if isinstance(card_id, str):
                    printing_faces[card_id] = max(printing_faces.get(card_id, 0), len(extra))
    for card_id, extra_count in sorted(printing_faces.items()):
        path = directory / f"{card_id}.json"
        if not path.is_file():
            continue
        faces = json.loads(path.read_text(encoding="utf-8")).get("faces")
        if not isinstance(faces, list) or len(faces) != extra_count + 1:
            print(f"{path.relative_to(ROOT)}: printings carry {extra_count} extra face(s); printed faces must list {extra_count + 1}")
            errors += 1
    # The rules file's identityFaces declaration (the play facts the engine
    # switches on, CR 3.1.1a) and the printed faces (the display record)
    # describe the same faces and must agree.
    for card_id, rules_path in sorted(card_ids.items()):
        rules = json.loads(rules_path.read_text(encoding="utf-8"))
        declared = None
        for ability in rules.get("abilities") or []:
            declaration = ability.get("declaration") if isinstance(ability, dict) else None
            if isinstance(declaration, dict) and declaration.get("field") == "identityFaces":
                declared = declaration.get("value")
        printed_path = directory / f"{card_id}.json"
        if not printed_path.is_file():
            continue
        printed_faces = json.loads(printed_path.read_text(encoding="utf-8")).get("faces")
        if declared is None and printed_faces is None:
            continue
        if not isinstance(declared, list) or not isinstance(printed_faces, list) or len(declared) != len(printed_faces):
            print(f"{printed_path.relative_to(ROOT)}: printed faces do not match the rules identityFaces")
            errors += 1
            continue
        for index, (face, printed_face) in enumerate(zip(declared, printed_faces)):
            for field in ("title", "subtypes", "link"):
                if face.get(field) != printed_face.get(field):
                    print(
                        f"{printed_path.relative_to(ROOT)}: faces[{index}] {field} "
                        "differs from the rules identityFaces"
                    )
                    errors += 1
    # "Use ... only during your turn" restricts paid abilities to the
    # controller's turn (CR 9.5.2f: restrictions specified in text). Every
    # non-click paid ability on such a card must declare onlyDuringOwnTurn,
    # and the flag must not appear without the printed restriction. A card
    # whose phrase restricts rezzing instead declares rezOnlyDuringCorpTurn
    # (Front Company) and has no paid abilities to flag.
    for card_id, rules_path in sorted(card_ids.items()):
        printed_path = directory / f"{card_id}.json"
        if not printed_path.is_file():
            continue
        printed = json.loads(printed_path.read_text(encoding="utf-8"))
        texts = [printed.get("strippedText") or ""]
        texts += [
            face.get("strippedText") or ""
            for face in printed.get("faces") or []
            if isinstance(face, dict)
        ]
        restricted = any("only during your turn" in text for text in texts)
        rules = json.loads(rules_path.read_text(encoding="utf-8"))
        abilities = [a for a in rules.get("abilities") or [] if isinstance(a, dict)]
        declared_fields = {
            a["declaration"].get("field")
            for a in abilities
            if isinstance(a.get("declaration"), dict)
        }
        if "rezOnlyDuringCorpTurn" in declared_fields:
            restricted = False
        for ability in abilities:
            if ability.get("class") != "paid":
                continue
            cost = ability.get("cost") or {}
            if isinstance(cost, dict) and cost.get("clicks"):
                continue  # a click-first cost is an action (CR 9.5.2a)
            flagged = ability.get("onlyDuringOwnTurn") is True
            if restricted and not flagged:
                print(
                    f"{printed_path.relative_to(ROOT)}: paid ability "
                    f"{ability.get('id')!r} lacks onlyDuringOwnTurn for its "
                    "printed 'only during your turn' restriction"
                )
                errors += 1
            if flagged and not restricted:
                print(
                    f"{printed_path.relative_to(ROOT)}: paid ability "
                    f"{ability.get('id')!r} declares onlyDuringOwnTurn but the "
                    "printed text has no 'only during your turn' restriction"
                )
                errors += 1
    # A paid ability whose cost includes a click is an action (CR 9.5.2a),
    # so it can only be offered in action windows. The one printed
    # exception is bioroid ice, whose click-cost break abilities are used
    # while encountering that ice. Fail closed on any other window shape
    # so a click-cost ability cannot silently become usable mid-run.
    for card_id, rules_path in sorted(card_ids.items()):
        rules = json.loads(rules_path.read_text(encoding="utf-8"))
        is_bioroid_ice = rules.get("type") == "ice" and "bioroid" in (
            rules.get("subtypes") or []
        )
        for ability in rules.get("abilities") or []:
            if not isinstance(ability, dict) or ability.get("class") != "paid":
                continue
            cost = ability.get("cost") or {}
            if not (isinstance(cost, dict) and cost.get("clicks")):
                continue
            windows = ability.get("windows") or []
            if all(
                isinstance(w, str) and w.endswith("_action_paw") for w in windows
            ):
                continue
            if is_bioroid_ice:
                continue
            print(
                f"{rules_path.relative_to(ROOT)}: paid ability "
                f"{ability.get('id')!r} costs a click but declares "
                f"non-action windows {windows!r} (only bioroid ice may)"
            )
            errors += 1
    missing = sorted(set(card_ids) - seen)
    if missing:
        print(f"cards with no printed text: {missing}")
        errors += 1
    return errors


REFERENCE_FILES = (
    "factions.json",
    "subtypes.json",
    "card-types.json",
    "sides.json",
    "card-set-types.json",
    "card-layouts.json",
    "ruling-sources.json",
    "card-sets.json",
    "card-cycles.json",
)


def load_reference() -> tuple[dict[str, set[str]], int]:
    """Vocabulary ids from the v2 reference files under data/."""
    found: dict[str, set[str]] = {}
    errors = 0
    for name in REFERENCE_FILES:
        path = DATA / name
        if not path.is_file():
            print(f"reference file missing: data/{name}")
            errors += 1
            continue
        records = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(records, list) or not records:
            print(f"data/{name}: must be a non-empty list")
            errors += 1
            continue
        ids: set[str] = set()
        for record in records:
            if (
                not isinstance(record, dict)
                or not isinstance(record.get("id"), str)
                or not isinstance(record.get("name"), str)
            ):
                print(f"data/{name}: record {record!r} needs string id and name")
                errors += 1
                continue
            if record["id"] in ids:
                print(f"data/{name}: duplicate id {record['id']!r}")
                errors += 1
            ids.add(record["id"])
        found[name] = ids
    return found, errors


def check_legality(card_ids: dict[str, Path], waves: dict, subtype_ids: set[str] | None = None) -> int:
    errors = 0
    corpus = set(waves)
    pools: dict[str, dict] = {}
    pool_dir = DATA / "card-pools"
    if not pool_dir.is_dir():
        print("card pool directory missing: data/card-pools")
        return 1
    for path in sorted(pool_dir.glob("*.json")):
        raw = json.loads(path.read_text(encoding="utf-8"))
        if raw.get("id") != path.stem:
            print(f"{path.relative_to(ROOT)}: id != filename")
            errors += 1
        for wave in raw.get("waves") or []:
            if wave not in corpus:
                print(f"{path.relative_to(ROOT)}: wave {wave!r} is not in the corpus")
                errors += 1
        pools[path.stem] = raw
    restrictions: set[str] = set()
    restriction_dir = DATA / "restrictions"
    if not restriction_dir.is_dir():
        print("restrictions directory missing: data/restrictions")
        return 1
    for path in sorted(restriction_dir.glob("*.json")):
        raw = json.loads(path.read_text(encoding="utf-8"))
        if raw.get("id") != path.stem:
            print(f"{path.relative_to(ROOT)}: id != filename")
            errors += 1
        restrictions.add(path.stem)
        if subtype_ids is not None:
            grouped_subtypes = raw.get("subtypes") or {}
            if not isinstance(grouped_subtypes, dict):
                print(f"{path.relative_to(ROOT)}: subtypes must be an object of name lists")
                errors += 1
            else:
                for subtype in (name for names in grouped_subtypes.values() for name in names):
                    if subtype not in subtype_ids:
                        print(f"{path.relative_to(ROOT)}: subtype {subtype!r} is not in subtypes.json")
                        errors += 1
        for field in ("banned", "restricted"):
            for card_id in raw.get(field) or []:
                if card_id not in card_ids:
                    print(f"{path.relative_to(ROOT)}: {field} card {card_id!r} has no rules file")
                    errors += 1
        for field in ("points", "globalPenalty", "universalFactionCost"):
            grouped = raw.get(field) or {}
            if not isinstance(grouped, dict):
                print(f"{path.relative_to(ROOT)}: {field} must be an object")
                errors += 1
                continue
            for card_id in (card for ids in grouped.values() for card in ids):
                if card_id not in card_ids:
                    print(f"{path.relative_to(ROOT)}: {field} card {card_id!r} has no rules file")
                    errors += 1
    formats = DATA / "formats"
    if not formats.is_dir():
        print("formats directory missing: data/formats")
        return 1
    for path in sorted(formats.glob("*.json")):
        raw = json.loads(path.read_text(encoding="utf-8"))
        if raw.get("id") != path.stem:
            print(f"{path.relative_to(ROOT)}: id != filename")
            errors += 1
        for snapshot in raw.get("snapshots") or []:
            pool_id = snapshot.get("cardPoolId")
            if pool_id not in pools:
                print(f"{path.relative_to(ROOT)}: card pool {pool_id!r} is missing")
                errors += 1
            restriction_id = snapshot.get("restrictionId")
            if restriction_id is not None and restriction_id not in restrictions:
                print(f"{path.relative_to(ROOT)}: restriction {restriction_id!r} is missing")
                errors += 1
    rotations = DATA / "rotations.json"
    if not rotations.is_file():
        print("rotations file missing: data/rotations.json")
        errors += 1
    else:
        for rotation in json.loads(rotations.read_text(encoding="utf-8")):
            for wave in rotation.get("waves") or []:
                if wave not in corpus:
                    print(f"rotations.json: wave {wave!r} is not in the corpus")
                    errors += 1
    for name, wave in waves.items():
        for field in ("dateRelease", "cycle"):
            if not isinstance(wave.get(field), str) or not wave[field]:
                print(f"pool.json {name}: {field} is missing")
                errors += 1
        if type(wave.get("size")) is not int:
            print(f"pool.json {name}: size must be an integer")
            errors += 1
    return errors


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
    reference, reference_errors = load_reference()
    errors += reference_errors
    faction_ids = reference.get("factions.json", set())
    subtype_ids = reference.get("subtypes.json", set())

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
            limit = raw.get("deckLimit")
            if type(limit) is not int or limit < 1:
                print(f"{path.relative_to(ROOT)}: deckLimit must be an integer >= 1")
                errors += 1
            if raw.get("side") != side or raw.get("type") != type_:
                print(
                    f"{path.relative_to(ROOT)}: side/type "
                    f"{raw.get('side')}/{raw.get('type')} != path {side}/{type_}"
                )
                errors += 1
            faction = raw.get("faction")
            if faction is not None and faction_ids and faction not in faction_ids:
                print(f"{path.relative_to(ROOT)}: faction {faction!r} is not in factions.json")
                errors += 1
            for subtype in raw.get("subtypes") or []:
                if subtype_ids and subtype not in subtype_ids:
                    print(f"{path.relative_to(ROOT)}: subtype {subtype!r} is not in subtypes.json")
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

    errors += check_printings(card_ids, waves)
    errors += check_rulings(card_ids)
    errors += check_printed(card_ids)
    errors += check_legality(card_ids, waves, subtype_ids)

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
