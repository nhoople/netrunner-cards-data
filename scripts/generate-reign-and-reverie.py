#!/usr/bin/env python3
"""Generate Reign and Reverie card JSON from pinned pack `rar`.

Catalog source: Null-Signal-Games/netrunner-cards-json (see data/nsg-catalog-pin.json).
Fetch with: python3 scripts/nsg_catalog.py fetch rar

Reign and Reverie is the next legacy-backwards wave after System Core 2019.
Titles already clear under SC19 / Gateway / SU21 are treated as reprints:
skip emitting duplicate files; list their ids in pool.json.

Hand-mapped Effect IR only where existing primitives fully cover the card;
everything else lists honest unsupported notes — never invent IR.

Usage: python3 scripts/generate-reign-and-reverie.py
"""
from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

from nsg_catalog import load_pack_cards

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "reign-and-reverie"
WAVE = "reign-and-reverie"
PACK = "rar"
EXPECTED = 58

# Already clear under system-core-2019 (and earlier). Do not emit duplicates.
REPRINTS = {
    "patchwork",
    "paragon",
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


def gain(side: str, n: int):
    return {"op": "do", "action": {"kind": "gain_credits", "side": side, "amount": n}}


def draw(side: str, n: int):
    return {"op": "do", "action": {"kind": "draw", "side": side, "amount": n}}


def seq(*effects):
    return {"op": "seq", "effects": list(effects)}


def decline(side: str):
    return {
        "id": "decline",
        "label": "Decline",
        "effect": gain(side, 0),
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

    # --- v1.75.0 kickoff: existing IR only ---

    if cid == "fly-on-the-wall":
        return base(
            c,
            onScore={
                "op": "do",
                "action": {"kind": "give_tags", "amount": 1},
            },
            unsupported=[],
        )

    if cid == "hyperloop-extension":
        return base(
            c,
            onAgendaScoredOrStolen=gain("corp", 3),
            unsupported=[],
        )

    if cid == "hot-pursuit":
        return base(
            c,
            runEvent={
                "servers": "hq",
                "onSuccessfulRun": seq(
                    gain("runner", 9),
                    {"op": "do", "action": {"kind": "give_tags", "amount": 1}},
                ),
            },
            unsupported=[],
        )

    if cid == "kyuban":
        return base(
            c,
            installOnIce=True,
            onPassHost=gain("runner", 2),
            unsupported=[],
        )

    if cid == "bankroll":
        return base(
            c,
            onSuccessfulRun={
                "op": "choose",
                "chooser": "runner",
                "options": [
                    {
                        "id": "place",
                        "label": "Place 1¢ on Bankroll",
                        "effect": {
                            "op": "do",
                            "action": {
                                "kind": "place_hosted_credits",
                                "amount": 1,
                            },
                        },
                    },
                    decline("runner"),
                ],
            },
            paidAbilities=[
                {
                    "id": "bankroll-take",
                    "label": "Trash Bankroll: take all hosted credits",
                    "clickCost": 0,
                    "creditCost": 0,
                    "cost": {"trashSelf": True},
                    "windows": ["runner_action_paw"],
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "take_hosted_credits",
                            "amount": 99,
                        },
                    },
                }
            ],
            unsupported=[],
        )

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
            "Reign and Reverie (rar) kickoff v1.75.0. "
            f"Wrote {len(written)} files; skipped {len(skipped)} SC19 reprints. "
            f"Kickoff clears among written: {clear_written}."
        ),
        "cards": pool_ids,
        "reprintIdsFromEarlierWaves": sorted(skipped),
        "kickoffClears": [
            "fly-on-the-wall",
            "hyperloop-extension",
            "hot-pursuit",
            "kyuban",
            "bankroll",
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
