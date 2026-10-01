#!/usr/bin/env python3
"""Generate Down the White Nile (dtwn) card JSON from pinned pack `dtwn`.

Fetch: python3 scripts/nsg_catalog.py fetch dtwn
Kitara #2 after Sovereign Sight (floor v1.136.0 → v1.137.0).
Reprint skips: none (20/20 new clears).
Follow NSG pack stripped_text (not IR-hint paraphrases).
Slug via spin_common.slugify (Kabonesa Wu: Netspace Thrillseeker→kabonesa-wu-netspace-thrillseeker).
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

OUT = Path(__file__).resolve().parents[1] / "data" / "down-the-white-nile"
WAVE = "down-the-white-nile"
PACK = "dtwn"
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
    return ab


def map_card(c: dict) -> dict | None:
    cid = slugify(c["title"])
    if cid in REPRINTS:
        return None

    if cid == "acacia":
        return base(
            c,
            onVirusPurge=may(
                seq(
                    do("dtwn_gain_credits_equal_to_last_purged_viruses"),
                    do("trash_self"),
                ),
                label="Gain 1¢ per virus purged and trash Acacia",
            ),
        )

    if cid == "plague":
        return base(
            c,
            subtypes=["virus"],
            onInstall=do("choose_server_runner"),
            onSuccessfulRun={
                "op": "if",
                "cond": {"op": "attacking_chosen_server"},
                "then": may(
                    do("add_virus_counter", amount=2),
                    label="Place 2 virus counters on Plague",
                ),
            },
        )

    if cid == "credit-kiting":
        return base(
            c,
            playRequiresSuccessfulCentralRunThisTurn=True,
            onPlay=seq(
                do(
                    "install_from_grip_discount",
                    types=["program", "hardware", "resource"],
                    discount=8,
                ),
                do("give_tags", amount=1),
            ),
        )

    if cid == "wari":
        return base(
            c,
            onFirstSuccessfulHqRunThisTurn=may(
                do("dtwn_wari"),
                label="Trash Wari: name subtype, expose ice, bounce if named",
            ),
        )

    if cid == "kabonesa-wu-netspace-thrillseeker":
        return base(
            c,
            subtypes=["g-mod"],
            link=c.get("base_link", 1),
            paidAbilities=[
                paid(
                    "kabonesa-search",
                    "[click]: Search stack for a non-virus program and install it, lowering install cost by 1¢; RFG it if still installed at turn end",
                    do("dtwn_kabonesa_search_install"),
                    clicks=1,
                    windows=["runner_action_paw"],
                    usable_by_runner=True,
                ),
            ],
        )

    if cid == "takobi":
        return base(
            c,
            onFullyBreak=may(
                do("add_power_counter", amount=1),
                label="Place 1 power counter on Takobi",
            ),
            paidAbilities=[
                paid(
                    "takobi-pump",
                    "2 hosted power counters: Choose 1 installed non-AI icebreaker. That icebreaker gets +3 strength for the remainder of the current encounter",
                    do("dtwn_takobi_pump_breaker", amount=3),
                    cost={"powerCounters": 2},
                    windows=["encounter_paw"],
                    usable_by_runner=True,
                ),
            ],
        )

    if cid == "kongamato":
        return base(
            c,
            subtypes=["virtual"],
            paidAbilities=[
                paid(
                    "kongamato-break",
                    "[trash]: Break the first subroutine on the encountered piece of ice",
                    do("dtwn_break_first_subroutine"),
                    trash_self=True,
                    windows=["encounter_paw"],
                    usable_by_runner=True,
                ),
            ],
        )

    if cid == "emergent-creativity":
        return base(
            c,
            subtypes=["double"],
            playAdditionalClick=True,
            onPlay=do("dtwn_emergent_creativity"),
        )

    if cid == "rng-key":
        return base(
            c,
            onFirstSuccessfulHqOrRdRunThisTurn=may(
                do("dtwn_rng_key"),
                label="Name a number (reveal next access this run)",
            ),
        )

    if cid == "nightdancer":
        return base(
            c,
            subtypes=["code gate"],
            subroutines=[
                {
                    "id": "nightdancer-1",
                    "text": "The Runner loses [click], if able. You have an additional [click] to spend during your next turn.",
                    "effect": seq(
                        do("lose_clicks", side="runner", amount=1),
                        do("dtwn_corp_additional_click_next_turn"),
                    ),
                },
                {
                    "id": "nightdancer-2",
                    "text": "The Runner loses [click], if able. You have an additional [click] to spend during your next turn.",
                    "effect": seq(
                        do("lose_clicks", side="runner", amount=1),
                        do("dtwn_corp_additional_click_next_turn"),
                    ),
                },
            ],
        )

    if cid == "jinja-city-grid":
        return base(
            c,
            subtypes=["region"],
            limitOnePerServer=True,
            onDrawIceMayRevealAndInstallProtectingThisServerPayingLess=4,
        )

    if cid == "aimor":
        return base(
            c,
            subtypes=["trap"],
            subroutines=[
                {
                    "id": "aimor-trash",
                    "text": "Trash the top 3 cards of the stack. Trash Aimor.",
                    "effect": seq(
                        do("trash_top_of_stack"),
                        do("trash_top_of_stack"),
                        do("trash_top_of_stack"),
                        do("trash_self"),
                    ),
                },
            ],
        )

    if cid == "bacterial-programming":
        return base(
            c,
            subtypes=["research"],
            onScore=may(
                do("dtwn_bacterial_programming"),
                label="Look at top 7 of R&D; HQ/trash/arrange",
                decline_side="corp",
            ),
            onSteal=may(
                do("dtwn_bacterial_programming"),
                label="Look at top 7 of R&D; HQ/trash/arrange",
                decline_side="corp",
            ),
        )

    if cid == "jua":
        return base(
            c,
            subtypes=["sentry"],
            onEncounter=do("dtwn_jua_forbid_install_remainder_of_turn"),
            subroutines=[
                {
                    "id": "jua-bounce",
                    "text": "Choose 2 installed Runner cards, if able. The Runner must add 1 of the chosen cards to the top of the stack.",
                    "effect": do("dtwn_jua_choose_two_bounce_one"),
                },
            ],
        )

    if cid == "threat-assessment":
        return base(
            c,
            subtypes=["reprisal", "gray ops"],
            playRequiresRunnerTrashedCorpCardLastTurn=True,
            playRequiresRunnerHasInstalledCard=True,
            rfgInsteadOfTrashing=True,
            onPlay=do("dtwn_threat_assessment"),
        )

    if cid == "economic-warfare":
        return base(
            c,
            subtypes=["gray ops"],
            playRequiresSuccessfulRunLastTurn=True,
            onPlay={
                "op": "if",
                "cond": {"op": "credits_gte", "side": "runner", "amount": 4},
                "then": do("lose_credits", side="runner", amount=4),
            },
        )

    if cid == "forced-connection":
        return base(
            c,
            subtypes=["ambush"],
            mustRevealWhenAccessedFromRd=True,
            skipOnAccessFromArchives=True,
            onAccess=do(
                "trace",
                strength=3,
                onSuccess=do("give_tags", amount=2),
            ),
        )

    if cid == "ssl-endorsement":
        return base(
            c,
            subtypes=["initiative"],
            onScore=do("place_hosted_credits", amount=9),
            onSteal=do("place_hosted_credits", amount=9),
            onTurnBeginFromRunnerScoreOnCorpTurn=True,
            onTurnBegin=may(
                do("take_hosted_credits", amount=3),
                label="Take 3¢ from SSL Endorsement",
                decline_side="corp",
            ),
        )

    if cid == "ngo-front":
        return base(
            c,
            canAdvance=True,
            paidAbilities=[
                paid(
                    "ngo-5",
                    "[trash], 1 hosted advancement token: Gain 5¢",
                    gain("corp", 5),
                    trash_self=True,
                    cost={"advancementTokens": 1},
                    windows=["corp_action_paw"],
                ),
                paid(
                    "ngo-8",
                    "[trash], 2 hosted advancement tokens: Gain 8¢",
                    gain("corp", 8),
                    trash_self=True,
                    cost={"advancementTokens": 2},
                    windows=["corp_action_paw"],
                ),
            ],
        )

    if cid == "distract-the-masses":
        return base(
            c,
            rfgInsteadOfTrashing=True,
            onPlay=seq(
                gain("runner", 2),
                do("dtwn_distract_trash_hq_shuffle_archives"),
            ),
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
