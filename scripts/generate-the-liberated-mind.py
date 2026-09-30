#!/usr/bin/env python3
"""Generate The Liberated Mind (tlm) card JSON from pinned pack `tlm`.

Fetch: python3 scripts/nrdb_catalog.py fetch tlm
Mumbad cycle after Salsette Island (floor v1.119.0 → v1.120.0).
Reprint skip: ravana-1-0 (18/19 new clears).
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
    etr,
    gain,
    net,
    seq,
    slugify,
    write_manifest,
)

OUT = Path(__file__).resolve().parents[1] / "data" / "the-liberated-mind"
WAVE = "the-liberated-mind"
PACK = "tlm"
EXPECTED = 19

REPRINTS: set[str] = {"ravana-1-0"}


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
    forfeit_agenda: bool = False,
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
    if forfeit_agenda:
        c["forfeitAgenda"] = True
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


def core(n: int) -> dict:
    return do("core_damage", amount=n)


def map_card(c: dict) -> dict | None:
    cid = slugify(c["title"])
    if cid in REPRINTS:
        return None

    if cid == "the-noble-path":
        return base(
            c,
            subtypes=["run"],
            onPlay=do("trash_all_cards_from_grip"),
            runEvent={
                "servers": "any",
                "preventAllDamageThisRun": True,
            },
        )

    if cid == "emptied-mind":
        return base(
            c,
            onTurnBegin=iff(
                {"op": "not", "cond": {"op": "grip_count_gte", "amount": 1}},
                do("gain_clicks", side="runner", amount=1),
            ),
        )

    if cid == "information-sifting":
        return base(
            c,
            subtypes=["run"],
            runEvent={
                "servers": "hq",
                "skipBreach": True,
                "onSuccessfulRun": do("information_sifting_corp_split_hq"),
            },
        )

    if cid == "out-of-the-ashes":
        return base(
            c,
            subtypes=["run"],
            deckLimit=6,
            runEvent={"servers": "any"},
            heapOnTurnBeginMayRfgSelfToMakeRun=True,
        )

    if cid == "liberated-chela":
        return base(
            c,
            subtypes=["connection"],
            paidAbilities=[
                paid(
                    "liberated-chela-forfeit",
                    "[click]×5, forfeit an agenda: Corp may forfeit to RFG this; if not, score as 2 AP agenda",
                    do("liberated_chela_corp_may_forfeit_or_score"),
                    clicks=5,
                    forfeit_agenda=True,
                    windows=["runner_action_paw"],
                    usable_by_runner=True,
                )
            ],
        )

    if cid == "temple-of-the-liberated-mind":
        return base(
            c,
            subtypes=["location", "ritzy"],
            paidAbilities=[
                paid(
                    "temple-place-power",
                    "[click]: Place 1 power counter on this resource",
                    do("add_power_counter", amount=1),
                    clicks=1,
                    windows=["runner_action_paw"],
                    usable_by_runner=True,
                ),
                paid(
                    "temple-spend-power",
                    "Hosted power counter: Gain [click]",
                    do("gain_clicks", side="runner", amount=1),
                    power_counters=1,
                    once_per_turn=True,
                    windows=["runner_action_paw"],
                    usable_by_runner=True,
                ),
            ],
        )

    if cid == "rebirth":
        return base(
            c,
            deckLimit=1,
            rfgInsteadOfTrashing=True,
            onPlay=do("rebirth_switch_identity_same_faction"),
        )

    if cid == "guru-davinder":
        return base(
            c,
            subtypes=["connection"],
            autoPreventNetOrMeatDamagePayOrTrash=4,
        )

    if cid == "the-turning-wheel":
        return base(
            c,
            subtypes=["virtual"],
            placePowerOnHqOrRdRunEndIfNoAgendaStolen=True,
            paidAbilities=[
                paid(
                    "turning-wheel-bonus-access",
                    "2 hosted power counters: Choose HQ or R&D; +1 access when breaching that server this run",
                    do("turning_wheel_choose_central_bonus_access"),
                    power_counters=2,
                    windows=["runner_action_paw", "approach_paw", "encounter_paw"],
                    usable_by_runner=True,
                )
            ],
        )

    if cid == "brainstorm":
        return base(
            c,
            subtypes=["sentry", "ap"],
            gainsSubroutinesOnEncounterEqualGripSize={
                "id": "brainstorm-core",
                "text": "Do 1 core damage.",
                "effect": core(1),
            },
        )

    if cid == "dedicated-neural-net":
        return base(
            c,
            subtypes=["initiative", "psi"],
            firstSuccessfulHqRunEachTurnPsiCorpChoosesAccess=True,
        )

    if cid == "chetana":
        return base(
            c,
            subtypes=["sentry", "ap", "psi"],
            subroutines=[
                {
                    "id": "chetana-gain",
                    "text": "Each player gains 2¢.",
                    "effect": seq(gain("corp", 2), gain("runner", 2)),
                },
                {
                    "id": "chetana-psi",
                    "text": "Psi game. If bids differ, do 1 net damage for each card in the Runner's grip.",
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "play_psi_game",
                            "maxBid": 2,
                            "ifBidsDiffer": do("net_damage_per_runner_grip_card"),
                        },
                    },
                },
            ],
        )

    if cid == "puppet-master":
        return base(
            c,
            subtypes=["initiative"],
            onSuccessfulRunMayPlaceAdvancementOnCanBeAdvanced=True,
        )

    if cid == "waiver":
        return base(
            c,
            subtypes=["code gate", "tracer"],
            subroutines=[
                {
                    "id": "waiver-trace",
                    "text": "Trace[5]. If successful, reveal grip; trash each card with play/install cost ≤ excess.",
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "trace",
                            "strength": 5,
                            "onSuccess": do(
                                "waiver_reveal_grip_trash_cost_lte_excess"
                            ),
                        },
                    },
                }
            ],
        )

    if cid == "exchange-of-information":
        return base(
            c,
            subtypes=["gray ops"],
            playRequiresTagged=True,
            onPlay=do("exchange_of_information_swap_scored_agendas"),
        )

    if cid == "red-tape":
        return base(
            c,
            subtypes=["code gate"],
            subroutines=[
                {
                    "id": "red-tape-fortify",
                    "text": "All ice has +3 strength for the remainder of this run.",
                    "effect": do("fortify_all_ice", amount=3),
                }
            ],
        )

    if cid == "consulting-visit":
        return base(
            c,
            subtypes=["alliance", "double"],
            playAdditionalClick=True,
            zeroInfluenceIfNonAllianceFactionCardsGte={
                "faction": "weyland-consortium",
                "threshold": 6,
            },
            onPlay=do("consulting_visit_search_rd_play_operation"),
        )

    if cid == "vanilla":
        return base(
            c,
            subtypes=["barrier"],
            subroutines=[
                {
                    "id": "vanilla-etr",
                    "text": "End the run.",
                    "effect": etr(),
                }
            ],
        )

    card = base(c)
    card["unsupported"] = [f"Unmapped tlm card: {cid}"]
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
