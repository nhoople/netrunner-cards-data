#!/usr/bin/env python3
"""Generate Blood Money (bm) card JSON from pinned pack `bm`.

Fetch: python3 scripts/nsg_catalog.py fetch bm
Flashpoint #2 after 23 Seconds (floor v1.122.0 → v1.123.0).
Reprint skip: none (20/20 new clears).
Follow NSG pack stripped_text (not IR-hint paraphrases).
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

OUT = Path(__file__).resolve().parents[1] / "data" / "blood-money"
WAVE = "blood-money"
PACK = "bm"
EXPECTED = 20

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
    require_fully_broken: bool = False,
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
    if require_fully_broken:
        ab["requireFullyBrokenThisEncounter"] = True
    return ab


def trace_sub(strength: int, on_success, on_failure=None) -> dict:
    action: dict = {"kind": "trace", "strength": strength, "onSuccess": on_success}
    if on_failure is not None:
        action["onFailure"] = on_failure
    return {"op": "do", "action": action}


def map_card(c: dict) -> dict | None:
    cid = slugify(c["title"])
    if cid in REPRINTS:
        return None

    if cid == "credit-crash":
        return base(
            c,
            subtypes=["run"],
            runEvent={
                "servers": "any",
                "trashFirstNonAgendaAccessCorpMayPayRezOrPlayCostToPrevent": True,
            },
        )

    if cid == "rumor-mill":
        return base(
            c,
            subtypes=["current"],
            lingerAsCurrent=True,
            currentTrashOnAgendaScored=True,
            blankUniqueNonRegionAssetUpgradePrintedAbilities=True,
        )

    if cid == "nfr":
        return base(
            c,
            subtypes=["icebreaker", "fracter"],
            memoryCost=1,
            strengthPerPowerCounter=True,
            onFullyBreak=do("add_power_counter", amount=1),
            breaker={
                "breaksSubtype": "barrier",
                "strength": 1,
                "breakCredits": 1,
                "breakMaxSubs": 1,
            },
        )

    if cid == "paperclip":
        return base(
            c,
            subtypes=["icebreaker", "fracter"],
            memoryCost=1,
            mayInstallSelfFromHeapOnEncounterBarrier=True,
            breaker={
                "breaksSubtype": "barrier",
                "strength": 1,
                "breakCredits": 1,
                "breakMaxSubs": 1,
                "breakViaPaidAbilityOnly": True,
            },
            paidAbilities=[
                paid(
                    "paperclip-x",
                    "X¢: +X strength. Then break up to X barrier subroutines",
                    do("spend_x_pump_and_break"),
                    windows=["encounter_paw"],
                    usable_by_runner=True,
                ),
            ],
        )

    if cid == "golden":
        return base(
            c,
            subtypes=["icebreaker", "killer"],
            memoryCost=1,
            breaker={
                "breaksSubtype": "sentry",
                "strength": 1,
                "breakCredits": 2,
                "breakMaxSubs": 2,
                "pumpCredits": 2,
                "pumpStrength": 4,
            },
            paidAbilities=[
                paid(
                    "golden-derez",
                    "2¢, add this program to your grip: Derez fully broken sentry",
                    seq(
                        do("derez_encounter_ice"),
                        do("return_source_to_grip"),
                    ),
                    credits=2,
                    windows=["encounter_paw"],
                    usable_by_runner=True,
                    require_fully_broken=True,
                ),
            ],
        )

    if cid == "temujin-contract":
        return base(
            c,
            subtypes=["job"],
            unique=True,
            onInstall=do("choose_server_runner"),
            hostedCreditsOnInstall=20,
            onSuccessfulRun={
                "op": "if",
                "cond": {"op": "attacking_chosen_server"},
                "then": do("take_hosted_credits", amount=4),
            },
        )

    if cid == "khan-savvy-skiptracer":
        return base(
            c,
            subtypes=["natural"],
            link=c.get("base_link", 0),
            onFirstPassIceEachTurn=may(
                do(
                    "may_install_from_grip",
                    types=["program"],
                    subtype="icebreaker",
                    discount=1,
                ),
                label="Install an icebreaker from grip, lowering install cost by 1",
            ),
        )

    if cid == "data-breach":
        return base(
            c,
            subtypes=["run"],
            runEvent={
                "servers": "rd",
                "onRunEnd": {
                    "op": "if",
                    "cond": {"op": "run_successful"},
                    "then": do("may_start_run", servers="rd"),
                },
            },
        )

    if cid == "algo-trading":
        return base(
            c,
            subtypes=["job"],
            onTurnBegin=seq(
                do("may_move_up_to_credits_from_pool_to_self", amount=3),
                {
                    "op": "if",
                    "cond": {"op": "hosted_credits_gte", "amount": 6},
                    "then": do("place_hosted_credits", amount=2),
                },
            ),
            paidAbilities=[
                paid(
                    "algo-take",
                    "[click],[trash]: Take all credits from Algo Trading",
                    do("take_hosted_credits", amount=999),
                    clicks=1,
                    trash_self=True,
                    windows=["runner_action_paw"],
                    usable_by_runner=True,
                ),
            ],
        )

    if cid == "beth-kilrain-chang":
        return base(
            c,
            subtypes=["connection"],
            unique=True,
            onTurnBegin=do("beth_kilrain_corp_credit_tiers"),
        )

    if cid == "fairchild-2-0":
        return base(
            c,
            subtypes=["code gate", "bioroid", "ap"],
            bioroidBreakMaxSubs=2,
            subroutines=[
                {
                    "id": "fairchild-2-0-pay-or-trash-1",
                    "text": "The Runner must pay 2¢ or trash 1 of their installed cards.",
                    "effect": do(
                        "pay_credits_or_trash_installed",
                        side="runner",
                        amount=2,
                    ),
                },
                {
                    "id": "fairchild-2-0-pay-or-trash-2",
                    "text": "The Runner must pay 2¢ or trash 1 of their installed cards.",
                    "effect": do(
                        "pay_credits_or_trash_installed",
                        side="runner",
                        amount=2,
                    ),
                },
                {
                    "id": "fairchild-2-0-core",
                    "text": "Do 1 core damage.",
                    "effect": do("core_damage", amount=1),
                },
            ],
        )

    if cid == "aiki":
        return base(
            c,
            subtypes=["code gate", "psi", "ap"],
            subroutines=[
                {
                    "id": "aiki-psi",
                    "text": "You and the Runner secretly spend 0¢, 1¢, or 2¢. Reveal spent credits. If you and the Runner spent a different number of credits, the Runner draws 2 cards.",
                    "effect": do(
                        "play_psi_game",
                        maxBid=2,
                        ifBidsDiffer=draw("runner", 2),
                    ),
                },
                {
                    "id": "aiki-net-1",
                    "text": "Do 1 net damage.",
                    "effect": net(1),
                },
                {
                    "id": "aiki-net-2",
                    "text": "Do 1 net damage.",
                    "effect": net(1),
                },
            ],
        )

    if cid == "enforcing-loyalty":
        return base(
            c,
            subtypes=["double", "gray ops"],
            playAdditionalClick=True,
            onPlay=trace_sub(
                3,
                do("trash_installed_not_matching_runner_identity_faction"),
            ),
        )

    if cid == "hatchet-job":
        return base(
            c,
            subtypes=["double", "gray ops"],
            playAdditionalClick=True,
            onPlay=trace_sub(
                5,
                do("add_installed_non_virtual_runner_to_grip"),
            ),
        )

    if cid == "special-report":
        return base(
            c,
            onPlay=do("shuffle_any_hq_draw"),
        )

    if cid == "c-i-fund":
        return base(
            c,
            onTurnBegin=seq(
                do("may_move_up_to_credits_from_pool_to_self", amount=3),
                {
                    "op": "if",
                    "cond": {"op": "hosted_credits_gte", "amount": 6},
                    "then": do("place_hosted_credits", amount=2),
                },
            ),
            paidAbilities=[
                paid(
                    "ci-fund-take",
                    "2¢,[trash]: Take all credits from C.I. Fund",
                    do("take_hosted_credits", amount=999),
                    credits=2,
                    trash_self=True,
                    windows=["corp_action_paw"],
                ),
            ],
        )

    if cid == "liquidation":
        return base(
            c,
            subtypes=["double", "gray ops", "transaction"],
            playAdditionalClick=True,
            onPlay=do("trash_any_rezzed_gain_3_each"),
        )

    if cid == "weyland-consortium-builder-of-nations":
        return base(
            c,
            subtypes=["megacorp"],
            firstAdvancedIceEncounterEndMeatDamageEachTurn=True,
        )

    if cid == "financial-collapse":
        return base(
            c,
            playRequiresRunnerCreditsGte=6,
            onPlay=do("lose_2_per_resource_or_trash"),
        )

    if cid == "prisec":
        return base(
            c,
            subtypes=["ambush"],
            onAccessRequiresInstalled=True,
            onAccess=may(
                seq(
                    do("lose_credits", side="corp", amount=2),
                    do("give_tags", amount=1),
                    do("meat_damage", amount=1),
                ),
                label="Pay 2¢: give the Runner 1 tag and do 1 meat damage",
                decline_side="corp",
            ),
        )

    card = base(c)
    card["unsupported"] = [f"Unmapped bm card: {cid}"]
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
