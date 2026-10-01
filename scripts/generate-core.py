#!/usr/bin/env python3
"""Generate FFG Core Set card JSON from pinned pack `core`.

Catalog source: Null-Signal-Games/netrunner-cards-json (see data/nsg-catalog-pin.json).
Fetch with: python3 scripts/nsg_catalog.py fetch core

Core Set is the first FFG Core-forward wave from floor v1.86.0.
Titles already clear under Gateway / SU21 / SC19 (etc.) are treated as reprints:
skip emitting duplicate files; list their ids in pool.json.

Hand-mapped Effect IR only where existing primitives fully cover the card;
everything else lists honest unsupported notes — never invent IR.

Note: Magnum Opus the *program* is Core Set content (distinct from packs `mo`/`mor`).

Usage: python3 scripts/generate-core.py
"""
from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

from nsg_catalog import load_pack_cards

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "core"
WAVE = "core"
PACK = "core"
EXPECTED = 113

# Already clear under system-gateway / system-update-2021 / system-core-2019.
# Do not emit duplicate files; pool.json still lists these ids for the wave.
REPRINTS = {
    "stimhack",
    "cyberfeeder",
    "corroder",
    "datasucker",
    "mimic",
    "ice-carver",
    "gabriel-santiago-consummate-professional",
    "easy-mark",
    "forged-activation-orders",
    "inside-job",
    "special-order",
    "femme-fatale",
    "sneakdoor-beta",
    "bank-job",
    "data-dealer",
    "diesel",
    "modded",
    "the-makers-eye",
    "tinkering",
    "akamatsu-mem-chip",
    "battering-ram",
    "gordian-blade",
    "pipeline",
    "aesops-pawnshop",
    "sure-gamble",
    "crypsis",
    "armitage-codebusting",
    "adonis-campaign",
    "aggressive-secretary",
    "archived-memories",
    "biotic-labor",
    "heimdall-1-0",
    "ichi-1-0",
    "viktor-1-0",
    "rototurret",
    "corporate-troubleshooter",
    "jinteki-personal-evolution",
    "nisei-mk-ii",
    "project-junebug",
    "snare",
    "neural-emp",
    "neural-katana",
    "wall-of-thorns",
    "nbn-making-news",
    "closed-accounts",
    "psychographics",
    "sea-source",
    "ghost-branch",
    "data-raven",
    "tollbooth",
    "red-herrings",
    "sansan-city-grid",
    "weyland-consortium-building-a-better-world",
    "hostile-takeover",
    "beanstalk-royalties",
    "archer",
    "hadrians-wall",
    "ice-wall",
    "priority-requisition",
    "pad-campaign",
    "hedge-fund",
    "enigma",
    "hunter",
    "wall-of-static",
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


def net(n: int):
    return {"op": "do", "action": {"kind": "net_damage", "amount": n}}


def meat(n: int):
    return {"op": "do", "action": {"kind": "meat_damage", "amount": n}}


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


def breaker_card(
    c,
    subtype,
    strength,
    break_c,
    pump_c=None,
    pump_s=None,
    break_max=None,
    duration=None,
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
        if duration:
            pump_eff["action"]["duration"] = duration
        label_dur = (
            " for the remainder of this run" if duration == "run" else ""
        )
        paid.append(
            {
                "id": f"{slugify(c['title'])}-pump",
                "label": (
                    f"Pump {c['title']} +{pump_s if pump_s is not None else 1} "
                    f"strength{label_dur}"
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

    # --- Kickoff clears: existing IR only ---

    if cid == "magnum-opus":
        return base(
            c,
            paidAbilities=[
                {
                    "id": "magnum-opus-gain",
                    "label": "[click]: Gain 2¢",
                    "clickCost": 1,
                    "creditCost": 0,
                    "cost": {"clicks": 1},
                    "windows": ["runner_action_paw"],
                    "effect": gain("runner", 2),
                }
            ],
            unsupported=[],
        )

    if cid == "anonymous-tip":
        return base(c, onPlay=draw("corp", 3), unsupported=[])

    if cid == "yog-0":
        return breaker_card(
            c,
            "code gate",
            strength=3,
            break_c=0,
            break_max=1,
            unsupported=[],
        )

    if cid == "aurora":
        return breaker_card(
            c,
            "barrier",
            strength=1,
            break_c=2,
            break_max=1,
            pump_c=2,
            pump_s=3,
            unsupported=[],
        )

    if cid == "ninja":
        return breaker_card(
            c,
            "sentry",
            strength=0,
            break_c=1,
            break_max=1,
            pump_c=3,
            pump_s=5,
            unsupported=[],
        )

    if cid == "access-to-globalsec":
        return base(c, link=1, unsupported=[])

    if cid == "desperado":
        return base(
            c,
            unique=True,
            muBonus=1,
            onSuccessfulRun=gain("runner", 1),
            unsupported=[],
        )

    if cid == "decoy":
        return base(
            c,
            paidAbilities=[
                {
                    "id": "decoy-prevent-tag",
                    "label": "[interrupt] → [trash]: Prevent 1 tag",
                    "clickCost": 0,
                    "creditCost": 0,
                    "cost": {"trashSelf": True},
                    "windows": ["tag_interrupt_paw"],
                    "effect": {
                        "op": "do",
                        "action": {"kind": "prevent_pending_tags", "amount": 1},
                    },
                }
            ],
            unsupported=[],
        )

    if cid == "wyldside":
        return base(
            c,
            unique=True,
            onTurnBegin=seq(
                draw("runner", 2),
                {
                    "op": "do",
                    "action": {
                        "kind": "lose_clicks",
                        "side": "runner",
                        "amount": 1,
                    },
                },
            ),
            unsupported=[],
        )

    if cid == "net-shield":
        return base(
            c,
            paidAbilities=[
                {
                    "id": "net-shield-prevent",
                    "label": (
                        "[interrupt] → 1¢: Prevent 1 net damage "
                        "(first each turn)"
                    ),
                    "clickCost": 0,
                    "creditCost": 1,
                    "cost": {"credits": 1},
                    "windows": ["damage_interrupt_paw"],
                    "requirePendingDamageTypes": ["net"],
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

    if cid == "the-toolbox":
        return base(
            c,
            unique=True,
            muBonus=2,
            link=2,
            recurringCreditsMax=2,
            recurringSpendFor=["use_program"],
            unsupported=[],
        )

    if cid == "crash-space":
        return base(
            c,
            recurringCreditsMax=2,
            paidAbilities=[
                {
                    "id": "crash-space-prevent-meat",
                    "label": "[interrupt] → [trash]: Prevent up to 3 meat damage",
                    "clickCost": 0,
                    "creditCost": 0,
                    "cost": {"trashSelf": True},
                    "windows": ["damage_interrupt_paw"],
                    "requirePendingDamageTypes": ["meat"],
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "prevent_pending_damage",
                            "amount": 3,
                        },
                    },
                }
            ],
            unsupported=[
                "Recurring credits spendable for the basic remove-tag action "
                "(no RecurringSpendPurpose for basic_remove_tag yet)."
            ],
        )

    if cid == "scorched-earth":
        return base(
            c,
            playRequiresTagged=True,
            onPlay=meat(4),
            unsupported=[],
        )

    if cid == "melange-mining-corp":
        return base(
            c,
            paidAbilities=[
                {
                    "id": "melange-mining-corp-gain",
                    "label": "[click][click][click]: Gain 7¢",
                    "clickCost": 3,
                    "creditCost": 0,
                    "cost": {"clicks": 3},
                    "windows": ["corp_action_paw"],
                    "effect": gain("corp", 7),
                }
            ],
            unsupported=[],
        )

    if cid == "shipment-from-kaguya":
        return base(
            c,
            onPlay={
                "op": "do",
                "action": {
                    "kind": "place_advancements_on_up_to",
                    "amountEach": 1,
                    "maxCards": 2,
                },
            },
            unsupported=[],
        )

    if cid == "data-mine":
        return base(
            c,
            subroutines=[
                {
                    "id": "data-mine-net-trash",
                    "text": "Do 1 net damage. Trash Data Mine.",
                    "effect": seq(
                        net(1),
                        {"op": "do", "action": {"kind": "trash_self"}},
                    ),
                }
            ],
            unsupported=[],
        )

    if cid == "breaking-news":
        return base(
            c,
            onScore={
                "op": "do",
                "action": {"kind": "give_tags", "amount": 2},
            },
            onDiscardPhaseEnd={
                "op": "if",
                "cond": {"op": "self_scored_this_turn"},
                "then": {
                    "op": "do",
                    "action": {"kind": "remove_tags", "amount": 2},
                },
            },
            unsupported=[],
        )

    if cid == "precognition":
        return base(
            c,
            onPlay={
                "op": "do",
                "action": {"kind": "look_top_n_rd_arrange", "n": 5},
            },
            unsupported=[],
        )

    if cid == "shadow":
        return base(
            c,
            canAdvance=True,
            strengthPerAdvancement=1,
            subroutines=[
                {
                    "id": "shadow-gain",
                    "text": "The Corp gains 2¢.",
                    "effect": gain("corp", 2),
                },
                {
                    "id": "shadow-trace-tag",
                    "text": "Trace[3]. If successful, give the Runner 1 tag.",
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "trace",
                            "strength": 3,
                            "onSuccess": {
                                "op": "do",
                                "action": {
                                    "kind": "give_tags",
                                    "amount": 1,
                                },
                            },
                        },
                    },
                },
            ],
            unsupported=[],
        )

    if cid == "research-station":
        return base(
            c,
            installServers=["hq"],
            handSizeBonus=2,
            unsupported=[],
        )

    if cid == "astroscript-pilot-program":
        return base(
            c,
            onScore={
                "op": "do",
                "action": {"kind": "add_agenda_counter", "amount": 1},
            },
            paidAbilities=[
                {
                    "id": "astroscript-advance",
                    "label": "Hosted agenda counter: Place 1 advancement counter",
                    "clickCost": 0,
                    "creditCost": 0,
                    "cost": {"agendaCounters": 1},
                    "windows": ["corp_action_paw"],
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "place_advancements",
                            "amount": 1,
                        },
                    },
                }
            ],
            unsupported=[],
        )

    if cid == "akitaro-watanabe":
        return base(
            c,
            unique=True,
            iceRezCostReductionProtectingThisServer=2,
            unsupported=[],
        )

    if cid == "private-security-force":
        return base(
            c,
            paidAbilities=[
                {
                    "id": "private-security-force-meat",
                    "label": "[click]: Do 1 meat damage (Runner tagged)",
                    "clickCost": 1,
                    "creditCost": 0,
                    "cost": {"clicks": 1},
                    "windows": ["corp_action_paw"],
                    "requireRunnerTagged": True,
                    "effect": meat(1),
                }
            ],
            unsupported=[],
        )

    if cid == "parasite":
        return base(
            c,
            installOnIce=True,
            hostStrengthPerVirusCounter=-1,
            onTurnBegin={
                "op": "do",
                "action": {"kind": "add_virus_counter", "amount": 1},
            },
            unsupported=[
                "Auto-trash host ice when its strength is 0 or less "
                "(continuous check not yet modeled; Chisel-class is "
                "encounter-timed only)."
            ],
        )

    if cid == "wyrm":
        return breaker_card(
            c,
            "*",
            strength=1,
            break_c=3,
            break_max=1,
            pump_c=1,
            pump_s=1,
            paidAbilities=[
                {
                    "id": "wyrm-weaken",
                    "label": (
                        "1¢: Encountered ice gets −1 strength for this encounter"
                    ),
                    "clickCost": 0,
                    "creditCost": 1,
                    "cost": {"credits": 1},
                    "windows": ["encounter_paw"],
                    "effect": {
                        "op": "do",
                        "action": {"kind": "weaken_ice", "amount": 1},
                    },
                }
            ],
            unsupported=[
                "Break ability requires ice with 0 or less strength "
                "(breakRequiresStrengthLte not yet modeled; break is "
                "always offered when interfacing)."
            ],
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
            "FFG Core Set (core) kickoff from floor v1.86.0. "
            f"Wrote {len(written)} files; skipped {len(skipped)} reprints "
            f"(Gateway/SU21/SC19). Kickoff full clears among written: "
            f"{len(clear_written)}; partial: {len(partial_written)}. "
            ""
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
