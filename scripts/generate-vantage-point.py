#!/usr/bin/env python3
"""Generate Vantage Point card JSON from pinned pack `vp`.

Catalog source: Null-Signal-Games/netrunner-cards-json (see data/nrdb-catalog-pin.json).
Fetch with: python3 scripts/nrdb_catalog.py fetch vp

Hand-mapped Effect IR only where existing primitives fully cover the card;
everything else lists honest unsupported notes — never invent IR.

Usage: python3 scripts/generate-vantage-point.py
"""
from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

from nrdb_catalog import load_pack_cards

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
            "op": "choose",
            "chooser": "runner",
            "options": [
                {
                    "id": "pay1",
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
                    "id": "etr",
                    "label": "End the run",
                    "effect": etr(),
                },
            ],
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

    # --- v1.14.0 B-slice: existing IR only ---

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
                    "id": "net",
                    "label": "Suffer 2 net damage",
                    "effect": net2,
                },
            ],
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

    # Fail closed — honest unsupported note for the remainder.
    # Corsair / Sell Out / Stowaway need IR not yet available (stealth credits,
    # trash-own-resource play cost, host-server successful-run gate).
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
    if full >= 8:
        manifest["notes"] = (
            "Null Signal Vantage Point (NRDB pack vp) — next constructed set after "
            "Elevation. Fail-closed IR; "
            f"{full} cards fully mapped, {partial} with unsupported notes "
            "(wave v1.14.0 B-slice)."
        )
        manifest["status"] = "in-progress"
    (OUT / "_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"
    )

    print(f"Wrote {len(written)} cards to {OUT}")
    print(f"Among written: full={full} partial={partial}")
    print("POOL_IDS=" + json.dumps(written))


if __name__ == "__main__":
    main()
