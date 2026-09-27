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
