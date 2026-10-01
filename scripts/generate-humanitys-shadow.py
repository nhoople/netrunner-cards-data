#!/usr/bin/env python3
"""Generate Humanity's Shadow card JSON from pinned pack `hs`.

Catalog source: Null-Signal-Games/netrunner-cards-json (see data/nsg-catalog-pin.json).
Fetch with: python3 scripts/nsg_catalog.py fetch hs

Fifth Genesis-cycle wave after A Study in Static set-complete (floor v1.91.0).
Titles already clear under earlier waves are treated as reprints: skip emitting
duplicate files; list their ids in pool.json.

Hand-mapped Effect IR only — empty unsupported for set-complete.

Usage: python3 scripts/generate-humanitys-shadow.py
"""
from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

from nsg_catalog import load_pack_cards

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "humanitys-shadow"
WAVE = "humanitys-shadow"
PACK = "hs"
EXPECTED = 20

# Already clear under Core / SC19 / SU21 / etc.
REPRINTS = {
    "xanadu",
    "networking",
    "hq-interface",
    "kati-jones",
    "hokusai-grid",
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


def draw(side: str, n: int):
    return {"op": "do", "action": {"kind": "draw", "side": side, "amount": n}}


def seq(*effects):
    return {"op": "seq", "effects": list(effects)}


def tags(n: int):
    return {"op": "do", "action": {"kind": "give_tags", "amount": n}}


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

    if cid == "surge":
        return base(
            c,
            playRequiresVirusCounterPlacedOnProgramThisTurn=True,
            onPlay={
                "op": "do",
                "action": {
                    "kind": "place_virus_on_program_that_received_virus_this_turn",
                    "amount": 2,
                },
            },
            unsupported=[],
        )

    if cid == "andromeda-dispossessed-ristie":
        return base(
            c,
            link=1,
            startingHandSize=9,
            unsupported=[],
        )

    if cid == "pheromones":
        return base(
            c,
            recurringCreditsMaxEqualsVirusCounters=True,
            recurringSpendFor=["run_hq"],
            onSuccessfulRun={
                "op": "if",
                "cond": {"op": "attacking_hq"},
                "then": {
                    "op": "do",
                    "action": {"kind": "add_virus_counter", "amount": 1},
                },
            },
            unsupported=[],
        )

    if cid == "quality-time":
        return base(c, onPlay=draw("runner", 5), unsupported=[])

    if cid == "replicator":
        return base(
            c,
            onHardwareInstall={
                "op": "do",
                "action": {
                    "kind": "may_search_stack_copy_of_last_installed_hardware_add_to_grip",
                },
            },
            unsupported=[],
        )

    if cid == "creeper":
        return base(
            c,
            breaker={
                "breaksSubtype": "sentry",
                "strength": 2,
                "breakCredits": 2,
                "breakMaxSubs": 1,
                "pumpCredits": 1,
                "pumpStrength": 1,
            },
            paidAbilities=[
                {
                    "id": "creeper-pump",
                    "label": "Pump Creeper +1 strength",
                    "clickCost": 0,
                    "creditCost": 1,
                    "cost": {"credits": 1},
                    "windows": ["encounter_paw"],
                    "effect": {
                        "op": "do",
                        "action": {"kind": "pump_strength", "amount": 1},
                    },
                }
            ],
            memoryCostZeroIfLinkGte=2,
            unsupported=[],
        )

    if cid == "kraken":
        return base(
            c,
            playRequiresAgendaStolenThisTurn=True,
            onPlay={
                "op": "do",
                "action": {
                    "kind": "choose_server_corp_trash_ice_protecting",
                },
            },
            unsupported=[],
        )

    if cid == "eve-campaign":
        return base(
            c,
            onRez={
                "op": "do",
                "action": {"kind": "place_hosted_credits", "amount": 16},
            },
            onTurnBegin={
                "op": "do",
                "action": {"kind": "take_hosted_credits", "amount": 2},
            },
            unsupported=[],
        )

    if cid == "rework":
        return base(
            c,
            onPlay={
                "op": "do",
                "action": {"kind": "shuffle_hq_to_rd", "amount": 1},
            },
            unsupported=[],
        )

    if cid == "whirlpool":
        return base(
            c,
            subroutines=[
                {
                    "id": "whirlpool-no-jack-trash",
                    "text": (
                        "The Runner cannot jack out for the remainder of "
                        "this run. Trash Whirlpool."
                    ),
                    "effect": seq(
                        {"op": "prevent", "forbid": "jack_out"},
                        {
                            "op": "do",
                            "action": {"kind": "trash_self"},
                        },
                    ),
                }
            ],
            unsupported=[],
        )

    if cid == "data-hound":
        return base(
            c,
            subroutines=[
                {
                    "id": "data-hound-trace",
                    "text": (
                        "Trace[2]. If successful, look at the top X cards of "
                        "the stack, where X is equal to the amount by which "
                        "your trace strength exceeded the Runner's link "
                        "strength. Trash 1 of those cards and arrange the "
                        "rest in any order."
                    ),
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "trace",
                            "strength": 2,
                            "onSuccess": {
                                "op": "do",
                                "action": {
                                    "kind": (
                                        "look_top_last_trace_excess_stack_"
                                        "trash_one_arrange_rest"
                                    ),
                                },
                            },
                        },
                    },
                }
            ],
            unsupported=[],
        )

    if cid == "bernice-mai":
        return base(
            c,
            unique=True,
            onSuccessfulRun={
                "op": "do",
                "action": {
                    "kind": "trace",
                    "strength": 5,
                    "onSuccess": tags(1),
                    "onFailure": {
                        "op": "do",
                        "action": {"kind": "trash_self"},
                    },
                },
            },
            unsupported=[],
        )

    if cid == "salvage":
        return base(
            c,
            canAdvance=True,
            canAdvanceOnlyWhenRezzed=True,
            gainsSubroutinesPerAdvancement={
                "subroutine": {
                    "id": "salvage-trace-tag",
                    "text": "Trace[2]. If successful, give the Runner 1 tag.",
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "trace",
                            "strength": 2,
                            "onSuccess": tags(1),
                        },
                    },
                }
            },
            subroutines=[],
            unsupported=[],
        )

    if cid == "simone-diego":
        return base(
            c,
            unique=True,
            recurringCreditsMax=2,
            recurringSpendFor=["advance_cards_this_server"],
            unsupported=[],
        )

    if cid == "foxfire":
        return base(
            c,
            onPlay={
                "op": "do",
                "action": {
                    "kind": "trace",
                    "strength": 7,
                    "onSuccess": {
                        "op": "do",
                        "action": {
                            "kind": "trash_virtual_resource_or_link_card",
                            "pick": "choose",
                        },
                    },
                },
            },
            unsupported=[],
        )

    card = base(c)
    text = strip_html(c.get("text") or "")
    plain = re.sub(r"\s+", " ", text).strip()
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
        "status": "supported",
        "notes": (
            "Humanity's Shadow (hs) Genesis set-complete from floor "
            f"v1.91.0 → v1.92.0. Wrote {len(written)} files; skipped "
            f"{len(skipped)} reprints. Full clears among written: "
            f"{len(clear_written)}; partial: {len(partial_written)}. "
            ""
        ),
        "cards": pool_ids,
        "reprintIdsFromEarlierWaves": sorted(skipped),
        "clears": clear_written,
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
