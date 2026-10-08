#!/usr/bin/env python3
"""Generate Uprising card JSON from pinned pack `ur`.

Catalog source: Null-Signal-Games/netrunner-cards-json (see data/nsg-catalog-pin.json).
Fetch with: python3 scripts/nsg_catalog.py fetch ur

Uprising Booster Pack (`urbp`) titles are absorbed into `ur` printings
(same pattern as Midnight Sun Booster → ms).

Hand-mapped Effect IR only where existing primitives fully cover the card;
everything else lists honest unsupported notes — never invent IR.

Usage: python3 scripts/generate-uprising.py
"""
from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

from nsg_catalog import load_pack_cards

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "uprising"
WAVE = "uprising"
PACK = "ur"
EXPECTED = 65


def slugify(title: str) -> str:
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


def gain(side: str, n: int):
    return {"op": "do", "action": {"kind": "gain_credits", "side": side, "amount": n}}


def gain_clicks(side: str, n: int):
    return {"op": "do", "action": {"kind": "gain_clicks", "side": side, "amount": n}}


def take_hosted(n: int):
    return {"op": "do", "action": {"kind": "take_hosted_credits", "amount": n}}


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
    if c.get("uniqueness"):
        card["unique"] = True
    card.update(extra)
    return card


def breaker_card(
    c,
    subtype,
    strength,
    break_c,
    pump_c=None,
    pump_s=None,
    break_max=None,
    **extra,
):
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


