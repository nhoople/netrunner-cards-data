#!/usr/bin/env python3
"""Generate Rebellion Without Rehearsal card JSON from pinned pack `rwr`.

Catalog source: Null-Signal-Games/netrunner-cards-json (see data/nrdb-catalog-pin.json).
Fetch with: python3 scripts/nrdb_catalog.py fetch rwr

Hand-mapped Effect IR only where existing primitives fully cover the card;
everything else lists honest unsupported notes — never invent IR.

Usage: python3 scripts/generate-rwr.py
"""
from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

from nrdb_catalog import load_pack_cards

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "rebellion-without-rehearsal"
WAVE = "rebellion-without-rehearsal"
PACK = "rwr"
EXPECTED = 65


def slugify(title: str) -> str:
    t = unicodedata.normalize("NFKD", title)
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = t.lower()
    t = t.replace(""", "").replace(""", "").replace('"', "")
    t = t.replace("'", "").replace("'", "").replace("ʼ", "")
    t = t.replace(".", "-").replace(":", " ")
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


def core(n: int):
    return {"op": "do", "action": {"kind": "core_damage", "amount": n}}


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

    if cid == "coalescence":
        return base(
            c,
            powerCountersOnInstall=2,
            paidAbilities=[
                {
                    "id": "coalescence-gain",
                    "label": "Hosted power counter: Gain 2¢",
                    "clickCost": 0,
                    "creditCost": 0,
                    "cost": {"powerCounters": 1},
                    "windows": ["runner_action_paw"],
                    "effect": gain("runner", 2),
                }
            ],
            unsupported=[],
        )

    if cid == "pressure-spike":
        card = breaker_card(
            c, "barrier", 1, 1, pump_c=2, pump_s=3, break_max=1, unsupported=[]
        )
        card["paidAbilities"].append(
            {
                "id": "pressure-spike-threat-pump",
                "label": "Threat 4 → 2¢: +9 strength (once per run)",
                "clickCost": 0,
                "creditCost": 2,
                "cost": {"credits": 2},
                "windows": ["encounter_paw"],
                "requiresThreat": 4,
                "oncePerRun": True,
                "effect": {
                    "op": "do",
                    "action": {"kind": "pump_strength", "amount": 9},
                },
            }
        )
        return card

    if cid == "see-how-they-run":
        return base(
            c,
            onScore=seq(
                tags(1),
                {
                    "op": "do",
                    "action": {
                        "kind": "play_psi_game",
                        "maxBid": 2,
                        "ifBidsDiffer": core(1),
                        "ifBidsMatch": net(1),
                    },
                },
            ),
            unsupported=[],
        )

    if cid == "corporate-hospitality":
        return base(
            c,
            playAdditionalClick=True,
            onPlay=seq(
                gain("corp", 6),
                draw("corp", 2),
                {
                    "op": "do",
                    "action": {"kind": "archives_to_hq", "amount": 1},
                },
            ),
            unsupported=[],
        )

    if cid == "boto":
        return base(
            c,
            threatStrengthBonus={"level": 4, "amount": 2},
            subroutines=[
                {
                    "id": "boto-net",
                    "text": "Do 2 net damage.",
                    "effect": net(2),
                },
                {
                    "id": "boto-trash-etr",
                    "text": "You may trash 1 card from HQ to end the run.",
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "may_trash_hq_then",
                            "then": etr(),
                        },
                    },
                },
                {
                    "id": "boto-etr",
                    "text": "End the run.",
                    "effect": etr(),
                },
            ],
            unsupported=[],
        )

    if cid == "capacitor":
        return base(
            c,
            strengthBonusWhileTagged=2,
            subroutines=[
                {
                    "id": "capacitor-credits",
                    "text": "Gain 1[credit] for each tag the Runner has.",
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "gain_credits_per_runner_tags",
                            "per": 1,
                        },
                    },
                },
                {
                    "id": "capacitor-etr",
                    "text": "End the run.",
                    "effect": etr(),
                },
            ],
            unsupported=[],
        )

    if cid == "friend-of-a-friend":
        return base(
            c,
            paidAbilities=[
                {
                    "id": "fof-untag",
                    "label": "[click], [trash]: Gain 5¢ and remove 1 tag",
                    "clickCost": 1,
                    "creditCost": 0,
                    "cost": {"clicks": 1, "trashSelf": True},
                    "windows": ["runner_action_paw"],
                    "effect": seq(
                        gain("runner", 5),
                        {
                            "op": "do",
                            "action": {"kind": "remove_tags", "amount": 1},
                        },
                    ),
                },
                {
                    "id": "fof-tag",
                    "label": "[click], [trash]: Gain 9¢ and take 1 tag (if untagged)",
                    "clickCost": 1,
                    "creditCost": 0,
                    "cost": {"clicks": 1, "trashSelf": True},
                    "windows": ["runner_action_paw"],
                    "requiresUntagged": True,
                    "effect": seq(gain("runner", 9), tags(1)),
                },
            ],
            unsupported=[],
        )

    if cid == "seraph":
        return base(
            c,
            onEncounter={
                "op": "choose",
                "chooser": "runner",
                "options": [
                    {
                        "id": "lose-3",
                        "label": "Lose 3¢",
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
                        "id": "net-2",
                        "label": "Suffer 2 net damage",
                        "effect": net(2),
                    },
                    {
                        "id": "tag-1",
                        "label": "Take 1 tag",
                        "effect": tags(1),
                    },
                ],
            },
            subroutines=[
                {
                    "id": "seraph-lose",
                    "text": "The Runner loses 3[credit].",
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
                    "id": "seraph-net",
                    "text": "Do 2 net damage.",
                    "effect": net(2),
                },
                {
                    "id": "seraph-tag",
                    "text": "Give the Runner 1 tag.",
                    "effect": tags(1),
                },
            ],
            unsupported=[],
        )

    if cid == "the-powers-that-be":
        return base(
            c,
            onAgendaScored={
                "op": "choose",
                "chooser": "corp",
                "options": [
                    {
                        "id": "install",
                        "label": "Install 1 card from HQ or Archives, ignoring all costs",
                        "effect": {
                            "op": "do",
                            "action": {"kind": "install_from_hq_or_archives"},
                        },
                    },
                    {
                        "id": "decline",
                        "label": "Decline",
                        "effect": gain("corp", 0),
                    },
                ],
            },
            unsupported=[],
        )

    if cid == "stoke-the-embers":
        place1 = {
            "op": "do",
            "action": {"kind": "place_advancements", "amount": 1},
        }
        return base(
            c,
            onScore=seq(gain("corp", 3), place1),
            onInstallFromNonHq={
                "op": "choose",
                "chooser": "corp",
                "options": [
                    {
                        "id": "reveal",
                        "label": "Reveal: gain 2¢ and place 1 advancement",
                        "effect": seq(gain("corp", 2), place1),
                    },
                    {
                        "id": "decline",
                        "label": "Decline",
                        "effect": gain("corp", 0),
                    },
                ],
            },
            unsupported=[],
        )

    if cid == "boi-tata":
        card = breaker_card(
            c, "sentry", 1, 2, pump_c=3, pump_s=3, break_max=2, unsupported=[]
        )
        card["paidAbilityCreditDiscountIfOwnInstalledTrashedThisTurn"] = 1
        return card

    if cid == "sorocaban-blade":
        return base(
            c,
            maxInstalledRunnerTrashesPerEncounter=1,
            subroutines=[
                {
                    "id": "soro-resource",
                    "text": "Trash 1 installed resource.",
                    "effect": {
                        "op": "do",
                        "action": {"kind": "trash_resource", "pick": "choose"},
                    },
                },
                {
                    "id": "soro-hardware",
                    "text": "Trash 1 installed piece of hardware.",
                    "effect": {
                        "op": "do",
                        "action": {"kind": "trash_hardware", "pick": "choose"},
                    },
                },
                {
                    "id": "soro-program",
                    "text": "Trash 1 installed program.",
                    "effect": {
                        "op": "do",
                        "action": {"kind": "trash_program", "pick": "choose"},
                    },
                },
            ],
            unsupported=[],
        )

    if cid == "piranhas":
        may_draw = {
            "op": "choose",
            "chooser": "corp",
            "options": [
                {
                    "id": "draw",
                    "label": "Draw 1 card",
                    "effect": draw("corp", 1),
                },
                {
                    "id": "decline",
                    "label": "Decline",
                    "effect": gain("corp", 0),
                },
            ],
        }
        return base(
            c,
            rezAdditionalCost={
                "op": "choose",
                "chooser": "corp",
                "options": [
                    {
                        "id": "bad-pub",
                        "label": "Take 1 bad publicity",
                        "effect": {
                            "op": "do",
                            "action": {
                                "kind": "give_bad_publicity",
                                "amount": 1,
                            },
                        },
                    },
                    {
                        "id": "remove-tag",
                        "label": "Remove 1 tag",
                        "effect": {
                            "op": "do",
                            "action": {"kind": "remove_tags", "amount": 1},
                        },
                    },
                ],
            },
            subroutines=[
                {
                    "id": "piranhas-draw",
                    "text": "You may draw 1 card.",
                    "effect": may_draw,
                },
                {
                    "id": "piranhas-net",
                    "text": "Do 1 net damage.",
                    "effect": net(1),
                },
                {
                    "id": "piranhas-etr",
                    "text": "End the run if there are more cards in HQ than in the grip.",
                    "effect": {
                        "op": "if",
                        "cond": {"op": "hq_count_gt_grip"},
                        "then": etr(),
                    },
                },
            ],
            unsupported=[],
        )

    if cid == "charlotte-cacador":
        return base(
            c,
            canAdvance=True,
            onTurnBegin={
                "op": "choose",
                "chooser": "corp",
                "options": [
                    {
                        "id": "remove-adv",
                        "label": "Remove 1 advancement: gain 4¢ and draw 1",
                        "effect": {
                            "op": "do",
                            "action": {
                                "kind": "remove_advancements",
                                "amount": 1,
                                "then": seq(gain("corp", 4), draw("corp", 1)),
                            },
                        },
                    },
                    {
                        "id": "decline",
                        "label": "Decline",
                        "effect": gain("corp", 0),
                    },
                ],
            },
            paidAbilities=[
                {
                    "id": "charlotte-gain",
                    "label": "[trash], hosted advancement: Gain 3¢",
                    "clickCost": 0,
                    "creditCost": 0,
                    "cost": {"trashSelf": True, "advancementTokens": 1},
                    "windows": ["corp_action_paw"],
                    "effect": gain("corp", 3),
                }
            ],
            unsupported=[],
        )

    if cid == "janaina-jk-dumont-kindelan":
        return base(
            c,
            onTurnBegin={
                "op": "do",
                "action": {"kind": "place_hosted_credits", "amount": 3},
            },
            paidAbilities=[
                {
                    "id": "janaina-take",
                    "label": "[click], add to HQ: Take all hosted credits; may install",
                    "clickCost": 1,
                    "creditCost": 0,
                    "cost": {"clicks": 1},
                    "windows": ["corp_action_paw"],
                    "effect": seq(
                        {
                            "op": "do",
                            "action": {"kind": "return_source_to_hq"},
                        },
                        {
                            "op": "do",
                            "action": {
                                "kind": "take_hosted_credits",
                                "amount": 99,
                            },
                        },
                        {
                            "op": "do",
                            "action": {
                                "kind": "may_install_from_hq_paying_costs"
                            },
                        },
                    ),
                }
            ],
            unsupported=[],
        )

    if cid == "arruaceiras-crew":
        return base(
            c,
            paidAbilities=[
                {
                    "id": "arruaceiras-weaken",
                    "label": "Take 1 tag: encountered ice gets –2 strength",
                    "clickCost": 0,
                    "creditCost": 0,
                    "cost": {"tags": 1},
                    "windows": ["encounter_paw"],
                    "oncePerTurn": True,
                    "effect": {
                        "op": "do",
                        "action": {"kind": "weaken_ice", "amount": 2},
                    },
                },
                {
                    "id": "arruaceiras-trash-ice",
                    "label": "[trash], 2¢: Trash encountered ice if strength ≤ 0",
                    "clickCost": 0,
                    "creditCost": 2,
                    "cost": {"credits": 2, "trashSelf": True},
                    "windows": ["encounter_paw"],
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "trash_encounter_ice_if_strength_lte",
                            "maxStrength": 0,
                        },
                    },
                },
            ],
            unsupported=[],
        )

    if cid == "logjam":
        return base(
            c,
            canAdvance=True,
            strengthPerAdvancement=1,
            onRez={
                "op": "do",
                "action": {
                    "kind": "place_advancements_on_self_per_faceup_archive_types",
                    "base": 1,
                },
            },
            subroutines=[
                {
                    "id": "logjam-gain-etr",
                    "text": "Gain 2[credit]. End the run.",
                    "effect": seq(gain("corp", 2), etr()),
                },
                {
                    "id": "logjam-etr-2",
                    "text": "End the run.",
                    "effect": etr(),
                },
                {
                    "id": "logjam-etr-3",
                    "text": "End the run.",
                    "effect": etr(),
                },
            ],
            unsupported=[],
        )

    if cid == "hammer":
        return base(
            c,
            maxPrintedSubsBreakExceptSubtype="killer",
            onEncounter={
                "op": "do",
                "action": {
                    "kind": "limit_printed_breaks_on_source_for_run",
                    "max": 1,
                },
            },
            subroutines=[
                {
                    "id": "hammer-tag",
                    "text": "Give the Runner 1 tag.",
                    "effect": tags(1),
                },
                {
                    "id": "hammer-trash-rh",
                    "text": "Trash 1 installed resource or piece of hardware.",
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "trash_resource_or_hardware",
                            "pick": "choose",
                        },
                    },
                },
                {
                    "id": "hammer-trash-prog",
                    "text": "Trash 1 installed program that is not a decoder, fracter, or killer.",
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "trash_program",
                            "pick": "choose",
                            "excludeSubtypes": [
                                "decoder",
                                "fracter",
                                "killer",
                            ],
                        },
                    },
                },
            ],
            unsupported=[],
        )

    if cid == "active-policing":
        decline = {
            "id": "decline",
            "label": "Decline",
            "effect": gain("corp", 0),
        }
        click_penalty = {
            "op": "do",
            "action": {
                "kind": "allotted_clicks_next_turn",
                "side": "runner",
                "delta": -1,
            },
        }
        return base(
            c,
            subtypes=["terminal", "gray ops"],
            playRequiresRunnerStoleOrTrashedCorpCardLastTurn=True,
            endsActionPhase=True,
            onPlay=seq(
                {
                    "op": "do",
                    "action": {"kind": "may_install_from_hq_paying_costs"},
                },
                click_penalty,
                {
                    "op": "if",
                    "cond": {"op": "threat", "level": 3},
                    "then": {
                        "op": "choose",
                        "chooser": "corp",
                        "options": [
                            {
                                "id": "pay",
                                "label": "Pay 2¢: Runner −1 allotted click next turn",
                                "effect": seq(
                                    {
                                        "op": "do",
                                        "action": {
                                            "kind": "lose_credits",
                                            "side": "corp",
                                            "amount": 2,
                                        },
                                    },
                                    click_penalty,
                                ),
                            },
                            decline,
                        ],
                    },
                },
            ),
            unsupported=[],
        )

    if cid == "bring-them-home":
        decline = {
            "id": "decline",
            "label": "Decline",
            "effect": gain("corp", 0),
        }
        return base(
            c,
            subtypes=["terminal", "gray ops"],
            playRequiresRunnerStoleOrTrashedCorpCardLastTurn=True,
            endsActionPhase=True,
            onPlay=seq(
                {
                    "op": "do",
                    "action": {
                        "kind": "add_random_grip_to_stack_top",
                        "count": 2,
                    },
                },
                {
                    "op": "if",
                    "cond": {"op": "threat", "level": 3},
                    "then": {
                        "op": "choose",
                        "chooser": "corp",
                        "options": [
                            {
                                "id": "pay",
                                "label": "Pay 2¢: shuffle 1 random grip card into stack",
                                "effect": seq(
                                    {
                                        "op": "do",
                                        "action": {
                                            "kind": "lose_credits",
                                            "side": "corp",
                                            "amount": 2,
                                        },
                                    },
                                    {
                                        "op": "do",
                                        "action": {
                                            "kind": "shuffle_random_grip_into_stack",
                                            "count": 1,
                                        },
                                    },
                                ),
                            },
                            decline,
                        ],
                    },
                },
            ),
            unsupported=[],
        )

    if cid == "pretty-mary-da-silva":
        return base(
            c,
            onBreachRdIfAccessGteMayBonusAccess={"min": 2, "amount": 1},
            unsupported=[],
        )

    if cid == "eye-for-an-eye":
        return base(
            c,
            subtypes=["run"],
            playRequiresUntagged=True,
            accessTrashFromGrip={"gripCards": 1},
            runEvent={
                "servers": "hq",
                "bonusAccess": 1,
                "onSuccessfulRun": tags(1),
            },
            unsupported=[],
        )

    if cid == "valentina-ferreira-carvalho":
        decline = {
            "id": "decline",
            "label": "Decline",
            "effect": gain("runner", 0),
        }
        return base(
            c,
            onRemoveTags=gain("runner", 1),
            onInstall={
                "op": "if",
                "cond": {"op": "threat", "level": 3},
                "then": {
                    "op": "choose",
                    "chooser": "runner",
                    "options": [
                        {
                            "id": "untag",
                            "label": "Remove 1 tag",
                            "effect": {
                                "op": "do",
                                "action": {
                                    "kind": "remove_tags",
                                    "amount": 1,
                                },
                            },
                        },
                        {
                            "id": "credits",
                            "label": "Gain 2¢",
                            "effect": gain("runner", 2),
                        },
                        decline,
                    ],
                },
            },
            unsupported=[],
        )

    if cid == "malandragem":
        return base(
            c,
            powerCountersOnInstall=2,
            rfgWhenPowerEmpty=True,
            paidAbilities=[
                {
                    "id": "malandragem-bypass",
                    "label": "Hosted power: bypass ice if strength ≤ 3 (once per turn)",
                    "clickCost": 0,
                    "creditCost": 0,
                    "cost": {"powerCounters": 1},
                    "windows": ["encounter_paw"],
                    "oncePerTurn": True,
                    "requireEncounterStrengthLte": 3,
                    "effect": {
                        "op": "do",
                        "action": {"kind": "bypass_current_ice"},
                    },
                },
                {
                    "id": "malandragem-threat-bypass",
                    "label": "Threat 4 → RFG: bypass encountered ice",
                    "clickCost": 0,
                    "creditCost": 0,
                    "cost": {},
                    "windows": ["encounter_paw"],
                    "requiresThreat": 4,
                    "effect": seq(
                        {
                            "op": "do",
                            "action": {"kind": "rfg_self"},
                        },
                        {
                            "op": "do",
                            "action": {"kind": "bypass_current_ice"},
                        },
                    ),
                },
            ],
            unsupported=[],
        )

    if cid == "physarum-entangler":
        return base(
            c,
            installOnIce=True,
            trashOnVirusPurge=True,
            paidAbilities=[
                {
                    "id": "physarum-bypass",
                    "label": "Pay 1¢ per sub: bypass host ice (if not barrier)",
                    "clickCost": 0,
                    "creditCost": 0,
                    "cost": {"creditsPerEncounterSubroutine": 1},
                    "windows": ["encounter_paw"],
                    "requireEncounterHost": True,
                    "forbidEncounterSubtype": "barrier",
                    "effect": {
                        "op": "do",
                        "action": {"kind": "bypass_current_ice"},
                    },
                }
            ],
            unsupported=[],
        )

    if cid == "lobisomem":
        card = base(
            c,
            breaker={
                "breaksSubtype": "code gate",
                "strength": c.get("strength") or 2,
                "breakCredits": 1,
                "breakMaxSubs": 1,
                "pumpCredits": 1,
                "pumpStrength": 2,
                "breakViaPaidAbilityOnly": True,
            },
            onInstall={
                "op": "do",
                "action": {"kind": "add_power_counter", "amount": 1},
            },
            onFullyBreak={
                "op": "do",
                "action": {"kind": "add_power_counter", "amount": 1},
            },
            paidAbilities=[
                {
                    "id": "lobisomem-break-cg",
                    "label": "1¢: Break 1 code gate subroutine",
                    "clickCost": 0,
                    "creditCost": 1,
                    "cost": {"credits": 1},
                    "windows": ["encounter_paw"],
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "break_encounter_subroutine",
                            "maxSubs": 1,
                            "requireSubtype": "code gate",
                        },
                    },
                },
                {
                    "id": "lobisomem-break-barrier",
                    "label": "X¢, hosted power: Break X barrier subroutines",
                    "clickCost": 0,
                    "creditCost": 0,
                    "cost": {"powerCounters": 1},
                    "windows": ["encounter_paw"],
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "break_encounter_subroutine",
                            "maxSubs": 99,
                            "requireSubtype": "barrier",
                            "payCreditsPerBrokenSub": 1,
                        },
                    },
                },
                {
                    "id": "lobisomem-pump",
                    "label": "1¢: +2 strength",
                    "clickCost": 0,
                    "creditCost": 1,
                    "cost": {"credits": 1},
                    "windows": ["encounter_paw"],
                    "effect": {
                        "op": "do",
                        "action": {"kind": "pump_strength", "amount": 2},
                    },
                },
            ],
            unsupported=[],
        )
        return card

    if cid == "trick-shot":
        return base(
            c,
            subtypes=["run"],
            runEvent={
                "servers": "rd",
                "placeEventCredits": 4,
                "bonusAccess": 1,
                "onSuccessfulRun": {
                    "op": "do",
                    "action": {"kind": "place_event_credits", "amount": 2},
                },
                "onRunEnd": {
                    "op": "do",
                    "action": {
                        "kind": "may_start_run",
                        "servers": "remote",
                    },
                },
            },
            unsupported=[],
        )

    if cid == "privileged-access":
        decline = {
            "id": "decline",
            "label": "Decline",
            "effect": gain("runner", 0),
        }
        install_resource = {
            "op": "do",
            "action": {
                "kind": "may_install_from_heap",
                "types": ["resource"],
                "discount": 2,
            },
        }
        install_program = {
            "op": "do",
            "action": {
                "kind": "may_install_from_heap",
                "types": ["program"],
                "discount": 0,
            },
        }
        return base(
            c,
            subtypes=["run"],
            playRequiresUntagged=True,
            runEvent={
                "servers": "archives",
                "skipBreach": True,
                "onSuccessfulRun": seq(
                    tags(1),
                    install_resource,
                    {
                        "op": "if",
                        "cond": {"op": "threat", "level": 3},
                        "then": install_program,
                    },
                ),
            },
            unsupported=[],
        )

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
            "Null Signal Rebellion Without Rehearsal (NRDB pack rwr) — Liberation "
            "set 2 of 2. Wave is in-progress: simple cards mapped where Effect "
            "IR covers them; remaining cards have explicit unsupported notes."
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
