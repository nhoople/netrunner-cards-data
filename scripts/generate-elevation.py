#!/usr/bin/env python3
"""Generate Elevation card JSON from pinned pack `elev`.

Catalog source: Null-Signal-Games/netrunner-cards-json (see data/nrdb-catalog-pin.json).
Fetch with: python3 scripts/nrdb_catalog.py fetch elev

Hand-mapped Effect IR only where existing primitives fully cover the card;
everything else lists honest unsupported notes — never invent IR.

Usage: python3 scripts/generate-elevation.py
"""
from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

from nrdb_catalog import load_pack_cards

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "elevation"
WAVE = "elevation"
PACK = "elev"
EXPECTED = 82


def slugify(title: str) -> str:
    # Strip marks before NFKD — ™ decomposes to ASCII "TM".
    t = title.replace("™", "").replace("®", "").replace("©", "")
    t = unicodedata.normalize("NFKD", t)
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = t.lower()
    t = t.replace("“", "").replace("”", "").replace('"', "")
    t = t.replace("'", "").replace("’", "").replace("ʼ", "")
    t = t.replace(".", "-").replace(":", " ").replace("!", "")
    t = t.replace("(", " ").replace(")", " ")
    t = re.sub(r"[^a-z0-9]+", "-", t)
    return t.strip("-")


def strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text or "")


def etr():
    return {"op": "do", "action": {"kind": "end_the_run"}}


def gain(side: str, n: int):
    return {"op": "do", "action": {"kind": "gain_credits", "side": side, "amount": n}}


def draw(side: str, n: int):
    return {"op": "do", "action": {"kind": "draw", "side": side, "amount": n}}


def net(n: int):
    return {"op": "do", "action": {"kind": "net_damage", "amount": n}}


def tags(n: int):
    return {"op": "do", "action": {"kind": "give_tags", "amount": n}}


def seq(*effects):
    return {"op": "seq", "effects": list(effects)}


