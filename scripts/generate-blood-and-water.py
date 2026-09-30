#!/usr/bin/env python3
"""Generate Blood and Water (baw) card JSON from pinned pack `baw`.

Fetch: python3 scripts/nrdb_catalog.py fetch baw
Red Sand #4 after Earth's Scion (floor v1.131.0 → v1.132.0).
Reprint skips: none (20/20 new clears).
Follow NRDB stripped_text (not IR-hint paraphrases).
Slug via spin_common.slugify (Māui→maui, Mirāju→miraju,
Alice Merchant: Clan Agitator→alice-merchant-clan-agitator,
Mass-Driver→mass-driver).
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

OUT = Path(__file__).resolve().parents[1] / "data" / "blood-and-water"
WAVE = "blood-and-water"
PACK = "baw"
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
    if require_during_run:
        ab["requireDuringRun"] = True
    if require_this_server:
        ab["requireThisServer"] = True
    return ab


def breaker(
    c: dict,
    *,
    breaks: str,
    break_credits: int,
    break_max: int = 1,
    pump_credits: int | None = None,
    pump_strength: int | None = None,
    **extra,
) -> dict:
    subtypes = []
    if c.get("keywords"):
        subtypes = [s.strip().lower() for s in c["keywords"].split(" - ")]
    card = base(c, subtypes=subtypes, **extra)
    br: dict = {
        "breaksSubtype": breaks,
        "strength": c.get("strength", 0),
        "breakCredits": break_credits,
        "breakMaxSubs": break_max,
    }
    if pump_credits is not None:
        br["pumpCredits"] = pump_credits
        br["pumpStrength"] = pump_strength if pump_strength is not None else 1
    card["breaker"] = br
    return card


def map_card(c: dict) -> dict | None:
    cid = slugify(c["title"])
    if cid in REPRINTS:
        return None

    if cid == "alice-merchant-clan-agitator":
        return base(
            c,
            subtypes=["cyborg"],
            onSuccessfulRunOncePerTurn=True,
            onSuccessfulRun={
                "op": "if",
                "cond": {"op": "attacking_archives"},
                "then": do("trash_hq", amount=1, pick="choose"),
            },
        )

    if cid == "jarogniew-mercs":
        prevent = paid(
            "jarogniew-prevent-meat",
            "[interrupt] → Hosted power counter: Prevent 1 meat damage",
            do("prevent_pending_damage", amount=1),
            cost={"powerCounters": 1},
            windows=["damage_interrupt_paw"],
        )
        prevent["requirePendingDamageTypes"] = ["meat"]
        return base(
            c,
            subtypes=["clan", "connection"],
            unique=True,
            onInstall=seq(
                do("give_tags", amount=1),
                do("jarogniew_load_power_equal_tags_plus_3"),
            ),
            trashWhenPowerEmpty=True,
            corpCannotTrashWhileOtherResourceInstalled=True,
            paidAbilities=[prevent],
        )

    if cid == "maui":
        return base(
            c,
            subtypes=["console"],
            unique=True,
            muBonus=2,
            recurringCreditsMaxEqualsIceProtectingHq=True,
            recurringSpendFor=["run_hq"],
        )

    if cid == "bug-out-bag":
        return base(
            c,
            installCost=0,
            installCostX=True,
            onInstall=do("bug_out_bag_choose_x_and_load_power"),
            onTurnEndIfGripEmptyDrawPerPowerThenTrash=True,
        )

    if cid == "keros-mcintyre":
        return base(
            c,
            subtypes=["connection"],
            unique=True,
            gainCreditsOnFirstDerezIceEachTurn=2,
        )

    if cid == "daredevil":
        return base(
            c,
            subtypes=["console"],
            unique=True,
            muBonus=2,
            drawOnFirstRunEachTurnIfServerIceGte={"ice": 2, "draw": 2},
        )

    if cid == "mass-driver":
        return breaker(
            c,
            breaks="code gate",
            break_credits=2,
            break_max=1,
            pump_credits=1,
            pump_strength=1,
            fullyBreakNextEncounterFirstNSubsDoNotResolve=3,
        )

    if cid == "warroid-tracker":
        return base(
            c,
            subtypes=["bioroid"],
            onRunnerTrashFromThisServerRootOrProtecting=do(
                "trace",
                strength=4,
                onSuccess=do("warroid_runner_trashes_installed", amount=2),
            ),
        )

    if cid == "loki":
        return base(
            c,
            subtypes=["bioroid"],
            unique=True,
            onEncounter=do("loki_choose_rezzed_ice_gain_subs_subtypes_for_run"),
            subroutines=[
                {
                    "id": "loki-etr-unless-shuffle-grip",
                    "text": "End the run unless the Runner shuffles all cards from the grip into the stack.",
                    "effect": do("end_the_run_unless_shuffle_grip_into_stack"),
                },
            ],
        )

    if cid == "obokata-protocol":
        return base(
            c,
            subtypes=["ambush"],
            stealAdditionalCost=net(4),
        )

    if cid == "miraju":
        return base(
            c,
            subtypes=["code gate", "deflector"],
            onEncounterEndIfPrintedSubroutineBroken=do(
                "miraju_move_archives_may_jack_out_derez"
            ),
            subroutines=[
                {
                    "id": "miraju-draw-shuffle",
                    "text": "You may draw 1 card. Then, shuffle 1 card from HQ into R&D.",
                    "effect": seq(
                        may(draw("corp", 1), label="Draw 1 card", decline_side="corp"),
                        do("shuffle_hq_to_rd", amount=1),
                    ),
                },
            ],
        )

    if cid == "shipment-from-tennin":
        return base(
            c,
            playRequiresNoSuccessfulRunLastTurn=True,
            onPlay=do("place_advancements", amount=2),
        )

    if cid == "escalate-vitriol":
        return base(
            c,
            subtypes=["initiative"],
            paidAbilities=[
                paid(
                    "escalate-vitriol-gain",
                    "Once per turn → [click]: Gain 1¢ for each tag the Runner has",
                    do("gain_credits_per_runner_tags", per=1),
                    clicks=1,
                    once_per_turn=True,
                ),
            ],
        )

    if cid == "reeducation":
        return base(
            c,
            subtypes=["initiative"],
            onScore=do("reeducation_hq_bottom_rd_draw_runner_grip_to_stack"),
        )

    if cid == "traffic-analyzer":
        return base(
            c,
            onRezIceProtectingThisServer=do(
                "trace",
                strength=2,
                onSuccess=gain("corp", 1),
            ),
        )

    if cid == "meteor-mining":
        return base(
            c,
            onScore=do("meteor_mining_may_gain_7_or_7_meat_if_tagged"),
        )

    if cid == "standoff":
        return base(
            c,
            onScore=do("standoff_trash_loop"),
        )

    if cid == "success":
        return base(
            c,
            subtypes=["triple"],
            playAdditionalClicks=2,
            playAdditionalCostForfeitAgenda=True,
            onPlay=do("success_advance_equal_forfeit_advancement_requirement"),
        )

    if cid == "whampoa-reclamation":
        return base(
            c,
            subtypes=["corporation"],
            paidAbilities=[
                paid(
                    "whampoa-reclaim",
                    "Once per turn → Trash 1 card from HQ: Add 1 card from Archives to the bottom of R&D",
                    do("whampoa_trash_hq_archives_to_rd_bottom"),
                    cost={"trashFromHq": 1},
                    once_per_turn=True,
                ),
            ],
        )

    if cid == "mass-commercialization":
        return base(
            c,
            subtypes=["transaction"],
            onPlay=do("gain_credits_per_card_with_advancement_tokens", per=2),
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
