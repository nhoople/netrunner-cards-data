#!/usr/bin/env python3
"""Generate Future Proof card JSON from pinned pack `fp`.

Catalog source: Null-Signal-Games/netrunner-cards-json (see data/nrdb-catalog-pin.json).
Fetch with: python3 scripts/nrdb_catalog.py fetch fp

Sixth Genesis-cycle wave after Humanity's Shadow set-complete (floor v1.92.0).
Titles already clear under earlier waves are treated as reprints: skip emitting
duplicate files; list their ids in pool.json.

Hand-mapped Effect IR only — empty unsupported for set-complete.
Never kick Magnum Opus packs (`mo` / `mor`).

Usage: python3 scripts/generate-future-proof.py
"""
from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

from nrdb_catalog import load_pack_cards

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "future-proof"
WAVE = "future-proof"
PACK = "fp"
EXPECTED = 20

# Already clear under Core / SC19 / SU21 / etc.
REPRINTS = {
    "retrieval-run",
    "faerie",
    "r-d-interface",
    "eli-1-0",
    "ronin",
    "project-beale",
    "flare",
}


def slugify(title: str) -> str:
    t = title.replace("™", "").replace("®", "").replace("©", "")
    t = unicodedata.normalize("NFKD", t)
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = t.lower()
    t = t.replace("“", "").replace("”", "").replace('"', "")
    t = t.replace("'", "").replace("’", "").replace("ʼ", "")
    t = t.replace(".", "-").replace(":", " ").replace("!", "").replace("*", "")
    t = t.replace("(", " ").replace(")", " ")
    t = re.sub(r"[^a-z0-9]+", "-", t)
    return t.strip("-")


def strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text or "")


def etr():
    return {"op": "do", "action": {"kind": "end_the_run"}}


def gain(side: str, n: int):
    return {"op": "do", "action": {"kind": "gain_credits", "side": side, "amount": n}}


def lose(side: str, n: int):
    return {"op": "do", "action": {"kind": "lose_credits", "side": side, "amount": n}}


def draw(side: str, n: int):
    return {"op": "do", "action": {"kind": "draw", "side": side, "amount": n}}


def seq(*effects):
    return {"op": "seq", "effects": list(effects)}


def tags(n: int):
    return {"op": "do", "action": {"kind": "give_tags", "amount": n}}


