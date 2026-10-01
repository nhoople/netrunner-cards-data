#!/usr/bin/env python3
"""Generate A Study in Static card JSON from pinned pack `asis`.

Catalog source: Null-Signal-Games/netrunner-cards-json (see data/nsg-catalog-pin.json).
Fetch with: python3 scripts/nsg_catalog.py fetch asis

Fourth Genesis-cycle wave after Cyber Exodus set-complete (floor v1.90.0).
Titles already clear under earlier waves are treated as reprints: skip emitting
duplicate files; list their ids in pool.json.

Hand-mapped Effect IR only — empty unsupported for set-complete.

Usage: python3 scripts/generate-a-study-in-static.py
"""
from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

from nsg_catalog import load_pack_cards

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "a-study-in-static"
WAVE = "a-study-in-static"
PACK = "asis"
EXPECTED = 20

# Already clear under Core / SC19 / SU21 / Uprising / etc.
REPRINTS = {
    "force-of-nature",
    "scrubber",
    "deus-x",
    "oversight-ai",
    "false-lead",
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


def seq(*effects):
    return {"op": "seq", "effects": list(effects)}


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

    if cid == "disrupter":
        return base(
            c,
            paidAbilities=[
                {
                    "id": "disrupter-trace",
                    "label": (
                        "[interrupt] → [trash]: Reduce base trace strength to 0"
                    ),
                    "clickCost": 0,
                    "creditCost": 0,
                    "cost": {"trashSelf": True},
                    "windows": ["trace_interrupt_paw"],
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "set_trace_base_strength",
                            "amount": 0,
                        },
                    },
                }
            ],
            unsupported=[],
        )

    if cid == "doppelganger":
        return base(
            c,
            unique=True,
            muBonus=1,
            onSuccessfulRunEndOncePerTurn={
                "op": "do",
                "action": {"kind": "may_start_run", "servers": "any"},
            },
            unsupported=[],
        )

    if cid == "crescentus":
        return base(
            c,
            paidAbilities=[
                {
                    "id": "crescentus-derez",
                    "label": (
                        "[trash]: Derez ice fully broken this encounter"
                    ),
                    "clickCost": 0,
                    "creditCost": 0,
                    "cost": {"trashSelf": True},
                    "windows": ["encounter_paw"],
                    "requireFullyBrokenThisEncounter": True,
                    "effect": {
                        "op": "do",
                        "action": {"kind": "derez_encounter_ice"},
                    },
                }
            ],
            unsupported=[],
        )

    if cid == "all-nighter":
        return base(
            c,
            paidAbilities=[
                {
                    "id": "all-nighter-clicks",
                    "label": "[click], [trash]: Gain [click][click]",
                    "clickCost": 1,
                    "creditCost": 0,
                    "cost": {"clicks": 1, "trashSelf": True},
                    "windows": ["runner_action_paw"],
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "gain_clicks",
                            "side": "runner",
                            "amount": 2,
                        },
                    },
                }
            ],
            unsupported=[],
        )

    if cid == "inside-man":
        return base(
            c,
            recurringCreditsMax=2,
            recurringSpendFor=["install_hardware"],
            unsupported=[],
        )

    if cid == "underworld-contact":
        return base(
            c,
            onTurnBegin={
                "op": "if",
                "cond": {"op": "link_gte", "amount": 2},
                "then": gain("runner", 1),
            },
            unsupported=[],
        )

    if cid == "green-level-clearance":
        return base(
            c,
            onPlay=seq(gain("corp", 3), {
                "op": "do",
                "action": {"kind": "draw", "side": "corp", "amount": 1},
            }),
            unsupported=[],
        )

    if cid == "hourglass":
        lose_click = {
            "id": "hourglass-lose-click",
            "text": "The Runner loses [click], if able.",
            "effect": {
                "op": "do",
                "action": {
                    "kind": "lose_clicks",
                    "side": "runner",
                    "amount": 1,
                },
            },
        }
        return base(
            c,
            subroutines=[
                {**lose_click, "id": "hourglass-lose-click-1"},
                {**lose_click, "id": "hourglass-lose-click-2"},
                {**lose_click, "id": "hourglass-lose-click-3"},
            ],
            unsupported=[],
        )

    if cid == "dedicated-server":
        return base(
            c,
            recurringCreditsMax=2,
            recurringSpendFor=["rez_ice"],
            unsupported=[],
        )

    if cid == "bullfrog":
        return base(
            c,
            subroutines=[
                {
                    "id": "bullfrog-psi",
                    "text": (
                        "You and the Runner secretly spend 0¢, 1¢ or 2¢. "
                        "Reveal spent credits. If you and the Runner spent a "
                        "different number of credits and this ice is installed, "
                        "move this ice to the outermost position protecting "
                        "another server. (The run continues from this new "
                        "position.)"
                    ),
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "play_psi_game",
                            "maxBid": 2,
                            "ifBidsDiffer": {
                                "op": "do",
                                "action": {
                                    "kind": (
                                        "move_source_ice_to_outermost_"
                                        "another_server_continue_run"
                                    ),
                                },
                            },
                        },
                    },
                }
            ],
            unsupported=[],
        )

    if cid == "uroboros":
        return base(
            c,
            subroutines=[
                {
                    "id": "uroboros-trace-no-run",
                    "text": (
                        "Trace[4]. If successful, the Runner cannot make "
                        "another run this turn."
                    ),
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "trace",
                            "strength": 4,
                            "onSuccess": {
                                "op": "do",
                                "action": {
                                    "kind": "forbid_runner_runs_this_turn",
                                },
                            },
                        },
                    },
                },
                {
                    "id": "uroboros-trace-etr",
                    "text": "Trace[4]. If successful, end the run.",
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "trace",
                            "strength": 4,
                            "onSuccess": etr(),
                        },
                    },
                },
            ],
            unsupported=[],
        )

    if cid == "net-police":
        return base(
            c,
            recurringCreditsMaxEqualsRunnerLink=True,
            recurringSpendFor=["trace"],
            unsupported=[],
        )

    if cid == "weyland-consortium-because-we-built-it":
        return base(
            c,
            recurringCreditsMax=1,
            recurringSpendFor=["advance_ice"],
            unsupported=[],
        )

    if cid == "government-contracts":
        return base(
            c,
            paidAbilities=[
                {
                    "id": "government-contracts-credits",
                    "label": "[click], [click]: Gain 4¢",
                    "clickCost": 2,
                    "creditCost": 0,
                    "cost": {"clicks": 2},
                    "windows": ["corp_action_paw"],
                    "effect": gain("corp", 4),
                }
            ],
            unsupported=[],
        )

    if cid == "tyrant":
        return base(
            c,
            canAdvance=True,
            canAdvanceOnlyWhenRezzed=True,
            gainsSubroutinesPerAdvancement={
                "subroutine": {
                    "id": "tyrant-etr",
                    "text": "End the run.",
                    "effect": etr(),
                }
            },
            subroutines=[],
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
            "A Study in Static (asis) Genesis set-complete from floor "
            f"v1.90.0 → v1.91.0. Wrote {len(written)} files; skipped "
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
