#!/usr/bin/env python3
"""Generate Fear and Loathing (fal) card JSON from pinned pack `fal`.

Fetch: python3 scripts/nsg_catalog.py fetch fal
Spin cycle after True Colors (floor v1.98.0 → v1.99.0).
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
    gain,
    seq,
    slugify,
    write_manifest,
)

OUT = Path(__file__).resolve().parents[1] / "data" / "fear-and-loathing"
WAVE = "fear-and-loathing"
PACK = "fal"
EXPECTED = 20

REPRINTS = {
    "quest-completed",
    "blue-level-clearance",
    "yagura",
    "wraparound",
    "subliminal-messaging",
}


def map_card(c: dict) -> dict | None:
    cid = slugify(c["title"])
    if cid in REPRINTS:
        return None

    if cid == "hemorrhage":
        return base(
            c,
            subtypes=["virus"],
            onSuccessfulRun=do("add_virus_counter", amount=1),
            paidAbilities=[
                {
                    "id": "hemorrhage-trash-hq",
                    "label": "[click], 2 virus counters: Corp trashes 1 card from HQ",
                    "clickCost": 1,
                    "creditCost": 0,
                    "cost": {"clicks": 1, "virusCounters": 2},
                    "windows": ["runner_action_paw"],
                    "effect": do("hemorrhage_corp_trash_from_hq"),
                }
            ],
        )

    if cid == "tallie-perrault":
        return base(
            c,
            subtypes=["resource"],
            onGrayOrBlackOpsTrashedAfterResolve=do("tallie_perrault_on_ops_trashed"),
            paidAbilities=[
                {
                    "id": "tallie-draw",
                    "label": "[trash]: Draw 1 if you have at least 1 tag",
                    "clickCost": 0,
                    "creditCost": 0,
                    "cost": {"trashSelf": True},
                    "windows": ["runner_action_paw"],
                    "effect": {
                        "op": "if",
                        "cond": {"op": "tags_gte", "amount": 1},
                        "then": draw("runner", 1),
                    },
                }
            ],
        )

    if cid == "executive-wiretaps":
        return base(
            c,
            playAdditionalClick=True,
            onPlay=do("reveal_hq_gain_credits", maxCards=99, creditsEach=0),
        )

    if cid == "blackguard":
        return base(
            c,
            subtypes=["console"],
            muBonus=2,
            maxConsole=1,
            blackguardForceRezOnExpose=True,
        )

    if cid == "cybersolutions-mem-chip":
        return base(c, muBonus=2)

    if cid == "alpha":
        card = breaker_card(c, "sentry", 0, 1, 1, 1)
        card["breakerOnlyOutermostIce"] = True
        return card

    if cid == "omega":
        card = breaker_card(c, "sentry", 0, 1, 1, 1)
        card["breakerOnlyInnermostIce"] = True
        return card

    if cid == "blackmail":
        return base(
            c,
            playRequiresCorpBadPublicityGte=1,
            runEvent={
                "servers": "any",
                "forbidCorpRezIceDuringRun": True,
            },
        )

    if cid == "strongbox":
        return base(
            c,
            subtypes=["persistent"],
            stealAdditionalClicks=1,
        )

    if cid == "toshiyuki-sakai":
        return base(
            c,
            subtypes=["sysop"],
            canAdvance=True,
            onAccess=do("toshiyuki_sakai_swap_with_hq"),
            onAccessRequiresInstalled=True,
        )

    if cid == "restoring-face":
        return base(
            c,
            onPlay=do("restoring_face_trash_exec_sysop_clone_remove_bp"),
        )

    if cid == "market-research":
        return base(
            c,
            onScoreIfRunnerTaggedPlaceAgendaCounter=True,
            agendaPointsPerAgendaCounter=1,
        )

    if cid == "grndl-power-unleashed":
        return base(
            c,
            onGameStart=seq(
                gain("corp", 10),
                do("give_bad_publicity", amount=1),
            ),
        )

    if cid == "vulcan-coverup":
        return base(
            c,
            onScore=do("meat_damage", amount=2),
            onSteal=do("give_bad_publicity", amount=1),
        )

    if cid == "grndl-refinery":
        return base(
            c,
            canAdvance=True,
            paidAbilities=[
                {
                    "id": "grndl-refinery-cash",
                    "label": "[click], [trash]: Gain 4[credit] per advancement token",
                    "clickCost": 1,
                    "creditCost": 0,
                    "cost": {"clicks": 1, "trashSelf": True},
                    "windows": ["corp_action_paw"],
                    "effect": do(
                        "gain_credits",
                        side="corp",
                        amount=0,
                        tally={
                            "count": "source_advancement_tokens",
                            "per": 4,
                            "side": "source",
                        },
                    ),
                }
            ],
        )

    card = base(c)
    card["unsupported"] = [f"Unmapped fal card: {cid}"]
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
