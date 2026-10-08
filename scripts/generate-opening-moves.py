#!/usr/bin/env python3
"""Generate Opening Moves card JSON from pinned pack `om`.

Catalog source: Null-Signal-Games/netrunner-cards-json (see data/nsg-catalog-pin.json).
Fetch with: python3 scripts/nsg_catalog.py fetch om

Spin cycle pack after Creation and Control set-complete (floor v1.94.0).
Titles already clear under earlier waves are treated as reprints: skip emitting
duplicate files; list their ids in pool.json.

Hand-mapped Effect IR only — empty unsupported for set-complete.

Usage: python3 scripts/generate-opening-moves.py
"""
from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

from nsg_catalog import load_pack_cards

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "opening-moves"
WAVE = "opening-moves"
PACK = "om"
EXPECTED = 20

REPRINTS = {
    "hostage",
    "john-masanori",
    "himitsu-bako",
    "celebrity-gift",
}


def slugify(title: str) -> str:
    t = title.replace("™", "").replace("®", "").replace("©", "")
    t = unicodedata.normalize("NFKD", t)
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = t.lower()
    t = t.replace(""", "").replace(""", "").replace('"', "")
    t = t.replace("'", "").replace("'", "").replace("ʼ", "")
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


def draw(side: str, n: int):
    return {"op": "do", "action": {"kind": "draw", "side": side, "amount": n}}


def seq(*effects):
    return {"op": "seq", "effects": list(effects)}


def do(kind: str, **kwargs):
    return {"op": "do", "action": {"kind": kind, **kwargs}}


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


def trash_prog_unless_pay3():
    return do(
        "unless",
        payer="runner",
        cost=do("lose_credits", side="runner", amount=3),
        instruction=do("trash_program", pick="choose"),
    )


