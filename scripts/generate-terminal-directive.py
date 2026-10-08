#!/usr/bin/env python3
"""Generate Terminal Directive Cards (td) card JSON from pinned pack `td`.

Fetch: python3 scripts/nsg_catalog.py fetch td
Red Sand deluxe after Station One (floor v1.129.0 → v1.130.0).
EXPECTED=57 catalog / 43 new clears; 14 reprint skips.
Defer `tdc` (campaign scenarios) entirely — do not extract or clear tdc.
Follow NSG pack stripped_text (not IR-hint paraphrases).
Slug via spin_common.slugify (LLDS→llds, Skorpios…, K. P. Lynn→k-p-lynn).
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
    seq,
    slugify,
    write_manifest,
)

OUT = Path(__file__).resolve().parents[1] / "data" / "terminal-directive"
WAVE = "terminal-directive"
PACK = "td"
EXPECTED = 57

REPRINTS = {
    "steve-cambridge-master-grifter",
    "spear-phishing",
    "abagnale",
    "demara",
    "ayla-bios-rahim-simulant-specialist",
    "egret",
    "seidr-laboratories-destiny-defined",
    "successful-field-test",
    "marilyn-campaign",
    "mason-bellamy",
    "colossus",
    "hortum",
    "paper-trail",
    "ipo",
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
    require_during_run: bool = False,
    require_this_server: bool = False,
    require_encounter_subtype: str | None = None,
    require_pending_damage_types: list[str] | None = None,
    require_suffered_meat_damage_this_turn: bool = False,
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
    if require_encounter_subtype:
        ab["requireEncounterSubtype"] = require_encounter_subtype
    if require_pending_damage_types:
        ab["requirePendingDamageTypes"] = require_pending_damage_types
    if require_suffered_meat_damage_this_turn:
        ab["requireSufferedMeatDamageThisTurn"] = True
    return ab


def trace_sub(strength: int, on_success: dict, on_failure: dict | None = None) -> dict:
    action: dict = {"kind": "trace", "strength": strength, "onSuccess": on_success}
    if on_failure:
        action["onFailure"] = on_failure
    return {"op": "do", "action": action}


def map_card(c: dict) -> dict | None:
    cid = slugify(c["title"])
    if cid in REPRINTS:
        return None

    # --- Criminal ---
    if cid == "brute-force-hack":
        return base(
            c,
            subtypes=["double"],
            playCost=0,
            playCostX=True,
            playAdditionalClick=True,
            onPlay=do("brute_force_hack_derez_ice_rez_cost_lte_x"),
        )

    if cid == "syn-attack":
        return base(
            c,
            subtypes=["double"],
            playAdditionalClick=True,
            onPlay=do("syn_attack_corp_discard_2_or_draw_4"),
        )

    if cid == "polyhistor":
        return base(
            c,
            subtypes=["console"],
            unique=True,
            maxConsole=1,
            muBonus=1,
            link=1,
            polyhistorPassAllHqIceMayDrawForceCorpDraw=True,
        )

    if cid == "lustig":
        return base(
            c,
            subtypes=["icebreaker", "killer"],
            breaker={
                "breaksSubtype": "sentry",
                "strength": c.get("strength") or 1,
                "breakCredits": 1,
                "breakMaxSubs": 1,
                "pumpCredits": 3,
                "pumpStrength": 5,
            },
            paidAbilities=[
                paid(
                    "lustig-pump",
                    "3¢: +5 strength",
                    do("pump_strength", amount=5),
                    credits=3,
                    windows=["encounter_paw"],
                    usable_by_runner=True,
                ),
                paid(
                    "lustig-bypass",
                    "[trash]: Bypass the sentry you are encountering",
                    do("bypass_current_ice", requireSubtype="sentry"),
                    trash_self=True,
                    windows=["encounter_paw"],
                    usable_by_runner=True,
                    require_encounter_subtype="sentry",
                ),
            ],
        )

    if cid == "mammon":
        return base(
            c,
            subtypes=["icebreaker", "ai"],
            breaker={
                "breaksSubtype": "*",
                "strength": c.get("strength") or 0,
                "breakCredits": 0,
                "breakMaxSubs": 1,
                "breakViaPaidAbilityOnly": True,
                "pumpCredits": 2,
                "pumpStrength": 2,
            },
            onRunnerTurnBegin=may(
                do("mammon_spend_credits_place_power_counters"),
                label="Spend credits to place power counters",
                decline_side="runner",
            ),
            onDiscardPhaseEnd=do("remove_all_power_counters"),
            paidAbilities=[
                paid(
                    "mammon-break",
                    "Hosted power counter: Break 1 subroutine",
                    do("break_encounter_subroutine", maxSubs=1),
                    cost={"powerCounters": 1},
                    windows=["encounter_paw"],
                    usable_by_runner=True,
                ),
                paid(
                    "mammon-pump",
                    "2¢: +2 strength",
                    do("pump_strength", amount=2),
                    credits=2,
                    windows=["encounter_paw"],
                    usable_by_runner=True,
                ),
            ],
        )

    if cid == "charlatan":
        return base(
            c,
            subtypes=["virtual"],
            paidAbilities=[
                paid(
                    "charlatan-run",
                    "[click][click]: Run any server; first approach rezzed ice may pay strength to bypass",
                    do("charlatan_run_any_server"),
                    clicks=2,
                    usable_by_runner=True,
                ),
            ],
        )

    if cid == "maxwell-james":
        return base(
            c,
            subtypes=["connection"],
            link=1,
            maxwellJamesRequireAfterSuccessfulHqRunPaidWindow=True,
            paidAbilities=[
                paid(
                    "maxwell-james-derez",
                    "[trash]: Derez a piece of ice protecting a remote server",
                    do("maxwell_james_derez_remote_ice"),
                    trash_self=True,
                    windows=["runner_action_paw", "corp_action_paw"],
                    usable_by_runner=True,
                ),
            ],
        )

    # --- Shaper ---
    if cid == "careful-planning":
        return base(
            c,
            subtypes=["priority"],
            playRequiresFirstClick=True,
            onPlay=do("careful_planning_choose_remote_card_cannot_rez_this_turn"),
        )

    if cid == "deep-data-mining":
        return base(
            c,
            subtypes=["run"],
            runEvent={
                "servers": "rd",
                "bonusAccessUnusedMuCapped": 4,
            },
        )

    if cid == "llds-memory-diamond":
        return base(
            c,
            subtypes=["mod"],
            muBonus=1,
            link=1,
            handSizeBonus=1,
        )

    if cid == "ubax":
        return base(
            c,
            subtypes=["console"],
            unique=True,
            maxConsole=1,
            muBonus=1,
            onRunnerTurnBegin=draw("runner", 1),
        )

    if cid == "adept":
        return base(
            c,
            subtypes=["icebreaker", "fracter", "killer"],
            strengthBonusPerUnusedMu=1,
            breaker={
                "breaksSubtype": "sentry",
                "strength": c.get("strength") or 2,
                "breakCredits": 2,
                "breakMaxSubs": 1,
                "breakViaPaidAbilityOnly": True,
            },
            paidAbilities=[
                paid(
                    "adept-break",
                    "2¢: Break 1 sentry or barrier subroutine",
                    do("adept_break_sentry_or_barrier"),
                    credits=2,
                    windows=["encounter_paw"],
                    usable_by_runner=True,
                ),
            ],
        )

    if cid == "savant":
        return base(
            c,
            subtypes=["icebreaker", "killer", "decoder"],
            strengthBonusPerUnusedMu=1,
            breaker={
                "breaksSubtype": "sentry",
                "strength": c.get("strength") or 1,
                "breakCredits": 2,
                "breakMaxSubs": 1,
                "breakViaPaidAbilityOnly": True,
            },
            paidAbilities=[
                paid(
                    "savant-break",
                    "2¢: Break 1 sentry or 2 code gate subroutines",
                    do("savant_break_sentry_or_code_gates"),
                    credits=2,
                    windows=["encounter_paw"],
                    usable_by_runner=True,
                ),
            ],
        )

    if cid == "dhegdheer":
        return base(
            c,
            subtypes=["daemon"],
            daemonHost=True,
            daemonHostMaxMu=99,
            maxHostedCards=1,
            daemonHostInstallCreditDiscount=1,
        )

    if cid == "levy-advanced-research-lab":
        return base(
            c,
            subtypes=["location", "ritzy"],
            paidAbilities=[
                paid(
                    "levy-reveal",
                    "[click]: Reveal top 4 of stack; may add 1 program to grip; rest to bottom",
                    do("levy_advanced_research_lab_reveal"),
                    clicks=1,
                    usable_by_runner=True,
                ),
            ],
        )

    if cid == "laguna-velasco-district":
        return base(
            c,
            subtypes=["location", "ritzy"],
            unique=True,
            basicDrawBonus=1,
        )

    # --- Neutral runner ---
    if cid == "process-automation":
        return base(
            c,
            onPlay=seq(gain("runner", 2), draw("runner", 1)),
        )

    if cid == "officer-frank":
        return base(
            c,
            subtypes=["connection"],
            unique=True,
            paidAbilities=[
                paid(
                    "officer-frank-trash-hq",
                    "[trash], 1¢: Corp trashes 2 cards from HQ at random",
                    do("corp_discard_random_from_hq", amount=2),
                    trash_self=True,
                    credits=1,
                    usable_by_runner=True,
                    require_suffered_meat_damage_this_turn=True,
                ),
            ],
        )

    if cid == "dean-lister":
        return base(
            c,
            subtypes=["connection"],
            unique=True,
            paidAbilities=[
                paid(
                    "dean-lister-boost",
                    "[trash]: Choose an icebreaker; +1 strength per grip card until end of run",
                    do("dean_lister_boost_icebreaker"),
                    trash_self=True,
                    windows=["runner_action_paw", "encounter_paw", "approach_paw"],
                    usable_by_runner=True,
                    require_during_run=True,
                ),
            ],
        )

    if cid == "biometric-spoofing":
        return base(
            c,
            paidAbilities=[
                paid(
                    "biometric-spoofing-prevent",
                    "[interrupt] → [trash]: Prevent 2 damage",
                    do("prevent_pending_damage", amount=2),
                    trash_self=True,
                    windows=["damage_interrupt_paw"],
                    usable_by_runner=True,
                ),
            ],
        )

    if cid == "the-shadow-net":
        return base(
            c,
            subtypes=["virtual"],
            unique=True,
            paidAbilities=[
                paid(
                    "shadow-net-play",
                    "[click], forfeit an agenda: Play an event from your heap, ignoring all costs",
                    do("the_shadow_net_play_event_from_heap"),
                    clicks=1,
                    cost={"forfeitAgenda": True},
                    usable_by_runner=True,
                ),
            ],
        )

    # --- Haas-Bioroid ---
    if cid == "brain-rewiring":
        return base(
            c,
            subtypes=["security"],
            onScore=may(
                do("brain_rewiring_spend_credits_force_bottom_draw"),
                label="Spend credits; Runner bottoms that many then draws 1",
                decline_side="corp",
            ),
        )

    if cid == "elective-upgrade":
        return base(
            c,
            subtypes=["initiative"],
            onScore=do("add_agenda_counter", amount=2),
            paidAbilities=[
                paid(
                    "elective-upgrade-clicks",
                    "[click], hosted agenda counter: Gain [click][click]",
                    do("gain_clicks", side="corp", amount=2),
                    clicks=1,
                    cost={"agendaCounters": 1},
                    once_per_turn=True,
                ),
            ],
        )

    if cid == "estelle-moon":
        return base(
            c,
            subtypes=["executive"],
            unique=True,
            placePowerCounterOnInstallCardInRemoteRoot=True,
            paidAbilities=[
                paid(
                    "estelle-moon-cash",
                    "[trash]: For each power counter, gain 2¢ and draw 1 card",
                    do("estelle_moon_trash_per_power"),
                    trash_self=True,
                ),
            ],
        )

    if cid == "eli-2-0":
        return base(
            c,
            subtypes=["barrier", "bioroid"],
            bioroidBreakMaxSubs=2,
            subroutines=[
                {
                    "id": "eli-2-0-draw",
                    "text": "You may draw 1 card.",
                    "effect": may(draw("corp", 1), label="Draw 1", decline_side="corp"),
                },
                {
                    "id": "eli-2-0-etr-1",
                    "text": "End the run.",
                    "effect": etr(),
                },
                {
                    "id": "eli-2-0-etr-2",
                    "text": "End the run.",
                    "effect": etr(),
                },
            ],
        )

    if cid == "executive-functioning":
        return base(
            c,
            subtypes=["code gate", "ap"],
            subroutines=[
                {
                    "id": "executive-functioning-trace",
                    "text": "Trace[4]. If successful, do 1 core damage.",
                    "effect": trace_sub(4, core(1)),
                },
            ],
        )

    if cid == "holmegaard":
        return base(
            c,
            subtypes=["sentry", "tracer", "destroyer"],
            subroutines=[
                {
                    "id": "holmegaard-trace",
                    "text": "Trace[4]. If successful, the Runner cannot access cards or breach the attacked server for the remainder of this run.",
                    "effect": trace_sub(
                        4, do("holmegaard_forbid_access_and_breach_this_run")
                    ),
                },
                {
                    "id": "holmegaard-trash-breaker",
                    "text": "Trash 1 installed icebreaker.",
                    "effect": do("holmegaard_trash_installed_icebreaker"),
                },
            ],
        )

    if cid == "tapestry":
        return base(
            c,
            subtypes=["code gate"],
            subroutines=[
                {
                    "id": "tapestry-lose-click",
                    "text": "The Runner loses [click], if able.",
                    "effect": do("lose_clicks", side="runner", amount=1),
                },
                {
                    "id": "tapestry-corp-draw",
                    "text": "The Corp may draw 1 card.",
                    "effect": may(draw("corp", 1), label="Draw 1", decline_side="corp"),
                },
                {
                    "id": "tapestry-hq-to-rd",
                    "text": "The Corp may add 1 card from HQ to the top of R&D.",
                    "effect": may(
                        do("hq_to_top_rd", pick="choose"),
                        label="Add 1 from HQ to top of R&D",
                        decline_side="corp",
                    ),
                },
            ],
        )

    if cid == "ultraviolet-clearance":
        return base(
            c,
            subtypes=["transaction", "double"],
            playAdditionalClicks=2,
            onPlay=seq(
                gain("corp", 10),
                draw("corp", 4),
                may(
                    do("may_install_from_hq_paying_costs"),
                    label="Install 1 card from HQ",
                    decline_side="corp",
                ),
            ),
        )

    if cid == "black-level-clearance":
        return base(
            c,
            subtypes=["security protocol"],
            onSuccessfulRunThisServer=do("black_level_clearance_core_or_jack_out"),
        )

    # --- Weyland ---
    if cid == "skorpios-defense-systems-persuasive-power":
        return base(
            c,
            subtypes=["subsidiary"],
            skorpiosRfgOneTrashedRunnerCardOncePerTurn=True,
        )

    if cid == "armored-servers":
        return base(
            c,
            subtypes=["security"],
            onScore=do("add_agenda_counter", amount=1),
            paidAbilities=[
                paid(
                    "armored-servers-activate",
                    "Hosted agenda counter: Remainder of run, trash 1 grip as additional cost to jack out or break a subroutine",
                    do("armored_servers_activate_this_run"),
                    cost={"agendaCounters": 1},
                    windows=[
                        "corp_action_paw",
                        "approach_paw",
                        "encounter_paw",
                        "approach_server_paw",
                    ],
                    require_during_run=True,
                ),
            ],
        )

    if cid == "illicit-sales":
        return base(
            c,
            subtypes=["expansion"],
            onScore=seq(
                may(
                    do("give_bad_publicity", amount=1),
                    label="Take 1 bad publicity",
                    decline_side="corp",
                ),
                do(
                    "gain_credits",
                    side="corp",
                    amount=0,
                    tally={"count": "bad_publicity", "per": 3, "side": "corp"},
                ),
            ),
        )

    if cid == "graft":
        return base(
            c,
            onScore=may(
                do("search_rd_to_hq", amount=3),
                label="Search R&D for up to 3 cards",
                decline_side="corp",
            ),
        )

    if cid == "illegal-arms-factory":
        return base(
            c,
            subtypes=["facility"],
            onTurnBegin=seq(gain("corp", 1), draw("corp", 1)),
            onTrashWhileRezzedTakeBadPublicity=1,
        )

    if cid == "mr-stone":
        return base(
            c,
            subtypes=["executive"],
            unique=True,
            meatDamageWhenRunnerTakesTags=1,
        )

    if cid == "bloodletter":
        return base(
            c,
            subtypes=["sentry", "destroyer"],
            subroutines=[
                {
                    "id": "bloodletter-trash",
                    "text": "The Runner must trash either 1 installed program or the top 2 cards of the stack.",
                    "effect": do("bloodletter_trash_program_or_top_2_stack"),
                },
            ],
        )

    if cid == "hailstorm":
        return base(
            c,
            subtypes=["barrier"],
            subroutines=[
                {
                    "id": "hailstorm-rfg",
                    "text": "Remove a card in the heap from the game.",
                    "effect": do("rfg_heap_card"),
                },
                {
                    "id": "hailstorm-etr",
                    "text": "End the run.",
                    "effect": etr(),
                },
            ],
        )

    if cid == "hunter-seeker":
        return base(
            c,
            subtypes=["gray ops", "double"],
            playAdditionalClick=True,
            playOnlyIfRunnerStoleAgendaLastTurn=True,
            onPlay=do("hunter_seeker_trash_installed"),
        )

    if cid == "k-p-lynn":
        return base(
            c,
            subtypes=["executive"],
            unique=True,
            onPassAllIceProtectingServer=do("k_p_lynn_tag_or_end_the_run"),
        )

    # --- Neutral corp ---
    if cid == "honeyfarm":
        return base(
            c,
            mustRevealWhenAccessedFromRd=True,
            onAccess=do("lose_credits", side="runner", amount=1),
        )

    if cid == "long-term-investment":
        return base(
            c,
            onTurnBegin=do("place_hosted_credits", amount=2),
            longTermInvestmentGainAbilityAtHostedCredits=8,
            paidAbilities=[
                paid(
                    "lti-take",
                    "[click]: Take any number of credits from Long-Term Investment",
                    do("long_term_investment_take_any_hosted_credits"),
                    clicks=1,
                ),
            ],
        )

    if cid == "weir":
        return base(
            c,
            subtypes=["code gate"],
            subroutines=[
                {
                    "id": "weir-lose-click",
                    "text": "The Runner loses [click].",
                    "effect": do("lose_clicks", side="runner", amount=1),
                },
                {
                    "id": "weir-trash-grip",
                    "text": "The Runner trashes 1 card from their grip.",
                    "effect": do("weir_trash_one_from_grip"),
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
    if set(skipped) != REPRINTS:
        print("REPRINT_MISMATCH skipped=" + json.dumps(sorted(skipped)))
        print("REPRINT_MISMATCH expected=" + json.dumps(sorted(REPRINTS)))
        sys.exit(1)


if __name__ == "__main__":
    main()
