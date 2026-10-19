#!/usr/bin/env python3
"""Offline checks for the catalog diff. No network."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from nsg_catalog import diff_card_facts, diff_pack_facts, pack_blobs, pack_codes_from_pool


def test_pool_pack_codes() -> None:
    codes = pack_codes_from_pool(
        {
            "waves": {
                "system-gateway": {"notes": "Null Signal System Gateway (NRDB pack sg) learner set."},
                "midnight-sun": {"notes": "Midnight Sun Booster Pack (msbp) titles absorbed."},
            }
        }
    )
    assert codes == {"sg", "msbp"}, codes


def test_pack_blobs() -> None:
    blobs = pack_blobs(
        {
            "tree": [
                {"path": "pack/sg.json", "type": "blob", "sha": "aaa"},
                {"path": "README.md", "type": "blob", "sha": "bbb"},
                {"path": "pack", "type": "tree", "sha": "ccc"},
            ]
        }
    )
    assert blobs == {"sg": "aaa"}, blobs


def test_fact_diff() -> None:
    before = {"code": "30072", "title": "Palisade", "faction_code": "neutral-corp", "cost": 3, "strength": 2, "text": "End the run."}
    after = {**before, "text": "End the run. Gain 1 credit."}
    assert diff_card_facts(before, after) == ["text changed"]
    assert diff_card_facts(before, {**before, "cost": 4}) == ["cost: 3 → 4"]
    assert diff_card_facts(None, after) == ["added"]
    assert diff_card_facts(before, before) == []
    rows = diff_pack_facts([before], [after])
    assert rows == [("30072", "Palisade", ["text changed"])], rows


def test_generator_pack_codes() -> None:
    from nsg_catalog import generator_pack_codes

    codes = generator_pack_codes()
    assert {"sg", "su21", "ms", "msbp", "vp", "core"} <= codes, codes


def test_restriction_card_ids() -> None:
    from build_catalog_facts import partition_card_ids, restriction_document

    mapped, missed = partition_card_ids(["sure_gamble", "unknown_card"], {"sure_gamble": "sure-gamble"})
    assert mapped == ["sure-gamble"] and missed == ["unknown_card"]
    document = restriction_document(
        {
            "id": "sample",
            "name": "Sample",
            "format_id": "startup",
            "date_start": "2026-03-02",
            "banned": ["sure_gamble"],
            "points": {"1": ["unknown_card"]},
            "point_limit": 7,
        },
        {"sure_gamble": "sure-gamble"},
    )
    assert document["banned"] == ["sure-gamble"]
    assert document["points"] == {"1": []}
    assert document["unmappedCardIds"] == ["unknown_card"]
    assert document["pointLimit"] == 7


def test_ruling_ids() -> None:
    from build_rulings import ruling_record, text_to_id, verified_rulings

    assert text_to_id("Account Siphon") == "account_siphon"
    assert text_to_id("Aesop's Pawnshop") == "aesops_pawnshop"
    assert text_to_id("The Wizard’s Chest") == "the_wizards_chest"
    text = ruling_record(
        {
            "card_id": "account_siphon",
            "date_update": "2017-04-08",
            "nsg_rules_team_verified": False,
            "text_ruling": "The Runner can choose not to use the ability.",
        }
    )
    assert text["rulesTeamVerified"] is False
    assert text["text"].startswith("The Runner")
    question = ruling_record(
        {
            "date_update": "2024-01-01",
            "nsg_rules_team_verified": True,
            "question": "Can the Runner trash it?",
            "answer": "Yes.",
        }
    )
    assert question["rulesTeamVerified"] is True
    assert "text" not in question
    kept = verified_rulings(
        [
            {
                "date_update": "2017-04-08",
                "nsg_rules_team_verified": False,
                "text_ruling": "Unverified.",
            },
            {
                "date_update": "2022-05-27",
                "nsg_rules_team_verified": True,
                "question": "Does it still trigger?",
                "answer": "Yes.",
            },
        ]
    )
    assert len(kept) == 1 and kept[0]["rulesTeamVerified"] is True


def test_printed_numbers() -> None:
    from printed_numbers import apply_printed_numbers

    runner = {}
    apply_printed_numbers(runner, {
        "type_code": "identity",
        "side_code": "runner",
        "base_link": 0,
        "minimum_deck_size": 40,
        "influence_limit": 15,
        "faction_cost": None,
        "deck_limit": 1,
    })
    assert runner == {
        "deckLimit": 1,
        "link": 0,
        "minimumDeckSize": 40,
        "influenceLimit": 15,
    }, runner

    corp = {}
    apply_printed_numbers(corp, {
        "type_code": "identity",
        "side_code": "corp",
        "base_link": 0,
        "minimum_deck_size": 45,
        "influence_limit": 15,
    })
    assert "link" not in corp, corp
    assert corp["minimumDeckSize"] == 45
    assert corp["influenceLimit"] == 15

    ice = {}
    apply_printed_numbers(ice, {"type_code": "ice", "faction_cost": 2, "deck_limit": 3})
    assert ice == {"deckLimit": 3, "influence": 2}, ice

    neutral = {}
    apply_printed_numbers(neutral, {"type_code": "event", "faction_cost": 0})
    assert neutral == {"influence": 0}, neutral

    no_bar = {}
    apply_printed_numbers(no_bar, {"type_code": "agenda", "faction_cost": None})
    assert no_bar == {}, no_bar


def main() -> int:
    test_pool_pack_codes()
    test_pack_blobs()
    test_fact_diff()
    test_generator_pack_codes()
    test_restriction_card_ids()
    test_ruling_ids()
    test_printed_numbers()
    print("ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
