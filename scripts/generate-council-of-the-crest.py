#!/usr/bin/env python3
"""Generate Council of the Crest (cotc) card JSON from pinned pack `cotc`.

Fetch: python3 scripts/nsg_catalog.py fetch cotc
Kitara #3 after Down the White Nile (floor v1.137.0 → v1.138.0).
Reprint skips: none (20/20 new clears).
Follow NSG pack stripped_text (not IR-hint paraphrases).
Slug via spin_common.slugify (Corporate "Grant"→corporate-grant, eXer→exer,
Azmari EdTech: Shaping the Future→azmari-edtech-shaping-the-future,
Kuwinda K4H1U3→kuwinda-k4h1u3, NEXT Sapphire→next-sapphire, TechnoCo→technoco).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from nsg_catalog import load_pack_cards
from spin_common import (
    base,
    do,
    draw,
    etr,
    gain,
    seq,
    slugify,
    write_manifest,
)

OUT = Path(__file__).resolve().parents[1] / "data" / "council-of-the-crest"
WAVE = "council-of-the-crest"
PACK = "cotc"
EXPECTED = 20

REPRINTS: set[str] = set()


def choose(chooser: str, options: list[dict]) -> dict:
    return {"op": "choose", "chooser": chooser, "options": options}


def may(effect: dict, label: str = "Accept", decline_side: str = "runner") -> dict:
    return choose(
        decline_side if decline_side in ("corp", "runner") else "runner",
        [
            {"id": "accept", "label": label, "effect": effect},
            {
                "id": "decline",
                "label": "Decline",
                "effect": gain(
                    decline_side if decline_side in ("corp", "runner") else "runner",
                    0,
                ),
            },
        ],
    )


def paid(
    id_: str,
    label: str,
    effect: dict,
    *,
    clicks: int = 0,
    credits: int = 0,
    windows: list[str] | None = None,
    cost: dict | None = None,
    once_per_turn: bool = False,
    trash_self: bool = False,
    usable_by_runner: bool = False,
    require_pending_damage_types: list[str] | None = None,
) -> dict:
    c = dict(cost or {})
    if clicks:
        c["clicks"] = clicks
    if credits:
        c["credits"] = credits
    if trash_self:
        c["trashSelf"] = True
    ab: dict = {
        "id": id_,
        "label": label,
        "clickCost": clicks,
        "creditCost": credits,
        "cost": c,
        "windows": windows
        or (["encounter_paw"] if usable_by_runner else ["corp_action_paw"]),
        "effect": effect,
    }
    if once_per_turn:
        ab["oncePerTurn"] = True
    if usable_by_runner:
        ab["usableByRunnerOnSelfIce"] = True
    if require_pending_damage_types:
        ab["requirePendingDamageTypes"] = require_pending_damage_types
    return ab


def map_card(c: dict) -> dict | None:
    cid = slugify(c["title"])
    if cid in REPRINTS:
        return None

    if cid == "exer":
        return base(
            c,
            subtypes=["virus"],
            onBreachRd=do("bonus_access", amount=1),
            onVirusPurge=do("trash_self"),
        )

    if cid == "friday-chip":
        return base(
            c,
            subtypes=["chip"],
            mayPlaceVirusCounterWhenCorpCardTrashed=True,
            onTurnBegin=may(
                do("cotc_friday_chip_move_virus"),
                label="Move 1 hosted virus counter to a virus program",
            ),
        )

    if cid == "crypt":
        return base(
            c,
            subtypes=["virtual"],
            onSuccessfulRun={
                "op": "if",
                "cond": {"op": "attacking_archives"},
                "then": may(
                    do("add_virus_counter", amount=1),
                    label="Place 1 virus counter on Crypt",
                ),
            },
            paidAbilities=[
                paid(
                    "crypt-search",
                    "[click], [trash], 3 hosted virus counters: Search stack for a virus program and install it (paying its install cost), then shuffle",
                    do("cotc_crypt_search_install"),
                    clicks=1,
                    trash_self=True,
                    cost={"virusCounters": 3},
                    windows=["runner_action_paw"],
                    usable_by_runner=True,
                ),
            ],
        )

    if cid == "corporate-grant":
        return base(
            c,
            subtypes=["current"],
            lingerAsCurrent=True,
            currentTrashOnAgendaScored=True,
            corpLosesCreditsOnFirstRunnerInstallEachTurn=1,
        )

    if cid == "no-one-home":
        return base(
            c,
            subtypes=["virtual"],
            paidAbilities=[
                paid(
                    "no-one-home-tags",
                    "[interrupt] → [trash]: first tags this turn — Corp Trace[0]; if unsuccessful, prevent all tags",
                    do("cotc_no_one_home", mode="tags"),
                    trash_self=True,
                    once_per_turn=True,
                    windows=["tag_interrupt_paw"],
                    usable_by_runner=True,
                ),
                paid(
                    "no-one-home-net",
                    "[interrupt] → [trash]: first net damage this turn — Corp Trace[0]; if unsuccessful, prevent all net damage",
                    do("cotc_no_one_home", mode="net"),
                    trash_self=True,
                    once_per_turn=True,
                    windows=["damage_interrupt_paw"],
                    usable_by_runner=True,
                    require_pending_damage_types=["net"],
                ),
            ],
        )

    if cid == "marathon":
        return base(
            c,
            subtypes=["run"],
            runEvent={
                "servers": "remote",
                "onRunEnd": {
                    "op": "if",
                    "cond": {"op": "run_successful"},
                    "then": do("cotc_marathon_resolve"),
                },
            },
        )

    if cid == "gbahali":
        return base(
            c,
            subtypes=["virtual"],
            paidAbilities=[
                paid(
                    "gbahali-break",
                    "[trash]: Break the last subroutine on the encountered piece of ice",
                    do("break_last_subroutine"),
                    trash_self=True,
                    windows=["encounter_paw"],
                    usable_by_runner=True,
                ),
            ],
        )

    if cid == "white-hat":
        return base(
            c,
            playRequiresSuccessfulCentralRunThisTurn=True,
            onPlay=do("cotc_white_hat"),
        )

    if cid == "kuwinda-k4h1u3":
        return base(
            c,
            subtypes=["bioroid"],
            onTurnBegin=may(
                do("cotc_kuwinda_trace"),
                label="Trace[X] (X = hosted power counters)",
                decline_side="corp",
            ),
        )

    if cid == "next-sapphire":
        return base(
            c,
            subtypes=["code gate", "next"],
            subroutines=[
                {
                    "id": "next-sapphire-draw",
                    "text": "Draw up to X cards.",
                    "effect": do("cotc_next_sapphire_draw"),
                },
                {
                    "id": "next-sapphire-archives",
                    "text": "Add up to X cards from Archives to HQ.",
                    "effect": do("cotc_next_sapphire_archives_to_hq"),
                },
                {
                    "id": "next-sapphire-shuffle",
                    "text": "Shuffle up to X cards from HQ into R&D.",
                    "effect": do("cotc_next_sapphire_hq_to_rd"),
                },
            ],
        )

    if cid == "anansi":
        return base(
            c,
            subtypes=["sentry", "ap"],
            onEncounterEndIfNotFullyBroken=do("net_damage", amount=3),
            subroutines=[
                {
                    "id": "anansi-arrange",
                    "text": "Look at the top 5 cards of R&D and arrange them in any order.",
                    "effect": do("cotc_anansi_arrange_rd", amount=5),
                },
                {
                    "id": "anansi-draw",
                    "text": "You may draw 1 card. The Runner may pay 2 credits to draw 1 card.",
                    "effect": seq(
                        may(draw("corp", 1), label="Draw 1 card", decline_side="corp"),
                        may(
                            seq(
                                do("lose_credits", side="runner", amount=2),
                                draw("runner", 1),
                            ),
                            label="Pay 2¢ to draw 1 card",
                        ),
                    ),
                },
                {
                    "id": "anansi-net",
                    "text": "Do 1 net damage.",
                    "effect": do("net_damage", amount=1),
                },
            ],
        )

    if cid == "code-replicator":
        return base(
            c,
            onPassRezzedIceProtectingThisServer=may(
                do("cotc_code_replicator"),
                label="Trash Code Replicator: Runner approaches that ice again (may jack out)",
                decline_side="corp",
            ),
        )

    if cid == "reverse-infection":
        return base(
            c,
            onPlay=choose(
                "corp",
                [
                    {
                        "id": "purge",
                        "label": "Purge virus counters; trash 1 from stack top per 3 purged",
                        "effect": do("cotc_reverse_infection_purge"),
                    },
                    {
                        "id": "credits",
                        "label": "Gain 2¢",
                        "effect": gain("corp", 2),
                    },
                ],
            ),
        )

    if cid == "azmari-edtech-shaping-the-future":
        return base(
            c,
            subtypes=["division"],
            onCorpTurnEnd=may(
                do("cotc_azmari_name_card_type"),
                label="Name a card type",
                decline_side="corp",
            ),
            gainCreditsOnFirstRunnerPlayOrInstallNamedType=2,
        )

    if cid == "degree-mill":
        return base(
            c,
            subtypes=["initiative"],
            stealAdditionalCost=do("shuffle_n_installed_runner_into_stack", amount=2),
        )

    if cid == "personalized-portal":
        return base(
            c,
            onTurnBegin=seq(
                draw("runner", 1),
                may(
                    do("cotc_personalized_portal_gain"),
                    label="Gain 1¢ for every 2 cards in the grip",
                    decline_side="corp",
                ),
            ),
        )

    if cid == "armed-intimidation":
        return base(
            c,
            subtypes=["security"],
            onScore=choose(
                "runner",
                [
                    {
                        "id": "meat",
                        "label": "Suffer 5 meat damage",
                        "effect": do("meat_damage", amount=5),
                    },
                    {
                        "id": "tags",
                        "label": "Take 2 tags",
                        "effect": do("give_tags", amount=2),
                    },
                ],
            ),
        )

    if cid == "death-and-taxes":
        return base(
            c,
            subtypes=["current", "transaction"],
            lingerAsCurrent=True,
            currentTrashOnAgendaStolen=True,
            mayGainCreditWhenRunnerInstallsOrTrashesInstalled=True,
        )

    if cid == "trojan-horse":
        return base(
            c,
            subtypes=["gray ops"],
            playRequiresRunnerAccessedCardLastTurn=True,
            onPlay=do(
                "trace",
                strength=4,
                onSuccess=do("cotc_trojan_horse_trash"),
            ),
        )

    if cid == "technoco":
        return base(
            c,
            subtypes=["corporation"],
            programInstallCostIncrease=1,
            hardwareInstallCostIncrease=1,
            virtualResourceInstallCostIncrease=1,
            mayGainCreditWhenRunnerInstallsProgramHardwareOrVirtual=True,
        )

    card = base(c)
    card["unsupported"] = [f"Unmapped in card: {cid}"]
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
    print("SKIPPED=" + json.dumps(skipped))
    if len(clear_written) != EXPECTED - len(REPRINTS):
        missing = [cid for cid in written if cid not in clear_written]
        print("UNCLEARED=" + json.dumps(missing))
        sys.exit(1)


if __name__ == "__main__":
    main()
