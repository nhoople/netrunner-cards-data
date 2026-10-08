#!/usr/bin/env python3
"""Generate True Colors (tc) card JSON from pinned pack `tc`.

Fetch: python3 scripts/nsg_catalog.py fetch tc
Spin cycle after Mala Tempora (floor v1.97.0 → v1.98.0).
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
    draw,
    etr,
    gain,
    net,
    seq,
    slugify,
    trace_sub,
    write_manifest,
)

OUT = Path(__file__).resolve().parents[1] / "data" / "true-colors"
WAVE = "true-colors"
PACK = "tc"
EXPECTED = 20

REPRINTS = {
    "tsurugi",
    "punitive-counterstrike",
}


def map_card(c: dict) -> dict | None:
    cid = slugify(c["title"])
    if cid in REPRINTS:
        return None

    if cid == "keyhole":
        return base(
            c,
            paidAbilities=[
                {
                    "id": "keyhole-run",
                    "label": "[click]: Run R&D; on success may look at top 3 and trash 1 program",
                    "clickCost": 1,
                    "creditCost": 0,
                    "cost": {"clicks": 1},
                    "windows": ["runner_action_paw"],
                    "effect": do("gain_credits", side="runner", amount=0),
                    "startsRun": {
                        "servers": "rd",
                        "onSuccessfulRun": do("keyhole_may_instead_of_breach"),
                    },
                }
            ],
        )

    if cid == "activist-support":
        return base(
            c,
            onCorpTurnBeginIfRunnerUntagged=do("give_tags", amount=1),
            onTurnBeginIfCorpNoBadPublicity=do("give_bad_publicity", amount=1),
        )

    if cid == "lawyer-up":
        return base(
            c,
            playAdditionalClick=True,
            onPlay=do("lawyer_up"),
        )

    if cid == "leverage":
        return base(
            c,
            playRequiresSuccessfulHqRunThisTurn=True,
            onPlay=do("leverage"),
        )

    if cid == "garrote":
        return breaker_card(c, "sentry", 0, 1, 1, 1)

    if cid == "llds-processor":
        return base(c, nonAiIcebreakerInstallStrengthBonusThisTurn=1)

    if cid == "sharpshooter":
        card = breaker_card(c, "destroyer", 0, 0, 1, 2)
        card["paidAbilities"] = [
            {
                "id": "sharpshooter-trash-break",
                "label": "[trash]: Break any number of destroyer subroutines",
                "clickCost": 0,
                "creditCost": 0,
                "cost": {"trashSelf": True},
                "windows": ["encounter_paw"],
                "oncePerTurn": True,
                "effect": do("break_all_destroyer_subroutines_on_encounter"),
            }
        ]
        return card

    if cid == "capstone":
        return base(
            c,
            paidAbilities=[
                {
                    "id": "capstone-trash-grip",
                    "label": "[click]: Trash grip copies; draw for installed dupes",
                    "clickCost": 1,
                    "creditCost": 0,
                    "cost": {"clicks": 1},
                    "windows": ["runner_action_paw"],
                    "effect": do("trash_grip_draw_for_installed_dupes"),
                }
            ],
        )

    if cid == "starlight-crusade-funding":
        return base(
            c,
            onTurnBegin=seq(
                do("lose_clicks", side="runner", amount=1),
            ),
            ignoreAdditionalCostFirstDoubleEventEachTurn=True,
        )

    if cid == "rex-campaign":
        return base(
            c,
            powerCountersOnRez=3,
            trashWhenPowerCountersEmpty=True,
            onTurnBegin=do("turn_begin"),
            onPowerCountersEmpty=do("rex_campaign_when_empty"),
        )

    if cid == "fenris":
        return base(
            c,
            onRez=do("give_bad_publicity", amount=1),
            subroutines=[
                {"id": "fenris-core", "text": "Do 1 core damage.", "effect": core(1)},
                {"id": "fenris-etr", "text": "End the run.", "effect": etr()},
            ],
        )

    if cid == "panic-button":
        return base(
            c,
            installServers=["hq"],
            paidAbilities=[
                {
                    "id": "panic-draw",
                    "label": "1[credit]: Draw 1 during a run on HQ",
                    "clickCost": 0,
                    "creditCost": 1,
                    "cost": {"credits": 1},
                    "windows": ["runner_action_paw"],
                    "onlyDuringHqRun": True,
                    "effect": draw("runner", 1),
                }
            ],
        )

    if cid == "shock":
        return base(
            c,
            mustRevealWhenAccessedFromRd=True,
            onAccess=net(1),
        )

    if cid == "tgtbt":
        return base(
            c,
            mustRevealWhenAccessedFromRd=True,
            onAccess=do("give_tags", amount=1),
        )

    if cid == "sweeps-week":
        return base(c, onPlay=do(
                "gain_credits",
                side="runner",
                amount=0,
                tally={"count": "runner_grip", "per": 1, "side": "runner"},
            ))

    if cid == "rsvp":
        return base(
            c,
            subroutines=[
                {
                    "id": "rsvp-no-spend",
                    "text": "Runner cannot spend credits for remainder of run.",
                    "effect": do("forbid_runner_spend_credits_for_run"),
                }
            ],
        )

    if cid == "curtain-wall":
        return base(
            c,
            strengthBonusIfOutermostOnServer=4,
            subroutines=[
                {"id": "cw-etr-1", "text": "End the run.", "effect": etr()},
                {"id": "cw-etr-2", "text": "End the run.", "effect": etr()},
                {"id": "cw-etr-3", "text": "End the run.", "effect": etr()},
            ],
        )

    if cid == "veterans-program":
        return base(
            c,
            onScore=do("remove_bad_publicity_up_to", max=2),
        )

    card = base(c)
    card["unsupported"] = [f"Unmapped tc card: {cid}"]
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
