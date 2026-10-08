#!/usr/bin/env python3
"""Generate Kala Ghoda (kg) card JSON from pinned pack `kg`.

Fetch: python3 scripts/nsg_catalog.py fetch kg
Mumbad cycle after Data and Destiny (floor v1.115.0 → v1.116.0).
Reprint skip: run-amok (system-core-2019).
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
    seq,
    slugify,
    trace_sub,
    write_manifest,
)

OUT = Path(__file__).resolve().parents[1] / "data" / "kala-ghoda"
WAVE = "kala-ghoda"
PACK = "kg"
EXPECTED = 19

REPRINTS = {
    "run-amok",  # system-core-2019
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
    power_counters: int = 0,
    windows: list[str] | None = None,
    cost: dict | None = None,
    once_per_turn: bool = False,
    trash_self: bool = False,
    usable_by_runner: bool = False,
    require_encounter_subtype: str | None = None,
    require_pending_damage_types: list[str] | None = None,
    forfeit_agenda: bool = False,
) -> dict:
    c = dict(cost or {})
    if clicks:
        c["clicks"] = clicks
    if credits:
        c["credits"] = credits
    if power_counters:
        c["powerCounters"] = power_counters
    if trash_self:
        c["trashSelf"] = True
    if forfeit_agenda:
        c["forfeitAgenda"] = True
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
    if require_pending_damage_types:
        ab["requirePendingDamageTypes"] = require_pending_damage_types
    return ab


def map_card(c: dict) -> dict | None:
    cid = slugify(c["title"])
    if cid in REPRINTS:
        return None

    if cid == "ramujan-reliant-550-bmi":
        return base(
            c,
            subtypes=["consumer-grade"],
            deckLimit=6,
            paidAbilities=[
                paid(
                    "ramujan-prevent",
                    "[interrupt] → [trash]: Prevent up to X net or core damage; trash that many from stack",
                    do("ramujan_prevent_damage_trash_stack"),
                    trash_self=True,
                    windows=["damage_interrupt_paw"],
                    require_pending_damage_types=["net", "core"],
                    usable_by_runner=True,
                )
            ],
        )

    if cid == "street-magic":
        return base(
            c,
            subtypes=["virtual"],
            runnerChoosesUnbrokenSubroutineOrder=True,
        )

    if cid == "high-stakes-job":
        return base(
            c,
            subtypes=["run", "job"],
            runEvent={
                "servers": "any",
                "requiresUnrezzedIce": True,
                "onSuccessfulRun": gain("runner", 12),
            },
        )

    if cid == "mongoose":
        card = breaker_card(c, "sentry", 1, 1, 2, 2)
        card["breaker"]["breakMaxSubs"] = 2
        card["breakOnAtMostOneIcePerRun"] = True
        return card

    if cid == "jesminder-sareen-girl-behind-the-curtain":
        return base(
            c,
            subtypes=["natural"],
            link=c.get("base_link", 0),
            preventFirstTagThisTurn=True,
        )

    if cid == "maya":
        return base(
            c,
            subtypes=["console"],
            unique=True,
            muBonus=2,
            onFinishAccessRdOncePerTurn=may(
                seq(
                    do("move_accessed_to_bottom_rd"),
                    do("give_tags", amount=1),
                ),
                label="Add accessed card to bottom of R&D; take 1 tag",
                decline_side="runner",
            ),
        )

    if cid == "panchatantra":
        return base(
            c,
            onEncounterAnyIceOncePerTurn=may(
                do("choose_subtype_for_encounter"),
                label="Choose a subtype for encountered ice this run",
                decline_side="runner",
            ),
        )

    if cid == "artist-colony":
        return base(
            c,
            subtypes=["location"],
            paidAbilities=[
                paid(
                    "artist-colony-search",
                    "Forfeit 1 agenda: Search stack for a program, resource, or hardware and install it",
                    do("search_stack_install"),
                    forfeit_agenda=True,
                    windows=["runner_action_paw"],
                    usable_by_runner=True,
                )
            ],
        )

    if cid == "chatterjee-university":
        return base(
            c,
            subtypes=["location", "ritzy"],
            unique=True,
            paidAbilities=[
                paid(
                    "chatterjee-power",
                    "[click]: Place 1 power counter on Chatterjee University",
                    do("add_power_counter", amount=1),
                    clicks=1,
                    windows=["runner_action_paw"],
                    usable_by_runner=True,
                ),
                paid(
                    "chatterjee-install",
                    "[click]: Install a program from grip, lowering cost by power counters; remove 1 power counter",
                    do("chatterjee_install_program_discount"),
                    clicks=1,
                    windows=["runner_action_paw"],
                    usable_by_runner=True,
                ),
            ],
        )

    if cid == "advanced-concept-hopper":
        return base(
            c,
            subtypes=["research"],
            onFirstRunBeginThisTurn=choose(
                "corp",
                [
                    {
                        "id": "draw",
                        "label": "Draw 1 card",
                        "effect": draw("corp", 1),
                    },
                    {
                        "id": "credit",
                        "label": "Gain 1¢",
                        "effect": gain("corp", 1),
                    },
                    {
                        "id": "decline",
                        "label": "Decline",
                        "effect": gain("corp", 0),
                    },
                ],
            ),
        )

    if cid == "vikram-1-0":
        return base(
            c,
            subtypes=["sentry", "bioroid", "tracer", "ap"],
            bioroidBreakMaxSubs=1,
            subroutines=[
                {
                    "id": "vikram-no-programs",
                    "text": "The Runner cannot use programs for the remainder of this run.",
                    "effect": do("kg_cannot_use_programs_this_run"),
                },
                {
                    "id": "vikram-trace-core-1",
                    "text": "Trace[4]. If successful, do 1 core damage.",
                    "effect": trace_sub(4, do("core_damage", amount=1)),
                },
                {
                    "id": "vikram-trace-core-2",
                    "text": "Trace[4]. If successful, do 1 core damage.",
                    "effect": trace_sub(4, do("core_damage", amount=1)),
                },
            ],
        )

    if cid == "heritage-committee":
        return base(
            c,
            subtypes=["alliance"],
            zeroInfluenceIfNonAllianceFactionCardsGte={
                "faction": "jinteki",
                "threshold": 6,
            },
            onPlay=seq(
                draw("corp", 3),
                do("hq_to_top_rd", pick="choose"),
            ),
        )

    if cid == "mumbad-city-grid":
        return base(
            c,
            subtypes=["region"],
            onPassIceProtectingThisServerMaySwap=True,
        )

    if cid == "kala-ghoda-real-tv":
        return base(
            c,
            subtypes=["cast"],
            onTurnBegin=may(
                do("look_at_top_of_stack"),
                label="Look at the top card of the stack",
                decline_side="corp",
            ),
            paidAbilities=[
                paid(
                    "kala-ghoda-trash-top",
                    "[trash]: The Runner trashes the top card of the stack",
                    do("trash_top_of_stack"),
                    trash_self=True,
                    windows=["corp_action_paw"],
                )
            ],
        )

    if cid == "interrupt-0":
        return base(
            c,
            subtypes=["code gate"],
            subroutines=[
                {
                    "id": "interrupt-0-break-cost-1",
                    "text": "For the remainder of this run, icebreaker break abilities cost +1¢.",
                    "effect": do(
                        "arm_icebreaker_break_additional_cost_this_run",
                        amount=1,
                    ),
                },
                {
                    "id": "interrupt-0-break-cost-2",
                    "text": "For the remainder of this run, icebreaker break abilities cost +1¢.",
                    "effect": do(
                        "arm_icebreaker_break_additional_cost_this_run",
                        amount=1,
                    ),
                },
            ],
        )

    if cid == "dedication-ceremony":
        return base(
            c,
            onPlay=do(
                "place_advancements",
                amount=3,
                pick="choose",
                faceupOnly=True,
                cannotScoreTargetThisTurn=True,
            ),
        )

    if cid == "mumba-temple":
        return base(
            c,
            subtypes=["alliance", "facility"],
            zeroInfluenceIfIceInDeckLte=15,
            recurringCreditsMax=2,
            recurringSpendFor=["rez"],
        )

    if cid == "museum-of-history":
        return base(
            c,
            subtypes=["alliance", "ritzy"],
            unique=True,
            zeroInfluenceIfCardsInDeckGte=50,
            onTurnBegin=may(
                do("shuffle_one_archives_into_rd"),
                label="Shuffle 1 card from Archives into R&D",
                decline_side="corp",
            ),
        )

    card = base(c)
    card["unsupported"] = [f"Unmapped kg card: {cid}"]
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
    if len(clear_written) != EXPECTED - len(REPRINTS):
        missing = [cid for cid in written if cid not in clear_written]
        print("UNCLEARED=" + json.dumps(missing))
        sys.exit(1)


if __name__ == "__main__":
    main()
