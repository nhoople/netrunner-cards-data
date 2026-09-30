"""Shared helpers for Spin cycle pack generate scripts."""
from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


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


def do(kind: str, **kwargs):
    return {"op": "do", "action": {"kind": kind, **kwargs}}


def seq(*effects):
    return {"op": "seq", "effects": list(effects)}


def gain(side: str, n: int):
    return do("gain_credits", side=side, amount=n)


def draw(side: str, n: int):
    return do("draw", side=side, amount=n)


def etr():
    return do("end_the_run")


def net(n: int):
    return do("net_damage", amount=n)


def core(n: int):
    return do("core_damage", amount=n)


def trace_sub(strength: int, on_success, on_failure=None):
    action = {"kind": "trace", "strength": strength, "onSuccess": on_success}
    if on_failure:
        action["onFailure"] = on_failure
    return {"op": "do", "action": action}


def breaker_card(c, subtype: str, strength: int, break_cost: int, pump_cost: int, pump_str: int):
    subtypes = []
    if c.get("keywords"):
        subtypes = [s.strip().lower() for s in c["keywords"].split(" - ")]
    card = base(c, subtypes=subtypes or [subtype.split()[-1]])
    card["breaker"] = {
        "breaksSubtype": subtype,
        "strength": strength,
        "breakCredits": break_cost,
        "breakMaxSubs": 1,
        "pumpCredits": pump_cost,
        "pumpStrength": pump_str,
    }
    return card


def base(c, **extra):
    subtypes = extra.pop("subtypes", None)
    if subtypes is None and c.get("keywords"):
        subtypes = [s.strip().lower() for s in c["keywords"].split(" - ")]
    card = {
        "id": slugify(c["title"]),
        "title": c["title"],
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
    if c.get("uniqueness"):
        card["unique"] = True
    card.update(extra)
    return card


def write_manifest(out: Path, wave: str, pack: str, expected: int, pool_ids, written, skipped, clear_written):
    manifest = {
        "pack": wave,
        "nrdbPackCode": pack,
        "count": expected,
        "written": len(written),
        "reprintSkipped": len(skipped),
        "status": "supported",
        "notes": (
            f"{wave} ({pack}) set-complete. Wrote {len(written)}; "
            f"skipped {len(skipped)} reprints. Clears: {len(clear_written)}."
        ),
        "cards": pool_ids,
        "reprintIdsFromEarlierWaves": sorted(skipped),
        "clears": clear_written,
    }
    (out / "_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"
    )
