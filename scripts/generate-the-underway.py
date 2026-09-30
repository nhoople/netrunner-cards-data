#!/usr/bin/env python3
"""Generate The Underway (uw) card JSON from pinned pack `uw`.

Fetch: python3 scripts/nrdb_catalog.py fetch uw
SanSan cycle after Chrome City (floor v1.111.0 → v1.112.0).
Reprint skip: chameleon, contract-killer, spiderweb.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from nrdb_catalog import load_pack_cards
from spin_common import (
    base,
    breaker_card,
    core,
    do,
    etr,
    gain,
    seq,
    slugify,
    write_manifest,
)

OUT = Path(__file__).resolve().parents[1] / "data" / "the-underway"
WAVE = "the-underway"
PACK = "uw"
EXPECTED = 20

REPRINTS = {
    "chameleon",  # system-update-2021
    "contract-killer",  # system-core-2019
    "spiderweb",  # system-core-2019
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
    require_runner_clicks_eq: int | None = None,
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
    if require_runner_clicks_eq is not None:
        ab["requireRunnerClicksEq"] = require_runner_clicks_eq
    return ab


def etr_if_tagged() -> dict:
    return {
        "op": "if",
        "cond": {"op": "runner_tagged"},
        "then": etr(),
    }


def map_card(c: dict) -> dict | None:
    cid = slugify(c["title"])
    if cid in REPRINTS:
        return None

    if cid == "faust":
        card = breaker_card(c, "*", 2, 0, 0, 0)
        card["breaker"]["breakViaPaidAbilityOnly"] = True
        card["breaker"]["breakMaxSubs"] = 1
        del card["breaker"]["pumpCredits"]
        del card["breaker"]["pumpStrength"]
        card["paidAbilities"] = [
            {
                "id": "faust-break",
                "label": "Trash a card from your grip: Break 1 subroutine",
                "clickCost": 0,
                "creditCost": 0,
                "cost": {"trashFromGrip": 1},
                "windows": ["encounter_paw"],
                "effect": do("break_encounter_subroutine", maxSubs=1),
            },
            {
                "id": "faust-pump",
                "label": "Trash a card from your grip: +2 strength",
                "clickCost": 0,
                "creditCost": 0,
                "cost": {"trashFromGrip": 1},
                "windows": ["encounter_paw"],
                "effect": do("pump_strength", amount=2),
            },
        ]
        return card

    if cid == "street-peddler":
        return base(
            c,
            subtypes=["connection", "seedy"],
            onInstall=do("host_top_n_of_stack_facedown", amount=3),
            paidAbilities=[
                paid(
                    "street-peddler-install",
                    "[trash]: Install 1 hosted card, lowering install cost by 1",
                    do("street_peddler_install_hosted", discount=1),
                    trash_self=True,
                    windows=["runner_action_paw"],
                )
            ],
        )

    if cid == "armand-geist-walker-tech-lord":
        return base(
            c,
            subtypes=["g-mod"],
            link=c.get("base_link", 1),
            drawOnUseTrashAbility=1,
        )

    if cid == "drive-by":
        return base(
            c,
            subtypes=["double"],
            playAdditionalClick=True,
            onPlay=do("drive_by_expose_and_trash_remote_root"),
        )

    if cid == "forger":
        return base(
            c,
            subtypes=["console"],
            unique=False,
            link=1,
            maxConsole=1,
            paidAbilities=[
                {
                    "id": "forger-prevent-tag",
                    "label": "[interrupt] → [trash]: Prevent 1 tag",
                    "clickCost": 0,
                    "creditCost": 0,
                    "cost": {"trashSelf": True},
                    "windows": ["tag_interrupt_paw"],
                    "effect": do("prevent_pending_tags", amount=1),
                },
                paid(
                    "forger-remove-tag",
                    "[trash]: Remove 1 tag",
                    do("remove_tags", amount=1),
                    trash_self=True,
                    windows=["runner_action_paw"],
                ),
            ],
        )

    if cid == "shiv":
        card = breaker_card(c, "sentry", 0, 0, 0, 0)
        card["breaker"]["breakViaPaidAbilityOnly"] = True
        card["breaker"]["breakMaxSubs"] = 3
        del card["breaker"]["pumpCredits"]
        del card["breaker"]["pumpStrength"]
        card["memoryCostZeroIfLinkGte"] = 2
        card["strengthBonusPerIcebreaker"] = 1
        card["paidAbilities"] = [
            {
                "id": "shiv-break",
                "label": "[trash]: Break up to 3 sentry subroutines",
                "clickCost": 0,
                "creditCost": 0,
                "cost": {"trashSelf": True},
                "windows": ["encounter_paw"],
                "requireEncounterSubtype": "sentry",
                "effect": do("break_encounter_subroutine", maxSubs=3),
            }
        ]
        return card

    if cid == "gang-sign":
        return base(
            c,
            subtypes=["virtual"],
            onAgendaScored=do("raymond_flint_breach_hq_no_root"),
        )

    if cid == "muertos-gang-member":
        return base(
            c,
            subtypes=["connection"],
            onInstall=do("corp_must_derez_a_card"),
            onUninstall=may(
                do("corp_may_rez_ignoring_cost"),
                label="Rez a card, ignoring the rez cost",
                decline_side="corp",
            ),
            paidAbilities=[
                paid(
                    "muertos-draw",
                    "[trash]: Draw 1 card",
                    do("draw", side="runner", amount=1),
                    trash_self=True,
                    windows=["runner_action_paw"],
                )
            ],
        )

    if cid == "hyperdriver":
        return base(
            c,
            onTurnBegin=may(
                seq(
                    do("rfg_self"),
                    do("gain_clicks", side="runner", amount=3),
                ),
                label="Remove Hyperdriver from the game: gain [click][click][click]",
                decline_side="runner",
            ),
        )

    if cid == "test-ground":
        return base(
            c,
            canAdvance=True,
            paidAbilities=[
                paid(
                    "test-ground-derez",
                    "[trash]: Derez 1 card for each advancement token on Test Ground",
                    do("derez_per_advancement_on_self"),
                    trash_self=True,
                    windows=["corp_action_paw"],
                )
            ],
        )

    if cid == "defective-brainchips":
        return base(
            c,
            subtypes=["current"],
            lingerAsCurrent=True,
            currentTrashOnAgendaStolen=True,
            increaseFirstCoreDamagePerTurn=1,
        )

    if cid == "allele-repression":
        return base(
            c,
            canAdvance=True,
            paidAbilities=[
                paid(
                    "allele-swap",
                    "[trash]: Swap 1 HQ ↔ Archives card per advancement",
                    do("swap_hq_archives_per_advancement_on_self"),
                    trash_self=True,
                    windows=["corp_action_paw"],
                )
            ],
        )

    if cid == "marcus-batty":
        return base(
            c,
            subtypes=["sysop", "psi"],
            unique=True,
            paidAbilities=[
                paid(
                    "marcus-batty-psi",
                    "[trash]: Psi game; if bids differ, resolve 1 sub on rezzed ice protecting this server",
                    {
                        "op": "do",
                        "action": {
                            "kind": "play_psi_game",
                            "maxBid": 2,
                            "ifBidsDiffer": do(
                                "resolve_subroutine_on_rezzed_ice_protecting_this_server"
                            ),
                        },
                    },
                    trash_self=True,
                    windows=[
                        "approach_paw",
                        "encounter_paw",
                        "approach_server_paw",
                    ],
                    require_during_run=True,
                    require_this_server=True,
                )
            ],
        )

    if cid == "expose":
        return base(
            c,
            canAdvance=True,
            paidAbilities=[
                paid(
                    "expose-remove-bp",
                    "[trash]: Remove 1 bad publicity per advancement",
                    do("remove_bad_publicity_per_advancement_on_self"),
                    trash_self=True,
                    windows=["corp_action_paw"],
                )
            ],
        )

    if cid == "pachinko":
        return base(
            c,
            subtypes=["barrier"],
            subroutines=[
                {
                    "id": "pachinko-etr-1",
                    "text": "End the run if the Runner is tagged.",
                    "effect": etr_if_tagged(),
                },
                {
                    "id": "pachinko-etr-2",
                    "text": "End the run if the Runner is tagged.",
                    "effect": etr_if_tagged(),
                },
            ],
        )

    if cid == "underway-renovation":
        return base(
            c,
            subtypes=["initiative", "public"],
            installFaceup=True,
            trashTopOfStackOnAdvance={
                "default": 1,
                "atOrAbove": 4,
                "bonus": 2,
            },
        )

    if cid == "underway-grid":
        return base(
            c,
            subtypes=["region"],
            iceCannotBeBypassedThisServer=True,
            cardsCannotBeExposedThisServer=True,
        )

    card = base(c)
    card["unsupported"] = [f"Unmapped uw card: {cid}"]
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
