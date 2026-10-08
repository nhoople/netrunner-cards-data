#!/usr/bin/env python3
"""Generate Station One (so) card JSON from pinned pack `so`.

Fetch: python3 scripts/nsg_catalog.py fetch so
Red Sand #2 after Daedalus Complex (floor v1.128.0 → v1.129.0).
Reprint skips: none (20/20 new clears).
Follow NSG pack stripped_text (not IR-hint paraphrases).
Slug via spin_common.slugify (Möbius→mobius, Los: Data Hijacker→los-data-hijacker).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from nsg_catalog import load_pack_cards
from spin_common import (
    base,
    core,
    do,
    draw,
    etr,
    gain,
    seq,
    slugify,
    write_manifest,
)

OUT = Path(__file__).resolve().parents[1] / "data" / "station-one"
WAVE = "station-one"
PACK = "so"
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
    return ab


def map_card(c: dict) -> dict | None:
    cid = slugify(c["title"])
    if cid in REPRINTS:
        return None

    if cid == "severnius-stim-implant":
        return base(
            c,
            subtypes=["cybernetic"],
            paidAbilities=[
                paid(
                    "severnius-run",
                    "[click]: Trash 2 or more cards from grip. Run HQ or R&D; +1 access per 2 trashed",
                    do("severnius_trash_grip_run_hq_or_rd"),
                    clicks=1,
                    usable_by_runner=True,
                ),
            ],
        )

    if cid == "clan-vengeance":
        return base(
            c,
            placePowerCounterOnSufferAnyDamage=True,
            paidAbilities=[
                paid(
                    "clan-vengeance-trash-hq",
                    "[trash]: Trash 1 card from HQ at random per power counter",
                    do("trash_random_hq_per_power_on_self"),
                    trash_self=True,
                    usable_by_runner=True,
                ),
            ],
        )

    if cid == "counter-surveillance":
        return base(
            c,
            paidAbilities=[
                paid(
                    "counter-surveillance-run",
                    "[click], [trash]: Run any server; on success pay X=tags to access ≤X instead of breach",
                    do("counter_surveillance_run"),
                    clicks=1,
                    trash_self=True,
                    usable_by_runner=True,
                ),
            ],
        )

    if cid == "mobius":
        return base(
            c,
            subtypes=["run"],
            runEvent={
                "servers": "rd",
                "onRunEnd": do("mobius_on_run_end"),
            },
        )

    if cid == "los-data-hijacker":
        return base(
            c,
            subtypes=["natural"],
            onFirstIceRezEachTurn=gain("runner", 2),
        )

    if cid == "system-seizure":
        return base(
            c,
            subtypes=["current"],
            lingerAsCurrent=True,
            currentTrashOnAgendaScored=True,
            systemSeizureFirstPumpStrengthLastsRemainderOfRun=True,
        )

    if cid == "customized-secretary":
        return base(
            c,
            onInstall=do("reveal_host_programs"),
            paidAbilities=[
                paid(
                    "customized-secretary-install",
                    "[click]: Install a hosted program, paying all install costs",
                    do("customized_secretary_install_hosted_program"),
                    clicks=1,
                    usable_by_runner=True,
                ),
            ],
        )

    if cid == "build-script":
        return base(
            c,
            onPlay=seq(gain("runner", 1), draw("runner", 2)),
        )

    if cid == "seidr-adaptive-barrier":
        return base(
            c,
            subtypes=["barrier"],
            strengthBonusPerIceProtectingThisServer=1,
            subroutines=[
                {
                    "id": "seidr-etr",
                    "text": "End the run.",
                    "effect": etr(),
                },
            ],
        )

    if cid == "nerine-2-0":
        return base(
            c,
            subtypes=["code gate", "bioroid", "ap"],
            bioroidBreakMaxSubs=2,
            subroutines=[
                {
                    "id": "nerine-2-0-core-1",
                    "text": "Do 1 core damage. You may draw 1 card.",
                    "effect": seq(
                        core(1),
                        may(draw("corp", 1), label="Draw 1", decline_side="corp"),
                    ),
                },
                {
                    "id": "nerine-2-0-core-2",
                    "text": "Do 1 core damage. You may draw 1 card.",
                    "effect": seq(
                        core(1),
                        may(draw("corp", 1), label="Draw 1", decline_side="corp"),
                    ),
                },
            ],
        )

    if cid == "load-testing":
        return base(
            c,
            onPlay=do("allotted_clicks_next_turn", side="runner", delta=-1),
        )

    if cid == "bloom":
        return base(
            c,
            subtypes=["code gate", "observer"],
            subroutines=[
                {
                    "id": "bloom-other-server",
                    "text": "You may install 1 piece of ice from HQ protecting another server, ignoring all costs.",
                    "effect": do(
                        "may_install_ice_from_hq_other_server_ignore_costs"
                    ),
                },
                {
                    "id": "bloom-inward",
                    "text": "You may install 1 piece of ice from HQ directly inward from this ice, ignoring all costs.",
                    "effect": do(
                        "may_install_ice_from_hq_inward_of_source_ignore_costs"
                    ),
                },
            ],
        )

    if cid == "replanting":
        return base(
            c,
            playAdditionalClick=True,
            onPlay=seq(
                do("add_installed_to_hq"),
                do("install_2_from_hq_ignore_costs"),
            ),
        )

    if cid == "cpc-generator":
        return base(
            c,
            corpGainsOnFirstRunnerBasicGainCreditEachTurn=1,
        )

    if cid == "free-lunch":
        return base(
            c,
            subtypes=["code gate"],
            paidAbilities=[
                paid(
                    "free-lunch-lose",
                    "Hosted power counter: The Runner loses 1¢",
                    do("lose_credits", side="runner", amount=1),
                    cost={"powerCounters": 1},
                    windows=[
                        "corp_action_paw",
                        "approach_paw",
                        "encounter_paw",
                        "approach_server_paw",
                    ],
                ),
            ],
            subroutines=[
                {
                    "id": "free-lunch-power-1",
                    "text": "Place 1 power counter on Free Lunch.",
                    "effect": do("add_power_counter", amount=1),
                },
                {
                    "id": "free-lunch-power-2",
                    "text": "Place 1 power counter on Free Lunch.",
                    "effect": do("add_power_counter", amount=1),
                },
            ],
        )

    if cid == "mca-informant":
        return base(
            c,
            subtypes=["gray ops"],
            endsActionPhase=True,
            onPlay=do("host_on_connection"),
        )

    if cid == "clyde-van-rite":
        return base(
            c,
            subtypes=["executive"],
            unique=True,
            onTurnBegin=do("pay_or_trash_top_stack"),
        )

    if cid == "watchtower":
        return base(
            c,
            subtypes=["code gate"],
            subroutines=[
                {
                    "id": "watchtower-search",
                    "text": "Search R&D for a card and add it to HQ. Shuffle R&D.",
                    "effect": do("search_rd_to_hq", amount=1),
                },
            ],
        )

    if cid == "sacrifice":
        return base(
            c,
            playAdditionalCostForfeitAgenda=True,
            onPlay=do("remove_bp_equal_forfeited_ap_gain_credits"),
        )

    if cid == "self-adapting-code-wall":
        return base(
            c,
            subtypes=["barrier"],
            strengthCannotBeLowered=True,
            subroutines=[
                {
                    "id": "sacw-etr",
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
