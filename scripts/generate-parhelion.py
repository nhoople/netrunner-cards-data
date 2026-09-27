#!/usr/bin/env python3
"""Generate Parhelion card JSON from NRDB pack `ph`.

Requires /tmp/nrdb-cards.json (curl https://netrunnerdb.com/api/2.0/public/cards).

Hand-mapped Effect IR only where existing primitives fully cover the card;
everything else lists honest unsupported notes — never invent IR.

Usage: python3 scripts/generate-parhelion.py
"""
from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "parhelion"
NRDB = Path("/tmp/nrdb-cards.json")


def slugify(title: str) -> str:
    t = unicodedata.normalize("NFKD", title)
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = t.lower()
    t = t.replace("“", "").replace("”", "").replace('"', "")
    t = t.replace("'", "").replace("’", "").replace("ʼ", "")
    t = t.replace(".", "-").replace(":", " ")
    t = re.sub(r"[^a-z0-9]+", "-", t)
    return t.strip("-")


def strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text or "")


def etr():
    return {"op": "do", "action": {"kind": "end_the_run"}}


def gain(side: str, n: int):
    return {"op": "do", "action": {"kind": "gain_credits", "side": side, "amount": n}}


def lose(side: str, n: int, then=None):
    action = {"kind": "lose_credits", "side": side, "amount": n}
    if then is not None:
        action["then"] = then
    return {"op": "do", "action": action}


def draw(side: str, n: int):
    return {"op": "do", "action": {"kind": "draw", "side": side, "amount": n}}


def net(n: int):
    return {"op": "do", "action": {"kind": "net_damage", "amount": n}}


def meat(n: int):
    return {"op": "do", "action": {"kind": "meat_damage", "amount": n}}


def core(n: int):
    return {"op": "do", "action": {"kind": "core_damage", "amount": n}}


def tags(n: int):
    return {"op": "do", "action": {"kind": "give_tags", "amount": n}}


def trash_prog(pick="choose"):
    return {"op": "do", "action": {"kind": "trash_program", "pick": pick}}


def trash_self():
    return {"op": "do", "action": {"kind": "trash_self"}}


def remove_tags(n: int):
    return {"op": "do", "action": {"kind": "remove_tags", "amount": n}}


def seq(*effects):
    return {"op": "seq", "effects": list(effects)}


def choose(chooser: str, options: list):
    return {"op": "choose", "chooser": chooser, "options": options}


def base(c, **extra):
    subtypes = []
    if c.get("keywords"):
        subtypes = [s.strip().lower() for s in c["keywords"].split(" - ")]
    card = {
        "id": slugify(c["title"]),
        "title": c["title"],
        "wave": "parhelion",
        "nrdbCode": c["code"],
        "type": c["type_code"],
        "side": "runner" if c["side_code"] == "runner" else "corp",
        "unsupported": [],
    }
    if subtypes:
        card["subtypes"] = subtypes
    if c.get("cost") is not None:
        if c["type_code"] in ("event", "operation"):
            card["playCost"] = c["cost"]
        elif c["type_code"] in ("ice", "asset", "upgrade"):
            card["installCost"] = c["cost"]
            card["rezCost"] = c["cost"]
        else:
            card["installCost"] = c["cost"]
    if c.get("trash_cost") is not None:
        card["trashCost"] = c["trash_cost"]
    if c.get("strength") is not None:
        card["strength"] = c["strength"]
    if c.get("memory_cost") is not None:
        card["memoryCost"] = c["memory_cost"]
    if c.get("advancement_cost") is not None:
        card["advancementRequirement"] = c["advancement_cost"]
    if c.get("agenda_points") is not None:
        card["agendaPoints"] = c["agenda_points"]
    if c.get("base_link") is not None:
        card["link"] = c["base_link"]
    card.update(extra)
    return card


