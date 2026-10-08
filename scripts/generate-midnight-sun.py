#!/usr/bin/env python3
"""Generate Midnight Sun card JSON from pinned pack `ms`.

Catalog source: Null-Signal-Games/netrunner-cards-json (see data/nsg-catalog-pin.json).
Fetch with: python3 scripts/nsg_catalog.py fetch ms msbp

Midnight Sun Booster Pack (`msbp`) titles all reprint in `ms` — absorb under
midnight-sun/; do not emit a separate msbp wave.

Hand-mapped Effect IR where existing primitives suffice; novel CR keywords
(sabotage / mark / charge) and other unmapped clauses list honest unsupported
notes — never invent IR.

Usage: python3 scripts/generate-midnight-sun.py
"""
from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

from nsg_catalog import load_pack_cards

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "midnight-sun"

# Titles that also appear in msbp (primary metadata is the ms printing).
MSBP_ABSORBED = {
    "light-the-fire",
    "revolver",
    "deep-dive",
    "hakarl-1-0",
    "anemone",
    "vladisibirsk-city-grid",
    "azef-protocol",
}


def slugify(title: str) -> str:
    t = unicodedata.normalize("NFKD", title)
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = t.lower()
    t = t.replace("“", "").replace("”", "").replace('"', "")
    t = t.replace("'", "").replace("’", "")
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


def brain(n: int):
    """Core damage (CR §10.4.2b); brain_damage remains a load-time alias."""
    return {"op": "do", "action": {"kind": "core_damage", "amount": n}}


def core(n: int):
    return {"op": "do", "action": {"kind": "core_damage", "amount": n}}


def tags(n: int):
    return {"op": "do", "action": {"kind": "give_tags", "amount": n}}


def gain_clicks(side: str, n: int):
    return {"op": "do", "action": {"kind": "gain_clicks", "side": side, "amount": n}}


def trash_prog(pick="choose"):
    return {"op": "do", "action": {"kind": "trash_program", "pick": pick}}


def trash_res(pick="choose"):
    return {"op": "do", "action": {"kind": "trash_resource", "pick": pick}}


def trash_self():
    return {"op": "do", "action": {"kind": "trash_self"}}


def add_power(n: int):
    return {"op": "do", "action": {"kind": "add_power_counter", "amount": n}}


def remove_tags(n: int):
    return {"op": "do", "action": {"kind": "remove_tags", "amount": n}}


def seq(*effects):
    return {"op": "seq", "effects": list(effects)}


def choose(chooser: str, options: list):
    return {"op": "choose", "chooser": chooser, "options": options}


def iff(cond, then, else_=None):
    e = {"op": "if", "cond": cond, "then": then}
    if else_ is not None:
        e["else"] = else_
    return e


