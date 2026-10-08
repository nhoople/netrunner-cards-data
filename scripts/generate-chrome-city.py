#!/usr/bin/env python3
"""Generate Chrome City (cc) card JSON from pinned pack `cc`.

Fetch: python3 scripts/nsg_catalog.py fetch cc
SanSan cycle after Breaker Bay (floor v1.110.0 → v1.111.0).
Reprint skip: oaktown-renovation, corporate-town (system-update-2021).
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
    core,
    do,
    etr,
    gain,
    seq,
    slugify,
    write_manifest,
)

OUT = Path(__file__).resolve().parents[1] / "data" / "chrome-city"
WAVE = "chrome-city"
PACK = "cc"
EXPECTED = 20

REPRINTS = {
    "oaktown-renovation",  # system-update-2021
    "corporate-town",  # system-update-2021
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
    require_during_run: bool = False,
    require_this_server: bool = False,
    require_runner_clicks_eq: int | None = None,
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
    if require_during_run:
        ab["requireDuringRun"] = True
    if require_this_server:
        ab["requireThisServer"] = True
    if require_runner_clicks_eq is not None:
        ab["requireRunnerClicksEq"] = require_runner_clicks_eq
    return ab


def map_card(c: dict) -> dict | None:
    cid = slugify(c["title"])
    if cid in REPRINTS:
        return None

    if cid == "immolation-script":
        return base(
            c,
            subtypes=["run"],
            runEvent={
                "servers": "archives",
                "immolationScriptAccessReplace": True,
            },
        )

    if cid == "skulljack":
        return base(
            c,
            subtypes=["cybernetic"],
            unique=True,
            corpCardTrashCostReduction=1,
            onInstall=core(1),
        )

    if cid == "turntable":
        return base(
            c,
            subtypes=["console"],
            unique=True,
            maxConsole=1,
            muBonus=1,
            onStealAgenda=may(
                do("swap_stolen_with_corp_scored"),
                label="Swap stolen agenda with one in Corp score area",
                decline_side="runner",
            ),
        )

    if cid == "chrome-parlor":
        return base(
            c,
            subtypes=["location"],
            preventCyberneticInstallDamage=True,
        )

    if cid == "titanium-ribs":
        return base(
            c,
            subtypes=["cybernetic"],
            unique=True,
            runnerChoosesDamageTrashFromGrip=True,
            onInstall=do("meat_damage", amount=2),
        )

    if cid == "crowbar":
        card = breaker_card(c, "code gate", 0, 0, 0, 0)
        card["breaker"]["breakViaPaidAbilityOnly"] = True
        card["breaker"]["breakMaxSubs"] = 3
        del card["breaker"]["pumpCredits"]
        del card["breaker"]["pumpStrength"]
        card["memoryCostZeroIfLinkGte"] = 2
        card["strengthBonusPerIcebreaker"] = 1
        card["paidAbilities"] = [
            {
                "id": "crowbar-break",
                "label": "[trash]: Break up to 3 code gate subroutines",
                "clickCost": 0,
                "creditCost": 0,
                "cost": {"trashSelf": True},
                "windows": ["encounter_paw"],
                "requireEncounterSubtype": "code gate",
                "effect": do("break_encounter_subroutine", maxSubs=3),
            }
        ]
        return card

    if cid == "net-ready-eyes":
        return base(
            c,
            subtypes=["cybernetic"],
            unique=True,
            onInstall=do("meat_damage", amount=2),
            onRunBegin=do("net_ready_eyes_choose_icebreaker_strength", amount=1),
        )

    if cid == "analog-dreamers":
        return base(
            c,
            paidAbilities=[
                paid(
                    "analog-dreamers-run",
                    "[click]: Run R&D. If successful, instead of breaching, may shuffle an unrezzed non-ice card with no advancements into R&D",
                    do("analog_dreamers_run_rd"),
                    clicks=1,
                    windows=["runner_action_paw"],
                )
            ],
        )

    if cid == "brain-cage":
        return base(
            c,
            subtypes=["cybernetic"],
            unique=True,
            handSizeBonus=3,
            onInstall=core(1),
        )

    if cid == "cybernetics-division-humanity-upgraded":
        return base(
            c,
            subtypes=["division"],
            handSizeBonus=-1,
            runnerHandSizeBonus=-1,
        )

    if cid == "self-destruct-chips":
        return base(
            c,
            subtypes=["security"],
            runnerHandSizeBonus=-1,
        )

    if cid == "lab-dog":
        return base(
            c,
            subtypes=["trap"],
            subroutines=[
                {
                    "id": "lab-dog-trash-hardware",
                    "text": "The Runner trashes an installed piece of hardware. Trash Lab Dog.",
                    "effect": seq(
                        do("trash_hardware", pick="choose"),
                        do("trash_self"),
                    ),
                }
            ],
        )

    if cid == "oaktown-grid":
        return base(
            c,
            subtypes=["region"],
            rootTrashCostIncreaseThisServer=3,
        )

    if cid == "ryon-knight":
        return base(
            c,
            subtypes=["sysop"],
            unique=True,
            paidAbilities=[
                paid(
                    "ryon-knight-core",
                    "[trash]: Do 1 core damage (run against this server; Runner has no unspent clicks)",
                    core(1),
                    trash_self=True,
                    windows=[
                        "approach_paw",
                        "encounter_paw",
                        "approach_server_paw",
                    ],
                    require_during_run=True,
                    require_this_server=True,
                    require_runner_clicks_eq=0,
                )
            ],
        )

    if cid == "clairvoyant-monitor":
        return base(
            c,
            subtypes=["code gate", "psi"],
            subroutines=[
                {
                    "id": "clairvoyant-monitor-psi",
                    "text": "Psi game. If bids differ, place 1 advancement token on an installed card and end the run.",
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "play_psi_game",
                            "maxBid": 2,
                            "ifBidsDiffer": {
                                "op": "do",
                                "action": {
                                    "kind": "place_advancements",
                                    "amount": 1,
                                    "pick": "choose",
                                    "then": etr(),
                                },
                            },
                        },
                    },
                }
            ],
        )

    if cid == "lockdown":
        return base(
            c,
            subtypes=["code gate"],
            subroutines=[
                {
                    "id": "lockdown-no-draw",
                    "text": "The Runner cannot draw cards for the remainder of this turn.",
                    "effect": do("runner_cannot_draw_remainder_of_turn"),
                }
            ],
        )

    if cid == "little-engine":
        return base(
            c,
            subtypes=["code gate"],
            subroutines=[
                {
                    "id": "little-engine-etr-1",
                    "text": "End the run.",
                    "effect": etr(),
                },
                {
                    "id": "little-engine-etr-2",
                    "text": "End the run.",
                    "effect": etr(),
                },
                {
                    "id": "little-engine-gain",
                    "text": "The Runner gains 5 credits.",
                    "effect": gain("runner", 5),
                },
            ],
        )

    if cid == "quicksand":
        return base(
            c,
            subtypes=["barrier"],
            strengthPerPowerCounter=True,
            onEncounter=do("add_power_counter", amount=1),
            subroutines=[
                {
                    "id": "quicksand-etr",
                    "text": "End the run.",
                    "effect": etr(),
                }
            ],
        )

    card = base(c)
    card["unsupported"] = [f"Unmapped cc card: {cid}"]
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
