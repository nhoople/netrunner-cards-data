#!/usr/bin/env python3
"""Generate Order and Chaos (oac) card JSON from pinned pack `oac`.

Fetch: python3 scripts/nsg_catalog.py fetch oac
Deluxe after The Source / Lunar (floor v1.107.0 → v1.108.0).
All 55 cards are new clears (0 reprints).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from nsg_catalog import load_pack_cards
from spin_common import (
    base,
    breaker_card,
    do,
    draw,
    etr,
    gain,
    net,
    seq,
    slugify,
    write_manifest,
)

OUT = Path(__file__).resolve().parents[1] / "data" / "order-and-chaos"
WAVE = "order-and-chaos"
PACK = "oac"
EXPECTED = 55

REPRINTS: set[str] = set()

DECLINE = {
    "id": "decline",
    "label": "Decline",
    "effect": gain("corp", 0),
}


def choose(chooser: str, options: list[dict]) -> dict:
    return {"op": "choose", "chooser": chooser, "options": options}


def may(effect: dict, label: str = "Accept", decline_side: str = "corp") -> dict:
    return choose(
        decline_side if decline_side in ("corp", "runner") else "corp",
        [
            {"id": "accept", "label": label, "effect": effect},
            {
                "id": "decline",
                "label": "Decline",
                "effect": gain(decline_side if decline_side in ("corp", "runner") else "corp", 0),
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
    return ab


def space_ice(c: dict, **extra) -> dict:
    """Asteroid Belt / Wormhole / Nebula / Orion advanceable rez-discount ice."""
    return base(
        c,
        canAdvance=True,
        rezCostReductionPerAdvancement=3,
        **extra,
    )


def map_card(c: dict) -> dict | None:
    cid = slugify(c["title"])
    if cid in REPRINTS:
        return None

    # --- Corp identities ---
    if cid == "argus-security-protection-guaranteed":
        return base(
            c,
            onAgendaStolen=choose(
                "runner",
                [
                    {
                        "id": "tag",
                        "label": "Take 1 tag",
                        "effect": do("give_tags", amount=1),
                    },
                    {
                        "id": "meat",
                        "label": "Suffer 2 meat damage",
                        "effect": do("meat_damage", amount=2),
                    },
                ],
            ),
        )

    if cid == "gagarin-deep-space-expanding-the-horizon":
        return base(c, additionalCreditsToAccessRemoteRoot=1)

    if cid == "titan-transnational-investing-in-your-future":
        return base(
            c,
            onAgendaScored=may(
                do("add_agenda_counter", amount=1),
                label="Place 1 agenda counter on the scored agenda",
            ),
        )

    # --- Agendas ---
    if cid == "firmware-updates":
        return base(
            c,
            onScore=do("add_agenda_counter", amount=3),
            paidAbilitiesOncePerTurn=True,
            paidAbilities=[
                paid(
                    "firmware-advance",
                    "Hosted agenda counter: Place 1 advancement on advanceable ice",
                    do("firmware_place_advancement_on_advanceable_ice"),
                    cost={"agendaCounters": 1},
                    windows=["corp_action_paw"],
                    once_per_turn=True,
                )
            ],
        )

    if cid == "glenn-station":
        return base(
            c,
            maxHostedCards=1,
            paidAbilities=[
                paid(
                    "glenn-host",
                    "[click]: Host a card from HQ facedown on Glenn Station",
                    do("glenn_host_from_hq"),
                    clicks=1,
                ),
                paid(
                    "glenn-retrieve",
                    "[click]: Add a card on Glenn Station to HQ",
                    do("glenn_retrieve_to_hq"),
                    clicks=1,
                ),
            ],
        )

    if cid == "government-takeover":
        return base(
            c,
            unique=True,
            paidAbilities=[
                paid(
                    "gov-takeover-credits",
                    "[click]: Gain 3[credit]",
                    gain("corp", 3),
                    clicks=1,
                )
            ],
        )

    if cid == "high-risk-investment":
        return base(
            c,
            onScore=do("add_agenda_counter", amount=1),
            paidAbilities=[
                paid(
                    "hri-cash",
                    "[click], hosted agenda counter: Gain 1¢ per Runner credit",
                    do("gain_credits_equal_to_runner_credits"),
                    clicks=1,
                    cost={"clicks": 1, "agendaCounters": 1},
                )
            ],
        )

    # --- Assets ---
    if cid == "constellation-protocol":
        return base(
            c,
            onTurnBegin=may(
                do("constellation_move_advancement_between_ice"),
                label="Move an advancement token between ice",
            ),
        )

    if cid == "mark-yale":
        return base(
            c,
            unique=True,
            gainCreditsOnSpendAgendaCounter=1,
            paidAbilities=[
                paid(
                    "mark-yale-trash",
                    "[trash]: Gain 2[credit]",
                    gain("corp", 2),
                    trash_self=True,
                    windows=["corp_action_paw"],
                ),
                paid(
                    "mark-yale-agenda",
                    "Any agenda counter: Gain 2[credit]",
                    do("mark_yale_spend_any_agenda_counter_gain_2"),
                    windows=["corp_action_paw"],
                ),
            ],
        )

    if cid == "space-camp":
        return base(
            c,
            mustRevealWhenAccessedFromRd=True,
            onAccess=may(
                do("place_advancement_on_advanceable_installed"),
                label="Place 1 advancement on an advanceable installed card",
            ),
        )

    if cid == "the-board":
        return base(
            c,
            unique=True,
            agendaPointsModifierInRunnerScoreArea=-1,
            onTrashWhileAccessed=do(
                "add_to_runner_score_as_agenda", agendaPoints=2
            ),
        )

    # --- Ice ---
    if cid == "asteroid-belt":
        return space_ice(
            c,
            subtypes=["barrier"],
            subroutines=[
                {
                    "id": "asteroid-etr",
                    "text": "End the run.",
                    "effect": etr(),
                }
            ],
        )

    if cid == "wormhole":
        return space_ice(
            c,
            subtypes=["code gate"],
            subroutines=[
                {
                    "id": "wormhole-resolve",
                    "text": "Resolve a subroutine on another piece of rezzed ice.",
                    "effect": do("may_resolve_subroutine_on_rezzed_ice"),
                }
            ],
        )

    if cid == "nebula":
        return space_ice(
            c,
            subtypes=["sentry", "destroyer"],
            subroutines=[
                {
                    "id": "nebula-trash",
                    "text": "Trash 1 program.",
                    "effect": do("trash_program", pick="choose"),
                }
            ],
        )

    if cid == "orion":
        return space_ice(
            c,
            unique=True,
            subtypes=["sentry", "code gate", "barrier"],
            subroutines=[
                {
                    "id": "orion-trash",
                    "text": "Trash 1 program.",
                    "effect": do("trash_program", pick="choose"),
                },
                {
                    "id": "orion-resolve",
                    "text": "Resolve a subroutine on another piece of rezzed ice.",
                    "effect": do("may_resolve_subroutine_on_rezzed_ice"),
                },
                {
                    "id": "orion-etr",
                    "text": "End the run.",
                    "effect": etr(),
                },
            ],
        )

    if cid == "builder":
        return base(
            c,
            subtypes=["code gate"],
            paidAbilities=[
                paid(
                    "builder-move",
                    "[click]: Move this ice to the outermost position of any server",
                    do("move_to_outermost"),
                    clicks=1,
                )
            ],
            subroutines=[
                {
                    "id": "builder-adv-1",
                    "text": "Place 1 advancement on ice protecting this server that can be advanced.",
                    "effect": do("place_advancement_on_advanceable_ice_protecting_this_server"),
                },
                {
                    "id": "builder-adv-2",
                    "text": "Place 1 advancement on ice protecting this server that can be advanced.",
                    "effect": do("place_advancement_on_advanceable_ice_protecting_this_server"),
                },
            ],
        )

    if cid == "checkpoint":
        return base(
            c,
            subtypes=["code gate", "tracer", "liability"],
            badPublicityOnRez=1,
            subroutines=[
                {
                    "id": "checkpoint-trace",
                    "text": "Trace[5]. If successful, do 3 meat damage when this run becomes successful.",
                    "effect": do(
                        "trace",
                        strength=5,
                        onSuccess=do(
                            "checkpoint_schedule_meat_on_successful_run",
                            amount=3,
                        ),
                    ),
                }
            ],
        )

    if cid == "fire-wall":
        return base(
            c,
            subtypes=["barrier"],
            canAdvance=True,
            strengthPerAdvancement=1,
            subroutines=[
                {
                    "id": "firewall-etr",
                    "text": "End the run.",
                    "effect": etr(),
                }
            ],
        )

    if cid == "searchlight":
        return base(
            c,
            subtypes=["sentry", "tracer", "observer"],
            canAdvance=True,
            subroutines=[
                {
                    "id": "searchlight-trace-1",
                    "text": "Trace[X]. If successful, give the Runner 1 tag. X = advancements.",
                    "effect": do(
                        "trace_strength_equal_source_advancements",
                        onSuccess=do("give_tags", amount=1),
                    ),
                },
                {
                    "id": "searchlight-trace-2",
                    "text": "Trace[X]. If successful, give the Runner 1 tag. X = advancements.",
                    "effect": do(
                        "trace_strength_equal_source_advancements",
                        onSuccess=do("give_tags", amount=1),
                    ),
                },
            ],
        )

    # --- Operations ---
    if cid == "housekeeping":
        return base(
            c,
            lingerAsCurrent=True,
            currentTrashOnAgendaStolen=True,
            firstRunnerInstallTrashFromGripEachTurn=True,
        )

    if cid == "patch":
        return base(
            c,
            onPlay=do("host_on_ice_as_condition"),
            hostStrengthModifier=2,
        )

    if cid == "traffic-accident":
        return base(
            c,
            playRequiresMinTags=2,
            onPlay=do("meat_damage", amount=2),
        )

    if cid == "sub-boost":
        return base(
            c,
            onPlay=do("host_on_ice_as_condition"),
            hostGainsBarrierAndEtrSubroutine=True,
        )

    # --- Upgrades ---
    if cid == "satellite-grid":
        return base(
            c,
            subtypes=["region"],
            iceProtectingThisServerAdditionalAdvancementTokens=1,
        )

    if cid == "the-twins":
        return base(
            c,
            unique=True,
            onPassRezzedIceProtectingThisServer=may(
                do("twins_trash_hq_copy_reencounter"),
                label="Reveal and trash a copy from HQ; Runner encounters again",
            ),
        )

    if cid == "dedicated-technician-team":
        return base(
            c,
            recurringCreditsMax=2,
            recurringSpendFor=["install_ice_this_server"],
        )

    if cid == "cyberdex-virus-suite":
        return base(
            c,
            mustRevealWhenAccessedFromRd=True,
            onAccess=may(
                do("purge_virus_counters"),
                label="Purge virus counters",
            ),
            paidAbilities=[
                paid(
                    "cvs-purge",
                    "[trash]: Purge virus counters",
                    do("purge_virus_counters"),
                    trash_self=True,
                    windows=["corp_action_paw", "approach_paw", "encounter_paw"],
                )
            ],
        )

    # --- Runner identities ---
    if cid == "edward-kim-humanitys-hammer":
        return base(c, firstAccessedOperationTrashFreeEachTurn=True)

    if cid == "maxx-maximum-punk-rock":
        return base(
            c,
            onTurnBegin=seq(
                do("trash_top_of_stack"),
                do("trash_top_of_stack"),
                draw("runner", 1),
            ),
        )

    if cid == "valencia-estevez-the-angel-of-cayambe":
        return base(c, corpStartsWithBadPublicity=1)

    # --- Events ---
    if cid == "amped-up":
        return base(
            c,
            onPlay=seq(
                do("gain_clicks", side="runner", amount=3),
                do("core_damage", amount=1, cannotPrevent=True),
            ),
        )

    if cid == "ive-had-worse":
        return base(
            c,
            onPlay=draw("runner", 3),
            onTrashFromGripOrStack=draw("runner", 3),
        )

    if cid == "itinerant-protesters":
        return base(
            c,
            lingerAsCurrent=True,
            currentTrashOnAgendaScored=True,
            corpHandSizeBonusPerBadPublicity=-1,
        )

    if cid == "showing-off":
        return base(
            c,
            runEvent={
                "servers": "rd",
                "accessFromBottomOfRd": True,
            },
        )

    if cid == "wanton-destruction":
        return base(
            c,
            runEvent={
                "servers": "hq",
                "onSuccessfulRun": do("wanton_destruction_instead_of_breach"),
            },
        )

    if cid == "day-job":
        return base(
            c,
            playAdditionalClicks=3,
            onPlay=gain("runner", 10),
        )

    if cid == "forked":
        return base(
            c,
            runEvent={
                "servers": "any",
                "trashFirstFullyBrokenSubtype": "sentry",
            },
        )

    if cid == "knifed":
        return base(
            c,
            runEvent={
                "servers": "any",
                "trashFirstFullyBrokenSubtype": "barrier",
            },
        )

    if cid == "spooned":
        return base(
            c,
            runEvent={
                "servers": "any",
                "trashFirstFullyBrokenSubtype": "code gate",
            },
        )

    if cid == "uninstall":
        return base(
            c,
            onPlay=do("uninstall_program_or_hardware_to_grip"),
        )

    # --- Programs ---
    if cid == "eater":
        card = base(c, subtypes=["icebreaker", "ai"])
        card["breaker"] = {
            "breaksSubtype": "*",
            "strength": 2,
            "breakCredits": 1,
            "breakMaxSubs": 1,
            "pumpCredits": 1,
            "pumpStrength": 1,
            "breakPreventsCardAccessForRun": True,
        }
        return card

    if cid == "gravedigger":
        return base(
            c,
            subtypes=["virus"],
            placeVirusCounterWhenInstalledCorpCardTrashed=True,
            paidAbilities=[
                paid(
                    "gravedigger-mill",
                    "[click], hosted virus counter: Corp trashes top of R&D",
                    do("trash_top_of_rd"),
                    clicks=1,
                    cost={"clicks": 1, "virusCounters": 1},
                    windows=["runner_action_paw"],
                    usable_by_runner=True,
                )
            ],
        )

    if cid == "hivemind":
        return base(
            c,
            unique=True,
            subtypes=["virus"],
            onInstall=do("add_virus_counter", amount=1),
            hivemindSharesVirusCounters=True,
        )

    if cid == "progenitor":
        return base(
            c,
            subtypes=["daemon"],
            daemonHost=True,
            daemonHostMaxMu=99,
            maxHostedCards=1,
            daemonHostVirusProgramsOnly=True,
            hostedIcebreakerMemoryDoesNotCount=True,
            preventOneVirusPurgeOnHostedProgram=True,
        )

    # --- Hardware ---
    if cid == "archives-interface":
        return base(
            c,
            archivesAccessMayRfgInstead={"oncePerArchivesBreach": True},
        )

    if cid == "chop-bot-3000":
        return base(
            c,
            unique=True,
            onTurnBegin=may(
                do("chop_bot_trash_installed_then_draw_or_remove_tag"),
                label="Trash another installed card",
                decline_side="runner",
            ),
        )

    if cid == "memstrips":
        return base(
            c,
            subtypes=["chip"],
            muBonus=3,
            muBonusOnlyForVirusPrograms=True,
        )

    if cid == "vigil":
        return base(
            c,
            unique=True,
            subtypes=["console"],
            maxConsole=1,
            muBonus=1,
            onTurnBegin=do("draw_if_hq_full"),
        )

    if cid == "qianju-pt":
        return base(
            c,
            subtypes=["vehicle"],
            onTurnBegin=may(
                do("qianju_lose_click_prevent_tag_until_next_turn"),
                label="Lose [click]: prevent 1 tag until your next turn",
                decline_side="runner",
            ),
        )

    # --- Resources ---
    if cid == "human-first":
        return base(
            c,
            unique=True,
            onAgendaScoredOrStolen=do(
                "gain_credits_equal_to_agenda_points_of_trigger"
            ),
        )

    if cid == "investigative-journalism":
        return base(
            c,
            installRequiresCorpBadPublicityGte=1,
            paidAbilities=[
                paid(
                    "ij-bp",
                    "[click]×4, [trash]: Give the Corp 1 bad publicity",
                    do("give_bad_publicity", amount=1),
                    clicks=4,
                    trash_self=True,
                    windows=["runner_action_paw"],
                    usable_by_runner=True,
                )
            ],
        )

    if cid == "sacrificial-clone":
        return base(
            c,
            paidAbilities=[
                {
                    "id": "sac-clone-prevent",
                    "label": "[interrupt] → [trash]: Prevent all damage",
                    "clickCost": 0,
                    "creditCost": 0,
                    "cost": {"trashSelf": True},
                    "windows": ["damage_interrupt_paw"],
                    "effect": do("prevent_all_damage"),
                }
            ],
        )

    if cid == "stim-dealer":
        return base(
            c,
            onTurnBegin=do("stim_dealer_turn_begin"),
        )

    if cid == "virus-breeding-ground":
        return base(
            c,
            subtypes=["virtual"],
            onTurnBegin=do("add_virus_counter", amount=1),
            paidAbilities=[
                paid(
                    "vbg-move",
                    "[click]: Move 1 virus counter to another card with a virus counter",
                    do("move_counter"),
                    clicks=1,
                    windows=["runner_action_paw"],
                    usable_by_runner=True,
                )
            ],
        )

    if cid == "data-folding":
        return base(
            c,
            subtypes=["virtual"],
            onTurnBegin=do("gain_if_unused_mu_gte", amount=1, threshold=2),
        )

    card = base(c)
    card["unsupported"] = [f"Unmapped oac card: {cid}"]
    return card


def main():
    pack = sorted(load_pack_cards(PACK), key=lambda c: c.get("position", 0))
    assert len(pack) == EXPECTED, len(pack)
    OUT.mkdir(parents=True, exist_ok=True)
    written: list[str] = []
    skipped: list[str] = []
    for c in pack:
        cid = slugify(c["title"])
        mapped = map_card(c)
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
    if len(clear_written) != EXPECTED:
        missing = [cid for cid in written if cid not in clear_written]
        print("UNCLEARED=" + json.dumps(missing))
        sys.exit(1)


if __name__ == "__main__":
    main()
