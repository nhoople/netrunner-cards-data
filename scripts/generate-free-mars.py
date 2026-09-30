#!/usr/bin/env python3
"""Generate Free Mars (fm) card JSON from pinned pack `fm`.

Fetch: python3 scripts/nrdb_catalog.py fetch fm
Red Sand #5 after Blood and Water (floor v1.132.0 → v1.133.0).
Reprint skips: none (20/20 new clears).
Follow NRDB stripped_text (not IR-hint paraphrases).
Slug via spin_common.slugify (Na'Not'K→nanotk, O₂ Shortage→o2-shortage,
Bloo Moose→bloo-moose).
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
    seq,
    slugify,
    write_manifest,
)

OUT = Path(__file__).resolve().parents[1] / "data" / "free-mars"
WAVE = "free-mars"
PACK = "fm"
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

    if cid == "mars-for-martians":
        return base(
            c,
            subtypes=["priority"],
            playRequiresFirstClick=True,
            onPlay=seq(
                do("draw_per_installed_clan_resource", per=1),
                do("gain_credits_per_runner_tags", per=1),
            ),
        )

    if cid == "god-of-war":
        return breaker(
            c,
            breaks="*",
            break_credits=0,
            break_max=1,
            pump_credits=2,
            pump_strength=1,
            break_via_paid_only=True,
            onTurnBegin=may(
                seq(
                    do("give_tags", amount=1),
                    do("add_virus_counter", amount=2),
                ),
                label="Take 1 tag to place 2 virus counters",
            ),
            paidAbilities=[
                paid(
                    "god-of-war-break",
                    "Hosted virus counter: Break 1 subroutine",
                    do("break_encounter_subroutine", maxSubs=1),
                    cost={"virusCounters": 1},
                    windows=["encounter_paw"],
                    usable_by_runner=True,
                ),
            ],
        )

    if cid == "leave-no-trace":
        return base(
            c,
            subtypes=["run"],
            runEvent={
                "servers": "any",
                "onRunEnd": do("derez_all_ice_rezzed_this_run"),
            },
        )

    if cid == "rip-deal":
        return base(
            c,
            subtypes=["run"],
            ripDealHeapInsteadOfHqAccess=True,
            rfgSelfOnRunEnd=True,
            runEvent={"servers": "hq"},
        )

    if cid == "flashbang":
        return breaker(
            c,
            breaks="sentry",
            break_credits=0,
            break_max=1,
            pump_credits=1,
            pump_strength=1,
            break_via_paid_only=True,
            paidAbilities=[
                paid(
                    "flashbang-derez",
                    "6¢: Derez the sentry you are encountering",
                    do("derez_encountered_ice"),
                    credits=6,
                    windows=["encounter_paw"],
                    usable_by_runner=True,
                    require_encounter_subtype="sentry",
                ),
            ],
        )

    if cid == "lean-and-mean":
        return base(
            c,
            subtypes=["run"],
            runEvent={
                "servers": "any",
                "icebreakerStrengthBonusIfInstalledProgramsLte": {
                    "programsMax": 3,
                    "bonus": 2,
                },
            },
        )

    if cid == "maven":
        return breaker(
            c,
            breaks="*",
            break_credits=2,
            break_max=1,
            strengthBonusPerInstalledProgram=1,
        )

    if cid == "nanotk":
        # Title Na'Not'K → nanotk; breaks sentry (NRDB), not barrier.
        return breaker(
            c,
            breaks="sentry",
            break_credits=1,
            break_max=1,
            pump_credits=3,
            pump_strength=2,
            strengthBonusPerIceProtectingAttackedServerDuringRun=1,
        )

    if cid == "bloo-moose":
        return base(
            c,
            subtypes=["location", "seedy"],
            unique=True,
            onTurnBegin=may(
                do("bloo_moose_rfg_heap_gain_credits", credits=2),
                label="Remove 1 card in the heap from the game to gain 2¢",
            ),
        )

    if cid == "o2-shortage":
        return base(
            c,
            onPlay=do("o2_shortage_runner_may_trash_random_grip_or_corp_gains_clicks"),
        )

    if cid == "helheim-servers":
        return base(
            c,
            subtypes=["facility"],
            unique=True,
            paidAbilities=[
                paid(
                    "helheim-boost",
                    "Trash 1 card from HQ: All ice protecting this server has +2 strength until end of run",
                    do("helheim_ice_protecting_this_server_strength_until_end_of_run", amount=2),
                    cost={"trashFromHq": 1},
                    windows=[
                        "corp_action_paw",
                        "approach_paw",
                        "encounter_paw",
                        "approach_server_paw",
                    ],
                    require_during_run=True,
                    require_this_server=True,
                ),
            ],
        )

    if cid == "mandatory-seed-replacement":
        return base(
            c,
            subtypes=["security"],
            onScore=do("rearrange_ice_protecting_all_servers"),
        )

    if cid == "water-monopoly":
        return base(
            c,
            subtypes=["initiative"],
            nonVirtualResourceInstallCostIncrease=1,
        )

    if cid == "metamorph":
        return base(
            c,
            subtypes=["code gate", "observer"],
            subroutines=[
                {
                    "id": "metamorph-swap",
                    "text": "Swap 2 other installed pieces of ice or 2 of your installed non-ice cards.",
                    "effect": do("metamorph_swap_2_other_ice_or_2_non_ice"),
                },
            ],
        )

    if cid == "data-loop":
        return base(
            c,
            subtypes=["barrier"],
            onEncounter=do("choose_n_grip_to_stack_top", count=2),
            subroutines=[
                {
                    "id": "data-loop-etr-if-tagged",
                    "text": "End the run if the Runner is tagged.",
                    "effect": {
                        "op": "if",
                        "cond": {"op": "runner_tagged"},
                        "then": etr(),
                    },
                },
                {
                    "id": "data-loop-etr",
                    "text": "End the run.",
                    "effect": etr(),
                },
            ],
        )

    if cid == "biased-reporting":
        return base(
            c,
            onPlay=do("biased_reporting_choose_type"),
        )

    if cid == "open-forum":
        return base(
            c,
            afterMandatoryDraw=do("open_forum_reveal_top_rd_to_hq_then_hq_to_rd_top"),
        )

    if cid == "tithonium":
        return base(
            c,
            subtypes=["barrier", "destroyer"],
            rezCostCreditDiscountOnForfeitAgenda=c.get("cost", 9),
            cannotHostCards=True,
            subroutines=[
                {
                    "id": "tithonium-trash-program-1",
                    "text": "Trash 1 program.",
                    "effect": do("trash_program", pick="choose"),
                },
                {
                    "id": "tithonium-trash-program-2",
                    "text": "Trash 1 program.",
                    "effect": do("trash_program", pick="choose"),
                },
                {
                    "id": "tithonium-trash-resource-etr",
                    "text": "Trash 1 resource and end the run.",
                    "effect": seq(
                        do("trash_resource", pick="choose"),
                        etr(),
                    ),
                },
            ],
        )

    if cid == "transparency-initiative":
        return base(
            c,
            subtypes=["condition"],
            onPlay=do("transparency_initiative_host_on_agenda"),
            onAdvance=gain("corp", 1),
            hostAgendaGainsPublic=True,
        )

    if cid == "rover-algorithm":
        return base(
            c,
            subtypes=["condition"],
            onPlay=do("host_on_rezzed_ice_as_condition"),
            hostStrengthPerPowerCounter=1,
            onPassHost=do("add_power_counter", amount=1),
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
