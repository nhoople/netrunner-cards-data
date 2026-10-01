#!/usr/bin/env python3
"""Generate What Lies Ahead card JSON from pinned pack `wla`.

Catalog source: Null-Signal-Games/netrunner-cards-json (see data/nrdb-catalog-pin.json).
Fetch with: python3 scripts/nrdb_catalog.py fetch wla

First Genesis-cycle wave after FFG Core Set set-complete (floor v1.87.0).
Titles already clear under Gateway / SU21 / SC19 / Core (etc.) are treated as
reprints: skip emitting duplicate files; list their ids in pool.json.

Hand-mapped Effect IR only where existing primitives fully cover the card;
everything else lists honest unsupported notes — never invent IR.

Never kick Magnum Opus packs (`mo` / `mor`).

Usage: python3 scripts/generate-what-lies-ahead.py
"""
from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

from nrdb_catalog import load_pack_cards

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "what-lies-ahead"
WAVE = "what-lies-ahead"
PACK = "wla"
EXPECTED = 20

# Already clear under Gateway / SU21 / SC19 / Core.
REPRINTS = {
    "imp",
    "haas-bioroid-stronger-together",
    "ash-2x3zb9cy",
    "project-atlas",
    "caduceus",
}
# plascrete-carapace is authored under this wave (catalog home).


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


