#!/usr/bin/env python3
"""Generate The Universe of Tomorrow (uot) card JSON from pinned pack `uot`.

Fetch: python3 scripts/nrdb_catalog.py fetch uot
SanSan cycle after Old Hollywood (floor v1.113.0 → v1.114.0).
Reprint skip: product-placement, public-support.
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
    seq,
    slugify,
    write_manifest,
)

OUT = Path(__file__).resolve().parents[1] / "data" / "the-universe-of-tomorrow"
WAVE = "the-universe-of-tomorrow"
PACK = "uot"
EXPECTED = 20

REPRINTS = {
    "product-placement",  # system-core-2019
    "public-support",  # system-core-2019
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
    usable_by_runner: bool = False,
    require_encounter_subtype: str | None = None,
    require_during_run: bool = False,
    require_this_server: bool = False,
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
    if require_encounter_subtype:
        ab["requireEncounterSubtype"] = require_encounter_subtype
    if require_during_run:
        ab["requireDuringRun"] = True
    if require_this_server:
        ab["requireThisServer"] = True
    return ab


def map_card(c: dict) -> dict | None:
    cid = slugify(c["title"])
    if cid in REPRINTS:
        return None

    if cid == "power-to-the-people":
        return base(
            c,
            subtypes=["priority"],
            playRequiresFirstClick=True,
            onPlay=do("arm_gain_credits_on_first_agenda_access", amount=7),
        )

    if cid == "surfer":
        return base(
            c,
            paidAbilities=[
                paid(
                    "surfer-swap",
                    "2¢: Swap encountered barrier with ice directly before or after it",
                    do("surfer_swap_encounter_barrier_adjacent"),
                    credits=2,
                    windows=["runner_action_paw"],
                    usable_by_runner=True,
                    require_encounter_subtype="barrier",
                    require_during_run=True,
                )
            ],
        )

    if cid == "ddos":
        return base(
            c,
            subtypes=["virtual"],
            paidAbilities=[
                paid(
                    "ddos-trash",
                    "[trash]: Corp cannot rez outermost ice during a run this turn",
                    do("arm_cannot_rez_outermost_ice_this_turn"),
                    trash_self=True,
                    windows=["runner_action_paw"],
                )
            ],
        )

    if cid == "laramy-fisk-savvy-investor":
        return base(
            c,
            subtypes=["natural"],
            link=c.get("base_link", 0),
            onFirstSuccessfulCentralRunThisTurn=may(
                do("draw", side="corp", amount=1),
                label="Force the Corp to draw 1 card",
                decline_side="runner",
            ),
        )

    if cid == "fisk-investment-seminar":
        return base(
            c,
            subtypes=["priority"],
            playRequiresFirstClick=True,
            onPlay=seq(
                do("draw", side="runner", amount=3),
                do("draw", side="corp", amount=3),
            ),
        )

    if cid == "bookmark":
        return base(
            c,
            maxHostedCards=3,
            paidAbilities=[
                paid(
                    "bookmark-host",
                    "[click]: Host up to 3 cards from grip facedown",
                    do("bookmark_host_up_to_3_from_grip_facedown"),
                    clicks=1,
                    windows=["runner_action_paw"],
                ),
                paid(
                    "bookmark-to-grip-click",
                    "[click]: Add all hosted cards to grip",
                    do("bookmark_add_all_hosted_to_grip"),
                    clicks=1,
                    windows=["runner_action_paw"],
                ),
                paid(
                    "bookmark-to-grip-trash",
                    "[trash]: Add all hosted cards to grip",
                    do("bookmark_add_all_hosted_to_grip"),
                    trash_self=True,
                    windows=["runner_action_paw"],
                ),
            ],
        )

    if cid == "davinci":
        return base(
            c,
            onSuccessfulRun=do("add_power_counter", amount=1),
            paidAbilities=[
                paid(
                    "davinci-install",
                    "[trash]: Install a grip card costing ≤ power counters, ignoring install cost",
                    do("davinci_install_from_grip_ignore_cost"),
                    trash_self=True,
                    windows=["runner_action_paw"],
                )
            ],
        )

    if cid == "wireless-net-pavilion":
        return base(
            c,
            subtypes=["location"],
            unique=True,
            basicTrashResourceAdditionalCostCredits=2,
        )

    if cid == "cybernetics-court":
        return base(
            c,
            subtypes=["facility", "ritzy"],
            unique=True,
            handSizeBonus=4,
        )

    if cid == "team-sponsorship":
        return base(
            c,
            onAgendaScored=do("may_install_from_hq_or_archives_ignore_costs"),
        )

    if cid == "chronos-protocol-selective-mind-mapping":
        return base(
            c,
            subtypes=["division"],
            corpChoosesFirstNetDamageCardEachTurn=True,
        )

    if cid == "ancestral-imager":
        return base(
            c,
            subtypes=["security"],
            netDamageOnJackOut=1,
        )

    if cid == "genetics-pavilion":
        return base(
            c,
            subtypes=["facility", "ritzy"],
            unique=True,
            runnerCannotDrawMoreThanPerTurn=2,
        )

    if cid == "franchise-city":
        return base(
            c,
            subtypes=["facility"],
            unique=True,
            mustRevealAgendasAccessedFromRd=True,
            addSelfToCorpScoreOnAgendaAccess={"agendaPoints": 1},
        )

    if cid == "worlds-plaza":
        return base(
            c,
            subtypes=["facility"],
            unique=True,
            maxHostedCards=3,
            hostAssetsOnly=True,
            paidAbilities=[
                paid(
                    "worlds-plaza-install",
                    "[click]: Install an asset from HQ on Worlds Plaza and rez it (−2¢)",
                    do("worlds_plaza_install_asset_from_hq_rez_discount", discount=2),
                    clicks=1,
                    windows=["corp_action_paw"],
                )
            ],
        )

    if cid == "tour-guide":
        return base(
            c,
            subtypes=["sentry"],
            etrSubroutinesPerRezzedAsset=True,
            subroutines=[],
        )

    if cid == "expo-grid":
        return base(
            c,
            subtypes=["region"],
            onTurnBegin=do("expo_grid_gain_if_rezzed_asset_in_root"),
        )

    if cid == "the-future-is-now":
        return base(
            c,
            subtypes=["initiative"],
            onScore=do("search_rd_to_hq", amount=1),
        )

    card = base(c)
    card["unsupported"] = [f"Unmapped uot card: {cid}"]
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
