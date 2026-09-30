#!/usr/bin/env python3
"""Generate Democracy and Dogma (dag) card JSON from pinned pack `dag`.

Fetch: python3 scripts/nrdb_catalog.py fetch dag
Mumbad cycle after Business First (floor v1.117.0 → v1.118.0).
No reprints (19/19 new).
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
    write_manifest,
)

OUT = Path(__file__).resolve().parents[1] / "data" / "democracy-and-dogma"
WAVE = "democracy-and-dogma"
PACK = "dag"
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


def iff(cond: dict, then: dict, else_: dict | None = None) -> dict:
    out: dict = {"op": "if", "cond": cond, "then": then}
    if else_ is not None:
        out["else"] = else_
    return out


def unprotected(then: dict) -> dict:
    return iff({"op": "host_server_unprotected_by_ice"}, then)


def paid(
    id_: str,
    label: str,
    effect: dict,
    *,
    clicks: int = 0,
    credits: int = 0,
    power_counters: int = 0,
    agenda_counters: int = 0,
    windows: list[str] | None = None,
    cost: dict | None = None,
    once_per_turn: bool = False,
    trash_self: bool = False,
    usable_by_runner: bool = False,
    require_during_run: bool = False,
    forbid_during_run: bool = False,
) -> dict:
    c = dict(cost or {})
    if clicks:
        c["clicks"] = clicks
    if credits:
        c["credits"] = credits
    if power_counters:
        c["powerCounters"] = power_counters
    if agenda_counters:
        c["agendaCounters"] = agenda_counters
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
    if forbid_during_run:
        ab["forbidDuringRun"] = True
    return ab


def map_card(c: dict) -> dict | None:
    cid = slugify(c["title"])
    if cid in REPRINTS:
        return None

    if cid == "political-graffiti":
        return base(
            c,
            subtypes=["run"],
            hostAgendaPointsModifier=-1,
            trashOnVirusPurge=True,
            runEvent={
                "servers": "archives",
                "onSuccessfulRun": do("political_graffiti_host_on_scored_agenda"),
            },
        )

    if cid == "nero-severn-information-broker":
        return base(
            c,
            subtypes=["natural"],
            link=c.get("base_link", 1),
            mayJackOutOnEncounterSentryOncePerTurn=True,
        )

    if cid == "reflection":
        return base(
            c,
            subtypes=["console"],
            muBonus=1,
            link=1,
            maxConsole=1,
            revealRandomHqOnJackOut=True,
        )

    if cid == "spy-camera":
        return base(
            c,
            subtypes=["consumer-grade"],
            deckLimit=6,
            paidAbilities=[
                paid(
                    "spy-camera-arrange",
                    "[click]: Look at the top X cards of your stack and arrange them (X = installed Spy Camera copies)",
                    do("spy_camera_look_top_x_stack_arrange"),
                    clicks=1,
                    windows=["runner_action_paw"],
                    usable_by_runner=True,
                ),
                paid(
                    "spy-camera-rd",
                    "[trash]: Look at the top card of R&D",
                    do("look_top_1_rd"),
                    trash_self=True,
                    windows=["runner_action_paw"],
                    usable_by_runner=True,
                ),
            ],
        )

    if cid == "political-operative":
        return base(
            c,
            subtypes=["connection"],
            installRequiresSuccessfulHqRunThisTurn=True,
            paidAbilities=[
                paid(
                    "political-operative-trash",
                    "[trash], X¢: Trash 1 rezzed card with trash cost equal to X",
                    do("political_operative_trash_rezzed_paying_trash_cost"),
                    trash_self=True,
                    windows=["runner_action_paw"],
                    usable_by_runner=True,
                )
            ],
        )

    if cid == "sadyojata":
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
                "breakRequiresIceSubtypeCountGte": 3,
            },
            paidAbilities=[
                paid(
                    "sadyojata-swap",
                    "2¢: Swap this program with a deva program from your grip",
                    do("swap_with_grip_subtype", subtype="deva"),
                    credits=2,
                    windows=["runner_action_paw", "encounter_paw"],
                    usable_by_runner=True,
                )
            ],
        )

    if cid == "freedom-through-equality":
        return base(
            c,
            subtypes=["current"],
            lingerAsCurrent=True,
            currentTrashOnAgendaScored=True,
            onStealAgenda=do("add_to_runner_score_as_agenda", agendaPoints=1),
        )

    if cid == "akshara-sareen":
        return base(
            c,
            subtypes=["connection"],
            allottedClicksBonus=1,
            corpAllottedClicksBonusWhileInstalled=1,
        )

    if cid == "councilman":
        return base(
            c,
            subtypes=["connection"],
            onCorpRezAssetOrUpgradeMayPayRezCostTrashSelfDerez=True,
        )

    if cid == "voting-machine-initiative":
        return base(
            c,
            subtypes=["initiative"],
            onScore=do("add_agenda_counter", amount=3),
            onRunnerTurnBegin=may(
                do("spend_agenda_counter_runner_lose_click"),
                label="Spend 1 agenda counter: Runner loses [click], if able",
                decline_side="corp",
            ),
        )

    if cid == "clone-suffrage-movement":
        return base(
            c,
            subtypes=["political"],
            onTurnBegin=unprotected(
                may(
                    do("may_add_operation_from_archives_to_hq"),
                    label="Add 1 operation from Archives to HQ",
                    decline_side="corp",
                )
            ),
        )

    if cid == "bio-ethics-association":
        return base(
            c,
            subtypes=["political"],
            onTurnBegin=unprotected(net(1)),
        )

    if cid == "political-dealings":
        return base(
            c,
            subtypes=["seedy"],
            onDrawAgendaMayRevealAndInstall=True,
        )

    if cid == "clones-are-not-people":
        return base(
            c,
            subtypes=["current"],
            lingerAsCurrent=True,
            currentTrashOnAgendaStolen=True,
            onAgendaScored=do("add_to_corp_score_as_agenda", agendaPoints=1),
        )

    if cid == "sensie-actors-union":
        return base(
            c,
            subtypes=["political"],
            onTurnBegin=unprotected(
                may(
                    seq(
                        draw("corp", 3),
                        do("sensie_add_one_hq_to_bottom_rd"),
                    ),
                    label="Draw 3 cards, then add 1 card from HQ to bottom of R&D",
                    decline_side="corp",
                )
            ),
        )

    if cid == "commercial-bankers-group":
        return base(
            c,
            subtypes=["political"],
            onTurnBegin=unprotected(gain("corp", 3)),
        )

    if cid == "mumbad-city-hall":
        return base(
            c,
            subtypes=["facility", "government"],
            paidAbilities=[
                paid(
                    "mumbad-city-hall-alliance",
                    "[click]: Search R&D for an alliance card, reveal it, and play or install it (paying all costs). Shuffle R&D",
                    do("mumbad_city_hall_search_alliance_play_or_install"),
                    clicks=1,
                    windows=["corp_action_paw"],
                )
            ],
        )

    if cid == "bailiff":
        return base(
            c,
            subtypes=["barrier"],
            gainCreditWheneverRunnerBreaksSubroutine=True,
            subroutines=[
                {
                    "id": "bailiff-etr",
                    "text": "End the run.",
                    "effect": etr(),
                }
            ],
        )

    if cid == "surat-city-grid":
        return base(
            c,
            subtypes=["region"],
            limitOnePerServer=True,
            onRezOtherCardInRootOrProtectingMayRezDiscount=2,
        )

    card = base(c)
    card["unsupported"] = [f"Unmapped dag card: {cid}"]
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