def core(n: int):
    return {"op": "do", "action": {"kind": "core_damage", "amount": n}}


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
                "label": (
                    f"Pump {c['title']} +{pump_s if pump_s is not None else 1} "
                    "strength"
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

    if cid == "whizzard-master-gamer":
        return base(
            c,
            recurringCreditsMax=3,
            recurringSpendFor=["trash"],
            unsupported=[],
        )

    if cid == "spinal-modem":
        return base(
            c,
            unique=True,
            muBonus=1,
            recurringCreditsMax=2,
            recurringSpendFor=["use_program"],
            onSuccessfulTraceDuringRun=core(1),
            unsupported=[],
        )

    if cid == "morning-star":
        return breaker_card(
            c,
            "barrier",
            strength=5,
            break_c=1,
            break_max=99,
            unsupported=[],
        )

    if cid == "cortez-chip":
        return base(
            c,
            paidAbilities=[
                {
                    "id": "cortez-chip-rez",
                    "label": (
                        "[trash]: Choose a piece of ice. +2¢ additional cost "
                        "to rez that ice until end of turn"
                    ),
                    "clickCost": 0,
                    "creditCost": 0,
                    "cost": {"trashSelf": True},
                    "windows": [
                        "runner_action_paw",
                        "approach_paw",
                        "encounter_paw",
                    ],
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "choose_ice_additional_rez_cost_this_turn",
                            "amount": 2,
                        },
                    },
                }
            ],
            unsupported=[],
        )

    if cid == "peacock":
        return breaker_card(
            c,
            "code gate",
            strength=2,
            break_c=2,
            break_max=1,
            pump_c=2,
            pump_s=3,
            unsupported=[],
        )

    if cid == "zu-13-key-master":
        return breaker_card(
            c,
            "code gate",
            strength=1,
            break_c=1,
            break_max=1,
            pump_c=1,
            pump_s=1,
            memoryCostZeroIfLinkGte=2,
            unsupported=[],
        )

    if cid == "the-helpful-ai":
        return base(
            c,
            unique=True,
            link=1,
            paidAbilities=[
                {
                    "id": "the-helpful-ai-boost",
                    "label": (
                        "[trash]: Choose an icebreaker. That icebreaker "
                        "has +2 strength until end of turn"
                    ),
                    "clickCost": 0,
                    "creditCost": 0,
                    "cost": {"trashSelf": True},
                    "windows": ["runner_action_paw", "encounter_paw"],
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "choose_icebreaker_gain_strength_this_turn",
                            "amount": 2,
                        },
                    },
                }
            ],
            unsupported=[],
        )

    if cid == "mandatory-upgrades":
        return base(c, allottedClicksBonus=1, unsupported=[])

    if cid == "janus-1-0":
        return base(
            c,
            subroutines=[
                {
                    "id": f"janus-1-0-core-{i}",
                    "text": "Do 1 core damage.",
                    "effect": core(1),
                }
                for i in range(1, 5)
            ],
            unsupported=[],
        )

    if cid == "braintrust":
        return base(
            c,
            onScore={
                "op": "do",
                "action": {
                    "kind": "add_agenda_counters_from_overadvance",
                    "past": 3,
                    "per": 2,
                },
            },
            iceRezCostReductionPerAgendaCounter=1,
            unsupported=[],
        )

    if cid == "snowflake":
        return base(
            c,
            subroutines=[
                {
                    "id": "snowflake-psi",
                    "text": (
                        "You and the Runner secretly spend 0¢, 1¢, or 2¢. "
                        "Reveal spent credits. End the run if you and the "
                        "Runner spent a different number of credits."
                    ),
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "play_psi_game",
                            "maxBid": 2,
                            "ifBidsDiffer": etr(),
                        },
                    },
                }
            ],
            unsupported=[],
        )

    if cid == "restructured-datapool":
        return base(
            c,
            paidAbilities=[
                {
                    "id": "restructured-datapool-trace",
                    "label": "[click]: Trace[2]. If successful, give the Runner 1 tag",
                    "clickCost": 1,
                    "creditCost": 0,
                    "cost": {"clicks": 1},
                    "windows": ["corp_action_paw"],
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "trace",
                            "strength": 2,
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

    if cid == "tmi":
        return base(
            c,
            onRez={
                "op": "do",
                "action": {
                    "kind": "trace",
                    "strength": 2,
                    "onSuccess": gain("corp", 0),
                    "onFailure": {
                        "op": "do",
                        "action": {"kind": "derez_source"},
                    },
                },
            },
            subroutines=[
                {
                    "id": "tmi-etr",
                    "text": "End the run.",
                    "effect": etr(),
                }
            ],
            unsupported=[],
        )

    if cid == "draco":
        return base(
            c,
            rezSpendCreditsForPowerCounters={"max": 99},
            strengthPerPowerCounter=True,
            subroutines=[
                {
                    "id": "draco-trace",
                    "text": (
                        "Trace[2]. If successful, give the Runner 1 tag "
                        "and end the run."
                    ),
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "trace",
                            "strength": 2,
                            "onSuccess": seq(
                                {
                                    "op": "do",
                                    "action": {
                                        "kind": "give_tags",
                                        "amount": 1,
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
    clear_written = [
        cid
        for cid in written
        if not json.loads((OUT / f"{cid}.json").read_text()).get("unsupported")
    ]
    partial_written = [cid for cid in written if cid not in clear_written]

    manifest = {
        "pack": WAVE,
        "nrdbPackCode": PACK,
        "count": EXPECTED,
        "written": len(written),
        "reprintSkipped": len(skipped),
        "status": "in-progress",
        "notes": (
            "What Lies Ahead (wla) Genesis kickoff from floor v1.87.0. "
            f"Wrote {len(written)} files; skipped {len(skipped)} reprints "
            f"(Gateway/SU21/SC19/Core). Full clears among written: "
            f"{len(clear_written)}; partial: {len(partial_written)}. "
            "Never kick mo/mor packs."
        ),
        "cards": pool_ids,
        "reprintIdsFromEarlierWaves": sorted(skipped),
        "kickoffClears": clear_written,
        "partialMapped": partial_written,
    }
    (OUT / "_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"
    )

    print(f"Wrote {len(written)} cards to {OUT}")
    print(f"Skipped reprints/shared: {len(skipped)}")
    print(
        f"Among written: full={len(clear_written)} "
        f"partial={len(partial_written)}"
    )
    print("CLEARS=" + json.dumps(clear_written))
    print("POOL_IDS=" + json.dumps(pool_ids))


if __name__ == "__main__":
    main()
