#!/usr/bin/env python3
"""Generate The Spaces Between (tsb) card JSON from pinned pack `tsb`.

Fetch: python3 scripts/nsg_catalog.py fetch tsb
Lunar cycle after Upstalk (floor v1.102.0 → v1.103.0).
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
    etr,
    gain,
    net,
    seq,
    slugify,
    trace_sub,
    write_manifest,
)

OUT = Path(__file__).resolve().parents[1] / "data" / "the-spaces-between"
WAVE = "the-spaces-between"
PACK = "tsb"
EXPECTED = 20

REPRINTS: set[str] = set()


def current_corp(c: dict, **extra):
    return base(
        c,
        subtypes=["current"],
        lingerAsCurrent=True,
        currentTrashOnAgendaStolen=True,
        **extra,
    )


def current_runner(c: dict, **extra):
    return base(
        c,
        subtypes=["current"],
        lingerAsCurrent=True,
        currentTrashOnAgendaScored=True,
        **extra,
    )


def map_card(c: dict) -> dict | None:
    cid = slugify(c["title"])
    if cid in REPRINTS:
        return None

    if cid == "the-foundry-refining-the-process":
        return base(
            c,
            onFirstIceRezEachTurn=do("foundry_search_copy_to_hq"),
        )

    if cid == "enhanced-login-protocol":
        return current_corp(
            c,
            runnerFirstRunEachTurnAdditionalCost=10,
        )

    if cid == "heinlein-grid":
        return base(
            c,
            subtypes=["region"],
            limitOnePerServer=True,
            runnerLosesAllCreditsOnClickLossDuringRunOnThisServer=True,
        )

    if cid == "encrypted-portals":
        return base(
            c,
            whileScoredIceSubtypeStrengthBonus={"subtype": "code gate", "bonus": 1},
            onScore=do("encrypted_portals_on_score"),
        )

    if cid == "cerebral-static":
        return current_corp(c, blankRunnerIdentityPrintedAbilities=True)

    if cid == "targeted-marketing":
        return current_corp(c, onPlay=do("name_card"))

    if cid == "information-overload":
        return base(
            c,
            onEncounter=do("information_overload_encounter"),
            subroutines=[
                {
                    "id": "information-overload-dynamic",
                    "text": "The Runner trashes 1 installed card for each tag they have.",
                    "effect": do("trash_per_tag"),
                }
            ],
        )

    if cid == "paywall-implementation":
        card = current_corp(c, onSuccessfulRun=gain("corp", 1))
        card["subtypes"] = ["current", "transaction"]
        return card

    if cid == "sealed-vault":
        return base(
            c,
            paidAbilities=[
                {
                    "id": "sealed-vault-store",
                    "label": "1[credit]: Move any number of credits from credit pool to Sealed Vault",
                    "clickCost": 0,
                    "creditCost": 1,
                    "cost": {"credits": 1},
                    "windows": ["corp_action_paw"],
                    "effect": do("sealed_vault_store_from_pool"),
                },
                {
                    "id": "sealed-vault-take-click",
                    "label": "[click]: Take any number of credits from Sealed Vault",
                    "clickCost": 1,
                    "creditCost": 0,
                    "cost": {"clicks": 1},
                    "windows": ["corp_action_paw"],
                    "effect": do("take_to_pool"),
                },
                {
                    "id": "sealed-vault-take-trash",
                    "label": "[trash]: Take any number of credits from Sealed Vault",
                    "clickCost": 0,
                    "creditCost": 0,
                    "cost": {"trashSelf": True},
                    "windows": ["corp_action_paw"],
                    "effect": do("take_to_pool"),
                },
            ],
        )

    if cid == "eden-fragment":
        return base(
            c,
            subtypes=["source"],
            ignoreInstallCostFirstIceEachTurn=True,
            deckLimitOne=True,
        )

    if cid == "lag-time":
        return current_corp(c, allIceStrengthBonus=1)

    if cid == "will-o-the-wisp":
        return base(
            c,
            onSuccessfulRunOnThisServer=do("will_o_wisp_trash_breaker_used"),
        )

    if cid == "d4v1d":
        card = base(c, powerCountersOnInstall=3)
        card["paidAbilities"] = [
            {
                "id": "d4v1d-break",
                "label": "Hosted power counter: Break 1 subroutine on ice strength 5+",
                "clickCost": 0,
                "creditCost": 0,
                "cost": {"powerCounters": 1},
                "windows": ["encounter_paw"],
                "effect": do(
                    "break_encounter_subroutine",
                    requireMinStrength=5,
                ),
            }
        ]
        return card

    if cid == "scrubbed":
        return current_runner(c, firstEncounteredIceStrengthPenaltyThisRun=2)

    if cid == "three-steps-ahead":
        return base(
            c,
            playRequiresFirstClick=True,
            onRunnerTurnEnd=do("three_steps_ahead_payout"),
        )

    if cid == "unscheduled-maintenance":
        return current_corp(c, corpMaxIceInstallsPerTurn=1)

    if cid == "cache":
        return base(
            c,
            subtypes=["virus"],
            onInstall=do("add_virus_counter", amount=3),
            paidAbilities=[
                {
                    "id": "cache-cash",
                    "label": "Hosted virus counter: Gain 1[credit]",
                    "clickCost": 0,
                    "creditCost": 0,
                    "cost": {"virusCounters": 1},
                    "windows": ["runner_action_paw", "encounter_paw"],
                    "effect": gain("runner", 1),
                }
            ],
        )

    if cid == "net-celebrity":
        return current_runner(
            c,
            recurringCreditsMax=1,
            recurringSpendFor=["run"],
        )

    if cid == "llds-energy-regulator":
        return base(
            c,
            paidAbilities=[
                {
                    "id": "llds-prevent",
                    "label": "3[credit] or [trash]: Prevent trashing 1 installed hardware",
                    "clickCost": 0,
                    "creditCost": 0,
                    "cost": {},
                    "windows": ["trash_interrupt_paw"],
                    "effect": do("llds_prevent_trash_hardware"),
                }
            ],
        )

    if cid == "ghost-runner":
        return base(
            c,
            subtypes=["stealth", "virtual"],
            hostedCreditsOnInstall=3,
            spendHostedCreditsDuringRuns=True,
            trashWhenHostedCreditsEmpty=True,
        )

    card = base(c)
    card["unsupported"] = [f"Unmapped tsb card: {cid}"]
    return card


def main():
    pack = sorted(load_pack_cards(PACK), key=lambda c: c.get("position", 0))
    assert len(pack) == EXPECTED, len(pack)
    OUT.mkdir(parents=True, exist_ok=True)
    written: list[str] = []
    skipped: list[str] = []
    for raw in pack:
        c = raw
        cid = slugify(c["title"])
        mapped = map_card(c)
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
