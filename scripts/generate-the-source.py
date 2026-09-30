#!/usr/bin/env python3
"""Generate The Source (ts) card JSON from pinned pack `ts`.

Fetch: python3 scripts/nrdb_catalog.py fetch ts
Lunar cycle after All That Remains (floor v1.106.0 → v1.107.0).
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
    etr,
    gain,
    draw,
    net,
    slugify,
    write_manifest,
)

OUT = Path(__file__).resolve().parents[1] / "data" / "the-source"
WAVE = "the-source"
PACK = "ts"
EXPECTED = 20

REPRINTS = {
    "earthrise-hotel",  # system-update-2021
}


def errand_boy_sub(n: int) -> dict:
    return {
        "id": f"errand-boy-{n}",
        "text": "The Corp gains 1[credit] or draws 1 card.",
        "effect": {
            "op": "choose",
            "chooser": "corp",
            "options": [
                {
                    "id": f"errand-gain-{n}",
                    "label": "Gain 1¢",
                    "effect": gain("corp", 1),
                },
                {
                    "id": f"errand-draw-{n}",
                    "label": "Draw 1 card",
                    "effect": draw("corp", 1),
                },
            ],
        },
    }


def map_card(c: dict) -> dict | None:
    cid = slugify(c["title"])
    if cid in REPRINTS:
        return None

    if cid == "helium-3-deposit":
        return base(
            c,
            onScore=do("helium3_place_up_to_2_power"),
        )

    if cid == "errand-boy":
        return base(
            c,
            subtypes=["sentry"],
            subroutines=[errand_boy_sub(1), errand_boy_sub(2), errand_boy_sub(3)],
        )

    if cid == "it-department":
        return base(
            c,
            paidAbilities=[
                {
                    "id": "it-department-place",
                    "label": "[click]: Place 1 power counter on IT Department",
                    "clickCost": 1,
                    "creditCost": 0,
                    "cost": {"clicks": 1},
                    "windows": ["corp_action_paw"],
                    "effect": do("add_power_counter", amount=1),
                },
                {
                    "id": "it-department-boost",
                    "label": "Hosted power counter: Choose rezzed ice; +1 strength per power (incl. spent) until end of turn",
                    "clickCost": 0,
                    "creditCost": 0,
                    "cost": {"powerCounters": 1},
                    "windows": ["corp_action_paw", "approach_paw", "encounter_paw"],
                    "effect": do("it_department_boost_ice"),
                },
            ],
        )

    if cid == "markus-1-0":
        return base(
            c,
            subtypes=["barrier", "bioroid"],
            paidAbilities=[
                {
                    "id": "markus-break",
                    "label": "Lose [click]: Break 1 subroutine on Markus 1.0",
                    "clickCost": 1,
                    "creditCost": 0,
                    "cost": {"clicks": 1},
                    "windows": ["encounter_paw"],
                    "usableByRunnerOnSelfIce": True,
                    "effect": do("break_subroutine_on_self", amount=1),
                }
            ],
            subroutines=[
                {
                    "id": "markus-trash",
                    "text": "The Runner trashes 1 of their installed cards.",
                    "effect": do("runner_trashes_one_installed"),
                },
                {
                    "id": "markus-etr",
                    "text": "End the run.",
                    "effect": etr(),
                },
            ],
        )

    if cid == "industrial-genomics-growing-solutions":
        return base(
            c,
            subtypes=["division"],
            trashCostIncreasePerFacedownArchivesCard=1,
        )

    if cid == "turtlebacks":
        return base(
            c,
            subtypes=["clone"],
            gainCreditsOnCreateServer=1,
        )

    if cid == "shoot-the-moon":
        return base(
            c,
            subtypes=["double"],
            playAdditionalClick=True,
            onPlay=do("shoot_the_moon_rez_ice_per_tag"),
        )

    if cid == "troll":
        return base(
            c,
            subtypes=["sentry"],
            onEncounter=do("troll_encounter_trace"),
        )

    if cid == "virgo":
        return base(
            c,
            subtypes=["sentry", "tracer"],
            subroutines=[
                {
                    "id": "virgo-trace",
                    "text": "Trace[2]. If successful, give the Runner 1 tag. If strength ≥5, give the Runner 1 tag.",
                    "effect": do("virgo_trace_subroutine"),
                }
            ],
        )

    if cid == "utopia-fragment":
        return base(
            c,
            subtypes=["source"],
            deckLimitOne=True,
            whileScoredStealAdditionalCreditsPerAdvancement=2,
        )

    if cid == "excalibur":
        return base(
            c,
            subtypes=["mythic", "grail"],
            subroutines=[
                {
                    "id": "excalibur-no-run",
                    "text": "The Runner cannot make another run this turn.",
                    "effect": do("forbid_runner_runs_this_turn"),
                }
            ],
        )

    if cid == "self-destruct":
        return base(
            c,
            remoteOnly=True,
            paidAbilities=[
                {
                    "id": "self-destruct-fire",
                    "label": "[trash]: Trash all cards in/protecting this server; Trace[X] for 3 net damage",
                    "clickCost": 0,
                    "creditCost": 0,
                    "cost": {"trashSelf": True},
                    "windows": ["approach_paw", "encounter_paw", "approach_server_paw"],
                    "effect": do("self_destruct_ability"),
                }
            ],
        )

    if cid == "incubator":
        return base(
            c,
            subtypes=["virus"],
            onTurnBegin=do("add_virus_counter", amount=1),
            paidAbilities=[
                {
                    "id": "incubator-move",
                    "label": "[click], [trash]: Move all virus counters to another installed virus program",
                    "clickCost": 1,
                    "creditCost": 0,
                    "cost": {"clicks": 1, "trashSelf": True},
                    "windows": ["runner_action_paw"],
                    "effect": do("incubator_move_virus_counters"),
                }
            ],
        )

    if cid == "ixodidae":
        return base(
            c,
            subtypes=["virus"],
            trashOnVirusPurge=True,
            gainCreditsWhenCorpLosesCredits=1,
        )

    if cid == "code-siphon":
        return base(
            c,
            subtypes=["run"],
            runEvent={
                "servers": "rd",
                "onSuccessfulRun": do("code_siphon_may_instead_of_breach"),
            },
        )

    if cid == "collective-consciousness":
        return base(
            c,
            drawWhenCorpRezzesIce=1,
        )

    if cid == "sage":
        card = breaker_card(c, "code gate", 0, 2, 0, 0)
        # Dual decoder/fracter via paid ability only; strength from unused MU.
        card["breaker"]["breakViaPaidAbilityOnly"] = True
        card["breaker"]["pumpCredits"] = 0
        card["breaker"]["pumpStrength"] = 0
        # Remove auto pump since pump cost is 0/0 and unused.
        del card["breaker"]["pumpCredits"]
        del card["breaker"]["pumpStrength"]
        card["strengthBonusPerUnusedMu"] = 1
        card["paidAbilities"] = [
            {
                "id": "sage-break",
                "label": "2¢: Break 1 code gate or 1 barrier subroutine",
                "clickCost": 0,
                "creditCost": 2,
                "cost": {"credits": 2},
                "windows": ["encounter_paw"],
                "effect": do("sage_break_code_gate_or_barrier"),
            }
        ]
        return card

    if cid == "bribery":
        # X play cost: Runner chooses X when playing; first approached ice +X rez.
        return base(
            c,
            subtypes=["run"],
            playCost=0,
            briberyPlayCostX=True,
            runEvent={
                "servers": "any",
                "briberyFirstIceAdditionalRezEqualsX": True,
            },
        )

    if cid == "au-revoir":
        return base(
            c,
            gainCreditsOnJackOut=1,
        )

    card = base(c)
    card["unsupported"] = [f"Unmapped ts card: {cid}"]
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
