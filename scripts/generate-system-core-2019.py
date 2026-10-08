#!/usr/bin/env python3
"""Generate System Core 2019 card JSON from pinned pack `sc19`.

Catalog source: Null-Signal-Games/netrunner-cards-json (see data/nsg-catalog-pin.json).
Fetch with: python3 scripts/nsg_catalog.py fetch sc19

System Core 2019 is the next legacy-backwards wave after Downfall. Magnum Opus
(`mo`) and Magnum Opus Reprint (`mor`) are skipped/absorbed — not corpus waves.

Titles already clear under System Gateway / System Update 2021 are treated as
reprints: skip emitting duplicate files; list their ids in pool.json (SU21 pattern).

Hand-mapped Effect IR only where existing primitives fully cover the card;
everything else lists honest unsupported notes — never invent IR.

Usage: python3 scripts/generate-system-core-2019.py
"""
from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

from nsg_catalog import load_pack_cards

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "system-core-2019"
WAVE = "system-core-2019"
PACK = "sc19"
EXPECTED = 147

# Already defined (and clear) under system-gateway / system-update-2021.
# Do not emit duplicate files; pool.json still lists these ids for the wave.
REPRINTS = {
    "abagnale",
    "aesops-pawnshop",
    "archer",
    "archived-memories",
    "atman",
    "biotic-labor",
    "career-fair",
    "celebrity-gift",
    "corroder",
    "crisium-grid",
    "daily-business-show",
    "diesel",
    "dirty-laundry",
    "earthrise-hotel",
    "eli-1-0",
    "emergency-shutdown",
    "enigma",
    "femme-fatale",
    "gordian-blade",
    "hedge-fund",
    "hokusai-grid",
    "hortum",
    "hostile-takeover",
    "ice-carver",
    "ice-wall",
    "imp",
    "inside-job",
    "jinteki-personal-evolution",
    "legwork",
    "liberated-account",
    "lotus-field",
    "marilyn-campaign",
    "mimic",
    "networking",
    "nisei-mk-ii",
    "oaktown-renovation",
    "pad-campaign",
    "pop-up-window",
    "professional-contacts",
    "project-atlas",
    "project-beale",
    "project-vitruvius",
    "psychographics",
    "punitive-counterstrike",
    "quetzal-free-spirit",
    "reina-roja-freedom-fighter",
    "retrieval-run",
    "reversed-accounts",
    "rielle-kit-peddler-transhuman",
    "ronin",
    "rototurret",
    "scrubber",
    "snare",
    "sneakdoor-beta",
    "sure-gamble",
    "swordsman",
    "test-run",
    "the-makers-eye",
    "tollbooth",
    "trick-of-light",
    "weyland-consortium-building-a-better-world",
    "wraparound",
    "xanadu",
}


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


def net(n: int):
    return {"op": "do", "action": {"kind": "net_damage", "amount": n}}


def draw(side: str, n: int):
    return {"op": "do", "action": {"kind": "draw", "side": side, "amount": n}}


def seq(*effects):
    return {"op": "seq", "effects": list(effects)}


