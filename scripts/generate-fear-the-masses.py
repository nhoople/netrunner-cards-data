#!/usr/bin/env python3
"""Generate Fear the Masses (ftm) card JSON from pinned pack `ftm`.

Fetch: python3 scripts/nrdb_catalog.py fetch ftm
Mumbad cycle after The Liberated Mind (floor v1.120.0 → v1.121.0).
Reprint skip: magnet (18/19 new clears).
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

OUT = Path(__file__).resolve().parents[1] / "data" / "fear-the-masses"
WAVE = "fear-the-masses"
PACK = "ftm"
EXPECTED = 19

REPRINTS: set[str] = {"magnet"}


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


def map_card(c: dict) -> dict | None:
    cid = slugify(c["title"])
    if cid in REPRINTS:
        return None

    if cid == "fear-the-masses":
        return base(
            c,
            subtypes=["run", "sabotage"],
            deckLimit=6,
            runEvent={
                "servers": "hq",
                "skipBreach": True,
                "onSuccessfulRun": do("fear_the_masses_reveal_copies_trash_rd"),
            },
        )

    if cid == "aghora":
        return base(
            c,
            subtypes=["icebreaker", "ai", "deva"],
            memoryCost=1,
            unique=True,
            breaker={
                "breaksSubtype": "*",
                "strength": 2,
                "breakCredits": 1,
                "breakMaxSubs": 1,
                "pumpCredits": 1,
                "pumpStrength": 1,
                "breakRequiresIceRezCostGte": 5,
            },
            paidAbilities=[
                paid(
                    "aghora-swap",
                    "2¢: Swap this program with a deva program from your grip",
                    do("swap_with_grip_subtype", subtype="deva"),
                    credits=2,
                    windows=["runner_action_paw", "encounter_paw"],
                    usable_by_runner=True,
                )
            ],
        )

    if cid == "bhagat":
        return base(
            c,
            subtypes=["connection"],
            unique=True,
            onFirstSuccessfulHqRunThisTurn=do("trash_top_of_rd"),
        )

    if cid == "the-black-file":
        return base(
            c,
            subtypes=["virtual"],
            unique=True,
            deckLimit=1,
            corpCannotWinExceptFlatline=True,
            onTurnBegin=do("add_power_counter", amount=1),
            onPowerCountersGte={
                "amount": 3,
                "effect": do("rfg_self"),
            },
        )

    if cid == "the-price-of-freedom":
        return base(
            c,
            playAdditionalCost=do(
                "trash_own_resource_with_subtype", subtype="connection"
            ),
            onPlay=do("next_corp_turn_cannot_advance_cards"),
            rfgInsteadOfTrashing=True,
        )

    if cid == "ankusa":
        return base(
            c,
            subtypes=["icebreaker", "fracter"],
            memoryCost=1,
            breaker={
                "breaksSubtype": "barrier",
                "strength": 0,
                "breakCredits": 2,
                "breakMaxSubs": 1,
                "pumpCredits": 1,
                "pumpStrength": 1,
            },
            onFullyBreak=do("ankusa_add_fully_broken_barrier_to_hq"),
        )

    if cid == "rigged-results":
        return base(
            c,
            onPlay=do("rigged_results_secret_spend_guess"),
        )

    if cid == "lateral-growth":
        return base(
            c,
            subtypes=["transaction"],
            onPlay=seq(
                gain("corp", 4),
                do("may_install_from_hq_paying_costs"),
            ),
        )

    if cid == "improved-protein-source":
        return base(
            c,
            subtypes=["research"],
            onScore=gain("runner", 4),
            onSteal=gain("runner", 4),
        )

    if cid == "voter-intimidation":
        return base(
            c,
            subtypes=["gray ops", "psi"],
            playRequiresAgendaInRunnerScoreArea=True,
            onPlay={
                "op": "do",
                "action": {
                    "kind": "play_psi_game",
                    "maxBid": 2,
                    "ifBidsDiffer": do("trash_resource", pick="choose"),
                },
            },
        )

    if cid == "harishchandra-ent-where-youre-the-star":
        return base(
            c,
            subtypes=["division"],
            revealGripWhileRunnerTagged=True,
        )

    if cid == "full-immersion-recstudio":
        return base(
            c,
            subtypes=["facility"],
            maxHostedCards=2,
            hostAssetsOrAgendas=True,
            trashCostIncreasePerHostedCard=3,
        )

    if cid == "ibrahim-salem":
        return base(
            c,
            subtypes=["alliance", "character"],
            unique=True,
            zeroInfluenceIfNonAllianceFactionCardsGte={
                "faction": "nbn",
                "threshold": 6,
            },
            rezAdditionalCostForfeitAgenda=True,
            onTurnBegin=do("ibrahim_salem_name_type_trash_from_grip"),
        )

    if cid == "navi-mumbai-city-grid":
        return base(
            c,
            subtypes=["region"],
            limitOnePerServer=True,
            blockRunnerPaidAbilitiesExceptIcebreakersAndMidAccess=True,
        )

    if cid == "zealous-judge":
        return base(
            c,
            subtypes=["character"],
            rezRequiresTagged=True,
            paidAbilities=[
                paid(
                    "zealous-judge-tag",
                    "[click], 1¢: Give the Runner 1 tag",
                    do("give_tags", amount=1),
                    clicks=1,
                    credits=1,
                    windows=["corp_action_paw"],
                )
            ],
        )

    if cid == "election-day":
        return base(
            c,
            onPlay=do("election_day_trash_hq_draw", amount=5),
        )

    if cid == "subcontract":
        return base(
            c,
            subtypes=["gray ops"],
            playRequiresTagged=True,
            onPlay=do("subcontract_play_ops_from_hq", max=2),
        )

    if cid == "merger":
        return base(
            c,
            subtypes=["expansion"],
            agendaPointsModifierInRunnerScoreArea=1,
        )

    card = base(c)
    card["unsupported"] = [f"Unmapped ftm card: {cid}"]
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
