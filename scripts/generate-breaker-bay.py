#!/usr/bin/env python3
"""Generate Breaker Bay (bb) card JSON from pinned pack `bb`.

Fetch: python3 scripts/nsg_catalog.py fetch bb
SanSan cycle after The Valley (floor v1.109.0 → v1.110.0).
Reprint skip: career-fair (system-update-2021), turing (system-core-2019).
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
    write_manifest,
)

OUT = Path(__file__).resolve().parents[1] / "data" / "breaker-bay"
WAVE = "breaker-bay"
PACK = "bb"
EXPECTED = 20

REPRINTS = {
    "career-fair",  # system-update-2021
    "turing",  # system-core-2019
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

    if cid == "hacktivist-meeting":
        return base(
            c,
            subtypes=["current"],
            lingerAsCurrent=True,
            currentTrashOnAgendaScored=True,
            rezNonIceAdditionalCostRandomTrashHq=True,
        )

    if cid == "off-campus-apartment":
        return base(
            c,
            subtypes=["location"],
            hostsConnectionResources=True,
            drawOnHostConnectionInstall=1,
        )

    if cid == "dorm-computer":
        return base(
            c,
            powerCountersOnInstall=4,
            paidAbilities=[
                paid(
                    "dorm-computer-run",
                    "[click], hosted power counter: Run any server; prevent all tags this run",
                    do("dorm_computer_run_prevent_all_tags"),
                    clicks=1,
                    power_counters=1,
                    windows=["runner_action_paw"],
                )
            ],
        )

    if cid == "hayley-kaplan-universal-scholar":
        return base(
            c,
            subtypes=["g-mod"],
            onFirstInstallEachTurn=may(
                do("hayley_install_same_type_from_grip"),
                label="Install another card of the same type from grip",
                decline_side="runner",
            ),
        )

    if cid == "game-day":
        return base(
            c,
            subtypes=["double"],
            playAdditionalClick=True,
            onPlay=do("draw_until_grip_equals_max_hand_size"),
        )

    if cid == "comet":
        return base(
            c,
            subtypes=["console"],
            maxConsole=1,
            muBonus=1,
            onFirstEventEachTurnMayPlayAnother=True,
        )

    if cid == "study-guide":
        card = breaker_card(c, "code gate", 0, 1, 0, 0)
        # Strength comes from power counters, not temporary pump.
        del card["breaker"]["pumpCredits"]
        del card["breaker"]["pumpStrength"]
        card["strengthPerPowerCounter"] = True
        card["paidAbilities"] = [
            paid(
                "study-guide-power",
                "2¢: Place 1 power counter on this program",
                do("add_power_counter", amount=1),
                credits=2,
                windows=["runner_action_paw", "encounter_paw"],
            )
        ]
        return card

    if cid == "london-library":
        return base(
            c,
            subtypes=["location"],
            trashHostedProgramsOnTurnEnd=True,
            paidAbilities=[
                paid(
                    "london-library-host",
                    "[click]: Install a non-virus program from grip on London Library, ignoring install cost",
                    do("host_non_virus_program_ignore_cost"),
                    clicks=1,
                    windows=["runner_action_paw"],
                ),
                paid(
                    "london-library-to-grip",
                    "[click]: Add a program on London Library to your grip",
                    do("add_hosted_program_to_grip"),
                    clicks=1,
                    windows=["runner_action_paw"],
                ),
            ],
        )

    if cid == "tyson-observatory":
        return base(
            c,
            subtypes=["location"],
            paidAbilities=[
                paid(
                    "tyson-search-hardware",
                    "[click][click]: Search stack for a piece of hardware, reveal it, add to grip; shuffle",
                    do("search_stack_type_add_to_grip", cardType="hardware"),
                    clicks=2,
                    windows=["runner_action_paw"],
                )
            ],
        )

    if cid == "beach-party":
        return base(
            c,
            handSizeBonus=5,
            onTurnBegin=do("lose_clicks", side="runner", amount=1),
        )

    if cid == "research-grant":
        return base(
            c,
            subtypes=["research"],
            onScore=may(
                do("score_another_installed_copy_of_self"),
                label="Score another installed Research Grant",
                decline_side="corp",
            ),
        )

    if cid == "crick":
        return base(
            c,
            subtypes=["code gate"],
            strengthBonusProtectingArchives=3,
            subroutines=[
                {
                    "id": "crick-install",
                    "text": "Install a card from Archives (paying its install cost).",
                    "effect": do(
                        "install_from_archives",
                        types=["agenda", "asset", "ice", "upgrade"],
                    ),
                }
            ],
        )

    if cid == "recruiting-trip":
        return base(
            c,
            playCost=0,
            playCostX=True,
            onPlay=do("search_rd_up_to_x_subtype_to_hq", subtype="sysop"),
        )

    if cid == "blacklist":
        return base(
            c,
            cardsCannotLeaveRunnerHeap=True,
        )

    if cid == "gutenberg":
        return base(
            c,
            subtypes=["sentry", "tracer"],
            strengthBonusProtectingRd=3,
            subroutines=[
                {
                    "id": "gutenberg-trace",
                    "text": "Trace[7]. If successful, give the Runner 1 tag.",
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "trace",
                            "strength": 7,
                            "onSuccess": do("give_tags", amount=1),
                        },
                    },
                }
            ],
        )

    if cid == "student-loans":
        return base(
            c,
            eventPlayExtraCostIfCopyInHeap=2,
        )

    if cid == "meru-mati":
        return base(
            c,
            subtypes=["barrier"],
            strengthBonusProtectingHq=3,
            subroutines=[
                {
                    "id": "meru-mati-etr",
                    "text": "End the run.",
                    "effect": etr(),
                }
            ],
        )

    if cid == "breaker-bay-grid":
        return base(
            c,
            subtypes=["region"],
            rootRezCostReductionThisServer=5,
        )

    card = base(c)
    card["unsupported"] = [f"Unmapped bb card: {cid}"]
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
