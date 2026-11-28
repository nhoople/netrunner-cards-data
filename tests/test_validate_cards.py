#!/usr/bin/env python3
"""Unit checks for validate_cards.py rules. No network."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
spec = importlib.util.spec_from_file_location(
    "validate_cards", SCRIPTS / "validate_cards.py"
)
assert spec and spec.loader
validate_cards = importlib.util.module_from_spec(spec)
sys.path.insert(0, str(SCRIPTS))
spec.loader.exec_module(validate_cards)


def paid(label: str, cost: dict) -> dict:
    return {"class": "paid", "rule": "9.3.7b", "label": label, "cost": cost}


def test_lose_click_cost_is_lose_clicks() -> None:
    check = validate_cards._lose_click_cost_error
    assert (
        check(paid("Lose [click]: Break 1 subroutine on Markus 1.0", {"loseClicks": 1}))
        is None
    )
    assert (
        check(
            paid(
                "Once per turn → Lose [click][click]: Break 1 subroutine",
                {"loseClicks": 2},
            )
        )
        is None
    )


def test_lose_click_cost_written_as_clicks_fails() -> None:
    check = validate_cards._lose_click_cost_error
    err = check(paid("Lose [click]: Break 1 subroutine on Markus 1.0", {"clicks": 1}))
    assert err and "loseClicks" in err, err
    err = check(
        paid(
            "Once per turn → Lose [click][click]: Break 1 subroutine", {"loseClicks": 1}
        )
    )
    assert err and "loses 2" in err, err


def test_click_cost_is_not_a_lose_click_cost() -> None:
    check = validate_cards._lose_click_cost_error
    assert check(paid("[click]: Gain 3[credit].", {"clicks": 1})) is None
    # "lose" inside the effect text is not the cost.
    assert check(paid("[click]: The Runner loses [click].", {"clicks": 1})) is None


def static(field: str) -> dict:
    return {
        "class": "static",
        "rule": "9.3.7a",
        "declaration": {"field": field, "value": True},
    }


def test_play_gate_on_hardware_with_paid_ability_fails() -> None:
    # Unregistered S&W '35 as cards v1.147.22 wrote it: the static play gate
    # never stopped its paid ability.
    check = validate_cards._play_gate_on_used_card_error
    card = {
        "type": "hardware",
        "abilities": [
            static("playRequiresSuccessfulHqRunThisTurn"),
            paid("[click][click]: Trash 1 rezzed bioroid", {"clicks": 2}),
        ],
    }
    err = check(card)
    assert err and "paid abilities" in err, err


def test_use_restriction_on_paid_ability_passes() -> None:
    check = validate_cards._play_gate_on_used_card_error
    ability = paid("[click][click]: Trash 1 rezzed bioroid", {"clicks": 2})
    ability["requiresSuccessfulHqRunThisTurn"] = True
    assert check({"type": "hardware", "abilities": [ability]}) is None


def test_play_gate_on_event_passes() -> None:
    check = validate_cards._play_gate_on_used_card_error
    card = {
        "type": "event",
        "abilities": [static("playRequiresSuccessfulHqRunThisTurn")],
    }
    assert check(card) is None


def ice_break(action: dict, **extra: object) -> dict:
    return {
        "class": "paid",
        "rule": "9.3.7b",
        "label": "3¢: Break 1 subroutine on N-Pot",
        "cost": {"credits": 3},
        "windows": ["encounter_paw"],
        "instructions": {"op": "do", "action": action},
        **extra,
    }


def test_ice_break_is_runner_self_break() -> None:
    check = validate_cards._ice_self_break_error
    ice = {"type": "ice"}
    good = ice_break(
        {"kind": "break_subroutine_on_self", "amount": 1}, usableByRunnerOnSelfIce=True
    )
    assert check(ice, good) is None


def test_ice_break_written_as_host_break_fails() -> None:
    check = validate_cards._ice_self_break_error
    err = check({"type": "ice"}, ice_break({"kind": "break_host_subroutine"}))
    assert err and "break_subroutine_on_self" in err, err


def test_ice_self_break_needs_runner_flag() -> None:
    check = validate_cards._ice_self_break_error
    err = check(
        {"type": "ice"}, ice_break({"kind": "break_subroutine_on_self", "amount": 1})
    )
    assert err and "usableByRunnerOnSelfIce" in err, err


def test_program_host_break_is_not_ice() -> None:
    check = validate_cards._ice_self_break_error
    assert (
        check({"type": "program"}, ice_break({"kind": "break_host_subroutine"})) is None
    )


FALSE_LEAD_TEXT = {
    "strippedTitle": "False Lead",
    "strippedText": "Forfeit this agenda: If the Runner has 2 or more click remaining, they lose click click.",
}


def test_forfeit_this_agenda_pays_forfeit_self() -> None:
    check = validate_cards._forfeit_self_cost_error
    rules = {"abilities": [paid("Forfeit", {"forfeitSelf": True})]}
    assert check(FALSE_LEAD_TEXT, rules) is None


def test_forfeit_this_agenda_written_as_trash_self_fails() -> None:
    check = validate_cards._forfeit_self_cost_error
    rules = {"abilities": [paid("Forfeit", {"trashSelf": True})]}
    err = check(FALSE_LEAD_TEXT, rules)
    assert err and "forfeitSelf" in err, err


def test_forfeit_self_without_printed_cost_fails() -> None:
    check = validate_cards._forfeit_self_cost_error
    printed = {
        "strippedTitle": "Data Dealer",
        "strippedText": "click, forfeit 1 agenda: Gain 9 credit.",
    }
    rules = {"abilities": [paid("Forfeit", {"forfeitSelf": True})]}
    assert check(printed, rules)
    assert (
        check(printed, {"abilities": [paid("Forfeit", {"forfeitAgenda": True})]})
        is None
    )


def test_rules_files_and_word_lists_are_read_from_data_rules() -> None:
    import data_paths

    rules = data_paths.RULES
    dirs = validate_cards.storage_dirs()
    assert len(dirs) == 11, dirs
    for directory in dirs:
        assert directory.parent.parent == rules, directory
        assert directory.is_dir() and any(directory.glob("*.json")), directory
    assert data_paths.SCHEMA_PATH.parent == rules
    assert data_paths.POOL_PATH.parent == rules
    for name in ("card-types.json", "factions.json", "sides.json", "subtypes.json"):
        assert data_paths.REFERENCE_FILES[name] == rules / name
    for path in data_paths.REFERENCE_FILES.values():
        assert path.is_file(), path


def test_print_files_are_read_from_data_print() -> None:
    import data_paths

    print_dir = data_paths.PRINT
    assert data_paths.PRINTED_DIR == print_dir / "printed"
    assert data_paths.PRINTINGS_DIR == print_dir / "printings"
    for directory in (data_paths.PRINTED_DIR, data_paths.PRINTINGS_DIR):
        assert directory.is_dir() and any(directory.glob("*.json")), directory
    for name in (
        "card-cycles.json",
        "card-layouts.json",
        "card-set-types.json",
        "card-sets.json",
    ):
        assert data_paths.REFERENCE_FILES[name] == print_dir / name


def test_format_files_are_read_from_data_formats() -> None:
    import data_paths

    formats = data_paths.FORMATS
    assert data_paths.FORMATS_DIR == formats / "formats"
    assert data_paths.CARD_POOLS_DIR == formats / "card-pools"
    assert data_paths.RESTRICTIONS_DIR == formats / "restrictions"
    assert data_paths.ROTATIONS_PATH == formats / "rotations.json"
    for directory in (
        data_paths.FORMATS_DIR,
        data_paths.CARD_POOLS_DIR,
        data_paths.RESTRICTIONS_DIR,
    ):
        assert directory.is_dir() and any(directory.glob("*.json")), directory
    assert data_paths.ROTATIONS_PATH.is_file()
    # Only folders and the rotations file sit at the top of data/formats/, so no
    # format glob can read rotations.json as a format.
    assert [p.name for p in formats.glob("*.json")] == ["rotations.json"]


def test_rulings_are_read_from_data_rulings() -> None:
    import data_paths

    rulings = data_paths.RULINGS
    assert data_paths.RULINGS_DIR == rulings / "rulings"
    assert data_paths.RULINGS_DIR.is_dir()
    assert any(data_paths.RULINGS_DIR.glob("*.json"))
    assert data_paths.REFERENCE_FILES["ruling-sources.json"] == (
        rulings / "ruling-sources.json"
    )
    # build_rulings.py deletes every *.json in RULINGS_DIR before it writes, so
    # ruling-sources.json must sit outside that folder.
    assert [p.name for p in rulings.glob("*.json")] == ["ruling-sources.json"]


def test_bookkeeping_is_outside_data() -> None:
    import data_paths

    bookkeeping = data_paths.BOOKKEEPING
    assert bookkeeping == data_paths.ROOT / "bookkeeping"
    assert data_paths.MANIFESTS_DIR == bookkeeping / "manifests"
    assert any(data_paths.MANIFESTS_DIR.glob("*.json"))
    assert data_paths.ALLOWLIST_PATH.parent == bookkeeping
    assert data_paths.CATALOG_PIN_PATH.parent == bookkeeping
    assert validate_cards.ALLOWLIST_PATH == data_paths.ALLOWLIST_PATH
    for path in (data_paths.ALLOWLIST_PATH, data_paths.CATALOG_PIN_PATH):
        assert path.is_file(), path


def data_files() -> set[Path]:
    """Files under data/ that git tracks or would add (ignored files left out)."""
    import subprocess

    import data_paths

    listed = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=data_paths.DATA,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    return {(data_paths.DATA / p).resolve() for p in filter(None, listed.split("\0"))}


def test_data_holds_only_the_four_card_data_groups() -> None:
    import data_paths

    groups = sorted(
        {p.relative_to(data_paths.DATA.resolve()).parts[0] for p in data_files()}
    )
    assert groups == ["formats", "print", "rules", "rulings"], groups


_OPENED: set[Path] | None = None


def _record_open(event: str, args: tuple) -> None:
    if _OPENED is not None and event == "open" and isinstance(args[0], str):
        _OPENED.add(Path(args[0]).resolve())


def test_validator_reads_every_file_under_data() -> None:
    """A path the validator stops reading after a move would pass silently."""
    import contextlib
    import io

    import data_paths

    global _OPENED
    _OPENED = set()
    sys.addaudithook(_record_open)
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            assert validate_cards.main() == 0
        opened = set(_OPENED)
    finally:
        _OPENED = None
    # The schema and the pool are read once, when validate_cards is imported.
    opened |= {data_paths.SCHEMA_PATH.resolve(), data_paths.POOL_PATH.resolve()}
    root = data_paths.ROOT.resolve()
    unread = sorted(str(p.relative_to(root)) for p in data_files() - opened)
    assert not unread, f"{len(unread)} files under data/ not read: {unread[:10]}"
    assert data_paths.ALLOWLIST_PATH.resolve() in opened


def main() -> int:
    tests = [
        value for name, value in sorted(globals().items()) if name.startswith("test_")
    ]
    for test in tests:
        test()
    print(f"validate-cards: {len(tests)} tests passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
