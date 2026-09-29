#!/usr/bin/env python3
"""Generate Uprising card JSON from pinned pack `ur`.

Catalog source: Null-Signal-Games/netrunner-cards-json (see data/nrdb-catalog-pin.json).
Fetch with: python3 scripts/nrdb_catalog.py fetch ur

Uprising Booster Pack (`urbp`) titles are absorbed into `ur` printings
(same pattern as Midnight Sun Booster → ms).

Hand-mapped Effect IR only where existing primitives fully cover the card;
everything else lists honest unsupported notes — never invent IR.

Usage: python3 scripts/generate-uprising.py
"""
from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

from nrdb_catalog import load_pack_cards

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "uprising"
WAVE = "uprising"
PACK = "ur"
EXPECTED = 65


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


def gain_clicks(side: str, n: int):
    return {"op": "do", "action": {"kind": "gain_clicks", "side": side, "amount": n}}


def take_hosted(n: int):
    return {"op": "do", "action": {"kind": "take_hosted_credits", "amount": n}}


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
                "label": f"Pump {c['title']} +{pump_s if pump_s is not None else 1} strength",
                "clickCost": 0,
                "creditCost": pump_c,
                "cost": {"credits": pump_c},
                "windows": ["encounter_paw"],
                "effect": pump_eff,
            }
        )
    return base(c, breaker=br, paidAbilities=paid, **extra)


