#!/usr/bin/env python3
"""Generate Vantage Point card JSON from pinned pack `vp`.

Catalog source: Null-Signal-Games/netrunner-cards-json (see data/nsg-catalog-pin.json).
Fetch with: python3 scripts/nsg_catalog.py fetch vp

Hand-mapped Effect IR only where existing primitives fully cover the card;
everything else lists honest unsupported notes — never invent IR.

Usage: python3 scripts/generate-vantage-point.py
"""
from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

from nsg_catalog import load_pack_cards

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "vantage-point"
WAVE = "vantage-point"
PACK = "vp"
EXPECTED = 66


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


def map_card(c: dict) -> dict:
    cid = slugify(c["title"])
    text = strip_html(c.get("text") or "")
    plain = re.sub(r"\s+", " ", text).strip()

    # --- v1.13.0 kickoff: existing IR only ---

    if cid == "vulture-fund":
        return base(
            c,
            onPlay=seq(
                gain("corp", 14),
                {
                    "op": "do",
                    "action": {"kind": "give_bad_publicity", "amount": 1},
                },
            ),
            unsupported=[],
        )

    if cid == "flywheel":
        sub = seq(gain("corp", 1), may_draw("corp", 1))
        return base(
            c,
            subroutines=[
                {
                    "id": "flywheel-1",
                    "text": "Gain 1[credit]. You may draw 1 card.",
                    "effect": sub,
                },
                {
                    "id": "flywheel-2",
                    "text": "Gain 1[credit]. You may draw 1 card.",
                    "effect": sub,
                },
            ],
            unsupported=[],
        )

    if cid == "paywall":
        etr_unless_pay1 = {
            "op": "do",
            "action": {
                "kind": "unless",
                "payer": "runner",
                "cost": {
                    "op": "do",
                    "action": {
                        "kind": "lose_credits",
                        "side": "runner",
                        "amount": 1,
                    },
                },
                "instruction": etr(),
            },
        }
        return base(
            c,
            onEncounter={
                "op": "do",
                "action": {
                    "kind": "lose_credits",
                    "side": "runner",
                    "amount": 1,
                },
            },
            subroutines=[
                {
                    "id": "paywall-etr",
                    "text": "End the run unless the Runner pays 1[credit].",
                    "effect": etr_unless_pay1,
                }
            ],
            unsupported=[],
        )

    if cid == "borrowed-goods":
        return base(
            c,
            muBonus=1,
            onInstall={
                "op": "if",
                "cond": {"op": "runner_tagged"},
                "then": gain("runner", 0),
                "else": tags(1),
            },
            unsupported=[],
        )

    # --- v1.15.0 B-slice (v1.14.0 already shipped 8/66) ---

    if cid == "virtual-intelligence-p-i-you-can-call-me-vic":
        return base(
            c,
            paidAbilities=[
                {
                    "id": "vic-draw-untag",
                    "label": "Once per turn → [click], 1[credit]: Draw 1 and remove 1 tag",
                    "clickCost": 1,
                    "creditCost": 1,
                    "cost": {"clicks": 1, "credits": 1},
                    "oncePerTurn": True,
                    "windows": ["runner_action_paw"],
                    "effect": seq(
                        draw("runner", 1),
                        {
                            "op": "do",
                            "action": {"kind": "remove_tags", "amount": 1},
                        },
                    ),
                }
            ],
            unsupported=[],
        )

    if cid == "lionsmane":
        net2 = net(2)
        net2_unless_pay3 = {
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
                "instruction": net2,
            },
        }
        net2_unless_jack = {
            "op": "choose",
            "chooser": "runner",
            "options": [
                {
                    "id": "jack-out",
                    "label": "Jack out",
                    "effect": etr(),
                },
                {
                    "id": "net",
                    "label": "Suffer 2 net damage",
                    "effect": net2,
                },
            ],
        }
        return base(
            c,
            subroutines=[
                {
                    "id": "lionsmane-net",
                    "text": "Do 2 net damage.",
                    "effect": net2,
                },
                {
                    "id": "lionsmane-pay",
                    "text": "Do 2 net damage unless the Runner pays 3[credit].",
                    "effect": net2_unless_pay3,
                },
                {
                    "id": "lionsmane-jack",
                    "text": "Do 2 net damage unless the Runner jacks out.",
                    "effect": net2_unless_jack,
                },
            ],
            unsupported=[],
        )

    if cid == "esca":
        return base(
            c,
            mustRevealWhenAccessedFromRd=True,
            onAccess=seq(
                {
                    "op": "do",
                    "action": {
                        "kind": "lose_credits",
                        "side": "runner",
                        "amount": 1,
                    },
                },
                {
                    "op": "if",
                    "cond": {"op": "runner_tagged"},
                    "then": net(1),
                },
            ),
            unsupported=[],
        )

    if cid == "sleipnir":
        may_shuffle = {
            "op": "choose",
            "chooser": "corp",
            "options": [
                {
                    "id": "hq",
                    "label": "Shuffle 1 card from HQ into R&D",
                    "effect": {
                        "op": "do",
                        "action": {"kind": "shuffle_hq_to_rd", "amount": 1},
                    },
                },
                {
                    "id": "archives",
                    "label": "Shuffle 1 card from Archives into R&D",
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "shuffle_archives_to_rd",
                            "amount": 1,
                        },
                    },
                },
                decline("corp"),
            ],
        }
        return base(
            c,
            subroutines=[
                {
                    "id": "sleipnir-draw",
                    "text": "You may draw 1 card.",
                    "effect": may_draw("corp", 1),
                },
                {
                    "id": "sleipnir-shuffle",
                    "text": "You may shuffle 1 card from HQ or Archives into R&D.",
                    "effect": may_shuffle,
                },
                {
                    "id": "sleipnir-etr",
                    "text": "End the run.",
                    "effect": etr(),
                },
            ],
            unsupported=[],
        )

    if cid == "caveat-emptor":
        allotted = lambda delta: {
            "op": "do",
            "action": {
                "kind": "allotted_clicks_next_turn",
                "side": "runner",
                "delta": delta,
            },
        }
        return base(
            c,
            onPlay={
                "op": "choose",
                "chooser": "corp",
                "options": [
                    {
                        "id": "gain6",
                        "label": "Gain 6¢; Runner −1 allotted click next turn",
                        "effect": seq(gain("corp", 6), allotted(-1)),
                    },
                    {
                        "id": "gain10",
                        "label": "Gain 10¢; Runner +1 allotted click next turn",
                        "effect": seq(gain("corp", 10), allotted(1)),
                    },
                ],
            },
            unsupported=[],
        )

    if cid == "grubber":
        etr_unless_pay3 = {
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
                "instruction": etr(),
            },
        }
        sub = {
            "id": "grubber-etr",
            "text": "End the run unless the Runner pays 3[credit].",
            "effect": etr_unless_pay3,
        }
        return base(
            c,
            onRez={
                "op": "if",
                "cond": {"op": "protecting_central"},
                "then": {
                    "op": "do",
                    "action": {"kind": "give_bad_publicity", "amount": 1},
                },
            },
            subroutines=[
                {**sub, "id": "grubber-etr-1"},
                {**sub, "id": "grubber-etr-2"},
            ],
            unsupported=[],
        )

    if cid == "reverb":
        return base(
            c,
            rezCostDiscountPerOtherUnrezzedIce=1,
            subroutines=[
                {
                    "id": "reverb-etr-1",
                    "text": "End the run.",
                    "effect": etr(),
                },
                {
                    "id": "reverb-etr-2",
                    "text": "End the run.",
                    "effect": etr(),
                },
            ],
            unsupported=[],
        )

    if cid == "vertigo":
        return base(
            c,
            onPass={
                "op": "if",
                "cond": {
                    "op": "not",
                    "cond": {"op": "clicks_remaining", "side": "runner"},
                },
                "then": {
                    "op": "do",
                    "action": {"kind": "forbid_steal_trash_this_run"},
                },
            },
            subroutines=[
                {
                    "id": "vertigo-lose-click",
                    "text": "The Runner loses [click].",
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "lose_clicks",
                            "side": "runner",
                            "amount": 1,
                        },
                    },
                }
            ],
            unsupported=[],
        )


    if cid == "take-a-dive":
        return base(
            c,
            runEvent={
                "servers": "hq_rd",
                "onSuccessfulRun": {
                    "op": "if",
                    "cond": {"op": "subroutine_resolved_this_run"},
                    "then": {
                        "op": "do",
                        "action": {"kind": "give_bad_publicity", "amount": 1},
                    },
                },
                "onRunEnd": {
                    "op": "do",
                    "action": {"kind": "rfg_self"},
                },
            },
            unsupported=[],
        )

    if cid == "event-horizon":
        trash_prog_unless_pay3 = {
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
                    "action": {"kind": "trash_program", "pick": "choose"},
                },
            },
        }
        etr_unless_pay3 = {
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
                "instruction": etr(),
            },
        }
        return base(
            c,
            paidAbilities=[
                {
                    "id": "event-horizon-trash-etr",
                    "label": "[trash]: End the run (run against this server)",
                    "clickCost": 0,
                    "creditCost": 0,
                    "cost": {"trashSelf": True},
                    "requireDuringRun": True,
                    "windows": [
                        "approach_paw",
                        "encounter_paw",
                        "approach_server_paw",
                    ],
                    "effect": etr(),
                }
            ],
            subroutines=[
                {
                    "id": "event-horizon-trash-prog",
                    "text": "Trash 1 installed program unless the Runner pays 3[credit].",
                    "effect": trash_prog_unless_pay3,
                },
                {
                    "id": "event-horizon-etr",
                    "text": "End the run unless the Runner pays 3[credit].",
                    "effect": etr_unless_pay3,
                },
            ],
            unsupported=[],
        )

    if cid == "vicsek":
        return base(
            c,
            subroutines=[
                {
                    "id": "vicsek-x",
                    "text": "Do X net damage and give the Runner X tags. X is equal to the number of tags the Runner has.",
                    "effect": {
                        "op": "do",
                        "action": {"kind": "net_damage_and_tags_equal_runner_tags"},
                    },
                },
                {
                    "id": "vicsek-trash",
                    "text": "Give the Runner 1 tag. Trash this ice.",
                    "effect": seq(
                        tags(1),
                        {"op": "do", "action": {"kind": "trash_self"}},
                    ),
                },
            ],
            unsupported=[],
        )

    if cid == "sell-out":
        return base(
            c,
            playRequiresInstalledResource=True,
            playAdditionalCost={
                "op": "do",
                "action": {"kind": "trash_own_resource"},
            },
            onPlay=seq(gain("runner", 4), draw("runner", 2)),
            unsupported=[],
        )

    if cid == "underdome-irregulars":
        return base(
            c,
            onRunnerActionPhaseEnd={
                "op": "if",
                "cond": {"op": "ice_rezzed_this_turn"},
                "then": {
                    "op": "choose",
                    "chooser": "runner",
                    "options": [
                        {
                            "id": "draw",
                            "label": "Draw 2 cards",
                            "effect": draw("runner", 2),
                        },
                        {
                            "id": "untag",
                            "label": "Remove 1 tag",
                            "effect": {
                                "op": "do",
                                "action": {"kind": "remove_tags", "amount": 1},
                            },
                        },
                    ],
                },
                "else": {
                    "op": "do",
                    "action": {"kind": "trash_self"},
                },
            },
            unsupported=[],
        )

    if cid == "unleash":
        return base(
            c,
            playRequiresTagged=True,
            playAdditionalCost={
                "op": "do",
                "action": {"kind": "remove_tags", "amount": 1},
            },
            onPlay={
                "op": "do",
                "action": {"kind": "unleash_rez_may_resolve_sub"},
            },
            unsupported=[],
        )

    # --- v1.18.0 B-slice ---

    if cid == "witch-hunt":
        return base(
            c,
            badPublicityOnScore=1,
            onSteal={
                "op": "do",
                "action": {"kind": "give_bad_publicity", "amount": 1},
            },
            onCorpActionPhaseEnd={
                "op": "if",
                "cond": {"op": "self_scored_this_turn"},
                "then": seq(
                    {"op": "do", "action": {"kind": "remove_all_tags"}},
                    tags(3),
                ),
            },
            unsupported=[],
        )

    if cid == "stowaway":
        return base(
            c,
            installOnIce=True,
            onSuccessfulRun=gain("runner", 2),
            unsupported=[],
        )

    if cid == "melies-city-luxury-line":
        return base(
            c,
            stealAdditionalClicks=1,
            onScore={
                "op": "do",
                "action": {"kind": "gain_clicks", "side": "corp", "amount": 1},
            },
            unsupported=[],
        )

    # --- v1.19.0 B-slice ---

    if cid == "ansel-2-0":
        return base(
            c,
            subroutines=[
                {
                    "id": "ansel2-trash",
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
                    "id": "ansel2-rfg-heap",
                    "text": "Remove 1 card in the heap from the game.",
                    "effect": {
                        "op": "do",
                        "action": {"kind": "rfg_heap_card"},
                    },
                },
                {
                    "id": "ansel2-install",
                    "text": "You may install 1 card from HQ or Archives.",
                    "effect": {
                        "op": "do",
                        "action": {"kind": "install_from_hq_or_archives"},
                    },
                },
                {
                    "id": "ansel2-etr",
                    "text": "End the run.",
                    "effect": etr(),
                },
            ],
            unsupported=[],
        )

    if cid == "kompromat":
        return base(
            c,
            runEvent={
                "servers": "any",
                "requiresProtectingIce": True,
                "onRunEnd": seq(
                    {
                        "op": "if",
                        "cond": {"op": "run_successful"},
                        "then": {
                            "op": "do",
                            "action": {
                                "kind": "bp_unless_derez_protecting_attacked"
                            },
                        },
                    },
                    {"op": "do", "action": {"kind": "rfg_self"}},
                ),
            },
            unsupported=[],
        )

    if cid == "retirement-plan":
        return base(
            c,
            playAdditionalClick=True,
            onPlay={
                "op": "do",
                "action": {
                    "kind": "install_from_archives",
                    "types": ["agenda", "asset", "ice"],
                },
            },
            unsupported=[],
        )

    # --- v1.20.0 B-slice ---

    if cid == "ezam":
        return base(
            c,
            paidAbilities=[
                {
                    "id": "ezam-swap",
                    "label": "[click]: Swap this ice with another installed ice",
                    "clickCost": 1,
                    "creditCost": 0,
                    "cost": {"clicks": 1},
                    "windows": ["corp_action_paw"],
                    "effect": {
                        "op": "do",
                        "action": {"kind": "swap_source_ice_with_other"},
                    },
                }
            ],
            subroutines=[
                {
                    "id": "ezam-look",
                    "text": "Look at the top card of R&D. You may add that card to the bottom of R&D.",
                    "effect": {
                        "op": "do",
                        "action": {"kind": "look_top_rd_may_bottom"},
                    },
                },
                {
                    "id": "ezam-fortify",
                    "text": "Each piece of ice gets +1 strength for the remainder of this run.",
                    "effect": {
                        "op": "do",
                        "action": {"kind": "fortify_all_ice", "amount": 1},
                    },
                },
            ],
            unsupported=[],
        )

    if cid == "magistrate-revontulet":
        return base(
            c,
            stealAdditionalCreditsWhileRezzed=3,
            onAgendaScored={
                "op": "do",
                "action": {
                    "kind": "lose_credits",
                    "side": "runner",
                    "amount": 3,
                },
            },
            unsupported=[],
        )

    if cid == "scapegoat":
        return base(
            c,
            onPlay={
                "op": "choose",
                "chooser": "runner",
                "options": [
                    {
                        "id": "remove-bp",
                        "label": "Corp removes 2 bad publicity",
                        "effect": {
                            "op": "do",
                            "action": {
                                "kind": "remove_bad_publicity",
                                "amount": 2,
                            },
                        },
                    },
                    {
                        "id": "shuffle-installed",
                        "label": "Shuffle 1 installed Runner card into the stack",
                        "effect": {
                            "op": "do",
                            "action": {
                                "kind": "shuffle_installed_runner_into_stack",
                            },
                        },
                    },
                ],
            },
            unsupported=[],
        )

    # --- v1.21.0 B-slice ---

    if cid == "tailgate":
        return base(
            c,
            playCostDiscountPerIceProtectingServer="hq",
            runEvent={"servers": "hq", "bonusAccess": 2},
            unsupported=[],
        )

    if cid == "chain-reaction":
        return base(
            c,
            playRequiresSuccessfulAllCentralsThisTurn=True,
            onPlay=seq(
                {
                    "op": "do",
                    "action": {
                        "kind": "trash_n_installed_corp",
                        "count": 2,
                        "chooser": "runner",
                    },
                },
                {
                    "op": "do",
                    "action": {
                        "kind": "trash_installed_runner",
                        "pick": "choose",
                    },
                },
            ),
            unsupported=[],
        )

    if cid == "realloc":
        return base(
            c,
            playAdditionalClick=True,
            onPlay={
                "op": "do",
                "action": {"kind": "realloc_two_rezzed_ice"},
            },
            unsupported=[],
        )

    # --- v1.22.0 B-slice ---

    if cid == "myoshu":
        return base(
            c,
            playRequiresScoredAgendaNotInstalledThisTurn=True,
            agendaPoints=2,
            onPlay={
                "op": "do",
                "action": {
                    "kind": "score_self_as_agenda",
                    "agendaPoints": 2,
                },
            },
            unsupported=[],
        )

    if cid == "flood-the-market":
        return base(
            c,
            playAdditionalClick=True,
            onPlay={
                "op": "do",
                "action": {
                    "kind": "place_advancements_per_iced_rooted_remote",
                },
            },
            unsupported=[],
        )

    if cid == "synchrocyclotron":
        return base(
            c,
            firstDoubleOperationClickDiscount=1,
            unsupported=[],
        )

    # --- v1.23.0 B-slice ---

    if cid == "knowledge-seeker":
        return base(
            c,
            subroutines=[
                {
                    "id": "knowledge-seeker-1",
                    "text": "Place 1 virus counter on this ice.",
                    "effect": {
                        "op": "do",
                        "action": {"kind": "add_virus_counter", "amount": 1},
                    },
                },
                {
                    "id": "knowledge-seeker-2",
                    "text": "Look at the top 4 cards of R&D and arrange them in any order.",
                    "effect": {
                        "op": "do",
                        "action": {"kind": "look_top_n_rd_arrange", "n": 4},
                    },
                },
                {
                    "id": "knowledge-seeker-3",
                    "text": "End the run.",
                    "effect": etr(),
                },
            ],
            onEncounterEnd={
                "op": "if",
                "cond": {"op": "virus_counters_gte", "amount": 3},
                "then": seq(
                    {
                        "op": "do",
                        "action": {"kind": "purge_virus_counters"},
                    },
                    {
                        "op": "do",
                        "action": {"kind": "derez_source"},
                    },
                ),
            },
            unsupported=[],
        )

    if cid == "lotus-haze":
        return base(
            c,
            onScore={
                "op": "do",
                "action": {"kind": "add_agenda_counter", "amount": 3},
            },
            paidAbilities=[
                {
                    "id": "lotus-haze-move",
                    "label": "Hosted agenda counter: Move 1 rezzed upgrade to another server",
                    "clickCost": 0,
                    "creditCost": 0,
                    "cost": {"agendaCounters": 1},
                    "windows": ["corp_action_paw"],
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "may_move_rezzed_upgrade_to_another_server_root",
                        },
                    },
                },
            ],
            unsupported=[],
        )

    if cid == "hype-machine":
        return base(
            c,
            rezCostDiscountIfAgendaScoredOrStolenThisTurn=6,
            paidAbilities=[
                {
                    "id": "hype-machine-advance",
                    "label": "[trash]: Place 1 advancement on a card you can advance in this server's root",
                    "clickCost": 0,
                    "creditCost": 0,
                    "cost": {"trashSelf": True},
                    "windows": ["corp_action_paw"],
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "place_advancements",
                            "amount": 1,
                            "pick": "choose",
                            "sameServerRootAsSource": True,
                        },
                    },
                },
            ],
            unsupported=[],
        )

    # --- v1.24.0 B-slice ---

    if cid == "lethe":
        return base(
            c,
            onBypass=tags(1),
            onFullyBreak=tags(1),
            subroutines=[
                {
                    "id": "lethe-1",
                    "text": "You may add 1 card from Archives to the top or bottom of R&D.",
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "may_add_archives_card_to_rd_top_or_bottom",
                        },
                    },
                },
                {
                    "id": "lethe-2",
                    "text": "Add 1 installed Runner card to the grip.",
                    "effect": {
                        "op": "do",
                        "action": {"kind": "add_installed_runner_to_grip"},
                    },
                },
            ],
            unsupported=[],
        )

    if cid == "reanimation-protocol":
        return base(
            c,
            onPlay={
                "op": "do",
                "action": {
                    "kind": "install_and_rez_ice_from_archives",
                    "totalDiscount": 10,
                    "badPublicityIfNotSubtype": "liability",
                },
            },
            unsupported=[],
        )

    if cid == "the-tungsten-tailor":
        return base(
            c,
            muBonus=1,
            allIceStrengthPenalty=1,
            gainCreditOnBreakIceStrengthLteOncePerTurn=0,
            unsupported=[],
        )

    # --- v1.25.0 B-slice ---

    if cid == "hiram-0mission-svensson-shadow-of-the-past":
        return base(
            c,
            onHardwareInstallOrTrash={
                "op": "do",
                "action": {"kind": "look_top_n_rd_peek", "n": 1},
            },
            unsupported=[],
        )

    if cid == "the-red-room":
        return base(
            c,
            installServers=["hq", "rd", "archives"],
            onFirstAgendaScoredOrStolenThisTurn={
                "op": "do",
                "action": {"kind": "add_power_counter", "amount": 1},
            },
            paidAbilities=[
                {
                    "id": "red-room-etr",
                    "label": "Hosted power counter: End the run (other server)",
                    "clickCost": 0,
                    "creditCost": 0,
                    "cost": {"powerCounters": 1},
                    "windows": [
                        "approach_paw",
                        "approach_server_paw",
                        "encounter_paw",
                    ],
                    "requireDuringRun": True,
                    "requireOtherServer": True,
                    "effect": etr(),
                },
            ],
            unsupported=[],
        )

    if cid == "nihilo-agent":
        return base(
            c,
            onRez={
                "op": "do",
                "action": {"kind": "add_power_counter", "amount": 3},
            },
            trashWhenPowerEmpty=True,
            onTurnBegin=seq(
                {
                    "op": "do",
                    "action": {"kind": "remove_tags", "amount": 1},
                },
                {
                    "op": "do",
                    "action": {"kind": "remove_bad_publicity", "amount": 1},
                },
            ),
            onDiscardPhaseEnd=seq(
                tags(1),
                {
                    "op": "do",
                    "action": {"kind": "give_bad_publicity", "amount": 1},
                },
                {
                    "op": "do",
                    "action": {"kind": "remove_power_counter", "amount": 1},
                },
            ),
            unsupported=[],
        )

    # --- v1.26.0 B-slice ---

    if cid == "flagship":
        return base(
            c,
            installServers=["hq", "rd"],
            runsCannotBeSuccessful=True,
            maxAccessOtherThanSelf=1,
            unsupported=[],
        )

    if cid == "cultivate":
        return base(
            c,
            onPlay={
                "op": "do",
                "action": {
                    "kind": "look_top_n_rd_trash_one_hq_one_arrange_rest",
                    "n": 5,
                },
            },
            unsupported=[],
        )

    if cid == "touchstone":
        return base(
            c,
            hostedCreditsOnFirstEventPlayOncePerTurn=1,
            spendHostedCreditsDuringRuns=True,
            unsupported=[],
        )

    # --- v1.27.0 B-slice ---

    if cid == "stick-and-poke":
        return base(
            c,
            firstEncounterGainsSubroutine={
                "text": "Do 1 net damage. The Runner draws 1 card.",
                "effect": seq(net(1), draw("runner", 1)),
            },
            unsupported=[],
        )

    if cid == "rotary":
        return base(
            c,
            muBonus=1,
            mayTakeTagForBonusAccessOnHqRdBreach=1,
            paidAbilities=[
                {
                    "id": "rotary-corp-trash",
                    "label": "[click], 2[credit]: Trash Rotary (Corp; Runner tagged)",
                    "clickCost": 1,
                    "creditCost": 2,
                    "cost": {"clicks": 1, "credits": 2},
                    "windows": ["corp_action_paw"],
                    "usableByAnyPlayer": True,
                    "requireRunnerTagged": True,
                    "effect": {
                        "op": "do",
                        "action": {"kind": "trash_self"},
                    },
                }
            ],
            unsupported=[],
        )

    if cid == "sipa":
        return base(
            c,
            maySwapOutermostIceOnPassAfterFullyBreakOncePerTurn=True,
            unsupported=[],
        )

    # --- v1.28.0 B-slice ---

    if cid == "sacrifice-zone-expansion":
        return base(
            c,
            installFaceup=True,
            creditsOnFirstAdvanceThisTurn=3,
            onSuccessfulRunOtherServerOncePerTurn={
                "op": "choose",
                "chooser": "corp",
                "options": [
                    {
                        "id": "remove-adv-meat",
                        "label": "Remove 1 advancement: do 1 meat damage",
                        "effect": {
                            "op": "do",
                            "action": {
                                "kind": "remove_advancements",
                                "amount": 1,
                                "then": {
                                    "op": "do",
                                    "action": {
                                        "kind": "meat_damage",
                                        "amount": 1,
                                    },
                                },
                            },
                        },
                    },
                    decline("corp"),
                ],
            },
            unsupported=[],
        )

    if cid == "shackleton-grid":
        return base(
            c,
            onSpendCreditsOutsidePoolDuringRunOncePerTurn={
                "op": "choose",
                "chooser": "corp",
                "options": [
                    {
                        "id": "meat-4",
                        "label": "Do 4 meat damage",
                        "effect": {
                            "op": "do",
                            "action": {"kind": "meat_damage", "amount": 4},
                        },
                    },
                    decline("corp"),
                ],
            },
            unsupported=[],
        )

    if cid == "tocsin":
        return base(
            c,
            paidAbilities=[
                {
                    "id": "tocsin-search",
                    "label": "[click], 1[credit], trash: Search R&D for barrier + sentry",
                    "clickCost": 1,
                    "creditCost": 1,
                    "cost": {"clicks": 1, "credits": 1, "trashSelf": True},
                    "windows": ["corp_action_paw"],
                    "usableFromHq": True,
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "search_rd_up_to_one_each_subtype_to_hq",
                            "subtypes": ["barrier", "sentry"],
                        },
                    },
                }
            ],
            subroutines=[
                {
                    "id": "tocsin-lose",
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
                    "id": "tocsin-etr-1",
                    "text": "End the run.",
                    "effect": etr(),
                },
                {
                    "id": "tocsin-etr-2",
                    "text": "End the run.",
                    "effect": etr(),
                },
            ],
            unsupported=[],
        )

    # --- v1.29.0 B-slice (stealth cluster foundation) ---

    if cid == "corsair":
        return breaker_card(
            c,
            "barrier",
            0,
            1,
            paidAbilities=[
                {
                    "id": "corsair-weaken",
                    "label": "1[credit] from stealth: barrier gets −3 strength",
                    "clickCost": 0,
                    "creditCost": 1,
                    "cost": {"credits": 1, "creditsFromStealthOnly": True},
                    "windows": ["encounter_paw"],
                    "requireEncounterSubtype": "barrier",
                    "effect": {
                        "op": "do",
                        "action": {"kind": "weaken_ice", "amount": 3},
                    },
                }
            ],
            unsupported=[],
        )

    if cid == "methuselah":
        return base(
            c,
            muBonus=1,
            spendHostedCreditsDuringRuns=True,
            onRunBegin={
                "op": "do",
                "action": {
                    "kind": "may_trash_hardware_from_grip_place_hosted_credits",
                    "amount": 2,
                },
            },
            unsupported=[],
        )

    if cid == "lampades":
        return base(
            c,
            powerCountersOnInstall=3,
            accessTrashPayingPrintedCostFromStealth=True,
            unsupported=[],
        )

    # --- v1.30.0 B-slice (stealth cluster finish) ---

    if cid == "baker":
        return base(
            c,
            paidAbilities=[
                {
                    "id": "baker-run",
                    "label": "[click]: Run Archives (may redirect approach with stealth)",
                    "clickCost": 1,
                    "creditCost": 0,
                    "cost": {"clicks": 1},
                    "windows": ["runner_action_paw"],
                    "oncePerTurn": True,
                    "startsRun": {
                        "servers": "archives",
                        "mayRedirectApproachArchivesToHqOrRdPayingStealthCredits": 1,
                    },
                    "effect": gain("runner", 0),
                }
            ],
            unsupported=[],
        )

    if cid == "aircheck":
        return base(
            c,
            runEvent={
                "servers": "hq_rd",
                "placeEventCredits": 4,
                "blockCreditPoolSpendAndLose": True,
                "onRunEnd": {
                    "op": "if",
                    "cond": {"op": "run_successful"},
                    "then": {
                        "op": "do",
                        "action": {
                            "kind": "may_start_run",
                            "servers": "remote",
                        },
                    },
                },
            },
            unsupported=[],
        )

    # --- v1.31.0 B-slice ---

    if cid == "luana-campos":
        return base(
            c,
            onTurnBegin={
                "op": "do",
                "action": {
                    "kind": "may_host_bad_publicity_then",
                    "amount": 1,
                    "then": seq(gain("corp", 3), draw("corp", 1)),
                },
            },
            returnHostedBadPublicityOnUninstall=True,
            unsupported=[],
        )

    if cid == "let-them-dream":
        return base(
            c,
            agendaPointsModifierInRunnerScoreArea=-1,
            onScore={
                "op": "do",
                "action": {
                    "kind": "may_search_hq_rd_archives_agenda_to_hq_or_rd_bottom",
                },
            },
            unsupported=[],
        )

    if cid == "editorial-division-ad-nihilum":
        return base(
            c,
            onFirstBadPublicityTakeEachTurn={
                "op": "do",
                "action": {
                    "kind": "may_search_rd_non_agenda_any_subtype_to_hq",
                    "subtypes": ["black ops", "gray ops", "liability"],
                },
            },
            unsupported=[],
        )

    # --- v1.32.0 B-slice ---

    if cid == "nurse-hanh":
        return base(
            c,
            onArchivesFacedownTurnedFaceupGte={
                "min": 2,
                "effect": draw("runner", 2),
            },
            unsupported=[],
        )

    if cid == "beta-build":
        return base(
            c,
            onPlay={
                "op": "do",
                "action": {
                    "kind": "search_stack_non_virus_program_install_ignore_costs_track",
                },
            },
            runEvent={
                "servers": "any",
                "onRunEnd": {
                    "op": "do",
                    "action": {
                        "kind": "return_tracked_install_to_stack_top_if_installed",
                    },
                },
            },
            unsupported=[],
        )

    if cid == "perfect-recall":
        return base(
            c,
            powerCountersOnRez=1,
            powerCounterOnAgendaScoredOrStolenFromThisServer=1,
            paidAbilities=[
                {
                    "id": "perfect-recall-reveal",
                    "label": "Hosted power: Reveal HQ card — Runner cannot steal/trash copies this run",
                    "clickCost": 0,
                    "creditCost": 0,
                    "cost": {"powerCounters": 1},
                    "windows": ["approach_paw", "encounter_paw", "approach_server_paw"],
                    "requiresActiveRun": True,
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "reveal_hq_forbid_steal_trash_copies_this_run",
                        },
                    },
                }
            ],
            unsupported=[],
        )

    # --- v1.33.0 B-slice (final four → 66/66) ---

    if cid == "word-on-the-street":
        return base(
            c,
            additionalCostOnScoreAgendaInstalledThisTurn={
                "op": "do",
                "action": {
                    "kind": "add_to_corp_score_as_agenda",
                    "agendaPoints": -1,
                    "cannotForfeit": True,
                },
            },
            onAgendaScored={
                "op": "if",
                "cond": {
                    "op": "not",
                    "cond": {"op": "last_scored_agenda_installed_this_turn"},
                },
                "then": seq(
                    {"op": "do", "action": {"kind": "trash_self"}},
                    gain("runner", 4),
                    draw("runner", 1),
                ),
            },
            unsupported=[],
        )

    if cid == "read-write-share":
        may_host = {
            "op": "do",
            "action": {"kind": "may_host_one_from_grip_facedown_then_draw"},
        }
        return base(
            c,
            maxHostedCards=4,
            onInstall=may_host,
            onTurnBegin=may_host,
            paidAbilities=[
                {
                    "id": "read-write-share-shuffle",
                    "label": "[trash]: Shuffle all hosted cards into your stack",
                    "clickCost": 0,
                    "creditCost": 0,
                    "cost": {"trashSelf": True},
                    "windows": ["runner_action_paw", "corp_action_paw"],
                    "effect": {
                        "op": "do",
                        "action": {"kind": "shuffle_hosted_cards_into_stack"},
                    },
                }
            ],
            unsupported=[],
        )

    if cid == "hackerspace":
        return base(
            c,
            hostsUniqueCompanionOrConnectionResources={"creditDiscount": 1},
            handSizeBonusIfHostingCompanionAndConnection=2,
            unsupported=[],
        )

    if cid == "melies-u-only-the-brightest":
        return base(
            c,
            onDiscardPhaseEnd={
                "op": "do",
                "action": {"kind": "melies_secretly_set_face"},
            },
            flipIdentityOnSuccessfulCentralRun=True,
            onRunnerActionPhaseEnd={
                "op": "if",
                "cond": {"op": "identity_unflipped"},
                "then": gain("corp", 1),
            },
            identityFlippedHooks={
                "onFlipToBackIfRunMatchesFace": {
                    "op": "do",
                    "action": {
                        "kind": "look_top_rd_may_trash_if_do_archives_to_hq"
                    },
                },
                "onRunnerDiscardPhaseEnd": {
                    "op": "do",
                    "action": {"kind": "flip_identity"},
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
            "Null Signal Vantage Point (NRDB pack vp) — next constructed set after "
            "Elevation. Kickoff extract: fail-closed IR; "
            f"{full} cards fully mapped, {partial} with unsupported notes "
            "(wave kickoff v1.13.0)."
        ),
        "cards": written,
    }
    if full >= 12:
        manifest["notes"] = (
            "Null Signal Vantage Point (NRDB pack vp) — next constructed set after "
            "Elevation. Fail-closed IR; "
            f"{full} cards fully mapped, {partial} with unsupported notes "
            f"(wave v1.33.0 B-slice)."
        )
        if full >= EXPECTED and partial == 0:
            manifest["status"] = "supported"
            manifest["notes"] = (
                "Null Signal Vantage Point (NRDB pack vp) — fully mapped "
                f"({full}/{EXPECTED}; wave gate v1.33.0)."
            )
        else:
            manifest["status"] = "in-progress"
    (OUT / "_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"
    )

    print(f"Wrote {len(written)} cards to {OUT}")
    print(f"Among written: full={full} partial={partial}")
    print("POOL_IDS=" + json.dumps(written))


if __name__ == "__main__":
    main()
