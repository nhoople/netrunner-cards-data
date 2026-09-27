#!/usr/bin/env python3
"""Generate The Automata Initiative card JSON from NRDB pack `tai`.

Requires /tmp/nrdb-cards.json (curl https://netrunnerdb.com/api/2.0/public/cards).

Hand-mapped Effect IR only where existing primitives fully cover the card;
everything else lists honest unsupported notes — never invent IR.

Usage: python3 scripts/generate-tai.py
"""
from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "the-automata-initiative"
NRDB = Path("/tmp/nrdb-cards.json")
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
            breaker={
                "breaksSubtype": "code gate",
                "strength": 5,
                "breakCredits": 0,
                "breakViaPaidAbilityOnly": True,
                "interfaceRequiresTrojanHost": True,
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

    # Fallback: skeleton with full text as unsupported

    card = base(c)
    card["unsupported"] = [f"Full text not yet mapped to IR: {plain[:240]}"]
    return card


def main():
    data = json.loads(NRDB.read_text())["data"]
    pack = sorted(
        [c for c in data if c.get("pack_code") == PACK],
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
            "Null Signal The Automata Initiative (NRDB pack tai) — Liberation "
            "set 1 of 2. Wave is in-progress: simple cards mapped where Effect "
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
