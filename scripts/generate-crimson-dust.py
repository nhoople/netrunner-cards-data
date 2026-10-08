#!/usr/bin/env python3
"""Generate Crimson Dust (cd) card JSON from pinned pack `cd`.

Fetch: python3 scripts/nsg_catalog.py fetch cd
Red Sand #6 after Free Mars (floor v1.133.0 → v1.134.0).
Reprint skips: none (20/20 new clears).
Follow NSG pack stripped_text (not IR-hint paraphrases).
Slug via spin_common.slugify (Diana's Hunt→dianas-hunt, AR-Enhanced→ar-enhanced-security).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from nsg_catalog import load_pack_cards
from spin_common import (
    base,
    do,
    draw,
    etr,
    nested_unless,
    gain,
    seq,
    slugify,
    write_manifest,
)

OUT = Path(__file__).resolve().parents[1] / "data" / "crimson-dust"
WAVE = "crimson-dust"
PACK = "cd"
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
    require_during_run: bool = False,
    require_this_server: bool = False,
    require_encounter_subtype: str | None = None,
    require_pending_damage_types: list[str] | None = None,
    require_suffered_any_damage_this_turn: bool = False,
    require_next_paw_after_damage: bool = False,
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
    if require_during_run:
        ab["requireDuringRun"] = True
    if require_this_server:
        ab["requireThisServer"] = True
    if require_encounter_subtype:
        ab["requireEncounterSubtype"] = require_encounter_subtype
    if require_pending_damage_types:
        ab["requirePendingDamageTypes"] = require_pending_damage_types
    if require_suffered_any_damage_this_turn:
        ab["requireSufferedAnyDamageThisTurn"] = True
    if require_next_paw_after_damage:
        ab["requireNextPawAfterDamage"] = True
    return ab


def breaker(
    c: dict,
    *,
    breaks: str,
    break_credits: int,
    break_max: int = 1,
    pump_credits: int | None = None,
    pump_strength: int | None = None,
    break_via_paid_only: bool = False,
    **extra,
) -> dict:
    subtypes = []
    if c.get("keywords"):
        subtypes = [s.strip().lower() for s in c["keywords"].split(" - ")]
    card = base(c, subtypes=subtypes, **extra)
    br: dict = {
        "breaksSubtype": breaks,
        "strength": c.get("strength", 0),
        "breakCredits": break_credits,
        "breakMaxSubs": break_max,
    }
    if pump_credits is not None:
        br["pumpCredits"] = pump_credits
        br["pumpStrength"] = pump_strength if pump_strength is not None else 1
    if break_via_paid_only:
        br["breakViaPaidAbilityOnly"] = True
    card["breaker"] = br
    return card


def map_card(c: dict) -> dict | None:
    cid = slugify(c["title"])
    if cid in REPRINTS:
        return None

    if cid == "mining-accident":
        return base(
            c,
            playRequiresSuccessfulCentralRunThisTurn=True,
            onPlay=seq(
                nested_unless(
                    "corp",
                    do("cd_corp_pay_credits", amount=5),
                    do("give_bad_publicity", amount=1),
                ),
                do("rfg_self"),
            ),
        )

    if cid == "respirocytes":
        return base(
            c,
            subtypes=["cybernetic"],
            onInstall=do("meat_damage", amount=1),
            onFirstEmptyGripEachTurn=seq(
                draw("runner", 1),
                do("add_power_counter", amount=1),
            ),
            onPowerCountersGte={
                "amount": 3,
                "effect": do("trash_self"),
            },
        )

    if cid == "salvaged-vanadis-armory":
        return base(
            c,
            subtypes=["clan"],
            paidAbilities=[
                paid(
                    "vanadis-trash-rd",
                    "[trash]: Corp trashes the top X cards of R&D (X = damage suffered this turn)",
                    do("trash_top_rd_equal_damage_suffered_this_turn"),
                    trash_self=True,
                    windows=[
                        "runner_action_paw",
                        "corp_action_paw",
                        "approach_paw",
                        "encounter_paw",
                        "approach_server_paw",
                    ],
                    usable_by_runner=True,
                    require_next_paw_after_damage=True,
                ),
            ],
        )

    if cid == "aumakua":
        return breaker(
            c,
            breaks="*",
            break_credits=1,
            break_max=1,
            strengthPerVirusCounter=1,
            placeVirusCounterOnExposeAnyCard=True,
            placeVirusCounterOnFinishBreachIfNoStealOrTrash=True,
        )

    if cid == "caldera":
        return base(
            c,
            subtypes=["virtual"],
            paidAbilities=[
                paid(
                    "caldera-prevent",
                    "[interrupt] → 3¢: Prevent 1 core damage or 1 net damage",
                    do("prevent_pending_damage", amount=1),
                    credits=3,
                    windows=["damage_interrupt_paw"],
                    usable_by_runner=True,
                    require_pending_damage_types=["net", "core"],
                ),
            ],
        )

    if cid == "dianas-hunt":
        return base(
            c,
            subtypes=["run"],
            runEvent={
                "servers": "any",
                "onEncounterMayInstallProgramFromGripIgnoringCosts": True,
                "trashProgramsInstalledThisWayOnRunEnd": True,
            },
        )

    if cid == "reshape":
        return base(
            c,
            onPlay=do("swap_2_unrezzed_ice"),
        )

    if cid == "dummy-box":
        return base(
            c,
            subtypes=["virtual"],
            paidAbilities=[
                paid(
                    "dummy-box-prevent",
                    "[interrupt] → Trash 1 card from grip: Prevent Corp trashing 1 installed card of the same type",
                    do("trash_grip_same_type_prevent"),
                    windows=["trash_interrupt_paw"],
                    usable_by_runner=True,
                ),
            ],
        )

    if cid == "corporate-defector":
        return base(
            c,
            subtypes=["connection"],
            revealCorpBasicActionDraws=True,
        )

    if cid == "cfc-excavation-contract":
        return base(
            c,
            onScore=do(
                "gain_credits",
                side="corp",
                amount=0,
                tally={
                    "count": "rezzed_ice_subtype",
                    "per": 2,
                    "side": "corp",
                    "subtype": "bioroid",
                },
            ),
        )

    if cid == "mca-austerity-policy":
        return base(
            c,
            paidAbilities=[
                paid(
                    "mca-place-power",
                    "[click]: Place 1 power counter; Runner loses [click] at start of their next turn",
                    seq(
                        do("add_power_counter", amount=1),
                        do("allotted_clicks_next_turn", side="runner", delta=-1),
                    ),
                    clicks=1,
                    once_per_turn=True,
                    windows=["corp_action_paw"],
                ),
                paid(
                    "mca-gain-clicks",
                    "[click], [trash], 3 hosted power counters: Gain [click][click][click][click]",
                    do("gain_clicks", side="corp", amount=4),
                    clicks=1,
                    trash_self=True,
                    cost={"powerCounters": 3},
                    windows=["corp_action_paw"],
                ),
            ],
        )

    if cid == "restore":
        return base(
            c,
            onPlay=do("install_and_rez_from_archives_paying_costs_rfg_other_copies"),
        )

    if cid == "breached-dome":
        return base(
            c,
            subtypes=["ambush"],
            mustRevealWhenAccessedFromRd=True,
            onAccess=seq(
                do("meat_damage", amount=1),
                do("trash_top_of_stack"),
            ),
        )

    if cid == "sand-storm":
        return base(
            c,
            subtypes=["trap", "deflector"],
            subroutines=[
                {
                    "id": "sand-storm-move-trash",
                    "text": "If this ice is installed, move it to the outermost position protecting another server. (The run continues from this new position.) Trash this ice.",
                    "effect": seq(
                        do("move_source_ice_to_outermost_another_server_continue_run"),
                        do("trash_self"),
                    ),
                },
            ],
        )

    if cid == "ar-enhanced-security":
        return base(
            c,
            subtypes=["security"],
            onFirstCorpCardTrashEachTurn=do("give_tags", amount=1),
        )

    if cid == "rolling-brownout":
        return base(
            c,
            subtypes=["current"],
            lingerAsCurrent=True,
            currentTrashOnAgendaStolen=True,
            operationAndEventPlayCostIncrease=1,
            corpGainsCreditsOnFirstRunnerEventEachTurn=1,
        )

    if cid == "threat-level-alpha":
        return base(
            c,
            subtypes=["double"],
            playAdditionalClick=True,
            onPlay=do(
                "trace",
                strength=1,
                onSuccess=do("give_tags_equal_to_runner_tags_min_1"),
            ),
        )

    if cid == "priority-construction":
        return base(
            c,
            subtypes=["double"],
            playAdditionalClick=True,
            onPlay=do(
                "install_ice_from_hq_outermost_remote_ignore_costs_place_advancements",
                advancements=3,
            ),
        )

    if cid == "fractal-threat-matrix":
        return base(
            c,
            subtypes=["security protocol"],
            trashTopOfStackWhenAllSubsBrokenOnProtectingIce=2,
        )

    if cid == "conundrum":
        return base(
            c,
            subtypes=["code gate"],
            strengthBonusIfInstalledSubtype={"subtype": "ai", "bonus": 3},
            subroutines=[
                {
                    "id": "conundrum-trash-program",
                    "text": "The Runner trashes an installed program.",
                    "effect": do("trash_program", pick="choose"),
                },
                {
                    "id": "conundrum-lose-click",
                    "text": "The Runner loses [click], if able.",
                    "effect": do("lose_clicks", side="runner", amount=1),
                },
                {
                    "id": "conundrum-etr",
                    "text": "End the run.",
                    "effect": etr(),
                },
            ],
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