def decline(side: str = "runner"):
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

    if cid == "darwin":
        return base(
            c,
            strength=0,
            strengthPerVirusCounter=1,
            breaker={
                "breaksSubtype": "*",
                "strength": 0,
                "breakCredits": 2,
                "breakMaxSubs": 1,
            },
            onTurnBegin={
                "op": "do",
                "action": {
                    "kind": "may_pay_credits_add_virus_counter",
                    "credits": 1,
                    "amount": 1,
                },
            },
            unsupported=[],
        )

    if cid == "data-leak-reversal":
        return base(
            c,
            installRequiresSuccessfulCentralRunThisTurn=True,
            paidAbilities=[
                {
                    "id": "dlr-trash-rd",
                    "label": "[click]: The Corp trashes the top card of R&D",
                    "clickCost": 1,
                    "creditCost": 0,
                    "cost": {"clicks": 1},
                    "windows": ["runner_action_paw"],
                    "requireRunnerTagged": True,
                    "effect": {
                        "op": "do",
                        "action": {"kind": "trash_top_of_rd"},
                    },
                }
            ],
            unsupported=[],
        )

    if cid == "mr-li":
        return base(
            c,
            unique=True,
            paidAbilities=[
                {
                    "id": "mr-li-draw",
                    "label": "[click]: Draw 2 cards; put 1 of those on bottom of stack",
                    "clickCost": 1,
                    "creditCost": 0,
                    "cost": {"clicks": 1},
                    "windows": ["runner_action_paw"],
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "draw_n_then_bottom_one_of_drawn",
                            "amount": 2,
                        },
                    },
                }
            ],
            unsupported=[],
        )

    if cid == "indexing":
        return base(
            c,
            runEvent={
                "servers": "rd",
                "onSuccessfulRun": {
                    "op": "do",
                    "action": {"kind": "indexing_may_instead_of_breach"},
                },
            },
            unsupported=[],
        )

    if cid == "deep-thought":
        return base(
            c,
            onSuccessfulRun={
                "op": "if",
                "cond": {"op": "attacking_rd"},
                "then": {
                    "op": "do",
                    "action": {"kind": "add_virus_counter", "amount": 1},
                },
            },
            onTurnBegin={
                "op": "if",
                "cond": {"op": "virus_counters_gte", "amount": 3},
                "then": {
                    "op": "choose",
                    "chooser": "runner",
                    "options": [
                        {
                            "id": "look",
                            "label": "Look at the top card of R&D",
                            "effect": {
                                "op": "do",
                                "action": {
                                    "kind": "look_top_n_rd_peek",
                                    "n": 1,
                                },
                            },
                        },
                        decline("runner"),
                    ],
                },
            },
            unsupported=[],
        )

    if cid == "new-angeles-city-hall":
        return base(
            c,
            unique=True,
            paidAbilities=[
                {
                    "id": "nach-prevent-tag",
                    "label": "[interrupt] → 2¢: Prevent 1 tag",
                    "clickCost": 0,
                    "creditCost": 2,
                    "cost": {"credits": 2},
                    "windows": ["tag_interrupt_paw"],
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "prevent_pending_tags",
                            "amount": 1,
                        },
                    },
                }
            ],
            onStealAgenda={
                "op": "do",
                "action": {"kind": "trash_self"},
            },
            unsupported=[],
        )

    if cid == "ruhr-valley":
        return base(
            c,
            additionalRunInitiateClicks=1,
            unsupported=[],
        )

    if cid == "midori":
        return base(
            c,
            unique=True,
            onApproachIceOncePerRun=True,
            onApproachIce={
                "op": "do",
                "action": {"kind": "midori_may_swap_approached_ice_with_hq"},
            },
            unsupported=[],
        )

    if cid == "nbn-the-world-is-yours":
        return base(
            c,
            handSizeBonus=1,
            unsupported=[],
        )

    if cid == "midseason-replacements":
        return base(
            c,
            playRequiresAgendaStolenLastTurn=True,
            onPlay={
                "op": "do",
                "action": {
                    "kind": "trace",
                    "strength": 6,
                    "onSuccess": {
                        "op": "do",
                        "action": {
                            "kind": "give_tags_equal_to_last_trace_excess",
                        },
                    },
                },
            },
            unsupported=[],
        )

    if cid == "dedicated-response-team":
        return base(
            c,
            onSuccessfulRunEnd={
                "op": "if",
                "cond": {"op": "runner_tagged"},
                "then": {
                    "op": "do",
                    "action": {"kind": "meat_damage", "amount": 2},
                },
            },
            unsupported=[],
        )

    if cid == "burke-bugs":
        return base(
            c,
            subroutines=[
                {
                    "id": "burke-bugs-trace",
                    "text": (
                        "Trace[0]. If successful, the Runner trashes 1 program."
                    ),
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "trace",
                            "strength": 0,
                            "onSuccess": {
                                "op": "do",
                                "action": {"kind": "trash_own_program"},
                            },
                        },
                    },
                }
            ],
            unsupported=[],
        )

    if cid == "corporate-war":
        return base(
            c,
            onScore={
                "op": "if",
                "cond": {
                    "op": "credits_gte",
                    "side": "corp",
                    "amount": 7,
                },
                "then": gain("corp", 7),
                "else": {
                    "op": "do",
                    "action": {"kind": "lose_all_credits", "side": "corp"},
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
            "Future Proof (fp) Genesis set-complete from floor "
            f"v1.92.0 → v1.93.0. Wrote {len(written)} files; skipped "
            f"{len(skipped)} reprints. Full clears among written: "
            f"{len(clear_written)}; partial: {len(partial_written)}. "
            "Never kick mo/mor."
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
