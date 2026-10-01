#!/usr/bin/env python3
"""Generate Cyber Exodus card JSON from pinned pack `ce`.

Catalog source: Null-Signal-Games/netrunner-cards-json (see data/nsg-catalog-pin.json).
Fetch with: python3 scripts/nsg_catalog.py fetch ce

Third Genesis-cycle wave after Trace Amount set-complete (floor v1.89.0).
Titles already clear under earlier waves are treated as reprints: skip emitting
duplicate files; list their ids in pool.json.

Hand-mapped Effect IR only — empty unsupported for set-complete.

Usage: python3 scripts/generate-cyber-exodus.py
"""
from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

from nsg_catalog import load_pack_cards

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "cyber-exodus"
WAVE = "cyber-exodus"
PACK = "ce"
EXPECTED = 20

# Already clear under Core / SC19 / SU21 / etc.
REPRINTS = {
    "emergency-shutdown",
    "chaos-theory-wunderkind",
    "test-run",
    "dinosaurus",
    "project-vitruvius",
    "marked-accounts",
    "pop-up-window",
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

    if cid == "nerve-agent":
        return base(
            c,
            onSuccessfulRun={
                "op": "if",
                "cond": {"op": "attacking_hq"},
                "then": {
                    "op": "do",
                    "action": {"kind": "add_virus_counter", "amount": 1},
                },
            },
            chooseBonusAccessLessThanVirusOnHqBreach=True,
            unsupported=[],
        )

    if cid == "joshua-b":
        return base(
            c,
            onTurnBegin={
                "op": "do",
                "action": {"kind": "may_gain_click_then_tag_at_turn_end"},
            },
            unsupported=[],
        )

    if cid == "muresh-bodysuit":
        return base(
            c,
            paidAbilities=[
                {
                    "id": "muresh-bodysuit-prevent",
                    "label": (
                        "[interrupt] → Prevent 1 meat damage "
                        "(first each turn)"
                    ),
                    "clickCost": 0,
                    "creditCost": 0,
                    "cost": {},
                    "windows": ["damage_interrupt_paw"],
                    "requirePendingDamageTypes": ["meat"],
                    "oncePerTurn": True,
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "prevent_pending_damage",
                            "amount": 1,
                        },
                    },
                }
            ],
            unsupported=[],
        )

    if cid == "snitch":
        return base(
            c,
            mayExposeApproachedUnrezzedIceOncePerRunThenMayJackOut=True,
            unsupported=[],
        )

    if cid == "personal-workshop":
        return base(
            c,
            personalWorkshop=True,
            paidAbilities=[
                {
                    "id": "personal-workshop-host",
                    "label": (
                        "[click]: Host a program or hardware from grip; "
                        "place power counters equal to its install cost"
                    ),
                    "clickCost": 1,
                    "creditCost": 0,
                    "cost": {"clicks": 1},
                    "windows": ["runner_action_paw"],
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": (
                                "host_grip_program_or_hardware_"
                                "with_power_equal_install_cost"
                            ),
                        },
                    },
                },
                {
                    "id": "personal-workshop-remove",
                    "label": (
                        "1¢: Remove 1 power counter from a hosted card "
                        "(install ignoring costs at 0)"
                    ),
                    "clickCost": 0,
                    "creditCost": 1,
                    "cost": {"credits": 1},
                    "windows": ["runner_action_paw"],
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": (
                                "remove_power_from_hosted_card_"
                                "install_at_zero_ignore_costs"
                            ),
                        },
                    },
                },
            ],
            onTurnBegin={
                "op": "do",
                "action": {
                    "kind": (
                        "remove_power_from_hosted_card_"
                        "install_at_zero_ignore_costs"
                    ),
                },
            },
            unsupported=[],
        )

    if cid == "public-sympathy":
        return base(c, handSizeBonus=2, unsupported=[])

    if cid == "viper":
        return base(
            c,
            subroutines=[
                {
                    "id": "viper-trace-click",
                    "text": (
                        "Trace[3]. If successful, the Runner loses "
                        "[click], if able."
                    ),
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "trace",
                            "strength": 3,
                            "onSuccess": {
                                "op": "do",
                                "action": {
                                    "kind": "lose_clicks",
                                    "side": "runner",
                                    "amount": 1,
                                },
                            },
                        },
                    },
                },
                {
                    "id": "viper-trace-etr",
                    "text": "Trace[3]. If successful, end the run.",
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "trace",
                            "strength": 3,
                            "onSuccess": etr(),
                        },
                    },
                },
            ],
            unsupported=[],
        )

    if cid == "edge-of-world":
        return base(
            c,
            onAccessRequiresInstalled=True,
            onAccess={
                "op": "do",
                "action": {
                    "kind": (
                        "may_pay_credits_for_core_damage_"
                        "per_ice_protecting_this_server"
                    ),
                    "amount": 3,
                },
            },
            unsupported=[],
        )

    if cid == "sunset":
        return base(
            c,
            onPlay={
                "op": "do",
                "action": {"kind": "choose_server_rearrange_ice"},
            },
            unsupported=[],
        )

    if cid == "woodcutter":
        return base(
            c,
            canAdvance=True,
            canAdvanceOnlyWhenRezzed=True,
            gainsSubroutinesPerAdvancement={
                "subroutine": {
                    "id": "woodcutter-net",
                    "text": "Do 1 net damage.",
                    "effect": {
                        "op": "do",
                        "action": {"kind": "net_damage", "amount": 1},
                    },
                }
            },
            subroutines=[],
            unsupported=[],
        )

    if cid == "commercialization":
        return base(
            c,
            onPlay={
                "op": "do",
                "action": {
                    "kind": "choose_ice_gain_credits_per_advancement",
                },
            },
            unsupported=[],
        )

    if cid == "private-contracts":
        return base(
            c,
            onRez={
                "op": "do",
                "action": {"kind": "place_hosted_credits", "amount": 14},
            },
            paidAbilities=[
                {
                    "id": "private-contracts-take",
                    "label": "[click]: Take 2¢ from Private Contracts",
                    "clickCost": 1,
                    "creditCost": 0,
                    "cost": {"clicks": 1},
                    "windows": ["corp_action_paw"],
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "take_hosted_credits",
                            "amount": 2,
                        },
                    },
                }
            ],
            unsupported=[],
        )

    if cid == "chimera":
        return base(
            c,
            onRez={
                "op": "do",
                "action": {"kind": "choose_one_subtype_until_derez"},
            },
            derezAtAnyTurnEnd=True,
            subroutines=[
                {
                    "id": "chimera-etr",
                    "text": "End the run.",
                    "effect": etr(),
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
            "Cyber Exodus (ce) Genesis set-complete from floor v1.89.0 → v1.90.0. "
            f"Wrote {len(written)} files; skipped {len(skipped)} reprints. "
            f"Full clears among written: {len(clear_written)}; "
            f"partial: {len(partial_written)}."
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
