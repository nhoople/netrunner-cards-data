#!/usr/bin/env python3
"""Generate Upstalk (up) card JSON from pinned pack `up`.

Fetch: python3 scripts/nsg_catalog.py fetch up
Lunar cycle after Honor and Profit (floor v1.101.0 → v1.102.0).
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
    etr,
    gain,
    net,
    seq,
    slugify,
    trace_sub,
    write_manifest,
)

OUT = Path(__file__).resolve().parents[1] / "data" / "upstalk"
WAVE = "upstalk"
PACK = "up"
EXPECTED = 20

REPRINTS = {
    "lotus-field",
    "near-earth-hub-broadcast-center",
    "lamprey",
}


def map_card(c: dict) -> dict | None:
    cid = slugify(c["title"])
    if cid in REPRINTS:
        return None

    if cid == "domestic-sleepers":
        return base(
            c,
            agendaPoints=0,
            agendaPointsPerAgendaCounter=1,
            paidAbilities=[
                {
                    "id": "domestic-sleepers-counter",
                    "label": "[click][click][click]: Place 1 agenda counter on Domestic Sleepers",
                    "clickCost": 3,
                    "creditCost": 0,
                    "cost": {"clicks": 3},
                    "windows": ["corp_action_paw"],
                    "effect": do("add_agenda_counter", amount=1),
                }
            ],
        )

    if cid == "next-silver":
        return base(
            c,
            dynamicEtrSubroutineCountFromRezzedIceSubtype="next",
            subroutines=[],
        )

    if cid == "mutate":
        return base(
            c,
            playAdditionalCost=do("mutate_trash_rezzed_ice_additional_cost"),
            onPlay=do("mutate_operation_resolve"),
        )

    if cid == "primary-transmission-dish":
        return base(
            c,
            recurringCreditsMax=3,
            recurringSpendFor=["trace"],
        )

    if cid == "midway-station-grid":
        return base(
            c,
            runnerIcebreakerAbilityAdditionalCostOnThisServer=1,
        )

    if cid == "the-root":
        return base(
            c,
            recurringCreditsMax=3,
            recurringSpendFor=[
                "advance_ice",
                "install_hardware",
                "install_program",
                "rez_ice",
            ],
        )

    if cid == "taurus":
        return base(
            c,
            subroutines=[
                {
                    "id": "taurus-trace",
                    "text": "Trace[2]. If successful, trash 1 hardware; if strength ≥5 trash another.",
                    "effect": do("taurus_trace_subroutine"),
                }
            ],
        )

    if cid == "mother-goddess":
        return base(
            c,
            hostGainsAllIceSubtypes=True,
            subroutines=[
                {"id": "mother-goddess-etr", "text": "End the run.", "effect": etr()}
            ],
        )

    if cid == "galahad":
        return base(
            c,
            onEncounter=do("grail_reveal_gain_subroutines", maxReveal=2),
            subroutines=[
                {"id": "galahad-etr", "text": "End the run.", "effect": etr()}
            ],
        )

    if cid == "bad-times":
        return base(
            c,
            playRequiresTagged=True,
            onPlay=do("runner_mu_modifier_until_turn_end", delta=-2),
        )

    if cid == "cyber-threat":
        return base(
            c,
            playRequiresFirstClick=True,
            onPlay=do("cyber_threat"),
        )

    if cid == "paper-tripping":
        return base(
            c,
            playRequiresFirstClick=True,
            onPlay=do("remove_all_tags"),
        )

    if cid == "power-tap":
        return base(c, gainCreditsOnTraceInitiated=1)

    if cid == "nasir-meidan-cyber-explorer":
        return base(
            c,
            onEncounterRezzedAfterApproach=do("nasir_lose_all_credits"),
        )

    if cid == "social-engineering":
        return base(
            c,
            playRequiresFirstClick=True,
            onPlay=do("social_engineering"),
        )

    if cid == "leprechaun":
        return base(c, daemonHost=True, daemonHostMaxMu=2)

    if cid == "eden-shard":
        return base(c, onGripRdSuccessInstallSelfIgnoringCosts=True)

    card = base(c)
    card["unsupported"] = [f"Unmapped up card: {cid}"]
    return card


def main():
    pack = sorted(load_pack_cards(PACK), key=lambda c: c.get("position", 0))
    assert len(pack) == EXPECTED, len(pack)
    OUT.mkdir(parents=True, exist_ok=True)
    written: list[str] = []
    skipped: list[str] = []
    for c in pack:
        cid = slugify(c["title"])
        mapped = map_card(c)
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
