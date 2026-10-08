#!/usr/bin/env python3
"""Generate Up and Over (uao) card JSON from pinned pack `uao`.

Fetch: python3 scripts/nsg_catalog.py fetch uao
Lunar cycle after First Contact (floor v1.104.0 → v1.105.0).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from nsg_catalog import load_pack_cards
from spin_common import (
    base,
    breaker_card,
    do,
    draw,
    etr,
    gain,
    net,
    seq,
    slugify,
    write_manifest,
)

OUT = Path(__file__).resolve().parents[1] / "data" / "up-and-over"
WAVE = "up-and-over"
PACK = "uao"
EXPECTED = 20

REPRINTS = {
    "reversed-accounts",
    "blue-sun-powering-the-future",
}


def map_card(c: dict) -> dict | None:
    cid = slugify(c["title"])
    if cid in REPRINTS:
        return None

    if cid == "architect":
        return base(
            c,
            subtypes=["sentry"],
            playersCannotTrashThisIce=True,
            subroutines=[
                {
                    "id": "architect-rd",
                    "text": "Look at top 5 of R&D; may install 1 ignoring cost",
                    "effect": do("look_top_n_rd_may_install_and_rez_ignore_costs", n=5),
                },
                {
                    "id": "architect-hq-arch",
                    "text": "May install 1 card from Archives or HQ",
                    "effect": do("install_from_hq_or_archives"),
                },
            ],
        )

    if cid == "peak-efficiency":
        return base(c, onPlay=do(
            "gain_credits",
            side="corp",
            amount=0,
            tally={"count": "rezzed_ice", "per": 1, "side": "corp"},
        ))

    if cid == "labyrinthine-servers":
        return base(
            c,
            subtypes=["security"],
            onScore=do("add_power_counter", amount=2),
            paidAbilities=[
                {
                    "id": "labyrinthine-jack",
                    "label": "Hosted power counter: prevent jack-out for run",
                    "clickCost": 0,
                    "creditCost": 0,
                    "cost": {"powerCounters": 1},
                    "windows": ["end_the_run_interrupt_paw"],
                    "effect": do("labyrinthine_prevent_jack_out"),
                }
            ],
        )

    if cid == "ashigaru":
        return base(
            c,
            subtypes=["barrier"],
            dynamicEtrSubroutineCountFromCorpHandSize=True,
        )

    if cid == "mamba":
        return base(
            c,
            subtypes=["sentry", "psi", "ap"],
            paidAbilities=[
                {
                    "id": "mamba-counter",
                    "label": "Hosted power counter: 1 net damage (during run)",
                    "clickCost": 0,
                    "creditCost": 0,
                    "cost": {"powerCounters": 1},
                    "windows": ["encounter_paw"],
                    "effect": net(1),
                }
            ],
            subroutines=[
                {"id": "mamba-net", "text": "Do 1 net damage", "effect": net(1)},
                {
                    "id": "mamba-psi",
                    "text": "Psi; if bids differ place 1 power counter on Mamba",
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "play_psi_game",
                            "maxBid": 2,
                            "ifBidsDiffer": do("add_power_counter", amount=1),
                            "ifBidsMatch": gain("corp", 0),
                        },
                    },
                },
            ],
        )

    if cid == "universal-connectivity-fee":
        return base(
            c,
            subtypes=["trap"],
            subroutines=[
                {
                    "id": "ucf",
                    "text": "Untagged lose 1¢; tagged lose all ¢ and trash this ice",
                    "effect": do("universal_connectivity_fee_sub"),
                }
            ],
        )

    if cid == "changeling":
        return base(
            c,
            subtypes=["barrier", "morph"],
            canAdvance=True,
            morphOddAdvancementSubtypeSwap={"gain": "sentry", "lose": "barrier"},
            subroutines=[{"id": "changeling-etr", "text": "End the run", "effect": etr()}],
        )

    if cid == "reuse":
        return base(
            c,
            subtypes=["double"],
            playAdditionalCost=do("spend_click_additional_cost"),
            onPlay=do("trash_hq_gain_credits"),
        )

    if cid == "hades-fragment":
        return base(
            c,
            subtypes=["source"],
            unique=True,
            deckLimitOne=True,
            onTurnBegin=do("may_add_archives_card_to_rd_bottom_only"),
        )

    if cid == "docklands-crackdown":
        return base(
            c,
            paidAbilities=[
                {
                    "id": "docklands-place",
                    "label": "[click][click]: Place 1 power counter",
                    "clickCost": 2,
                    "creditCost": 0,
                    "cost": {"clicks": 2},
                    "windows": ["corp_action_paw"],
                    "effect": do("add_power_counter", amount=1),
                }
            ],
            runnerFirstInstallCostIncreasePerPowerCounterOnThis=1,
        )

    if cid == "inject":
        return base(c, onPlay=do("reveal_top_four"))

    if cid == "origami":
        return base(c, handSizeBonusPerInstalledCopyWithSameDefId=1)

    if cid == "fester":
        return base(
            c,
            subtypes=["virtual"],
            onVirusPurge=do("corp_lose_two_if_can"),
        )

    if cid == "autoscripter":
        return base(
            c,
            unique=True,
            onFirstProgramInstallEachTurn=do("gain_clicks", side="runner", amount=1),
            trashSelfOnUnsuccessfulRunThisTurn=True,
        )

    if cid == "switchblade":
        card = breaker_card(c, "sentry", 0, 1, 1, 7)
        card["paidAbilitiesUseStealthCreditsOnly"] = True
        card["paidAbilities"] = [
            {
                "id": "switchblade-break",
                "label": "1¢ (stealth): Break any number of sentry subroutines",
                "clickCost": 0,
                "creditCost": 1,
                "cost": {"credits": 1, "creditsFromStealthOnly": True},
                "windows": ["encounter_paw"],
                "requireEncounterSubtype": "sentry",
                "effect": do(
                    "break_encounter_subroutine",
                    maxSubs=99,
                    requireSubtype="sentry",
                ),
            },
            {
                "id": "switchblade-pump",
                "label": "1¢ (stealth): +7 strength",
                "clickCost": 0,
                "creditCost": 1,
                "cost": {"credits": 1, "creditsFromStealthOnly": True},
                "windows": ["encounter_paw"],
                "effect": do("pump_strength", amount=7),
            },
        ]
        card["breaker"]["breakViaPaidAbilityOnly"] = True
        return card

    if cid == "trade-in":
        return base(
            c,
            playAdditionalCost=do("trash_hardware_additional_cost"),
            onPlay=do("trade_in_resolve"),
        )

    if cid == "astrolabe":
        return base(
            c,
            subtypes=["console"],
            unique=True,
            maxConsole=1,
            muBonus=1,
            onCorpRemoteServerCreated=draw("runner", 1),
        )

    if cid == "angel-arena":
        return base(
            c,
            subtypes=["location"],
            unique=True,
            onInstall=do("place_x_counters"),
            trashWhenPowerEmpty=True,
            paidAbilities=[
                {
                    "id": "angel-reveal",
                    "label": "Hosted power counter: reveal top of stack; may bottom",
                    "clickCost": 0,
                    "creditCost": 0,
                    "cost": {"powerCounters": 1},
                    "windows": ["runner_action_paw"],
                    "effect": do("reveal_top_may_bottom"),
                }
            ],
        )

    card = base(c)
    card["unsupported"] = [f"Unmapped uao card: {cid}"]
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