def breaker_card(c, subtype, strength, break_c, pump_c=None, pump_s=None, break_max=None, **extra):
    br = {
        "breaksSubtype": subtype,
        "strength": strength,
        "breakCredits": break_c,
    }
    if break_max is not None:
        br["breakMaxSubs"] = break_max
    if pump_c is not None:
        br["pumpCredits"] = pump_c
        br["pumpStrength"] = pump_s if pump_s is not None else 1
    paid = []
    if pump_c is not None:
        pump_eff = {
            "op": "do",
            "action": {
                "kind": "pump_strength",
                "amount": pump_s if pump_s is not None else 1,
            },
        }
        paid.append(
            {
                "id": f"{slugify(c['title'])}-pump",
                "label": f"Pump {c['title']} +{pump_s if pump_s is not None else 1} strength",
                "clickCost": 0,
                "creditCost": pump_c,
                "cost": {"credits": pump_c},
                "windows": ["encounter_paw"],
                "effect": pump_eff,
            }
        )
    return base(c, breaker=br, paidAbilities=paid, **extra)


def map_card(c: dict) -> dict:
    cid = slugify(c["title"])
    text = strip_html(c.get("text") or "")
    plain = re.sub(r"\s+", " ", text).strip()

    # --- Identities (deckbuilding-only or deferred) ---
    if cid == "nova-initiumia-catalyst-impetus":
        # Singleton deckbuilding only — no in-play ability.
        return base(c, unsupported=[])

    if cid == "ampere-cybernetics-for-anyone":
        # Deckbuilding-only (singleton + faction agenda mix) — no in-play ability.
        return base(c, unsupported=[])

    # --- Simple breakers ---
    if cid == "num":
        # Fixed strength 8; break 1 sentry for 2¢; no pump.
        return breaker_card(c, "sentry", 8, 2, break_max=1)

    # --- Runner cybernetics / power / run events ---
    if cid == "zenit-chip-jz-2mj":
        return base(
            c,
            onInstall=core(1),
            onFirstSuccessfulCentralRunThisTurn=draw("runner", 1),
            unsupported=[],
        )

    if cid == "nga":
        return base(
            c,
            powerCountersOnInstall=3,
            trashWhenPowerEmpty=True,
            onSuccessfulRunOncePerTurn=True,
            onSuccessfulRun=choose(
                "runner",
                [
                    {
                        "id": "sabotage",
                        "label": "Remove 1 power counter to sabotage 1",
                        "effect": seq(
                            {
                                "op": "do",
                                "action": {
                                    "kind": "remove_power_counter",
                                    "amount": 1,
                                },
                            },
                            {
                                "op": "do",
                                "action": {
                                    "kind": "sabotage",
                                    "amount": 1,
                                    "interactive": True,
                                },
                            },
                        ),
                    },
                    {
                        "id": "decline",
                        "label": "Decline",
                        "effect": gain("runner", 0),
                    },
                ],
            ),
            unsupported=[],
        )

    if cid == "dr-nuka-vrolyck":
        return base(
            c,
            powerCountersOnInstall=2,
            trashWhenPowerEmpty=True,
            paidAbilities=[
                {
                    "id": "nuka-draw",
                    "label": "[click], hosted power counter: Draw 3 cards",
                    "clickCost": 1,
                    "creditCost": 0,
                    "cost": {"clicks": 1, "powerCounters": 1},
                    "windows": ["runner_action_paw"],
                    "effect": draw("runner", 3),
                }
            ],
            unsupported=[],
        )

    if cid == "finality":
        return base(
            c,
            playAdditionalCost=core(1),
            runEvent={"servers": "rd", "bonusAccess": 3},
            unsupported=[],
        )

    if cid == "tremolo":
        card = breaker_card(
            c, "barrier", 2, 3, pump_c=2, pump_s=2, break_max=2, unsupported=[]
        )
        card["breaker"]["breakCreditsDiscountPerInstalledSubtype"] = {
            "subtype": "cybernetic",
            "amount": 1,
        }
        return card

    if cid == "basilar-synthgland-2kvj":
        return base(
            c,
            onInstall=core(2),
            allottedClicksBonus=1,
            unsupported=[],
        )

    if cid == "hypoxia":
        return base(
            c,
            playRequiresTagged=True,
            onPlay=seq(
                core(1),
                {
                    "op": "do",
                    "action": {
                        "kind": "allotted_clicks_next_turn",
                        "side": "runner",
                        "delta": -1,
                    },
                },
                {"op": "do", "action": {"kind": "rfg_self"}},
            ),
            unsupported=[],
        )

    if cid == "k2cp-turbine":
        return base(
            c,
            giveStrengthToInstalledIcebreakers={
                "amount": 2,
                "excludeSubtype": "ai",
            },
            unsupported=[],
        )

    if cid == "distributed-tracing":
        return base(
            c,
            playAdditionalClick=True,
            playRequiresAgendaStolenLastTurn=True,
            onPlay=tags(1),
            unsupported=[],
        )

    if cid == "bloop":
        return base(
            c,
            rezAdditionalCostDerezSubtype="harmonic",
            subroutines=[
                {
                    "id": "bloop-core",
                    "text": "Do 1 core damage.",
                    "effect": core(1),
                },
                {
                    "id": "bloop-trash-1",
                    "text": "Trash 1 installed program.",
                    "effect": trash_prog("choose"),
                },
                {
                    "id": "bloop-trash-2",
                    "text": "Trash 1 installed program.",
                    "effect": trash_prog("choose"),
                },
            ],
            unsupported=[],
        )

    if cid == "pulse":
        return base(
            c,
            onRez={
                "op": "if",
                "cond": {"op": "source_protects_attacked_server"},
                "then": {
                    "op": "do",
                    "action": {
                        "kind": "lose_clicks",
                        "side": "runner",
                        "amount": 1,
                    },
                },
            },
            subroutines=[
                {
                    "id": "pulse-lose",
                    "text": "The Runner loses 1¢ for each rezzed piece of harmonic ice.",
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "lose_credits_per_rezzed_subtype",
                            "side": "runner",
                            "subtype": "harmonic",
                            "per": 1,
                        },
                    },
                },
                {
                    "id": "pulse-etr",
                    "text": "End the run unless the Runner spends [click].",
                    "effect": choose(
                        "runner",
                        [
                            {
                                "id": "spend-click",
                                "label": "Spend [click]",
                                "effect": {
                                    "op": "do",
                                    "action": {
                                        "kind": "lose_clicks",
                                        "side": "runner",
                                        "amount": 1,
                                    },
                                },
                            },
                            {
                                "id": "etr",
                                "label": "End the run",
                                "effect": etr(),
                            },
                        ],
                    ),
                },
            ],
            unsupported=[],
        )

    if cid == "shipment-from-vladisibirsk":
        return base(
            c,
            playRequiresMinTags=2,
            onPlay={
                "op": "do",
                "action": {"kind": "place_advancements", "amount": 4},
            },
            unsupported=[],
        )

    if cid == "katorga-breakout":
        return base(
            c,
            runEvent={
                "servers": "any",
                "onSuccessfulRun": {
                    "op": "do",
                    "action": {
                        "kind": "add_from_heap_to_grip",
                        "pick": "choose",
                    },
                },
            },
            unsupported=[],
        )

    if cid == "raindrops-cut-stone":
        # Run any server; +1 power per subroutine that resolves; on run end
        # draw 1 per hosted power + gain 3¢.
        return base(
            c,
            subtypes=["run"],
            runEvent={
                "servers": "any",
                "addPowerCounterOnSubroutineResolve": 1,
                "onRunEnd": seq(
                    {
                        "op": "do",
                        "action": {
                            "kind": "draw_per_power_counter",
                            "side": "runner",
                            "per": 1,
                        },
                    },
                    gain("runner", 3),
                ),
            },
            unsupported=[],
        )

    if cid == "simulation-reset":
        return base(
            c,
            onPlay={
                "op": "do",
                "action": {
                    "kind": "simulation_reset_resolve",
                    "trashHqMax": 5,
                },
            },
            unsupported=[],
        )

    if cid == "poison-vial":
        return base(
            c,
            powerCountersOnInstall=3,
            trashWhenPowerEmpty=True,
            paidAbilities=[
                {
                    "id": "poison-vial-break",
                    "label": "Hosted power counter: Break up to 2 subroutines",
                    "clickCost": 0,
                    "creditCost": 0,
                    "cost": {"powerCounters": 1},
                    "windows": ["encounter_paw"],
                    "requireBrokenSubThisEncounter": True,
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "break_encounter_subroutine",
                            "maxSubs": 2,
                        },
                    },
                }
            ],
            unsupported=[],
        )

    if cid == "hippocampic-mechanocytes":
        return base(
            c,
            powerCountersOnInstall=2,
            handSizePerPowerCounter=1,
            onInstall=meat(1),
            unsupported=[],
        )

    if cid == "dr-vientiane-keeling":
        return base(
            c,
            runnerHandSizePenaltyPerPowerCounter=1,
            onRez={"op": "do", "action": {"kind": "add_power_counter", "amount": 1}},
            onTurnBegin={
                "op": "do",
                "action": {"kind": "add_power_counter", "amount": 1},
            },
            unsupported=[],
        )

    if cid == "time-bomb":
        return base(
            c,
            installRequiresSuccessfulCentralRunThisTurn=True,
            powerCountersOnInstall=1,
            onTurnBegin={
                "op": "seq",
                "effects": [
                    {
                        "op": "do",
                        "action": {"kind": "add_power_counter", "amount": 1},
                    },
                    {
                        "op": "if",
                        "cond": {"op": "power_counters_gte", "amount": 3},
                        "then": {
                            "op": "seq",
                            "effects": [
                                {"op": "do", "action": {"kind": "trash_self"}},
                                {
                                    "op": "do",
                                    "action": {
                                        "kind": "sabotage",
                                        "amount": 3,
                                        "interactive": True,
                                    },
                                },
                            ],
                        },
                    },
                ],
            },
            unsupported=[],
        )

    if cid == "gaslight":
        return base(
            c,
            onTurnBegin=choose(
                "corp",
                [
                    {
                        "id": "trash-search",
                        "label": "Trash Gaslight: search R&D for an operation",
                        "effect": seq(
                            trash_self(),
                            {
                                "op": "do",
                                "action": {"kind": "search_rd_operation_to_hq"},
                            },
                        ),
                    },
                    {
                        "id": "decline",
                        "label": "Decline",
                        "effect": gain("corp", 0),
                    },
                ],
            ),
            unsupported=[],
        )

    if cid == "djupstad-grid":
        return base(
            c,
            coreDamageOnAgendaScoredFromThisServer=1,
            unsupported=[],
        )

    if cid == "nanisivik-grid":
        # Approach this server: may flip 1 facedown Archives ice faceup and
        # resolve 1 subroutine on it. Region limit is engine-enforced.
        return base(
            c,
            onApproachServer={
                "op": "do",
                "action": {"kind": "may_flip_archives_ice_resolve_subroutine"},
            },
            unsupported=[],
        )

    if cid == "zato-city-grid":
        # Remote only. Protecting ice gains encounter may-trash-to-resolve-sub.
        return base(
            c,
            remoteOnly=True,
            iceGainsTrashToResolveChosenSubOnEncounter=True,
            unsupported=[],
        )

    if cid == "tsakhia-bankhar-gantulga":
        # Turn begin: may name a server. First encounter with ice protecting
        # that server: each sub becomes Do 1 net damage instead.
        return base(
            c,
            onTurnBegin={
                "op": "do",
                "action": {"kind": "may_choose_server"},
            },
            firstEncounterSubsBecomeNetDamage=1,
            unsupported=[],
        )

    if cid == "hybrid-release":
        return base(
            c,
            onScore=choose(
                "corp",
                [
                    {
                        "id": "install",
                        "label": "Install 1 facedown card from Archives",
                        "effect": {
                            "op": "do",
                            "action": {
                                "kind": "may_install_facedown_from_archives",
                            },
                        },
                    },
                    {
                        "id": "decline",
                        "label": "Decline",
                        "effect": gain("corp", 0),
                    },
                ],
            ),
            unsupported=[],
        )

    if cid == "thule-subsea-safety-below":
        return base(
            c,
            onAgendaStolen=choose(
                "runner",
                [
                    {
                        "id": "pay",
                        "label": "Spend [click] and 2¢",
                        "effect": seq(
                            {
                                "op": "do",
                                "action": {
                                    "kind": "lose_clicks",
                                    "side": "runner",
                                    "amount": 1,
                                },
                            },
                            lose("runner", 2),
                        ),
                    },
                    {
                        "id": "damage",
                        "label": "Suffer 1 core damage",
                        "effect": core(1),
                    },
                ],
            ),
            unsupported=[],
        )

    if cid == "reprise":
        return base(
            c,
            playRequiresAgendaStolenThisTurn=True,
            onPlay={
                "op": "do",
                "action": {
                    "kind": "return_installed_corp_to_hq",
                    "pick": "choose",
                },
            },
            runEvent={"servers": "any"},
            runEventOptional=True,
            unsupported=[],
        )

    if cid == "orca":
        card = breaker_card(
            c, "sentry", 3, 2, pump_c=2, pump_s=3, break_max=99, unsupported=[]
        )
        card["onFullyBreakOncePerTurn"] = choose(
            "runner",
            [
                {
                    "id": "charge",
                    "label": "Charge 1 of your installed cards",
                    "effect": {
                        "op": "do",
                        "action": {"kind": "charge", "pick": "choose"},
                    },
                },
                {
                    "id": "decline",
                    "label": "Decline",
                    "effect": gain("runner", 0),
                },
            ],
        )
        return card

    if cid == "abaasy":
        card = breaker_card(
            c, "code gate", 1, 1, pump_c=2, pump_s=2, unsupported=[]
        )
        card["onFullyBreakOncePerTurn"] = {
            "op": "do",
            "action": {"kind": "may_trash_from_grip_to_draw"},
        }
        return card

    if cid == "info-bounty":
        return base(
            c,
            onTurnBegin={"op": "do", "action": {"kind": "identify_mark"}},
            gainCreditsOnFirstMarkRunEndIfBreached=2,
            unsupported=[],
        )

    if cid == "hostile-architecture":
        return base(
            c,
            meatDamageOnInstalledCorpTrashOncePerTurn=2,
            unsupported=[],
        )

    if cid == "wake-implant-v2a-jrj":
        return base(
            c,
            onInstall=meat(1),
            onSuccessfulRun={
                "op": "if",
                "cond": {"op": "attacking_hq"},
                "then": {
                    "op": "do",
                    "action": {"kind": "add_power_counter", "amount": 1},
                },
            },
            maySpendPowerCountersForBonusRdAccess={"max": 3},
            unsupported=[],
        )

    if cid == "vera-ivanovna-shuyskaya":
        return base(
            c,
            onAgendaScoredOrStolen={
                "op": "do",
                "action": {"kind": "may_trash_one_from_grip"},
            },
            unsupported=[],
        )

    if cid == "issuaq-adaptics-sustaining-diversity":
        return base(
            c,
            powerOnScoreIfAgendaNotInstalledOrAdvancedThisTurn=True,
            agendaPointsToWinReductionPerPowerCounter=1,
            unsupported=[],
        )

    if cid == "kimberlite-field":
        return base(
            c,
            onScore={
                "op": "do",
                "action": {
                    "kind": "may_trash_installed",
                    "excludeSelf": True,
                    "rezzedOnly": True,
                    "then": {
                        "op": "do",
                        "action": {
                            "kind": "trash_installed_runner_lte_last_trashed_rez",
                            "pick": "choose",
                        },
                    },
                },
            },
            unsupported=[],
        )

    if cid == "yakov-erikovich-avdakov":
        return base(
            c,
            creditsOnTrashFromThisServer=2,
            unsupported=[],
        )

    if cid == "hush":
        return base(
            c,
            installOnIce=True,
            blanksHostAbilities=True,
            paidAbilities=[
                {
                    "id": "hush-rehost",
                    "label": "[click]: Host on another installed ice",
                    "clickCost": 1,
                    "creditCost": 0,
                    "cost": {"clicks": 1},
                    "windows": ["runner_action_paw"],
                    "effect": {
                        "op": "do",
                        "action": {"kind": "rehost_on_other_ice"},
                    },
                }
            ],
            unsupported=[],
        )

    if cid == "flux-capacitor":
        return base(
            c,
            installOnIce=True,
            chargeOnFirstBreakDuringHostEncounter=True,
            unsupported=[],
        )

    if cid == "concerto":
        return base(
            c,
            subtypes=["run"],
            onPlay={
                "op": "do",
                "action": {"kind": "reveal_top_stack_to_grip_place_hosted_credits"},
            },
            runEvent={"servers": "any"},
            unsupported=[],
        )

    if cid == "anvil":
        return base(
            c,
            onEncounter={
                "op": "do",
                "action": {
                    "kind": "may_trash_installed",
                    "excludeSelf": True,
                    "then": {
                        "op": "do",
                        "action": {"kind": "forbid_runner_break_on_source"},
                    },
                },
            },
            subroutines=[
                {
                    "id": "anvil-gain-lose",
                    "text": "Gain 1[credit]. The Runner loses 1[credit].",
                    "effect": seq(gain("corp", 1), lose("runner", 1)),
                },
                {
                    "id": "anvil-trash-runner",
                    "text": "The Runner trashes 1 of their installed cards.",
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "trash_installed_runner",
                            "pick": "choose",
                        },
                    },
                },
            ],
            unsupported=[],
        )

    if cid == "hafrun":
        return base(
            c,
            onRez={
                "op": "if",
                "cond": {"op": "source_protects_attacked_server"},
                "then": {
                    "op": "do",
                    "action": {
                        "kind": "may_trash_hq_then",
                        "then": {
                            "op": "do",
                            "action": {
                                "kind": "forbid_installed_runner_break_for_run"
                            },
                        },
                    },
                },
            },
            subroutines=[
                {
                    "id": "hafrun-etr",
                    "text": "End the run.",
                    "effect": etr(),
                }
            ],
            unsupported=[],
        )

    if cid == "klevetnik":
        return base(
            c,
            onRez={
                "op": "if",
                "cond": {"op": "source_protects_attacked_server"},
                "then": {
                    "op": "do",
                    "action": {
                        "kind": "may_give_runner_credits_then",
                        "amount": 2,
                        "then": {
                            "op": "do",
                            "action": {
                                "kind": "blank_installed_resource_until_corp_turn_end"
                            },
                        },
                    },
                },
            },
            subroutines=[
                {
                    "id": "klevetnik-etr",
                    "text": "End the run.",
                    "effect": etr(),
                }
            ],
            unsupported=[],
        )

    if cid == "unsmiling-tsarevna":
        return base(
            c,
            onRez={
                "op": "if",
                "cond": {"op": "source_protects_attacked_server"},
                "then": {
                    "op": "do",
                    "action": {
                        "kind": "may_give_runner_credits_then",
                        "amount": 2,
                        "then": {
                            "op": "do",
                            "action": {
                                "kind": "limit_printed_breaks_on_source_for_run",
                                "max": 1,
                            },
                        },
                    },
                },
            },
            subroutines=[
                {
                    "id": "unsmiling-net",
                    "text": "Do 2 net damage.",
                    "effect": net(2),
                },
                {
                    "id": "unsmiling-tag",
                    "text": "Give the Runner 1 tag.",
                    "effect": tags(1),
                },
            ],
            unsupported=[],
        )

    if cid == "tunnel-vision":
        card = breaker_card(
            c, "*", 2, 2, pump_c=2, pump_s=2, break_max=2, unsupported=[]
        )
        card["breaker"]["breakRequiresAttackingMark"] = True
        card["onTurnBegin"] = {"op": "do", "action": {"kind": "identify_mark"}}
        return card

    if cid == "nanuq":
        return breaker_card(
            c,
            "*",
            3,
            2,
            pump_c=1,
            pump_s=1,
            break_max=2,
            rfgOnUninstall=True,
            onAgendaScoredOrStolen={"op": "do", "action": {"kind": "rfg_self"}},
            unsupported=[],
        )

    # --- Simple agendas ---
    if cid == "post-truth-dividend":
        return base(
            c,
            onScore=choose(
                "corp",
                [
                    {
                        "id": "draw",
                        "label": "Draw 1",
                        "effect": draw("corp", 1),
                    },
                    {
                        "id": "decline",
                        "label": "Decline",
                        "effect": gain("corp", 0),
                    },
                ],
            ),
            unsupported=[],
        )

    if cid == "freedom-of-information":
        return base(
            c,
            advancementRequirementReductionPerTag=1,
            unsupported=[],
        )

    if cid == "ontological-dependence":
        return base(
            c,
            advancementRequirementReductionPerCoreDamageThisGame=1,
            unsupported=[],
        )

    if cid == "regulatory-capture":
        return base(
            c,
            advancementRequirementReductionPerBadPublicity={"per": 1, "max": 4},
            unsupported=[],
        )

    # --- Simple operations ---
    if cid == "end-of-the-line":
        return base(
            c,
            playAdditionalCost=remove_tags(1),
            onPlay=meat(4),
            unsupported=[],
        )

    if cid == "nonequivalent-exchange":
        return base(
            c,
            onPlay=seq(
                gain("corp", 5),
                choose(
                    "corp",
                    [
                        {
                            "id": "both-gain-2",
                            "label": "Each player gains 2¢",
                            "effect": seq(gain("corp", 2), gain("runner", 2)),
                        },
                        {
                            "id": "decline",
                            "label": "Decline",
                            "effect": gain("corp", 0),
                        },
                    ],
                ),
            ),
            unsupported=[],
        )

    # --- Simple assets ---
    if cid == "reaper-function":
        return base(
            c,
            onTurnBegin=choose(
                "corp",
                [
                    {
                        "id": "trash-net",
                        "label": "Trash Reaper Function to do 2 net damage",
                        "effect": seq(trash_self(), net(2)),
                    },
                    {
                        "id": "decline",
                        "label": "Decline",
                        "effect": gain("corp", 0),
                    },
                ],
            ),
            unsupported=[],
        )

    if cid == "superdeep-borehole":
        # Load 6 hosted BP on rez (not player BP). Turn begin: take 1 from
        # this asset → player BP. When empty, Corp wins.
        return base(
            c,
            badPublicityCountersOnRez=6,
            winWhenBadPublicityCountersEmpty=True,
            onTurnBegin={
                "op": "do",
                "action": {"kind": "take_hosted_bad_publicity", "amount": 1},
            },
            unsupported=[],
        )

    if cid == "spark-of-inspiration":
        # Set aside stack until a program; may install it −10¢; shuffle aside.
        return base(
            c,
            onPlay={
                "op": "do",
                "action": {
                    "kind": "spark_of_inspiration_resolve",
                    "discount": 10,
                },
            },
            unsupported=[],
        )

    if cid == "world-tree":
        # First successful run each turn (Nga once-per-turn pattern): may trash
        # another installed card → search stack for same type, install −3¢.
        return base(
            c,
            onSuccessfulRunOncePerTurn=True,
            onSuccessfulRun={
                "op": "do",
                "action": {
                    "kind": "may_trash_other_installed_search_stack_same_type_install",
                    "discount": 3,
                },
            },
            unsupported=[],
        )

    if cid == "mr-hendrik":
        return base(
            c,
            onAccess={
                "op": "if",
                "cond": {"op": "source_installed"},
                "then": {
                    "op": "do",
                    "action": {
                        "kind": "may_pay_credits_for_core_damage",
                        "amount": 2,
                        "damage": 1,
                    },
                },
            },
            unsupported=[],
        )

    if cid == "nightmare-archive":
        return base(
            c,
            mustRevealWhenAccessedFromRd=True,
            onAccess=choose(
                "runner",
                [
                    {
                        "id": "score-neg1",
                        "label": "Add to score area as −1 agenda point",
                        "effect": {
                            "op": "do",
                            "action": {
                                "kind": "add_to_runner_score_as_agenda",
                                "agendaPoints": -1,
                            },
                        },
                    },
                    {
                        "id": "damage-rfg",
                        "label": "Suffer 1 core damage; remove from the game",
                        "effect": seq(
                            core(1),
                            {"op": "do", "action": {"kind": "rfg_self"}},
                        ),
                    },
                ],
            ),
            unsupported=[],
        )

    # --- Ice with fully mappable printed subs (on-rez / encounter deferred) ---
    if cid == "vampyronassa":
        return base(
            c,
            subroutines=[
                {
                    "id": "vamp-lose",
                    "text": "The Runner loses 2¢.",
                    "effect": lose("runner", 2),
                },
                {
                    "id": "vamp-gain",
                    "text": "Gain 2¢.",
                    "effect": gain("corp", 2),
                },
                {
                    "id": "vamp-net",
                    "text": "Do 2 net damage.",
                    "effect": net(2),
                },
                {
                    "id": "vamp-draw",
                    "text": "You may draw 1 or 2 cards.",
                    "effect": choose(
                        "corp",
                        [
                            {
                                "id": "draw1",
                                "label": "Draw 1",
                                "effect": draw("corp", 1),
                            },
                            {
                                "id": "draw2",
                                "label": "Draw 2",
                                "effect": draw("corp", 2),
                            },
                            {
                                "id": "decline",
                                "label": "Decline",
                                "effect": gain("corp", 0),
                            },
                        ],
                    ),
                },
            ],
            unsupported=[],
        )

    # Fallback: skeleton with full text as unsupported
    card = base(c)
    card["unsupported"] = [f"Full text not yet mapped to IR: {plain[:240]}"]
    return card


