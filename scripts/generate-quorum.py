#!/usr/bin/env python3
"""Generate Quorum (qu) card JSON from pinned pack `qu`.

Fetch: python3 scripts/nsg_catalog.py fetch qu
Flashpoint #6 cycle closer after Martial Law (floor v1.126.0 → v1.127.0).
Reprint skips: none (20/20 new clears).
Follow NSG pack stripped_text (not IR-hint paraphrases).
Slug via spin_common.slugify against catalog titles (Şifr→sifr, Sūnya→sunya).
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

OUT = Path(__file__).resolve().parents[1] / "data" / "quorum"
WAVE = "quorum"
PACK = "qu"
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

    if cid == "sifr":
        return base(
            c,
            subtypes=["console"],
            unique=True,
            muBonus=2,
            sifrMayZeroEncounterIceStrengthOncePerTurn=True,
        )

    if cid == "sunya":
        return base(
            c,
            subtypes=["icebreaker", "killer"],
            memoryCost=1,
            strength=1,
            strengthPerPowerCounter=True,
            onFullyBreak=do("add_power_counter", amount=1),
            breaker={
                "breaksSubtype": "sentry",
                "strength": 1,
                "breakCredits": 2,
                "breakMaxSubs": 1,
            },
        )

    if cid == "recon-drone":
        return base(
            c,
            paidAbilities=[
                paid(
                    "recon-drone-prevent",
                    "[interrupt] → X¢, [trash]: Prevent X damage from a card you are accessing",
                    do("recon_drone_prevent_x_damage"),
                    cost={"trashSelf": True},
                    windows=["damage_interrupt_paw"],
                    usable_by_runner=True,
                ),
            ],
        )

    if cid == "tapwrm":
        return base(
            c,
            subtypes=["virus"],
            memoryCost=1,
            installRequiresSuccessfulCentralRunThisTurn=True,
            trashOnVirusPurge=True,
            onRunnerTurnBegin=do("tapwrm_gain_credits_per_corp_credits"),
        )

    if cid == "tracker":
        return base(
            c,
            memoryCost=2,
            onRunnerTurnBegin=may(
                do("choose_server_runner"),
                label="Choose a server",
                decline_side="runner",
            ),
            paidAbilities=[
                paid(
                    "tracker-run",
                    "[click], 2¢: Run the chosen server; prevent first subroutine that would resolve",
                    do("tracker_run_chosen_prevent_first_sub"),
                    clicks=1,
                    credits=2,
                    windows=["runner_action_paw"],
                    usable_by_runner=True,
                ),
            ],
        )

    if cid == "aaron-marron":
        return base(
            c,
            subtypes=["connection"],
            unique=True,
            onAgendaScoredOrStolen=do("add_power_counter", amount=2),
            paidAbilities=[
                paid(
                    "aaron-marron-tag-draw",
                    "Hosted power counter: Remove 1 tag and draw 1 card",
                    seq(do("remove_tags", amount=1), draw("runner", 1)),
                    cost={"powerCounters": 1},
                    windows=["runner_action_paw"],
                    usable_by_runner=True,
                ),
            ],
        )

    if cid == "encore":
        return base(
            c,
            playRequiresSuccessfulAllCentralsThisTurn=True,
            rfgInsteadOfTrashing=True,
            onPlay=do("schedule_additional_runner_turn"),
        )

    if cid == "fawkes":
        return base(
            c,
            subtypes=["icebreaker", "killer"],
            memoryCost=1,
            strength=1,
            breaker={
                "breaksSubtype": "sentry",
                "strength": 1,
                "breakCredits": 1,
                "breakMaxSubs": 1,
            },
            paidAbilities=[
                paid(
                    "fawkes-pump",
                    "X¢ (≥1 stealth): +X strength for the remainder of this run",
                    do("fawkes_spend_x_pump"),
                    cost={"minCreditsFromStealth": 1},
                    windows=["encounter_paw"],
                    usable_by_runner=True,
                ),
            ],
        )

    if cid == "peace-in-our-time":
        return base(
            c,
            subtypes=["priority"],
            playRequiresFirstClick=True,
            playRequiresCorpScoredNoAgendasLastTurn=True,
            onPlay=seq(
                gain("runner", 10),
                gain("corp", 5),
                do("forbid_runner_runs_this_turn"),
            ),
        )

    if cid == "sensor-net-activation":
        return base(
            c,
            subtypes=["security"],
            onScore=do("add_agenda_counter", amount=1),
            paidAbilities=[
                paid(
                    "sensor-net-rez",
                    "Hosted agenda counter: Rez a bioroid, ignoring all costs; derez at turn end",
                    do("sensor_net_rez_bioroid_ignoring_costs_derez_turn_end"),
                    cost={"agendaCounters": 1},
                    windows=["corp_action_paw", "runner_action_paw"],
                ),
            ],
        )

    if cid == "violet-level-clearance":
        return base(
            c,
            subtypes=["terminal", "transaction"],
            endsActionPhase=True,
            onPlay=seq(gain("corp", 8), draw("corp", 4)),
        )

    if cid == "chiyashi":
        return base(
            c,
            subtypes=["barrier", "ap"],
            trashTopOfStackOnBreakSubIfRunnerHasAi=2,
            subroutines=[
                {
                    "id": "chiyashi-net-1",
                    "text": "Do 2 net damage.",
                    "effect": net(2),
                },
                {
                    "id": "chiyashi-net-2",
                    "text": "Do 2 net damage.",
                    "effect": net(2),
                },
                {
                    "id": "chiyashi-etr",
                    "text": "End the run.",
                    "effect": etr(),
                },
            ],
        )

    if cid == "psychokinesis":
        return base(
            c,
            subtypes=["terminal"],
            endsActionPhase=True,
            onPlay=do("psychokinesis_look_top5_may_install_remote"),
        )

    if cid == "net-quarantine":
        return base(
            c,
            subtypes=["security"],
            firstTraceEachTurnRunnerLinkTreatedAs0=True,
            gainCreditsWhenRunnerSpendsForLinkPer2Spent=True,
        )

    if cid == "herald":
        return base(
            c,
            subtypes=["code gate"],
            mustRevealWhenAccessedFromRd=True,
            skipOnAccessFromArchives=True,
            onAccess=do("force_encounter_accessed_ice"),
            subroutines=[
                {
                    "id": "herald-gain",
                    "text": "Gain 2¢.",
                    "effect": gain("corp", 2),
                },
                {
                    "id": "herald-advance",
                    "text": "You may pay up to 2¢ to place that many advancement counters on 1 installed card you can advance.",
                    "effect": do("herald_pay_up_to_place_advancements", max=2),
                },
            ],
        )

    if cid == "veritas":
        return base(
            c,
            subtypes=["sentry", "tracer"],
            subroutines=[
                {
                    "id": "veritas-gain",
                    "text": "The Corp gains 2¢.",
                    "effect": gain("corp", 2),
                },
                {
                    "id": "veritas-lose",
                    "text": "The Runner loses 2¢.",
                    "effect": do("lose_credits", side="runner", amount=2),
                },
                {
                    "id": "veritas-trace",
                    "text": "Trace[2]. If successful, give the Runner 1 tag.",
                    "effect": trace_sub(2, do("give_tags", amount=1)),
                },
            ],
        )

    if cid == "bryan-stinson":
        return base(
            c,
            subtypes=["character"],
            unique=True,
            bryanStinsonPlayArchivesTransactionWhileRunnerLt6c=True,
        )

    if cid == "nasx":
        return base(
            c,
            unique=True,
            onTurnBegin=gain("corp", 1),
            nasxMaySpendUpTo2OnAbilityCreditGainToPlacePower=True,
            paidAbilities=[
                paid(
                    "nasx-cash-out",
                    "[click], [trash]: Gain 2¢ for each power counter on NASX",
                    do(
                        "gain_credits",
                        side="corp",
                        amount=0,
                        tally={
                            "count": "source_power_counters",
                            "per": 2,
                            "side": "source",
                        },
                    ),
                    clicks=1,
                    trash_self=True,
                    windows=["corp_action_paw"],
                ),
            ],
        )

    if cid == "macrophage":
        return base(
            c,
            subtypes=["code gate", "tracer"],
            subroutines=[
                {
                    "id": "macrophage-purge",
                    "text": "Trace[4]. If successful, purge virus counters.",
                    "effect": trace_sub(4, do("purge_virus_counters")),
                },
                {
                    "id": "macrophage-trash-virus",
                    "text": "Trace[3]. If successful, trash 1 virus.",
                    "effect": trace_sub(3, do("trash_installed_virus", pick="choose")),
                },
                {
                    "id": "macrophage-rfg-heap-virus",
                    "text": "Trace[2]. If successful, remove a virus in the heap from the game.",
                    "effect": trace_sub(2, do("rfg_virus_from_heap")),
                },
                {
                    "id": "macrophage-etr",
                    "text": "Trace[1]. If successful, end the run.",
                    "effect": trace_sub(1, etr()),
                },
            ],
        )

    if cid == "tribunal":
        return base(
            c,
            subtypes=["sentry"],
            subroutines=[
                {
                    "id": "tribunal-trash-1",
                    "text": "The Runner trashes 1 of their installed cards.",
                    "effect": do("trash_installed_runner", pick="choose"),
                },
                {
                    "id": "tribunal-trash-2",
                    "text": "The Runner trashes 1 of their installed cards.",
                    "effect": do("trash_installed_runner", pick="choose"),
                },
                {
                    "id": "tribunal-trash-3",
                    "text": "The Runner trashes 1 of their installed cards.",
                    "effect": do("trash_installed_runner", pick="choose"),
                },
            ],
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
