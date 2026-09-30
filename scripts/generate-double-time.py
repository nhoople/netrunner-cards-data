#!/usr/bin/env python3
"""Generate Double Time (dt) card JSON from pinned pack `dt`.

Fetch: python3 scripts/nrdb_catalog.py fetch dt
Spin cycle after Fear and Loathing (floor v1.99.0 → v1.100.0).
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
    trace_sub,
    write_manifest,
)

OUT = Path(__file__).resolve().parents[1] / "data" / "double-time"
WAVE = "double-time"
PACK = "dt"
EXPECTED = 20

REPRINTS = {"queens-gambit"}


def map_card(c: dict) -> dict | None:
    cid = slugify(c["title"])
    if cid in REPRINTS:
        return None

    if cid == "singularity":
        return base(
            c,
            playAdditionalClick=True,
            runEvent={
                "servers": "remote",
                "onSuccessfulRun": do("singularity_instead_of_breach_trash_root"),
            },
        )

    if cid == "dyson-fractal-generator":
        return base(
            c,
            recurringCreditsMax=1,
            recurringSpendFor=["use_fracter"],
        )

    if cid == "silencer":
        return base(
            c,
            recurringCreditsMax=1,
            recurringSpendFor=["use_killer"],
        )

    if cid == "savoir-faire":
        return base(
            c,
            oncePerTurnPaidAbilities=True,
            paidAbilities=[
                {
                    "id": "savoir-faire-install",
                    "label": "2[credit]: Install a program from grip paying install cost",
                    "clickCost": 0,
                    "creditCost": 2,
                    "cost": {"credits": 2},
                    "windows": ["runner_action_paw"],
                    "effect": do("savoir_faire_install_program_from_grip"),
                }
            ],
        )

    if cid == "fall-guy":
        return base(
            c,
            paidAbilities=[
                {
                    "id": "fall-guy-prevent",
                    "label": "[interrupt] [trash]: Prevent trash of another resource",
                    "clickCost": 0,
                    "creditCost": 0,
                    "cost": {"trashSelf": True},
                    "windows": ["trash_interrupt_paw"],
                    "effect": do("fall_guy_prevent_trash_resource"),
                },
                {
                    "id": "fall-guy-credits",
                    "label": "[trash]: Gain 2[credit]",
                    "clickCost": 0,
                    "creditCost": 0,
                    "cost": {"trashSelf": True},
                    "windows": ["runner_action_paw"],
                    "effect": gain("runner", 2),
                },
            ],
        )

    if cid == "power-nap":
        return base(
            c,
            playAdditionalClick=True,
            onPlay=do("power_nap_gain_per_double_in_heap"),
        )

    if cid == "paintbrush":
        return base(
            c,
            paidAbilities=[
                {
                    "id": "paintbrush-paint",
                    "label": "[click]: Choose rezzed ice; gain subtype until end of next run",
                    "clickCost": 1,
                    "creditCost": 0,
                    "cost": {"clicks": 1},
                    "windows": ["runner_action_paw"],
                    "effect": do("paintbrush_choose_ice_gain_subtype"),
                }
            ],
        )

    if cid == "lucky-find":
        return base(c, playAdditionalClick=True, onPlay=gain("runner", 9))

    if cid == "gyri-labyrinth":
        return base(
            c,
            subroutines=[
                {
                    "id": "gyri-hand",
                    "text": "Runner max hand size -2 until Corp next turn.",
                    "effect": do("gyri_labyrinth_reduce_max_hand"),
                }
            ],
        )

    if cid == "reclamation-order":
        return base(
            c,
            playAdditionalClick=True,
            onPlay=do("reclamation_order_archives_to_hq"),
        )

    if cid == "broadcast-square":
        return base(
            c,
            onWouldTakeBadPublicity=do("broadcast_square_trace_prevent_bad_publicity"),
        )

    if cid == "corporate-shuffle":
        return base(
            c,
            playAdditionalClick=True,
            onPlay=do("corporate_shuffle_hq_to_rd_draw", draw=5),
        )

    if cid == "caprice-nisei":
        return base(
            c,
            onPassAllIceProtectingServer=do("caprice_nisei_secret_spend"),
        )

    if cid == "shinobi":
        return base(
            c,
            onRez=do("give_bad_publicity", amount=1),
            subroutines=[
                {
                    "id": "shinobi-trace-1",
                    "text": "Trace 1 — If successful, do 1 net damage.",
                    "effect": trace_sub(1, net(1)),
                },
                {
                    "id": "shinobi-trace-2",
                    "text": "Trace 2 — If successful, do 2 net damage.",
                    "effect": trace_sub(2, net(2)),
                },
                {
                    "id": "shinobi-trace-3",
                    "text": "Trace 3 — If successful, do 3 net damage.",
                    "effect": trace_sub(3, net(3)),
                },
            ],
        )

    if cid == "marker":
        return base(
            c,
            subroutines=[
                {
                    "id": "marker-etr-next",
                    "text": "Next ice encountered gains ETR after its subroutines.",
                    "effect": do("marker_add_etr_to_next_ice"),
                }
            ],
        )

    if cid == "hive":
        return base(
            c,
            dynamicEtrSubroutineCountFromCorpAgendaPoints=True,
            subroutines=[
                {"id": "hive-etr-1", "text": "End the run.", "effect": etr()},
                {"id": "hive-etr-2", "text": "End the run.", "effect": etr()},
                {"id": "hive-etr-3", "text": "End the run.", "effect": etr()},
                {"id": "hive-etr-4", "text": "End the run.", "effect": etr()},
            ],
        )

    if cid == "witness-tampering":
        return base(
            c,
            playAdditionalClick=True,
            onPlay=do("remove_bad_publicity_up_to", max=2),
        )

    if cid == "napd-contract":
        return base(
            c,
            stealAdditionalCredits=4,
            advancementRequirementIncreasePerCorpBadPublicity=1,
        )

    if cid == "quandary":
        return base(
            c,
            subroutines=[{"id": "quandary-etr", "text": "End the run.", "effect": etr()}],
        )

    card = base(c)
    card["unsupported"] = [f"Unmapped dt card: {cid}"]
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
