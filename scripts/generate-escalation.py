#!/usr/bin/env python3
"""Generate Escalation (es) card JSON from pinned pack `es`.

Fetch: python3 scripts/nrdb_catalog.py fetch es
Flashpoint #3 after Blood Money (floor v1.123.0 → v1.124.0).
Reprint skip: none (20/20 new clears).
Follow NRDB stripped_text (not IR-hint paraphrases).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from nrdb_catalog import load_pack_cards
from spin_common import (
    base,
    do,
    draw,
    etr,
    gain,
    net,
    seq,
    slugify,
    write_manifest,
)

OUT = Path(__file__).resolve().parents[1] / "data" / "escalation"
WAVE = "escalation"
PACK = "es"
EXPECTED = 20

REPRINTS: set[str] = set()


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
    require_fully_broken: bool = False,
    starts_run: dict | None = None,
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
    if require_fully_broken:
        ab["requireFullyBrokenThisEncounter"] = True
    if starts_run is not None:
        ab["startsRun"] = starts_run
    return ab


def trace_sub(strength: int, on_success, on_failure=None) -> dict:
    action: dict = {"kind": "trace", "strength": strength, "onSuccess": on_success}
    if on_failure is not None:
        action["onFailure"] = on_failure
    return {"op": "do", "action": action}


def map_card(c: dict) -> dict | None:
    cid = slugify(c["title"])
    if cid in REPRINTS:
        return None

    if cid == "obelus":
        return base(
            c,
            subtypes=["console"],
            unique=True,
            muBonus=1,
            handSizeBonusPerTag=1,
            drawPerAccessOnFirstSuccessfulHqOrRdRunEndEachTurn=True,
        )

    if cid == "black-orchestra":
        return base(
            c,
            subtypes=["icebreaker", "decoder"],
            memoryCost=1,
            mayInstallSelfFromHeapOnEncounterCodeGate=True,
            breaker={
                "breaksSubtype": "code gate",
                "strength": 2,
                "breakCredits": 3,
                "breakMaxSubs": 2,
                "breakViaPaidAbilityOnly": True,
            },
            paidAbilities=[
                paid(
                    "black-orchestra-x",
                    "3¢: +2 strength. Then, if this can interface, break up to 2 code gate subroutines",
                    do("black_orchestra_spend_pump_and_break"),
                    credits=3,
                    windows=["encounter_paw"],
                    usable_by_runner=True,
                ),
            ],
        )

    if cid == "omar-keung-conspiracy-theorist":
        return base(
            c,
            subtypes=["natural"],
            link=c.get("base_link", 0),
            paidAbilities=[
                paid(
                    "omar-archives",
                    "[click]: Run Archives. If that run would be successful, change attacked server to HQ or R&D",
                    gain("runner", 0),
                    clicks=1,
                    windows=["runner_action_paw"],
                    usable_by_runner=True,
                    once_per_turn=True,
                    starts_run={
                        "servers": "archives",
                        "redirectSuccessChooseHqOrRd": True,
                    },
                ),
            ],
        )

    if cid == "peregrine":
        return base(
            c,
            subtypes=["icebreaker", "decoder"],
            memoryCost=1,
            breaker={
                "breaksSubtype": "code gate",
                "strength": 2,
                "breakCredits": 1,
                "breakMaxSubs": 1,
                "pumpCredits": 3,
                "pumpStrength": 3,
            },
            paidAbilities=[
                paid(
                    "peregrine-derez",
                    "2¢, add this program to your grip: Derez fully broken code gate",
                    seq(
                        do("derez_encounter_ice"),
                        do("return_source_to_grip"),
                    ),
                    credits=2,
                    windows=["encounter_paw"],
                    usable_by_runner=True,
                    require_fully_broken=True,
                ),
            ],
        )

    if cid == "houdini":
        return base(
            c,
            subtypes=["icebreaker", "decoder"],
            memoryCost=1,
            breaker={
                "breaksSubtype": "code gate",
                "strength": 2,
                "breakCredits": 1,
                "breakMaxSubs": 1,
                "breakViaPaidAbilityOnly": False,
            },
            paidAbilities=[
                paid(
                    "houdini-break",
                    "1¢: Break 1 code gate subroutine",
                    do(
                        "break_encounter_subroutine",
                        maxSubs=1,
                        requireSubtype="code gate",
                    ),
                    credits=1,
                    windows=["encounter_paw"],
                    usable_by_runner=True,
                ),
                paid(
                    "houdini-pump",
                    "2¢ (≥1 stealth): +4 strength for the remainder of this run",
                    do("pump_strength", amount=4, duration="run"),
                    credits=2,
                    cost={"credits": 2, "minCreditsFromStealth": 1},
                    windows=["encounter_paw"],
                    usable_by_runner=True,
                ),
            ],
        )

    if cid == "net-mercur":
        return base(
            c,
            subtypes=["stealth", "virtual"],
            unique=True,
            firstStealthSpendEachRunPlaceCreditOrDraw=True,
            spendHostedCreditsForAnything=True,
        )

    if cid == "find-the-truth":
        return base(
            c,
            subtypes=["directive", "virtual"],
            unique=True,
            revealDrawnCards=True,
            onFirstSuccessfulRunThisTurn=may(
                do("look_top_1_rd"),
                label="Look at the top card of R&D",
            ),
        )

    if cid == "first-responders":
        return base(
            c,
            subtypes=["connection"],
            paidAbilities=[
                {
                    **paid(
                        "first-responders-draw",
                        "2¢: Draw 1 card (if suffered Corp damage this turn)",
                        draw("runner", 1),
                        credits=2,
                        windows=["runner_action_paw"],
                        usable_by_runner=True,
                    ),
                    "requireSufferedCorpDamageThisTurn": True,
                },
            ],
        )

    if cid == "fairchild-3-0":
        return base(
            c,
            subtypes=["code gate", "bioroid", "ap"],
            bioroidBreakMaxSubs=3,
            subroutines=[
                {
                    "id": "fairchild-3-0-pay-or-trash-1",
                    "text": "The Runner must pay 3¢ or trash 1 of their installed cards.",
                    "effect": do(
                        "pay_credits_or_trash_installed",
                        side="runner",
                        amount=3,
                    ),
                },
                {
                    "id": "fairchild-3-0-pay-or-trash-2",
                    "text": "The Runner must pay 3¢ or trash 1 of their installed cards.",
                    "effect": do(
                        "pay_credits_or_trash_installed",
                        side="runner",
                        amount=3,
                    ),
                },
                {
                    "id": "fairchild-3-0-core-or-etr",
                    "text": "Do 1 core damage or end the run.",
                    "effect": choose(
                        "corp",
                        [
                            {
                                "id": "core",
                                "label": "Do 1 core damage",
                                "effect": do("core_damage", amount=1),
                            },
                            {
                                "id": "etr",
                                "label": "End the run",
                                "effect": etr(),
                            },
                        ],
                    ),
                },
            ],
        )

    if cid == "ark-lockdown":
        return base(
            c,
            onPlay=do("ark_lockdown_name_and_rfg_heap_copies"),
        )

    if cid == "hellion-beta-test":
        return base(
            c,
            subtypes=["black ops", "liability"],
            playRequiresRunnerTrashedCorpCardLastTurn=True,
            onPlay=trace_sub(
                2,
                do("hellion_beta_trash_two_installed_non_program"),
                do("give_bad_publicity", amount=1),
            ),
        )

    if cid == "project-kusanagi":
        return base(
            c,
            subtypes=["security"],
            onScore=do(
                "add_agenda_counters_from_overadvance",
                past=2,
                per=1,
            ),
            paidAbilities=[
                paid(
                    "kusanagi-net-sub",
                    "Hosted agenda counter: choose ice to gain '[subroutine] Do 1 net damage' this run",
                    do("kusanagi_grant_net_subroutine_this_run"),
                    cost={"agendaCounters": 1},
                    windows=["corp_action_paw", "encounter_paw", "approach_paw"],
                ),
            ],
        )

    if cid == "dna-tracker":
        return base(
            c,
            subtypes=["code gate", "ap"],
            subroutines=[
                {
                    "id": f"dna-tracker-{i}",
                    "text": "Do 1 net damage. The Runner loses 2¢.",
                    "effect": seq(
                        net(1),
                        do("lose_credits", side="runner", amount=2),
                    ),
                }
                for i in range(1, 4)
            ],
        )

    if cid == "jinteki-potential-unleashed":
        return base(
            c,
            subtypes=["megacorp"],
            trashTopOfStackOnRunnerNetDamage=True,
        )

    if cid == "alexa-belsky":
        return base(
            c,
            subtypes=["character"],
            unique=True,
            paidAbilities=[
                paid(
                    "alexa-shuffle",
                    "[trash]: Shuffle HQ into R&D; Runner may pay 2¢ each to trash instead of shuffling",
                    do("alexa_belsky_shuffle_hq"),
                    trash_self=True,
                    windows=["corp_action_paw"],
                ),
            ],
        )

    if cid == "observe-and-destroy":
        return base(
            c,
            subtypes=["gray ops"],
            playRequiresRunnerCreditsLt=6,
            playAdditionalCost=do("remove_tags", amount=1),
            onPlay=do("trash_installed_runner", pick="choose"),
        )

    if cid == "service-outage":
        return base(
            c,
            subtypes=["current"],
            lingerAsCurrent=True,
            currentTrashOnAgendaStolen=True,
            runnerFirstRunEachTurnAdditionalCost=1,
        )

    if cid == "boom":
        return base(
            c,
            subtypes=["double", "black ops"],
            playRequiresMinTags=2,
            playAdditionalClick=True,
            onPlay=do("meat_damage", amount=7),
        )

    if cid == "door-to-door":
        return base(
            c,
            subtypes=["current", "black ops"],
            lingerAsCurrent=True,
            currentTrashOnAgendaStolen=True,
            onRunnerTurnBegin=trace_sub(
                1,
                {
                    "op": "if",
                    "cond": {"op": "runner_tagged"},
                    "then": do("meat_damage", amount=1),
                    "else": do("give_tags", amount=1),
                },
            ),
        )

    if cid == "scarcity-of-resources":
        return base(
            c,
            subtypes=["current"],
            lingerAsCurrent=True,
            currentTrashOnAgendaStolen=True,
            resourceInstallCostIncrease=2,
        )

    card = base(c)
    card["unsupported"] = [f"Unmapped es card: {cid}"]
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
    print("SKIPPED=" + json.dumps(skipped))
    if len(clear_written) != EXPECTED - len(REPRINTS):
        missing = [cid for cid in written if cid not in clear_written]
        print("UNCLEARED=" + json.dumps(missing))
        sys.exit(1)


if __name__ == "__main__":
    main()
