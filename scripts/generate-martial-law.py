#!/usr/bin/env python3
"""Generate Martial Law (ml) card JSON from pinned pack `ml`.

Fetch: python3 scripts/nsg_catalog.py fetch ml
Flashpoint #5 after Intervention (floor v1.125.0 → v1.126.0).
Reprint skips: none (20/20 new clears).
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
    core,
    do,
    draw,
    etr,
    gain,
    net,
    seq,
    slugify,
    write_manifest,
)

OUT = Path(__file__).resolve().parents[1] / "data" / "martial-law"
WAVE = "martial-law"
PACK = "ml"
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
    require_pending_damage_types: list[str] | None = None,
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
    if require_pending_damage_types is not None:
        ab["requirePendingDamageTypes"] = require_pending_damage_types
    return ab


def trace_sub(strength: int, on_success, on_failure=None) -> dict:
    action: dict = {"kind": "trace", "strength": strength, "onSuccess": on_success}
    if on_failure is not None:
        action["onFailure"] = on_failure
    return {"op": "do", "action": action}


def etr_if_tagged() -> dict:
    return {
        "op": "if",
        "cond": {"op": "runner_tagged"},
        "then": etr(),
    }


def if_adv_gte(amount: int, then: dict, else_: dict) -> dict:
    return {
        "op": "if",
        "cond": {"op": "advancements_gte", "amount": amount},
        "then": then,
        "else": else_,
    }


def map_card(c: dict) -> dict | None:
    cid = slugify(c["title"])
    if cid in REPRINTS:
        return None

    if cid == "mkultra":
        return base(
            c,
            subtypes=["icebreaker", "killer"],
            memoryCost=1,
            mayInstallSelfFromHeapOnEncounterSentry=True,
            breaker={
                "breaksSubtype": "sentry",
                "strength": 1,
                "breakCredits": 3,
                "breakMaxSubs": 2,
                "breakViaPaidAbilityOnly": True,
            },
            paidAbilities=[
                paid(
                    "mkultra-pump-break",
                    "3¢: +2 strength. Then, if this can interface with the sentry, break up to 2 subroutines",
                    do("mkultra_spend_pump_and_break"),
                    credits=3,
                    windows=["encounter_paw"],
                    usable_by_runner=True,
                ),
            ],
        )

    if cid == "on-the-lam":
        return base(
            c,
            subtypes=["condition"],
            onPlay=do("host_on_installed_resource_as_condition"),
            paidAbilities=[
                paid(
                    "on-the-lam-prevent",
                    "[interrupt] → [trash]: Prevent up to 3 tags or up to 3 damage",
                    do("on_the_lam_prevent_tags_or_damage", max=3),
                    cost={"trashSelf": True},
                    windows=["tag_interrupt_paw", "damage_interrupt_paw"],
                    usable_by_runner=True,
                ),
            ],
        )

    if cid == "cold-read":
        return base(
            c,
            subtypes=["run", "stealth"],
            runEvent={
                "servers": "any",
                "placeEventCredits": 4,
                "onRunEnd": do(
                    "trash_one_program_used_this_run_cannot_prevent"
                ),
            },
        )

    if cid == "equivocation":
        return base(
            c,
            unique=True,
            memoryCost=1,
            onSuccessfulRunOnRd=do("equivocation_may_reveal_force_draw"),
        )

    if cid == "misdirection":
        return base(
            c,
            memoryCost=1,
            paidAbilities=[
                paid(
                    "misdirection-remove-tags",
                    "[click], [click], X¢: Remove X tags",
                    do("misdirection_spend_x_remove_tags"),
                    clicks=2,
                    windows=["runner_action_paw"],
                    usable_by_runner=True,
                ),
            ],
        )

    if cid == "reaver":
        return base(
            c,
            memoryCost=1,
            drawOnFirstTrashInstalledEachTurn=True,
        )

    if cid == "interdiction":
        return base(
            c,
            subtypes=["current"],
            lingerAsCurrent=True,
            currentTrashOnAgendaScored=True,
            cannotRezNonIceDuringRunnerTurn=True,
        )

    if cid == "baba-yaga":
        return base(
            c,
            subtypes=["icebreaker", "ai"],
            memoryCost=1,
            strength=0,
            maxHostedCards=99,
            hostNonAiIcebreaker=True,
            gainsPaidAbilitiesOfHostedIcebreakers=True,
        )

    if cid == "fairchild":
        return base(
            c,
            subtypes=["code gate", "bioroid", "ap"],
            unique=True,
            bioroidBreakMaxSubs=4,
            subroutines=[
                {
                    "id": "fairchild-etr-pay-1",
                    "text": "End the run unless the Runner pays 4¢.",
                    "effect": do(
                        "end_the_run_unless_pay_credits",
                        side="runner",
                        amount=4,
                    ),
                },
                {
                    "id": "fairchild-etr-pay-2",
                    "text": "End the run unless the Runner pays 4¢.",
                    "effect": do(
                        "end_the_run_unless_pay_credits",
                        side="runner",
                        amount=4,
                    ),
                },
                {
                    "id": "fairchild-etr-trash",
                    "text": "End the run unless the Runner trashes 1 of their installed cards.",
                    "effect": do("end_the_run_unless_trash_installed"),
                },
                {
                    "id": "fairchild-etr-core",
                    "text": "End the run unless the Runner suffers 1 core damage.",
                    "effect": do(
                        "end_the_run_unless_core_damage",
                        amount=1,
                    ),
                },
            ],
        )

    if cid == "friends-in-high-places":
        return base(
            c,
            subtypes=["terminal"],
            endsActionPhase=True,
            onPlay=do("install_up_to_n_from_archives_paying", max=2),
        )

    if cid == "manta-grid":
        return base(
            c,
            subtypes=["region"],
            unique=True,
            additionalClickNextTurnOnSuccessfulRunEndIfRunnerLt6cOrNoClicks=True,
        )

    if cid == "mind-game":
        return base(
            c,
            subtypes=["code gate", "psi", "deflector"],
            subroutines=[
                {
                    "id": "mind-game-psi",
                    "text": (
                        "Psi game. If bids differ, choose another server; "
                        "Runner moves to outermost of that server; "
                        "additional cost to jack out; Runner may jack out."
                    ),
                    "effect": do(
                        "play_psi_game",
                        maxBid=2,
                        ifBidsDiffer=do("mind_game_psi_differ_redirect"),
                    ),
                },
            ],
        )

    if cid == "nihongai-grid":
        return base(
            c,
            subtypes=["region"],
            unique=True,
            onSuccessfulRunOnThisServer=do("nihongai_may_look_top5_swap_hq"),
        )

    if cid == "ip-block":
        return base(
            c,
            subtypes=["barrier", "tracer"],
            onEncounter=do(
                "give_tags_if_runner_has_installed_subtype",
                amount=1,
                subtype="ai",
            ),
            subroutines=[
                {
                    "id": "ip-block-trace",
                    "text": "Trace[3]. If successful, give the Runner 1 tag.",
                    "effect": trace_sub(3, do("give_tags", amount=1)),
                },
                {
                    "id": "ip-block-etr-tagged",
                    "text": "End the run if the Runner is tagged.",
                    "effect": etr_if_tagged(),
                },
            ],
        )

    if cid == "thoth":
        return base(
            c,
            subtypes=["sentry", "tracer"],
            unique=True,
            onEncounter=do("give_tags", amount=1),
            subroutines=[
                {
                    "id": "thoth-net-per-tag",
                    "text": "Trace[4]. If successful, do 1 net damage for each tag the Runner has.",
                    "effect": trace_sub(4, do("net_damage_per_tag")),
                },
                {
                    "id": "thoth-lose-credits-per-tag",
                    "text": "Trace[4]. If successful, the Runner loses 1¢ for each tag they have.",
                    "effect": trace_sub(4, do("lose_credits_per_tag", side="runner")),
                },
            ],
        )

    if cid == "anson-rose":
        return base(
            c,
            subtypes=["executive"],
            unique=True,
            onTurnBegin=do("bf_place_advancement_on_self", amount=1),
            mayMoveAnyAdvancementsFromSelfToRezzedIce=True,
        )

    if cid == "mausolus":
        return base(
            c,
            subtypes=["code gate", "ap"],
            canAdvance=True,
            subroutines=[
                {
                    "id": "mausolus-gain",
                    "text": "Gain 1¢. If 3+ hosted advancement counters, instead gain 3¢.",
                    "effect": if_adv_gte(3, gain("corp", 3), gain("corp", 1)),
                },
                {
                    "id": "mausolus-net",
                    "text": "Do 1 net damage. If 3+ hosted advancement counters, instead do 3 net damage.",
                    "effect": if_adv_gte(3, net(3), net(1)),
                },
                {
                    "id": "mausolus-tag",
                    "text": (
                        "Give the Runner 1 tag. If 3+ hosted advancement counters, "
                        "instead give the Runner 1 tag and end the run."
                    ),
                    "effect": if_adv_gte(
                        3,
                        seq(do("give_tags", amount=1), etr()),
                        do("give_tags", amount=1),
                    ),
                },
            ],
        )

    if cid == "sapper":
        return base(
            c,
            subtypes=["sentry", "destroyer"],
            mustRevealWhenAccessedFromRd=True,
            skipOnAccessFromArchives=True,
            onAccess=do("force_encounter_accessed_ice"),
            subroutines=[
                {
                    "id": "sapper-trash-program",
                    "text": "Trash 1 installed program.",
                    "effect": do("trash_program", pick="choose"),
                },
            ],
        )

    if cid == "show-of-force":
        return base(
            c,
            subtypes=["security"],
            onScore=do("meat_damage", amount=2),
        )

    if cid == "enforced-curfew":
        return base(
            c,
            subtypes=["current"],
            lingerAsCurrent=True,
            currentTrashOnAgendaStolen=True,
            runnerHandSizeBonus=-1,
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
