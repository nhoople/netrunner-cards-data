#!/usr/bin/env python3
"""Generate 23 Seconds (23s) card JSON from pinned pack `23s`.

Fetch: python3 scripts/nsg_catalog.py fetch 23s
Flashpoint #1 after Fear the Masses (floor v1.121.0 → v1.122.0).
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

OUT = Path(__file__).resolve().parents[1] / "data" / "twenty-three-seconds"
WAVE = "twenty-three-seconds"
PACK = "23s"
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
    credits_from_stealth_only: bool = False,
) -> dict:
    c = dict(cost or {})
    if clicks:
        c["clicks"] = clicks
    if credits:
        c["credits"] = credits
    if trash_self:
        c["trashSelf"] = True
    if credits_from_stealth_only:
        c["creditsFromStealthOnly"] = True
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


def trace_sub(strength: int, on_success, on_failure=None) -> dict:
    action: dict = {"kind": "trace", "strength": strength, "onSuccess": on_success}
    if on_failure is not None:
        action["onFailure"] = on_failure
    return {"op": "do", "action": action}


def map_card(c: dict) -> dict | None:
    cid = slugify(c["title"])
    if cid in REPRINTS:
        return None

    if cid == "system-outage":
        return base(
            c,
            subtypes=["current"],
            lingerAsCurrent=True,
            currentTrashOnAgendaScored=True,
            corpLosesCreditsOnNonFirstDrawThisTurn=1,
        )

    if cid == "null-whistleblower":
        return base(
            c,
            subtypes=["natural"],
            link=c.get("base_link", 0),
            onEncounterAnyIceOncePerTurn=may(
                do("null_trash_grip_lower_encountered_ice_strength", amount=2),
                label="Trash 1 from grip: encountered ice gets −2 strength this run",
            ),
        )

    if cid == "gpi-net-tap":
        return base(
            c,
            mayExposeApproachedIceThenMayTrashSelfToJackOut=True,
        )

    if cid == "hernando-cortez":
        return base(
            c,
            subtypes=["connection"],
            unique=True,
            additionalIceRezCostEqualToSubroutineCountWhenCorpCreditsGte=10,
        )

    if cid == "mirror":
        return base(
            c,
            subtypes=["console"],
            unique=True,
            muBonus=2,
            maxConsole=1,
            onSuccessfulRdRunMayReplaceSpentRecurringCredit=True,
        )

    if cid == "dai-v":
        return base(
            c,
            subtypes=["icebreaker", "ai"],
            memoryCost=1,
            breaker={
                "breaksSubtype": "*",
                "strength": 1,
                "breakCredits": 2,
                "breakMaxSubs": 99,
                "pumpCredits": 1,
                "pumpStrength": 1,
                "breakViaPaidAbilityOnly": True,
            },
            paidAbilities=[
                paid(
                    "dai-v-break",
                    "2¢ (stealth): Break all subroutines",
                    do("break_encounter_subroutine", maxSubs=99),
                    credits=2,
                    credits_from_stealth_only=True,
                    windows=["encounter_paw"],
                    usable_by_runner=True,
                ),
                paid(
                    "dai-v-pump",
                    "1¢: +1 strength",
                    do("pump_strength", amount=1),
                    credits=1,
                    windows=["encounter_paw"],
                    usable_by_runner=True,
                ),
            ],
        )

    if cid == "another-day-another-paycheck":
        return base(
            c,
            subtypes=["current"],
            lingerAsCurrent=True,
            currentTrashOnAgendaScored=True,
            onStealAgenda=do("another_day_force_corp_trace0_gain_ap_credits"),
        )

    if cid == "deuces-wild":
        return base(
            c,
            onPlay=do("deuces_wild_resolve_two"),
        )

    if cid == "injection-attack":
        return base(
            c,
            subtypes=["run"],
            onPlay=do("injection_attack_choose_breaker_run", strengthBonus=2),
        )

    if cid == "fairchild-1-0":
        return base(
            c,
            subtypes=["code gate", "bioroid"],
            bioroidBreakMaxSubs=1,
            subroutines=[
                {
                    "id": "fairchild-1-0-pay-or-trash-1",
                    "text": "The Runner must pay 1¢ or trash 1 of their installed cards.",
                    "effect": do(
                        "pay_credits_or_trash_installed",
                        side="runner",
                        amount=1,
                    ),
                },
                {
                    "id": "fairchild-1-0-pay-or-trash-2",
                    "text": "The Runner must pay 1¢ or trash 1 of their installed cards.",
                    "effect": do(
                        "pay_credits_or_trash_installed",
                        side="runner",
                        amount=1,
                    ),
                },
            ],
        )

    if cid == "sherlock-2-0":
        return base(
            c,
            subtypes=["sentry", "bioroid", "tracer"],
            bioroidBreakMaxSubs=2,
            subroutines=[
                {
                    "id": "sherlock-2-0-trace-1",
                    "text": "Trace[4]. If successful, add 1 installed program to the bottom of the Runner's stack.",
                    "effect": trace_sub(
                        4,
                        do("add_installed_program_to_stack_bottom"),
                    ),
                },
                {
                    "id": "sherlock-2-0-trace-2",
                    "text": "Trace[4]. If successful, add 1 installed program to the bottom of the Runner's stack.",
                    "effect": trace_sub(
                        4,
                        do("add_installed_program_to_stack_bottom"),
                    ),
                },
                {
                    "id": "sherlock-2-0-tag",
                    "text": "Give the Runner 1 tag.",
                    "effect": do("give_tags", amount=1),
                },
            ],
        )

    if cid == "hyoubu-research-facility":
        return base(
            c,
            subtypes=["facility"],
            unique=True,
            firstRevealSecretlySpentCreditsGainThatManyEachTurn=True,
        )

    if cid == "chrysalis":
        return base(
            c,
            subtypes=["sentry", "ap"],
            mustRevealWhenAccessedFromRd=True,
            skipOnAccessFromArchives=True,
            onAccess=do("force_encounter_accessed_ice"),
            subroutines=[
                {
                    "id": "chrysalis-net",
                    "text": "Do 2 net damage.",
                    "effect": net(2),
                }
            ],
        )

    if cid == "georgia-emelyov":
        return base(
            c,
            subtypes=["sysop"],
            unique=True,
            onUnsuccessfulRunOnThisServer=net(1),
            paidAbilities=[
                paid(
                    "georgia-move",
                    "2¢: Move Georgia Emelyov to another server",
                    do("move_source_upgrade_to_another_server_root"),
                    credits=2,
                    windows=["corp_action_paw"],
                )
            ],
        )

    if cid == "watchdog":
        return base(
            c,
            firstIceRezCostReductionPerRunnerTag=True,
        )

    if cid == "hard-hitting-news":
        return base(
            c,
            subtypes=["terminal"],
            endsActionPhase=True,
            playRequiresRunnerMadeRunLastTurn=True,
            onPlay=trace_sub(4, do("give_tags", amount=4)),
        )

    if cid == "nbn-controlling-the-message":
        return base(
            c,
            subtypes=["megacorp"],
            onFirstCorpCardTrashEachTurn=may(
                trace_sub(
                    4,
                    do("give_tags", amount=1, cannotBeAvoided=True),
                ),
                label="Trace[4]: give the Runner 1 tag (cannot be avoided)",
                decline_side="corp",
            ),
        )

    if cid == "crisis-management":
        return base(
            c,
            subtypes=["security"],
            onTurnBeginIfRunnerTagged=do("meat_damage", amount=1),
        )

    if cid == "stock-buy-back":
        return base(
            c,
            subtypes=["terminal", "transaction"],
            endsActionPhase=True,
            onPlay=do(
                "gain_credits",
                side="corp",
                amount=0,
                tally={"count": "runner_score", "per": 3, "side": "corp"},
            ),
        )

    if cid == "sandburg":
        return base(
            c,
            unique=True,
            iceStrengthBonusPerFiveCorpCreditsWhenCorpCreditsGte={
                "threshold": 10,
                "perCredits": 5,
                "bonus": 1,
            },
        )

    card = base(c)
    card["unsupported"] = [f"Unmapped 23s card: {cid}"]
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
