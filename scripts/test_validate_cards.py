#!/usr/bin/env python3
"""Unit checks for validate-cards.py rules. No network."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("validate_cards", HERE / "validate-cards.py")
assert spec and spec.loader
validate_cards = importlib.util.module_from_spec(spec)
sys.path.insert(0, str(HERE))
spec.loader.exec_module(validate_cards)


def paid(label: str, cost: dict) -> dict:
    return {"class": "paid", "rule": "9.3.7b", "label": label, "cost": cost}


def test_lose_click_cost_is_lose_clicks() -> None:
    check = validate_cards._lose_click_cost_error
    assert check(paid("Lose [click]: Break 1 subroutine on Markus 1.0", {"loseClicks": 1})) is None
    assert check(
        paid("Once per turn → Lose [click][click]: Break 1 subroutine", {"loseClicks": 2})
    ) is None


def test_lose_click_cost_written_as_clicks_fails() -> None:
    check = validate_cards._lose_click_cost_error
    err = check(paid("Lose [click]: Break 1 subroutine on Markus 1.0", {"clicks": 1}))
    assert err and "loseClicks" in err, err
    err = check(paid("Once per turn → Lose [click][click]: Break 1 subroutine", {"loseClicks": 1}))
    assert err and "loses 2" in err, err


def test_click_cost_is_not_a_lose_click_cost() -> None:
    check = validate_cards._lose_click_cost_error
    assert check(paid("[click]: Gain 3[credit].", {"clicks": 1})) is None
    # "lose" inside the effect text is not the cost.
    assert check(paid("[click]: The Runner loses [click].", {"clicks": 1})) is None


def static(field: str) -> dict:
    return {"class": "static", "rule": "9.3.7a", "declaration": {"field": field, "value": True}}


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
    card = {"type": "event", "abilities": [static("playRequiresSuccessfulHqRunThisTurn")]}
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
    err = check({"type": "ice"}, ice_break({"kind": "break_subroutine_on_self", "amount": 1}))
    assert err and "usableByRunnerOnSelfIce" in err, err


def test_program_host_break_is_not_ice() -> None:
    check = validate_cards._ice_self_break_error
    assert check({"type": "program"}, ice_break({"kind": "break_host_subroutine"})) is None


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
    printed = {"strippedTitle": "Data Dealer", "strippedText": "click, forfeit 1 agenda: Gain 9 credit."}
    rules = {"abilities": [paid("Forfeit", {"forfeitSelf": True})]}
    assert check(printed, rules)
    assert check(printed, {"abilities": [paid("Forfeit", {"forfeitAgenda": True})]}) is None


def main() -> int:
    tests = [value for name, value in sorted(globals().items()) if name.startswith("test_")]
    for test in tests:
        test()
    print(f"validate-cards: {len(tests)} tests passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
