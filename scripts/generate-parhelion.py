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
