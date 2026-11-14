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


def main() -> int:
    tests = [value for name, value in sorted(globals().items()) if name.startswith("test_")]
    for test in tests:
        test()
    print(f"validate-cards: {len(tests)} tests passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