def base(c, **extra):
    subtypes = []
    if c.get("keywords"):
        subtypes = [s.strip().lower() for s in c["keywords"].split(" - ")]
    card = {
        "id": slugify(c["title"]),
        "title": c["title"],
        "wave": "midnight-sun",
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


def note_core_damage_alias() -> str:
    return "Uses core_damage IR (CR §10.4.2b)."


def sabotage(n: int, interactive: bool = True):
    action = {"kind": "sabotage", "amount": n}
    if interactive:
        action["interactive"] = True
    return {"op": "do", "action": action}


def identify_mark():
    return {"op": "do", "action": {"kind": "identify_mark"}}


def start_run_on_mark():
    return {"op": "do", "action": {"kind": "start_run_on_mark"}}


def charge_choose():
    return {"op": "do", "action": {"kind": "charge", "pick": "choose"}}


def may_charge_choose():
    """Optional charge (Runner may decline)."""
    return choose(
        "runner",
        [
            {
                "id": "charge",
                "label": "Charge 1 installed card",
                "effect": charge_choose(),
            },
            {
                "id": "decline",
                "label": "Decline",
                "effect": gain("runner", 0),
            },
        ],
    )


def note_sabotage_trigger(extra: str) -> str:
    return f"{extra} (sabotage IR exists; still needs this trigger wiring)."


def note_mark_remainder(extra: str) -> str:
    return f"{extra} (identify_mark IR exists; remaining mark triggers not wired)."


def note_charge_trigger(extra: str) -> str:
    return f"{extra} (charge IR exists; still needs this trigger/cost wiring)."


def map_card(c: dict) -> dict:
    cid = slugify(c["title"])
    text = strip_html(c.get("text") or "")
    plain = re.sub(r"\s+", " ", text).strip()

    # --- Runner identities ---
    if cid == "esa-afontov-eco-insurrectionist":
        return base(
            c,
            onFirstCoreDamageThisTurn=choose(
                "runner",
                [
                    {
                        "id": "draw-sabotage",
                        "label": "Draw 1 and sabotage 2",
                        "effect": seq(draw("runner", 1), sabotage(2, True)),
                    },
                    {
                        "id": "decline",
                        "label": "Decline",
                        "effect": seq(),
                    },
                ],
            ),
            unsupported=[],
        )
    if cid == "nyusha-sable-sintashta-symphonic-prodigy":
        return base(
            c,
            onTurnBegin=identify_mark(),
            onSuccessfulRunOncePerTurn=True,
            onSuccessfulRun={
                "op": "if",
                "cond": {"op": "attacking_mark"},
                "then": gain_clicks("runner", 1),
            },
            unsupported=[],
        )
    if cid == "captain-padma-isbister-intrepid-explorer":
        return base(
            c,
            onFirstRdRunBeginThisTurn=may_charge_choose(),
            unsupported=[],
        )

    # --- Corp identities ---
    if cid == "pravdivost-consulting-political-solutions":
        return base(
            c,
            onFirstSuccessfulRunThisTurn=choose(
                "corp",
                [
                    {
                        "id": "place-adv",
                        "label": "Place 1 advancement on an advanceable card",
                        "effect": {
                            "op": "do",
                            "action": {"kind": "place_advancements", "amount": 1},
                        },
                    },
                    {
                        "id": "decline",
                        "label": "Decline",
                        "effect": {
                            "op": "do",
                            "action": {
                                "kind": "gain_credits",
                                "side": "corp",
                                "amount": 0,
                            },
                        },
                    },
                ],
            ),
            unsupported=[],
        )
    if cid == "ob-superheavy-logistics-extract-export-excel":
        return base(
            c,
            onRezzedCardTrashed={
                "op": "do",
                "action": {
                    "kind": "search_rd_install_rez_by_printed_rez_cost",
                    "delta": -1,
                },
            },
            unsupported=[],
        )

    # --- Events ---
    if cid == "chastushka":
        return base(
            c,
            subtypes=["run", "sabotage"],
            runEvent={
                "servers": "hq",
                "skipBreach": True,
                "onSuccessfulRun": sabotage(4, interactive=True),
            },
            unsupported=[],
        )
    if cid == "running-hot":
        return base(
            c,
            playAdditionalCost=core(1),
            onPlay=gain_clicks("runner", 3),
            unsupported=[],
        )
    if cid == "steelskin-scarring":
        return base(
            c,
            onPlay=draw("runner", 3),
            onTrashFromGripOrStack={
                "op": "choose",
                "chooser": "runner",
                "options": [
                    {
                        "id": "draw",
                        "label": "Draw 2",
                        "effect": draw("runner", 2),
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
    if cid == "carpe-diem":
        return base(
            c,
            subtypes=["run"],
            onPlay=seq(
                identify_mark(),
                gain("runner", 4),
                choose(
                    "runner",
                    [
                        {
                            "id": "run-mark",
                            "label": "Make a run on the mark",
                            "effect": start_run_on_mark(),
                        },
                        {
                            "id": "decline",
                            "label": "Decline",
                            "effect": seq(),
                        },
                    ],
                ),
            ),
            unsupported=[],
        )
    if cid == "pinhole-threading":
        return base(
            c,
            subtypes=["run"],
            runEvent={
                "servers": "any",
                "skipBreach": True,
                "onSuccessfulRun": {
                    "op": "do",
                    "action": {"kind": "access_one_root_other_server"},
                },
            },
            unsupported=[],
        )
    if cid == "deep-dive":
        return base(
            c,
            playRequiresSuccessfulAllCentralsThisTurn=True,
            onPlay={
                "op": "do",
                "action": {
                    "kind": "deep_dive_resolve",
                    "setAside": 8,
                    "initialAccess": 1,
                },
            },
            unsupported=[],
        )
    if cid == "into-the-depths":
        return base(
            c,
            subtypes=["run"],
            runEvent={"servers": "any"},
            unsupported=[
                note_charge_trigger(
                    "On success, for each ice passed resolve one unique option "
                    "(gain 4¢ / search+install program / charge) — needs passed-ice count + "
                    "exclusive choice resolution"
                ),
            ],
        )
    if cid == "rigging-up":
        return base(
            c,
            subtypes=["mod"],
            onPlay={
                "op": "do",
                "action": {"kind": "may_install_from_grip"},
            },
            unsupported=[
                note_charge_trigger(
                    "Install program or hardware from grip paying 3¢ less; may charge if able — "
                    "discounted install targeting incomplete"
                ),
            ],
        )

    # --- Hardware ---
    if cid == "ghosttongue":
        return base(
            c,
            subtypes=["cybernetic"],
            onInstall=core(1),
            eventPlayCostDiscount=1,
            unsupported=[],
        )
    if cid == "marrow":
        return base(
            c,
            subtypes=["console", "cybernetic"],
            muBonus=1,
            handSizeBonus=3,
            onInstall=core(1),
            onAgendaScored=sabotage(1, interactive=True),
            unsupported=[
                "Console limit (1 console) not enforced.",
            ],
        )
    if cid == "pan-weave":
        return base(
            c,
            subtypes=["cybernetic"],
            onInstall=meat(1),
            onFirstSuccessfulHqRunThisTurn=lose("corp", 1, then=gain("runner", 1)),
            unsupported=[],
        )
    if cid == "virtuoso":
        return base(
            c,
            subtypes=["console"],
            muBonus=1,
            onTurnBegin=identify_mark(),
            unsupported=[
                note_mark_remainder(
                    "First successful mark run: bonus HQ access or breach HQ at run end"
                )
                + "; console limit not enforced.",
            ],
        )
    if cid == "endurance":
        return base(
            c,
            subtypes=["console", "vehicle"],
            muBonus=2,
            powerCountersOnInstall=3,
            unsupported=[
                "First successful run each turn places 1 power counter; 2 hosted power counters "
                "break up to 2 subs — success trigger + break ability not wired "
                "(cost.powerCounters IR exists); console limit not enforced."
            ],
        )

    # --- Programs / breakers ---
    if cid == "begemot":
        card = breaker_card(c, "barrier", 2, 1, break_max=99)
        card["memoryCost"] = 2
        card["onInstall"] = core(1)
        card["strengthBonusPerCoreDamageThisGame"] = 1
        card["unsupported"] = []
        return card
    if cid == "cats-cradle":
        card = breaker_card(c, "code gate", 1, 1, 1, 1)
        card["iceRezCostIncreaseBySubtype"] = {
            "subtype": "code gate",
            "amount": 1,
        }
        card["unsupported"] = []
        return card
    if cid == "cezve":
        return base(
            c,
            memoryCost=1,
            recurringCreditsMax=2,
            recurringSpendFor=["run_central"],
            unsupported=[],
        )
    if cid == "revolver":
        card = breaker_card(c, "sentry", 1, 0, 2, 3)
        card["powerCountersOnInstall"] = 6
        card["breaker"]["breakViaPaidAbilityOnly"] = True
        card["paidAbilities"] = card.get("paidAbilities", []) + [
            {
                "id": "revolver-power-break",
                "label": "Spend 1 power counter: break 1 sentry subroutine",
                "clickCost": 0,
                "creditCost": 0,
                "cost": {"powerCounters": 1},
                "windows": ["encounter_paw"],
                "effect": {
                    "op": "do",
                    "action": {
                        "kind": "break_encounter_subroutine",
                        "requireSubtype": "sentry",
                    },
                },
            },
            {
                "id": "revolver-trash-break",
                "label": "Trash Revolver: break 1 sentry subroutine",
                "clickCost": 0,
                "creditCost": 0,
                "cost": {"trashSelf": True},
                "windows": ["encounter_paw"],
                "effect": {
                    "op": "do",
                    "action": {
                        "kind": "break_encounter_subroutine",
                        "requireSubtype": "sentry",
                    },
                },
            },
        ]
        card["unsupported"] = []
        return card
    if cid == "hyperbaric":
        card = breaker_card(c, "code gate", 0, 1)
        card["powerCountersOnInstall"] = 1
        card["strengthPerPowerCounter"] = True
        card["unsupported"] = [
            "Strength per power counter flag set; 2¢ paid ability to place a power counter "
            "deferred (no add_power_counter IR) — not listed as a free no-op."
        ]
        return card
    if cid == "propeller":
        card = breaker_card(c, "barrier", 0, 1)
        card["powerCountersOnInstall"] = 4
        card["paidAbilities"] = [
            {
                "id": "propeller-power-pump",
                "label": "Spend 1 power counter: +2 strength",
                "clickCost": 0,
                "creditCost": 0,
                "cost": {"powerCounters": 1},
                "windows": ["encounter_paw"],
                "effect": {
                    "op": "do",
                    "action": {"kind": "pump_strength", "amount": 2},
                },
            }
        ]
        card["unsupported"] = []
        return card

    # --- Resources ---
    if cid == "avgustina-ivanovskaya":
        return base(
            c,
            subtypes=["connection"],
            unsupported=[
                note_sabotage_trigger(
                    "First virus program install each turn: sabotage 1 — needs install trigger"
                ),
            ],
        )
    if cid == "light-the-fire":
        return base(
            c,
            subtypes=["sabotage"],
            paidAbilities=[
                {
                    "id": "ltf-run",
                    "label": (
                        "[click], trash, suffer 1 core damage: run a remote; "
                        "blank root; on success trash root"
                    ),
                    "clickCost": 1,
                    "creditCost": 0,
                    "cost": {
                        "clicks": 1,
                        "trashSelf": True,
                        "coreDamage": 1,
                    },
                    "windows": ["runner_action_paw"],
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "gain_credits",
                            "side": "runner",
                            "amount": 0,
                        },
                    },
                    "startsRun": {
                        "servers": "remote",
                        "blankAttackedServerRoot": True,
                        "onSuccessfulRun": {
                            "op": "do",
                            "action": {"kind": "trash_attacked_server_root"},
                        },
                    },
                }
            ],
            unsupported=[],
        )
    if cid == "the-twinning":
        return base(
            c,
            subtypes=["virtual"],
            powerOnFirstInstalledCardCreditSpendThisTurn=True,
            removePowerForBonusAccessOnHqRdBreach=2,
            unsupported=[],
        )
    if cid == "backstitching":
        return base(
            c,
            subtypes=["virtual"],
            onTurnBegin=identify_mark(),
            unsupported=[
                note_mark_remainder(
                    "Encounter ice on mark run: trash to bypass — needs mark-encounter bypass"
                ),
            ],
        )
    if cid == "no-free-lunch":
        return base(
            c,
            paidAbilities=[
                {
                    "id": "nfl-credits",
                    "label": "Trash No Free Lunch: gain 3¢",
                    "clickCost": 0,
                    "creditCost": 0,
                    "cost": {"trashSelf": True},
                    "windows": ["runner_action_paw"],
                    "effect": gain("runner", 3),
                },
                {
                    "id": "nfl-tag",
                    "label": "Trash No Free Lunch: remove 1 tag",
                    "clickCost": 0,
                    "creditCost": 0,
                    "cost": {"trashSelf": True},
                    "windows": ["runner_action_paw"],
                    "effect": remove_tags(1),
                },
            ],
            unsupported=[],
        )
    if cid == "daeg-first-net-cat":
        return base(
            c,
            subtypes=["companion", "virtual"],
            onAgendaScoredOrStolen=may_charge_choose(),
            unsupported=[],
        )
    if cid == "environmental-testing":
        return base(
            c,
            onProgramOrHardwareInstall=add_power(1),
            onPowerCountersGte={
                "amount": 4,
                "effect": seq(trash_self(), gain("runner", 9)),
            },
            unsupported=[],
        )
    if cid == "stoneship-chart-room":
        return base(
            c,
            subtypes=["location"],
            paidAbilities=[
                {
                    "id": "stoneship-draw",
                    "label": "Trash Stoneship Chart Room: draw 2",
                    "clickCost": 0,
                    "creditCost": 0,
                    "cost": {"trashSelf": True},
                    "windows": ["runner_action_paw"],
                    "effect": draw("runner", 2),
                },
                {
                    "id": "stoneship-charge",
                    "label": "Trash Stoneship Chart Room: charge 1 installed card",
                    "clickCost": 0,
                    "creditCost": 0,
                    "cost": {"trashSelf": True},
                    "windows": ["runner_action_paw"],
                    "effect": charge_choose(),
                },
            ],
            unsupported=[],
        )

    # --- Agendas ---
    if cid == "elivagar-bifurcation":
        return base(
            c,
            subtypes=["security"],
            onScore={
                "op": "do",
                "action": {
                    "kind": "may_derez_installed",
                    "excludeSelf": True,
                },
            },
            unsupported=[],
        )
    if cid == "midnight-3-arcology":
        return base(
            c,
            subtypes=["expansion"],
            onScore=seq(
                draw("corp", 3),
                choose(
                    "corp",
                    [
                        {
                            "id": "skip-discard",
                            "label": "Skip discard step this turn",
                            "effect": {
                                "op": "do",
                                "action": {"kind": "skip_discard_this_turn"},
                            },
                        },
                        {
                            "id": "decline",
                            "label": "Decline",
                            "effect": {
                                "op": "do",
                                "action": {
                                    "kind": "gain_credits",
                                    "side": "corp",
                                    "amount": 0,
                                },
                            },
                        },
                    ],
                ),
            ),
            unsupported=[],
        )
    if cid == "blood-in-the-water":
        return base(
            c,
            subtypes=["research"],
            advancementRequirementEqualsRunnerGrip=True,
            unsupported=[],
        )
    if cid == "regenesis":
        return base(
            c,
            subtypes=["research"],
            unsupported=[
                "On score if no Corp cards added to Archives this turn: reveal facedown agenda "
                "in Archives and add to score area — needs Archives-empty gate + score-from-archives."
            ],
        )
    if cid == "artificial-cryptocrash":
        return base(
            c,
            subtypes=["initiative"],
            onScore=lose("runner", 7),
            unsupported=[],
        )
    if cid == "azef-protocol":
        return base(
            c,
            subtypes=["security"],
            scoreAdditionalCost={
                "op": "do",
                "action": {"kind": "must_trash_installed", "excludeSelf": True},
            },
            onScore=meat(2),
            unsupported=[],
        )

    # --- Assets ---
    if cid == "refuge-campaign":
        return base(
            c,
            subtypes=["advertisement"],
            onTurnBegin=gain("corp", 2),
            unsupported=[],
        )
    if cid == "trieste-model-bioroids":
        return base(
            c,
            subtypes=["bioroid"],
            unsupported=[
                "On rez choose rezzed bioroid ice; Runner card abilities cannot break its "
                "subroutines — needs chosen-ice lock + break forbid."
            ],
        )
    if cid == "bladderwort":
        return base(
            c,
            subtypes=["hostile"],
            onTurnBegin=seq(
                gain("corp", 1),
                iff(
                    {"op": "credits_lte", "side": "corp", "amount": 4},
                    net(1),
                ),
            ),
            unsupported=[],
        )
    if cid == "moon-pool":
        return base(
            c,
            subtypes=["facility"],
            paidAbilities=[
                {
                    "id": "moon-pool-resolve",
                    "label": "[click], trash: Remove Moon Pool from the game",
                    "clickCost": 1,
                    "creditCost": 0,
                    "cost": {"clicks": 1, "trashSelf": True},
                    "windows": ["corp_action_paw"],
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "moon_pool_resolve",
                            "trashHqMax": 2,
                            "revealArchivesMax": 2,
                        },
                    },
                }
            ],
            unsupported=[],
        )
    if cid == "chekist-scion":
        return base(
            c,
            subtypes=["ambush"],
            canAdvance=True,
            onAccess={
                "op": "do",
                "action": {
                    "kind": "give_tags_per_advancement",
                    "base": 1,
                    "per": 1,
                },
            },
            unsupported=[],
        )
    if cid == "drago-ivanov":
        return base(
            c,
            subtypes=["executive"],
            canAdvance=True,
            paidAbilities=[
                {
                    "id": "drago-tag",
                    "label": "Remove 2 advancements: give Runner 1 tag",
                    "clickCost": 1,
                    "creditCost": 0,
                    "cost": {"clicks": 1, "advancementTokens": 2},
                    "windows": ["corp_action_paw"],
                    "effect": {
                        "op": "do",
                        "action": {"kind": "give_tags", "amount": 1},
                    },
                }
            ],
            unsupported=[],
        )
    if cid == "ubiquitous-vig":
        return base(
            c,
            subtypes=["advertisement"],
            canAdvance=True,
            onTurnBegin={
                "op": "do",
                "action": {
                    "kind": "gain_credits",
                    "side": "corp",
                    "amount": 0,
                    "tally": {
                        "count": "source_advancement_tokens",
                        "per": 1,
                        "side": "source",
                    },
                },
            },
            unsupported=[],
        )
    if cid == "svyatogor-excavator":
        return base(
            c,
            subtypes=["industrial"],
            onTurnBegin={
                "op": "do",
                "action": {
                    "kind": "may_trash_installed",
                    "excludeSelf": True,
                    "then": {
                        "op": "do",
                        "action": {
                            "kind": "gain_credits",
                            "side": "corp",
                            "amount": 3,
                        },
                    },
                },
            },
            unsupported=[],
        )

    # --- Ice ---
    if cid == "echo":
        return base(
            c,
            subtypes=["barrier", "harmonic"],
            powerCounterOnHarmonicIceRez=True,
            etrSubroutinesPerPowerCounter=True,
            subroutines=[],
            unsupported=[],
        )
    if cid == "hakarl-1-0":
        return base(
            c,
            subtypes=["barrier", "bioroid", "ap"],
            onRez={
                "op": "if",
                "cond": {"op": "source_protects_attacked_server"},
                "then": {
                    "op": "do",
                    "action": {
                        "kind": "may_derez_installed",
                        "excludeSelf": True,
                        "then": {
                            "op": "do",
                            "action": {
                                "kind": "forbid_bioroid_ice_paid_abilities_this_turn"
                            },
                        },
                    },
                },
            },
            subroutines=[
                {
                    "id": "hakarl-core",
                    "text": "Do 1 core damage.",
                    "effect": core(1),
                },
                {"id": "hakarl-etr", "text": "End the run.", "effect": etr()},
            ],
            paidAbilities=[
                {
                    "id": "hakarl-click-break",
                    "label": "Lose [click]: Break 1 subroutine on Hákarl 1.0",
                    "clickCost": 1,
                    "creditCost": 0,
                    "cost": {"clicks": 1},
                    "windows": ["encounter_paw"],
                    "effect": {"op": "do", "action": {"kind": "break_host_subroutine"}},
                }
            ],
            unsupported=[],
        )
    if cid == "wave":
        return base(
            c,
            subtypes=["code gate", "harmonic"],
            unsupported=[
                "On rez during run vs this server: may search R&D for ice, reveal, add to HQ; "
                "subroutine: gain 1¢ per rezzed harmonic ice — per-harmonic gain not modeled "
                "(sub omitted rather than flat 1¢)."
            ],
        )
    if cid == "anemone":
        return base(
            c,
            subtypes=["sentry", "ap"],
            onRez={
                "op": "if",
                "cond": {"op": "source_protects_attacked_server"},
                "then": choose(
                    "corp",
                    [
                        {
                            "id": "trash-hq-net",
                            "label": "Trash 1 from HQ: do 2 net damage",
                            "effect": {
                                "op": "do",
                                "action": {
                                    "kind": "trash_hq",
                                    "pick": "first",
                                    "then": net(2),
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
            },
            subroutines=[
                {"id": "anemone-net", "text": "Do 1 net damage.", "effect": net(1)}
            ],
            unsupported=[],
        )
    if cid == "bathynomus":
        return base(
            c,
            subtypes=["sentry", "ap"],
            strengthBonusProtectingArchives=3,
            subroutines=[
                {"id": "bath-net", "text": "Do 3 net damage.", "effect": net(3)}
            ],
            unsupported=[],
        )
    if cid == "ivik":
        return base(
            c,
            subtypes=["barrier", "ap"],
            rezCostDiscountPerRezzedSubtype={
                "subtype": "code gate",
                "amount": 1,
            },
            subroutines=[
                {"id": "ivik-net", "text": "Do 2 net damage.", "effect": net(2)},
                {"id": "ivik-etr", "text": "End the run.", "effect": etr()},
            ],
            unsupported=[],
        )
    if cid == "mestnichestvo":
        return base(
            c,
            subtypes=["code gate"],
            canAdvance=True,
            onEncounter=choose(
                "corp",
                [
                    {
                        "id": "remove-adv",
                        "label": "Remove 1 advancement: Runner loses 3¢",
                        "effect": {
                            "op": "do",
                            "action": {
                                "kind": "remove_advancements",
                                "amount": 1,
                                "then": lose("runner", 3),
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
            subroutines=[
                {
                    "id": "mest-lose",
                    "text": "The Runner loses 3¢.",
                    "effect": lose("runner", 3),
                },
                {"id": "mest-etr", "text": "End the run.", "effect": etr()},
            ],
            unsupported=[],
        )
    if cid == "vasilisa":
        return base(
            c,
            subtypes=["sentry", "observer"],
            onEncounter=choose(
                "corp",
                [
                    {
                        "id": "pay-adv",
                        "label": "Pay 1¢: place 1 advancement on advanceable card",
                        "effect": seq(
                            lose("corp", 1),
                            {
                                "op": "do",
                                "action": {"kind": "place_advancements", "amount": 1},
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
            subroutines=[
                {
                    "id": "vasilisa-tag",
                    "text": "Give the Runner 1 tag.",
                    "effect": tags(1),
                }
            ],
            unsupported=[],
        )
    if cid == "envelopment":
        return base(
            c,
            subtypes=["barrier"],
            etrSubroutinesPerPowerCounter=True,
            onRez={"op": "do", "action": {"kind": "add_power_counter", "amount": 4}},
            onTurnBegin={"op": "do", "action": {"kind": "remove_power_counter", "amount": 1}},
            subroutines=[
                {
                    "id": "env-trash",
                    "text": "Trash this ice.",
                    "effect": {"op": "do", "action": {"kind": "trash_self"}},
                }
            ],
            unsupported=[],
        )
    if cid == "maskirovka":
        return base(
            c,
            subtypes=["barrier"],
            subroutines=[
                {"id": "mask-gain", "text": "Gain 2¢.", "effect": gain("corp", 2)},
                {"id": "mask-etr", "text": "End the run.", "effect": etr()},
            ],
            unsupported=[],
        )
    if cid == "stavka":
        return base(
            c,
            subtypes=["sentry", "destroyer"],
            onRez={
                "op": "do",
                "action": {
                    "kind": "may_trash_installed",
                    "excludeSelf": True,
                    "then": {
                        "op": "do",
                        "action": {"kind": "fortify_ice", "amount": 5},
                    },
                },
            },
            subroutines=[
                {
                    "id": "stavka-trash1",
                    "text": "Trash 1 installed program.",
                    "effect": trash_prog(),
                },
                {
                    "id": "stavka-trash2",
                    "text": "Trash 1 installed program.",
                    "effect": trash_prog(),
                },
            ],
            unsupported=[],
        )

    # --- Operations ---
    if cid == "big-deal":
        return base(
            c,
            subtypes=["terminal"],
            endsActionPhase=True,
            onPlay={
                "op": "do",
                "action": {
                    "kind": "place_advancements",
                    "amount": 4,
                    "thenMayScore": True,
                    "then": {"op": "do", "action": {"kind": "rfg_self"}},
                },
            },
            unsupported=[],
        )
    if cid == "mitosis":
        return base(
            c,
            subtypes=["double"],
            playAdditionalClick=True,
            onPlay={
                "op": "do",
                "action": {
                    "kind": "install_hq_new_remotes_with_advancements",
                    "max": 2,
                    "advancements": 2,
                },
            },
            unsupported=[],
        )
    if cid == "backroom-machinations":
        return base(
            c,
            subtypes=["gray ops"],
            playRequiresTagged=True,
            playAdditionalCost=remove_tags(1),
            agendaPoints=1,
            onPlay={
                "op": "do",
                "action": {"kind": "score_self_as_agenda", "agendaPoints": 1},
            },
            unsupported=[],
        )
    if cid == "extract":
        return base(
            c,
            subtypes=["transaction"],
            onPlay=seq(
                gain("corp", 6),
                {
                    "op": "do",
                    "action": {
                        "kind": "may_trash_installed",
                        "excludeSelf": True,
                        "then": {
                            "op": "do",
                            "action": {
                                "kind": "gain_credits",
                                "side": "corp",
                                "amount": 3,
                            },
                        },
                    },
                },
            ),
            unsupported=[],
        )
    if cid == "mutually-assured-destruction":
        return base(
            c,
            subtypes=["triple"],
            playAdditionalClicks=2,
            onPlay={
                "op": "do",
                "action": {"kind": "trash_any_rezzed_give_tags"},
            },
            unsupported=[],
        )
    if cid == "trust-operation":
        return base(
            c,
            subtypes=["gray ops"],
            playRequiresTagged=True,
            onPlay=seq(
                trash_res(),
                {
                    "op": "do",
                    "action": {"kind": "install_and_rez_from_archives_free"},
                },
            ),
            unsupported=[],
        )

    # --- Upgrades ---
    if cid == "mavirus":
        return base(
            c,
            subtypes=["ambush"],
            onAccess={
                "op": "seq",
                "effects": [
                    {
                        "op": "if",
                        "cond": {"op": "source_rezzed"},
                        "then": net(1),
                    },
                    {
                        "op": "choose",
                        "chooser": "corp",
                        "options": [
                            {
                                "id": "purge",
                                "label": "Purge virus counters",
                                "effect": {
                                    "op": "do",
                                    "action": {"kind": "purge_virus_counters"},
                                },
                            },
                            {
                                "id": "decline",
                                "label": "Decline",
                                "effect": gain("corp", 0),
                            },
                        ],
                    },
                ],
            },
            onTrash={"op": "do", "action": {"kind": "purge_virus_counters"}},
            unsupported=[],
        )
    if cid == "vladisibirsk-city-grid":
        return base(
            c,
            subtypes=["region"],
            canAdvance=True,
            paidAbilities=[
                {
                    "id": "vlad-place",
                    "label": "Remove 2 advancements: place 2 on another root card",
                    "clickCost": 1,
                    "creditCost": 0,
                    "cost": {"clicks": 1, "advancementTokens": 2},
                    "oncePerTurn": True,
                    "windows": ["corp_action_paw"],
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "place_advancements",
                            "amount": 2,
                            "sameServerRootAsSource": True,
                            "excludeSelf": True,
                        },
                    },
                }
            ],
            unsupported=[],
        )

    # Fallback: skeleton with full text as unsupported
    card = base(c)
    card["unsupported"] = [
        f"Full text not yet mapped to IR: {plain[:240]}"
    ]
    return card


def main():
    ms = sorted(
        load_pack_cards("ms"),
        key=lambda c: c.get("position", 0),
    )
    assert len(ms) == 65, len(ms)

    msbp = load_pack_cards("msbp")
    assert len(msbp) == 7, len(msbp)
    msbp_slugs = {slugify(c["title"]) for c in msbp}
    assert msbp_slugs == MSBP_ABSORBED, (msbp_slugs, MSBP_ABSORBED)
    ms_slugs = {slugify(c["title"]) for c in ms}
    assert msbp_slugs <= ms_slugs, msbp_slugs - ms_slugs

    OUT.mkdir(parents=True, exist_ok=True)
    for p in OUT.glob("*.json"):
        p.unlink()

    written = []
    for c in ms:
        mapped = map_card(c)
        cid = mapped["id"]
        path = OUT / f"{cid}.json"
        path.write_text(json.dumps(mapped, indent=2, ensure_ascii=False) + "\n")
        written.append(cid)

    assert len(written) == 65, len(written)

    full = sum(
        1
        for cid in written
        if not json.loads((OUT / f"{cid}.json").read_text()).get("unsupported")
    )
    partial = len(written) - full

    manifest = {
        "pack": "midnight-sun",
        "nrdbPackCode": "ms",
        "count": 65,
        "written": 65,
        "status": "in-progress",
        "msbpAbsorbed": sorted(MSBP_ABSORBED),
        "notes": (
            "Midnight Sun Booster Pack (msbp) titles reprint in ms — absorbed here; "
            "no separate msbp wave. Wave is in-progress: many cards have explicit "
            "unsupported notes (sabotage/mark/charge and other IR gaps)."
        ),
        "cards": written,
    }
    (OUT / "_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"
    )

    print(f"Wrote {len(written)} cards to {OUT}")
    print(f"Among written: full={full} partial={partial}")
    print(f"msbp absorbed: {sorted(MSBP_ABSORBED)}")
    print("POOL_IDS=" + json.dumps(written))


if __name__ == "__main__":
    main()
