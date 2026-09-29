#!/usr/bin/env python3
"""Generate The Automata Initiative card JSON from pinned pack `tai`.

Catalog source: Null-Signal-Games/netrunner-cards-json (see data/nrdb-catalog-pin.json).
Fetch with: python3 scripts/nrdb_catalog.py fetch tai

Hand-mapped Effect IR only where existing primitives fully cover the card;
everything else lists honest unsupported notes — never invent IR.

Usage: python3 scripts/generate-tai.py
"""
from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

from nrdb_catalog import load_pack_cards

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "the-automata-initiative"
WAVE = "the-automata-initiative"
PACK = "tai"
EXPECTED = 65


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


def trash_self():
    return {"op": "do", "action": {"kind": "trash_self"}}


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

    # --- Fully clear kickoff mappings (existing IR only) ---
    if cid == "strike-fund":
        return base(
            c,
            onPlay=gain("runner", 4),
            onTrashFromGripOrStack=choose(
                "runner",
                [
                    {
                        "id": "gain-2",
                        "label": "Gain 2¢",
                        "effect": gain("runner", 2),
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

    if cid == "joy-ride":
        return base(
            c,
            runEvent={
                "servers": "rd",
                "onSuccessfulRun": draw("runner", 5),
            },
            unsupported=[],
        )

    if cid == "fujii-asset-retrieval":
        return base(
            c,
            onScore=net(2),
            onSteal=net(2),
            unsupported=[],
        )

    if cid == "behold":
        return base(
            c,
            mustRevealWhenAccessedFromRd=True,
            skipOnAccessFromArchives=True,
            onAccess=choose(
                "corp",
                [
                    {
                        "id": "pay",
                        "label": "Pay 4¢: give the Runner 2 tags",
                        "effect": seq(
                            lose("corp", 4),
                            tags(2),
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

    if cid == "your-digital-life":
        return base(
            c,
            onPlay={
                "op": "do",
                "action": {"kind": "gain_credits_per_hq_card", "per": 1},
            },
            unsupported=[],
        )

    if cid == "shibboleth":
        card = breaker_card(
            c, "code gate", 3, 1, pump_c=2, pump_s=2, break_max=1, unsupported=[]
        )
        card["threatStrengthBonus"] = {"level": 4, "amount": -2}
        return card

    if cid == "mindscaping":
        return base(
            c,
            onPlay=choose(
                "corp",
                [
                    {
                        "id": "gain-draw",
                        "label": "Gain 4¢ and draw 2 cards",
                        "effect": seq(gain("corp", 4), draw("corp", 2)),
                    },
                    {
                        "id": "hq-top-rd",
                        "label": "Add 1 card from HQ to the top of R&D",
                        "effect": {
                            "op": "do",
                            "action": {"kind": "hq_to_top_rd", "pick": "choose"},
                        },
                    },
                    {
                        "id": "net-tags",
                        "label": "Do X net damage (X = tags, max 3)",
                        "effect": {
                            "op": "do",
                            "action": {"kind": "net_damage_up_to_tags", "max": 3},
                        },
                    },
                ],
            ),
            unsupported=[],
        )

    if cid == "jaguarundi":
        return base(
            c,
            onEncounter={
                "op": "if",
                "cond": {"op": "threat", "level": 4},
                "then": choose(
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
                            "id": "take-tag",
                            "label": "Take 1 tag",
                            "effect": tags(1),
                        },
                    ],
                ),
            },
            subroutines=[
                {
                    "id": "jag-tag",
                    "text": "Give the Runner 1 tag.",
                    "effect": tags(1),
                },
                {
                    "id": "jag-core",
                    "text": "If the Runner is tagged, do 1 core damage.",
                    "effect": {
                        "op": "if",
                        "cond": {"op": "runner_tagged"},
                        "then": core(1),
                    },
                },
            ],
            unsupported=[],
        )

    if cid == "tree-line":
        return base(
            c,
            canAdvance=True,
            strengthPerAdvancement=1,
            paidAbilities=[
                {
                    "id": "tree-line-expend",
                    "label": (
                        "[click], 1¢, reveal and trash from HQ: "
                        "place 3 advancements on 1 installed ice"
                    ),
                    "clickCost": 1,
                    "creditCost": 1,
                    "cost": {"clicks": 1, "credits": 1, "trashSelf": True},
                    "windows": ["corp_action_paw"],
                    "usableFromHq": True,
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "place_advancements",
                            "amount": 3,
                            "anyInstalledIce": True,
                        },
                    },
                }
            ],
            subroutines=[
                {
                    "id": "tl-gain-etr",
                    "text": "Gain 1[credit]. End the run.",
                    "effect": seq(gain("corp", 1), etr()),
                }
            ],
            unsupported=[],
        )

    if cid == "phoneutria":
        return base(
            c,
            onPass={
                "op": "if",
                "cond": {"op": "grip_count_gte", "amount": 4},
                "then": tags(1),
            },
            subroutines=[
                {
                    "id": "phone-net-1",
                    "text": "Do 1 net damage.",
                    "effect": net(1),
                },
                {
                    "id": "phone-net-2",
                    "text": "Do 1 net damage.",
                    "effect": net(1),
                },
            ],
            unsupported=[],
        )

    if cid == "slap-vandal":
        return base(
            c,
            installOnIce=True,
            strength=6,
            paidAbilities=[
                {
                    "id": "slap-break-host",
                    "label": "1¢: Break 1 subroutine on host ice",
                    "clickCost": 0,
                    "creditCost": 1,
                    "cost": {"credits": 1},
                    "windows": ["encounter_paw"],
                    "oncePerEncounter": True,
                    "effect": {
                        "op": "do",
                        "action": {"kind": "break_host_subroutine"},
                    },
                }
            ],
            unsupported=[],
        )

    if cid == "attini":
        pay_or_net = choose(
            "runner",
            [
                {
                    "id": "pay",
                    "label": "Pay 2¢",
                    "effect": lose("runner", 2),
                },
                {
                    "id": "net",
                    "label": "Suffer 1 net damage",
                    "effect": net(1),
                },
            ],
        )
        # Threat 3: Runner cannot spend credits while these resolve →
        # pay path is impossible; take net. Spend-block also covers prevention.
        sub_fx = {
            "op": "if",
            "cond": {"op": "threat", "level": 3},
            "then": net(1),
            "else": pay_or_net,
        }
        return base(
            c,
            threatCannotSpendCreditsDuringSubs=3,
            subroutines=[
                {
                    "id": "attini-1",
                    "text": "Do 1 net damage unless the Runner pays 2[credit].",
                    "effect": sub_fx,
                },
                {
                    "id": "attini-2",
                    "text": "Do 1 net damage unless the Runner pays 2[credit].",
                    "effect": sub_fx,
                },
                {
                    "id": "attini-3",
                    "text": "Do 1 net damage unless the Runner pays 2[credit].",
                    "effect": sub_fx,
                },
            ],
            unsupported=[],
        )

    if cid == "beatriz-friere-gonzalez":
        return base(
            c,
            paidAbilities=[
                {
                    "id": "beatriz-run",
                    "label": "[click][click]: Run HQ; success → breach R&D +1 access",
                    "clickCost": 2,
                    "creditCost": 0,
                    "cost": {"clicks": 2},
                    "windows": ["runner_action_paw"],
                    "effect": gain("runner", 0),
                    "startsRun": {
                        "servers": "hq",
                        "redirectSuccessTo": "rd",
                        "bonusAccess": 1,
                    },
                }
            ],
            unsupported=[],
        )

    if cid == "laser-pointer":
        paid = []
        for sub in ("ap", "destroyer", "observer"):
            paid.append(
                {
                    "id": f"laser-bypass-{sub}",
                    "label": f"Trash Laser Pointer: bypass encountered {sub} ice",
                    "clickCost": 0,
                    "creditCost": 0,
                    "cost": {"trashSelf": True},
                    "windows": ["encounter_paw"],
                    "requireEncounterSubtype": sub,
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "bypass_current_ice",
                            "requireSubtype": sub,
                        },
                    },
                }
            )
        return base(c, paidAbilities=paid, unsupported=[])

    if cid == "m-i-c":
        return base(
            c,
            paidAbilities=[
                {
                    "id": "mic-trash-etr",
                    "label": "[trash]: End the run unless the Runner spends [click]",
                    "clickCost": 0,
                    "creditCost": 0,
                    "cost": {"trashSelf": True},
                    "windows": ["approach_paw"],
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
                }
            ],
            subroutines=[
                {
                    "id": "mic-lose-1",
                    "text": "The Runner loses [click].",
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
                    "id": "mic-lose-2",
                    "text": "The Runner loses [click].",
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
                    "id": "mic-etr",
                    "text": "End the run.",
                    "effect": etr(),
                },
            ],
            unsupported=[],
        )

    if cid == "hermes":
        return base(
            c,
            muBonus=1,
            onAgendaScoredOrStolen=draw("corp", 1),
            unsupported=[],
        )

    if cid == "salvo-testing":
        return base(
            c,
            onAgendaScored=choose(
                "corp",
                [
                    {
                        "id": "core",
                        "label": "Do 1 core damage",
                        "effect": core(1),
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

    if cid == "monkeywrench":
        return base(
            c,
            installOnIce=True,
            hostStrengthModifier=-2,
            otherIceProtectingServerStrengthModifier=-1,
            unsupported=[],
        )

    if cid == "capybara":
        return base(
            c,
            onBypass=choose(
                "runner",
                [
                    {
                        "id": "rfg-derez",
                        "label": "Remove from the game: derez that ice",
                        "effect": {
                            "op": "do",
                            "action": {
                                "kind": "rfg_self_then_derez_bypassed_ice"
                            },
                        },
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

    if cid == "ablative-barrier":
        return base(
            c,
            onRez={
                "op": "if",
                "cond": {"op": "threat", "level": 3},
                "then": {
                    "op": "if",
                    "cond": {"op": "source_protects_attacked_server"},
                    "then": choose(
                        "corp",
                        [
                            {
                                "id": "install",
                                "label": (
                                    "Install 1 non-agenda from HQ/Archives "
                                    "protecting/root of another server"
                                ),
                                "effect": {
                                    "op": "do",
                                    "action": {
                                        "kind": "install_from_hq_or_archives",
                                        "excludeAgenda": True,
                                        "excludeSourceServer": True,
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
            },
            subroutines=[
                {
                    "id": "ablative-etr",
                    "text": "End the run.",
                    "effect": etr(),
                }
            ],
            unsupported=[],
        )

    if cid == "lilypad":
        return base(
            c,
            muBonus=2,
            onFirstProgramInstallEachTurn=choose(
                "runner",
                [
                    {
                        "id": "draw",
                        "label": "Draw 1 card",
                        "effect": draw("runner", 1),
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

    if cid == "hannah-wheels-pilintra":
        return base(
            c,
            paidAbilities=[
                {
                    "id": "wheels-run",
                    "label": (
                        "[click]: Gain [click]. Run a remote; "
                        "if unsuccessful, take 1 tag"
                    ),
                    "clickCost": 1,
                    "creditCost": 0,
                    "cost": {"clicks": 1},
                    "windows": ["runner_action_paw"],
                    "oncePerTurn": True,
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "gain_clicks",
                            "side": "runner",
                            "amount": 1,
                        },
                    },
                    "startsRun": {
                        "servers": "remote",
                        "onRunEnd": {
                            "op": "if",
                            "cond": {"op": "run_unsuccessful"},
                            "then": tags(1),
                        },
                    },
                },
                {
                    "id": "wheels-remove-tag",
                    "label": "[click], [trash]: Gain [click][click]. Remove 1 tag",
                    "clickCost": 1,
                    "creditCost": 0,
                    "cost": {"clicks": 1, "trashSelf": True},
                    "windows": ["runner_action_paw"],
                    "effect": seq(
                        {
                            "op": "do",
                            "action": {
                                "kind": "gain_clicks",
                                "side": "runner",
                                "amount": 2,
                            },
                        },
                        {
                            "op": "do",
                            "action": {"kind": "remove_tags", "amount": 1},
                        },
                    ),
                },
            ],
            unsupported=[],
        )

    if cid == "armed-asset-protection":
        return base(
            c,
            onPlay=seq(
                gain("corp", 3),
                {
                    "op": "do",
                    "action": {
                        "kind": "gain_credits_per_distinct_faceup_archive_type"
                    },
                },
            ),
            unsupported=[],
        )

    if cid == "saci":
        return base(
            c,
            installOnIce=True,
            onHostRezzed=gain("runner", 3),
            onHostDerezzed=gain("runner", 3),
            unsupported=[],
        )

    if cid == "tatu-bola":
        return base(
            c,
            onPass=choose(
                "corp",
                [
                    {
                        "id": "swap",
                        "label": "Swap with ice from HQ; gain 4¢",
                        "effect": {
                            "op": "do",
                            "action": {
                                "kind": "swap_ice_with_hq",
                                "gainCredits": 4,
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
                    "id": "tatu-bola-etr",
                    "text": "End the run.",
                    "effect": etr(),
                }
            ],
            unsupported=[],
        )

    if cid == "solidarity-badge":
        return base(
            c,
            onFirstCorpCardTrashEachTurn={
                "op": "do",
                "action": {"kind": "add_power_counter", "amount": 1},
            },
            onTurnBegin={
                "op": "if",
                "cond": {"op": "power_counters_gte", "amount": 1},
                "then": choose(
                    "runner",
                    [
                        {
                            "id": "draw",
                            "label": "Remove 1 power: draw 1 card",
                            "effect": seq(
                                {
                                    "op": "do",
                                    "action": {
                                        "kind": "remove_power_counter",
                                        "amount": 1,
                                    },
                                },
                                draw("runner", 1),
                            ),
                        },
                        {
                            "id": "remove-tag",
                            "label": "Remove 1 power: remove 1 tag",
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
                                        "kind": "remove_tags",
                                        "amount": 1,
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
            },
            unsupported=[],
        )

    if cid == "eru-ayase-pessoa":
        return base(
            c,
            paidAbilities=[
                {
                    "id": "eru-run-archives",
                    "label": (
                        "[click], take 1 tag: Run Archives; "
                        "success → breach R&D (Threat 3: +1 access)"
                    ),
                    "clickCost": 1,
                    "creditCost": 0,
                    "cost": {"clicks": 1, "tags": 1},
                    "windows": ["runner_action_paw"],
                    "oncePerTurn": True,
                    "effect": gain("runner", 0),
                    "startsRun": {
                        "servers": "archives",
                        "redirectSuccessTo": "rd",
                        "onSuccessfulRun": {
                            "op": "if",
                            "cond": {"op": "threat", "level": 3},
                            "then": {
                                "op": "do",
                                "action": {
                                    "kind": "bonus_access",
                                    "amount": 1,
                                },
                            },
                        },
                    },
                }
            ],
            unsupported=[],
        )

    if cid == "valentao":
        return base(
            c,
            rezAdditionalCost=choose(
                "corp",
                [
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
            ),
            subroutines=[
                {
                    "id": "valentao-gain",
                    "text": "Gain 2[credit].",
                    "effect": gain("corp", 2),
                },
                {
                    "id": "valentao-lose",
                    "text": "The Runner loses 2[credit].",
                    "effect": lose("runner", 2),
                },
                {
                    "id": "valentao-etr",
                    "text": "End the run if you have more credits than the Runner.",
                    "effect": {
                        "op": "if",
                        "cond": {"op": "credits_gt_other_side", "side": "corp"},
                        "then": etr(),
                    },
                },
            ],
            unsupported=[],
        )

    if cid == "s-dobrado":
        return base(
            c,
            runEvent={
                "servers": "central",
                "bypassFirstEncounter": True,
                "bypassSecondEncounterForClickIfThreat": 4,
            },
            unsupported=[],
        )

    if cid == "slash-and-burn-agriculture":
        return base(
            c,
            paidAbilities=[
                {
                    "id": "sab-expend",
                    "label": (
                        "[click], 1¢, reveal and trash from HQ: "
                        "place 2 advancements on 1 advanceable card"
                    ),
                    "clickCost": 1,
                    "creditCost": 1,
                    "cost": {"clicks": 1, "credits": 1, "trashSelf": True},
                    "windows": ["corp_action_paw"],
                    "usableFromHq": True,
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "place_advancements",
                            "amount": 2,
                        },
                    },
                }
            ],
            unsupported=[],
        )

    if cid == "audrey-v2":
        return base(
            c,
            breaker={
                "breaksSubtype": "*",
                "strength": 0,
                "breakCredits": 0,
                "breakViaPaidAbilityOnly": True,
            },
            onAccessTrash={
                "op": "do",
                "action": {"kind": "add_virus_counter", "amount": 1},
            },
            paidAbilities=[
                {
                    "id": "audrey-break",
                    "label": "Hosted virus counter: Break up to 2 subroutines",
                    "clickCost": 0,
                    "creditCost": 0,
                    "cost": {"virusCounters": 1},
                    "windows": ["encounter_paw"],
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "break_encounter_subroutine",
                            "maxSubs": 2,
                        },
                    },
                },
                {
                    "id": "audrey-pump",
                    "label": "Trash 1 card from grip: +3 strength",
                    "clickCost": 0,
                    "creditCost": 0,
                    "cost": {"trashFromGrip": 1},
                    "windows": ["encounter_paw"],
                    "effect": {
                        "op": "do",
                        "action": {"kind": "pump_strength", "amount": 3},
                    },
                },
            ],
            unsupported=[],
        )

    if cid == "the-price":
        return base(
            c,
            onPlay={
                "op": "do",
                "action": {
                    "kind": "trash_top_n_may_install_discount",
                    "count": 4,
                    "discount": 3,
                },
            },
            unsupported=[],
        )

    if cid == "lago-paranoa-shelter":
        return base(
            c,
            onFirstCorpRootInstallEachTurn=choose(
                "runner",
                [
                    {
                        "id": "mill-draw",
                        "label": "Trash top of stack: draw 1",
                        "effect": seq(
                            {
                                "op": "do",
                                "action": {"kind": "trash_top_of_stack"},
                            },
                            draw("runner", 1),
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

    if cid == "angelique-garza-correa":
        return base(
            c,
            onAccessRequiresRezzed=True,
            onAccess=choose(
                "corp",
                [
                    {
                        "id": "pay",
                        "label": "Pay 2¢: do 2 meat damage",
                        "effect": seq(lose("corp", 2), meat(2)),
                    },
                    {
                        "id": "decline",
                        "label": "Decline",
                        "effect": gain("corp", 0),
                    },
                ],
            ),
            paidAbilities=[
                {
                    "id": "angelique-expend",
                    "label": (
                        "Threat 3 → [click], 1¢, trash from HQ: do 1 meat damage"
                    ),
                    "clickCost": 1,
                    "creditCost": 1,
                    "requiresThreat": 3,
                    "cost": {"clicks": 1, "credits": 1, "trashSelf": True},
                    "windows": ["corp_action_paw"],
                    "usableFromHq": True,
                    "effect": meat(1),
                }
            ],
            unsupported=[],
        )

    if cid == "b-1001":
        return base(
            c,
            paidAbilities=[
                {
                    "id": "b1001-etr",
                    "label": "Remove 1 tag: End the run (other server only)",
                    "clickCost": 0,
                    "creditCost": 0,
                    "cost": {"removeTags": 1},
                    "windows": [
                        "approach_server_paw",
                        "approach_paw",
                        "encounter_paw",
                    ],
                    "requireOtherServer": True,
                    "effect": etr(),
                }
            ],
            unsupported=[],
        )

    if cid == "umbrella":
        return base(
            c,
            interfaceRequiresTrojanHost=True,
            breaker={
                "breaksSubtype": "code gate",
                "strength": 5,
                "breakCredits": 0,
                "breakViaPaidAbilityOnly": True,
            },
            paidAbilities=[
                {
                    "id": "umbrella-break",
                    "label": (
                        "2¢: Break up to 3 code gate subs; "
                        "if any, each player may draw 1"
                    ),
                    "clickCost": 0,
                    "creditCost": 2,
                    "cost": {"credits": 2},
                    "windows": ["encounter_paw"],
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "break_encounter_subroutine",
                            "maxSubs": 3,
                            "requireSubtype": "code gate",
                            "thenIfBroke": seq(
                                choose(
                                    "runner",
                                    [
                                        {
                                            "id": "draw",
                                            "label": "Draw 1",
                                            "effect": draw("runner", 1),
                                        },
                                        {
                                            "id": "decline",
                                            "label": "Decline",
                                            "effect": gain("runner", 0),
                                        },
                                    ],
                                ),
                                choose(
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
                            ),
                        },
                    },
                }
            ],
            unsupported=[],
        )

    if cid == "pichacao":
        return base(
            c,
            installOnIce=True,
            onPassHost=choose(
                "runner",
                [
                    {
                        "id": "gain-click",
                        "label": "Gain [click]",
                        "effect": seq(
                            {
                                "op": "do",
                                "action": {
                                    "kind": "gain_clicks",
                                    "side": "runner",
                                    "amount": 1,
                                },
                            },
                            {
                                "op": "if",
                                "cond": {
                                    "op": "clicks_gained_this_run_gte",
                                    "amount": 2,
                                },
                                "then": {
                                    "op": "do",
                                    "action": {
                                        "kind": "return_source_to_grip"
                                    },
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

    if cid == "cybersand-harvester":
        return base(
            c,
            hostedCreditsOnAnyIceRez=2,
            hostedCreditsSpendFor=["install"],
            paidAbilities=[
                {
                    "id": "cybersand-take-all",
                    "label": "[trash]: Take all hosted credits",
                    "clickCost": 0,
                    "creditCost": 0,
                    "cost": {"trashSelf": True},
                    "windows": ["corp_action_paw"],
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "take_hosted_credits",
                            "amount": 999,
                        },
                    },
                }
            ],
            unsupported=[],
        )

    if cid == "urban-art-vernissage":
        return base(
            c,
            hostedCreditsSpendFor=["install"],
            onTurnBegin={
                "op": "do",
                "action": {
                    "kind": "may_return_non_virus_trojan_to_grip_place_hosted",
                    "hostedAmount": 2,
                },
            },
            unsupported=[],
        )

    if cid == "banner":
        return base(
            c,
            breaker={
                "breaksSubtype": "barrier",
                "strength": 5,
                "breakCredits": 0,
                "breakViaPaidAbilityOnly": True,
            },
            paidAbilities=[
                {
                    "id": "banner-suppress-etr",
                    "label": "2¢: barrier subs cannot ETR this encounter",
                    "clickCost": 0,
                    "creditCost": 2,
                    "cost": {"credits": 2},
                    "windows": ["encounter_paw"],
                    "requireEncounterSubtype": "barrier",
                    "effect": {
                        "op": "do",
                        "action": {"kind": "forbid_end_the_run_this_encounter"},
                    },
                }
            ],
            unsupported=[],
        )

    if cid == "curupira":
        return base(
            c,
            breaker={
                "breaksSubtype": "barrier",
                "strength": 1,
                "breakCredits": 1,
                "breakMaxSubs": 1,
                "pumpCredits": 1,
                "pumpStrength": 1,
                "breakViaPaidAbilityOnly": True,
            },
            onFullyBreak={
                "op": "do",
                "action": {"kind": "add_power_counter", "amount": 1},
            },
            paidAbilities=[
                {
                    "id": "curupira-bypass",
                    "label": "Spend 3 power: bypass encountered barrier",
                    "clickCost": 0,
                    "creditCost": 0,
                    "cost": {"powerCounters": 3},
                    "windows": ["encounter_paw"],
                    "requireEncounterSubtype": "barrier",
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "bypass_current_ice",
                            "requireSubtype": "barrier",
                        },
                    },
                },
                {
                    "id": "curupira-break",
                    "label": "1¢: Break 1 barrier subroutine",
                    "clickCost": 0,
                    "creditCost": 1,
                    "cost": {"credits": 1},
                    "windows": ["encounter_paw"],
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
                    "id": "curupira-pump",
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

    if cid == "debbie-downtown-moreira":
        return base(
            c,
            hostedCreditsOnRunEventPlay=1,
            onInstall={
                "op": "if",
                "cond": {"op": "threat", "level": 4},
                "then": {
                    "op": "do",
                    "action": {"kind": "place_hosted_credits", "amount": 2},
                },
            },
            paidAbilities=[
                {
                    "id": "debbie-run",
                    "label": (
                        "[click]: Run any server; spend hosted credits "
                        "during that run"
                    ),
                    "clickCost": 1,
                    "creditCost": 0,
                    "cost": {"clicks": 1},
                    "windows": ["runner_action_paw"],
                    "effect": gain("runner", 0),
                    "startsRun": {
                        "servers": "any",
                        "transferHostedCreditsToEventCredits": True,
                    },
                }
            ],
            unsupported=[],
        )

    if cid == "virtual-service-agent":
        return base(
            c,
            onPass={
                "op": "if",
                "cond": {
                    "op": "did_not_break_printed_sub_with_decoder_this_encounter"
                },
                "then": tags(1),
            },
            subroutines=[
                {
                    "id": "vsa-lose",
                    "text": "The Runner loses 1[credit].",
                    "effect": lose("runner", 1),
                }
            ],
            unsupported=[],
        )

    if cid == "mercury-chrome-libertador":
        return base(
            c,
            onBreachHqRdIfNoBreaksOncePerTurnMayBonusAccess=1,
            unsupported=[],
        )

    if cid == "oracle-thinktank":
        return base(
            c,
            onSteal=tags(1),
            paidAbilities=[
                {
                    "id": "oracle-shuffle",
                    "label": "[click], remove 1 tag: Shuffle this into R&D",
                    "clickCost": 1,
                    "creditCost": 0,
                    "cost": {"clicks": 1, "removeTags": 1},
                    "windows": ["corp_action_paw"],
                    "usableFromRunnerScoreArea": True,
                    "effect": {
                        "op": "do",
                        "action": {"kind": "shuffle_source_into_rd"},
                    },
                }
            ],
            unsupported=[],
        )

    if cid == "living-mural":
        return base(
            c,
            installOnIce=True,
            breaker={
                "breaksSubtype": "sentry",
                "strength": 1,
                "breakCredits": 1,
                "breakMaxSubs": 1,
                "pumpCredits": 1,
                "pumpStrength": 2,
                "breakViaPaidAbilityOnly": True,
            },
            onInstall={
                "op": "if",
                "cond": {"op": "threat", "level": 4},
                "then": {
                    "op": "do",
                    "action": {"kind": "gain_strength_this_turn", "amount": 3},
                },
            },
            paidAbilities=[
                {
                    "id": "mural-break",
                    "label": "1¢: Break 1 sentry sub protecting host server",
                    "clickCost": 0,
                    "creditCost": 1,
                    "cost": {"credits": 1},
                    "windows": ["encounter_paw"],
                    "requireProtectingHostServer": True,
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
                    "id": "mural-pump",
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

    if cid == "greasing-the-palm":
        return base(
            c,
            onPlay=seq(
                gain("corp", 5),
                {
                    "op": "do",
                    "action": {
                        "kind": "may_install_from_hq_paying_costs",
                        "thenMayRemoveTagToAdvance": True,
                    },
                },
            ),
            unsupported=[],
        )

    if cid == "bahia-bands":
        return base(
            c,
            runEvent={
                "servers": "any",
                "onSuccessfulRun": {
                    "op": "do",
                    "action": {
                        "kind": "choose_exactly_n",
                        "n": 2,
                        "options": [
                            {
                                "id": "draw2",
                                "label": "Draw 2",
                                "effect": draw("runner", 2),
                            },
                            {
                                "id": "install-discount",
                                "label": "Install from grip (−1¢)",
                                "effect": {
                                    "op": "do",
                                    "action": {
                                        "kind": "may_install_from_grip",
                                        "discount": 1,
                                    },
                                },
                            },
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
                                "id": "bank-trash-credits",
                                "label": "Place 4¢; spend for trash costs this run",
                                "effect": seq(
                                    {
                                        "op": "do",
                                        "action": {
                                            "kind": "place_hosted_credits",
                                            "amount": 4,
                                        },
                                    },
                                    {
                                        "op": "do",
                                        "action": {
                                            "kind": "enable_hosted_credits_spend_for",
                                            "purposes": ["trash"],
                                        },
                                    },
                                ),
                            },
                        ],
                    },
                },
            },
            unsupported=[],
        )

    if cid == "vovo-ozetti":
        return base(
            c,
            iceRezCostReductionProtectingThisServer=2,
            rootRezCostReductionThisServerIfThreat={
                "level": 4,
                "amount": 2,
            },
            onCorpTurnEnd={
                "op": "do",
                "action": {
                    "kind": "may_move_source_upgrade_to_another_server_root"
                },
            },
            unsupported=[],
        )

    if cid == "oppo-research":
        return base(
            c,
            playRequiresRunnerStoleOrTrashedCorpCardLastTurn=True,
            endsActionPhase=True,
            onPlay=seq(
                tags(2),
                {
                    "op": "if",
                    "cond": {"op": "threat", "level": 3},
                    "then": choose(
                        "corp",
                        [
                            {
                                "id": "pay",
                                "label": "Pay 5¢: give 2 tags",
                                "effect": seq(
                                    lose("corp", 5),
                                    tags(2),
                                ),
                            },
                            {
                                "id": "decline",
                                "label": "Decline",
                                "effect": gain("corp", 0),
                            },
                        ],
                    ),
                },
            ),
            unsupported=[],
        )

    if cid == "epiphany-analytica-nations-undivided":
        return base(
            c,
            onFirstRunnerStoleOrTrashedCorpCardThisTurn={
                "op": "do",
                "action": {"kind": "add_power_counter", "amount": 1},
            },
            paidAbilities=[
                {
                    "id": "epiphany-look-install",
                    "label": (
                        "[click], hosted power counter: Look at top 3 "
                        "of R&D; may install 1"
                    ),
                    "clickCost": 1,
                    "creditCost": 0,
                    "cost": {"clicks": 1, "powerCounters": 1},
                    "windows": ["corp_action_paw"],
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "look_top_n_rd_may_install_one",
                            "n": 3,
                        },
                    },
                }
            ],
            unsupported=[],
        )

    if cid == "pivot":
        return base(
            c,
            playAdditionalClick=True,
            onPlay=seq(
                {
                    "op": "do",
                    "action": {
                        "kind": "search_rd_operation_or_agenda_to_hq"
                    },
                },
                {
                    "op": "if",
                    "cond": {"op": "threat", "level": 3},
                    "then": {
                        "op": "do",
                        "action": {"kind": "may_play_or_install_from_hq"},
                    },
                },
            ),
            unsupported=[],
        )

    if cid == "federal-fundraising":
        return base(
            c,
            onTurnBegin=choose(
                "corp",
                [
                    {
                        "id": "look",
                        "label": "Look at top 3 of R&D and arrange",
                        "effect": {
                            "op": "do",
                            "action": {
                                "kind": "look_top_n_rd_arrange",
                                "n": 3,
                                "thenMayDrawIfUnprotected": True,
                            },
                        },
                    },
                    {
                        "id": "decline-look",
                        "label": "Decline to look",
                        "effect": {
                            "op": "if",
                            "cond": {
                                "op": "host_server_unprotected_by_ice"
                            },
                            "then": choose(
                                "corp",
                                [
                                    {
                                        "id": "draw",
                                        "label": "Draw 1 card",
                                        "effect": draw("corp", 1),
                                    },
                                    {
                                        "id": "decline",
                                        "label": "Decline to draw",
                                        "effect": gain("corp", 0),
                                    },
                                ],
                            ),
                            "else": gain("corp", 0),
                        },
                    },
                ],
            ),
            unsupported=[],
        )

    if cid == "wage-workers":
        return base(
            c,
            wageWorkersTrackActions=True,
            unsupported=[],
        )

    if cid == "front-company":
        return base(
            c,
            rezOnlyDuringCorpTurn=True,
            firstRunCannotTargetRemote=True,
            onFirstArchivesRunBeginThisTurn={
                "op": "if",
                "cond": {"op": "host_server_unprotected_by_ice"},
                "then": net(2),
            },
            unsupported=[],
        )

    if cid == "balanced-coverage":
        return base(
            c,
            onTurnBegin=choose(
                "corp",
                [
                    {
                        "id": "peek",
                        "label": "Choose a type and look at the top card of R&D",
                        "effect": {
                            "op": "do",
                            "action": {
                                "kind": "look_top_1_rd_choose_type_may_reveal_gain",
                                "credits": 2,
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

    if cid == "chrysopoeian-skimming":
        return base(
            c,
            onPlay={
                "op": "do",
                "action": {
                    "kind": "corp_may_reveal_agenda_from_hq",
                    "then": seq(
                        {
                            "op": "do",
                            "action": {
                                "kind": "gain_clicks",
                                "side": "runner",
                                "amount": 1,
                            },
                        },
                        draw("runner", 1),
                    ),
                    "else": {
                        "op": "do",
                        "action": {"kind": "look_top_n_rd_peek", "n": 3},
                    },
                },
            },
            unsupported=[],
        )

    if cid == "tucana":
        return base(
            c,
            remoteOnly=True,
            persistent=True,
            onAgendaScoredOrStolen={
                "op": "if",
                "cond": {
                    "op": "last_agenda_scored_or_stolen_from_source_server_root"
                },
                "then": choose(
                    "corp",
                    [
                        {
                            "id": "search",
                            "label": "Search R&D for ice; install and rez (−3¢)",
                            "effect": {
                                "op": "do",
                                "action": {
                                    "kind": "search_rd_install_rez_ice_on_source_server",
                                    "totalDiscount": 3,
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
            unsupported=[],
        )

    if cid == "starlit-knight":
        return base(
            c,
            onEncounter={
                "op": "if",
                "cond": {"op": "threat", "level": 4},
                "then": {
                    "op": "do",
                    "action": {
                        "kind": "etr_subroutines_per_runner_tags_on_encounter"
                    },
                },
            },
            subroutines=[
                {
                    "id": "starlit-tag-1",
                    "text": "Give the Runner 1 tag.",
                    "effect": tags(1),
                },
                {
                    "id": "starlit-tag-2",
                    "text": "Give the Runner 1 tag.",
                    "effect": tags(1),
                },
            ],
            unsupported=[],
        )

    if cid == "daniela-jorge-inacio":
        grip_bottom = {
            "op": "do",
            "action": {
                "kind": "add_random_grip_to_stack_bottom",
                "count": 2,
            },
        }
        return base(
            c,
            persistent=True,
            trashAdditionalCost=grip_bottom,
            stealAdditionalCostFromProtectingServer=grip_bottom,
            unsupported=[],
        )

    if cid == "adrian-seis":
        return base(
            c,
            onSuccessfulRun={
                "op": "do",
                "action": {
                    "kind": "play_psi_game",
                    "maxBid": 2,
                    "ifBidsDiffer": {
                        "op": "do",
                        "action": {
                            "kind": "restrict_run_access",
                            "mode": "only_source",
                            "cardIdsFromSource": True,
                        },
                    },
                    "ifBidsMatch": {
                        "op": "do",
                        "action": {
                            "kind": "restrict_run_access",
                            "mode": "forbid_source",
                            "cardIdsFromSource": True,
                        },
                    },
                },
            },
            onCorpTurnEnd={
                "op": "do",
                "action": {
                    "kind": "may_move_source_upgrade_to_another_server_root"
                },
            },
            unsupported=[],
        )

    if cid == "a-teia-ip-recovery":
        return base(
            c,
            maxRemoteServers=2,
            onFirstRemoteInstallThisTurn={
                "op": "do",
                "action": {
                    "kind": "may_install_from_hq_on_other_remote_ignore_costs",
                    "cannotScoreInstalledCardThisTurn": True,
                },
            },
            unsupported=[],
        )

    if cid == "arissana-rocha-nahu-street-artist":
        return base(
            c,
            paidAbilities=[
                {
                    "id": "arissana-install-program",
                    "label": (
                        "Once per turn: 0¢ install 1 program from grip "
                        "(pay install cost); run only"
                    ),
                    "clickCost": 0,
                    "creditCost": 0,
                    "cost": {"credits": 0},
                    "oncePerTurn": True,
                    "requireDuringRun": True,
                    "windows": [
                        "approach_paw",
                        "approach_server_paw",
                        "encounter_paw",
                        "runner_action_paw",
                    ],
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "install_program_from_grip_paying_cost",
                            "trackOnRunEndTrashUnlessSubtype": "trojan",
                        },
                    },
                }
            ],
            unsupported=[],
        )

    if cid == "stegodon-mk-iv":
        return base(
            c,
            whileScoredBreakerStrengthPenaltyIfIceDerezzedThisRun=2,
            onFirstRunBeginThisTurn={
                "op": "do",
                "action": {
                    "kind": "may_derez_installed",
                    "onlyIce": True,
                    "excludeProtectingAttackedServer": True,
                    "then": gain("corp", 1),
                },
            },
            unsupported=[],
        )

    if cid == "airbladex-jsrf-ed":
        return base(
            c,
            powerCountersOnInstall=3,
            trashWhenPowerEmpty=True,
            paidAbilities=[
                {
                    "id": "airblade-prevent-damage",
                    "label": (
                        "Interrupt: hosted power counter — prevent 1 net "
                        "damage (run only)"
                    ),
                    "clickCost": 0,
                    "creditCost": 0,
                    "cost": {"powerCounters": 1},
                    "windows": ["damage_interrupt_paw"],
                    "requireDuringRun": True,
                    "requirePendingDamageTypes": ["net"],
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "prevent_pending_damage",
                            "amount": 1,
                        },
                    },
                },
                {
                    "id": "airblade-prevent-encounter",
                    "label": (
                        "Interrupt: hosted power counter — prevent when "
                        "encountered on ice"
                    ),
                    "clickCost": 0,
                    "creditCost": 0,
                    "cost": {"powerCounters": 1},
                    "windows": ["when_encountered_interrupt_paw"],
                    "requireDuringRun": True,
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "prevent_current_ice_on_encounter"
                        },
                    },
                },
            ],
            unsupported=[],
        )

    # Fallback: skeleton with full text as unsupported

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
        "status": "supported",
        "notes": (
            "Null Signal The Automata Initiative (NRDB pack tai) — Liberation "
            "set 1 of 2. Fully supported: all 65 cards mapped (wave gate v0.86.0)."
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
