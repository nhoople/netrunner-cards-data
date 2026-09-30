#!/usr/bin/env python3
"""Generate Sovereign Sight (ss) card JSON from pinned pack `ss`.

Fetch: python3 scripts/nrdb_catalog.py fetch ss
Kitara #1 after Revised Core (floor v1.135.0 → v1.136.0).
Reprint skips: none (20/20 new clears).
Follow NRDB stripped_text (not IR-hint paraphrases).
Slug via spin_common.slugify (Lewi Guilherme→lewi-guilherme, Najja 1.0→najja-1-0).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from nrdb_catalog import load_pack_cards
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

OUT = Path(__file__).resolve().parents[1] / "data" / "sovereign-sight"
WAVE = "sovereign-sight"
PACK = "ss"
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


def breaker(
    c: dict,
    *,
    breaks: str,
    break_credits: int,
    break_max: int = 1,
    pump_credits: int | None = None,
    pump_strength: int | None = None,
    break_via_paid_only: bool = False,
    **extra,
) -> dict:
    subtypes = []
    if c.get("keywords"):
        subtypes = [s.strip().lower() for s in c["keywords"].split(" - ")]
    card = base(c, subtypes=subtypes, **extra)
    br: dict = {
        "breaksSubtype": breaks,
        "strength": c.get("strength", 0),
        "breakCredits": break_credits,
        "breakMaxSubs": break_max,
    }
    if pump_credits is not None:
        br["pumpCredits"] = pump_credits
        br["pumpStrength"] = pump_strength if pump_strength is not None else 1
    if break_via_paid_only:
        br["breakViaPaidAbilityOnly"] = True
    card["breaker"] = br
    return card


def map_card(c: dict) -> dict | None:
    cid = slugify(c["title"])
    if cid in REPRINTS:
        return None

    if cid == "by-any-means":
        return base(
            c,
            subtypes=["priority", "sabotage"],
            playRequiresFirstClick=True,
            onPlay=do("ss_activate_by_any_means"),
        )

    if cid == "yusuf":
        return breaker(
            c,
            breaks="barrier",
            break_credits=0,
            break_max=1,
            break_via_paid_only=True,
            onSuccessfulRun=may(
                do("add_virus_counter", amount=1),
                label="Place 1 virus counter on Yusuf",
            ),
            paidAbilities=[
                paid(
                    "yusuf-break",
                    "Any virus counter: Break 1 barrier subroutine",
                    do("break_encounter_subroutine", maxSubs=1),
                    cost={"virusCounters": 1},
                    windows=["encounter_paw"],
                    usable_by_runner=True,
                ),
                paid(
                    "yusuf-pump",
                    "Any virus counter: +1 strength",
                    do("pump_strength", amount=1),
                    cost={"virusCounters": 1},
                    windows=["encounter_paw"],
                    usable_by_runner=True,
                ),
            ],
        )

    if cid == "zamba":
        return base(
            c,
            subtypes=["console"],
            unique=True,
            muBonus=2,
            mayGainCreditsOnCorpCardExposed=1,
        )

    if cid == "puffer":
        return breaker(
            c,
            breaks="sentry",
            break_credits=1,
            break_max=1,
            pump_credits=2,
            pump_strength=1,
            strengthPerPowerCounter=True,
            memoryCostPerPowerCounter=1,
            paidAbilities=[
                paid(
                    "puffer-power",
                    "[click]: Place 1 power counter on this program or remove 1 hosted power counter",
                    do("ss_puffer_add_or_remove_power"),
                    clicks=1,
                    windows=["runner_action_paw"],
                    usable_by_runner=True,
                ),
            ],
        )

    if cid == "lewi-guilherme":
        return base(
            c,
            subtypes=["connection"],
            unique=True,
            corpHandSizeBonusWhileInstalled=-1,
            onTurnBegin=choose(
                "runner",
                [
                    {
                        "id": "lose-credit",
                        "label": "Lose 1¢",
                        "effect": do("lose_credits", side="runner", amount=1),
                    },
                    {
                        "id": "trash-lewi",
                        "label": "Trash Lewi Guilherme",
                        "effect": do("trash_self"),
                    },
                ],
            ),
        )

    if cid == "cyberdelia":
        return base(
            c,
            subtypes=["chip"],
            muBonus=1,
            gainCreditsOnFirstFullyBreakEachTurn=1,
        )

    if cid == "upya":
        return base(
            c,
            onSuccessfulRunOnRd=may(
                do("add_power_counter", amount=1),
                label="Place 1 power counter on Upya",
            ),
            paidAbilities=[
                paid(
                    "upya-clicks",
                    "[click], 3 hosted power counters: Gain [click][click]",
                    do("gain_clicks", side="runner", amount=2),
                    clicks=1,
                    cost={"powerCounters": 3},
                    once_per_turn=True,
                    windows=["runner_action_paw"],
                    usable_by_runner=True,
                ),
            ],
        )

    if cid == "assimilator":
        return base(
            c,
            subtypes=["virtual"],
            paidAbilities=[
                paid(
                    "assimilator-faceup",
                    "[click][click]: Turn one of your facedown installed cards faceup. If that card is an event, trash it.",
                    do("ss_assimilator_turn_facedown_faceup"),
                    clicks=2,
                    windows=["runner_action_paw"],
                    usable_by_runner=True,
                ),
            ],
        )

    if cid == "asa-group-security-through-vigilance":
        return base(
            c,
            subtypes=["division"],
            onFirstCorpCardInstallEachTurn=may(
                do("ss_asa_install_non_agenda_same_server"),
                label="Install 1 non-agenda from HQ in/protecting the same server",
                decline_side="corp",
            ),
        )

    if cid == "ikawah-project":
        return base(
            c,
            subtypes=["security"],
            stealAdditionalClicks=1,
            stealAdditionalCredits=2,
        )

    if cid == "najja-1-0":
        return base(
            c,
            subtypes=["barrier", "bioroid"],
            subroutines=[
                {
                    "id": "najja-etr-1",
                    "text": "End the run.",
                    "effect": etr(),
                },
                {
                    "id": "najja-etr-2",
                    "text": "End the run.",
                    "effect": etr(),
                },
            ],
        )

    if cid == "gene-splicer":
        return base(
            c,
            subtypes=["ambush"],
            canAdvance=True,
            onAccess=do("net_damage_per_advancement"),
            paidAbilities=[
                paid(
                    "gene-splicer-score",
                    "[click], 3 hosted advancement tokens: Add Gene Splicer to your score area as an agenda worth 1 agenda point",
                    do("score_self_as_agenda", agendaPoints=1),
                    clicks=1,
                    cost={"advancementTokens": 3},
                    windows=["corp_action_paw"],
                ),
            ],
        )

    if cid == "mganga":
        return base(
            c,
            subtypes=["trap", "psi", "ap"],
            subroutines=[
                {
                    "id": "mganga-psi",
                    "text": "You and the Runner secretly spend 0¢, 1¢, or 2¢. Reveal spent credits. If you and the Runner spend a different number of credits, do 2 net damage; otherwise do 1 net damage. Trash Mganga.",
                    "effect": do(
                        "play_psi_game",
                        maxBid=2,
                        ifBidsDiffer=seq(
                            do("net_damage", amount=2),
                            do("trash_self"),
                        ),
                        ifBidsMatch=seq(
                            do("net_damage", amount=1),
                            do("trash_self"),
                        ),
                    ),
                },
            ],
        )

    if cid == "genotyping":
        return base(
            c,
            rfgInsteadOfTrashing=True,
            onPlay=seq(
                do("trash_top_of_rd"),
                do("trash_top_of_rd"),
                do("shuffle_archives_to_rd", amount=4),
            ),
        )

    if cid == "echo-chamber":
        return base(
            c,
            paidAbilities=[
                paid(
                    "echo-chamber-score",
                    "[click][click][click]: Add Echo Chamber to your score area as an agenda worth 1 agenda point",
                    do("score_self_as_agenda", agendaPoints=1),
                    clicks=3,
                    windows=["corp_action_paw"],
                ),
            ],
        )

    if cid == "self-growth-program":
        return base(
            c,
            subtypes=["gray ops"],
            playRequiresTagged=True,
            onPlay=do("ss_add_n_installed_runner_to_grip", amount=2),
        )

    if cid == "calibration-testing":
        return base(
            c,
            subtypes=["off-site"],
            remoteOnly=True,
            paidAbilities=[
                paid(
                    "calibration-adv",
                    "[trash]: Place 1 advancement counter on a card installed in the root of this server",
                    do("ss_place_advancement_on_root_of_this_server"),
                    trash_self=True,
                    windows=["corp_action_paw"],
                ),
            ],
        )

    if cid == "urban-renewal":
        return base(
            c,
            subtypes=["hostile"],
            powerCountersOnRez=3,
            trashWhenPowerEmpty=True,
            onPowerCountersEmpty=do("meat_damage", amount=4),
            onTurnBegin=do("remove_power_counter", amount=1),
        )

    if cid == "wake-up-call":
        return base(
            c,
            subtypes=["reprisal", "gray ops"],
            playRequiresRunnerTrashedCorpCardLastTurn=True,
            playRequiresRunnerHasInstalledHardwareOrNonVirtualResource=True,
            rfgInsteadOfTrashing=True,
            onPlay=do("ss_wake_up_call"),
        )

    if cid == "reconstruction-contract":
        return base(
            c,
            placeAdvancementOnSufferMeatDamage=True,
            paidAbilities=[
                paid(
                    "reconstruction-move",
                    "[trash]: Move any number of advancement tokens from Reconstruction Contract to a card that can be advanced",
                    do("ss_move_any_advancements_from_self_to_advanceable"),
                    trash_self=True,
                    windows=["corp_action_paw"],
                ),
            ],
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