def map_card(c: dict) -> dict:
    cid = slugify(c["title"])
    text = strip_html(c.get("text") or "")
    plain = re.sub(r"\s+", " ", text).strip()

    # --- v1.35.0 kickoff: existing IR only ---

    if cid == "daily-casts":
        return base(
            c,
            hostedCreditsOnInstall=8,
            onTurnBegin=take_hosted(2),
            unsupported=[],
        )

    if cid == "bass-ch1r180g4":
        return base(
            c,
            paidAbilities=[
                {
                    "id": "bass-ch1r180g4-clicks",
                    "label": "[click], [trash]: Gain [click][click]",
                    "clickCost": 1,
                    "creditCost": 0,
                    "cost": {"clicks": 1, "trashSelf": True},
                    "windows": ["corp_action_paw"],
                    "effect": gain_clicks("corp", 2),
                }
            ],
            unsupported=[],
        )

    if cid == "makler":
        return breaker_card(
            c,
            "barrier",
            2,
            2,
            2,
            2,
            break_max=2,
            onFullyBreakOncePerTurn=gain("runner", 1),
            unsupported=[],
        )

    # --- v1.36.0 A-slice ---

    if cid == "la-costa-grid":
        return base(
            c,
            remoteOnly=True,
            onTurnBegin={
                "op": "do",
                "action": {
                    "kind": "place_advancements",
                    "amount": 1,
                    "sameServerRootAsSource": True,
                    "pick": "choose",
                },
            },
            unsupported=[],
        )

    if cid == "gold-farmer":
        etr_unless_3 = {
            "op": "choose",
            "chooser": "runner",
            "options": [
                {
                    "id": "pay3",
                    "label": "Pay 3¢",
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "lose_credits",
                            "side": "runner",
                            "amount": 3,
                        },
                    },
                },
                {
                    "id": "etr",
                    "label": "End the run",
                    "effect": {
                        "op": "do",
                        "action": {"kind": "end_the_run"},
                    },
                },
            ],
        }
        return base(
            c,
            runnerLoseCreditsOnBreakPrintedSubroutine=1,
            subroutines=[
                {
                    "id": "gold-farmer-1",
                    "text": "End the run unless the Runner pays 3[credit].",
                    "effect": etr_unless_3,
                },
                {
                    "id": "gold-farmer-2",
                    "text": "End the run unless the Runner pays 3[credit].",
                    "effect": etr_unless_3,
                },
            ],
            unsupported=[],
        )

    if cid == "mantle":
        return base(
            c,
            recurringCreditsMax=1,
            recurringSpendFor=["use_program", "use_hardware"],
            unsupported=[],
        )

    if cid == "false-lead":
        return base(
            c,
            paidAbilities=[
                {
                    "id": "false-lead-forfeit",
                    "label": "Forfeit: if Runner has 2+ [click], they lose [click][click]",
                    "clickCost": 0,
                    "creditCost": 0,
                    "cost": {"trashSelf": True},
                    "windows": ["corp_action_paw"],
                    "effect": {
                        "op": "if",
                        "cond": {
                            "op": "clicks_gte",
                            "side": "runner",
                            "amount": 2,
                        },
                        "then": {
                            "op": "do",
                            "action": {
                                "kind": "lose_clicks",
                                "side": "runner",
                                "amount": 2,
                            },
                        },
                    },
                }
            ],
            unsupported=[],
        )

    if cid == "bellona":
        return base(
            c,
            stealAdditionalCredits=5,
            onScore=gain("corp", 5),
            unsupported=[],
        )

    # --- v1.37.0 B-slice ---

    if cid == "euler":
        return base(
            c,
            breaker={
                "breaksSubtype": "code gate",
                "strength": 2,
                "breakCredits": 2,
                "breakMaxSubs": 2,
                "pumpCredits": 1,
                "pumpStrength": 1,
                "breakViaPaidAbilityOnly": True,
            },
            paidAbilities=[
                {
                    "id": "euler-break-install",
                    "label": "0¢: Break 1 code gate subroutine (installed this turn)",
                    "clickCost": 0,
                    "creditCost": 0,
                    "cost": {"credits": 0},
                    "windows": ["encounter_paw"],
                    "requireInstalledThisTurn": True,
                    "requireEncounterSubtype": "code gate",
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "break_encounter_subroutine",
                            "maxSubs": 1,
                            "requireSubtype": "code gate",
                        },
                    },
                },
                {
                    "id": "euler-break",
                    "label": "2¢: Break up to 2 code gate subroutines",
                    "clickCost": 0,
                    "creditCost": 2,
                    "cost": {"credits": 2},
                    "windows": ["encounter_paw"],
                    "requireEncounterSubtype": "code gate",
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "break_encounter_subroutine",
                            "maxSubs": 2,
                            "requireSubtype": "code gate",
                        },
                    },
                },
                {
                    "id": "euler-pump",
                    "label": "1¢: +1 strength",
                    "clickCost": 0,
                    "creditCost": 1,
                    "cost": {"credits": 1},
                    "windows": ["encounter_paw"],
                    "effect": {
                        "op": "do",
                        "action": {"kind": "pump_strength", "amount": 1},
                    },
                },
            ],
            unsupported=[],
        )

    if cid == "penrose":
        return base(
            c,
            breaker={
                "breaksSubtype": "code gate",
                "strength": 2,
                "breakCredits": 1,
                "breakMaxSubs": 1,
                "pumpCredits": 1,
                "pumpStrength": 3,
                "breakViaPaidAbilityOnly": True,
            },
            paidAbilities=[
                {
                    "id": "penrose-break-barrier",
                    "label": "1¢: Break 1 barrier subroutine (installed this turn)",
                    "clickCost": 0,
                    "creditCost": 1,
                    "cost": {"credits": 1},
                    "windows": ["encounter_paw"],
                    "requireInstalledThisTurn": True,
                    "requireEncounterSubtype": "barrier",
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "break_encounter_subroutine",
                            "maxSubs": 1,
                            "requireSubtype": "barrier",
                        },
                    },
                },
                {
                    "id": "penrose-break-cg",
                    "label": "1¢: Break 1 code gate subroutine",
                    "clickCost": 0,
                    "creditCost": 1,
                    "cost": {"credits": 1},
                    "windows": ["encounter_paw"],
                    "requireEncounterSubtype": "code gate",
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "break_encounter_subroutine",
                            "maxSubs": 1,
                            "requireSubtype": "code gate",
                        },
                    },
                },
                {
                    "id": "penrose-pump",
                    "label": "1¢: +3 strength (stealth credits only)",
                    "clickCost": 0,
                    "creditCost": 1,
                    "cost": {"credits": 1, "creditsFromStealthOnly": True},
                    "windows": ["encounter_paw"],
                    "effect": {
                        "op": "do",
                        "action": {"kind": "pump_strength", "amount": 3},
                    },
                },
            ],
            unsupported=[],
        )

    if cid == "odore":
        return base(
            c,
            breaker={
                "breaksSubtype": "sentry",
                "strength": 0,
                "breakCredits": 2,
                "breakMaxSubs": 99,
                "pumpCredits": 3,
                "pumpStrength": 3,
                "breakViaPaidAbilityOnly": True,
            },
            paidAbilities=[
                {
                    "id": "odore-break-any",
                    "label": "2¢: Break any number of sentry subroutines",
                    "clickCost": 0,
                    "creditCost": 2,
                    "cost": {"credits": 2},
                    "windows": ["encounter_paw"],
                    "requireEncounterSubtype": "sentry",
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "break_encounter_subroutine",
                            "maxSubs": 99,
                            "requireSubtype": "sentry",
                        },
                    },
                },
                {
                    "id": "odore-break-virtual",
                    "label": "0¢: Break 1 sentry (3+ virtual resources)",
                    "clickCost": 0,
                    "creditCost": 0,
                    "cost": {"credits": 0},
                    "windows": ["encounter_paw"],
                    "requireInstalledVirtualResourcesGte": 3,
                    "requireEncounterSubtype": "sentry",
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "break_encounter_subroutine",
                            "maxSubs": 1,
                            "requireSubtype": "sentry",
                        },
                    },
                },
                {
                    "id": "odore-pump",
                    "label": "3¢: +3 strength",
                    "clickCost": 0,
                    "creditCost": 3,
                    "cost": {"credits": 3},
                    "windows": ["encounter_paw"],
                    "effect": {
                        "op": "do",
                        "action": {"kind": "pump_strength", "amount": 3},
                    },
                },
            ],
            unsupported=[],
        )

    if cid == "moshing":
        return base(
            c,
            playRequiresOtherGripCardsGte=3,
            playAdditionalCost={
                "op": "do",
                "action": {"kind": "trash_n_from_grip", "amount": 3},
            },
            onPlay={
                "op": "seq",
                "effects": [
                    gain("runner", 3),
                    {
                        "op": "do",
                        "action": {
                            "kind": "draw",
                            "side": "runner",
                            "amount": 3,
                        },
                    },
                ],
            },
            unsupported=[],
        )

    if cid == "cayambe-grid":
        return base(
            c,
            onTurnBegin={
                "op": "do",
                "action": {
                    "kind": "place_advancements",
                    "amount": 1,
                    "onlyIceProtectingSourceServer": True,
                    "pick": "choose",
                },
            },
            approachServerEtrUnlessCreditsPerAdvancedIce=2,
            unsupported=[],
        )

    if cid == "cyberdex-sandbox":
        return base(
            c,
            onVirusPurgeOncePerTurn=True,
            onVirusPurge=gain("corp", 4),
            onScore={
                "op": "choose",
                "chooser": "corp",
                "options": [
                    {
                        "id": "purge",
                        "label": "Purge virus counters",
                        "effect": {
                            "op": "do",
                            "action": {"kind": "purge_virus_counters"},
                        },
                    },
                    {
                        "id": "decline",
                        "label": "Decline",
                        "effect": {
                            "op": "do",
                            "action": {
                                "kind": "gain_credits",
                                "side": "corp",
                                "amount": 0,
                            },
                        },
                    },
                ],
            },
            unsupported=[],
        )

    if cid == "dreamnet":
        return base(
            c,
            onFirstSuccessfulRunThisTurn={
                "op": "seq",
                "effects": [
                    {
                        "op": "do",
                        "action": {
                            "kind": "draw",
                            "side": "runner",
                            "amount": 1,
                        },
                    },
                    {
                        "op": "if",
                        "cond": {
                            "op": "or",
                            "conds": [
                                {
                                    "op": "identity_has_subtype",
                                    "subtype": "digital",
                                },
                                {"op": "link_gte", "amount": 2},
                            ],
                        },
                        "then": gain("runner", 1),
                    },
                ],
            },
            unsupported=[],
        )

    if cid == "swift":
        return base(
            c,
            muBonus=1,
            gainClickOnFirstRunEventThisTurn=True,
            unsupported=[],
        )

    if cid == "self-modifying-code":
        return base(
            c,
            paidAbilities=[
                {
                    "id": "smc-search",
                    "label": "2¢, [trash]: Search stack for a program and install it",
                    "clickCost": 0,
                    "creditCost": 2,
                    "cost": {"credits": 2, "trashSelf": True},
                    "windows": ["runner_action_paw"],
                    "effect": {
                        "op": "do",
                        "action": {"kind": "search_stack_program_install"},
                    },
                }
            ],
            unsupported=[],
        )

    # Fail closed — honest unsupported note for the remainder.
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

    written = []
    for c in pack:
        mapped = map_card(c)
        cid = mapped["id"]
        path = OUT / f"{cid}.json"
        path.write_text(json.dumps(mapped, indent=2, ensure_ascii=False) + "\n")
        written.append(cid)

    assert len(written) == EXPECTED, len(written)
    assert len(set(written)) == EXPECTED, "duplicate slug ids"

    full = sum(
        1
        for cid in written
        if not json.loads((OUT / f"{cid}.json").read_text()).get("unsupported")
    )
    partial = len(written) - full

    manifest = {
        "pack": WAVE,
        "nrdbPackCode": PACK,
        "count": EXPECTED,
        "written": EXPECTED,
        "status": "in-progress",
        "notes": (
            "Null Signal Uprising (NRDB pack ur) — Ashes set 2 of 2; first "
            "legacy backwards wave before System Gateway. urbp titles absorbed. "
            f"In-progress: {full} cards fully mapped, {partial} with unsupported "
            "notes (wave slice v1.37.0)."
        ),
        "cards": written,
    }
    (OUT / "_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"
    )

    print(f"Wrote {len(written)} cards to {OUT}")
    print(f"Among written: full={full} partial={partial}")
    print("POOL_IDS=" + json.dumps(written))


if __name__ == "__main__":
    main()
