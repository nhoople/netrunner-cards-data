#!/usr/bin/env python3
"""Generate Business First (bf) card JSON from pinned pack `bf`.

Fetch: python3 scripts/nsg_catalog.py fetch bf
Mumbad cycle after Kala Ghoda (floor v1.116.0 → v1.117.0).
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
    seq,
    slugify,
    write_manifest,
)

OUT = Path(__file__).resolve().parents[1] / "data" / "business-first"
WAVE = "business-first"
PACK = "bf"
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
    power_counters: int = 0,
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

    if cid == "emp-device":
        return base(
            c,
            subtypes=["weapon"],
            paidAbilities=[
                paid(
                    "emp-device-limit-rez",
                    "[trash]: Corp cannot rez more than 1 ice for the remainder of this run",
                    do("emp_device_limit_ice_rez_this_run"),
                    trash_self=True,
                    windows=[
                        "approach_paw",
                        "encounter_paw",
                        "approach_server_paw",
                    ],
                    usable_by_runner=True,
                    require_during_run=True,
                )
            ],
        )

    if cid == "diwan":
        return base(
            c,
            subtypes=["virus"],
            memoryCost=1,
            chooseServerOnInstall=True,
            additionalCreditCostToInstallInChosenServer=1,
            trashOnVirusPurge=True,
        )

    if cid == "cbi-raid":
        return base(
            c,
            subtypes=["run"],
            runEvent={
                "servers": "hq",
                "onSuccessfulRun": do("cbi_raid_instead_of_breach"),
            },
        )

    if cid == "tech-trader":
        return base(
            c,
            subtypes=["connection"],
            gainCreditOnTrashAbilityUse=True,
        )

    if cid == "netchip":
        return base(
            c,
            subtypes=["chip"],
            deckLimit=6,
            daemonHost=True,
            maxHostedCards=1,
            daemonHostMaxMuFromInstalledCopiesOfSelf=True,
            hostedProgramMemoryDoesNotCount=True,
        )

    if cid == "corporate-scandal":
        return base(
            c,
            subtypes=["current"],
            lingerAsCurrent=True,
            currentTrashOnAgendaScored=True,
            corpAdditionalBadPublicity=1,
            corpAdditionalBadPublicityCannotBeRemoved=True,
        )

    if cid == "populist-rally":
        return base(
            c,
            playRequiresInstalledSubtype="seedy",
            onPlay=do("allotted_clicks_next_turn", side="corp", delta=-1),
        )

    if cid == "advanced-assembly-lines":
        return base(
            c,
            onRez=gain("corp", 3),
            paidAbilities=[
                paid(
                    "aal-install",
                    "[trash]: Install a non-agenda card from HQ (paying install cost)",
                    do("may_install_from_hq_paying_costs", excludeAgenda=True),
                    trash_self=True,
                    windows=["corp_action_paw"],
                    forbid_during_run=True,
                )
            ],
        )

    if cid == "lakshmi-smartfabrics":
        return base(
            c,
            placePowerCounterOnAnyCardRez=True,
            paidAbilities=[
                paid(
                    "lakshmi-reveal",
                    "X hosted power counters: Reveal an agenda worth X from HQ; Runner cannot steal copies this turn",
                    do("lakshmi_reveal_agenda_cannot_steal_copies"),
                    windows=["corp_action_paw"],
                )
            ],
        )

    if cid == "product-recall":
        return base(
            c,
            subtypes=["alliance"],
            zeroInfluenceIfNonAllianceFactionCardsGte={
                "faction": "haas-bioroid",
                "threshold": 6,
            },
            onPlay=do("product_recall_trash_rezzed_gain_trash_cost"),
        )

    if cid == "palana-foods-sustainable-growth":
        return base(
            c,
            subtypes=["division"],
            gainCreditOnFirstRunnerDrawEachTurn=True,
        )

    if cid == "palana-agroplex":
        return base(
            c,
            onTurnBegin=seq(draw("corp", 1), draw("runner", 1)),
        )

    if cid == "harvester":
        return base(
            c,
            subtypes=["code gate"],
            subroutines=[
                {
                    "id": "harvester-draw-discard-1",
                    "text": "The Runner draws 3 cards and then discards down to their maximum hand size.",
                    "effect": do(
                        "harvester_draw_then_discard_down_to_hand_size",
                        drawAmount=3,
                    ),
                },
                {
                    "id": "harvester-draw-discard-2",
                    "text": "The Runner draws 3 cards and then discards down to their maximum hand size.",
                    "effect": do(
                        "harvester_draw_then_discard_down_to_hand_size",
                        drawAmount=3,
                    ),
                },
            ],
        )

    if cid == "remote-data-farm":
        return base(
            c,
            handSizeBonus=2,
        )

    if cid == "disposable-hq":
        return base(
            c,
            mustRevealWhenAccessedFromRd=True,
            onAccess=may(
                do("disposable_hq_add_hq_to_bottom_rd"),
                label="Add any number of cards from HQ to the bottom of R&D",
                decline_side="corp",
            ),
        )

    if cid == "new-construction":
        return base(
            c,
            subtypes=["public"],
            installFaceup=True,
            onAdvance=may(
                do("new_construction_install_from_hq_new_remote"),
                label="Install 1 card from HQ in the root of a new server",
                decline_side="corp",
            ),
        )

    if cid == "mumbad-construction-co":
        return base(
            c,
            onTurnBegin=do("bf_place_advancement_on_self", amount=1),
            paidAbilities=[
                paid(
                    "mcc-move-adv",
                    "2¢: Move 1 advancement token from Mumbad Construction Co. to a faceup card",
                    do("mumbad_construction_move_advancement_to_faceup"),
                    credits=2,
                    windows=["corp_action_paw"],
                )
            ],
        )

    if cid == "corporate-sales-team":
        return base(
            c,
            onScore=do("place_hosted_credits", amount=10),
            onTurnBegin=do("take_hosted_credits", amount=1),
            onRunnerTurnBegin=do("take_hosted_credits", amount=1),
        )

    if cid == "pad-factory":
        return base(
            c,
            zeroInfluenceIfCardCopiesGte={
                "cardId": "pad-campaign",
                "threshold": 3,
            },
            paidAbilities=[
                paid(
                    "pad-factory-advance",
                    "[click]: Place 1 advancement token on a card; cannot score it until your next turn begins",
                    do("pad_factory_place_advancement_cannot_score_until_next_turn"),
                    clicks=1,
                    windows=["corp_action_paw"],
                )
            ],
        )

    card = base(c)
    card["unsupported"] = [f"Unmapped bf card: {cid}"]
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
