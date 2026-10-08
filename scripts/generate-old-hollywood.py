#!/usr/bin/env python3
"""Generate Old Hollywood (oh) card JSON from pinned pack `oh`.

Fetch: python3 scripts/nsg_catalog.py fetch oh
SanSan cycle after The Underway (floor v1.112.0 → v1.113.0).
Reprint skip: explode-a-palooza.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from nsg_catalog import load_pack_cards
from spin_common import (
    base,
    core,
    do,
    etr,
    gain,
    seq,
    slugify,
    write_manifest,
)

OUT = Path(__file__).resolve().parents[1] / "data" / "old-hollywood"
WAVE = "old-hollywood"
PACK = "oh"
EXPECTED = 20

REPRINTS = {
    "explode-a-palooza",  # system-core-2019
}


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
    rfg_self: bool = False,
    usable_by_runner: bool = False,
    require_encounter_subtype: str | None = None,
    require_during_run: bool = False,
    require_this_server: bool = False,
    require_pending_damage_types: list[str] | None = None,
) -> dict:
    c = dict(cost or {})
    if clicks:
        c["clicks"] = clicks
    if credits:
        c["credits"] = credits
    if trash_self:
        c["trashSelf"] = True
    if rfg_self:
        c["rfgSelf"] = True
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
    if require_encounter_subtype:
        ab["requireEncounterSubtype"] = require_encounter_subtype
    if require_during_run:
        ab["requireDuringRun"] = True
    if require_this_server:
        ab["requireThisServer"] = True
    if require_pending_damage_types:
        ab["requirePendingDamageTypes"] = require_pending_damage_types
    return ab


def map_card(c: dict) -> dict | None:
    cid = slugify(c["title"])
    if cid in REPRINTS:
        return None

    if cid == "trope":
        return base(
            c,
            onTurnBegin=do("add_power_counter", amount=1),
            paidAbilities=[
                paid(
                    "trope-shuffle",
                    "[click], remove Trope from the game: Shuffle 1 heap card into stack per power counter",
                    do("shuffle_n_heap_cards_into_stack_per_power_counter"),
                    clicks=1,
                    rfg_self=True,
                    windows=["runner_action_paw"],
                )
            ],
        )

    if cid == "spoilers":
        return base(
            c,
            subtypes=["virtual"],
            onAgendaScored=do("trash_top_of_rd"),
        )

    if cid == "drug-dealer":
        return base(
            c,
            subtypes=["connection"],
            onTurnBegin=do("lose_credits", side="runner", amount=1),
            onCorpTurnBegin=do("draw", side="runner", amount=1),
        )

    if cid == "rolodex":
        return base(
            c,
            subtypes=["virtual"],
            onInstall=do("look_top_n_stack_arrange", n=5),
            onTrash=seq(
                do("trash_top_of_stack"),
                do("trash_top_of_stack"),
                do("trash_top_of_stack"),
            ),
        )

    if cid == "fan-site":
        return base(
            c,
            subtypes=["virtual"],
            onAgendaScored=do(
                "add_to_runner_score_as_agenda", agendaPoints=0
            ),
        )

    if cid == "film-critic":
        return base(
            c,
            subtypes=["connection"],
            hostAgendaCapacity=1,
            mayHostAccessedAgenda=True,
            paidAbilities=[
                paid(
                    "film-critic-score",
                    "[click],[click]: Add a hosted agenda to your score area",
                    do("add_hosted_agenda_to_runner_score"),
                    clicks=2,
                    windows=["runner_action_paw"],
                )
            ],
        )

    if cid == "paparazzi":
        return base(
            c,
            countsAsTagged=True,
            preventAllMeatDamage=True,
        )

    if cid == "ronald-five":
        return base(
            c,
            subtypes=["bioroid"],
            unique=True,
            runnerLosesClickWhenTrashesCorpCard=True,
        )

    if cid == "enforcer-1-0":
        return base(
            c,
            subtypes=["sentry", "bioroid", "destroyer", "ap"],
            rezAdditionalCostForfeitAgenda=True,
            bioroidBreakMaxSubs=1,
            subroutines=[
                {
                    "id": "enforcer-trash-program",
                    "text": "Trash 1 installed program.",
                    "effect": do("trash_program", pick="choose"),
                },
                {
                    "id": "enforcer-core",
                    "text": "Do 1 core damage.",
                    "effect": core(1),
                },
                {
                    "id": "enforcer-trash-console",
                    "text": "Trash 1 installed console.",
                    "effect": do(
                        "trash_hardware_with_subtype",
                        subtype="console",
                        pick="choose",
                    ),
                },
                {
                    "id": "enforcer-trash-virtual",
                    "text": "Trash all installed virtual resources.",
                    "effect": do(
                        "trash_installed_resources_with_any_subtype",
                        subtypes=["virtual"],
                    ),
                },
            ],
        )

    if cid == "its-a-trap":
        return base(
            c,
            subtypes=["trap"],
            onExposeWhileInstalled=do("net_damage", amount=2),
            subroutines=[
                {
                    "id": "its-a-trap-trash",
                    "text": "The Runner trashes 1 of their installed cards. Trash this ice.",
                    "effect": seq(
                        do("runner_trashes_one_installed"),
                        do("trash_self"),
                    ),
                }
            ],
        )

    if cid == "an-offer-you-cant-refuse":
        return base(
            c,
            onPlay=do("an_offer_you_cant_refuse"),
        )

    if cid == "haarpsichord-studios-entertainment-unleashed":
        return base(
            c,
            subtypes=["division"],
            cannotStealMoreThanOneAgendaPerTurn=True,
        )

    if cid == "award-bait":
        return base(
            c,
            subtypes=["sensie"],
            mustRevealWhenAccessedFromRd=True,
            onAccess=may(
                do(
                    "place_up_to_n_advancements_on_advanceable_installed",
                    max=2,
                ),
                label="Place up to 2 advancements on an advanceable installed card",
                decline_side="corp",
            ),
        )

    if cid == "early-premiere":
        return base(
            c,
            onTurnBegin=may(
                do("pay_place_advancement"),
                label="Pay 1¢: place 1 advancement on an advanceable card in a remote root",
                decline_side="corp",
            ),
        )

    if cid == "casting-call":
        return base(
            c,
            subtypes=["condition"],
            onPlay=do("install_agenda_faceup"),
        )

    if cid == "old-hollywood-grid":
        return base(
            c,
            subtypes=["region"],
            persistent=True,
            cannotStealUnlessCopyInRunnerScore=True,
        )

    if cid == "hollywood-renovation":
        return base(
            c,
            subtypes=["initiative", "public"],
            installFaceup=True,
            placeAdvancementOnAnotherOnAdvance={
                "default": 1,
                "atOrAbove": 6,
                "bonus": 2,
            },
        )

    if cid == "back-channels":
        return base(
            c,
            subtypes=["transaction"],
            onPlay=do("trash_remote_root"),
        )

    if cid == "vanity-project":
        return base(c)

    card = base(c)
    card["unsupported"] = [f"Unmapped oh card: {cid}"]
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
