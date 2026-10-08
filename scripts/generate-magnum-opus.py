#!/usr/bin/env python3
"""Generate Magnum Opus (mo) card JSON from pinned pack `mo`.

Fetch: python3 scripts/nsg_catalog.py fetch mo
Set-complete at floor v1.142.0 (current host floor v1.142.2).
All 8 titles are unique (mor reprints absorbed — do not generate a mor wave).
Follow NSG pack stripped_text (not IR-hint paraphrases).
Slug via spin_common.slugify.
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
    seq,
    slugify,
    write_manifest,
)

OUT = Path(__file__).resolve().parents[1] / "data" / "magnum-opus"
WAVE = "magnum-opus"
PACK = "mo"
EXPECTED = 8

# Magnum Opus Reprint (`mor`) is entirely absorbed — same 6 playable titles.
REPRINTS: set[str] = set()


def choose(chooser: str, options: list[dict]) -> dict:
    return {"op": "choose", "chooser": chooser, "options": options}


def may(effect: dict, label: str = "Accept", decline_side: str = "corp") -> dict:
    return choose(
        decline_side if decline_side in ("corp", "runner") else "corp",
        [
            {"id": "accept", "label": label, "effect": effect},
            {
                "id": "decline",
                "label": "Decline",
                "effect": gain(
                    decline_side if decline_side in ("corp", "runner") else "corp",
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
    require_during_run: bool = False,
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
        "windows": windows or ["corp_action_paw"],
        "effect": effect,
    }
    if once_per_turn:
        ab["oncePerTurn"] = True
    if require_during_run:
        ab["requireDuringRun"] = True
    return ab


def map_card(c: dict) -> dict | None:
    cid = slugify(c["title"])
    if cid in REPRINTS:
        return None

    if cid == "labor-rights":
        return base(
            c,
            rfgInsteadOfTrashing=True,
            onPlay=seq(
                do("trash_top_of_stack"),
                do("trash_top_of_stack"),
                do("trash_top_of_stack"),
                do("shuffle_n_heap_cards_into_stack", amount=3),
                draw("runner", 1),
            ),
        )

    if cid == "crowdfunding":
        return base(
            c,
            subtypes=["seedy", "virtual"],
            hostedCreditsOnInstall=3,
            drawOnHostedEmpty=1,
            onTurnBegin=do("take_hosted_credits", amount=1),
            onRunnerTurnEnd=do(
                "mo_crowdfunding_may_install_from_heap_ignore_costs",
                minSuccessfulRuns=3,
            ),
        )

    if cid == "embolus":
        return base(
            c,
            unique=True,
            removePowerCounterOnAnySuccessfulRun=True,
            onTurnBegin=may(
                seq(
                    do("lose_credits", side="corp", amount=1),
                    do("add_power_counter", amount=1),
                ),
                label="Pay 1¢ to place 1 power counter",
                decline_side="corp",
            ),
            paidAbilities=[
                paid(
                    "embolus-etr",
                    "Hosted power counter: End the run (run on this server)",
                    etr(),
                    cost={"powerCounters": 1},
                    windows=[
                        "approach_paw",
                        "encounter_paw",
                        "approach_server_paw",
                    ],
                    require_during_run=True,
                ),
            ],
        )

    if cid == "timely-public-release":
        return base(
            c,
            subtypes=["initiative"],
            onScore=do("add_agenda_counter", amount=1),
            paidAbilities=[
                paid(
                    "timely-install-ice",
                    "Hosted agenda counter: Install 1 ice from HQ or Archives "
                    "in any position protecting a server, ignoring all costs",
                    do("install_ice_hq_or_archives_any_position_ignore_costs"),
                    cost={"agendaCounters": 1},
                    windows=["corp_action_paw"],
                ),
            ],
        )

    if cid == "slot-machine":
        return base(
            c,
            subtypes=["code gate"],
            onEncounter=do("mo_slot_machine_encounter"),
            subroutines=[
                {
                    "id": "slot-lose-3",
                    "text": "The Runner loses 3 credits.",
                    "effect": do("lose_credits", side="runner", amount=3),
                },
                {
                    "id": "slot-gain-3",
                    "text": (
                        "If you revealed 2 or more cards that share a type when "
                        "this encounter began, gain 3 credits."
                    ),
                    "effect": do(
                        "mo_slot_machine_if_shared_type_gte",
                        threshold=2,
                        then=gain("corp", 3),
                    ),
                },
                {
                    "id": "slot-advance-3",
                    "text": (
                        "If you revealed 3 or more cards that share a type when "
                        "this encounter began, place 3 advancement tokens on an "
                        "installed card."
                    ),
                    "effect": do(
                        "mo_slot_machine_if_shared_type_gte",
                        threshold=3,
                        then=do("place_advancements", amount=3),
                    ),
                },
            ],
        )

    if cid == "border-control":
        return base(
            c,
            subtypes=["barrier"],
            paidAbilities=[
                paid(
                    "border-control-trash-etr",
                    "[trash]: End the run (run on this server)",
                    etr(),
                    trash_self=True,
                    windows=[
                        "approach_paw",
                        "encounter_paw",
                        "approach_server_paw",
                    ],
                    require_during_run=True,
                ),
            ],
            subroutines=[
                {
                    "id": "border-gain-per-ice",
                    "text": "Gain 1 credit for each piece of ice protecting this server.",
                    "effect": do(
                        "gain_credits",
                        side="corp",
                        amount=0,
                        tally={
                            "count": "ice_protecting_source_server",
                            "per": 1,
                            "side": "corp",
                        },
                    ),
                },
                {
                    "id": "border-etr",
                    "text": "End the run.",
                    "effect": etr(),
                },
            ],
        )

    if cid == "watch-the-world-burn":
        return base(
            c,
            subtypes=["orgcrime", "run", "terminal"],
            endsActionPhase=True,
            deckLimit=1,
            runEvent={
                "servers": "remote",
                "rfgFirstNonAgendaAccess": True,
                "lastingRfgCopiesOnAccess": True,
            },
        )

    if cid == "hired-help":
        return base(
            c,
            subtypes=["orgcrime", "enforcer"],
            deckLimit=1,
            additionalRunCostTrashAgendaFromScoreUnlessSuccessfulHqThisTurn=True,
        )

    card = base(c)
    card["unsupported"] = [f"Unmapped in card: {cid}"]
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
