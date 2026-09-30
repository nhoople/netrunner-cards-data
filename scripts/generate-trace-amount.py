#!/usr/bin/env python3
"""Generate Trace Amount card JSON from pinned pack `ta`.

Catalog source: Null-Signal-Games/netrunner-cards-json (see data/nrdb-catalog-pin.json).
Fetch with: python3 scripts/nrdb_catalog.py fetch ta

Second Genesis-cycle wave after What Lies Ahead set-complete (floor v1.88.0).
Titles already clear under earlier waves are treated as reprints: skip emitting
duplicate files; list their ids in pool.json.

Hand-mapped Effect IR only — empty unsupported for set-complete.
Never kick Magnum Opus packs (`mo` / `mor`).

Usage: python3 scripts/generate-trace-amount.py
"""
from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

from nrdb_catalog import load_pack_cards

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "trace-amount"
WAVE = "trace-amount"
PACK = "ta"
EXPECTED = 20

# Already clear under Core / SC19 / etc.
REPRINTS = {
    "liberated-account",
    "notoriety",
    "jinteki-replicating-perfection",
    "fetal-ai",
    "trick-of-light",
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


def give_tags(n: int):
    return {"op": "do", "action": {"kind": "give_tags", "amount": n}}


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

    if cid == "vamp":
        return base(
            c,
            runEvent={
                "servers": "hq",
                "onSuccessfulRun": {
                    "op": "do",
                    "action": {"kind": "vamp_may_instead_of_breach"},
                },
            },
            unsupported=[],
        )

    if cid == "satellite-uplink":
        return base(
            c,
            onPlay={
                "op": "do",
                "action": {"kind": "expose_up_to", "max": 2},
            },
            unsupported=[],
        )

    if cid == "e3-feedback-implants":
        return base(
            c,
            onBreakSubroutineMayPayCreditsBreakAnother={"credits": 1},
            unsupported=[],
        )

    if cid == "compromised-employee":
        return base(
            c,
            link=1,
            recurringCreditsMax=1,
            recurringSpendFor=["trace"],
            onAnyIceRez=gain("runner", 1),
            unsupported=[],
        )

    if cid == "snowball":
        return breaker_card(
            c,
            "barrier",
            strength=1,
            break_c=1,
            break_max=1,
            pump_c=1,
            pump_s=1,
            strengthBonusOnBreakSubForRun=1,
            unsupported=[],
        )

    if cid == "dyson-mem-chip":
        return base(c, muBonus=1, link=1, unsupported=[])

    if cid == "encryption-protocol":
        return base(
            c,
            installedCardsTrashCostBonus=1,
            unsupported=[],
        )

    if cid == "sherlock-1-0":
        return base(
            c,
            subroutines=[
                {
                    "id": "sherlock-1-0-trace-1",
                    "text": (
                        "Trace[4]. If successful, add 1 installed program "
                        "to the top of the Runner's stack."
                    ),
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "trace",
                            "strength": 4,
                            "onSuccess": {
                                "op": "do",
                                "action": {
                                    "kind": "add_installed_program_to_stack_top"
                                },
                            },
                        },
                    },
                },
                {
                    "id": "sherlock-1-0-trace-2",
                    "text": (
                        "Trace[4]. If successful, add 1 installed program "
                        "to the top of the Runner's stack."
                    ),
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "trace",
                            "strength": 4,
                            "onSuccess": {
                                "op": "do",
                                "action": {
                                    "kind": "add_installed_program_to_stack_top"
                                },
                            },
                        },
                    },
                },
            ],
            unsupported=[],
        )

    if cid == "sensei":
        return base(
            c,
            subroutines=[
                {
                    "id": "sensei-etr-other",
                    "text": (
                        "For the remainder of this run, while the Runner is "
                        "encountering another piece of ice, it gains "
                        '"[subroutine] End the run." after its other subroutines.'
                    ),
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "sensei_register_etr_on_other_ice_for_run"
                        },
                    },
                }
            ],
            unsupported=[],
        )

    if cid == "big-brother":
        return base(
            c,
            playRequiresTagged=True,
            onPlay=give_tags(2),
            unsupported=[],
        )

    if cid == "chilo-city-grid":
        return base(
            c,
            onSuccessfulTraceDuringRun=give_tags(1),
            unsupported=[],
        )

    if cid == "power-grid-overload":
        return base(
            c,
            playRequiresSuccessfulRunLastTurn=True,
            onPlay={
                "op": "do",
                "action": {
                    "kind": "trace",
                    "strength": 2,
                    "onSuccess": {
                        "op": "do",
                        "action": {
                            "kind": "trash_hardware_install_cost_lte_last_trace_excess",
                            "pick": "choose",
                        },
                    },
                },
            },
            unsupported=[],
        )

    if cid == "amazon-industrial-zone":
        return base(
            c,
            mayImmediatelyRezIceOnInstallProtectingThisServerDiscount=3,
            unsupported=[],
        )

    if cid == "executive-retreat":
        return base(
            c,
            onScore=seq(
                {
                    "op": "do",
                    "action": {"kind": "add_agenda_counter", "amount": 1},
                },
                {
                    "op": "do",
                    "action": {"kind": "shuffle_hq_to_rd", "amount": 99},
                },
            ),
            paidAbilities=[
                {
                    "id": "executive-retreat-draw",
                    "label": "[click], hosted agenda counter: Draw 5 cards",
                    "clickCost": 1,
                    "creditCost": 0,
                    "cost": {"clicks": 1, "agendaCounters": 1},
                    "windows": ["corp_action_paw"],
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "draw",
                            "side": "corp",
                            "amount": 5,
                        },
                    },
                }
            ],
            unsupported=[],
        )

    if cid == "freelancer":
        return base(
            c,
            playRequiresTagged=True,
            onPlay={
                "op": "do",
                "action": {"kind": "trash_up_to_n_resources", "n": 2},
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
            "Trace Amount (ta) Genesis set-complete from floor v1.88.0 → v1.89.0. "
            f"Wrote {len(written)} files; skipped {len(skipped)} reprints. "
            f"Full clears among written: {len(clear_written)}; "
            f"partial: {len(partial_written)}. Never kick mo/mor packs."
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
