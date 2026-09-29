#!/usr/bin/env python3
"""Generate Downfall card JSON from pinned pack `df`.

Catalog source: Null-Signal-Games/netrunner-cards-json (see data/nrdb-catalog-pin.json).
Fetch with: python3 scripts/nrdb_catalog.py fetch df

Downfall is Ashes set 1 of 2 (Uprising is set 2). Magnum Opus Reprint (`mor`)
is skipped/absorbed — not a corpus wave.

Hand-mapped Effect IR only where existing primitives fully cover the card;
everything else lists honest unsupported notes — never invent IR.

Usage: python3 scripts/generate-downfall.py
"""
from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

from nrdb_catalog import load_pack_cards

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "downfall"
WAVE = "downfall"
PACK = "df"
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


def draw(side: str, n: int):
    return {"op": "do", "action": {"kind": "draw", "side": side, "amount": n}}


def decline(side: str):
    return {
        "id": "decline",
        "label": "Decline",
        "effect": gain(side, 0),
    }


def may_draw(side: str, n: int = 1):
    return {
        "op": "choose",
        "chooser": side,
        "options": [
            {
                "id": "draw",
                "label": f"Draw {n} card" + ("s" if n != 1 else ""),
                "effect": draw(side, n),
            },
            decline(side),
        ],
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

    # --- v1.47.0 kickoff: existing IR only ---

    if cid == "rezeki":
        return base(
            c,
            onTurnBegin=gain("runner", 1),
            unsupported=[],
        )

    if cid == "bukhgalter":
        return breaker_card(
            c,
            "sentry",
            1,
            1,
            1,
            1,
            break_max=1,
            onFullyBreakOncePerTurn=gain("runner", 2),
            unsupported=[],
        )

    if cid == "tiered-subscription":
        return base(
            c,
            onFirstRunBeginThisTurn=gain("corp", 1),
            unsupported=[],
        )

    if cid == "isolation":
        return base(
            c,
            playRequiresInstalledResource=True,
            playAdditionalCost={
                "op": "do",
                "action": {"kind": "trash_own_resource"},
            },
            onPlay=gain("runner", 7),
            unsupported=[],
        )

    if cid == "csr-campaign":
        return base(
            c,
            onTurnBegin=may_draw("corp", 1),
            unsupported=[],
        )

    # --- v1.48.0 A-slice ---

    if cid == "congratulations":
        return base(
            c,
            onPass=gain("corp", 1),
            subroutines=[
                {
                    "id": "congratulations-credits",
                    "text": "Gain 2[credit]. The Runner gains 1[credit].",
                    "effect": {
                        "op": "seq",
                        "effects": [
                            gain("corp", 2),
                            gain("runner", 1),
                        ],
                    },
                }
            ],
            unsupported=[],
        )

    if cid == "gauss":
        return breaker_card(
            c,
            "barrier",
            1,
            1,
            2,
            2,
            break_max=1,
            onInstall={
                "op": "do",
                "action": {"kind": "gain_strength_this_turn", "amount": 3},
            },
            unsupported=[],
        )

    if cid == "spec-work":
        return base(
            c,
            playRequiresInstalledProgram=True,
            playAdditionalCost={
                "op": "do",
                "action": {"kind": "trash_own_program"},
            },
            onPlay={
                "op": "seq",
                "effects": [
                    gain("runner", 4),
                    draw("runner", 2),
                ],
            },
            unsupported=[],
        )

    if cid == "nanoetching-matrix":
        return base(
            c,
            paidAbilities=[
                {
                    "id": "nanoetching-matrix-gain",
                    "label": "[click]: Gain 2¢",
                    "clickCost": 1,
                    "creditCost": 0,
                    "cost": {"clicks": 1},
                    "windows": ["corp_action_paw"],
                    "oncePerTurn": True,
                    "effect": gain("corp", 2),
                }
            ],
            onTrash={
                "op": "choose",
                "chooser": "corp",
                "options": [
                    {
                        "id": "gain",
                        "label": "Gain 2¢",
                        "effect": gain("corp", 2),
                    },
                    decline("corp"),
                ],
            },
            unsupported=[],
        )

    if cid == "sandstone":
        return base(
            c,
            onEncounter={
                "op": "do",
                "action": {"kind": "add_virus_counter", "amount": 1},
            },
            strengthPerVirusCounter=-1,
            subroutines=[
                {
                    "id": "sandstone-etr",
                    "text": "End the run.",
                    "effect": {
                        "op": "do",
                        "action": {"kind": "end_the_run"},
                    },
                }
            ],
            unsupported=[],
        )

    # --- v1.49.0 B-slice ---

    if cid == "vulnerability-audit":
        return base(
            c,
            cannotScoreIfInstalledThisTurn=True,
            unsupported=[],
        )

    if cid == "calvin-b4l3y":
        return base(
            c,
            paidAbilities=[
                {
                    "id": "calvin-b4l3y-draw",
                    "label": "[click]: Draw 2 cards",
                    "clickCost": 1,
                    "creditCost": 0,
                    "cost": {"clicks": 1},
                    "windows": ["corp_action_paw"],
                    "oncePerTurn": True,
                    "effect": draw("corp", 2),
                }
            ],
            onTrash=may_draw("corp", 2),
            unsupported=[],
        )

    if cid == "remastered-edition":
        return base(
            c,
            onScore={
                "op": "do",
                "action": {"kind": "add_agenda_counter", "amount": 1},
            },
            paidAbilities=[
                {
                    "id": "remastered-edition-advance",
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

    if cid == "roughneck-repair-squad":
        return base(
            c,
            paidAbilities=[
                {
                    "id": "roughneck-repair-squad-main",
                    "label": "[click][click][click]: Gain 6¢. You may remove 1 bad publicity.",
                    "clickCost": 3,
                    "creditCost": 0,
                    "cost": {"clicks": 3},
                    "windows": ["corp_action_paw"],
                    "effect": {
                        "op": "seq",
                        "effects": [
                            gain("corp", 6),
                            {
                                "op": "choose",
                                "chooser": "corp",
                                "options": [
                                    {
                                        "id": "remove-bp",
                                        "label": "Remove 1 bad publicity",
                                        "effect": {
                                            "op": "do",
                                            "action": {
                                                "kind": "remove_bad_publicity",
                                                "amount": 1,
                                            },
                                        },
                                    },
                                    decline("corp"),
                                ],
                            },
                        ],
                    },
                }
            ],
            unsupported=[],
        )

    if cid == "the-artist":
        return base(
            c,
            paidAbilities=[
                {
                    "id": "the-artist-gain",
                    "label": "[click]: Gain 2¢",
                    "clickCost": 1,
                    "creditCost": 0,
                    "cost": {"clicks": 1},
                    "windows": ["runner_action_paw"],
                    "oncePerTurn": True,
                    "effect": gain("runner", 2),
                },
                {
                    "id": "the-artist-install",
                    "label": "[click]: Install program or hardware, paying 1¢ less",
                    "clickCost": 1,
                    "creditCost": 0,
                    "cost": {"clicks": 1},
                    "windows": ["runner_action_paw"],
                    "oncePerTurn": True,
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "install_from_grip_discount",
                            "types": ["program", "hardware"],
                            "discount": 1,
                        },
                    },
                },
            ],
            unsupported=[],
        )

    # --- v1.50.0 C-slice ---

    if cid == "increased-drop-rates":
        return base(
            c,
            mustRevealWhenAccessedFromRd=True,
            onAccess={
                "op": "choose",
                "chooser": "runner",
                "options": [
                    {
                        "id": "take-tag",
                        "label": "Take 1 tag",
                        "effect": {
                            "op": "do",
                            "action": {"kind": "give_tags", "amount": 1},
                        },
                    },
                    {
                        "id": "allow-remove-bp",
                        "label": "Allow Corp to remove 1 bad publicity",
                        "effect": {
                            "op": "do",
                            "action": {
                                "kind": "remove_bad_publicity",
                                "amount": 1,
                            },
                        },
                    },
                ],
            },
            unsupported=[],
        )

    if cid == "red-level-clearance":
        return base(
            c,
            onPlay={
                "op": "do",
                "action": {
                    "kind": "choose_exactly_n",
                    "n": 2,
                    "options": [
                        {
                            "id": "draw",
                            "label": "Draw 2 cards",
                            "effect": draw("corp", 2),
                        },
                        {
                            "id": "credits",
                            "label": "Gain 2¢",
                            "effect": gain("corp", 2),
                        },
                        {
                            "id": "install",
                            "label": "Install 1 non-agenda card from HQ",
                            "effect": {
                                "op": "do",
                                "action": {
                                    "kind": "may_install_from_hq_paying_costs",
                                    "excludeAgenda": True,
                                },
                            },
                        },
                        {
                            "id": "click",
                            "label": "Gain [click]",
                            "effect": {
                                "op": "do",
                                "action": {
                                    "kind": "gain_clicks",
                                    "side": "corp",
                                    "amount": 1,
                                },
                            },
                        },
                    ],
                },
            },
            unsupported=[],
        )

    if cid == "afshar":
        return base(
            c,
            onEncounter={
                "op": "if",
                "cond": {"op": "attacking_hq"},
                "then": {
                    "op": "do",
                    "action": {
                        "kind": "limit_printed_breaks_on_source_for_run",
                        "max": 1,
                    },
                },
            },
            subroutines=[
                {
                    "id": "afshar-lose",
                    "text": "The Runner loses 2[credit].",
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "lose_credits",
                            "side": "runner",
                            "amount": 2,
                        },
                    },
                },
                {
                    "id": "afshar-etr",
                    "text": "End the run.",
                    "effect": {
                        "op": "do",
                        "action": {"kind": "end_the_run"},
                    },
                },
            ],
            unsupported=[],
        )

    if cid == "hagen":
        return base(
            c,
            strengthBonusPerIcebreaker=-1,
            subroutines=[
                {
                    "id": "hagen-trash",
                    "text": "Trash 1 installed program that is not a decoder, fracter, or killer.",
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "trash_program",
                            "pick": "choose",
                            "excludeSubtypes": [
                                "decoder",
                                "fracter",
                                "killer",
                            ],
                        },
                    },
                },
                {
                    "id": "hagen-etr",
                    "text": "End the run.",
                    "effect": {
                        "op": "do",
                        "action": {"kind": "end_the_run"},
                    },
                },
            ],
            unsupported=[],
        )

    if cid == "sds-drone-deployment":
        return base(
            c,
            stealAdditionalCost={
                "op": "do",
                "action": {"kind": "trash_own_program"},
            },
            onScore={
                "op": "do",
                "action": {
                    "kind": "trash_program",
                    "pick": "choose",
                },
            },
            unsupported=[],
        )

    # --- v1.51.0 D-slice ---

    if cid == "supercorridor":
        return base(
            c,
            muBonus=2,
            handSizeBonus=1,
            onRunnerTurnEnd={
                "op": "if",
                "cond": {"op": "credits_eq_other_side", "side": "runner"},
                "then": {
                    "op": "choose",
                    "chooser": "runner",
                    "options": [
                        {
                            "id": "gain",
                            "label": "Gain 2¢",
                            "effect": gain("runner", 2),
                        },
                        decline("runner"),
                    ],
                },
            },
            unsupported=[],
        )

    if cid == "public-health-portal":
        return base(
            c,
            onTurnBegin={
                "op": "seq",
                "effects": [
                    {
                        "op": "do",
                        "action": {"kind": "reveal_top_of_rd"},
                    },
                    gain("corp", 2),
                ],
            },
            unsupported=[],
        )

    if cid == "demolisher":
        return base(
            c,
            muBonus=1,
            corpCardTrashCostReduction=1,
            onFirstCorpCardTrashEachTurn=gain("runner", 1),
            unsupported=[],
        )

    if cid == "flip-switch":
        return base(
            c,
            paidAbilities=[
                {
                    "id": "flip-switch-jack-out",
                    "label": "[trash]: Jack out",
                    "clickCost": 0,
                    "creditCost": 0,
                    "cost": {"trashSelf": True},
                    "requireDuringRun": True,
                    "windows": [
                        "approach_paw",
                        "encounter_paw",
                        "approach_server_paw",
                    ],
                    "effect": {
                        "op": "do",
                        "action": {"kind": "end_the_run"},
                    },
                },
                {
                    "id": "flip-switch-remove-tag",
                    "label": "[trash]: Remove 1 tag",
                    "clickCost": 0,
                    "creditCost": 0,
                    "cost": {"trashSelf": True},
                    "windows": ["runner_action_paw"],
                    "effect": {
                        "op": "do",
                        "action": {"kind": "remove_tags", "amount": 1},
                    },
                },
                {
                    "id": "flip-switch-trace",
                    "label": "[interrupt] → [trash]: Reduce base trace strength to 0",
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
                },
            ],
            unsupported=[],
        )

    if cid == "fully-operational":
        return base(
            c,
            onPlay={
                "op": "do",
                "action": {"kind": "fully_operational_resolve"},
            },
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

    status = "supported" if partial == 0 else "in-progress"
    notes = (
        "Null Signal Downfall (NRDB pack df) — Ashes set 1 of 2; legacy "
        "backwards wave before Uprising / System Gateway. Skip Magnum Opus "
        f"Reprint (mor). In-progress: {full} cards fully mapped, {partial} "
        "with unsupported notes (D-slice v1.51.0)."
    )
    manifest = {
        "pack": WAVE,
        "nrdbPackCode": PACK,
        "count": EXPECTED,
        "written": EXPECTED,
        "status": status,
        "notes": notes,
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
