#!/usr/bin/env python3
"""Generate Kampala Ascendent (ka) card JSON from pinned pack `ka`.

Fetch: python3 scripts/nsg_catalog.py fetch ka
Kitara #6 after Whispers in Nalubaale (floor v1.140.0 → v1.141.0).
Reprint skips: none (20/20 new clears).
Follow NSG pack stripped_text (not IR-hint paraphrases).
NRDB pack name is **Kampala Ascendent** (with e) — folder `kampala-ascendent`.
Slug via spin_common.slugify (Zer0→zer0, Flame-out→flame-out,
Mti Mwekundu: Life Improved→mti-mwekundu-life-improved,
Diversion of Funds→diversion-of-funds, High-Profile Target→high-profile-target,
Better Citizen Program→better-citizen-program, NEXT Diamond→next-diamond,
PAD Tap→pad-tap, Kasi String→kasi-string, False Flag→false-flag).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from nsg_catalog import load_pack_cards
from spin_common import (
    base,
    core,
    do,
    draw,
    etr,
    gain,
    net,
    seq,
    slugify,
    write_manifest,
)

OUT = Path(__file__).resolve().parents[1] / "data" / "kampala-ascendent"
WAVE = "kampala-ascendent"
PACK = "ka"
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
    usable_by_any_player: bool = False,
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
    if usable_by_any_player:
        ab["usableByAnyPlayer"] = True
    return ab


def net_damage_unless_trash_top(damage: int, trash_n: int) -> dict:
    trash_effects = [do("trash_top_of_stack") for _ in range(trash_n)]
    return choose(
        "runner",
        [
            {
                "id": f"trash-top-{trash_n}",
                "label": f"Trash the top {trash_n} cards of the stack",
                "effect": seq(*trash_effects) if trash_n > 1 else trash_effects[0],
            },
            {
                "id": f"net-{damage}",
                "label": f"Suffer {damage} net damage",
                "effect": net(damage),
            },
        ],
    )


def map_card(c: dict) -> dict | None:
    cid = slugify(c["title"])
    if cid in REPRINTS:
        return None

    if cid == "zer0":
        return base(
            c,
            unique=True,
            paidAbilities=[
                paid(
                    "zer0",
                    "Once per turn → [click], suffer 1 net damage: Gain 1¢ and draw 2 cards",
                    seq(gain("runner", 1), draw("runner", 2)),
                    clicks=1,
                    cost={"clicks": 1, "netDamage": 1},
                    windows=["runner_action_paw"],
                    once_per_turn=True,
                    usable_by_runner=True,
                ),
            ],
        )

    if cid == "musaazi":
        return base(
            c,
            subtypes=["icebreaker", "killer", "virus"],
            onSuccessfulRun=may(
                do("add_virus_counter", amount=1),
                label="Place 1 virus counter on Musaazi",
            ),
            paidAbilities=[
                paid(
                    "musaazi-break",
                    "Any virus counter: Break sentry subroutine",
                    do("break_encounter_subroutine", maxSubs=1),
                    cost={"virusCounters": 1},
                    windows=["encounter_paw"],
                    usable_by_runner=True,
                ),
                paid(
                    "musaazi-pump",
                    "Any virus counter: +1 strength",
                    do("pump_strength", amount=1),
                    cost={"virusCounters": 1},
                    windows=["encounter_paw"],
                    usable_by_runner=True,
                ),
            ],
            breaker={
                "breaksSubtype": "sentry",
                "strength": c.get("strength", 1),
                "breakCredits": 0,
                "breakMaxSubs": 1,
                "breakViaPaidAbilityOnly": True,
            },
        )

    if cid == "hippo":
        return base(
            c,
            unique=True,
            mayRfgSelfToTrashOutermostIceOnFirstFullBreakEachTurn=True,
        )

    if cid == "amina":
        return base(
            c,
            subtypes=["icebreaker", "decoder"],
            breaker={
                "breaksSubtype": "code gate",
                "strength": c.get("strength", 3),
                "breakCredits": 2,
                "breakMaxSubs": 3,
                "pumpCredits": 2,
                "pumpStrength": 3,
            },
            onFullyBreakOncePerTurn=do("lose_credits", side="corp", amount=1),
        )

    if cid == "diversion-of-funds":
        return base(
            c,
            subtypes=["double", "run", "sabotage"],
            playAdditionalClick=True,
            runEvent={
                "servers": "hq",
                "onSuccessfulRun": do("ka_diversion_of_funds_may_instead_of_breach"),
            },
        )

    if cid == "pad-tap":
        return base(
            c,
            mayGainCreditOnFirstCorpCardAbilityCreditGainEachTurn=True,
            paidAbilities=[
                paid(
                    "pad-tap-corp-trash",
                    "[click], 3¢: Trash PAD Tap (Corp only)",
                    do("trash_self"),
                    clicks=1,
                    credits=3,
                    windows=["corp_action_paw"],
                    usable_by_any_player=True,
                ),
            ],
        )

    if cid == "reclaim":
        return base(
            c,
            paidAbilities=[
                paid(
                    "reclaim",
                    "[click], [trash], trash a card from grip: Install program/hardware/virtual from heap paying cost",
                    do("ka_reclaim_install_from_heap"),
                    clicks=1,
                    cost={"clicks": 1, "trashSelf": True, "trashFromGrip": 1},
                    windows=["runner_action_paw"],
                    usable_by_runner=True,
                ),
            ],
        )

    if cid == "engolo":
        return base(
            c,
            subtypes=["icebreaker", "decoder"],
            breaker={
                "breaksSubtype": "code gate",
                "strength": c.get("strength", 2),
                "breakCredits": 1,
                "breakMaxSubs": 1,
                "pumpCredits": 2,
                "pumpStrength": 4,
            },
            onEncounterMayPayCreditsGrantIceSubtype={
                "credits": 2,
                "subtype": "code gate",
                "oncePerTurn": True,
            },
        )

    if cid == "flame-out":
        return base(
            c,
            subtypes=["mod"],
            unique=True,
            maxHostedCards=1,
            hostsAnyProgramMemoryCostLte=99,
            hostedCreditsOnInstall=9,
            spendHostedCreditsToUseHostedProgram=True,
            trashHostedProgramAtEndOfTurnIfHostedCreditsUsed=True,
        )

    if cid == "black-hat":
        return base(
            c,
            onPlay=do(
                "trace",
                strength=4,
                onSuccess=gain("runner", 0),
                onFailure=do("ka_black_hat_bonus_access"),
            ),
        )

    if cid == "kasi-string":
        return base(
            c,
            subtypes=["virtual"],
            unique=True,
            placePowerOnFirstSuccessfulRemoteRunEndIfBreachedNoSteal=True,
            scoreWhenPowerGte={"threshold": 4, "agendaPoints": 1},
        )

    if cid == "next-diamond":
        return base(
            c,
            subtypes=["sentry", "next", "destroyer", "ap"],
            rezCostDiscountPerRezzedSubtype={"subtype": "next", "amount": 1},
            subroutines=[
                {
                    "id": "next-diamond-core-1",
                    "text": "Do 1 core damage.",
                    "effect": core(1),
                },
                {
                    "id": "next-diamond-core-2",
                    "text": "Do 1 core damage.",
                    "effect": core(1),
                },
                {
                    "id": "next-diamond-trash",
                    "text": "Trash 1 installed Runner card.",
                    "effect": do("trash_installed_runner", pick="choose"),
                },
            ],
        )

    if cid == "riot-suppression":
        return base(
            c,
            subtypes=["reprisal", "gray ops"],
            playRequiresRunnerTrashedCorpCardLastTurn=True,
            rfgInsteadOfTrashing=True,
            onPlay=choose(
                "runner",
                [
                    {
                        "id": "suffer-core",
                        "label": "Suffer 1 core damage",
                        "effect": core(1),
                    },
                    {
                        "id": "lose-clicks",
                        "label": "Get −3 allotted [click] for your next turn",
                        "effect": do("allotted_clicks_next_turn", side="runner", delta=-3),
                    },
                ],
            ),
        )

    if cid == "mti-mwekundu-life-improved":
        return base(
            c,
            subtypes=["division"],
            onApproachServerOncePerTurn=True,
            onApproachServer=may(
                do("ka_mti_install_ice_innermost_from_hq"),
                label="Install 1 ice from HQ innermost protecting this server, ignoring all costs",
                decline_side="corp",
            ),
        )

    if cid == "mlinzi":
        return base(
            c,
            subtypes=["sentry", "ap"],
            subroutines=[
                {
                    "id": "mlinzi-1",
                    "text": "Do 1 net damage unless the Runner trashes the top 2 cards of the stack.",
                    "effect": net_damage_unless_trash_top(1, 2),
                },
                {
                    "id": "mlinzi-2",
                    "text": "Do 2 net damage unless the Runner trashes the top 3 cards of the stack.",
                    "effect": net_damage_unless_trash_top(2, 3),
                },
                {
                    "id": "mlinzi-3",
                    "text": "Do 3 net damage unless the Runner trashes the top 4 cards of the stack.",
                    "effect": net_damage_unless_trash_top(3, 4),
                },
            ],
        )

    if cid == "better-citizen-program":
        return base(
            c,
            subtypes=["initiative"],
            mayTagOnFirstRunEventOrIcebreakerInstallEachTurn=True,
        )

    if cid == "market-forces":
        return base(
            c,
            subtypes=["gray ops"],
            playRequiresTagged=True,
            onPlay=do("ka_market_forces"),
        )

    if cid == "surveyor":
        # X = 2 × ice protecting this server (strength + Trace[X]).
        return base(
            c,
            subtypes=["sentry", "tracer"],
            strength=0,
            strengthBonusPerIceProtectingThisServer=2,
            subroutines=[
                {
                    "id": "surveyor-tags",
                    "text": "Trace[X]. If successful, give the Runner 2 tags.",
                    "effect": do(
                        "trace_strength_equal_source_strength",
                        onSuccess=do("give_tags", amount=2),
                    ),
                },
                {
                    "id": "surveyor-etr",
                    "text": "Trace[X]. If successful, end the run.",
                    "effect": do(
                        "trace_strength_equal_source_strength",
                        onSuccess=etr(),
                    ),
                },
            ],
        )

    if cid == "high-profile-target":
        return base(
            c,
            subtypes=["black ops"],
            playRequiresTagged=True,
            onPlay=do(
                "meat_damage",
                amount=0,
                tally={"count": "runner_tags", "per": 2, "side": "runner"},
            ),
        )

    if cid == "false-flag":
        return base(
            c,
            subtypes=["ambush"],
            canAdvance=True,
            onAccess=do("give_tags_per_two_advancements"),
            paidAbilities=[
                paid(
                    "false-flag-score",
                    "[click], 7 hosted advancement tokens: add False Flag to score area as 3AP agenda",
                    do("score_self_as_agenda", agendaPoints=3),
                    clicks=1,
                    cost={"clicks": 1, "advancementTokens": 7},
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