def map_card(c: dict) -> dict:
    cid = slugify(c["title"])
    text = strip_html(c.get("text") or "")
    plain = re.sub(r"\s+", " ", text).strip()

    # --- v1.35.0 kickoff: existing IR only ---

    if cid == "daily-casts":
        return base(
            c,
            hostedCreditsOnInstall=8,
            onTurnBegin=take_hosted(2),
            unsupported=[],
        )

    if cid == "bass-ch1r180g4":
        return base(
            c,
            paidAbilities=[
                {
                    "id": "bass-ch1r180g4-clicks",
                    "label": "[click], [trash]: Gain [click][click]",
                    "clickCost": 1,
                    "creditCost": 0,
                    "cost": {"clicks": 1, "trashSelf": True},
                    "windows": ["corp_action_paw"],
                    "effect": gain_clicks("corp", 2),
                }
            ],
            unsupported=[],
        )

    if cid == "makler":
        return breaker_card(
            c,
            "barrier",
            2,
            2,
            2,
            2,
            break_max=2,
            onFullyBreakOncePerTurn=gain("runner", 1),
            unsupported=[],
        )

    # --- v1.36.0 A-slice ---

    if cid == "la-costa-grid":
        return base(
            c,
            remoteOnly=True,
            onTurnBegin={
                "op": "do",
                "action": {
                    "kind": "place_advancements",
                    "amount": 1,
                    "sameServerRootAsSource": True,
                    "pick": "choose",
                },
            },
            unsupported=[],
        )

    if cid == "gold-farmer":
        etr_unless_3 = {
            "op": "do",
            "action": {
                "kind": "unless",
                "payer": "runner",
                "cost": {
                    "op": "do",
                    "action": {
                        "kind": "lose_credits",
                        "side": "runner",
                        "amount": 3,
                    },
                },
                "instruction": {
                    "op": "do",
                    "action": {"kind": "end_the_run"},
                },
            },
        }
        return base(
            c,
            runnerLoseCreditsOnBreakPrintedSubroutine=1,
            subroutines=[
                {
                    "id": "gold-farmer-1",
                    "text": "End the run unless the Runner pays 3[credit].",
                    "effect": etr_unless_3,
                },
                {
                    "id": "gold-farmer-2",
                    "text": "End the run unless the Runner pays 3[credit].",
                    "effect": etr_unless_3,
                },
            ],
            unsupported=[],
        )

    if cid == "mantle":
        return base(
            c,
            recurringCreditsMax=1,
            recurringSpendFor=["use_program", "use_hardware"],
            unsupported=[],
        )

    if cid == "false-lead":
        return base(
            c,
            paidAbilities=[
                {
                    "id": "false-lead-forfeit",
                    "label": "Forfeit: if Runner has 2+ [click], they lose [click][click]",
                    "clickCost": 0,
                    "creditCost": 0,
                    "cost": {"trashSelf": True},
                    "windows": ["corp_action_paw"],
                    "effect": {
                        "op": "if",
                        "cond": {
                            "op": "clicks_gte",
                            "side": "runner",
                            "amount": 2,
                        },
                        "then": {
                            "op": "do",
                            "action": {
                                "kind": "lose_clicks",
                                "side": "runner",
                                "amount": 2,
                            },
                        },
                    },
                }
            ],
            unsupported=[],
        )

    if cid == "bellona":
        return base(
            c,
            stealAdditionalCredits=5,
            onScore=gain("corp", 5),
            unsupported=[],
        )

    # --- v1.37.0 B-slice ---

    if cid == "euler":
        return base(
            c,
            breaker={
                "breaksSubtype": "code gate",
                "strength": 2,
                "breakCredits": 2,
                "breakMaxSubs": 2,
                "pumpCredits": 1,
                "pumpStrength": 1,
                "breakViaPaidAbilityOnly": True,
            },
            paidAbilities=[
                {
                    "id": "euler-break-install",
                    "label": "0¢: Break 1 code gate subroutine (installed this turn)",
                    "clickCost": 0,
                    "creditCost": 0,
                    "cost": {"credits": 0},
                    "windows": ["encounter_paw"],
                    "requireInstalledThisTurn": True,
                    "requireEncounterSubtype": "code gate",
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
                    "id": "euler-break",
                    "label": "2¢: Break up to 2 code gate subroutines",
                    "clickCost": 0,
                    "creditCost": 2,
                    "cost": {"credits": 2},
                    "windows": ["encounter_paw"],
                    "requireEncounterSubtype": "code gate",
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "break_encounter_subroutine",
                            "maxSubs": 2,
                            "requireSubtype": "code gate",
                        },
                    },
                },
                {
                    "id": "euler-pump",
                    "label": "1¢: +1 strength",
                    "clickCost": 0,
                    "creditCost": 1,
                    "cost": {"credits": 1},
                    "windows": ["encounter_paw"],
                    "effect": {
                        "op": "do",
                        "action": {"kind": "pump_strength", "amount": 1},
                    },
                },
            ],
            unsupported=[],
        )

    if cid == "penrose":
        return base(
            c,
            breaker={
                "breaksSubtype": "code gate",
                "strength": 2,
                "breakCredits": 1,
                "breakMaxSubs": 1,
                "pumpCredits": 1,
                "pumpStrength": 3,
                "breakViaPaidAbilityOnly": True,
            },
            paidAbilities=[
                {
                    "id": "penrose-break-barrier",
                    "label": "1¢: Break 1 barrier subroutine (installed this turn)",
                    "clickCost": 0,
                    "creditCost": 1,
                    "cost": {"credits": 1},
                    "windows": ["encounter_paw"],
                    "requireInstalledThisTurn": True,
                    "requireEncounterSubtype": "barrier",
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "break_encounter_subroutine",
                            "maxSubs": 1,
                            "requireSubtype": "barrier",
                        },
                    },
                },
                {
                    "id": "penrose-break-cg",
                    "label": "1¢: Break 1 code gate subroutine",
                    "clickCost": 0,
                    "creditCost": 1,
                    "cost": {"credits": 1},
                    "windows": ["encounter_paw"],
                    "requireEncounterSubtype": "code gate",
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
                    "id": "penrose-pump",
                    "label": "1¢: +3 strength (stealth credits only)",
                    "clickCost": 0,
                    "creditCost": 1,
                    "cost": {"credits": 1, "creditsFromStealthOnly": True},
                    "windows": ["encounter_paw"],
                    "effect": {
                        "op": "do",
                        "action": {"kind": "pump_strength", "amount": 3},
                    },
                },
            ],
            unsupported=[],
        )

    if cid == "odore":
        return base(
            c,
            breaker={
                "breaksSubtype": "sentry",
                "strength": 0,
                "breakCredits": 2,
                "breakMaxSubs": 99,
                "pumpCredits": 3,
                "pumpStrength": 3,
                "breakViaPaidAbilityOnly": True,
            },
            paidAbilities=[
                {
                    "id": "odore-break-any",
                    "label": "2¢: Break any number of sentry subroutines",
                    "clickCost": 0,
                    "creditCost": 2,
                    "cost": {"credits": 2},
                    "windows": ["encounter_paw"],
                    "requireEncounterSubtype": "sentry",
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "break_encounter_subroutine",
                            "maxSubs": 99,
                            "requireSubtype": "sentry",
                        },
                    },
                },
                {
                    "id": "odore-break-virtual",
                    "label": "0¢: Break 1 sentry (3+ virtual resources)",
                    "clickCost": 0,
                    "creditCost": 0,
                    "cost": {"credits": 0},
                    "windows": ["encounter_paw"],
                    "requireInstalledVirtualResourcesGte": 3,
                    "requireEncounterSubtype": "sentry",
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "break_encounter_subroutine",
                            "maxSubs": 1,
                            "requireSubtype": "sentry",
                        },
                    },
                },
                {
                    "id": "odore-pump",
                    "label": "3¢: +3 strength",
                    "clickCost": 0,
                    "creditCost": 3,
                    "cost": {"credits": 3},
                    "windows": ["encounter_paw"],
                    "effect": {
                        "op": "do",
                        "action": {"kind": "pump_strength", "amount": 3},
                    },
                },
            ],
            unsupported=[],
        )

    if cid == "moshing":
        return base(
            c,
            playRequiresOtherGripCardsGte=3,
            playAdditionalCost={
                "op": "do",
                "action": {"kind": "trash_n_from_grip", "amount": 3},
            },
            onPlay={
                "op": "seq",
                "effects": [
                    gain("runner", 3),
                    {
                        "op": "do",
                        "action": {
                            "kind": "draw",
                            "side": "runner",
                            "amount": 3,
                        },
                    },
                ],
            },
            unsupported=[],
        )

    if cid == "cayambe-grid":
        return base(
            c,
            onTurnBegin={
                "op": "do",
                "action": {
                    "kind": "place_advancements",
                    "amount": 1,
                    "onlyIceProtectingSourceServer": True,
                    "pick": "choose",
                },
            },
            approachServerEtrUnlessCreditsPerAdvancedIce=2,
            unsupported=[],
        )

    if cid == "cyberdex-sandbox":
        return base(
            c,
            onVirusPurgeOncePerTurn=True,
            onVirusPurge=gain("corp", 4),
            onScore={
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
            },
            unsupported=[],
        )

    if cid == "dreamnet":
        return base(
            c,
            onFirstSuccessfulRunThisTurn={
                "op": "seq",
                "effects": [
                    {
                        "op": "do",
                        "action": {
                            "kind": "draw",
                            "side": "runner",
                            "amount": 1,
                        },
                    },
                    {
                        "op": "if",
                        "cond": {
                            "op": "or",
                            "conds": [
                                {
                                    "op": "identity_has_subtype",
                                    "subtype": "digital",
                                },
                                {"op": "link_gte", "amount": 2},
                            ],
                        },
                        "then": gain("runner", 1),
                    },
                ],
            },
            unsupported=[],
        )

    if cid == "swift":
        return base(
            c,
            muBonus=1,
            gainClickOnFirstRunEventThisTurn=True,
            unsupported=[],
        )

    if cid == "self-modifying-code":
        return base(
            c,
            paidAbilities=[
                {
                    "id": "smc-search",
                    "label": "2¢, [trash]: Search stack for a program and install it",
                    "clickCost": 0,
                    "creditCost": 2,
                    "cost": {"credits": 2, "trashSelf": True},
                    "windows": ["runner_action_paw"],
                    "effect": {
                        "op": "do",
                        "action": {"kind": "search_stack_program_install"},
                    },
                }
            ],
            unsupported=[],
        )

    # --- v1.38.0 C-slice ---

    if cid == "afterimage":
        return base(
            c,
            breaker={
                "breaksSubtype": "sentry",
                "strength": 2,
                "breakCredits": 1,
                "breakMaxSubs": 2,
                "pumpCredits": 1,
                "pumpStrength": 2,
                "breakViaPaidAbilityOnly": True,
            },
            paidAbilities=[
                {
                    "id": "afterimage-bypass",
                    "label": "2¢: Bypass encountered sentry (stealth; once per turn)",
                    "clickCost": 0,
                    "creditCost": 2,
                    "cost": {"credits": 2, "creditsFromStealthOnly": True},
                    "windows": ["encounter_paw"],
                    "oncePerTurn": True,
                    "requireEncounterSubtype": "sentry",
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "bypass_current_ice",
                            "requireSubtype": "sentry",
                        },
                    },
                },
                {
                    "id": "afterimage-break",
                    "label": "1¢: Break up to 2 sentry subroutines",
                    "clickCost": 0,
                    "creditCost": 1,
                    "cost": {"credits": 1},
                    "windows": ["encounter_paw"],
                    "requireEncounterSubtype": "sentry",
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "break_encounter_subroutine",
                            "maxSubs": 2,
                            "requireSubtype": "sentry",
                        },
                    },
                },
                {
                    "id": "afterimage-pump",
                    "label": "1¢: +2 strength (stealth credits only)",
                    "clickCost": 0,
                    "creditCost": 1,
                    "cost": {"credits": 1, "creditsFromStealthOnly": True},
                    "windows": ["encounter_paw"],
                    "effect": {
                        "op": "do",
                        "action": {"kind": "pump_strength", "amount": 2},
                    },
                },
            ],
            unsupported=[],
        )

    if cid == "penumbral-toolkit":
        return base(
            c,
            hostedCreditsOnInstall=4,
            spendHostedCreditsDuringRuns=True,
            installCostDiscountIfSuccessfulHqRunThisTurn=2,
            unsupported=[],
        )

    if cid == "f2p":
        return base(
            c,
            paidAbilities=[
                {
                    "id": "f2p-break",
                    "label": "2¢: Break 1 subroutine (Runner; untagged)",
                    "clickCost": 0,
                    "creditCost": 2,
                    "cost": {"credits": 2},
                    "windows": ["encounter_paw"],
                    "usableByAnyPlayer": True,
                    "requiresUntagged": True,
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "break_encounter_subroutine",
                            "maxSubs": 1,
                        },
                    },
                }
            ],
            subroutines=[
                {
                    "id": "f2p-bounce",
                    "text": "Add 1 installed Runner card to the grip.",
                    "effect": {
                        "op": "do",
                        "action": {"kind": "add_installed_runner_to_grip"},
                    },
                },
                {
                    "id": "f2p-tag",
                    "text": "Give the Runner 1 tag.",
                    "effect": {
                        "op": "do",
                        "action": {"kind": "give_tags", "amount": 1},
                    },
                },
            ],
            unsupported=[],
        )

    if cid == "transport-monopoly":
        return base(
            c,
            onScore={
                "op": "do",
                "action": {"kind": "add_agenda_counter", "amount": 2},
            },
            paidAbilities=[
                {
                    "id": "transport-monopoly-block",
                    "label": "Hosted agenda counter: this run cannot be declared successful",
                    "clickCost": 0,
                    "creditCost": 0,
                    "cost": {"agendaCounters": 1},
                    "windows": [
                        "approach_paw",
                        "encounter_paw",
                        "approach_server_paw",
                    ],
                    "oncePerTurn": True,
                    "requireDuringRun": True,
                    "effect": {
                        "op": "do",
                        "action": {"kind": "prevent_declare_run_successful"},
                    },
                }
            ],
            unsupported=[],
        )

    if cid == "akhet":
        return base(
            c,
            canAdvance=True,
            strengthBonusAtAdvancements={"threshold": 3, "bonus": 3},
            maxPrintedSubsBreakablePerEncounterAtAdvancements={
                "threshold": 3,
                "max": 1,
            },
            subroutines=[
                {
                    "id": "akhet-adv",
                    "text": "Gain 1[credit]. Place 1 advancement counter on an installed card.",
                    "effect": {
                        "op": "seq",
                        "effects": [
                            gain("corp", 1),
                            {
                                "op": "do",
                                "action": {
                                    "kind": "place_advancements",
                                    "amount": 1,
                                    "pick": "choose",
                                },
                            },
                        ],
                    },
                },
                {
                    "id": "akhet-etr",
                    "text": "End the run.",
                    "effect": {
                        "op": "do",
                        "action": {"kind": "end_the_run"},
                    },
                },
            ],
            unsupported=[],
        )

    if cid == "colossus":
        return base(
            c,
            canAdvance=True,
            strengthPerAdvancement=1,
            subroutines=[
                {
                    "id": "colossus-tag",
                    "text": "Give the Runner 1 tag. If 3+ advancements, instead give 2 tags.",
                    "effect": {
                        "op": "if",
                        "cond": {"op": "advancements_gte", "amount": 3},
                        "then": {
                            "op": "do",
                            "action": {"kind": "give_tags", "amount": 2},
                        },
                        "else": {
                            "op": "do",
                            "action": {"kind": "give_tags", "amount": 1},
                        },
                    },
                },
                {
                    "id": "colossus-trash",
                    "text": "Trash 1 installed program. If 3+ advancements, also trash 1 installed resource.",
                    "effect": {
                        "op": "if",
                        "cond": {"op": "advancements_gte", "amount": 3},
                        "then": {
                            "op": "seq",
                            "effects": [
                                {
                                    "op": "do",
                                    "action": {
                                        "kind": "trash_program",
                                        "pick": "choose",
                                    },
                                },
                                {
                                    "op": "do",
                                    "action": {
                                        "kind": "trash_resource",
                                        "pick": "choose",
                                    },
                                },
                            ],
                        },
                        "else": {
                            "op": "do",
                            "action": {
                                "kind": "trash_program",
                                "pick": "choose",
                            },
                        },
                    },
                },
            ],
            unsupported=[],
        )

    # --- v1.39.0 D-slice ---

    if cid == "drafter":
        may_archives = {
            "op": "choose",
            "chooser": "corp",
            "options": [
                {
                    "id": "take",
                    "label": "Add 1 card from Archives to HQ",
                    "effect": {
                        "op": "do",
                        "action": {"kind": "archives_to_hq", "amount": 1},
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
        }
        may_install = {
            "op": "choose",
            "chooser": "corp",
            "options": [
                {
                    "id": "install",
                    "label": "Install 1 card from Archives or HQ, ignoring all costs",
                    "effect": {
                        "op": "do",
                        "action": {"kind": "install_from_hq_or_archives"},
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
        }
        return base(
            c,
            subroutines=[
                {
                    "id": "drafter-archives",
                    "text": "You may add 1 card from Archives to HQ.",
                    "effect": may_archives,
                },
                {
                    "id": "drafter-install",
                    "text": "You may install 1 card from Archives or HQ, ignoring all costs.",
                    "effect": may_install,
                },
            ],
            unsupported=[],
        )

    if cid == "aniccam":
        return base(
            c,
            muBonus=1,
            onFirstEventTrashedThisTurn={
                "op": "do",
                "action": {"kind": "draw", "side": "runner", "amount": 1},
            },
            unsupported=[],
        )

    if cid == "cybertrooper-talut":
        return base(
            c,
            link=1,
            nonAiIcebreakerInstallStrengthBonusThisTurn=2,
            unsupported=[],
        )

    if cid == "tranquility-home-grid":
        return base(
            c,
            remoteOnly=True,
            onFirstInstallInThisServerRootThisTurn={
                "op": "choose",
                "chooser": "corp",
                "options": [
                    {
                        "id": "credits",
                        "label": "Gain 2¢",
                        "effect": gain("corp", 2),
                    },
                    {
                        "id": "draw",
                        "label": "Draw 1 card",
                        "effect": {
                            "op": "do",
                            "action": {
                                "kind": "draw",
                                "side": "corp",
                                "amount": 1,
                            },
                        },
                    },
                ],
            },
            unsupported=[],
        )

    if cid == "winchester":
        trace_program = {
            "op": "do",
            "action": {
                "kind": "trace",
                "strength": 4,
                "onSuccess": {
                    "op": "do",
                    "action": {"kind": "trash_program", "pick": "choose"},
                },
            },
        }
        trace_hardware = {
            "op": "do",
            "action": {
                "kind": "trace",
                "strength": 3,
                "onSuccess": {
                    "op": "do",
                    "action": {"kind": "trash_hardware", "pick": "choose"},
                },
            },
        }
        trace_etr = {
            "op": "do",
            "action": {
                "kind": "trace",
                "strength": 3,
                "onSuccess": {
                    "op": "do",
                    "action": {"kind": "end_the_run"},
                },
            },
        }
        return base(
            c,
            subroutines=[
                {
                    "id": "winchester-program",
                    "text": "Trace[4]. If successful, trash 1 installed program.",
                    "effect": trace_program,
                },
                {
                    "id": "winchester-hardware",
                    "text": "Trace[3]. If successful, trash 1 installed piece of hardware.",
                    "effect": trace_hardware,
                },
            ],
            gainsSubroutinesWhileProtectingHq=[
                {
                    "id": "winchester-etr",
                    "text": "Trace[3]. If successful, end the run.",
                    "effect": trace_etr,
                }
            ],
            unsupported=[],
        )

    # --- E-slice (v1.40.0): Cerebral Overwriter / Bravado / Scapenet /
    # Megaprix Qualifier / Harmony AR Therapy ---

    if cid == "cerebral-overwriter":
        return base(
            c,
            canAdvance=True,
            onAccess={
                "op": "if",
                "cond": {"op": "source_installed"},
                "then": {
                    "op": "do",
                    "action": {
                        "kind": "may_pay_credits_for_core_damage_per_advancement",
                        "amount": 3,
                    },
                },
            },
            unsupported=[],
        )

    if cid == "bravado":
        return base(
            c,
            runEvent={
                "servers": "any",
                "requiresProtectingIce": True,
                "onRunEnd": {
                    "op": "do",
                    "action": {
                        "kind": "gain_credits",
                        "side": "runner",
                        "amount": 0,
                        "tally": {
                            "count": "passed_ice",
                            "per": 1,
                            "side": "runner",
                            "base": 6,
                        },
                    },
                },
            },
            unsupported=[],
        )

    if cid == "scapenet":
        return base(
            c,
            playRequiresSuccessfulRunLastTurn=True,
            onPlay={
                "op": "do",
                "action": {
                    "kind": "trace",
                    "strength": 7,
                    "onSuccess": {
                        "op": "do",
                        "action": {
                            "kind": "rfg_installed_with_any_subtype",
                            "subtypes": ["chip", "virtual"],
                            "pick": "choose",
                        },
                    },
                },
            },
            unsupported=[],
        )

    if cid == "megaprix-qualifier":
        return base(
            c,
            onScore={
                "op": "if",
                "cond": {"op": "another_copy_of_source_title_in_either_score_area"},
                "then": {
                    "op": "do",
                    "action": {"kind": "add_agenda_counter", "amount": 1},
                },
            },
            agendaPointsPerAgendaCounter=1,
            unsupported=[],
        )

    if cid == "harmony-ar-therapy":
        return base(
            c,
            onPlay={
                "op": "seq",
                "effects": [
                    {
                        "op": "do",
                        "action": {
                            "kind": "shuffle_up_to_n_distinct_heap_titles_into_stack",
                            "max": 5,
                        },
                    },
                    {"op": "do", "action": {"kind": "rfg_self"}},
                ],
            },
            unsupported=[],
        )

    # --- F-slice (v1.41.0): Devil Charm / Simulchip / Cordyceps / Keiko /
    # Flower Sermon ---

    if cid == "devil-charm":
        return base(
            c,
            paidAbilities=[
                {
                    "id": "devil-charm-weaken",
                    "label": "Remove Devil Charm from the game: encountered ice gets −6 strength this run",
                    "clickCost": 0,
                    "creditCost": 0,
                    "cost": {},
                    "windows": ["encounter_paw"],
                    "effect": {
                        "op": "seq",
                        "effects": [
                            {"op": "do", "action": {"kind": "rfg_self"}},
                            {
                                "op": "do",
                                "action": {"kind": "weaken_ice", "amount": 6},
                            },
                        ],
                    },
                }
            ],
            unsupported=[],
        )

    if cid == "simulchip":
        return base(
            c,
            paidAbilities=[
                {
                    "id": "simulchip-install",
                    "label": "[trash]: Install 1 program from heap, paying 3¢ less",
                    "clickCost": 0,
                    "creditCost": 0,
                    "cost": {
                        "trashSelf": True,
                        "trashInstalledProgramUnlessOwnInstalledTrashedThisTurn": True,
                    },
                    "windows": ["runner_action_paw"],
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "install_from_heap",
                            "types": ["program"],
                            "discount": 3,
                        },
                    },
                }
            ],
            unsupported=[],
        )

    if cid == "cordyceps":
        remove_and_swap = {
            "op": "seq",
            "effects": [
                {
                    "op": "do",
                    "action": {"kind": "remove_virus_counters", "amount": 1},
                },
                {
                    "op": "do",
                    "action": {
                        "kind": "may_swap_protecting_attacked_ice_with_other_installed"
                    },
                },
            ],
        }
        return base(
            c,
            memoryCost=1,
            onInstall={
                "op": "do",
                "action": {"kind": "add_virus_counter", "amount": 2},
            },
            onSuccessfulRunOncePerTurn=True,
            onSuccessfulRun={
                "op": "if",
                "cond": {"op": "attacking_central"},
                "then": {
                    "op": "if",
                    "cond": {"op": "virus_counters_gte", "amount": 1},
                    "then": {
                        "op": "choose",
                        "chooser": "runner",
                        "options": [
                            {
                                "id": "swap",
                                "label": "Remove 1 virus counter: swap ice protecting this server",
                                "effect": remove_and_swap,
                            },
                            {
                                "id": "decline",
                                "label": "Decline",
                                "effect": {
                                    "op": "do",
                                    "action": {
                                        "kind": "gain_credits",
                                        "side": "runner",
                                        "amount": 0,
                                    },
                                },
                            },
                        ],
                    },
                },
            },
            unsupported=[],
        )

    if cid == "keiko":
        return base(
            c,
            muBonus=2,
            gainCreditsOnFirstCompanionInstallOrSpendThisTurn=1,
            unsupported=[],
        )

    if cid == "flower-sermon":
        return base(
            c,
            onScore={
                "op": "do",
                "action": {"kind": "add_agenda_counter", "amount": 5},
            },
            paidAbilities=[
                {
                    "id": "flower-sermon-look",
                    "label": "Hosted agenda counter: Look at top of R&D; may advance; may bottom",
                    "clickCost": 0,
                    "creditCost": 0,
                    "cost": {"agendaCounters": 1},
                    "windows": ["corp_action_paw"],
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "look_top_rd_may_advance_may_bottom"
                        },
                    },
                }
            ],
            unsupported=[],
        )

    # --- G-slice (v1.42.0): Týr / Vaporframe Fabricator / Mu Safecracker /
    # Wall to Wall / Engram Flush ---

    if cid == "tyr":
        return base(
            c,
            bioroidBreakGivesCorpAllottedClickNextTurn=True,
            subroutines=[
                {
                    "id": "tyr-core",
                    "text": "Do 2 core damage.",
                    "effect": {
                        "op": "do",
                        "action": {"kind": "core_damage", "amount": 2},
                    },
                },
                {
                    "id": "tyr-trash",
                    "text": "Trash 1 installed Runner card. Gain 3¢.",
                    "effect": {
                        "op": "seq",
                        "effects": [
                            {
                                "op": "do",
                                "action": {
                                    "kind": "trash_installed_runner",
                                    "pick": "choose",
                                },
                            },
                            gain("corp", 3),
                        ],
                    },
                },
                {
                    "id": "tyr-etr",
                    "text": "End the run.",
                    "effect": {
                        "op": "do",
                        "action": {"kind": "end_the_run"},
                    },
                },
            ],
            unsupported=[],
        )

    if cid == "vaporframe-fabricator":
        return base(
            c,
            paidAbilities=[
                {
                    "id": "vaporframe-click-install",
                    "label": "[click]: Install 1 card from HQ, ignoring all costs",
                    "clickCost": 1,
                    "creditCost": 0,
                    "cost": {"clicks": 1},
                    "windows": ["corp_action_paw"],
                    "oncePerTurn": True,
                    "effect": {
                        "op": "do",
                        "action": {"kind": "may_install_from_hq_ignore_costs"},
                    },
                }
            ],
            onTrash={
                "op": "do",
                "action": {
                    "kind": "may_install_from_hq_ignore_costs_exclude_source_server"
                },
            },
            unsupported=[],
        )

    if cid == "mu-safecracker":
        return base(
            c,
            paidAbilitiesUseStealthCreditsOnly=True,
            onSuccessfulHqRunMayPayForBonusAccess={"credits": 1, "bonusAccess": 1},
            onSuccessfulRdRunMayPayForBonusAccess={"credits": 2, "bonusAccess": 1},
            unsupported=[],
        )

    if cid == "wall-to-wall":
        # Resolve 1 if any other rezzed asset exists; otherwise up to 3 in any order.
        # Represented via dedicated primitive that encodes the card's choice rules.
        return base(
            c,
            onTurnBegin={
                "op": "do",
                "action": {"kind": "wall_to_wall_turn_begin"},
            },
            unsupported=[],
        )

    if cid == "engram-flush":
        return base(
            c,
            onEncounter={
                "op": "do",
                "action": {"kind": "choose_card_type_for_encounter"},
            },
            subroutines=[
                {
                    "id": "engram-reveal-1",
                    "text": "Reveal the grip.",
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "reveal_grip_may_trash_chosen_encounter_type"
                        },
                    },
                },
                {
                    "id": "engram-reveal-2",
                    "text": "Reveal the grip.",
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "reveal_grip_may_trash_chosen_encounter_type"
                        },
                    },
                },
            ],
            unsupported=[],
        )

    # --- H-slice (v1.43.0): Ganked! / Mystic Maemi / Paladin Poemu /
    # Prognostic Q-Loop / Boomerang ---

    if cid == "ganked":
        return base(
            c,
            mustRevealWhenAccessedFromRd=True,
            onAccess={
                "op": "choose",
                "chooser": "corp",
                "options": [
                    {
                        "id": "trash-encounter",
                        "label": (
                            "Trash Ganked! to choose rezzed ice protecting "
                            "this server; Runner encounters it"
                        ),
                        "effect": {
                            "op": "do",
                            "action": {
                                "kind": (
                                    "trash_self_choose_rezzed_protecting_ice_encounter"
                                )
                            },
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
            },
            unsupported=[],
        )

    _companion_place_credit = {
        "op": "do",
        "action": {"kind": "place_hosted_credits", "amount": 1},
    }

    if cid == "mystic-maemi":
        return base(
            c,
            onTurnBegin=_companion_place_credit,
            onStealAgenda=_companion_place_credit,
            hostedCreditsSpendFor=["play_event"],
            onRunnerTurnEnd={
                "op": "if",
                "cond": {"op": "hosted_credits_gte", "amount": 3},
                "then": {
                    "op": "choose",
                    "chooser": "runner",
                    "options": [
                        {
                            "id": "trash-grip",
                            "label": "Trash 1 card from grip at random",
                            "effect": {
                                "op": "do",
                                "action": {
                                    "kind": "trash_random_from_grip",
                                    "amount": 1,
                                },
                            },
                        },
                        {
                            "id": "trash-self",
                            "label": "Trash Mystic Maemi",
                            "effect": {
                                "op": "do",
                                "action": {"kind": "trash_self"},
                            },
                        },
                    ],
                },
            },
            unsupported=[],
        )

    if cid == "paladin-poemu":
        return base(
            c,
            onTurnBegin=_companion_place_credit,
            onStealAgenda=_companion_place_credit,
            hostedCreditsSpendFor=["install"],
            hostedCreditsSpendForInstallExcludeSubtypes=["connection"],
            onRunnerTurnEnd={
                "op": "if",
                "cond": {"op": "hosted_credits_gte", "amount": 3},
                "then": {
                    "op": "do",
                    "action": {"kind": "must_trash_own_installed"},
                },
            },
            unsupported=[],
        )

    if cid == "prognostic-q-loop":
        return base(
            c,
            onFirstRunBeginThisTurn={
                "op": "choose",
                "chooser": "runner",
                "options": [
                    {
                        "id": "look",
                        "label": "Look at the top 2 cards of your stack",
                        "effect": {
                            "op": "do",
                            "action": {
                                "kind": "look_top_n_stack_peek",
                                "amount": 2,
                            },
                        },
                    },
                    {
                        "id": "decline",
                        "label": "Decline",
                        "effect": {
                            "op": "do",
                            "action": {
                                "kind": "gain_credits",
                                "side": "runner",
                                "amount": 0,
                            },
                        },
                    },
                ],
            },
            paidAbilities=[
                {
                    "id": "prognostic-q-loop-reveal-install",
                    "label": (
                        "1¢: Reveal top of stack; may install if program "
                        "or hardware"
                    ),
                    "clickCost": 0,
                    "creditCost": 1,
                    "cost": {"credits": 1},
                    "windows": ["runner_action_paw"],
                    "oncePerTurn": True,
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": (
                                "reveal_top_stack_may_install_program_or_hardware"
                            )
                        },
                    },
                }
            ],
            unsupported=[],
        )

    if cid == "boomerang":
        return base(
            c,
            chooseIceOnInstall=True,
            paidAbilities=[
                {
                    "id": "boomerang-break",
                    "label": (
                        "[trash]: Break up to 2 subroutines; if this run is "
                        "successful, may shuffle Boomerang from heap into stack"
                    ),
                    "clickCost": 0,
                    "creditCost": 0,
                    "cost": {"trashSelf": True},
                    "windows": ["encounter_paw"],
                    "requireEncounterChosenIce": True,
                    "effect": {
                        "op": "seq",
                        "effects": [
                            {
                                "op": "do",
                                "action": {
                                    "kind": "break_encounter_subroutine",
                                    "maxSubs": 2,
                                },
                            },
                            {
                                "op": "do",
                                "action": {
                                    "kind": (
                                        "register_may_shuffle_title_from_heap_"
                                        "on_successful_run_end"
                                    ),
                                    "title": "Boomerang",
                                },
                            },
                        ],
                    },
                }
            ],
            unsupported=[],
        )

    # --- I-slice (v1.44.0): SYNC Rerouting / Argus Crackdown /
    # Hyoubu Precog Manifold / NAPD Cordon / NEXT Activation Command ---
    # Shared lockdown shell: playRequiresNoActiveLockdown +
    # lingerUntilCorpNextTurnBegins (CR 3.5.1c / 8.6.6c).

    _lockdown = dict(
        playRequiresNoActiveLockdown=True,
        lingerUntilCorpNextTurnBegins=True,
    )

    if cid == "sync-rerouting":
        return base(
            c,
            **_lockdown,
            onRunBegin={
                "op": "choose",
                "chooser": "runner",
                "options": [
                    {
                        "id": "pay4",
                        "label": "Pay 4¢",
                        "effect": {
                            "op": "do",
                            "action": {
                                "kind": "lose_credits",
                                "side": "runner",
                                "amount": 4,
                            },
                        },
                    },
                    {
                        "id": "tag",
                        "label": "Take 1 tag",
                        "effect": {
                            "op": "do",
                            "action": {"kind": "give_tags", "amount": 1},
                        },
                    },
                ],
            },
            unsupported=[],
        )

    if cid == "argus-crackdown":
        return base(
            c,
            **_lockdown,
            onSuccessfulRun={
                "op": "if",
                "cond": {"op": "attacked_server_protected_by_ice"},
                "then": {
                    "op": "do",
                    "action": {"kind": "meat_damage", "amount": 2},
                },
            },
            unsupported=[],
        )

    if cid == "hyoubu-precog-manifold":
        return base(
            c,
            **_lockdown,
            onPlay={
                "op": "do",
                "action": {"kind": "choose_server"},
            },
            onSuccessfulRun={
                "op": "if",
                "cond": {"op": "attacking_chosen_server"},
                "then": {
                    "op": "do",
                    "action": {
                        "kind": "play_psi_game",
                        "maxBid": 2,
                        "ifBidsDiffer": {
                            "op": "do",
                            "action": {"kind": "end_the_run"},
                        },
                    },
                },
            },
            unsupported=[],
        )

    if cid == "napd-cordon":
        return base(
            c,
            **_lockdown,
            stealAdditionalCreditsFormula={
                "base": 4,
                "perAdvancement": 2,
            },
            unsupported=[],
        )

    if cid == "next-activation-command":
        return base(
            c,
            **_lockdown,
            allIceStrengthBonus=2,
            cannotBreakExceptIcebreaker=True,
            unsupported=[],
        )

    # --- J-slice (v1.45.0): Hoshiko / DRM / Paule's Café / Konjin /
    # Buffer Drive ---

    if cid == "hoshiko-shiro-untold-protagonist":
        return base(
            c,
            onRunnerTurnEnd={
                "op": "if",
                "cond": {
                    "op": "and",
                    "conds": [
                        {"op": "identity_unflipped"},
                        {"op": "accessed_a_card_this_turn"},
                    ],
                },
                "then": {
                    "op": "seq",
                    "effects": [
                        gain("runner", 2),
                        {
                            "op": "do",
                            "action": {"kind": "flip_identity"},
                        },
                    ],
                },
                "else": {
                    "op": "if",
                    "cond": {
                        "op": "and",
                        "conds": [
                            {"op": "identity_flipped"},
                            {"op": "not_accessed_a_card_this_turn"},
                        ],
                    },
                    "then": {
                        "op": "do",
                        "action": {"kind": "flip_identity"},
                    },
                },
            },
            onTurnBegin={
                "op": "if",
                "cond": {"op": "identity_flipped"},
                "then": {
                    "op": "seq",
                    "effects": [
                        {
                            "op": "do",
                            "action": {
                                "kind": "draw",
                                "side": "runner",
                                "amount": 1,
                            },
                        },
                        {
                            "op": "do",
                            "action": {
                                "kind": "lose_credits",
                                "side": "runner",
                                "amount": 1,
                            },
                        },
                    ],
                },
            },
            unsupported=[],
        )

    if cid == "digital-rights-management":
        return base(
            c,
            playRequiresNoSuccessfulHqRunLastTurn=True,
            onPlay={
                "op": "seq",
                "effects": [
                    {
                        "op": "do",
                        "action": {"kind": "search_rd_type_to_hq", "cardType": "agenda"},
                    },
                    {
                        "op": "do",
                        "action": {
                            "kind": (
                                "may_install_from_hq_in_remote_root_paying_costs"
                            )
                        },
                    },
                    {
                        "op": "do",
                        "action": {
                            "kind": "forbid_scoring_agendas_this_turn"
                        },
                    },
                ],
            },
            unsupported=[],
        )

    if cid == "paules-cafe":
        return base(
            c,
            paidAbilities=[
                {
                    "id": "paules-cafe-host",
                    "label": (
                        "[click]: Host 1 program or hardware from grip "
                        "faceup on this resource"
                    ),
                    "clickCost": 1,
                    "creditCost": 0,
                    "cost": {"clicks": 1},
                    "windows": ["runner_action_paw"],
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": (
                                "may_host_one_program_or_hardware_from_grip_faceup"
                            )
                        },
                    },
                },
                {
                    "id": "paules-cafe-install",
                    "label": (
                        "1¢: Install 1 hosted card (first this turn −1¢ per "
                        "unique ♦ connection resource installed)"
                    ),
                    "clickCost": 0,
                    "creditCost": 1,
                    "cost": {"credits": 1},
                    "windows": ["runner_action_paw"],
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "may_install_one_hosted_card",
                            "firstThisTurnDiscountPerUniqueConnection": True,
                        },
                    },
                },
            ],
            unsupported=[],
        )

    if cid == "konjin":
        return base(
            c,
            onEncounter={
                "op": "do",
                "action": {
                    "kind": "play_psi_game",
                    "maxBid": 2,
                    "ifBidsDiffer": {
                        "op": "do",
                        "action": {
                            "kind": (
                                "may_choose_other_rezzed_ice_encounter_"
                                "then_resume_source"
                            )
                        },
                    },
                },
            },
            unsupported=[],
        )

    if cid == "buffer-drive":
        return base(
            c,
            onFirstGripOrStackTrashBatchEachTurn={
                "op": "do",
                "action": {
                    "kind": "may_add_one_of_card_ids_to_stack_bottom"
                },
            },
            paidAbilities=[
                {
                    "id": "buffer-drive-heap-top",
                    "label": (
                        "Remove Buffer Drive from the game: Add 1 card from "
                        "your heap to the top of your stack"
                    ),
                    "clickCost": 0,
                    "creditCost": 0,
                    "cost": {},
                    "windows": ["runner_action_paw"],
                    "effect": {
                        "op": "seq",
                        "effects": [
                            {
                                "op": "do",
                                "action": {"kind": "rfg_self"},
                            },
                            {
                                "op": "do",
                                "action": {
                                    "kind": "may_add_from_heap_to_stack_top"
                                },
                            },
                        ],
                    },
                }
            ],
            unsupported=[],
        )

    # --- K-slice (v1.46.0): final 7 → 65/65 set-complete ---
    # Prāna / Vacheron / Earth Station / Kakurenbo / Gachapon /
    # The Back / GameNET. CR pin v26.03.

    if cid == "prana-condenser":
        return base(
            c,
            paidAbilities=[
                {
                    "id": "prana-prevent-net",
                    "label": (
                        "Interrupt: prevent 1 net damage → +1 power + 3¢"
                    ),
                    "clickCost": 0,
                    "creditCost": 0,
                    "cost": {},
                    "windows": ["damage_interrupt_paw"],
                    "requirePendingDamageTypes": ["net"],
                    "oncePerPendingDamageInstance": True,
                    "effect": {
                        "op": "seq",
                        "effects": [
                            {
                                "op": "do",
                                "action": {
                                    "kind": "prevent_pending_damage",
                                    "amount": 1,
                                },
                            },
                            {
                                "op": "do",
                                "action": {
                                    "kind": "add_power_counter",
                                    "amount": 1,
                                },
                            },
                            gain("corp", 3),
                        ],
                    },
                },
                {
                    "id": "prana-discharge",
                    "label": (
                        "[click][click], [trash]: Do 1 net damage for each "
                        "hosted power counter"
                    ),
                    "clickCost": 2,
                    "creditCost": 0,
                    "cost": {"clicks": 2, "trashSelf": True},
                    "windows": ["corp_action_paw"],
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "net_damage",
                            "amount": 0,
                            "tally": {
                                "count": "source_power_counters",
                                "per": 1,
                                "side": "source",
                            },
                        },
                    },
                },
            ],
            unsupported=[],
        )

    if cid == "project-vacheron":
        return base(
            c,
            vacheronStealReplacement=True,
            worthZeroAgendaPointsWhileHasAgendaCounters=True,
            onTurnBegin={
                "op": "do",
                "action": {
                    "kind": "remove_agenda_counters",
                    "amount": 1,
                },
            },
            unsupported=[],
        )

    if cid == "earth-station-sea-headquarters":
        return base(
            c,
            maxRemoteServers=1,
            additionalRunInitiateCredits={
                "hqUnflipped": 1,
                "remoteFlipped": 6,
            },
            paidAbilities=[
                {
                    "id": "earth-station-flip",
                    "label": "[click]: Flip this identity",
                    "clickCost": 1,
                    "creditCost": 0,
                    "cost": {"clicks": 1},
                    "windows": ["corp_action_paw"],
                    "effect": {
                        "op": "do",
                        "action": {"kind": "flip_identity"},
                    },
                }
            ],
            identityFlippedHooks={
                "onSuccessfulHqRun": {
                    "op": "do",
                    "action": {"kind": "flip_identity"},
                }
            },
            unsupported=[],
        )

    if cid == "kakurenbo":
        return base(
            c,
            playAdditionalClicks=2,
            onPlay={
                "op": "seq",
                "effects": [
                    {
                        "op": "do",
                        "action": {"kind": "trash_any_number_from_hq"},
                    },
                    {
                        "op": "do",
                        "action": {"kind": "turn_all_archives_facedown"},
                    },
                    {
                        "op": "do",
                        "action": {
                            "kind": (
                                "may_install_from_archives_in_remote_root_"
                                "with_advancements"
                            ),
                            "amount": 2,
                        },
                    },
                    {
                        "op": "do",
                        "action": {"kind": "rfg_self"},
                    },
                ],
            },
            unsupported=[],
        )

    if cid == "gachapon":
        return base(
            c,
            paidAbilities=[
                {
                    "id": "gachapon-resolve",
                    "label": (
                        "[trash]: Set aside top 6 faceup; may install "
                        "program/virtual −2¢; shuffle 3; RFG rest"
                    ),
                    "clickCost": 0,
                    "creditCost": 0,
                    "cost": {"trashSelf": True},
                    "windows": ["runner_action_paw"],
                    "effect": {
                        "op": "do",
                        "action": {"kind": "gachapon_resolve"},
                    },
                }
            ],
            unsupported=[],
        )

    if cid == "the-back":
        return base(
            c,
            onFirstHardwareUseDuringRunEachTurn={
                "op": "do",
                "action": {
                    "kind": "add_power_counter",
                    "amount": 1,
                },
            },
            paidAbilities=[
                {
                    "id": "the-back-heap-shuffle",
                    "label": (
                        "[click], remove The Back from the game: For each "
                        "hosted power counter, shuffle up to 2 heap cards "
                        "with [trash] abilities into your stack"
                    ),
                    "clickCost": 1,
                    "creditCost": 0,
                    "cost": {"clicks": 1, "rfgSelf": True},
                    "windows": ["runner_action_paw"],
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": (
                                "shuffle_up_to_n_heap_cards_with_trash_"
                                "abilities_into_stack"
                            ),
                            "nPerPowerCounter": 2,
                        },
                    },
                }
            ],
            unsupported=[],
        )

    if cid == "gamenet-where-dreams-are-real":
        return base(
            c,
            onCorpAbilityCausesRunnerSpendOrLoseCreditsDuringRun={
                "op": "do",
                "action": {
                    "kind": "gain_credits",
                    "side": "corp",
                    "amount": 1,
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

    status = "supported" if partial == 0 else "in-progress"
    if status == "supported":
        notes = (
            "Null Signal Uprising (NRDB pack ur) — Ashes set 2 of 2; first "
            "legacy backwards wave before System Gateway. urbp titles absorbed. "
            f"Fully supported: all {EXPECTED} cards mapped (wave gate v1.46.0; "
            f"full={full}, partial={partial})."
        )
    else:
        notes = (
            "Null Signal Uprising (NRDB pack ur) — Ashes set 2 of 2; first "
            "legacy backwards wave before System Gateway. urbp titles absorbed. "
            f"In-progress: {full} cards fully mapped, {partial} with unsupported "
            "notes (wave slice v1.46.0)."
        )
    manifest = {
        "pack": WAVE,
        "nrdbPackCode": PACK,
        "count": EXPECTED,
        "written": EXPECTED,
        "status": status,
        "notes": notes,
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
