#!/usr/bin/env python3
"""Checks for the printed-text label report (scripts/check_labels.py). No network."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from check_labels import DATA, compare, label_found, missing_words, normalize


def printed(card_id: str) -> dict:
    return json.loads((DATA / "printed" / f"{card_id}.json").read_text(encoding="utf-8"))


def test_normalize_symbols() -> None:
    assert normalize("[click][click]: Gain 3[credit].") == "click click gain 3 credit"
    assert normalize("{click}, [trash]: Gain 1¢") == "click trash gain 1 credit"
    assert normalize("Interrupt → 3 credits:") == "interrupt 3 credit"
    assert normalize("Threat 3 -> Boi-tatá's <strong>+1</strong>") == "threat 3 boi tatas 1"
    assert normalize("[recurring-credit]") == "recurring credit"


def test_label_matches_after_normalization() -> None:
    # Bass (CH1R180G4): label "[click], [trash]: Gain [click][click]", printed "click, trash: Gain click click."
    assert label_found("[click], [trash]: Gain [click][click]", printed("bass-ch1r180g4"))
    # Government Takeover: "3[credit]" against printed "3 credits".
    assert label_found("[click]: Gain 3[credit]", printed("government-takeover"))
    # Caldera: arrow and ¢ against "Interrupt -> 3 credits:".
    assert label_found("[interrupt] → 3¢: Prevent 1 core damage or 1 net damage", printed("caldera"))


def test_label_matches_a_face() -> None:
    # SYNC's second face is only in faces[1]; the top-level strippedText is face 0.
    sync = printed("sync-everything-everywhere")
    assert label_found("You may pay 2[credit] fewer when spending a [click] to trash a resource", sync)
    assert not label_found("You may pay 2[credit] fewer", {"strippedText": sync["strippedText"]})


def test_drift_is_reported() -> None:
    # Chetana's printed psi subroutine spells out the bidding; the label paraphrases it.
    label = "Psi game. If bids differ, do 1 net damage for each card in the Runner's grip."
    assert not label_found(label, printed("chetana"))
    assert missing_words(label, printed("chetana")) == ["psi", "game", "bids", "differ"]
    # Whole words only: "Trash 1 program." is not inside "trash 1 installed program".
    assert not label_found("Trash 1 program.", printed("archer"))


def test_compare_is_shrink_only() -> None:
    baseline = {"unlabelled": {"a": ["0:play"]}, "drift": {"b": ["x"]}, "unsupported": []}
    assert compare(baseline, baseline) == []
    grown = {"unlabelled": {"a": ["0:play", "1:conditional"]}, "drift": {"b": ["x"]}, "unsupported": []}
    assert compare(grown, baseline) == ["new unlabelled entry: a 1:conditional"]
    shrunk = {"unlabelled": {}, "drift": {"b": ["x"]}, "unsupported": []}
    problems = compare(shrunk, baseline)
    assert len(problems) == 1 and "regenerate" in problems[0], problems


def main() -> int:
    tests = [value for name, value in sorted(globals().items()) if name.startswith("test_")]
    for test in tests:
        test()
    print(f"check_labels: {len(tests)} tests passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
