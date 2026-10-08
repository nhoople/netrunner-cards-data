#!/usr/bin/env python3
"""Generate Downfall card JSON from pinned pack `df`.

Catalog source: Null-Signal-Games/netrunner-cards-json (see data/nsg-catalog-pin.json).
Fetch with: python3 scripts/nsg_catalog.py fetch df

Downfall is Ashes set 1 of 2 (Uprising is set 2). Magnum Opus Reprint (`mor`)
is skipped/absorbed — not a corpus wave.

Hand-mapped Effect IR only where existing primitives fully cover the card;
everything else lists honest unsupported notes — never invent IR.

Usage: python3 scripts/generate-downfall.py
"""
from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

from nsg_catalog import load_pack_cards

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "downfall"
WAVE = "downfall"
PACK = "df"
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


def draw(side: str, n: int):
    return {"op": "do", "action": {"kind": "draw", "side": side, "amount": n}}


def decline(side: str):
    return {
        "id": "decline",
        "label": "Decline",
        "effect": gain(side, 0),
    }


def may_draw(side: str, n: int = 1):
    return {
        "op": "choose",
        "chooser": side,
        "options": [
            {
                "id": "draw",
                "label": f"Draw {n} card" + ("s" if n != 1 else ""),
                "effect": draw(side, n),
            },
            decline(side),
        ],
    }


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
    # NRDB faction_code — required for Storgotic Resonator (match Runner ID faction).
    if c.get("faction_code"):
        card["faction"] = c["faction_code"]
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

    # --- v1.47.0 kickoff: existing IR only ---

    if cid == "rezeki":
        return base(
            c,
            onTurnBegin=gain("runner", 1),
            unsupported=[],
        )

    if cid == "bukhgalter":
        return breaker_card(
            c,
            "sentry",
            1,
            1,
            1,
            1,
            break_max=1,
            onFullyBreakOncePerTurn=gain("runner", 2),
            unsupported=[],
        )

    if cid == "tiered-subscription":
        return base(
            c,
            onFirstRunBeginThisTurn=gain("corp", 1),
            unsupported=[],
        )

    if cid == "isolation":
        return base(
            c,
            playRequiresInstalledResource=True,
            playAdditionalCost={
                "op": "do",
                "action": {"kind": "trash_own_resource"},
            },
            onPlay=gain("runner", 7),
            unsupported=[],
        )

    if cid == "csr-campaign":
        return base(
            c,
            onTurnBegin=may_draw("corp", 1),
            unsupported=[],
        )

    # --- v1.48.0 A-slice ---

    if cid == "congratulations":
        return base(
            c,
            onPass=gain("corp", 1),
            subroutines=[
                {
                    "id": "congratulations-credits",
                    "text": "Gain 2[credit]. The Runner gains 1[credit].",
                    "effect": {
                        "op": "seq",
                        "effects": [
                            gain("corp", 2),
                            gain("runner", 1),
                        ],
                    },
                }
            ],
            unsupported=[],
        )

    if cid == "gauss":
        return breaker_card(
            c,
            "barrier",
            1,
            1,
            2,
            2,
            break_max=1,
            onInstall={
                "op": "do",
                "action": {"kind": "gain_strength_this_turn", "amount": 3},
            },
            unsupported=[],
        )

    if cid == "spec-work":
        return base(
            c,
            playRequiresInstalledProgram=True,
            playAdditionalCost={
                "op": "do",
                "action": {"kind": "trash_own_program"},
            },
            onPlay={
                "op": "seq",
                "effects": [
                    gain("runner", 4),
                    draw("runner", 2),
                ],
            },
            unsupported=[],
        )

    if cid == "nanoetching-matrix":
        return base(
            c,
            paidAbilities=[
                {
                    "id": "nanoetching-matrix-gain",
                    "label": "[click]: Gain 2¢",
                    "clickCost": 1,
                    "creditCost": 0,
                    "cost": {"clicks": 1},
                    "windows": ["corp_action_paw"],
                    "oncePerTurn": True,
                    "effect": gain("corp", 2),
                }
            ],
            onTrash={
                "op": "choose",
                "chooser": "corp",
                "options": [
                    {
                        "id": "gain",
                        "label": "Gain 2¢",
                        "effect": gain("corp", 2),
                    },
                    decline("corp"),
                ],
            },
            unsupported=[],
        )

    if cid == "sandstone":
        return base(
            c,
            onEncounter={
                "op": "do",
                "action": {"kind": "add_virus_counter", "amount": 1},
            },
            strengthPerVirusCounter=-1,
            subroutines=[
                {
                    "id": "sandstone-etr",
                    "text": "End the run.",
                    "effect": {
                        "op": "do",
                        "action": {"kind": "end_the_run"},
                    },
                }
            ],
            unsupported=[],
        )

    # --- v1.49.0 B-slice ---

    if cid == "vulnerability-audit":
        return base(
            c,
            cannotScoreIfInstalledThisTurn=True,
            unsupported=[],
        )

    if cid == "calvin-b4l3y":
        return base(
            c,
            paidAbilities=[
                {
                    "id": "calvin-b4l3y-draw",
                    "label": "[click]: Draw 2 cards",
                    "clickCost": 1,
                    "creditCost": 0,
                    "cost": {"clicks": 1},
                    "windows": ["corp_action_paw"],
                    "oncePerTurn": True,
                    "effect": draw("corp", 2),
                }
            ],
            onTrash=may_draw("corp", 2),
            unsupported=[],
        )

    if cid == "remastered-edition":
        return base(
            c,
            onScore={
                "op": "do",
                "action": {"kind": "add_agenda_counter", "amount": 1},
            },
            paidAbilities=[
                {
                    "id": "remastered-edition-advance",
                    "label": "Hosted agenda counter: Place 1 advancement counter",
                    "clickCost": 0,
                    "creditCost": 0,
                    "cost": {"agendaCounters": 1},
                    "windows": ["corp_action_paw"],
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "place_advancements",
                            "amount": 1,
                        },
                    },
                }
            ],
            unsupported=[],
        )

    if cid == "roughneck-repair-squad":
        return base(
            c,
            paidAbilities=[
                {
                    "id": "roughneck-repair-squad-main",
                    "label": "[click][click][click]: Gain 6¢. You may remove 1 bad publicity.",
                    "clickCost": 3,
                    "creditCost": 0,
                    "cost": {"clicks": 3},
                    "windows": ["corp_action_paw"],
                    "effect": {
                        "op": "seq",
                        "effects": [
                            gain("corp", 6),
                            {
                                "op": "choose",
                                "chooser": "corp",
                                "options": [
                                    {
                                        "id": "remove-bp",
                                        "label": "Remove 1 bad publicity",
                                        "effect": {
                                            "op": "do",
                                            "action": {
                                                "kind": "remove_bad_publicity",
                                                "amount": 1,
                                            },
                                        },
                                    },
                                    decline("corp"),
                                ],
                            },
                        ],
                    },
                }
            ],
            unsupported=[],
        )

    if cid == "the-artist":
        return base(
            c,
            paidAbilities=[
                {
                    "id": "the-artist-gain",
                    "label": "[click]: Gain 2¢",
                    "clickCost": 1,
                    "creditCost": 0,
                    "cost": {"clicks": 1},
                    "windows": ["runner_action_paw"],
                    "oncePerTurn": True,
                    "effect": gain("runner", 2),
                },
                {
                    "id": "the-artist-install",
                    "label": "[click]: Install program or hardware, paying 1¢ less",
                    "clickCost": 1,
                    "creditCost": 0,
                    "cost": {"clicks": 1},
                    "windows": ["runner_action_paw"],
                    "oncePerTurn": True,
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "install_from_grip_discount",
                            "types": ["program", "hardware"],
                            "discount": 1,
                        },
                    },
                },
            ],
            unsupported=[],
        )

    # --- v1.50.0 C-slice ---

    if cid == "increased-drop-rates":
        return base(
            c,
            mustRevealWhenAccessedFromRd=True,
            onAccess={
                "op": "choose",
                "chooser": "runner",
                "options": [
                    {
                        "id": "take-tag",
                        "label": "Take 1 tag",
                        "effect": {
                            "op": "do",
                            "action": {"kind": "give_tags", "amount": 1},
                        },
                    },
                    {
                        "id": "allow-remove-bp",
                        "label": "Allow Corp to remove 1 bad publicity",
                        "effect": {
                            "op": "do",
                            "action": {
                                "kind": "remove_bad_publicity",
                                "amount": 1,
                            },
                        },
                    },
                ],
            },
            unsupported=[],
        )

    if cid == "red-level-clearance":
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
                            "label": "Draw 2 cards",
                            "effect": draw("corp", 2),
                        },
                        {
                            "id": "credits",
                            "label": "Gain 2¢",
                            "effect": gain("corp", 2),
                        },
                        {
                            "id": "install",
                            "label": "Install 1 non-agenda card from HQ",
                            "effect": {
                                "op": "do",
                                "action": {
                                    "kind": "may_install_from_hq_paying_costs",
                                    "excludeAgenda": True,
                                },
                            },
                        },
                        {
                            "id": "click",
                            "label": "Gain [click]",
                            "effect": {
                                "op": "do",
                                "action": {
                                    "kind": "gain_clicks",
                                    "side": "corp",
                                    "amount": 1,
                                },
                            },
                        },
                    ],
                },
            },
            unsupported=[],
        )

    if cid == "afshar":
        return base(
            c,
            onEncounter={
                "op": "if",
                "cond": {"op": "attacking_hq"},
                "then": {
                    "op": "do",
                    "action": {
                        "kind": "limit_printed_breaks_on_source_for_run",
                        "max": 1,
                    },
                },
            },
            subroutines=[
                {
                    "id": "afshar-lose",
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
                    "id": "afshar-etr",
                    "text": "End the run.",
                    "effect": {
                        "op": "do",
                        "action": {"kind": "end_the_run"},
                    },
                },
            ],
            unsupported=[],
        )

    if cid == "hagen":
        return base(
            c,
            strengthBonusPerIcebreaker=-1,
            subroutines=[
                {
                    "id": "hagen-trash",
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
                {
                    "id": "hagen-etr",
                    "text": "End the run.",
                    "effect": {
                        "op": "do",
                        "action": {"kind": "end_the_run"},
                    },
                },
            ],
            unsupported=[],
        )

    if cid == "sds-drone-deployment":
        return base(
            c,
            stealAdditionalCost={
                "op": "do",
                "action": {"kind": "trash_own_program"},
            },
            onScore={
                "op": "do",
                "action": {
                    "kind": "trash_program",
                    "pick": "choose",
                },
            },
            unsupported=[],
        )

    # --- v1.51.0 D-slice ---

    if cid == "supercorridor":
        return base(
            c,
            muBonus=2,
            handSizeBonus=1,
            onRunnerTurnEnd={
                "op": "if",
                "cond": {"op": "credits_eq_other_side", "side": "runner"},
                "then": {
                    "op": "choose",
                    "chooser": "runner",
                    "options": [
                        {
                            "id": "gain",
                            "label": "Gain 2¢",
                            "effect": gain("runner", 2),
                        },
                        decline("runner"),
                    ],
                },
            },
            unsupported=[],
        )

    if cid == "public-health-portal":
        return base(
            c,
            onTurnBegin={
                "op": "seq",
                "effects": [
                    {
                        "op": "do",
                        "action": {"kind": "reveal_top_of_rd"},
                    },
                    gain("corp", 2),
                ],
            },
            unsupported=[],
        )

    if cid == "demolisher":
        return base(
            c,
            muBonus=1,
            corpCardTrashCostReduction=1,
            onFirstCorpCardTrashEachTurn=gain("runner", 1),
            unsupported=[],
        )

    if cid == "flip-switch":
        return base(
            c,
            paidAbilities=[
                {
                    "id": "flip-switch-jack-out",
                    "label": "[trash]: Jack out",
                    "clickCost": 0,
                    "creditCost": 0,
                    "cost": {"trashSelf": True},
                    "requireDuringRun": True,
                    "windows": [
                        "approach_paw",
                        "encounter_paw",
                        "approach_server_paw",
                    ],
                    "effect": {
                        "op": "do",
                        "action": {"kind": "end_the_run"},
                    },
                },
                {
                    "id": "flip-switch-remove-tag",
                    "label": "[trash]: Remove 1 tag",
                    "clickCost": 0,
                    "creditCost": 0,
                    "cost": {"trashSelf": True},
                    "windows": ["runner_action_paw"],
                    "effect": {
                        "op": "do",
                        "action": {"kind": "remove_tags", "amount": 1},
                    },
                },
                {
                    "id": "flip-switch-trace",
                    "label": "[interrupt] → [trash]: Reduce base trace strength to 0",
                    "clickCost": 0,
                    "creditCost": 0,
                    "cost": {"trashSelf": True},
                    "windows": ["trace_interrupt_paw"],
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "set_trace_base_strength",
                            "amount": 0,
                        },
                    },
                },
            ],
            unsupported=[],
        )

    if cid == "fully-operational":
        return base(
            c,
            onPlay={
                "op": "do",
                "action": {"kind": "fully_operational_resolve"},
            },
            unsupported=[],
        )

    # --- v1.52.0 E-slice ---

    if cid == "trebuchet":
        return base(
            c,
            onRez={
                "op": "do",
                "action": {"kind": "give_bad_publicity", "amount": 1},
            },
            subroutines=[
                {
                    "id": "trebuchet-trash",
                    "text": "Trash 1 installed Runner card.",
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "trash_installed_runner",
                            "pick": "choose",
                        },
                    },
                },
                {
                    "id": "trebuchet-trace",
                    "text": "Trace[6]. If successful, the Runner cannot steal or trash Corp cards for the remainder of this run.",
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "trace",
                            "strength": 6,
                            "onSuccess": {
                                "op": "do",
                                "action": {
                                    "kind": "forbid_steal_trash_this_run"
                                },
                            },
                        },
                    },
                },
            ],
            unsupported=[],
        )

    if cid == "blueberry-diesel":
        return base(
            c,
            onPlay={
                "op": "seq",
                "effects": [
                    {
                        "op": "do",
                        "action": {
                            "kind": "look_top_n_stack_may_bottom_one",
                            "n": 2,
                        },
                    },
                    draw("runner", 2),
                ],
            },
            unsupported=[],
        )

    if cid == "pelangi":
        return base(
            c,
            onInstall={
                "op": "do",
                "action": {"kind": "add_virus_counter", "amount": 2},
            },
            paidAbilities=[
                {
                    "id": "pelangi-grant-subtype",
                    "label": "Hosted virus counter: Choose an ice subtype for encountered ice",
                    "clickCost": 0,
                    "creditCost": 0,
                    "cost": {"virusCounters": 1},
                    "windows": ["encounter_paw"],
                    "oncePerTurn": True,
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "choose_grant_encounter_ice_subtype"
                        },
                    },
                }
            ],
            unsupported=[],
        )

    if cid == "loot-box":
        return base(
            c,
            subroutines=[
                {
                    "id": "loot-box-pay",
                    "text": "End the run unless the Runner pays 2[credit].",
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "unless",
                            "payer": "runner",
                            "cost": {
                                "op": "do",
                                "action": {
                                    "kind": "lose_credits",
                                    "side": "runner",
                                    "amount": 2,
                                },
                            },
                            "instruction": {
                                "op": "do",
                                "action": {"kind": "end_the_run"},
                            },
                        },
                    },
                },
                {
                    "id": "loot-box-reveal",
                    "text": "Reveal the top 3 cards of the stack. Add 1 of those cards to the grip and gain X[credit], where X is equal to that card's play or install cost. The Runner shuffles the remaining cards into the stack.",
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "loot_box_reveal_top_n",
                            "n": 3,
                        },
                    },
                },
            ],
            unsupported=[],
        )

    if cid == "utae":
        return base(
            c,
            breaker={
                "breaksSubtype": "code gate",
                "strength": c.get("strength") or 1,
                "breakCredits": 1,
                "breakMaxSubs": 1,
                "pumpCredits": 1,
                "pumpStrength": 1,
                "breakViaPaidAbilityOnly": True,
            },
            paidAbilities=[
                {
                    "id": "utae-break-x",
                    "label": "X¢: Break X code gate subroutines (once per run)",
                    "clickCost": 0,
                    "creditCost": 0,
                    "cost": {},
                    "windows": ["encounter_paw"],
                    "oncePerRun": True,
                    "requireEncounterSubtype": "code gate",
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "break_encounter_subroutine",
                            "maxSubs": 99,
                            "requireSubtype": "code gate",
                            "payCreditsPerBrokenSub": 1,
                        },
                    },
                },
                {
                    "id": "utae-break-virtual",
                    "label": "1¢: Break 1 code gate subroutine (3+ virtual resources)",
                    "clickCost": 0,
                    "creditCost": 1,
                    "cost": {"credits": 1},
                    "windows": ["encounter_paw"],
                    "requireInstalledVirtualResourcesGte": 3,
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
                    "id": "utae-pump",
                    "label": "1¢: +1 strength",
                    "clickCost": 0,
                    "creditCost": 1,
                    "cost": {"credits": 1},
                    "windows": ["encounter_paw"],
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "pump_strength",
                            "amount": 1,
                        },
                    },
                },
            ],
            unsupported=[],
        )

    # --- v1.53.0 F-slice ---

    if cid == "secure-and-protect":
        return base(
            c,
            playAdditionalClick=True,
            onPlay={
                "op": "do",
                "action": {
                    "kind": "search_rd_ice_install_central_discount",
                    "discount": 3,
                },
            },
            unsupported=[],
        )

    if cid == "chisel":
        return base(
            c,
            installOnIce=True,
            hostStrengthPerVirusCounter=-1,
            onHostEncounter={
                "op": "if",
                "cond": {"op": "encounter_ice_strength_lte", "amount": 0},
                "then": {
                    "op": "do",
                    "action": {
                        "kind": "trash_encounter_ice_if_strength_lte",
                        "maxStrength": 0,
                    },
                },
                "else": {
                    "op": "do",
                    "action": {"kind": "add_virus_counter", "amount": 1},
                },
            },
            unsupported=[],
        )

    if cid == "rime":
        return base(
            c,
            rezAsNonIceDuringRunsOnServer=True,
            sameServerIceStrengthBonus=1,
            subroutines=[
                {
                    "id": "rime-lose",
                    "text": "The Runner loses 1[credit].",
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "lose_credits",
                            "side": "runner",
                            "amount": 1,
                        },
                    },
                }
            ],
            unsupported=[],
        )

    if cid == "lat-ethical-freelancer":
        return base(
            c,
            onDiscardPhaseEnd={
                "op": "if",
                "cond": {"op": "grip_count_eq_hq"},
                "then": may_draw("runner", 1),
            },
            unsupported=[],
        )

    if cid == "rejig":
        return base(
            c,
            playRequiresInstalledProgramOrHardware=True,
            onPlay={
                "op": "do",
                "action": {"kind": "rejig_bounce_install"},
            },
            unsupported=[],
        )

    # --- v1.54.0 G-slice ---

    if cid == "project-yagi-uda":
        return base(
            c,
            onScore={
                "op": "do",
                "action": {
                    "kind": "add_agenda_counters_from_overadvance",
                    "past": 3,
                },
            },
            paidAbilities=[
                {
                    "id": "yagi-swap",
                    "label": (
                        "Hosted agenda counter: Swap 1 HQ card with 1 card "
                        "in the root of or protecting the attacked server; "
                        "Runner may jack out"
                    ),
                    "clickCost": 0,
                    "creditCost": 0,
                    "cost": {"agendaCounters": 1},
                    "windows": [
                        "approach_paw",
                        "encounter_paw",
                        "approach_server_paw",
                    ],
                    "requireDuringRun": True,
                    "effect": {
                        "op": "seq",
                        "effects": [
                            {
                                "op": "do",
                                "action": {
                                    "kind": "yagi_swap_hq_with_attacked_root_or_ice",
                                },
                            },
                            {
                                "op": "do",
                                "action": {"kind": "offer_jack_out"},
                            },
                        ],
                    },
                }
            ],
            unsupported=[],
        )

    if cid == "architect-deployment-test":
        return base(
            c,
            onScore={
                "op": "do",
                "action": {
                    "kind": "look_top_n_rd_may_install_and_rez_ignore_costs",
                    "n": 5,
                },
            },
            unsupported=[],
        )

    if cid == "daily-quest":
        return base(
            c,
            rezOnlyDuringCorpTurn=True,
            onSuccessfulRun=gain("runner", 2),
            onTurnBegin={
                "op": "if",
                "cond": {"op": "no_successful_run_on_host_server_last_turn"},
                "then": gain("corp", 3),
            },
            unsupported=[],
        )

    if cid == "baklan-bochkin":
        return base(
            c,
            onFirstEncounterEachRun={
                "op": "do",
                "action": {"kind": "add_power_counter", "amount": 1},
            },
            paidAbilities=[
                {
                    "id": "baklan-derez",
                    "label": (
                        "[trash], X power: Derez encountering ice if "
                        "strength ≤ X; take 1 tag"
                    ),
                    "clickCost": 0,
                    "creditCost": 0,
                    "cost": {
                        "trashSelf": True,
                        "powerCountersEqualEncounterStrength": True,
                    },
                    "windows": ["encounter_paw"],
                    "effect": {
                        "op": "seq",
                        "effects": [
                            {
                                "op": "do",
                                "action": {"kind": "derez_encounter_ice"},
                            },
                            {
                                "op": "do",
                                "action": {
                                    "kind": "give_tags",
                                    "amount": 1,
                                },
                            },
                        ],
                    },
                }
            ],
            unsupported=[],
        )

    if cid == "masterwork-v37":
        return base(
            c,
            muBonus=1,
            onFirstHardwareInstallEachTurn=draw("runner", 1),
            onRunBegin={
                "op": "do",
                "action": {
                    "kind": "may_install_from_grip",
                    "types": ["hardware"],
                    "discount": -1,
                },
            },
            unsupported=[],
        )

    # --- v1.55.0 H-slice ---

    if cid == "sting":
        sting_dmg = {
            "op": "do",
            "action": {
                "kind": "net_damage_1_plus_copies_of_source_title_in_other_score_area",
            },
        }
        return base(
            c,
            onScore=sting_dmg,
            onSteal=sting_dmg,
            unsupported=[],
        )

    if cid == "az-mccaffrey-mechanical-prodigy":
        return base(
            c,
            firstJobConnectionOrHardwareInstallDiscount=1,
            unsupported=[],
        )

    if cid == "saisentan":
        net1 = {
            "op": "do",
            "action": {"kind": "net_damage", "amount": 1},
        }
        return base(
            c,
            onEncounter={
                "op": "do",
                "action": {"kind": "choose_card_type_for_encounter"},
            },
            amplifyNetDamageOnTrashChosenEncounterType=True,
            subroutines=[
                {
                    "id": "saisentan-net-1",
                    "text": "Do 1 net damage.",
                    "effect": net1,
                },
                {
                    "id": "saisentan-net-2",
                    "text": "Do 1 net damage.",
                    "effect": net1,
                },
                {
                    "id": "saisentan-net-3",
                    "text": "Do 1 net damage.",
                    "effect": net1,
                },
            ],
            unsupported=[],
        )

    if cid == "focus-group":
        return base(
            c,
            playRequiresSuccessfulRunLastTurn=True,
            onPlay={
                "op": "do",
                "action": {"kind": "focus_group_reveal_may_advance"},
            },
            unsupported=[],
        )

    if cid == "divested-trust":
        return base(
            c,
            onOtherAgendaStolen={
                "op": "do",
                "action": {
                    "kind": "divested_trust_may_forfeit_return_stolen",
                    "gainCredits": 5,
                },
            },
            unsupported=[],
        )

    # --- v1.56.0 I-slice ---

    _companion_place_credit = {
        "op": "do",
        "action": {"kind": "place_hosted_credits", "amount": 1},
    }

    if cid == "fencer-fueno":
        return base(
            c,
            onTurnBegin=_companion_place_credit,
            onStealAgenda=_companion_place_credit,
            spendHostedCreditsDuringRuns=True,
            onRunnerTurnEnd={
                "op": "if",
                "cond": {"op": "hosted_credits_gte", "amount": 3},
                "then": {
                    "op": "choose",
                    "chooser": "runner",
                    "options": [
                        {
                            "id": "pay-1",
                            "label": "Pay 1¢",
                            "effect": {
                                "op": "do",
                                "action": {
                                    "kind": "lose_credits",
                                    "side": "runner",
                                    "amount": 1,
                                },
                            },
                        },
                        {
                            "id": "trash-self",
                            "label": "Trash Fencer Fueno",
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

    if cid == "trickster-taka":
        return base(
            c,
            onTurnBegin=_companion_place_credit,
            onStealAgenda=_companion_place_credit,
            spendHostedCreditsToUseProgramsDuringRuns=True,
            onRunnerTurnEnd={
                "op": "if",
                "cond": {"op": "hosted_credits_gte", "amount": 3},
                "then": {
                    "op": "choose",
                    "chooser": "runner",
                    "options": [
                        {
                            "id": "take-tag",
                            "label": "Take 1 tag",
                            "effect": {
                                "op": "do",
                                "action": {
                                    "kind": "give_tags",
                                    "amount": 1,
                                },
                            },
                        },
                        {
                            "id": "trash-self",
                            "label": "Trash Trickster Taka",
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

    if cid == "the-nihilist":
        return base(
            c,
            onFirstVirusInstallThisTurn={
                "op": "do",
                "action": {"kind": "add_virus_counter", "amount": 2},
            },
            onTurnBegin={
                "op": "do",
                "action": {
                    "kind": "nihilist_may_remove_2_virus_draw_unless_corp_trash_top_rd",
                },
            },
            unsupported=[],
        )

    if cid == "in-the-groove":
        return base(
            c,
            playRequiresFirstClick=True,
            remainderOfTurnOnInstallPrintedCostGte={
                "min": 1,
                "effect": {
                    "op": "choose",
                    "chooser": "runner",
                    "options": [
                        {
                            "id": "draw",
                            "label": "Draw 1 card",
                            "effect": draw("runner", 1),
                        },
                        {
                            "id": "gain",
                            "label": "Gain 1¢",
                            "effect": gain("runner", 1),
                        },
                    ],
                },
            },
            unsupported=[],
        )

    if cid == "game-over":
        return base(
            c,
            playRequiresAgendaStolenLastTurn=True,
            onPlay={
                "op": "seq",
                "effects": [
                    {
                        "op": "do",
                        "action": {
                            "kind": "game_over_trash_type_may_pay_3_prevent",
                        },
                    },
                    {
                        "op": "do",
                        "action": {
                            "kind": "give_bad_publicity",
                            "amount": 1,
                        },
                    },
                ],
            },
            unsupported=[],
        )

    # --- v1.57.0 J-slice ---

    if cid == "reduced-service":
        return base(
            c,
            rezSpendCreditsForPowerCounters={"max": 4},
            additionalRunInitiatePerPowerCounter={"credits": 2},
            onSuccessfulRun={
                "op": "if",
                "cond": {"op": "attacking_central"},
                "then": {
                    "op": "do",
                    "action": {"kind": "remove_power_counter", "amount": 1},
                },
            },
            unsupported=[],
        )

    if cid == "cold-site-server":
        return base(
            c,
            paidAbilities=[
                {
                    "id": "cold-site-power",
                    "label": "[click]: Place 1 power counter",
                    "clickCost": 1,
                    "creditCost": 0,
                    "cost": {"clicks": 1},
                    "windows": ["corp_action_paw"],
                    "effect": {
                        "op": "do",
                        "action": {"kind": "add_power_counter", "amount": 1},
                    },
                }
            ],
            additionalRunInitiatePerPowerCounter={"clicks": 1, "credits": 1},
            onTurnBegin={
                "op": "do",
                "action": {"kind": "remove_all_power_counters"},
            },
            unsupported=[],
        )

    if cid == "stargate":
        return base(
            c,
            paidAbilities=[
                {
                    "id": "stargate-run-rd",
                    "label": "[click]: Run R&D (once per turn)",
                    "clickCost": 1,
                    "creditCost": 0,
                    "cost": {"clicks": 1},
                    "windows": ["runner_action_paw"],
                    "oncePerTurn": True,
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "gain_credits",
                            "side": "runner",
                            "amount": 0,
                        },
                    },
                    "startsRun": {
                        "servers": "rd",
                        "onSuccessfulRun": {
                            "op": "seq",
                            "effects": [
                                {
                                    "op": "do",
                                    "action": {"kind": "set_run_skip_breach"},
                                },
                                {
                                    "op": "do",
                                    "action": {
                                        "kind": "reveal_top_n_rd_trash_one",
                                        "n": 3,
                                    },
                                },
                            ],
                        },
                    },
                }
            ],
            unsupported=[],
        )

    if cid == "letheia-nisei":
        return base(
            c,
            onApproachServerOncePerRun=True,
            onApproachServer={
                "op": "do",
                "action": {
                    "kind": "play_psi_game",
                    "maxBid": 2,
                    "ifBidsDiffer": {
                        "op": "choose",
                        "chooser": "corp",
                        "options": [
                            {
                                "id": "trash-move",
                                "label": "Trash Letheia Nisei → outermost + may jack out",
                                "effect": {
                                    "op": "seq",
                                    "effects": [
                                        {
                                            "op": "do",
                                            "action": {"kind": "trash_self"},
                                        },
                                        {
                                            "op": "do",
                                            "action": {
                                                "kind": "move_runner_to_outermost_attacked",
                                            },
                                        },
                                        {
                                            "op": "do",
                                            "action": {"kind": "offer_jack_out"},
                                        },
                                    ],
                                },
                            },
                            {
                                "id": "decline",
                                "label": "Decline",
                                "effect": gain("corp", 0),
                            },
                        ],
                    },
                },
            },
            unsupported=[],
        )

    if cid == "climactic-showdown":
        return base(
            c,
            onTurnBegin={
                "op": "seq",
                "effects": [
                    {"op": "do", "action": {"kind": "rfg_self"}},
                    {
                        "op": "do",
                        "action": {
                            "kind": "climactic_choose_server_corp_may_trash_ice_else_bonus_access",
                        },
                    },
                ],
            },
            unsupported=[],
        )

    # --- v1.58.0 K-slice (set-complete) ---

    if cid == "direct-access":
        return base(
            c,
            blankIdentitiesWhileResolving=True,
            runEvent={
                "servers": "any",
                "onRunEnd": {
                    "op": "do",
                    "action": {
                        "kind": "may_shuffle_title_from_heap_into_stack",
                        "title": "Direct Access",
                    },
                },
            },
            unsupported=[],
        )

    if cid == "lucky-charm":
        return base(
            c,
            paidAbilities=[
                {
                    "id": "lucky-charm-prevent-etr",
                    "label": (
                        "[interrupt] → Remove from the game: Prevent a "
                        "Corp card ability from ending the run"
                    ),
                    "clickCost": 0,
                    "creditCost": 0,
                    "cost": {"rfgSelf": True},
                    "windows": ["end_the_run_interrupt_paw"],
                    "requiresSuccessfulHqRunThisTurn": True,
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": (
                                "prevent_pending_end_the_run_"
                                "from_corp_card_ability"
                            ),
                        },
                    },
                }
            ],
            unsupported=[],
        )

    if cid == "whistleblower":
        return base(
            c,
            onSuccessfulRun={
                "op": "do",
                "action": {
                    "kind": (
                        "whistleblower_may_trash_name_agenda_"
                        "steal_ignore_costs"
                    ),
                },
            },
            unsupported=[],
        )

    if cid == "storgotic-resonator":
        return base(
            c,
            onFirstTrashMatchingRunnerIdentityFactionEachTurn={
                "op": "do",
                "action": {"kind": "add_power_counter", "amount": 1},
            },
            paidAbilities=[
                {
                    "id": "storgotic-net",
                    "label": "[click], hosted power counter: Do 1 net damage",
                    "clickCost": 1,
                    "creditCost": 0,
                    "cost": {"clicks": 1, "powerCounters": 1},
                    "windows": ["corp_action_paw"],
                    "effect": {
                        "op": "do",
                        "action": {"kind": "net_damage", "amount": 1},
                    },
                }
            ],
            unsupported=[],
        )

    if cid == "hyoubu-institute-absolute-clarity":
        return base(
            c,
            onFirstRevealEachTurn={
                "op": "do",
                "action": {
                    "kind": "gain_credits",
                    "side": "corp",
                    "amount": 1,
                },
            },
            paidAbilities=[
                {
                    "id": "hyoubu-reveal",
                    "label": (
                        "[click]: Reveal 1 card from the grip at random "
                        "or the top card of the stack"
                    ),
                    "clickCost": 1,
                    "creditCost": 0,
                    "cost": {"clicks": 1},
                    "windows": ["corp_action_paw"],
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "hyoubu_reveal_grip_random_or_stack_top",
                        },
                    },
                }
            ],
            unsupported=[],
        )

    if cid == "the-class-act":
        return base(
            c,
            onDiscardPhaseEnd={
                "op": "if",
                "cond": {"op": "self_installed_this_turn"},
                "then": draw("runner", 4),
            },
            onWouldDrawOncePerTurn={
                "op": "do",
                "action": {
                    "kind": "class_act_look_top_draw_amount_plus_one_bottom_one",
                },
            },
            unsupported=[],
        )

    if cid == "always-have-a-backup-plan":
        return base(
            c,
            runEvent={
                "servers": "any",
                "onRunEnd": {
                    "op": "if",
                    "cond": {"op": "run_unsuccessful"},
                    "then": {
                        "op": "do",
                        "action": {
                            "kind": (
                                "backup_plan_may_rerun_ignore_additional_"
                                "costs_bypass_last_ice"
                            ),
                        },
                    },
                },
            },
            unsupported=[],
        )

    if cid == "complete-image":
        return base(
            c,
            playRequiresSuccessfulRunLastTurn=True,
            playRequiresRunnerAgendaPointsGte=3,
            endsActionPhase=True,
            onPlay={
                "op": "do",
                "action": {"kind": "complete_image_name_net_damage_loop"},
            },
            unsupported=[],
        )

    if cid == "khusyuk":
        return base(
            c,
            runEvent={
                "servers": "rd",
                "onSuccessfulRun": {
                    "op": "seq",
                    "effects": [
                        {
                            "op": "do",
                            "action": {"kind": "set_run_skip_breach"},
                        },
                        {
                            "op": "do",
                            "action": {
                                "kind": (
                                    "khusyuk_choose_install_cost_"
                                    "set_aside_access_shuffle"
                                ),
                            },
                        },
                    ],
                },
            },
            unsupported=[],
        )

    if cid == "mirrormorph-endless-iteration":
        return base(
            c,
            mirrormorphOnThirdDistinctAction={
                "op": "choose",
                "chooser": "corp",
                "options": [
                    {
                        "id": "gain-1",
                        "label": "Gain 1¢",
                        "effect": gain("corp", 1),
                    },
                    {
                        "id": "extra-action",
                        "label": (
                            "Take another different action, paying [click] less"
                        ),
                        "effect": {
                            "op": "do",
                            "action": {
                                "kind": (
                                    "mirrormorph_take_different_"
                                    "action_click_discount"
                                ),
                            },
                        },
                    },
                    decline("corp"),
                ],
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
    notes = (
        "Null Signal Downfall (NRDB pack df) — Ashes set 1 of 2; legacy "
        "backwards wave before Uprising / System Gateway. Skip Magnum Opus "
        "Reprint (mor). Fully supported: all 65 cards mapped "
        "(wave gate v1.58.0)."
        if partial == 0
        else (
            "Null Signal Downfall (NRDB pack df) — Ashes set 1 of 2; legacy "
            "backwards wave before Uprising / System Gateway. Skip Magnum Opus "
            f"Reprint (mor). In-progress: {full} cards fully mapped, {partial} "
            "with unsupported notes (K-slice v1.58.0)."
        )
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