def base(c, **extra):
    subtypes = []
    if c.get("keywords"):
        subtypes = [s.strip().lower() for s in c["keywords"].split(" - ")]
    card = {
        "id": slugify(c["title"]),
        "title": c["title"],
        "wave": WAVE,
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
    paid = list(extra.pop("paidAbilities", []) or [])
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


def decline(side: str):
    return {
        "id": "decline",
        "label": "Decline",
        "effect": gain(side, 0),
    }


def may_place_adv(amount: int = 1):
    return {
        "op": "choose",
        "chooser": "corp",
        "options": [
            {
                "id": "place",
                "label": f"Place {amount} advancement",
                "effect": {
                    "op": "do",
                    "action": {"kind": "place_advancements", "amount": amount},
                },
            },
            decline("corp"),
        ],
    }


def map_card(c: dict) -> dict:
    cid = slugify(c["title"])
    text = strip_html(c.get("text") or "")
    plain = re.sub(r"\s+", " ", text).strip()

    # --- Mapped (existing IR covers full card text) ---

    if cid == "clean-getaway":
        return base(
            c,
            subtypes=["run"],
            runEvent={
                "servers": "any",
                "onSuccessfulRun": gain("runner", 6),
            },
            unsupported=[],
        )

    if cid == "rent-rioters":
        return base(
            c,
            paidAbilities=[
                {
                    "id": "rent-rioters-gain",
                    "label": "[click][click][click], [trash]: Gain 9¢",
                    "clickCost": 3,
                    "creditCost": 0,
                    "cost": {"clicks": 3, "trashSelf": True},
                    "windows": ["runner_action_paw"],
                    "effect": gain("runner", 9),
                }
            ],
            unsupported=[],
        )

    if cid == "anthill-excavation-contract":
        return base(
            c,
            onRez={
                "op": "do",
                "action": {"kind": "place_hosted_credits", "amount": 8},
            },
            onTurnBegin=seq(
                {
                    "op": "do",
                    "action": {"kind": "take_hosted_credits", "amount": 4},
                },
                draw("corp", 1),
            ),
            unsupported=[],
        )

    if cid == "azimat":
        return base(
            c,
            recurringCreditsMax=2,
            recurringSpendFor=["trash"],
            unsupported=[],
        )

    if cid == "chromatophores":
        return base(
            c,
            installOnIce=True,
            hostGainsAllIceSubtypes=True,
            unsupported=[],
        )

    if cid == "byte":
        return base(
            c,
            mustRevealWhenAccessedFromRd=True,
            skipOnAccessFromArchives=True,
            onAccess={
                "op": "choose",
                "chooser": "corp",
                "options": [
                    {
                        "id": "pay",
                        "label": "Pay 4¢: give 1 tag and do 3 net damage",
                        "effect": seq(
                            {
                                "op": "do",
                                "action": {
                                    "kind": "lose_credits",
                                    "side": "corp",
                                    "amount": 4,
                                },
                            },
                            tags(1),
                            net(3),
                        ),
                    },
                    decline("corp"),
                ],
            },
            unsupported=[],
        )

    if cid == "nanomanagement":
        return base(
            c,
            onPlay={
                "op": "do",
                "action": {
                    "kind": "gain_clicks",
                    "side": "corp",
                    "amount": 2,
                },
            },
            unsupported=[],
        )

    if cid == "hantu":
        return breaker_card(
            c,
            "sentry",
            c.get("strength") or 2,
            1,
            break_max=1,
            onInstall={
                "op": "do",
                "action": {"kind": "add_virus_counter", "amount": 2},
            },
            paidAbilities=[
                {
                    "id": "hantu-pump",
                    "label": "Hosted virus counter: +2 strength",
                    "clickCost": 0,
                    "creditCost": 0,
                    "cost": {"virusCounters": 1},
                    "windows": ["encounter_paw"],
                    "effect": {
                        "op": "do",
                        "action": {"kind": "pump_strength", "amount": 2},
                    },
                }
            ],
            unsupported=[],
        )

    if cid == "flyswatter":
        return base(
            c,
            onRez={
                "op": "if",
                "cond": {"op": "source_protects_attacked_server"},
                "then": {
                    "op": "do",
                    "action": {"kind": "purge_virus_counters"},
                },
            },
            subroutines=[
                {
                    "id": "flyswatter-etr",
                    "text": "End the run.",
                    "effect": etr(),
                }
            ],
            unsupported=[],
        )

    if cid == "n-pot":
        return base(
            c,
            paidAbilities=[
                {
                    "id": "n-pot-break",
                    "label": "3¢: Break 1 subroutine on N-Pot",
                    "clickCost": 0,
                    "creditCost": 3,
                    "cost": {"credits": 3},
                    "windows": ["encounter_paw"],
                    "effect": {
                        "op": "do",
                        "action": {"kind": "break_host_subroutine"},
                    },
                }
            ],
            subroutines=[
                {
                    "id": "n-pot-etr",
                    "text": "End the run.",
                    "effect": etr(),
                },
                {
                    "id": "n-pot-threat-2",
                    "text": "If threat ≥ 2, end the run.",
                    "effect": {
                        "op": "if",
                        "cond": {"op": "threat", "level": 2},
                        "then": etr(),
                    },
                },
                {
                    "id": "n-pot-threat-4",
                    "text": "If threat ≥ 4, end the run.",
                    "effect": {
                        "op": "if",
                        "cond": {"op": "threat", "level": 4},
                        "then": etr(),
                    },
                },
            ],
            unsupported=[],
        )

    if cid == "empiricist":
        return base(
            c,
            subroutines=[
                {
                    "id": "empiricist-draw",
                    "text": "Draw 1. You may add 1 card from HQ to the top of R&D.",
                    "effect": seq(
                        draw("corp", 1),
                        {
                            "op": "choose",
                            "chooser": "corp",
                            "options": [
                                {
                                    "id": "hq-top",
                                    "label": "Add 1 from HQ to top of R&D",
                                    "effect": {
                                        "op": "do",
                                        "action": {
                                            "kind": "hq_to_top_rd",
                                            "pick": "choose",
                                        },
                                    },
                                },
                                decline("corp"),
                            ],
                        },
                    ),
                },
                {
                    "id": "empiricist-net-tag",
                    "text": "Do 1 net damage. Give the Runner 1 tag.",
                    "effect": seq(net(1), tags(1)),
                },
                {
                    "id": "empiricist-net-2",
                    "text": "Do 2 net damage.",
                    "effect": net(2),
                },
            ],
            unsupported=[],
        )

    if cid == "syailendra":
        return base(
            c,
            canAdvance=True,
            onEncounter={
                "op": "if",
                "cond": {"op": "advancements_gte", "amount": 3},
                "then": may_place_adv(1),
            },
            subroutines=[
                {
                    "id": "syailendra-adv",
                    "text": "You may place 1 advancement on an advanceable card.",
                    "effect": may_place_adv(1),
                },
                {
                    "id": "syailendra-lose",
                    "text": "The Runner loses 2[credit].",
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "lose_credits",
                            "side": "runner",
                            "amount": 2,
                        },
                    },
                },
                {
                    "id": "syailendra-net",
                    "text": "Do 1 net damage.",
                    "effect": net(1),
                },
            ],
            unsupported=[],
        )

    if cid == "lamplighter":
        return base(
            c,
            onAgendaScoredOrStolen={
                "op": "if",
                "cond": {
                    "op": "last_agenda_scored_or_stolen_from_source_server_root"
                },
                "then": {"op": "do", "action": {"kind": "trash_self"}},
            },
            subroutines=[
                {
                    "id": "lamplighter-tag",
                    "text": "Give the Runner 1 tag unless they pay 3[credit].",
                    "effect": {
                        "op": "choose",
                        "chooser": "runner",
                        "options": [
                            {
                                "id": "pay",
                                "label": "Pay 3¢",
                                "effect": {
                                    "op": "do",
                                    "action": {
                                        "kind": "lose_credits",
                                        "side": "runner",
                                        "amount": 3,
                                    },
                                },
                            },
                            {
                                "id": "tag",
                                "label": "Take 1 tag",
                                "effect": tags(1),
                            },
                        ],
                    },
                },
                {
                    "id": "lamplighter-etr",
                    "text": "End the run if the Runner is tagged.",
                    "effect": {
                        "op": "if",
                        "cond": {"op": "runner_tagged"},
                        "then": etr(),
                    },
                },
            ],
            unsupported=[],
        )

    if cid == "top-down-solutions":
        return base(
            c,
            onPlay=seq(
                draw("corp", 2),
                {
                    "op": "do",
                    "action": {"kind": "may_install_from_hq_paying_costs"},
                },
                {
                    "op": "do",
                    "action": {"kind": "may_install_from_hq_paying_costs"},
                },
            ),
            unsupported=[],
        )

    if cid == "illumination":
        install1 = {
            "op": "do",
            "action": {"kind": "may_install_from_grip", "discount": 1},
        }
        return base(
            c,
            subtypes=["run"],
            runEvent={
                "servers": "rd",
                "onSuccessfulRun": seq(install1, install1, install1),
            },
            unsupported=[],
        )

    if cid == "maglectric-rapid-748-mod":
        return base(
            c,
            onSuccessfulRun={
                "op": "if",
                "cond": {"op": "attacking_hq"},
                "then": {
                    "op": "choose",
                    "chooser": "runner",
                    "options": [
                        {
                            "id": "trash-derez",
                            "label": "Trash Maglectric: derez 1 installed Corp card",
                            "effect": seq(
                                {
                                    "op": "do",
                                    "action": {"kind": "trash_self"},
                                },
                                {
                                    "op": "do",
                                    "action": {"kind": "may_derez_installed"},
                                },
                            ),
                        },
                        decline("runner"),
                    ],
                },
            },
            unsupported=[],
        )

    if cid == "idiosyncresis":
        return base(
            c,
            canAdvance=True,
            onTurnBegin={
                "op": "choose",
                "chooser": "corp",
                "options": [
                    {
                        "id": "detonate",
                        "label": "Trash: gain 3¢ and Runner loses 2¢ per advancement",
                        "effect": seq(
                            {
                                "op": "do",
                                "action": {
                                    "kind": "gain_credits_per_advancement",
                                    "per": 3,
                                },
                            },
                            {
                                "op": "do",
                                "action": {
                                    "kind": "lose_credits_per_advancement",
                                    "per": 2,
                                },
                            },
                            {
                                "op": "do",
                                "action": {"kind": "trash_self"},
                            },
                        ),
                    },
                    decline("corp"),
                ],
            },
            unsupported=[],
        )

    if cid == "devadatta-drone":
        return base(
            c,
            powerCountersOnInstall=2,
            maySpendPowerCountersForBonusRdAccess={"max": 1},
            unsupported=[],
        )

    if cid == "doomscroll":
        return base(
            c,
            subroutines=[
                {
                    "id": "doomscroll-tag",
                    "text": "Give the Runner 1 tag.",
                    "effect": tags(1),
                },
                {
                    "id": "doomscroll-net-1",
                    "text": "Do 1 net damage.",
                    "effect": net(1),
                },
                {
                    "id": "doomscroll-net-2",
                    "text": "Do 2 net damage if the Runner has at least 2 tags.",
                    "effect": {
                        "op": "if",
                        "cond": {"op": "tags_gte", "amount": 2},
                        "then": net(2),
                    },
                },
            ],
            unsupported=[],
        )

    if cid == "otto-campaign":
        return base(
            c,
            onRez={
                "op": "do",
                "action": {"kind": "place_hosted_credits", "amount": 6},
            },
            onTurnBegin={
                "op": "do",
                "action": {"kind": "take_hosted_credits", "amount": 2},
            },
            clicksOnHostedEmpty=2,
            unsupported=[],
        )

    if cid == "principia":
        return breaker_card(
            c,
            "barrier",
            c.get("strength") or 2,
            1,
            pump_c=2,
            pump_s=2,
            break_max=1,
            installCostDiscountPerInstalledIcebreaker=1,
            unsupported=[],
        )

    if cid == "rising-tide":
        return breaker_card(
            c,
            "barrier",
            c.get("strength") or 1,
            1,
            pump_c=1,
            pump_s=1,
            break_max=1,
            strengthBonusPerHeapSubtype={"subtype": "fracter", "bonus": 1},
            unsupported=[],
        )

    if cid == "greenmail":
        return base(
            c,
            onScore=gain("corp", 2),
            onForfeit=gain("corp", 4),
            unsupported=[],
        )

    if cid == "lie-low":
        return base(
            c,
            playAdditionalClick=True,
            onPlay={
                "op": "choose",
                "chooser": "runner",
                "options": [
                    {
                        "id": "draw",
                        "label": "Draw 4 cards",
                        "effect": draw("runner", 4),
                    },
                    {
                        "id": "tags",
                        "label": "Remove up to 2 tags",
                        "effect": {
                            "op": "do",
                            "action": {"kind": "remove_tags", "amount": 2},
                        },
                    },
                ],
            },
            unsupported=[],
        )

    if cid == "measured-response":
        return base(
            c,
            playRequiresThreat=4,
            playRequiresSuccessfulRunLastTurn=True,
            onPlay={
                "op": "choose",
                "chooser": "runner",
                "options": [
                    {
                        "id": "pay8",
                        "label": "Pay 8¢",
                        "effect": {
                            "op": "do",
                            "action": {
                                "kind": "lose_credits",
                                "side": "runner",
                                "amount": 8,
                            },
                        },
                    },
                    {
                        "id": "meat",
                        "label": "Suffer 4 meat damage",
                        "effect": {
                            "op": "do",
                            "action": {"kind": "meat_damage", "amount": 4},
                        },
                    },
                ],
            },
            unsupported=[],
        )

    if cid == "kessleroid":
        return base(
            c,
            cannotBeTrashedByRunnerWhileRezzed=True,
            subroutines=[
                {
                    "id": "kessleroid-etr-1",
                    "text": "End the run.",
                    "effect": etr(),
                },
                {
                    "id": "kessleroid-etr-2",
                    "text": "End the run.",
                    "effect": etr(),
                },
            ],
            unsupported=[],
        )

    if cid == "scatter-field":
        return base(
            c,
            strengthBonusIfSoleIceProtectingServer=4,
            subroutines=[
                {
                    "id": "scatter-field-install",
                    "text": "You may install 1 card from HQ.",
                    "effect": {
                        "op": "do",
                        "action": {"kind": "may_install_from_hq_paying_costs"},
                    },
                },
                {
                    "id": "scatter-field-etr",
                    "text": "End the run.",
                    "effect": etr(),
                },
            ],
            unsupported=[],
        )

    if cid == "semak-samun":
        return base(
            c,
            cannotBreakExceptSubtype="fracter",
            subroutines=[
                {
                    "id": "semak-samun-etr",
                    "text": "End the run unless the Runner suffers 3 net damage.",
                    "effect": {
                        "op": "choose",
                        "chooser": "runner",
                        "options": [
                            {
                                "id": "net",
                                "label": "Suffer 3 net damage",
                                "effect": net(3),
                            },
                            {
                                "id": "etr",
                                "label": "End the run",
                                "effect": etr(),
                            },
                        ],
                    },
                },
            ],
            unsupported=[],
        )

    if cid == "fransofia-ward":
        return base(
            c,
            iceRezCostIncrease=1,
            paidAbilities=[
                {
                    "id": "fransofia-ward-bypass",
                    "label": "Trash Fransofia Ward: bypass encountered ice (Corp ≥15¢)",
                    "clickCost": 0,
                    "creditCost": 0,
                    "cost": {"trashSelf": True},
                    "windows": ["encounter_paw"],
                    "requiresCorpCreditsGte": 15,
                    "effect": {
                        "op": "do",
                        "action": {"kind": "bypass_current_ice"},
                    },
                }
            ],
            unsupported=[],
        )

    if cid == "bumi-1-0":
        return base(
            c,
            onRez={
                "op": "if",
                "cond": {"op": "source_protects_attacked_server"},
                "then": {
                    "op": "choose",
                    "chooser": "corp",
                    "options": [
                        {
                            "id": "trash-trojan",
                            "label": "Trash 1 installed trojan program",
                            "effect": {
                                "op": "do",
                                "action": {
                                    "kind": "trash_program",
                                    "pick": "choose",
                                    "includeSubtypes": ["trojan"],
                                },
                            },
                        },
                        decline("corp"),
                    ],
                },
            },
            subroutines=[
                {
                    "id": "bumi-trash",
                    "text": "Trash 1 installed program.",
                    "effect": {
                        "op": "do",
                        "action": {"kind": "trash_program", "pick": "choose"},
                    },
                },
                {
                    "id": "bumi-core",
                    "text": "Do 1 core damage.",
                    "effect": {
                        "op": "do",
                        "action": {"kind": "core_damage", "amount": 1},
                    },
                },
            ],
            unsupported=[],
        )

    if cid == "ritual":
        return base(
            c,
            onPlay={
                "op": "do",
                "action": {"kind": "draw_per_clicks_remaining", "side": "runner"},
            },
            unsupported=[],
        )

    if cid == "sang-kancil":
        return breaker_card(
            c,
            "code gate",
            c.get("strength") or 2,
            1,
            pump_c=3,
            pump_s=2,
            break_max=1,
            paidAbilityCreditDiscountIfRunEventActive=2,
            unsupported=[],
        )

    if cid == "transfer-of-wealth":
        return base(
            c,
            subtypes=["run"],
            runEvent={
                "servers": "hq",
                "onSuccessfulRun": seq(
                    tags(1),
                    {
                        "op": "do",
                        "action": {
                            "kind": "lose_credits",
                            "side": "corp",
                            "amount": 3,
                            "gainPerCreditLost": {"side": "runner", "per": 2},
                        },
                    },
                ),
            },
            unsupported=[],
        )

    if cid == "public-access-plaza":
        return base(
            c,
            onTurnBegin=gain("corp", 1),
            threatGiveTagsOnRezzedTrash={"level": 2, "tags": 1},
            unsupported=[],
        )

    if cid == "scrounge":
        return base(
            c,
            playAdditionalClick=True,
            onPlay=seq(
                {
                    "op": "do",
                    "action": {
                        "kind": "install_from_heap",
                        "types": ["program"],
                        "discount": 0,
                    },
                },
                {
                    "op": "do",
                    "action": {
                        "kind": "may_add_from_heap_to_stack_bottom",
                        "types": ["program"],
                    },
                },
            ),
            unsupported=[],
        )

    if cid == "topan-ormas-leader":
        return base(
            c,
            paidAbilities=[
                {
                    "id": "topan-install",
                    "label": "Once per turn → [click]: Install 1 card from grip (−2¢); suffer 1 meat damage",
                    "clickCost": 1,
                    "creditCost": 0,
                    "cost": {"clicks": 1},
                    "oncePerTurn": True,
                    "windows": ["runner_action_paw"],
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "install_from_grip_discount",
                            "types": ["program", "hardware", "resource"],
                            "discount": 2,
                            "thenOnInstall": {
                                "op": "do",
                                "action": {"kind": "meat_damage", "amount": 1},
                            },
                        },
                    },
                }
            ],
            unsupported=[],
        )

    if cid == "key-performance-indicators":
        return base(
            c,
            onPlay={
                "op": "do",
                "action": {
                    "kind": "choose_exactly_n",
                    "n": 2,
                    "options": [
                        {
                            "id": "draw",
                            "label": "Draw 1 card",
                            "effect": draw("corp", 1),
                        },
                        {
                            "id": "shuffle",
                            "label": "Shuffle 1 card from HQ into R&D",
                            "effect": {
                                "op": "do",
                                "action": {
                                    "kind": "shuffle_hq_to_rd",
                                    "amount": 1,
                                },
                            },
                        },
                        {
                            "id": "install-ice",
                            "label": "Install 1 ice from HQ, ignoring all costs",
                            "effect": {
                                "op": "do",
                                "action": {
                                    "kind": "install_ice_from_hq_ignore_costs"
                                },
                            },
                        },
                        {
                            "id": "advance",
                            "label": "Place 1 advancement counter on an installed card you can advance",
                            "effect": {
                                "op": "do",
                                "action": {
                                    "kind": "place_advancements",
                                    "amount": 1,
                                },
                            },
                        },
                        {
                            "id": "credits",
                            "label": "Gain 2¢",
                            "effect": gain("corp", 2),
                        },
                    ],
                },
            },
            unsupported=[],
        )

    if cid == "open-market":
        return base(
            c,
            hostedCreditsOnInstall=6,
            hostedCreditsSpendFor=["install"],
            hostedCreditsSpendForInstallSubtypes=["connection", "job"],
            onTurnBegin={
                "op": "do",
                "action": {"kind": "take_hosted_credits", "amount": 1},
            },
            unsupported=[],
        )

    if cid == "gourmand":
        return base(
            c,
            accessTrashSelfNonAgendaThenDraw=True,
            unsupported=[],
        )

    # --- v1.07.0: Corp discard-phase hub + deferred B ---

    def dividends_on_score(*, past: int = 3, per: int = 1, counters_per_excess: int | None = None):
        action = {
            "kind": "add_agenda_counters_from_overadvance",
            "past": past,
        }
        if counters_per_excess is not None:
            action["countersPerExcess"] = counters_per_excess
        elif per != 1:
            action["per"] = per
        else:
            action["per"] = 1
        return {"op": "do", "action": action}

    def discard_spend_agenda(label: str, option_id: str, body_effect: dict) -> dict:
        return {
            "op": "if",
            "cond": {"op": "agenda_counters_gte", "amount": 1},
            "then": {
                "op": "choose",
                "chooser": "corp",
                "options": [
                    {
                        "id": option_id,
                        "label": label,
                        "effect": seq(
                            {
                                "op": "do",
                                "action": {
                                    "kind": "remove_agenda_counters",
                                    "amount": 1,
                                },
                            },
                            body_effect,
                        ),
                    },
                    {
                        "id": "decline",
                        "label": "Decline",
                        "effect": gain("corp", 0),
                    },
                ],
            },
        }

    if cid == "project-ingatan":
        return base(
            c,
            onScore=dividends_on_score(),
            onDiscardPhaseEnd=discard_spend_agenda(
                "Remove 1 agenda counter: install 1 card from Archives, ignoring all costs",
                "install",
                {
                    "op": "do",
                    "action": {"kind": "may_install_from_archives_ignore_costs"},
                },
            ),
            unsupported=[],
        )

    if cid == "embedded-reporting":
        return base(
            c,
            onScore=dividends_on_score(counters_per_excess=2),
            onDiscardPhaseEnd=discard_spend_agenda(
                "Remove 1 agenda counter: search R&D for 1 operation → top of R&D",
                "search",
                {
                    "op": "do",
                    "action": {"kind": "search_rd_operation_to_top_rd"},
                },
            ),
            unsupported=[],
        )

    if cid == "sericulture-expansion":
        return base(
            c,
            onScore=dividends_on_score(),
            onDiscardPhaseEnd=discard_spend_agenda(
                "Remove 1 agenda counter: place 2 advancements (cannot score that card this turn)",
                "advance",
                {
                    "op": "do",
                    "action": {
                        "kind": "place_advancements",
                        "amount": 2,
                        "pick": "choose",
                        "cannotScoreTargetThisTurn": True,
                    },
                },
            ),
            unsupported=[],
        )

    if cid == "side-hustle":
        return base(
            c,
            onInstall={
                "op": "do",
                "action": {"kind": "place_hosted_credits", "amount": 1},
            },
            onRunBegin={
                "op": "do",
                "action": {"kind": "place_hosted_credits", "amount": 1},
            },
            onHostedCreditsGte={
                "amount": 6,
                "effect": {
                    "op": "do",
                    "action": {"kind": "take_hosted_credits", "amount": 999},
                },
            },
            drawOnHostedEmpty=1,
            unsupported=[],
        )

    if cid == "leo-construction-labor-solutions":
        return base(
            c,
            paidAbilities=[
                {
                    "id": "leo-etr",
                    "label": "Once per turn → Trash 1 rezzed bioroid in/protecting attacked server: End the run",
                    "clickCost": 0,
                    "creditCost": 0,
                    "cost": {},
                    "oncePerTurn": True,
                    "windows": [
                        "approach_paw",
                        "encounter_paw",
                        "approach_server_paw",
                    ],
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "trash_installed",
                            "rezzedOnly": True,
                            "includeSubtypes": ["bioroid"],
                            "attackedServerOnly": True,
                            "then": {
                                "op": "do",
                                "action": {"kind": "end_the_run"},
                            },
                        },
                    },
                }
            ],
            unsupported=[],
        )

    if cid == "synapse-global-faster-than-thought":
        return base(
            c,
            onRemoveTags={
                "op": "do",
                "action": {"kind": "may_install_from_hq_ignore_costs"},
            },
            paidAbilities=[
                {
                    "id": "synapse-untag",
                    "label": "[click], remove 1 tag: Gain 2¢",
                    "clickCost": 1,
                    "creditCost": 0,
                    "cost": {"clicks": 1, "removeTags": 1},
                    "windows": ["corp_action_paw"],
                    "effect": gain("corp", 2),
                }
            ],
            unsupported=[],
        )

    if cid == "pt-untaian-lifes-building-blocks":
        return base(
            c,
            onDiscardPhaseEnd={
                "op": "if",
                "cond": {"op": "hq_count_lte", "amount": 3},
                "then": {
                    "op": "choose",
                    "chooser": "corp",
                    "options": [
                        {
                            "id": "pay-advance",
                            "label": "Pay 1¢: place 1 advancement on an unrezzed advanceable card",
                            "effect": seq(
                                {
                                    "op": "do",
                                    "action": {
                                        "kind": "lose_credits",
                                        "side": "corp",
                                        "amount": 1,
                                    },
                                },
                                {
                                    "op": "do",
                                    "action": {
                                        "kind": "place_advancements",
                                        "amount": 1,
                                        "pick": "choose",
                                        "unrezzedOnly": True,
                                        "cannotScoreTargetThisTurn": True,
                                    },
                                },
                            ),
                        },
                        {
                            "id": "decline",
                            "label": "Decline",
                            "effect": gain("corp", 0),
                        },
                    ],
                },
            },
            unsupported=[],
        )

    if cid == "off-the-books":
        return base(
            c,
            onScore=dividends_on_score(),
            onDiscardPhaseEnd=discard_spend_agenda(
                "Remove 1 agenda counter: search R&D — may install ignoring costs, else HQ",
                "search",
                {
                    "op": "do",
                    "action": {
                        "kind": "search_rd_reveal_may_install_ignore_costs_else_hq"
                    },
                },
            ),
            unsupported=[],
        )

    # --- v1.08.0: Humanoid / Next Big Thing / Poétrï / Phật / Biawak / Cacophony / Mercia ---

    if cid == "humanoid-resources":
        return base(
            c,
            paidAbilities=[
                {
                    "id": "humanoid-resources-main",
                    "label": "[click][click][click], [trash]: Gain 4¢ and draw 3. Install up to 2 from HQ. May play 1 operation from HQ.",
                    "clickCost": 3,
                    "creditCost": 0,
                    "cost": {"clicks": 3, "trashSelf": True},
                    "windows": ["corp_action_paw"],
                    "effect": seq(
                        gain("corp", 4),
                        draw("corp", 3),
                        {
                            "op": "do",
                            "action": {"kind": "may_install_from_hq_paying_costs"},
                        },
                        {
                            "op": "do",
                            "action": {"kind": "may_install_from_hq_paying_costs"},
                        },
                        {
                            "op": "do",
                            "action": {"kind": "may_play_operation_from_hq"},
                        },
                    ),
                }
            ],
            unsupported=[],
        )

    if cid == "next-big-thing":
        return base(
            c,
            onScore={
                "op": "do",
                "action": {"kind": "add_agenda_counter", "amount": 1},
            },
            onSteal={
                "op": "do",
                "action": {"kind": "add_agenda_counter", "amount": 1},
            },
            paidAbilities=[
                {
                    "id": "next-big-thing-draw",
                    "label": "[click], hosted agenda counter: Draw 4. Shuffle any number from HQ into R&D.",
                    "clickCost": 1,
                    "creditCost": 0,
                    "cost": {"clicks": 1, "agendaCounters": 1},
                    "windows": ["corp_action_paw"],
                    "usableFromRunnerScoreArea": True,
                    "effect": seq(
                        draw("corp", 4),
                        {
                            "op": "do",
                            "action": {"kind": "shuffle_any_number_hq_to_rd"},
                        },
                    ),
                }
            ],
            unsupported=[],
        )

    if cid == "poetri-luxury-brands-all-the-rage":
        return base(
            c,
            onAgendaScored={
                "op": "do",
                "action": {
                    "kind": "look_top_n_rd_may_install_one",
                    "n": 3,
                    "excludeAgenda": True,
                },
            },
            onAgendaStolen={
                "op": "do",
                "action": {
                    "kind": "may_install_from_hq_paying_costs",
                    "excludeAgenda": True,
                },
            },
            unsupported=[],
        )

    if cid == "phat-gioan-baotixita":
        return base(
            c,
            onDiscardPhaseEnd={
                "op": "do",
                "action": {"kind": "add_power_counter", "amount": 1},
            },
            onFirstAgendaScoredOrStolenThisTurn={
                "op": "do",
                "action": {
                    "kind": "may_remove_power_counters_then_net_damage",
                    "base": 1,
                    "perRemoved": 1,
                    "maxRemove": 2,
                },
            },
            unsupported=[],
        )

    if cid == "biawak":
        return base(
            c,
            rezCostCreditDiscountOnForfeitAgenda=10,
            subroutines=[
                {
                    "id": "biawak-trash-program",
                    "text": "Trash 1 installed program or end the run.",
                    "effect": {
                        "op": "choose",
                        "chooser": "corp",
                        "options": [
                            {
                                "id": "trash",
                                "label": "Trash a program",
                                "effect": {
                                    "op": "do",
                                    "action": {
                                        "kind": "trash_program",
                                        "pick": "choose",
                                    },
                                },
                            },
                            {
                                "id": "etr",
                                "label": "End the run",
                                "effect": etr(),
                            },
                        ],
                    },
                },
                {
                    "id": "biawak-trash-resource",
                    "text": "Trash 1 installed resource or end the run.",
                    "effect": {
                        "op": "choose",
                        "chooser": "corp",
                        "options": [
                            {
                                "id": "trash",
                                "label": "Trash a resource",
                                "effect": {
                                    "op": "do",
                                    "action": {
                                        "kind": "trash_resource",
                                        "pick": "choose",
                                    },
                                },
                            },
                            {
                                "id": "etr",
                                "label": "End the run",
                                "effect": etr(),
                            },
                        ],
                    },
                },
                {
                    "id": "biawak-etr",
                    "text": "End the run.",
                    "effect": etr(),
                },
            ],
            unsupported=[],
        )

    if cid == "cacophony":
        return base(
            c,
            onFirstRunnerStoleOrTrashedCorpCardThisTurn={
                "op": "do",
                "action": {"kind": "add_power_counter", "amount": 1},
            },
            onRunnerActionPhaseEnd={
                "op": "choose",
                "chooser": "runner",
                "options": [
                    {
                        "id": "sabotage",
                        "label": "Remove 2 power counters to sabotage 3",
                        "effect": seq(
                            {
                                "op": "do",
                                "action": {
                                    "kind": "remove_power_counter",
                                    "amount": 2,
                                },
                            },
                            {
                                "op": "do",
                                "action": {
                                    "kind": "sabotage",
                                    "amount": 3,
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
            },
            unsupported=[],
        )

    if cid == "mercia-b4ll4rd":
        return base(
            c,
            onCorpActionPhaseEnd={
                "op": "do",
                "action": {
                    "kind": "may_install_ice_from_hq_discount_then_move_source",
                    "discount": 1,
                },
            },
            unsupported=[],
        )

    # --- v1.09.0: Touch-ups / Knickknack / Barry / Proprionegation / Mycoweb / Mahkota / Nebula ---

    if cid == "touch-ups":
        return base(
            c,
            playAdditionalClick=True,
            onPlay=seq(
                {
                    "op": "do",
                    "action": {
                        "kind": "place_advancements",
                        "amount": 2,
                        "pick": "choose",
                    },
                },
                {
                    "op": "do",
                    "action": {
                        "kind": "touch_ups_choose_type_shuffle_grip",
                        "maxCards": 2,
                    },
                },
            ),
            unsupported=[],
        )

    if cid == "knickknack-obrian":
        return base(
            c,
            onFirstRunBeginThisTurn={
                "op": "do",
                "action": {
                    "kind": "may_trash_other_installed_gain_printed_install_and_draw",
                },
            },
            unsupported=[],
        )

    if cid == "barry-baz-wong-tri-maf-veteran":
        return base(
            c,
            onAnyIceRez={
                "op": "do",
                "action": {
                    "kind": "may_install_from_grip",
                    "types": ["resource", "hardware"],
                },
            },
            unsupported=[],
        )

    if cid == "proprionegation":
        return base(
            c,
            onScore={
                "op": "do",
                "action": {"kind": "add_agenda_counter", "amount": 1},
            },
            paidAbilities=[
                {
                    "id": "proprionegation-archives",
                    "label": "Hosted agenda counter: Move Runner to outermost Archives (during a run)",
                    "clickCost": 0,
                    "creditCost": 0,
                    "cost": {"agendaCounters": 1},
                    "windows": ["corp_action_paw"],
                    "requireDuringRun": True,
                    "usableFromRunnerScoreArea": True,
                    "effect": {
                        "op": "do",
                        "action": {"kind": "move_runner_to_archives_outermost"},
                    },
                }
            ],
            unsupported=[],
        )

    if cid == "mycoweb":
        return base(
            c,
            subroutines=[
                {
                    "id": "mycoweb-archives-install",
                    "text": "You may install 1 piece of ice from Archives, ignoring all costs.",
                    "effect": {
                        "op": "do",
                        "action": {"kind": "may_install_from_archives_ignore_costs"},
                    },
                },
                {
                    "id": "mycoweb-rez-discount",
                    "text": "You may rez 1 installed piece of ice, paying 2[credit] less.",
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "may_rez_installed_ice_discount",
                            "discount": 2,
                        },
                    },
                },
                {
                    "id": "mycoweb-sentry-sub",
                    "text": "Resolve 1 subroutine on a rezzed sentry.",
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "may_resolve_subroutine_on_rezzed_ice",
                            "subtype": "sentry",
                            "excludeSelf": True,
                        },
                    },
                },
                {
                    "id": "mycoweb-code-gate-sub",
                    "text": "Resolve 1 subroutine on another rezzed code gate.",
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "may_resolve_subroutine_on_rezzed_ice",
                            "subtype": "code gate",
                            "excludeSelf": True,
                        },
                    },
                },
            ],
            unsupported=[],
        )

    if cid == "mahkota-langit-grid":
        return base(
            c,
            subtypes=["region"],
            recurringCreditsMax=2,
            recurringSpendFor=["rez_host_server"],
            persistent=True,
            serverRootAssetTrashCostBonus=2,
            unsupported=[],
        )

    # --- v1.10.0 safer 6: Muslihat / Nebula / Petty Cash / Zwicky / Magdalene / Peer Review ---

    if cid == "muslihat-multifarious-marketeer":
        return base(
            c,
            onTurnBegin={
                "op": "do",
                "action": {
                    "kind": "look_top_stack_may_reveal_breaker_or_run_event",
                },
            },
            unsupported=[],
        )

    if cid == "nebula-talent-management-making-stars":
        return base(
            c,
            onCorpActionPhaseEnd={
                "op": "if",
                "cond": {"op": "corp_played_operation_this_turn"},
                "then": {
                    "op": "if",
                    "cond": {"op": "identity_unflipped"},
                    "then": seq(
                        gain("corp", 1),
                        {
                            "op": "do",
                            "action": {"kind": "flip_identity"},
                        },
                    ),
                },
            },
            identityFlippedHooks={
                "onFirstOperationPlayThisTurn": {
                    "op": "do",
                    "action": {
                        "kind": "gain_clicks",
                        "side": "corp",
                        "amount": 1,
                    },
                },
                "onSuccessfulHqOrRdRun": {
                    "op": "do",
                    "action": {"kind": "flip_identity"},
                },
            },
            unsupported=[],
        )

    if cid == "petty-cash":
        return base(
            c,
            playRequiresNoCorpActionFinished=True,
            onPlay=seq(
                gain("corp", 5),
                {
                    "op": "if",
                    "cond": {"op": "played_from_non_hq"},
                    "then": {
                        "op": "do",
                        "action": {
                            "kind": "gain_clicks",
                            "side": "corp",
                            "amount": 1,
                        },
                    },
                },
            ),
            paidAbilities=[
                {
                    "id": "petty-cash-archives",
                    "label": "[click]: Play this operation from Archives. After it resolves, remove it from the game.",
                    "clickCost": 1,
                    "creditCost": 0,
                    "cost": {"clicks": 1},
                    "windows": ["corp_action_paw"],
                    "usableFromArchives": True,
                    "effect": {
                        "op": "do",
                        "action": {"kind": "play_self_from_archives_then_rfg"},
                    },
                }
            ],
            unsupported=[],
        )

    if cid == "the-zwicky-group-invisible-hands":
        return base(
            c,
            onCreditsGainedFromAgendaOrOperationAbility={
                "op": "choose",
                "chooser": "corp",
                "options": [
                    {
                        "id": "draw",
                        "label": "Draw 1 card",
                        "effect": draw("corp", 1),
                    },
                    decline("corp"),
                ],
            },
            unsupported=[],
        )

    if cid == "magdalene-keino-chemutai-cryptarchitect":
        return base(
            c,
            onRunnerDiscardOverMaxHand={
                "op": "do",
                "action": {
                    "kind": "may_install_program_hardware_from_last_runner_discarded",
                },
            },
            unsupported=[],
        )

    if cid == "peer-review":
        return base(
            c,
            onPlay={
                "op": "do",
                "action": {"kind": "peer_review"},
            },
            unsupported=[],
        )

    # --- v1.11.0: Mitra / Bigger Picture / Aggressive / Plutus / IP / Maintenance ---

    if cid == "mitra-aman":
        return base(
            c,
            onApproachIce={
                "op": "choose",
                "chooser": "corp",
                "options": [
                    decline("corp"),
                    {
                        "id": "activate",
                        "label": "Trash this upgrade: gain 3[credit] and may swap approached ice",
                        "effect": {
                            "op": "do",
                            "action": {"kind": "mitra_aman_approach_ice"},
                        },
                    },
                ],
            },
            unsupported=[],
        )

    if cid == "bigger-picture":
        return base(
            c,
            playRequiresTagged=True,
            onPlay={
                "op": "choose",
                "chooser": "corp",
                "options": [
                    {
                        "id": "tag",
                        "label": "Give the Runner 1 tag",
                        "effect": tags(1),
                    },
                    {
                        "id": "remove",
                        "label": "Remove tags (Runner loses 5[credit] each; you gain that much)",
                        "effect": {
                            "op": "do",
                            "action": {"kind": "bigger_picture_remove_tags"},
                        },
                    },
                ],
            },
            unsupported=[],
        )

    if cid == "aggressive-trendsetting":
        return base(
            c,
            onFirstCorpCardTrashEachTurn={
                "op": "choose",
                "chooser": "runner",
                "options": [
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
                        "id": "corp-click",
                        "label": "Decline — Corp gets +1 allotted click next turn",
                        "effect": {
                            "op": "do",
                            "action": {
                                "kind": "allotted_clicks_next_turn",
                                "side": "corp",
                                "delta": 1,
                            },
                        },
                    },
                ],
            },
            unsupported=[],
        )

    if cid == "plutus":
        return base(
            c,
            rezAdditionalCost={
                "op": "do",
                "action": {"kind": "plutus_pay_rez_additional_cost"},
            },
            onTurnBegin={
                "op": "do",
                "action": {"kind": "plutus_may_play_transaction_from_archives"},
            },
            unsupported=[],
        )

    if cid == "ip-enforcement":
        return base(
            c,
            playAdditionalCost={
                "op": "do",
                "action": {"kind": "ip_enforcement_remove_tags"},
            },
            onPlay={
                "op": "do",
                "action": {"kind": "ip_enforcement_install_from_runner_score"},
            },
            unsupported=[],
        )

    if cid == "maintenance-access":
        return base(
            c,
            playAdditionalClick=True,
            subtypes=["run", "double"],
            runEvent={
                "servers": "archives",
                "redirectApproachArchivesToHq": True,
            },
            unsupported=[],
        )

    # --- v1.12.0: final 10 (82/82) ---

    if cid == "ryo-phoenix-ono-out-of-the-ashes":
        return base(
            c,
            onSuccessfulRunOncePerTurn={
                "op": "if",
                "cond": {"op": "subroutine_resolved_this_run"},
                "then": seq(
                    gain("runner", 1),
                    {
                        "op": "do",
                        "action": {
                            "kind": "trash_hq",
                            "pick": "random",
                            "amount": 1,
                        },
                    },
                ),
            },
            unsupported=[],
        )

    if cid == "dewi-subrotoputri-pedagogical-dhalang":
        return base(
            c,
            onSuccessfulRun={
                "op": "choose",
                "chooser": "runner",
                "options": [
                    {
                        "id": "unflipped",
                        "label": "MU full: flip and gain 1[credit]",
                        "effect": {
                            "op": "if",
                            "cond": {
                                "op": "and",
                                "conds": [
                                    {"op": "identity_unflipped"},
                                    {"op": "runner_mu_full"},
                                ],
                            },
                            "then": seq(
                                {
                                    "op": "do",
                                    "action": {"kind": "flip_identity"},
                                },
                                gain("runner", 1),
                            ),
                        },
                    },
                    {
                        "id": "flipped",
                        "label": "Unused MU: flip and draw 1",
                        "effect": {
                            "op": "if",
                            "cond": {
                                "op": "and",
                                "conds": [
                                    {"op": "identity_flipped"},
                                    {"op": "runner_unused_mu_gte", "amount": 1},
                                ],
                            },
                            "then": seq(
                                {
                                    "op": "do",
                                    "action": {"kind": "flip_identity"},
                                },
                                draw("runner", 1),
                            ),
                        },
                    },
                    decline("runner"),
                ],
            },
            unsupported=[],
        )

    if cid == "charm-offensive":
        return base(
            c,
            subtypes=["run"],
            runEvent={
                "servers": "archives",
                "onRunEnd": {
                    "op": "do",
                    "action": {"kind": "charm_offensive_trash_rezzed_accessed"},
                },
            },
            unsupported=[],
        )

    # Fail closed — honest unsupported note for the remainder.
    card = base(c)
    card["unsupported"] = [f"Full text not yet mapped to IR: {plain[:240]}"]
    return card


