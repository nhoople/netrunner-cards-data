#!/usr/bin/env python3
"""Offline checks for the catalog diff. No network."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from nsg_catalog import (
    card_blobs,
    card_type,
    diff_card_facts,
    diff_card_sets,
    faction_slug,
    nsg_id,
    our_id,
    pack_codes_from_pool,
)


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


def test_card_blobs() -> None:
    blobs = card_blobs(
        {
            "tree": [
                {"path": "v2/cards/hedge_fund.json", "type": "blob", "sha": "aaa"},
                {"path": "README.md", "type": "blob", "sha": "bbb"},
                {"path": "v2/cards", "type": "tree", "sha": "ccc"},
            ]
        }
    )
    assert blobs == {"hedge_fund": "aaa"}, blobs


def test_id_transforms() -> None:
    assert our_id("hedge_fund") == "hedge-fund"
    assert nsg_id("hedge-fund") == "hedge_fund"
    assert our_id("the_wizards_chest") == "the-wizard-s-chest"
    assert our_id("o_shortage") == "o2-shortage"
    assert nsg_id("the-wizard-s-chest") == "the_wizards_chest"
    assert nsg_id("o2-shortage") == "o_shortage"
    assert card_type({"card_type_id": "runner_identity"}) == "identity"
    assert card_type({"card_type_id": "corp_identity"}) == "identity"
    assert card_type({"card_type_id": "ice"}) == "ice"
    assert card_type({}) is None
    assert faction_slug({"faction_id": "haas_bioroid"}) == "haas-bioroid"
    assert faction_slug({}) is None


def test_fact_diff() -> None:
    before = {"id": "palisade", "title": "Palisade", "faction_id": "neutral_corp", "cost": 3, "strength": 2, "text": "End the run."}
    after = {**before, "text": "End the run. Gain 1 credit."}
    assert diff_card_facts(before, after) == ["text changed"]
    assert diff_card_facts(before, {**before, "cost": 4}) == ["cost: 3 → 4"]
    assert diff_card_facts(None, after) == ["added"]
    assert diff_card_facts(before, before) == []
    rows = diff_card_sets([before], [after])
    assert rows == [("palisade", "Palisade", ["text changed"])], rows


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
        "card_type_id": "runner_identity",
        "side_id": "runner",
        "base_link": 0,
        "minimum_deck_size": 40,
        "influence_limit": 15,
        "influence_cost": None,
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
        "card_type_id": "corp_identity",
        "side_id": "corp",
        "base_link": 0,
        "minimum_deck_size": 45,
        "influence_limit": 15,
    })
    assert "link" not in corp, corp
    assert corp["minimumDeckSize"] == 45
    assert corp["influenceLimit"] == 15

    ice = {}
    apply_printed_numbers(ice, {"card_type_id": "ice", "influence_cost": 2, "deck_limit": 3})
    assert ice == {"deckLimit": 3, "influence": 2}, ice

    neutral = {}
    apply_printed_numbers(neutral, {"card_type_id": "event", "influence_cost": 0})
    assert neutral == {"influence": 0}, neutral

    no_bar = {}
    apply_printed_numbers(no_bar, {"card_type_id": "agenda", "influence_cost": None})
    assert no_bar == {}, no_bar


def test_printed_face_and_unique() -> None:
    from build_catalog_facts import printed_face, rules_unique

    back = printed_face(
        {
            "stripped_title": "Hoshiko Shiro: Mahou Shoujo",
            "text": "When your turn begins, draw 1 card.",
            "stripped_text": "When your turn begins, draw 1 card.",
            "base_link": 1,
        },
        "Hoshiko Shiro: Untold Protagonist",
    )
    assert back["title"] == "Hoshiko Shiro: Mahou Shoujo"
    assert back["link"] == 1 and "subtypes" not in back
    untitled = printed_face({"text": "x", "stripped_text": "x"}, "SYNC: Everything, Everywhere")
    assert untitled["title"] == "SYNC: Everything, Everywhere"

    assert rules_unique({"abilities": [{"declaration": {"field": "unique", "value": True}}]})
    assert rules_unique({"unique": True})
    assert not rules_unique({"abilities": [{"declaration": {"field": "unique", "value": False}}]})
    assert not rules_unique({})


def main() -> int:
    test_pool_pack_codes()
    test_card_blobs()
    test_id_transforms()
    test_fact_diff()
    test_generator_pack_codes()
    test_restriction_card_ids()
    test_ruling_ids()
    test_printed_numbers()
    test_printed_face_and_unique()
    print("ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
