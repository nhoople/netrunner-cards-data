#!/usr/bin/env python3
"""Generate Honor and Profit (hap) card JSON from pinned pack `hap`.

Fetch: python3 scripts/nsg_catalog.py fetch hap
Deluxe after Double Time (floor v1.100.0 → v1.101.0).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from nsg_catalog import load_pack_cards
from spin_common import (
    base,
    breaker_card,
    do,
    draw,
    etr,
    gain,
    net,
    seq,
    slugify,
    trace_sub,
    write_manifest,
)

OUT = Path(__file__).resolve().parents[1] / "data" / "honor-and-profit"
WAVE = "honor-and-profit"
PACK = "hap"
EXPECTED = 55

REPRINTS = {
    "house-of-knives",
    "philotic-entanglement",
    "ken-express-tenma-disappeared-clone",
    "legwork",
    "security-testing",
}

DECLINE = {
    "id": "decline",
    "label": "Decline",
    "effect": gain("runner", 0),
}


def psi(max_bid: int, on_match, on_differ):
    return do(
        "play_psi_game",
        maxBid=max_bid,
        ifBidsMatch=on_match,
        ifBidsDiffer=on_differ,
    )


def map_card(c: dict) -> dict | None:
    cid = slugify(c["title"])
    if cid in REPRINTS:
        return None

    if cid == "harmony-medtech-biomedical-pioneer":
        return base(c, agendaPointsToWinModifierBoth=-1)

    if cid == "nisei-division-the-next-generation":
        return base(c, onPsiCreditsRevealed=gain("corp", 1))

    if cid == "tennin-institute-the-secrets-within":
        return base(
            c,
            onTurnBeginIfNoRunnerSuccessfulRunLastTurn=do(
                "tennin_place_advancement_on_installed"
            ),
        )

    if cid == "medical-breakthrough":
        return base(c, advancementRequirementReductionPerSameTitleAnywhere=1)

    if cid == "the-future-perfect":
        return base(
            c,
            onAccessWhileUninstalled=psi(2, net(1), gain("corp", 0)),
        )

    if cid == "chairman-hiro":
        return base(
            c,
            subtypes=["executive"],
            runnerHandSizeBonus=-2,
            onTrashWhileAccessed=do(
                "add_to_runner_score_as_agenda", agendaPoints=-2
            ),
        )

    if cid == "mental-health-clinic":
        return base(
            c,
            onTurnBegin=gain("corp", 1),
            runnerHandSizeBonus=1,
        )

    if cid == "psychic-field":
        return base(
            c,
            onAccessWhileInstalled=psi(3, net(2), gain("corp", 0)),
            onExposeWhileInstalled=psi(3, net(2), gain("corp", 0)),
        )

    if cid == "shi-kyu":
        return base(
            c,
            onAccessNotFromRd=do("shi_kyu_spend_for_net_damage"),
        )

    if cid == "tenma-line":
        return base(
            c,
            paidAbilities=[
                {
                    "id": "tenma-swap",
                    "label": "[click]: Swap 2 pieces of installed ice",
                    "clickCost": 1,
                    "creditCost": 0,
                    "cost": {"clicks": 1},
                    "windows": ["corp_action_paw"],
                    "effect": do("may_swap_two_installed_ice"),
                }
            ],
        )

    if cid == "cerebral-cast":
        return base(
            c,
            playRequiresSuccessfulRunLastTurn=True,
            onPlay=psi(3, net(2), gain("corp", 0)),
        )

    if cid == "medical-research-fundraiser":
        return base(
            c,
            onPlay=seq(gain("corp", 8), gain("runner", 3)),
        )

    if cid == "mushin-no-shin":
        return base(
            c,
            playAdditionalClick=True,
            onPlay=do("mushin_install_from_hq_root"),
        )

    if cid == "inazuma":
        return base(
            c,
            subroutines=[
                {
                    "id": "inazuma-lock",
                    "text": "Next encounter this run Runner cannot break subroutines on encountered ice.",
                    "effect": do("inazuma_lock_breaking_next_encounter"),
                },
                {"id": "inazuma-etr", "text": "End the run.", "effect": etr()},
            ],
        )

    if cid == "komainu":
        return base(c, onEncounter=do("komainu_add_net_subs_for_rezzed_ice"))

    if cid == "pup":
        return base(
            c,
            subroutines=[
                {
                    "id": "pup-1",
                    "text": "Do 1 net unless Runner pays 1[credit].",
                    "effect": do("pup_pay_or_net", amount=1),
                },
                {
                    "id": "pup-2",
                    "text": "Do 1 net unless Runner pays 1[credit].",
                    "effect": do("pup_pay_or_net", amount=1),
                },
            ],
        )

    if cid == "shiro":
        return base(
            c,
            subroutines=[
                {
                    "id": "shiro-arrange",
                    "text": "Look at top 3 of R&D and arrange them.",
                    "effect": do("look_top_n_rd_arrange", n=3),
                },
                {
                    "id": "shiro-pay",
                    "text": "You may pay 1[credit]. If you do, do 1 net damage.",
                    "effect": do("corp_may_pay_net", creditCost=1, damage=1),
                },
            ],
        )

    if cid == "susanoo-no-mikoto":
        return base(
            c,
            subroutines=[
                {
                    "id": "susanoo-redirect",
                    "text": "If server is not Archives, move to outermost Archives instead of passing.",
                    "effect": do("susanoo_redirect_to_archives"),
                }
            ],
        )

    if cid == "neotokyo-grid":
        return base(
            c,
            onFirstAdvancementOnServerThisTurn=gain("corp", 1),
            oncePerTurn=True,
        )

    if cid == "tori-hanzo":
        return base(
            c,
            onFirstNetDamageThisRunOnServer=do("tori_hanzo_pay_instead_net"),
        )

    if cid == "plan-b":
        return base(
            c,
            canAdvance=True,
            onAccessWhileInstalled=do("plan_b_reveal_score_from_hq"),
        )

    if cid == "guard":
        return base(
            c,
            cannotBeBypassed=True,
            subroutines=[{"id": "guard-etr", "text": "End the run.", "effect": etr()}],
        )

    if cid == "rainbow":
        return base(
            c,
            subroutines=[{"id": "rainbow-etr", "text": "End the run.", "effect": etr()}],
        )

    if cid == "diversified-portfolio":
        return base(
            c,
            onPlay=do("gain_credits_per_remote_with_root_card", per=1),
        )

    if cid == "fast-track":
        return base(c, onPlay=do("search_rd_agenda_to_hq"))

    if cid == "iain-stirling-retired-spook":
        return base(
            c,
            onTurnBegin=do("iain_gain_if_corp_ahead_on_agenda"),
        )

    if cid == "silhouette-stealth-operative":
        return base(
            c,
            onFirstSuccessfulHqRunThisTurn={
                "op": "choose",
                "chooser": "runner",
                "options": [
                    {
                        "id": "expose",
                        "label": "Expose 1 card",
                        "effect": do("expose_up_to", max=1),
                    },
                    DECLINE,
                ],
            },
        )

    if cid == "calling-in-favors":
        return base(
            c,
            onPlay=do("gain_credits_per_installed_subtype", subtype="connection"),
        )

    if cid == "early-bird":
        return base(
            c,
            playRequiresFirstClick=True,
            onPlay=seq(
                do("gain_clicks", side="runner", amount=1),
                do("may_start_run", servers="any"),
            ),
        )

    if cid == "express-delivery":
        return base(c, onPlay=do("look_top_n_stack_add_one_to_grip_shuffle", n=4))

    if cid == "feint":
        return base(
            c,
            subtypes=["run"],
            runEvent={
                "servers": "hq",
                "bypassEncountersRemaining": 2,
                "skipBreach": True,
            },
        )

    if cid == "planned-assault":
        return base(
            c,
            playAdditionalClick=True,
            onPlay=do("planned_assault_play_run_event_from_stack"),
        )

    if cid == "logos":
        return base(
            c,
            muBonus=1,
            handSizeBonus=1,
            onAgendaScored=do("search_stack_take_to_grip", max=1),
        )

    if cid == "public-terminal":
        return base(
            c,
            recurringCreditsMax=1,
            recurringSpendFor=["play_event"],
            recurringSpendForPlayEventSubtypes=["run"],
        )

    if cid == "unregistered-s-w-35":
        return base(
            c,
            playRequiresSuccessfulHqRunThisTurn=True,
            paidAbilities=[
                {
                    "id": "unregistered-trash",
                    "label": "[click][click]: Trash 1 rezzed ice, gain 2[credit] per strength",
                    "clickCost": 2,
                    "creditCost": 0,
                    "cost": {"clicks": 2},
                    "windows": ["runner_action_paw"],
                    "effect": do("unregistered_trash_rezzed_ice_gain_per_strength"),
                }
            ],
        )

    if cid == "window":
        return base(
            c,
            paidAbilities=[
                {
                    "id": "window-draw",
                    "label": "[click]: Draw 1 from bottom of stack",
                    "clickCost": 1,
                    "creditCost": 0,
                    "cost": {"clicks": 1},
                    "windows": ["runner_action_paw"],
                    "effect": do("draw_from_stack_bottom", side="runner", amount=1),
                }
            ],
        )

    if cid == "alias":
        return breaker_card(c, "sentry", 1, 1, 2, 3)

    if cid == "breach":
        card = breaker_card(c, "barrier", 2, 2, 2, 3)
        card["breaker"]["breakMaxSubs"] = 3
        return card

    if cid == "gingerbread":
        return breaker_card(c, "tracer", 1, 1, 2, 3)

    if cid == "passport":
        return breaker_card(c, "code gate", 1, 1, 2, 2)

    if cid == "bug":
        return base(
            c,
            playRequiresSuccessfulHqRunThisTurn=True,
            onCorpDrawCard=do("bug_may_pay_reveal_top"),
        )

    if cid == "grappling-hook":
        return base(
            c,
            paidAbilities=[
                {
                    "id": "grappling-break",
                    "label": "[trash]: Break all but 1 subroutine on a piece of ice",
                    "clickCost": 0,
                    "creditCost": 0,
                    "cost": {"trashSelf": True},
                    "windows": ["runner_action_paw"],
                    "effect": do("break_all_but_n_subroutines_on_encounter", leave=1),
                }
            ],
        )

    if cid == "push-your-luck":
        return base(c, onPlay=do("push_your_luck_secret_spend_guess"))

    if cid == "theophilius-bagbiter":
        return base(
            c,
            onInstall=do("lose_all_credits", side="runner"),
            handSizeEqualsCredits=True,
        )

    if cid == "tri-maf-contact":
        return base(
            c,
            paidAbilitiesOncePerTurn=True,
            paidAbilities=[
                {
                    "id": "tri-maf-gain",
                    "label": "[click]: Gain 2[credit]",
                    "clickCost": 1,
                    "creditCost": 0,
                    "cost": {"clicks": 1},
                    "windows": ["runner_action_paw"],
                    "effect": gain("runner", 2),
                }
            ],
            onTrash=do("give_tags", amount=1),
        )

    if cid == "mass-install":
        return base(
            c,
            onPlay=do(
                "install_up_to_n_programs_from_grip_discount",
                remaining=3,
                discount=0,
            ),
        )

    if cid == "q-coherence-chip":
        return base(
            c,
            muBonus=1,
            trashSelfWhenInstalledProgramTrashed=True,
        )

    if cid == "overmind":
        card = base(c, subtypes=["icebreaker", "ai"])
        card["breaker"] = {
            "breaksSubtype": "*",
            "strength": 0,
            "breakCredits": 1,
            "breakMaxSubs": 99,
        }
        card["powerCountersOnInstallFromUnusedMu"] = True
        card["strengthPerPowerCounter"] = True
        return card

    if cid == "oracle-may":
        return base(
            c,
            paidAbilitiesOncePerTurn=True,
            paidAbilities=[
                {
                    "id": "oracle-may",
                    "label": "[click]: Choose type; reveal top of stack; install if match",
                    "clickCost": 1,
                    "creditCost": 0,
                    "cost": {"clicks": 1},
                    "windows": ["runner_action_paw"],
                    "effect": do("oracle_may_choose_type_reveal_install"),
                }
            ],
        )

    if cid == "donut-taganes":
        return base(c, corpPlayCostIncreaseForRunnerEventsOps=1)

    card = base(c)
    card["unsupported"] = [f"Unmapped hap card: {cid}"]
    return card


def main():
    pack = sorted(load_pack_cards(PACK), key=lambda c: c.get("position", 0))
    assert len(pack) == EXPECTED, len(pack)
    OUT.mkdir(parents=True, exist_ok=True)
    written: list[str] = []
    skipped: list[str] = []
    for c in pack:
        cid = slugify(c["title"])
        mapped = map_card(c)
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
