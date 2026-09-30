#!/usr/bin/env python3
"""Generate Intervention (in) card JSON from pinned pack `in`.

Fetch: python3 scripts/nrdb_catalog.py fetch in
Flashpoint #4 after Escalation (floor v1.124.0 → v1.125.0).
Reprint skips: en-passant, haas-bioroid-architects-of-tomorrow (18/20 new clears).
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

OUT = Path(__file__).resolve().parents[1] / "data" / "intervention"
WAVE = "intervention"
PACK = "in"
EXPECTED = 20

REPRINTS: set[str] = {
    "en-passant",
    "haas-bioroid-architects-of-tomorrow",
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
    require_fully_broken: bool = False,
    require_pending_damage_types: list[str] | None = None,
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
    if require_pending_damage_types is not None:
        ab["requirePendingDamageTypes"] = require_pending_damage_types
    return ab


def trace_sub(strength: int, on_success, on_failure=None) -> dict:
    action: dict = {"kind": "trace", "strength": strength, "onSuccess": on_success}
    if on_failure is not None:
        action["onFailure"] = on_failure
    return {"op": "do", "action": action}


def etr_if_tagged() -> dict:
    return {
        "op": "if",
        "cond": {"op": "runner_tagged"},
        "then": etr(),
    }


def map_card(c: dict) -> dict | None:
    cid = slugify(c["title"])
    if cid in REPRINTS:
        return None

    if cid == "frantic-coding":
        return base(
            c,
            onPlay=do("frantic_coding_look_top_install", n=10, discount=5),
        )

    if cid == "the-gauntlet":
        return base(
            c,
            subtypes=["console"],
            unique=True,
            muBonus=2,
            bonusAccessOnHqBreachPerFullyBrokenProtectingIce=True,
        )

    if cid == "saker":
        return base(
            c,
            subtypes=["icebreaker", "fracter"],
            memoryCost=1,
            breaker={
                "breaksSubtype": "barrier",
                "strength": 1,
                "breakCredits": 1,
                "breakMaxSubs": 1,
                "pumpCredits": 2,
                "pumpStrength": 2,
            },
            paidAbilities=[
                paid(
                    "saker-derez",
                    "2¢, add this program to your grip: Derez fully broken barrier",
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

    if cid == "blockade-runner":
        return base(
            c,
            subtypes=["connection"],
            paidAbilities=[
                paid(
                    "blockade-runner-draw",
                    "[click],[click]: Draw 3 cards. Shuffle 1 card from your grip into your stack",
                    seq(
                        draw("runner", 3),
                        do("shuffle_one_grip_into_stack"),
                    ),
                    clicks=2,
                    windows=["runner_action_paw"],
                    usable_by_runner=True,
                ),
            ],
        )

    if cid == "ele-smoke-scovak-cynosure-of-the-net":
        return base(
            c,
            subtypes=["g-mod", "stealth"],
            link=c.get("base_link", 0),
            recurringCreditsMax=1,
            recurringSpendFor=["use_program"],
        )

    if cid == "top-hat":
        return base(
            c,
            mayInsteadOfBreachRdAccessOneOfTopN=5,
        )

    if cid == "blackstone":
        return base(
            c,
            subtypes=["icebreaker", "fracter"],
            memoryCost=1,
            breaker={
                "breaksSubtype": "barrier",
                "strength": 3,
                "breakCredits": 1,
                "breakMaxSubs": 1,
                "breakViaPaidAbilityOnly": False,
            },
            paidAbilities=[
                paid(
                    "blackstone-break",
                    "1¢: Break 1 barrier subroutine",
                    do(
                        "break_encounter_subroutine",
                        maxSubs=1,
                        requireSubtype="barrier",
                    ),
                    credits=1,
                    windows=["encounter_paw"],
                    usable_by_runner=True,
                ),
                paid(
                    "blackstone-pump",
                    "3¢ (≥1 stealth): +4 strength for the remainder of this run",
                    do("pump_strength", amount=4, duration="run"),
                    credits=3,
                    cost={"credits": 3, "minCreditsFromStealth": 1},
                    windows=["encounter_paw"],
                    usable_by_runner=True,
                ),
            ],
        )

    if cid == "government-investigations":
        return base(
            c,
            subtypes=["current"],
            lingerAsCurrent=True,
            currentTrashOnAgendaStolen=True,
            # NRDB: "While secretly spending credits, players cannot spend 2 credits."
            # (exactly 2 — not >2)
            secretSpendCannotEqual=2,
        )

    if cid == "citadel-sanctuary":
        return base(
            c,
            subtypes=["location"],
            unique=True,
            onDiscardPhaseEnd={
                "op": "if",
                "cond": {"op": "runner_tagged"},
                "then": trace_sub(
                    1,
                    gain("corp", 0),
                    do("remove_tags", amount=1),
                ),
            },
            paidAbilities=[
                {
                    **paid(
                        "citadel-prevent-meat",
                        "[interrupt] → [trash], trash all cards from your grip: Prevent all meat damage",
                        do("prevent_pending_damage", amount=99),
                        cost={"trashSelf": True, "trashEntireGrip": True},
                        windows=["damage_interrupt_paw"],
                        require_pending_damage_types=["meat"],
                    ),
                },
            ],
        )

    if cid == "wetwork-refit":
        return base(
            c,
            subtypes=["condition"],
            onPlay=do("host_on_rezzed_bioroid_ice_as_condition"),
            hostGainsSubroutinesBeforePrinted=[
                {
                    "id": "wetwork-core",
                    "text": "Do 1 core damage.",
                    "effect": do("core_damage", amount=1),
                }
            ],
        )

    if cid == "fumiko-yamamori":
        return base(
            c,
            subtypes=["character"],
            unique=True,
            meatDamageWhenSecretSpendAmountsDiffer=1,
        )

    if cid == "hasty-relocation":
        return base(
            c,
            playAdditionalCost=do("trash_top_of_rd"),
            onPlay=seq(
                draw("corp", 3),
                do("add_n_hq_to_top_rd", amount=3),
            ),
        )

    if cid == "data-ward":
        return base(
            c,
            subtypes=["barrier"],
            onEncounter=choose(
                "runner",
                [
                    {
                        "id": "pay3",
                        "label": "Pay 3¢",
                        "effect": do("lose_credits", side="runner", amount=3),
                    },
                    {
                        "id": "tag",
                        "label": "Take 1 tag",
                        "effect": do("give_tags", amount=1),
                    },
                ],
            ),
            subroutines=[
                {
                    "id": f"data-ward-etr-{i}",
                    "text": "End the run if the Runner is tagged.",
                    "effect": etr_if_tagged(),
                }
                for i in range(1, 5)
            ],
        )

    if cid == "drone-screen":
        return base(
            c,
            onRunDeclaredOnThisServerIfTagged=trace_sub(
                3,
                do("meat_damage", amount=1, cannotPrevent=True),
            ),
        )

    if cid == "chief-slee":
        return base(
            c,
            subtypes=["character"],
            unique=True,
            placePowerPerUnbrokenSubOnAnyEncounterEnd=True,
            paidAbilities=[
                paid(
                    "chief-slee-meat",
                    "[click], 5 hosted power counters: Do 5 meat damage",
                    do("meat_damage", amount=5),
                    clicks=1,
                    cost={"clicks": 1, "powerCounters": 5},
                    windows=["corp_action_paw"],
                ),
            ],
        )

    if cid == "bulwark":
        return base(
            c,
            subtypes=["barrier", "liability"],
            badPublicityOnRez=1,
            # NRDB: when encountered, if there is an installed AI program, gain 2¢
            onEncounter=do(
                "gain_credits_if_runner_has_installed_subtype",
                side="corp",
                amount=2,
                subtype="ai",
            ),
            subroutines=[
                {
                    "id": "bulwark-trash-program",
                    "text": "The Runner trashes 1 installed program.",
                    "effect": do("trash_program"),
                },
                {
                    "id": "bulwark-gain-etr-1",
                    "text": "Gain 2¢. End the run.",
                    "effect": seq(gain("corp", 2), etr()),
                },
                {
                    "id": "bulwark-gain-etr-2",
                    "text": "Gain 2¢. End the run.",
                    "effect": seq(gain("corp", 2), etr()),
                },
            ],
        )

    if cid == "best-defense":
        return base(
            c,
            subtypes=["gray ops"],
            onPlay=do("trash_installed_with_install_cost_lte_tags"),
        )

    if cid == "preemptive-action":
        return base(
            c,
            subtypes=["terminal"],
            endsActionPhase=True,
            rfgInsteadOfTrashing=True,
            onPlay=do("shuffle_archives_to_rd", amount=3),
        )

    card = base(c)
    card["unsupported"] = [f"Unmapped in card: {cid}"]
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