def breaker_card(
    c,
    subtype,
    strength,
    break_c,
    pump_c=None,
    pump_s=None,
    break_max=None,
    duration=None,
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
        if duration:
            pump_eff["action"]["duration"] = duration
        label_dur = (
            " for the remainder of this run" if duration == "run" else ""
        )
        paid.append(
            {
                "id": f"{slugify(c['title'])}-pump",
                "label": (
                    f"Pump {c['title']} +{pump_s if pump_s is not None else 1} "
                    f"strength{label_dur}"
                ),
                "clickCost": 0,
                "creditCost": pump_c,
                "cost": {"credits": pump_c},
                "windows": ["encounter_paw"],
                "effect": pump_eff,
            }
        )
    return base(c, breaker=br, paidAbilities=paid, **extra)


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


def map_card(c: dict) -> dict | None:
    cid = slugify(c["title"])
    if cid in REPRINTS:
        return None

    text = strip_html(c.get("text") or "")
    plain = re.sub(r"\s+", " ", text).strip()

    # --- v1.59.0 kickoff: existing IR only ---

    if cid == "easy-mark":
        return base(c, onPlay=gain("runner", 3), unsupported=[])

    if cid == "beanstalk-royalties":
        return base(c, onPlay=gain("corp", 3), unsupported=[])

    if cid == "wall-of-static":
        return base(
            c,
            subroutines=[
                {
                    "id": "wall-of-static-etr",
                    "text": "End the run.",
                    "effect": etr(),
                }
            ],
            unsupported=[],
        )

    if cid == "akamatsu-mem-chip":
        return base(c, muBonus=1, unsupported=[])

    if cid == "spiderweb":
        return base(
            c,
            subroutines=[
                {
                    "id": "spiderweb-etr-1",
                    "text": "End the run.",
                    "effect": etr(),
                },
                {
                    "id": "spiderweb-etr-2",
                    "text": "End the run.",
                    "effect": etr(),
                },
                {
                    "id": "spiderweb-etr-3",
                    "text": "End the run.",
                    "effect": etr(),
                },
            ],
            unsupported=[],
        )

    # --- v1.60.0 A-slice: existing IR only ---

    if cid == "neural-katana":
        return base(
            c,
            subroutines=[
                {
                    "id": "neural-katana-net",
                    "text": "Do 3 net damage.",
                    "effect": net(3),
                }
            ],
            unsupported=[],
        )

    if cid == "wall-of-thorns":
        return base(
            c,
            subroutines=[
                {
                    "id": "wall-of-thorns-net",
                    "text": "Do 2 net damage.",
                    "effect": net(2),
                },
                {
                    "id": "wall-of-thorns-etr",
                    "text": "End the run.",
                    "effect": etr(),
                },
            ],
            unsupported=[],
        )

    if cid == "armitage-codebusting":
        return base(
            c,
            hostedCreditsOnInstall=12,
            paidAbilities=[
                {
                    "id": "armitage-codebusting-take",
                    "label": "Take 2¢",
                    "clickCost": 1,
                    "creditCost": 0,
                    "cost": {"clicks": 1},
                    "windows": ["runner_action_paw"],
                    "effect": {
                        "op": "do",
                        "action": {"kind": "take_hosted_credits", "amount": 2},
                    },
                }
            ],
            unsupported=[],
        )

    if cid == "hadrians-wall":
        return base(
            c,
            canAdvance=True,
            strengthPerAdvancement=1,
            subroutines=[
                {
                    "id": "hadrians-wall-etr-1",
                    "text": "End the run.",
                    "effect": etr(),
                },
                {
                    "id": "hadrians-wall-etr-2",
                    "text": "End the run.",
                    "effect": etr(),
                },
            ],
            unsupported=[],
        )

    if cid == "ipo":
        return base(
            c,
            endsActionPhase=True,
            onPlay=gain("corp", 13),
            unsupported=[],
        )

    # --- v1.61.0 B-slice: existing IR only ---

    if cid == "battering-ram":
        return breaker_card(
            c,
            "barrier",
            3,
            2,
            1,
            1,
            break_max=2,
            duration="run",
            unsupported=[],
        )

    if cid == "force-of-nature":
        return breaker_card(
            c,
            "code gate",
            1,
            2,
            1,
            1,
            break_max=2,
            unsupported=[],
        )

    if cid == "pipeline":
        return breaker_card(
            c,
            "sentry",
            1,
            1,
            2,
            1,
            break_max=1,
            duration="run",
            unsupported=[],
        )

    if cid == "blue-level-clearance":
        return base(
            c,
            playAdditionalClick=True,
            onPlay=seq(gain("corp", 5), draw("corp", 2)),
            unsupported=[],
        )

    if cid == "adonis-campaign":
        return base(
            c,
            hostedCreditsOnInstall=12,
            onTurnBegin={
                "op": "do",
                "action": {"kind": "take_hosted_credits", "amount": 3},
            },
            unsupported=[],
        )

    # --- v1.62.0 C-slice: existing IR only ---

    if cid == "demara":
        card = breaker_card(
            c,
            "barrier",
            1,
            2,
            2,
            3,
            break_max=2,
            unsupported=[],
        )
        card["paidAbilities"] = list(card.get("paidAbilities") or []) + [
            {
                "id": "demara-bypass",
                "label": "Trash Demara: bypass encountered barrier",
                "clickCost": 0,
                "creditCost": 0,
                "cost": {"trashSelf": True},
                "windows": ["encounter_paw"],
                "requireEncounterSubtype": "barrier",
                "effect": {
                    "op": "do",
                    "action": {
                        "kind": "bypass_current_ice",
                        "requireSubtype": "barrier",
                    },
                },
            }
        ]
        return card

    if cid == "himitsu-bako":
        return base(
            c,
            paidAbilities=[
                {
                    "id": "himitsu-bako-hq",
                    "label": "1¢: Add Himitsu-Bako to HQ",
                    "clickCost": 0,
                    "creditCost": 1,
                    "cost": {"credits": 1},
                    "windows": ["corp_action_paw", "encounter_paw"],
                    "effect": {
                        "op": "do",
                        "action": {"kind": "return_source_to_hq"},
                    },
                }
            ],
            subroutines=[
                {
                    "id": "himitsu-bako-etr",
                    "text": "End the run.",
                    "effect": etr(),
                }
            ],
            unsupported=[],
        )

    if cid == "marked-accounts":
        return base(
            c,
            onTurnBegin={
                "op": "do",
                "action": {"kind": "take_hosted_credits", "amount": 1},
            },
            paidAbilities=[
                {
                    "id": "marked-accounts-load",
                    "label": "[click]: Place 3¢ on Marked Accounts",
                    "clickCost": 1,
                    "creditCost": 0,
                    "cost": {"clicks": 1},
                    "windows": ["corp_action_paw"],
                    "effect": {
                        "op": "do",
                        "action": {"kind": "place_hosted_credits", "amount": 3},
                    },
                }
            ],
            unsupported=[],
        )

    if cid == "modded":
        return base(
            c,
            onPlay={
                "op": "do",
                "action": {
                    "kind": "install_from_grip_discount",
                    "types": ["program", "hardware"],
                    "discount": 3,
                },
            },
            unsupported=[],
        )

    if cid == "chaos-theory-wunderkind":
        return base(c, muBonus=1, unsupported=[])

    # --- v1.63.0 D-slice: existing IR only ---

    if cid == "hunter":
        return base(
            c,
            subroutines=[
                {
                    "id": "hunter-trace-tag",
                    "text": "Trace[3]. If successful, give the Runner 1 tag.",
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "trace",
                            "strength": 3,
                            "onSuccess": {
                                "op": "do",
                                "action": {
                                    "kind": "give_tags",
                                    "amount": 1,
                                },
                            },
                        },
                    },
                }
            ],
            unsupported=[],
        )

    if cid == "caduceus":
        return base(
            c,
            subroutines=[
                {
                    "id": "caduceus-trace-gain",
                    "text": "Trace[3]. If successful, the Corp gains 3[credit].",
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "trace",
                            "strength": 3,
                            "onSuccess": gain("corp", 3),
                        },
                    },
                },
                {
                    "id": "caduceus-trace-etr",
                    "text": "Trace[2]. If successful, end the run.",
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "trace",
                            "strength": 2,
                            "onSuccess": etr(),
                        },
                    },
                },
            ],
            unsupported=[],
        )

    if cid == "yagura":
        return base(
            c,
            subroutines=[
                {
                    "id": "yagura-look",
                    "text": "Look at the top card of R&D. You may add that card to the bottom of R&D.",
                    "effect": {
                        "op": "do",
                        "action": {"kind": "look_top_rd_may_bottom"},
                    },
                },
                {
                    "id": "yagura-net",
                    "text": "Do 1 net damage.",
                    "effect": net(1),
                },
            ],
            unsupported=[],
        )

    if cid == "viktor-1-0":
        return base(
            c,
            subroutines=[
                {
                    "id": "viktor-1-0-core",
                    "text": "Do 1 core damage.",
                    "effect": {
                        "op": "do",
                        "action": {"kind": "core_damage", "amount": 1},
                    },
                },
                {
                    "id": "viktor-1-0-etr",
                    "text": "End the run.",
                    "effect": etr(),
                },
            ],
            unsupported=[],
        )

    if cid == "special-order":
        return base(
            c,
            onPlay={
                "op": "do",
                "action": {"kind": "search_stack_icebreaker"},
            },
            unsupported=[],
        )

    # --- v1.64.0 E-slice: existing IR only ---

    if cid == "heimdall-1-0":
        return base(
            c,
            subroutines=[
                {
                    "id": "heimdall-1-0-core",
                    "text": "Do 1 core damage.",
                    "effect": {
                        "op": "do",
                        "action": {"kind": "core_damage", "amount": 1},
                    },
                },
                {
                    "id": "heimdall-1-0-etr-1",
                    "text": "End the run.",
                    "effect": etr(),
                },
                {
                    "id": "heimdall-1-0-etr-2",
                    "text": "End the run.",
                    "effect": etr(),
                },
            ],
            unsupported=[],
        )

    if cid == "ichi-1-0":
        return base(
            c,
            subroutines=[
                {
                    "id": "ichi-1-0-trash-1",
                    "text": "Trash 1 installed program.",
                    "effect": {
                        "op": "do",
                        "action": {"kind": "trash_program", "pick": "choose"},
                    },
                },
                {
                    "id": "ichi-1-0-trash-2",
                    "text": "Trash 1 installed program.",
                    "effect": {
                        "op": "do",
                        "action": {"kind": "trash_program", "pick": "choose"},
                    },
                },
                {
                    "id": "ichi-1-0-trace",
                    "text": "Trace[1]. If successful, do 1 core damage and give the Runner 1 tag.",
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "trace",
                            "strength": 1,
                            "onSuccess": seq(
                                {
                                    "op": "do",
                                    "action": {
                                        "kind": "core_damage",
                                        "amount": 1,
                                    },
                                },
                                {
                                    "op": "do",
                                    "action": {
                                        "kind": "give_tags",
                                        "amount": 1,
                                    },
                                },
                            ),
                        },
                    },
                },
            ],
            unsupported=[],
        )

    if cid == "sea-source":
        return base(
            c,
            playRequiresSuccessfulRunLastTurn=True,
            onPlay={
                "op": "do",
                "action": {
                    "kind": "trace",
                    "strength": 3,
                    "onSuccess": {
                        "op": "do",
                        "action": {"kind": "give_tags", "amount": 1},
                    },
                },
            },
            unsupported=[],
        )

    if cid == "product-placement":
        return base(
            c,
            mustRevealWhenAccessedFromRd=True,
            skipOnAccessFromArchives=True,
            onAccess=gain("corp", 2),
            unsupported=[],
        )

    if cid == "notoriety":
        return base(
            c,
            playRequiresSuccessfulAllCentralsThisTurn=True,
            onPlay={
                "op": "do",
                "action": {
                    "kind": "add_to_runner_score_as_agenda",
                    "agendaPoints": 1,
                },
            },
            unsupported=[],
        )

    # --- v1.65.0 F-slice: existing IR only ---

    if cid == "gabriel-santiago-consummate-professional":
        return base(
            c,
            onFirstSuccessfulHqRunThisTurn=gain("runner", 2),
            unsupported=[],
        )

    if cid == "quest-completed":
        return base(
            c,
            playRequiresSuccessfulAllCentralsThisTurn=True,
            onPlay={
                "op": "do",
                "action": {"kind": "access_one_root_other_server"},
            },
            unsupported=[],
        )

    if cid == "explode-a-palooza":
        return base(
            c,
            mustRevealWhenAccessedFromRd=True,
            onAccess={
                "op": "choose",
                "chooser": "corp",
                "options": [
                    {
                        "id": "gain",
                        "label": "Gain 5¢",
                        "effect": gain("corp", 5),
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

    if cid == "lamprey":
        return base(
            c,
            trashOnVirusPurge=True,
            onSuccessfulRun={
                "op": "if",
                "cond": {"op": "attacking_hq"},
                "then": {
                    "op": "do",
                    "action": {
                        "kind": "lose_credits",
                        "side": "corp",
                        "amount": 1,
                    },
                },
            },
            unsupported=[],
        )

    if cid == "ghost-branch":
        return base(
            c,
            canAdvance=True,
            onAccess={
                "op": "choose",
                "chooser": "corp",
                "options": [
                    {
                        "id": "tags",
                        "label": "Give 1 tag per advancement",
                        "effect": {
                            "op": "do",
                            "action": {
                                "kind": "give_tags",
                                "amount": 0,
                                "tally": {
                                    "count": "source_advancement_tokens",
                                    "per": 1,
                                    "side": "source",
                                },
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
            unsupported=[],
        )

    # --- v1.66.0 G-slice: new Effect IR leaves (fail-closed engine pair) ---

    if cid == "hq-interface":
        return base(c, bonusAccessOnHqBreach=1, unsupported=[])

    if cid == "r-d-interface":
        return base(c, bonusAccessOnRdBreach=1, unsupported=[])

    if cid == "closed-accounts":
        return base(
            c,
            playRequiresTagged=True,
            onPlay={
                "op": "do",
                "action": {"kind": "lose_all_credits", "side": "runner"},
            },
            unsupported=[],
        )

    if cid == "flare":
        return base(
            c,
            subroutines=[
                {
                    "id": "flare-trace",
                    "text": (
                        "Trace[6]. If successful, trash 1 piece of hardware, "
                        "do 2 meat damage (cannot be prevented), and end the run."
                    ),
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "trace",
                            "strength": 6,
                            "onSuccess": seq(
                                {
                                    "op": "do",
                                    "action": {
                                        "kind": "trash_hardware",
                                        "pick": "choose",
                                    },
                                },
                                {
                                    "op": "do",
                                    "action": {
                                        "kind": "meat_damage",
                                        "amount": 2,
                                        "cannotPrevent": True,
                                    },
                                },
                                etr(),
                            ),
                        },
                    },
                }
            ],
            unsupported=[],
        )

    if cid == "leela-patel-trained-pragmatist":
        return base(
            c,
            onAgendaScoredOrStolen={
                "op": "do",
                "action": {
                    "kind": "return_installed_corp_to_hq",
                    "pick": "choose",
                    "unrezzedOnly": True,
                },
            },
            unsupported=[],
        )

    # --- v1.67.0 H-slice: new Effect IR leaves (fail-closed engine pair) ---

    if cid == "priority-requisition":
        return base(
            c,
            onScore={
                "op": "do",
                "action": {"kind": "rez_ice_ignoring_costs"},
            },
            unsupported=[],
        )

    if cid == "neural-emp":
        return base(
            c,
            playRequiresRunnerMadeRunLastTurn=True,
            onPlay=net(1),
            unsupported=[],
        )

    if cid == "haas-bioroid-stronger-together":
        return base(
            c,
            iceStrengthBonusForSubtype={"subtype": "bioroid", "bonus": 1},
            unsupported=[],
        )

    if cid == "nbn-making-news":
        return base(
            c,
            recurringCreditsMax=2,
            recurringSpendFor=["trace"],
            unsupported=[],
        )

    if cid == "philotic-entanglement":
        return base(
            c,
            deckLimit=1,
            onScore={
                "op": "do",
                "action": {
                    "kind": "net_damage",
                    "amount": 0,
                    "tally": {
                        "count": "runner_score",
                        "per": 1,
                        "side": "runner",
                    },
                },
            },
            unsupported=[],
        )

    # --- v1.68.0 I-slice: new Effect IR leaves (fail-closed engine pair) ---

    if cid == "john-masanori":
        return base(
            c,
            onFirstSuccessfulRunThisTurn=draw("runner", 1),
            onFirstUnsuccessfulRunThisTurn={
                "op": "do",
                "action": {"kind": "give_tags", "amount": 1},
            },
            unsupported=[],
        )

    if cid == "spark-agency-worldswide-reach":
        return base(
            c,
            loseCreditsOnFirstAdvertisementRezThisTurn=1,
            unsupported=[],
        )

    if cid == "paper-trail":
        return base(
            c,
            onScore={
                "op": "do",
                "action": {
                    "kind": "trace",
                    "strength": 6,
                    "onSuccess": {
                        "op": "do",
                        "action": {
                            "kind": "trash_installed_resources_with_any_subtype",
                            "subtypes": ["connection", "job"],
                        },
                    },
                },
            },
            unsupported=[],
        )

    if cid == "data-dealer":
        return base(
            c,
            paidAbilities=[
                {
                    "id": "data-dealer-forfeit",
                    "label": "Forfeit 1 agenda: Gain 9¢",
                    "clickCost": 1,
                    "creditCost": 0,
                    "cost": {"clicks": 1, "forfeitAgenda": True},
                    "windows": ["runner_action_paw"],
                    "effect": gain("runner", 9),
                }
            ],
            unsupported=[],
        )

    if cid == "cyberfeeder":
        return base(
            c,
            recurringCreditsMax=1,
            recurringSpendFor=["use_program", "install_virus"],
            unsupported=[],
        )

    # --- v1.69.0 J-slice: new Effect IR leaves (fail-closed engine pair) ---

    if cid == "run-amok":
        return base(
            c,
            runEvent={
                "servers": "any",
                "onRunEnd": {
                    "op": "do",
                    "action": {
                        "kind": "trash_ice_rezzed_this_run",
                        "pick": "choose",
                    },
                },
            },
            unsupported=[],
        )

    if cid == "tsurugi":
        return base(
            c,
            subroutines=[
                {
                    "id": "tsurugi-etr-unless-pay",
                    "text": "End the run unless the Corp pays 1¢.",
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "unless",
                            "payer": "corp",
                            "cost": {
                                "op": "do",
                                "action": {
                                    "kind": "lose_credits",
                                    "side": "corp",
                                    "amount": 1,
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
                    "id": "tsurugi-net-1",
                    "text": "Do 1 net damage.",
                    "effect": net(1),
                },
                {
                    "id": "tsurugi-net-2",
                    "text": "Do 1 net damage.",
                    "effect": net(1),
                },
                {
                    "id": "tsurugi-net-3",
                    "text": "Do 1 net damage.",
                    "effect": net(1),
                },
            ],
            unsupported=[],
        )

    if cid == "elizabeth-mills":
        return base(
            c,
            onRez={
                "op": "do",
                "action": {"kind": "remove_bad_publicity", "amount": 1},
            },
            paidAbilities=[
                {
                    "id": "elizabeth-mills-trash-location",
                    "label": "Trash: Trash 1 location resource. Take 1 bad publicity.",
                    "clickCost": 1,
                    "creditCost": 0,
                    "cost": {"clicks": 1, "trashSelf": True},
                    "windows": ["corp_action_paw"],
                    "effect": seq(
                        {
                            "op": "do",
                            "action": {
                                "kind": "trash_installed_resource_with_subtype",
                                "subtype": "location",
                                "pick": "choose",
                            },
                        },
                        {
                            "op": "do",
                            "action": {
                                "kind": "give_bad_publicity",
                                "amount": 1,
                            },
                        },
                    ),
                }
            ],
            unsupported=[],
        )

    if cid == "kati-jones":
        return base(
            c,
            paidAbilitiesOncePerTurn=True,
            paidAbilities=[
                {
                    "id": "kati-jones-load",
                    "label": "[click]: Place 3¢ on Kati Jones",
                    "clickCost": 1,
                    "creditCost": 0,
                    "cost": {"clicks": 1},
                    "windows": ["runner_action_paw"],
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "place_hosted_credits",
                            "amount": 3,
                        },
                    },
                },
                {
                    "id": "kati-jones-take",
                    "label": "[click]: Take all credits from Kati Jones",
                    "clickCost": 1,
                    "creditCost": 0,
                    "cost": {"clicks": 1},
                    "windows": ["runner_action_paw"],
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "take_hosted_credits",
                            "amount": 999,
                        },
                    },
                },
            ],
            unsupported=[],
        )

    if cid == "ice-analyzer":
        return base(
            c,
            hostedCreditsOnAnyIceRez=1,
            hostedCreditsSpendFor=["install"],
            hostedCreditsSpendForInstallTypes=["program"],
            unsupported=[],
        )

    # --- v1.70.0 K-slice: reuse + new Effect IR leaves (fail-closed engine pair) ---

    if cid == "faerie":
        return breaker_card(
            c,
            "sentry",
            2,
            0,
            1,
            1,
            trashAfterBreakingThisRun=True,
            unsupported=[],
        )

    if cid == "datasucker":
        return base(
            c,
            onSuccessfulRun={
                "op": "if",
                "cond": {"op": "attacking_central"},
                "then": {
                    "op": "do",
                    "action": {"kind": "add_virus_counter", "amount": 1},
                },
            },
            paidAbilities=[
                {
                    "id": "datasucker-weaken",
                    "label": "Spend virus: ice −1 strength",
                    "clickCost": 0,
                    "creditCost": 0,
                    "cost": {"virusCounters": 1},
                    "windows": ["encounter_paw"],
                    "effect": {
                        "op": "do",
                        "action": {"kind": "weaken_ice", "amount": 1},
                    },
                }
            ],
            unsupported=[],
        )

    if cid == "stimhack":
        return base(
            c,
            runEvent={
                "servers": "any",
                "placeEventCredits": 9,
                "onRunEnd": {
                    "op": "do",
                    "action": {
                        "kind": "core_damage",
                        "amount": 1,
                        "cannotPrevent": True,
                    },
                },
            },
            unsupported=[],
        )

    if cid == "turing":
        return base(
            c,
            strengthBonusProtectingRemote=3,
            cannotBreakWithAi=True,
            subroutines=[
                {
                    "id": "turing-etr-unless-clicks",
                    "text": "End the run unless the Runner spends [click][click][click].",
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "unless",
                            "payer": "runner",
                            "cost": {
                                "op": "do",
                                "action": {
                                    "kind": "lose_clicks",
                                    "side": "runner",
                                    "amount": 3,
                                },
                            },
                            "instruction": {
                                "op": "do",
                                "action": {"kind": "end_the_run"},
                            },
                        },
                    },
                }
            ],
            unsupported=[],
        )

    if cid == "spear-phishing":
        return base(
            c,
            runEvent={
                "servers": "any",
                "bypassInnermostEncounter": True,
            },
            unsupported=[],
        )

    # --- v1.71.0 L-slice: reuse + new Effect IR leaves (fail-closed engine pair) ---

    if cid == "fetal-ai":
        return base(
            c,
            mustRevealWhenAccessedFromRd=True,
            skipOnAccessFromArchives=True,
            stealAdditionalCredits=2,
            onAccess={
                "op": "do",
                "action": {"kind": "net_damage", "amount": 2},
            },
            unsupported=[],
        )

    if cid == "data-raven":
        return base(
            c,
            onEncounter={
                "op": "do",
                "action": {
                    "kind": "unless",
                    "payer": "runner",
                    "cost": {
                        "op": "do",
                        "action": {"kind": "give_tags", "amount": 1},
                    },
                    "instruction": {
                        "op": "do",
                        "action": {"kind": "end_the_run"},
                    },
                },
            },
            paidAbilities=[
                {
                    "id": "data-raven-tag",
                    "label": "Hosted power: Give the Runner 1 tag",
                    "clickCost": 0,
                    "creditCost": 0,
                    "cost": {"powerCounters": 1},
                    "windows": [
                        "corp_action_paw",
                        "approach_paw",
                        "encounter_paw",
                        "approach_server_paw",
                    ],
                    "effect": {
                        "op": "do",
                        "action": {"kind": "give_tags", "amount": 1},
                    },
                }
            ],
            subroutines=[
                {
                    "id": "data-raven-trace",
                    "text": "Trace[3]. If successful, place 1 power counter on this ice.",
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "trace",
                            "strength": 3,
                            "onSuccess": {
                                "op": "do",
                                "action": {
                                    "kind": "add_power_counter",
                                    "amount": 1,
                                },
                            },
                        },
                    },
                }
            ],
            unsupported=[],
        )

    if cid == "red-herrings":
        return base(
            c,
            persistent=True,
            stealAdditionalCreditsFromProtectingServer=5,
            unsupported=[],
        )

    if cid == "public-support":
        return base(
            c,
            powerCountersOnRez=3,
            scoreWhenPowerEmpty={"agendaPoints": 1},
            onTurnBegin={
                "op": "do",
                "action": {"kind": "remove_power_counter", "amount": 1},
            },
            unsupported=[],
        )

    if cid == "project-junebug":
        return base(
            c,
            canAdvance=True,
            onAccess={
                "op": "do",
                "action": {
                    "kind": "may_pay_credits_for_net_damage_per_advancement",
                    "amount": 1,
                    "per": 2,
                },
            },
            unsupported=[],
        )

    # --- v1.72.0 M-slice: reuse + new Effect IR leaves (fail-closed engine pair) ---

    if cid == "paragon":
        return base(
            c,
            muBonus=1,
            onSuccessfulRunOncePerTurn=True,
            onSuccessfulRun={
                "op": "choose",
                "chooser": "runner",
                "options": [
                    {
                        "id": "paragon-yes",
                        "label": "Gain 1¢ and look at the top of your stack",
                        "effect": seq(
                            gain("runner", 1),
                            {
                                "op": "do",
                                "action": {
                                    "kind": "look_top_n_stack_may_bottom_one",
                                    "n": 1,
                                },
                            },
                        ),
                    },
                    {
                        "id": "paragon-decline",
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
            unsupported=[],
        )

    if cid == "aggressive-secretary":
        return base(
            c,
            canAdvance=True,
            onAccess={
                "op": "do",
                "action": {
                    "kind": "may_pay_credits_for_trash_programs_per_advancement",
                    "amount": 2,
                },
            },
            unsupported=[],
        )

    if cid == "successful-field-test":
        return base(
            c,
            onScore={
                "op": "do",
                "action": {
                    "kind": "install_any_number_from_hq_ignore_costs",
                },
            },
            unsupported=[],
        )

    if cid == "hostage":
        return base(
            c,
            playAdditionalClick=True,
            onPlay={
                "op": "do",
                "action": {
                    "kind": "search_stack_subtype_may_install",
                    "subtype": "connection",
                },
            },
            unsupported=[],
        )

    if cid == "tinkering":
        return base(
            c,
            onPlay={
                "op": "do",
                "action": {
                    "kind": "grant_chosen_ice_subtypes_until_end_of_turn",
                    "subtypes": ["sentry", "code gate", "barrier"],
                },
            },
            unsupported=[],
        )

    # --- v1.73.0 N-slice: reuse + new Effect IR / continuous fields ---

    if cid == "contract-killer":
        return base(
            c,
            canAdvance=True,
            paidAbilities=[
                {
                    "id": "contract-killer-fire",
                    "label": "Trash Contract Killer: trash a connection or do 2 meat damage (needs 2 advancements)",
                    "clickCost": 1,
                    "creditCost": 0,
                    "cost": {"clicks": 1, "trashSelf": True},
                    "windows": ["corp_action_paw"],
                    "requiresAdvancements": 2,
                    "effect": {
                        "op": "choose",
                        "chooser": "corp",
                        "options": [
                            {
                                "id": "trash-connection",
                                "label": "Trash a connection",
                                "effect": {
                                    "op": "do",
                                    "action": {
                                        "kind": "trash_installed_resource_with_subtype",
                                        "subtype": "connection",
                                        "pick": "choose",
                                    },
                                },
                            },
                            {
                                "id": "meat-2",
                                "label": "Do 2 meat damage",
                                "effect": {
                                    "op": "do",
                                    "action": {
                                        "kind": "meat_damage",
                                        "amount": 2,
                                    },
                                },
                            },
                        ],
                    },
                }
            ],
            unsupported=[],
        )

    # Queen's Gambit: place 0..max adv on 1 unrezzed remote-root card; gain
    # creditsPer each; that card cannot be accessed for the remainder of the turn.
    if cid == "queens-gambit":
        return base(
            c,
            playAdditionalClick=True,
            onPlay={
                "op": "do",
                "action": {
                    "kind": "place_up_to",
                    "max": 3,
                    "creditsPer": 2,
                },
            },
            unsupported=[],
        )

    if cid == "blue-sun-powering-the-future":
        return base(
            c,
            onTurnBegin={
                "op": "do",
                "action": {
                    "kind": "may_return_rezzed_to_hq_gain_rez_cost",
                },
            },
            unsupported=[],
        )

    if cid == "mason-bellamy":
        return base(
            c,
            loseClickOnProtectingIceEncounterEndIfBroke=True,
            unsupported=[],
        )

    if cid == "jinteki-replicating-perfection":
        return base(
            c,
            cannotRunRemotesUntilCentralRunThisTurn=True,
            unsupported=[],
        )

    # --- v1.74.0 O-slice set-complete: remaining 9 SC19-only ---

    if cid == "ash-2x3zb9cy":
        return base(
            c,
            onSuccessfulRun={
                "op": "do",
                "action": {
                    "kind": "trace",
                    "strength": 4,
                    "onSuccess": {
                        "op": "do",
                        "action": {
                            "kind": "restrict_run_access",
                            "mode": "only_source",
                            "cardIdsFromSource": True,
                        },
                    },
                },
            },
            unsupported=[],
        )

    if cid == "crypsis":
        return breaker_card(
            c,
            "*",
            0,
            1,
            pump_c=1,
            pump_s=1,
            paidAbilities=[
                {
                    "id": "crypsis-virus",
                    "label": "Place 1 virus counter",
                    "clickCost": 1,
                    "creditCost": 0,
                    "cost": {"clicks": 1},
                    "windows": ["runner_action_paw"],
                    "effect": {
                        "op": "do",
                        "action": {"kind": "add_virus_counter", "amount": 1},
                    },
                }
            ],
            removeVirusOrTrashOnEncounterEndIfBroke=True,
            unsupported=[],
        )

    if cid == "deus-x":
        return base(
            c,
            breaker={
                "breaksSubtype": "ap",
                "strength": 10,
                "breakCredits": 0,
                "breakMaxSubs": 99,
                "breakViaPaidAbilityOnly": True,
            },
            paidAbilities=[
                {
                    "id": "deus-x-break",
                    "label": "Trash Deus X: break any number of AP subroutines",
                    "clickCost": 0,
                    "creditCost": 0,
                    "cost": {"trashSelf": True},
                    "windows": ["encounter_paw"],
                    "requireEncounterSubtype": "ap",
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "break_encounter_subroutine",
                            "maxSubs": 99,
                            "requireSubtype": "ap",
                        },
                    },
                },
                {
                    "id": "deus-x-prevent-net",
                    "label": "Interrupt: trash Deus X — prevent any amount of net damage",
                    "clickCost": 0,
                    "creditCost": 0,
                    "cost": {"trashSelf": True},
                    "windows": ["damage_interrupt_paw"],
                    "requirePendingDamageTypes": ["net"],
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "prevent_pending_damage",
                            "amount": 99,
                        },
                    },
                },
            ],
            unsupported=[],
        )

    if cid == "bank-job":
        return base(
            c,
            hostedCreditsOnInstall=8,
            onSuccessfulRun={
                "op": "if",
                "cond": {"op": "attacking_remote"},
                "then": {
                    "op": "do",
                    "action": {"kind": "may_take_any_hosted_credits_skip_breach"},
                },
            },
            unsupported=[],
        )

    if cid == "seidr-laboratories-destiny-defined":
        return base(
            c,
            onFirstRunnerClickSpendOrLoseDuringRun={
                "op": "do",
                "action": {"kind": "may_add_archives_card_to_rd_top"},
            },
            unsupported=[],
        )

    if cid == "dinosaurus":
        return base(
            c,
            muBonus=1,
            maxHostedCards=1,
            hostIcebreakerStrengthBonus=2,
            hostNonAiIcebreaker=True,
            hostedIcebreakerMemoryDoesNotCount=True,
            unsupported=[],
        )

    if cid == "patchwork":
        return base(
            c,
            muBonus=1,
            playOrInstallDiscountByTrashingGripOncePerTurn=2,
            unsupported=[],
        )

    if cid == "sundew":
        return base(
            c,
            gainCreditsOnFirstRunnerClickSpendThisTurn=2,
            refundCreditsIfRunBeginsOnThisServerDuringClickAction=2,
            unsupported=[],
        )

    if cid == "oversight-ai":
        return base(
            c,
            onPlay={
                "op": "do",
                "action": {"kind": "rez_and_host"},
            },
            trashHostIfAllSubsBrokenThisEncounter=True,
            unsupported=[],
        )

    card = base(c)
    card["unsupported"] = [
        f"Full text not yet mapped to IR: {plain[:200]}"
    ]
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

    written: list[str] = []
    skipped: list[str] = []
    for c in pack:
        cid = slugify(c["title"])
        mapped = map_card(c)
        if mapped is None:
            skipped.append(cid)
            continue
        path = OUT / f"{cid}.json"
        path.write_text(json.dumps(mapped, indent=2, ensure_ascii=False) + "\n")
        written.append(cid)

    pool_ids = [slugify(c["title"]) for c in pack]
    clear_written = sum(
        1
        for cid in written
        if not json.loads((OUT / f"{cid}.json").read_text()).get("unsupported")
    )

    manifest = {
        "pack": WAVE,
        "nrdbPackCode": PACK,
        "count": EXPECTED,
        "written": len(written),
        "reprintSkipped": len(skipped),
        "status": "in-progress",
        "notes": (
            "System Core 2019 (sc19) kickoff v1.59.0. "
            f"Wrote {len(written)} files; skipped {len(skipped)} Gateway/SU21 reprints. "
            f"Kickoff clears among written: {clear_written}."
        ),
        "cards": pool_ids,
        "reprintIdsFromEarlierWaves": sorted(skipped),
        "kickoffClears": [
            "easy-mark",
            "beanstalk-royalties",
            "wall-of-static",
            "akamatsu-mem-chip",
            "spiderweb",
        ],
        "aSliceClears": [
            "neural-katana",
            "wall-of-thorns",
            "armitage-codebusting",
            "hadrians-wall",
            "ipo",
        ],
        "bSliceClears": [
            "battering-ram",
            "force-of-nature",
            "pipeline",
            "blue-level-clearance",
            "adonis-campaign",
        ],
        "cSliceClears": [
            "demara",
            "himitsu-bako",
            "marked-accounts",
            "modded",
            "chaos-theory-wunderkind",
        ],
        "dSliceClears": [
            "hunter",
            "caduceus",
            "yagura",
            "viktor-1-0",
            "special-order",
        ],
        "eSliceClears": [
            "heimdall-1-0",
            "ichi-1-0",
            "sea-source",
            "product-placement",
            "notoriety",
        ],
        "fSliceClears": [
            "gabriel-santiago-consummate-professional",
            "quest-completed",
            "explode-a-palooza",
            "lamprey",
            "ghost-branch",
        ],
        "gSliceClears": [
            "hq-interface",
            "r-d-interface",
            "closed-accounts",
            "flare",
            "leela-patel-trained-pragmatist",
        ],
        "hSliceClears": [
            "priority-requisition",
            "neural-emp",
            "haas-bioroid-stronger-together",
            "nbn-making-news",
            "philotic-entanglement",
        ],
        "iSliceClears": [
            "john-masanori",
            "spark-agency-worldswide-reach",
            "paper-trail",
            "data-dealer",
            "cyberfeeder",
        ],
        "jSliceClears": [
            "run-amok",
            "tsurugi",
            "elizabeth-mills",
            "kati-jones",
            "ice-analyzer",
        ],
        "kSliceClears": [
            "faerie",
            "datasucker",
            "stimhack",
            "turing",
            "spear-phishing",
        ],
        "lSliceClears": [
            "fetal-ai",
            "data-raven",
            "red-herrings",
            "public-support",
            "project-junebug",
        ],
        "mSliceClears": [
            "paragon",
            "aggressive-secretary",
            "successful-field-test",
            "hostage",
            "tinkering",
        ],
        "nSliceClears": [
            "contract-killer",
            "queens-gambit",
            "blue-sun-powering-the-future",
            "mason-bellamy",
            "jinteki-replicating-perfection",
        ],
        "oSliceClears": [
            "ash-2x3zb9cy",
            "crypsis",
            "deus-x",
            "bank-job",
            "seidr-laboratories-destiny-defined",
            "dinosaurus",
            "patchwork",
            "sundew",
            "oversight-ai",
        ],
    }
    (OUT / "_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"
    )

    print(f"Wrote {len(written)} cards to {OUT}")
    print(f"Skipped reprints/shared: {len(skipped)}")
    print(f"Among written: full={clear_written} partial={len(written) - clear_written}")
    print("POOL_IDS=" + json.dumps(pool_ids))


if __name__ == "__main__":
    main()
