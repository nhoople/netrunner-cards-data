#!/usr/bin/env python3
"""Generate Salsette Island (si) card JSON from pinned pack `si`.

Fetch: python3 scripts/nsg_catalog.py fetch si
Mumbad cycle after Democracy and Dogma (floor v1.118.0 → v1.119.0).
No reprints (19/19 new).
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
    gain,
    net,
    seq,
    slugify,
    write_manifest,
)

OUT = Path(__file__).resolve().parents[1] / "data" / "salsette-island"
WAVE = "salsette-island"
PACK = "si"
EXPECTED = 19

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
    return ab


def lose(side: str, n: int) -> dict:
    return do("lose_credits", side=side, amount=n)


def map_card(c: dict) -> dict | None:
    cid = slugify(c["title"])
    if cid in REPRINTS:
        return None

    if cid == "making-an-entrance":
        return base(
            c,
            subtypes=["priority"],
            playRequiresFirstClick=True,
            onPlay=do("look_top_n_stack_trash_any_arrange_rest", n=6),
        )

    if cid == "salsette-slums":
        return base(
            c,
            subtypes=["location", "seedy"],
            accessPayTrashCostRemoveFromGameOncePerTurn=True,
        )

    if cid == "exclusive-party":
        return base(
            c,
            deckLimit=6,
            onPlay=seq(
                draw("runner", 1),
                do(
                    "gain_credits",
                    side="runner",
                    amount=0,
                    tally={
                        "count": "copies_in_runner_heap",
                        "per": 1,
                        "side": "runner",
                    },
                ),
            ),
        )

    if cid == "vamadeva":
        return base(
            c,
            subtypes=["icebreaker", "ai", "deva"],
            memoryCost=1,
            breaker={
                "breaksSubtype": "*",
                "strength": 2,
                "breakCredits": 1,
                "breakMaxSubs": 1,
                "pumpCredits": 1,
                "pumpStrength": 1,
                "breakRequiresIceExactSubroutineCount": 1,
            },
            paidAbilities=[
                paid(
                    "vamadeva-swap",
                    "2¢: Swap this program with a deva program from your grip",
                    do("swap_with_grip_subtype", subtype="deva"),
                    credits=2,
                    windows=["runner_action_paw", "encounter_paw"],
                    usable_by_runner=True,
                )
            ],
        )

    if cid == "brahman":
        return base(
            c,
            subtypes=["icebreaker", "ai"],
            memoryCost=2,
            breaker={
                "breaksSubtype": "*",
                "strength": 3,
                "breakCredits": 1,
                "breakMaxSubs": 2,
                "pumpCredits": 2,
                "pumpStrength": 1,
            },
            addInstalledNonVirusProgramToStackTopOnEncounterEndIfBroke=True,
        )

    if cid == "patron":
        return base(
            c,
            subtypes=["connection"],
            patronChooseServerDrawInsteadOfBreach=2,
        )

    if cid == "sports-hopper":
        return base(
            c,
            subtypes=["vehicle"],
            link=1,
            paidAbilities=[
                paid(
                    "sports-hopper-draw",
                    "[trash]: Draw 3 cards",
                    draw("runner", 3),
                    trash_self=True,
                    windows=["runner_action_paw"],
                    usable_by_runner=True,
                )
            ],
        )

    if cid == "bazaar":
        return base(
            c,
            subtypes=["location", "ritzy"],
            onInstallHardwareFromGripMayInstallAnotherCopy=True,
        )

    if cid == "personality-profiles":
        return base(
            c,
            subtypes=["security"],
            onRunnerSearchStackOrInstallFromHeapTrashRandomFromGrip=True,
        )

    if cid == "jeeves-model-bioroids":
        return base(
            c,
            subtypes=["alliance"],
            zeroInfluenceIfNonAllianceFactionCardsGte={
                "faction": "haas-bioroid",
                "threshold": 6,
            },
            gainClickFirstTimeSpendClicksGteOnSameActionEachTurn=3,
        )

    if cid == "raman-rai":
        return base(
            c,
            subtypes=["alliance", "executive"],
            zeroInfluenceIfNonAllianceFactionCardsGte={
                "faction": "jinteki",
                "threshold": 6,
            },
            onDrawMayLoseClickRevealSwapArchivesSameTypeOncePerTurn=True,
        )

    if cid == "upayoga":
        return base(
            c,
            subtypes=["code gate", "psi"],
            subroutines=[
                {
                    "id": "upayoga-psi",
                    "text": "Psi game. If bids differ, the Runner loses 2¢.",
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "play_psi_game",
                            "maxBid": 2,
                            "ifBidsDiffer": lose("runner", 2),
                        },
                    },
                },
                {
                    "id": "upayoga-resolve-psi",
                    "text": "Resolve a subroutine on a piece of rezzed psi ice.",
                    "effect": do(
                        "may_resolve_subroutine_on_rezzed_ice",
                        subtype="psi",
                    ),
                },
            ],
        )

    if cid == "aryabhata-tech":
        return base(
            c,
            subtypes=["ritzy"],
            onAnySuccessfulTraceGainAndRunnerLose={"gain": 1, "lose": 1},
        )

    if cid == "salems-hospitality":
        return base(
            c,
            subtypes=["alliance", "gray ops"],
            zeroInfluenceIfNonAllianceFactionCardsGte={
                "faction": "nbn",
                "threshold": 6,
            },
            onPlay=do("salems_hospitality_name_reveal_trash_grip_copies"),
        )

    if cid == "executive-search-firm":
        return base(
            c,
            subtypes=["alliance", "ritzy"],
            zeroInfluenceIfNonAllianceFactionCardsGte={
                "faction": "weyland-consortium",
                "threshold": 6,
            },
            paidAbilities=[
                paid(
                    "executive-search-firm-search",
                    "[click]: Search R&D for an executive, sysop, or character, reveal it, and add it to HQ. Shuffle R&D",
                    do(
                        "search_rd_for_any_subtype_to_hq",
                        subtypes=["executive", "sysop", "character"],
                    ),
                    clicks=1,
                    windows=["corp_action_paw"],
                )
            ],
        )

    if cid == "indian-union-stock-exchange":
        return base(
            c,
            onRezOrPlayOutOfFactionGainCredits=1,
        )

    if cid == "cobra":
        return base(
            c,
            subtypes=["sentry", "destroyer", "ap"],
            subroutines=[
                {
                    "id": "cobra-trash-program",
                    "text": "Trash 1 program.",
                    "effect": do("trash_program", pick="choose"),
                },
                {
                    "id": "cobra-net",
                    "text": "Do 2 net damage.",
                    "effect": net(2),
                },
            ],
        )

    if cid == "localized-product-line":
        return base(
            c,
            onPlay=do("localized_product_line_search_rd_copies_to_hq"),
        )

    if cid == "mumbad-virtual-tour":
        return base(
            c,
            subtypes=["alliance"],
            zeroInfluenceIfAssetsInDeckGte=7,
            mustTrashWhenAccessedWhileInstalled=True,
        )

    card = base(c)
    card["unsupported"] = [f"Unmapped si card: {cid}"]
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
    if len(clear_written) != EXPECTED - len(REPRINTS):
        missing = [cid for cid in written if cid not in clear_written]
        print("UNCLEARED=" + json.dumps(missing))
        sys.exit(1)


if __name__ == "__main__":
    main()