def main():
    pack = sorted(
        load_pack_cards(PACK),
        key=lambda c: c.get("position", 0),
    )
    assert len(pack) == EXPECTED, len(pack)

    OUT.mkdir(parents=True, exist_ok=True)
    for p in OUT.glob("*.json"):
        p.unlink()

    written = []
    for c in pack:
        mapped = map_card(c)
        cid = mapped["id"]
        path = OUT / f"{cid}.json"
        path.write_text(json.dumps(mapped, indent=2, ensure_ascii=False) + "\n")
        written.append(cid)

    assert len(written) == EXPECTED, len(written)
    assert len(set(written)) == EXPECTED, "duplicate slug ids"

    full = sum(
        1
        for cid in written
        if not json.loads((OUT / f"{cid}.json").read_text()).get("unsupported")
    )
    partial = len(written) - full

    manifest = {
        "pack": WAVE,
        "nrdbPackCode": PACK,
        "count": EXPECTED,
        "written": EXPECTED,
        "status": "in-progress",
        "notes": (
            "Null Signal Elevation (NRDB pack elev) — next constructed set after "
            "Rebellion Without Rehearsal. Kickoff extract: fail-closed IR; "
            f"{full} cards fully mapped, {partial} with unsupported notes "
            "(wave kickoff v1.01.0)."
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
