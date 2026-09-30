#!/usr/bin/env python3
"""Generate All That Remains (atr) card JSON from pinned pack `atr`.

Fetch: python3 scripts/nrdb_catalog.py fetch atr
Lunar cycle after Up and Over (floor v1.105.0 → v1.106.0).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from nrdb_catalog import load_pack_cards
from spin_common import (
    base,
    breaker_card,
    do,
    net,
    slugify,
    write_manifest,
)

OUT = Path(__file__).resolve().parents[1] / "data" / "all-that-remains"
WAVE = "all-that-remains"
PACK = "atr"
EXPECTED = 20

REPRINTS = {
    "daily-business-show",  # system-update-2021
    "leela-patel-trained-pragmatist",  # system-core-2019
    "license-acquisition",  # system-update-2021
}


def cerberus(c, subtype: str, strength: int, break_label: str):
    """Power-counter icebreaker: install 4 counters; spend 1 to break up to 2; 1¢ +1 str."""
    card = breaker_card(c, subtype, strength, 0, 1, 1)
    card["powerCountersOnInstall"] = 4
    card["breaker"]["breakViaPaidAbilityOnly"] = True
    card["paidAbilities"] = [
        {
            "id": f"{card['id']}-break",
            "label": f"Hosted power counter: Break up to 2 {subtype} subroutines",
            "clickCost": 0,
            "creditCost": 0,
            "cost": {"powerCounters": 1},
            "windows": ["encounter_paw"],
            "requireEncounterSubtype": subtype,
            "effect": do(
                "break_encounter_subroutine",
                maxSubs=2,
                requireSubtype=subtype,
            ),
        },
        {
            "id": f"{card['id']}-pump",
            "label": "1¢: +1 strength",
            "clickCost": 0,
            "creditCost": 1,
            "cost": {"credits": 1},
            "windows": ["encounter_paw"],
            "effect": do("pump_strength", amount=1),
        },
    ]
    return card


def map_card(c: dict) -> dict | None:
    cid = slugify(c["title"])
    if cid in REPRINTS:
        return None

    if cid == "bifrost-array":
        return base(
            c,
            subtypes=["initiative"],
            onScore=do("bifrost_may_trigger_scored_agenda_on_score"),
        )

    if cid == "sagittarius":
        return base(
            c,
            subtypes=["sentry", "tracer", "destroyer"],
            subroutines=[
                {
                    "id": "sagittarius-trace",
                    "text": "Trace[2]. If successful, trash 1 program. If strength ≥5, trash 1 program.",
                    "effect": do("sagittarius_trace_subroutine"),
                }
            ],
        )

    if cid == "hostile-infrastructure":
        return base(
            c,
            netDamageWheneverRunnerTrashesCorpCard=1,
            onTrash=net(1),
        )

    if cid == "gemini":
        return base(
            c,
            subtypes=["sentry", "tracer", "ap"],
            subroutines=[
                {
                    "id": "gemini-trace",
                    "text": "Trace[2]. If successful, do 1 net damage. If strength ≥5, do 1 net damage.",
                    "effect": do("gemini_trace_subroutine"),
                }
            ],
        )

    if cid == "superior-cyberwalls":
        return base(
            c,
            subtypes=["security"],
            whileScoredIceSubtypeStrengthBonus={"subtype": "barrier", "bonus": 1},
            onScore=do("gain_credits_per_rezzed_subtype", subtype="barrier", per=1),
        )

    if cid == "executive-boot-camp":
        return base(
            c,
            onTurnBegin=do("may_rez_card_with_discount", discount=1),
            paidAbilities=[
                {
                    "id": "ebc-search",
                    "label": "1¢,[trash]: Search R&D for an asset, reveal it, add to HQ",
                    "clickCost": 0,
                    "creditCost": 1,
                    "cost": {"credits": 1, "trashSelf": True},
                    "windows": ["corp_action_paw"],
                    "effect": do("search_rd_asset_to_hq"),
                }
            ],
        )

    if cid == "lycan":
        return base(
            c,
            subtypes=["sentry", "destroyer", "morph"],
            canAdvance=True,
            morphOddAdvancementSubtypeSwap={"gain": "code gate", "lose": "sentry"},
            subroutines=[
                {
                    "id": "lycan-trash",
                    "text": "Trash 1 program.",
                    "effect": do("trash_one_installed_runner_program"),
                }
            ],
        )

    if cid == "snatch-and-grab":
        return base(
            c,
            subtypes=["gray ops"],
            onPlay=do("snatch_and_grab_on_play"),
        )

    if cid == "merlin":
        return base(
            c,
            subtypes=["code gate", "grail", "ap"],
            onEncounter=do("grail_reveal_gain_subroutines", maxReveal=2),
            subroutines=[
                {
                    "id": "merlin-net",
                    "text": "Do 2 net damage.",
                    "effect": net(2),
                }
            ],
        )

    if cid == "shell-corporation":
        return base(
            c,
            paidAbilitiesOncePerTurn=True,
            paidAbilities=[
                {
                    "id": "shell-place",
                    "label": "[click]: Place 3¢ on Shell Corporation",
                    "clickCost": 1,
                    "creditCost": 0,
                    "cost": {"clicks": 1},
                    "windows": ["corp_action_paw"],
                    "effect": do("place_hosted_credits", amount=3),
                },
                {
                    "id": "shell-take",
                    "label": "[click]: Take all credits from Shell Corporation",
                    "clickCost": 1,
                    "creditCost": 0,
                    "cost": {"clicks": 1},
                    "windows": ["corp_action_paw"],
                    "effect": do("take_hosted_credits", amount=999),
                },
            ],
        )

    if cid == "ekomind":
        return base(
            c,
            subtypes=["console"],
            unique=True,
            maxConsole=1,
            memoryLimitEqualsGripSize=True,
        )

    if cid == "cerberus-cuj-0-h3":
        return cerberus(c, "sentry", 0, "sentry")

    if cid == "cerberus-rex-h2":
        return cerberus(c, "code gate", 1, "code gate")

    if cid == "zona-sul-shipping":
        return base(
            c,
            onTurnBegin=do("place_hosted_credits", amount=1),
            trashSelfWhenRunnerTagged=True,
            paidAbilities=[
                {
                    "id": "zona-take",
                    "label": "[click]: Take all credits from Zona Sul Shipping",
                    "clickCost": 1,
                    "creditCost": 0,
                    "cost": {"clicks": 1},
                    "windows": ["runner_action_paw"],
                    "effect": do("take_hosted_credits", amount=999),
                }
            ],
        )

    if cid == "cybsoft-macrodrive":
        return base(
            c,
            recurringCreditsMax=1,
            recurringSpendFor=["install_program"],
        )

    if cid == "cerberus-lady-h1":
        return cerberus(c, "barrier", 3, "barrier")

    if cid == "utopia-shard":
        return base(
            c,
            subtypes=["virtual", "source"],
            unique=True,
            deckLimitOne=True,
            onGripHqSuccessInstallSelfIgnoringCosts=True,
            paidAbilities=[
                {
                    "id": "utopia-discard",
                    "label": "[trash]: Corp discards 2 cards from HQ at random",
                    "clickCost": 0,
                    "creditCost": 0,
                    "cost": {"trashSelf": True},
                    "windows": ["runner_action_paw", "encounter_paw"],
                    "effect": do("corp_discard_random_from_hq", amount=2),
                }
            ],
        )

    card = base(c)
    card["unsupported"] = [f"Unmapped atr card: {cid}"]
    return card


def main():
    pack = sorted(load_pack_cards(PACK), key=lambda c: c.get("position", 0))
    assert len(pack) == EXPECTED, len(pack)
    OUT.mkdir(parents=True, exist_ok=True)
    written: list[str] = []
    skipped: list[str] = []
    for raw in pack:
        cid = slugify(raw["title"])
        mapped = map_card(raw)
        if mapped is None:
            skipped.append(cid)
            continue
        mapped["wave"] = WAVE
        path = OUT / f"{cid}.json"
        path.write_text(json.dumps(mapped, indent=2, ensure_ascii=False) + "\n")
        written.append(cid)

    pool_ids = [slugify(c["title"]) for c in pack]
    clear_written = [
        cid
        for cid in written
        if not json.loads((OUT / f"{cid}.json").read_text()).get("unsupported")
    ]
    write_manifest(OUT, WAVE, PACK, EXPECTED, pool_ids, written, skipped, clear_written)
    print(f"Wrote {len(written)}; skipped {len(skipped)}; clears {len(clear_written)}")
    print("CLEARS=" + json.dumps(clear_written))


if __name__ == "__main__":
    main()