def map_card(c: dict) -> dict | None:
    cid = slugify(c["title"])
    if cid in REPRINTS:
        return None

    if cid == "frame-job":
        return base(
            c,
            playAdditionalClick=True,
            playAdditionalCost=do("choose_forfeit_runner_scored_agenda"),
            onPlay=do("give_bad_publicity", amount=1),
            unsupported=[],
        )

    if cid == "pawn":
        return base(
            c,
            installOnIce=True,
            caissaAdvanceOnSuccessfulRun=True,
            paidAbilities=[
                {
                    "id": "pawn-host",
                    "label": "[click]: Host on outermost ice protecting a central server",
                    "clickCost": 1,
                    "creditCost": 0,
                    "cost": {"clicks": 1},
                    "windows": ["runner_action_paw"],
                    "effect": do("caissa_pawn_host_outermost_central"),
                }
            ],
            unsupported=[],
        )

    if cid == "rook":
        return base(
            c,
            installOnIce=True,
            iceRezCostIncreaseProtectingHostedServer=2,
            paidAbilities=[
                {
                    "id": "rook-host",
                    "label": "[click]: Host on ice not hosting a Caïssa program",
                    "clickCost": 1,
                    "creditCost": 0,
                    "cost": {"clicks": 1},
                    "windows": ["runner_action_paw"],
                    "effect": do("caissa_rook_host"),
                }
            ],
            unsupported=[],
        )

    if cid == "gorman-drip-v1":
        return base(
            c,
            onCorpBasicClickForCreditOrDraw=do("add_virus_counter", amount=1),
            paidAbilities=[
                {
                    "id": "gorman-cash",
                    "label": "[click], [trash]: Gain 1¢ per virus counter",
                    "clickCost": 1,
                    "creditCost": 0,
                    "cost": {"clicks": 1, "trashSelf": True},
                    "windows": ["runner_action_paw"],
                    "effect": do(
                        "gain_credits",
                        side="runner",
                        amount=0,
                        tally={
                            "count": "source_virus_counters",
                            "per": 1,
                            "side": "source",
                        },
                    ),
                }
            ],
            unsupported=[],
        )

    if cid == "lockpick":
        return base(
            c,
            recurringCreditsMax=1,
            recurringSpendFor=["use_decoder"],
            unsupported=[],
        )

    if cid == "false-echo":
        return base(
            c,
            onPassUnrezzedIce={
                "op": "choose",
                "chooser": "runner",
                "options": [
                    {
                        "id": "trash",
                        "label": "Trash False Echo",
                        "effect": do(
                            "false_echo_trash_then_corp_rez_or_hq",
                            iceIdFromPass=True,
                        ),
                    },
                    {
                        "id": "decline",
                        "label": "Decline",
                        "effect": gain("runner", 0),
                    },
                ],
            },
            unsupported=[],
        )

    if cid == "motivation":
        return base(
            c,
            onTurnBegin={
                "op": "choose",
                "chooser": "runner",
                "options": [
                    {
                        "id": "look",
                        "label": "Look at top card of stack",
                        "effect": do("look_top_n_stack_peek", amount=1),
                    },
                    {
                        "id": "decline",
                        "label": "Decline",
                        "effect": gain("runner", 0),
                    },
                ],
            },
            unsupported=[],
        )

    if cid == "project-ares":
        return base(
            c,
            onScore=do("project_ares_on_score", past=4),
            unsupported=[],
        )

    if cid == "next-bronze":
        return base(
            c,
            strengthBonusPerRezzedIceWithSubtype={"subtype": "next", "bonus": 1},
            subroutines=[
                {
                    "id": "next-bronze-etr",
                    "text": "End the run.",
                    "effect": etr(),
                }
            ],
            unsupported=[],
        )

    if cid == "character-assassination":
        return base(
            c,
            onScore=do("trash_resource", pick="choose", cannotPrevent=True),
            unsupported=[],
        )

    if cid == "jackson-howard":
        return base(
            c,
            paidAbilities=[
                {
                    "id": "jackson-draw",
                    "label": "[click]: Draw 2 cards",
                    "clickCost": 1,
                    "creditCost": 0,
                    "cost": {"clicks": 1},
                    "windows": ["corp_action_paw"],
                    "effect": draw("corp", 2),
                },
                {
                    "id": "jackson-rfg",
                    "label": "Remove Jackson Howard from the game: Shuffle up to 3 from Archives into R&D",
                    "clickCost": 0,
                    "creditCost": 0,
                    "cost": {"rfgSelf": True},
                    "windows": ["corp_action_paw"],
                    "effect": do("shuffle_archives_to_rd", amount=3),
                },
            ],
            unsupported=[],
        )

    if cid == "invasion-of-privacy":
        return base(
            c,
            playAdditionalClick=True,
            onPlay=do("invasion_of_privacy", traceStrength=2),
            unsupported=[],
        )

    if cid == "geothermal-fracking":
        return base(
            c,
            onScore=do("add_agenda_counter", amount=2),
            paidAbilities=[
                {
                    "id": "geothermal-cash",
                    "label": "[click], hosted agenda counter: Gain 7[credit] and take 1 bad publicity",
                    "clickCost": 1,
                    "creditCost": 0,
                    "cost": {"clicks": 1, "agendaCounters": 1},
                    "windows": ["corp_action_paw"],
                    "effect": seq(
                        gain("corp", 7),
                        do("give_bad_publicity", amount=1),
                    ),
                }
            ],
            unsupported=[],
        )

    if cid == "swarm":
        return base(
            c,
            onRez=do("give_bad_publicity", amount=1),
            canAdvance=True,
            canAdvanceOnlyWhenRezzed=True,
            gainsSubroutinesPerAdvancement={
                "subroutine": {
                    "id": "swarm-trash-prog",
                    "text": "Trash 1 installed program unless the Runner pays 3[credit].",
                    "effect": trash_prog_unless_pay3(),
                }
            },
            subroutines=[],
            unsupported=[],
        )

    if cid == "cyberdex-trial":
        return base(
            c,
            onPlay=do("purge_virus_counters"),
            unsupported=[],
        )

    if cid == "grim":
        return base(
            c,
            onRez=do("give_bad_publicity", amount=1),
            subroutines=[
                {
                    "id": "grim-trash-prog",
                    "text": "Trash 1 installed program.",
                    "effect": do("trash_program", pick="choose"),
                }
            ],
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
            "Opening Moves (om) set-complete from floor "
            f"v1.94.0 → v1.95.0. Wrote {len(written)} files; skipped "
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
    if partial_written:
        print("PARTIAL=" + json.dumps(partial_written))
    print("CLEARS=" + json.dumps(clear_written))
    print("POOL_IDS=" + json.dumps(pool_ids))


if __name__ == "__main__":
    main()
