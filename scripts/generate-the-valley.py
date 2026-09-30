#!/usr/bin/env python3
"""Generate The Valley (val) card JSON from pinned pack `val`.

Fetch: python3 scripts/nrdb_catalog.py fetch val
SanSan cycle after Order and Chaos (floor v1.108.0 → v1.109.0).
Reprint skip: clot (already in system-update-2021).
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
    draw,
    etr,
    gain,
    net,
    seq,
    slugify,
    write_manifest,
)

OUT = Path(__file__).resolve().parents[1] / "data" / "the-valley"
WAVE = "the-valley"
PACK = "val"
EXPECTED = 20

REPRINTS = {
    "clot",  # system-update-2021
}


def choose(chooser: str, options: list[dict]) -> dict:
    return {"op": "choose", "chooser": chooser, "options": options}


def may(effect: dict, label: str = "Accept", decline_side: str = "runner") -> dict:
    return choose(
        decline_side if decline_side in ("corp", "runner") else "runner",
        [
            {"id": "accept", "label": label, "effect": effect},
            {
                "id": "decline",
                "label": "Decline",
                "effect": gain(
                    decline_side if decline_side in ("corp", "runner") else "runner",
                    0,
                ),
            },
        ],
    )


def paid(
    id_: str,
    label: str,
    effect: dict,
    *,
    clicks: int = 0,
    credits: int = 0,
    windows: list[str] | None = None,
    cost: dict | None = None,
    once_per_turn: bool = False,
    trash_self: bool = False,
    usable_by_runner: bool = False,
    require_encounter_subtype: str | None = None,
) -> dict:
    c = dict(cost or {})
    if clicks:
        c["clicks"] = clicks
    if credits:
        c["credits"] = credits
    if trash_self:
        c["trashSelf"] = True
    ab: dict = {
        "id": id_,
        "label": label,
        "clickCost": clicks,
        "creditCost": credits,
        "cost": c,
        "windows": windows
        or (
            ["corp_action_paw"]
            if not usable_by_runner
            else ["runner_action_paw"]
        ),
        "effect": effect,
    }
    if once_per_turn:
        ab["oncePerTurn"] = True
    if usable_by_runner:
        ab["usableByRunnerOnSelfIce"] = True
    if require_encounter_subtype:
        ab["requireEncounterSubtype"] = require_encounter_subtype
    return ab


def map_card(c: dict) -> dict | None:
    cid = slugify(c["title"])
    if cid in REPRINTS:
        return None

    if cid == "paige-piper":
        return base(
            c,
            subtypes=["connection"],
            onFirstInstallEachTurn=may(
                do("paige_piper_search_stack_copies_to_heap"),
                label="Search stack for copies → heap",
                decline_side="runner",
            ),
        )

    if cid == "adjusted-chronotype":
        return base(
            c,
            subtypes=["genetics"],
            onFirstClickLossEachTurnExceptPaidAbility=do(
                "gain_clicks", side="runner", amount=1
            ),
        )

    if cid == "spike":
        card = breaker_card(c, "barrier", 0, 0, 0, 0)
        card["breaker"]["breakViaPaidAbilityOnly"] = True
        card["breaker"]["breakMaxSubs"] = 3
        del card["breaker"]["pumpCredits"]
        del card["breaker"]["pumpStrength"]
        card["memoryCostZeroIfLinkGte"] = 2
        card["strengthBonusPerIcebreaker"] = 1
        card["paidAbilities"] = [
            {
                "id": "spike-break",
                "label": "[trash]: Break up to 3 barrier subroutines",
                "clickCost": 0,
                "creditCost": 0,
                "cost": {"trashSelf": True},
                "windows": ["encounter_paw"],
                "requireEncounterSubtype": "barrier",
                "effect": do("break_encounter_subroutine", maxSubs=3),
            }
        ]
        return card

    if cid == "enhanced-vision":
        return base(
            c,
            subtypes=["genetics"],
            onFirstSuccessfulRunThisTurn=do("reveal_random_hq_card"),
        )

    if cid == "gene-conditioning-shoppe":
        return base(
            c,
            subtypes=["location"],
            geneticsAlsoTriggerSecondTime=True,
        )

    if cid == "synthetic-blood":
        return base(
            c,
            subtypes=["genetics"],
            onFirstDamageEachTurn=draw("runner", 1),
        )

    if cid == "traffic-jam":
        return base(
            c,
            subtypes=["current"],
            lingerAsCurrent=True,
            currentTrashOnAgendaScored=True,
            agendaAdvancementRequirementBonusPerCopyInCorpScore=1,
        )

    if cid == "symmetrical-visage":
        return base(
            c,
            subtypes=["genetics"],
            onFirstBasicClickDrawEachTurn=gain("runner", 1),
        )

    if cid == "brain-taping-warehouse":
        return base(
            c,
            subtypes=["facility"],
            bioroidIceRezCostReductionPerRunnerClickRemaining=1,
        )

    if cid == "next-gold":
        return base(
            c,
            subtypes=["sentry", "next", "ap", "destroyer"],
            subroutines=[
                {
                    "id": "next-gold-net",
                    "text": "Do X net damage.",
                    "effect": do("next_gold_net_damage"),
                },
                {
                    "id": "next-gold-trash",
                    "text": "Trash X programs.",
                    "effect": do("next_gold_trash_programs"),
                },
            ],
        )

    if cid == "jinteki-biotech-life-imagined":
        return base(
            c,
            subtypes=["division"],
            chooseIdentityFaceBeforeFirstTurn=True,
            identityFaceOptions=[
                {
                    "id": "brewery",
                    "label": "Brewery",
                    "onFlip": net(2),
                },
                {
                    "id": "agriculture",
                    "label": "Agriculture Division",
                    "onFlip": do("jinteki_biotech_shuffle_archives_into_rd"),
                },
                {
                    "id": "warehouse",
                    "label": "Warehouse",
                    "onFlip": do("jinteki_biotech_place_4_advancement"),
                },
            ],
            paidAbilities=[
                paid(
                    "jinteki-biotech-flip",
                    "[click][click][click]: Flip this identity",
                    do("jinteki_biotech_flip"),
                    clicks=3,
                    windows=["corp_action_paw"],
                )
            ],
        )

    if cid == "genetic-resequencing":
        return base(
            c,
            subtypes=["research"],
            onScore=may(
                do("genetic_resequencing_place_agenda_counter"),
                label="Place 1 agenda counter on a scored agenda",
                decline_side="corp",
            ),
        )

    if cid == "cortex-lock":
        return base(
            c,
            subtypes=["sentry", "ap"],
            subroutines=[
                {
                    "id": "cortex-lock-net",
                    "text": "Do 1 net damage for each unused MU the Runner has.",
                    "effect": do("net_damage_equal_unused_mu"),
                }
            ],
        )

    if cid == "valley-grid":
        return base(
            c,
            subtypes=["region"],
            onFullyBreakProtectingIce=do(
                "valley_grid_hand_size_penalty_until_next_corp_turn"
            ),
        )

    if cid == "bandwidth":
        return base(
            c,
            subtypes=["code gate"],
            subroutines=[
                {
                    "id": "bandwidth-tag",
                    "text": "Give the Runner 1 tag. If this run is successful, the Runner removes 1 tag.",
                    "effect": do("bandwidth_give_tag_remove_if_successful"),
                }
            ],
        )

    if cid == "predictive-algorithm":
        return base(
            c,
            subtypes=["current"],
            lingerAsCurrent=True,
            currentTrashOnAgendaStolen=True,
            stealAdditionalCreditsWhileRezzed=2,
        )

    if cid == "capital-investors":
        return base(
            c,
            paidAbilities=[
                paid(
                    "capital-investors-gain",
                    "[click]: Gain 2¢",
                    gain("corp", 2),
                    clicks=1,
                    windows=["corp_action_paw"],
                )
            ],
        )

    if cid == "negotiator":
        return base(
            c,
            subtypes=["sentry", "destroyer"],
            paidAbilities=[
                paid(
                    "negotiator-break",
                    "2¢: Break 1 subroutine on this ice (Runner only)",
                    do("break_subroutine_on_self", amount=1),
                    credits=2,
                    windows=["encounter_paw"],
                    usable_by_runner=True,
                )
            ],
            subroutines=[
                {
                    "id": "negotiator-gain",
                    "text": "Gain 2¢.",
                    "effect": gain("corp", 2),
                },
                {
                    "id": "negotiator-trash",
                    "text": "Trash 1 installed program.",
                    "effect": do("trash_program"),
                },
            ],
        )

    if cid == "tech-startup":
        return base(
            c,
            onTurnBegin=may(
                seq(
                    do("trash_self"),
                    do("tech_startup_search_rd_asset_install"),
                ),
                label="Trash Tech Startup → search R&D for an asset",
                decline_side="corp",
            ),
        )

    card = base(c)
    card["unsupported"] = [f"Unmapped val card: {cid}"]
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