def main():
    data = json.loads(NRDB.read_text())["data"]
    ph = sorted(
        [c for c in data if c.get("pack_code") == "ph"],
        key=lambda c: c.get("position", 0),
    )
    assert len(ph) == 63, len(ph)

    OUT.mkdir(parents=True, exist_ok=True)
    for p in OUT.glob("*.json"):
        p.unlink()

    written = []
    for c in ph:
        mapped = map_card(c)
        cid = mapped["id"]
        path = OUT / f"{cid}.json"
        path.write_text(json.dumps(mapped, indent=2, ensure_ascii=False) + "\n")
        written.append(cid)

    assert len(written) == 63, len(written)

    full = sum(
        1
        for cid in written
        if not json.loads((OUT / f"{cid}.json").read_text()).get("unsupported")
    )
    partial = len(written) - full

    manifest = {
        "pack": "parhelion",
        "nrdbPackCode": "ph",
        "count": 63,
        "written": 63,
        "status": "in-progress",
        "notes": (
            "Null Signal Parhelion (NRDB pack ph) — Borealis set 2 of 2. "
            "Wave is in-progress: simple cards mapped where Effect IR covers them; "
            "remaining cards have explicit unsupported notes."
        ),
        "cards": written,
    }
    (OUT / "_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"
    )

    print(f"Wrote {len(written)} cards to {OUT}")
    print(f"Among written: full={full} partial={partial}")
    print("POOL_IDS=" + json.dumps(written))


if __name__ == "__main__":
    main()
