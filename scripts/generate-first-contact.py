#!/usr/bin/env python3
"""Generate First Contact (fc) card JSON from pinned pack `fc`.

Fetch: python3 scripts/nrdb_catalog.py fetch fc
Lunar cycle after The Spaces Between (floor v1.103.0 → v1.104.0).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from nrdb_catalog import load_pack_cards
from spin_common import (
    base,
    breaker_card,
    do,
    draw,
    etr,
    gain,
    seq,
    slugify,
    trace_sub,
    write_manifest,
)

OUT = Path(__file__).resolve().parents[1] / "data" / "first-contact"
WAVE = "first-contact"
PACK = "fc"
EXPECTED = 20

REPRINTS = {
    "crisium-grid",
    "quetzal-free-spirit",
}


def current_corp(c, **extra):
    return base(
        c,
        subtypes=["current"],
        lingerAsCurrent=True,
        currentTrashOnAgendaStolen=True,
        **extra,
    )


def map_card(c: dict) -> dict | None:
    cid = slugify(c["title"])
    if cid in REPRINTS:
        return None

    if cid == "iq":
        return base(
            c,
            subtypes=["code gate"],
            strengthPerCorpCardInHq=1,
            rezCostIncreasePerCorpCardInHq=1,
            subroutines=[
                {"id": "iq-etr", "text": "End the run.", "effect": etr()}
            ],
        )

    if cid == "elizas-toybox":
        return base(
            c,
            paidAbilities=[
                {
                    "id": "eliza-rez",
                    "label": "[click][click][click]: Rez a card, ignoring all costs",
                    "clickCost": 3,
                    "creditCost": 0,
                    "cost": {"clicks": 3},
                    "windows": ["corp_action_paw"],
                    "effect": do("rez_ice_ignoring_costs"),
                }
            ],
        )

    if cid == "kitsune":
        return base(
            c,
            subtypes=["trap"],
            subroutines=[
                {
                    "id": "kitsune-breach",
                    "text": "Choose 1 card in HQ; breach HQ with forced access",
                    "effect": do("kitsune_breach_hq"),
                }
            ],
        )

    if cid == "port-anson-grid":
        return base(
            c,
            subtypes=["region"],
            limitOnePerServer=True,
            jackOutOnThisServerTrashRunnerProgram=True,
        )

    if cid == "the-news-now-hour":
        return base(c, runnerCannotPlayCurrentEvents=True)

    if cid == "manhunt":
        return current_corp(
            c,
            onFirstSuccessfulRunThisTurn=trace_sub(
                2,
                do("give_tags", amount=1),
            ),
        )

    if cid == "wendigo":
        return base(
            c,
            subtypes=["code gate", "morph"],
            morphOddAdvancementSubtypeSwap={"gain": "barrier", "lose": "code gate"},
            subroutines=[
                {
                    "id": "wendigo-ban",
                    "text": "Choose a program; Runner cannot use it this run",
                    "effect": do("wendigo_ban_program"),
                }
            ],
        )

    if cid == "chronos-project":
        return base(
            c,
            subtypes=["research"],
            onScore=do("rfg_runner_heap"),
        )

    if cid == "shattered-remains":
        return base(
            c,
            subtypes=["ambush"],
            onAccess=do("shattered_remains_access"),
        )

    if cid == "lancelot":
        return base(
            c,
            subtypes=["sentry", "grail", "destroyer"],
            onEncounter=do("grail_reveal_gain_subroutines", maxReveal=2),
            subroutines=[
                {
                    "id": "lancelot-trash",
                    "text": "Trash 1 installed program",
                    "effect": do("trash_one_installed_runner_program"),
                }
            ],
        )

    if cid == "blackat":
        card = breaker_card(c, "barrier", 3, 1, 2, 1)
        card["paidAbilities"] = [
            {
                "id": "blackat-break",
                "label": "1¢: Break 1 barrier subroutine (up to 3 if stealth paid)",
                "clickCost": 0,
                "creditCost": 1,
                "cost": {"credits": 1},
                "windows": ["encounter_paw"],
                "requireEncounterSubtype": "barrier",
                "effect": do("blackat_break_barrier"),
            },
            {
                "id": "blackat-pump",
                "label": "2¢: +1 strength (+2 if stealth paid)",
                "clickCost": 0,
                "creditCost": 2,
                "cost": {"credits": 2},
                "windows": ["encounter_paw"],
                "effect": do("blackat_pump_strength"),
            },
        ]
        card["breaker"]["breakViaPaidAbilityOnly"] = True
        return card

    if cid == "duggars":
        return base(
            c,
            subtypes=["location", "seedy"],
            paidAbilities=[
                {
                    "id": "duggars-draw",
                    "label": "[click]×4: Draw 10 cards",
                    "clickCost": 4,
                    "creditCost": 0,
                    "cost": {"clicks": 4},
                    "windows": ["runner_action_paw"],
                    "effect": draw("runner", 10),
                }
            ],
        )

    if cid == "box-e":
        return base(
            c,
            subtypes=["console"],
            muBonus=2,
            handSizeBonus=2,
            maxConsole=1,
            unique=True,
        )

    if cid == "the-supplier":
        return base(
            c,
            subtypes=["connection"],
            unique=True,
            supplierHost=True,
            paidAbilities=[
                {
                    "id": "supplier-host",
                    "label": "[click]: Host a resource or hardware from grip",
                    "clickCost": 1,
                    "creditCost": 0,
                    "cost": {"clicks": 1},
                    "windows": ["runner_action_paw"],
                    "effect": do("supplier_host_from_grip"),
                }
            ],
            onTurnBegin=do("supplier_turn_begin_install"),
        )

    if cid == "refractor":
        card = breaker_card(c, "code gate", 2, 1, 1, 3)
        card["paidAbilitiesUseStealthCreditsOnly"] = True
        card["paidAbilities"] = [
            {
                "id": "refractor-break",
                "label": "1¢ (stealth): Break 1 code gate subroutine",
                "clickCost": 0,
                "creditCost": 1,
                "cost": {"credits": 1, "creditsFromStealthOnly": True},
                "windows": ["encounter_paw"],
                "requireEncounterSubtype": "code gate",
                "effect": do(
                    "break_encounter_subroutine",
                    maxSubs=1,
                    requireSubtype="code gate",
                ),
            },
            {
                "id": "refractor-pump",
                "label": "1¢ (stealth): +3 strength",
                "clickCost": 0,
                "creditCost": 1,
                "cost": {"credits": 1, "creditsFromStealthOnly": True},
                "windows": ["encounter_paw"],
                "effect": do("pump_strength", amount=3),
            },
        ]
        card["breaker"]["breakViaPaidAbilityOnly"] = True
        return card

    if cid == "order-of-sol":
        return base(
            c,
            subtypes=["location"],
            unique=True,
            onFirstRunnerCreditPoolEmptyThisTurn=gain("runner", 1),
        )

    if cid == "hades-shard":
        return base(
            c,
            subtypes=["virtual", "source"],
            deckLimitOne=True,
            onGripArchivesSuccessInstallSelfIgnoringCosts=True,
            paidAbilities=[
                {
                    "id": "hades-breach",
                    "label": "[trash]: Breach Archives (no root access)",
                    "clickCost": 0,
                    "creditCost": 0,
                    "cost": {"trashSelf": True},
                    "windows": ["runner_action_paw", "encounter_paw"],
                    "effect": do("hades_shard_breach_archives"),
                }
            ],
        )

    if cid == "rachel-beckman":
        return base(
            c,
            subtypes=["connection"],
            unique=True,
            allottedClicksBonus=1,
            trashSelfWhenRunnerTagged=True,
        )

    card = base(c)
    card["unsupported"] = [f"Unmapped fc card: {cid}"]
    return card


def main():
    pack = sorted(load_pack_cards(PACK), key=lambda c: c.get("position", 0))
    assert len(pack) == EXPECTED, len(pack)
    OUT.mkdir(parents=True, exist_ok=True)
    written: list[str] = []
    skipped: list[str] = []
    for raw in pack:
        cid = slugify(raw["title"])
        mapped = map_card(raw)
        if mapped is None:
            skipped.append(cid)
            continue
        mapped["wave"] = WAVE
        path = OUT / f"{cid}.json"
        path.write_text(json.dumps(mapped, indent=2, ensure_ascii=False) + "\n")
        written.append(cid)

    pool_ids = [slugify(c["title"]) for c in pack]
    clear_written = [
        cid
        for cid in written
        if not json.loads((OUT / f"{cid}.json").read_text()).get("unsupported")
    ]
    write_manifest(OUT, WAVE, PACK, EXPECTED, pool_ids, written, skipped, clear_written)
    print(f"Wrote {len(written)}; skipped {len(skipped)}; clears {len(clear_written)}")
    print("CLEARS=" + json.dumps(clear_written))


if __name__ == "__main__":
    main()
