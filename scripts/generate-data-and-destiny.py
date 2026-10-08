#!/usr/bin/env python3
"""Generate Data and Destiny (dad) card JSON from pinned pack `dad`.

Fetch: python3 scripts/nsg_catalog.py fetch dad
Deluxe after The Universe of Tomorrow / SanSan (floor v1.114.0 → v1.115.0).
Reprint skip: spark-agency-worldswide-reach (SC19).
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
    etr,
    gain,
    net,
    seq,
    slugify,
    write_manifest,
)

OUT = Path(__file__).resolve().parents[1] / "data" / "data-and-destiny"
WAVE = "data-and-destiny"
PACK = "dad"
EXPECTED = 55

REPRINTS = {
    "spark-agency-worldswide-reach",  # system-core-2019
}


def choose(chooser: str, options: list[dict]) -> dict:
    return {"op": "choose", "chooser": chooser, "options": options}


def may(effect: dict, label: str = "Accept", decline_side: str = "corp") -> dict:
    return choose(
        decline_side if decline_side in ("corp", "runner") else "corp",
        [
            {"id": "accept", "label": label, "effect": effect},
            {
                "id": "decline",
                "label": "Decline",
                "effect": gain(
                    decline_side if decline_side in ("corp", "runner") else "corp",
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
    usable_from_runner_score: bool = False,
    require_during_run: bool = False,
    require_this_server: bool = False,
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
        or (
            ["corp_action_paw"]
            if not usable_by_runner
            else ["runner_action_paw"]
        ),
        "effect": effect,
    }
    if once_per_turn:
        ab["oncePerTurn"] = True
    if usable_by_runner:
        ab["usableByRunnerOnSelfIce"] = True
    if usable_from_runner_score:
        ab["usableFromRunnerScoreArea"] = True
    if require_during_run:
        ab["requireDuringRun"] = True
    if require_this_server:
        ab["requireThisServer"] = True
    return ab


def cloud_breaker(c: dict, subtype: str) -> dict:
    card = base(
        c,
        memoryCostZeroIfLinkGte=2,
        breaker={
            "breaksSubtype": subtype,
            "strength": c.get("strength") or 1,
            "breakCredits": 2,
            "breakMaxSubs": 99,
            "pumpCredits": 2,
            "pumpStrength": 3,
        },
    )
    return card


def map_card(c: dict) -> dict | None:
    cid = slugify(c["title"])
    if cid in REPRINTS:
        return None

    # --- NBN identities ---
    if cid == "sync-everything-everywhere":
        return base(
            c,
            paidAbilities=[
                paid(
                    "sync-flip",
                    "[click]: Flip this identity",
                    do("flip_identity"),
                    clicks=1,
                )
            ],
            # Front (unflipped): remove-tag basic action costs +1¢
            basicRemoveTagAdditionalCostCreditsWhileUnflipped=1,
            # Back (flipped): trash-resource basic action costs −2¢
            basicTrashResourceCreditReductionWhileFlipped=2,
        )

    if cid == "new-angeles-sol-your-news":
        return base(
            c,
            onAgendaScoredOrStolen=may(
                do("play_current_from_hq_or_archives"),
                label="Play 1 current from HQ or Archives",
            ),
        )

    # --- Agendas ---
    if cid == "15-minutes":
        return base(
            c,
            deckLimit=1,
            paidAbilities=[
                paid(
                    "15-minutes-shuffle",
                    "[click]: Shuffle 15 Minutes into R&D",
                    do("shuffle_source_into_rd"),
                    clicks=1,
                    usable_from_runner_score=True,
                )
            ],
        )

    if cid == "improved-tracers":
        return base(
            c,
            subtypes=["security"],
            iceStrengthBonusForSubtype={"subtype": "tracer", "bonus": 1},
            subroutineTraceBaseStrengthBonus=1,
        )

    if cid == "rebranding-team":
        return base(
            c,
            subtypes=["initiative"],
            assetsGainSubtype="advertisement",
        )

    if cid == "quantum-predictive-model":
        return base(
            c,
            subtypes=["security"],
            mustRevealWhenAccessedFromRd=True,
            addToCorpScoreOnAccessIfRunnerTagged=True,
        )

    # --- Assets ---
    if cid == "lily-lockwell":
        return base(
            c,
            subtypes=["character"],
            onRez=do("draw", side="corp", amount=3),
            paidAbilities=[
                paid(
                    "lily-search",
                    "[click], remove 1 tag: Search R&D for an operation; add to top of R&D",
                    do("search_rd_operation_to_top_rd"),
                    clicks=1,
                    cost={"removeTags": 1},
                )
            ],
        )

    if cid == "news-team":
        return base(
            c,
            subtypes=["ambush"],
            mustRevealWhenAccessedFromRd=True,
            onAccess=choose(
                "runner",
                [
                    {
                        "id": "tags",
                        "label": "Take 2 tags",
                        "effect": do("give_tags", amount=2),
                    },
                    {
                        "id": "score",
                        "label": "Add News Team to score area as −1 agenda point",
                        "effect": do(
                            "add_to_runner_score_as_agenda", agendaPoints=-1
                        ),
                    },
                ],
            ),
        )

    if cid == "shannon-claire":
        return base(
            c,
            subtypes=["character"],
            paidAbilities=[
                paid(
                    "shannon-draw-bottom",
                    "[click]: Draw 1 card from the bottom of R&D",
                    do("draw_from_bottom_of_rd", amount=1),
                    clicks=1,
                ),
                paid(
                    "shannon-search",
                    "[trash]: Search R&D or Archives for an agenda; add to bottom of R&D",
                    do("search_rd_or_archives_agenda_to_bottom_rd"),
                    trash_self=True,
                ),
            ],
        )

    if cid == "victoria-jenkins":
        return base(
            c,
            subtypes=["executive"],
            unique=True,
            runnerAllottedClicksBonus=-1,
            onTrashWhileAccessed=do(
                "add_to_runner_score_as_agenda", agendaPoints=2
            ),
        )

    if cid == "reality-threedee":
        return base(
            c,
            subtypes=["liability"],
            badPublicityOnRez=1,
            onTurnBegin=do("reality_threedee_gain_credits"),
        )

    # --- Ice ---
    if cid == "archangel":
        return base(
            c,
            subtypes=["code gate", "tracer", "ambush"],
            mustRevealWhenAccessedFromRd=True,
            skipOnAccessFromArchives=True,
            onAccess=may(
                seq(
                    do("lose_credits", side="corp", amount=3),
                    do("force_encounter_accessed_ice"),
                ),
                label="Pay 3¢: Runner encounters Archangel",
            ),
            subroutines=[
                {
                    "id": "archangel-trace",
                    "text": "Trace[6]. If successful, add 1 installed Runner card to the grip.",
                    "effect": do(
                        "trace",
                        strength=6,
                        onSuccess=do("add_installed_runner_to_grip"),
                    ),
                }
            ],
        )

    if cid == "news-hound":
        return base(
            c,
            subtypes=["sentry", "tracer"],
            gainsEtrSubroutineWhileCurrentActive=True,
            subroutines=[
                {
                    "id": "news-hound-trace",
                    "text": "Trace[3]. If successful, give the Runner 1 tag.",
                    "effect": do(
                        "trace",
                        strength=3,
                        onSuccess=do("give_tags", amount=1),
                    ),
                }
            ],
        )

    if cid == "resistor":
        return base(
            c,
            subtypes=["barrier", "tracer"],
            strengthBonusPerRunnerTag=1,
            subroutines=[
                {
                    "id": "resistor-trace",
                    "text": "Trace[4]. If successful, end the run.",
                    "effect": do(
                        "trace", strength=4, onSuccess=etr()
                    ),
                }
            ],
        )

    if cid == "special-offer":
        return base(
            c,
            subtypes=["trap", "advertisement"],
            subroutines=[
                {
                    "id": "special-offer-gain",
                    "text": "The Corp gains 5[credit]. Trash Special Offer.",
                    "effect": seq(gain("corp", 5), do("trash_self")),
                }
            ],
        )

    if cid == "tl-dr":
        return base(
            c,
            subtypes=["code gate"],
            subroutines=[
                {
                    "id": "tl-dr-duplicate",
                    "text": "Next ice encounter this run gains a second copy of each subroutine.",
                    "effect": do("arm_duplicate_subs_on_next_ice_encounter"),
                }
            ],
        )

    if cid == "turnpike":
        return base(
            c,
            subtypes=["sentry", "tracer"],
            onEncounter=do("lose_credits", side="runner", amount=1),
            subroutines=[
                {
                    "id": "turnpike-trace",
                    "text": "Trace[5]. If successful, give the Runner 1 tag.",
                    "effect": do(
                        "trace",
                        strength=5,
                        onSuccess=do("give_tags", amount=1),
                    ),
                }
            ],
        )

    # --- Operations ---
    if cid == "24-7-news-cycle":
        return base(
            c,
            playCost=0,
            playAdditionalCostForfeitAgenda=True,
            onPlay=do("resolve_when_scored_on_scored_agenda"),
        )

    if cid == "ad-blitz":
        return base(
            c,
            subtypes=["double"],
            playCost=0,
            playCostX=True,
            playAdditionalClicks=1,
            onPlay=do("install_and_rez_x_advertisements_from_hq_or_archives"),
        )

    if cid == "media-blitz":
        return base(
            c,
            subtypes=["current"],
            lingerAsCurrent=True,
            currentTrashOnAgendaStolen=True,
            onPlay=do("gain_text_of_runner_scored_agenda"),
        )

    if cid == "the-all-seeing-i":
        return base(
            c,
            playRequiresTagged=True,
            onPlay=do("trash_all_resources_unless_remove_bad_publicity"),
        )

    if cid == "surveillance-sweep":
        return base(
            c,
            subtypes=["current"],
            lingerAsCurrent=True,
            currentTrashOnAgendaStolen=True,
            runnerSpendsFirstForTracesDuringRun=True,
        )

    # --- Upgrades ---
    if cid == "keegan-lane":
        return base(
            c,
            subtypes=["sysop"],
            paidAbilities=[
                paid(
                    "keegan-trash-program",
                    "[trash], remove 1 tag: Trash 1 program (run on this server)",
                    do("trash_program", pick="choose"),
                    trash_self=True,
                    cost={"removeTags": 1},
                    windows=["corp_action_paw"],
                    require_during_run=True,
                    require_this_server=True,
                )
            ],
        )

    if cid == "rutherford-grid":
        return base(
            c,
            subtypes=["region"],
            traceBaseStrengthBonusDuringRunOnThisServer=2,
        )

    # --- Neutral corp ---
    if cid == "global-food-initiative":
        return base(
            c,
            subtypes=["initiative"],
            agendaPointsModifierInRunnerScoreArea=-1,
        )

    if cid == "launch-campaign":
        return base(
            c,
            subtypes=["advertisement"],
            onRez=do("place_hosted_credits", amount=6),
            onTurnBegin=do("take_hosted_credits", amount=2),
            trashWhenHostedCreditsEmpty=True,
        )

    if cid == "assassin":
        return base(
            c,
            subtypes=["sentry", "destroyer", "ap", "tracer"],
            subroutines=[
                {
                    "id": "assassin-net",
                    "text": "Trace[5]. If successful, do 3 net damage.",
                    "effect": do(
                        "trace", strength=5, onSuccess=net(3)
                    ),
                },
                {
                    "id": "assassin-trash",
                    "text": "Trace[4]. If successful, trash 1 program.",
                    "effect": do(
                        "trace",
                        strength=4,
                        onSuccess=do("trash_program", pick="choose"),
                    ),
                },
            ],
        )

    # --- Apex ---
    if cid == "apex-invasive-predator":
        return base(
            c,
            link=c.get("base_link", 0),
            cannotInstallNonVirtualResources=True,
            onTurnBegin=may(
                do("install_from_grip_facedown"),
                label="Install 1 card from grip facedown",
                decline_side="runner",
            ),
        )

    if cid == "apocalypse":
        return base(
            c,
            playRequiresSuccessfulAllCentralsThisTurn=True,
            onPlay=seq(
                do("trash_all_installed_corp_cards"),
                do("turn_all_installed_runner_cards_facedown"),
            ),
        )

    if cid == "prey":
        return base(
            c,
            subtypes=["run"],
            runEvent={
                "servers": "any",
                "onPassIceMayTrashEqualStrengthToTrashIce": True,
            },
        )

    if cid == "heartbeat":
        return base(
            c,
            subtypes=["console"],
            unique=True,
            muBonus=1,
            paidAbilities=[
                paid(
                    "heartbeat-prevent",
                    "[interrupt] → Trash 1 installed card: Prevent 1 damage",
                    do("trash_installed_prevent_damage", amount=1),
                    windows=["damage_interrupt_paw"],
                    usable_by_runner=True,
                )
            ],
        )

    if cid == "endless-hunger":
        return base(
            c,
            subtypes=["icebreaker"],
            breaker={
                "breaksSubtype": "end-the-run",
                "strength": c.get("strength") or 11,
                "breakCredits": 0,
                "breakMaxSubs": 1,
                "breakCostTrashInstalled": 1,
                "breakViaPaidAbilityOnly": True,
            },
            paidAbilities=[
                paid(
                    "endless-hunger-break",
                    "Trash 1 installed card: Break 1 End the run subroutine",
                    do("break_etr_subroutine_trash_installed"),
                    windows=["runner_action_paw"],
                    usable_by_runner=True,
                    require_during_run=True,
                )
            ],
        )

    if cid == "harbinger":
        return base(
            c,
            turnFacedownInsteadOfHeapWhenTrashed=True,
        )

    if cid == "hunting-grounds":
        return base(
            c,
            subtypes=["location", "virtual"],
            paidAbilities=[
                paid(
                    "hunting-grounds-prevent",
                    "[interrupt], once per turn → 0¢: Prevent a when-encountered ability",
                    do("prevent_pending_when_encountered"),
                    credits=0,
                    once_per_turn=True,
                    windows=["when_encountered_interrupt_paw"],
                    usable_by_runner=True,
                ),
                paid(
                    "hunting-grounds-install",
                    "[trash]: Install the top 3 cards of your stack facedown",
                    do("install_top_n_of_stack_facedown", amount=3),
                    trash_self=True,
                    windows=["runner_action_paw"],
                    usable_by_runner=True,
                ),
            ],
        )

    if cid == "wasteland":
        return base(
            c,
            subtypes=["location", "virtual"],
            gainCreditsOnFirstOwnInstalledTrashEachTurn=1,
        )

    # --- Adam ---
    if cid == "adam-compulsive-hacker":
        return base(
            c,
            link=c.get("base_link", 0),
            startWithDirectiveCards=3,
        )

    if cid == "independent-thinking":
        return base(
            c,
            onPlay=do("trash_draw"),
        )

    if cid == "brain-chip":
        return base(
            c,
            subtypes=["console"],
            unique=True,
            muEqualsAgendaPoints=True,
            handSizeEqualsAgendaPoints=True,
        )

    if cid == "multithreader":
        return base(
            c,
            recurringCreditsMax=2,
            recurringSpendFor=["use_program"],
        )

    if cid == "always-be-running":
        return base(
            c,
            subtypes=["directive", "virtual"],
            firstClickMustBeRunOrRunEvent=True,
            paidAbilities=[
                paid(
                    "abr-break",
                    "Once per turn → Lose [click][click]: Break 1 subroutine",
                    do("break_any_subroutine"),
                    cost={"clicks": 2},
                    once_per_turn=True,
                    windows=["runner_action_paw"],
                    usable_by_runner=True,
                    require_during_run=True,
                )
            ],
        )

    if cid == "dr-lovegood":
        return base(
            c,
            subtypes=["connection"],
            onTurnBegin=do("blank_installed_abilities"),
        )

    if cid == "neutralize-all-threats":
        return base(
            c,
            subtypes=["directive", "virtual"],
            mustTrashFirstAccessedCardWithTrashCostEachTurn=True,
            bonusAccessOnHqBreach=1,
        )

    if cid == "safety-first":
        return base(
            c,
            subtypes=["directive", "virtual"],
            handSizeBonus=-2,
            drawAtTurnEndIfGripBelowMaxHandSize=1,
        )

    # --- Sunny ---
    if cid == "sunny-lebeau-security-specialist":
        return base(c, link=c.get("base_link", 2))

    if cid == "security-chip":
        return base(
            c,
            subtypes=["chip"],
            paidAbilities=[
                paid(
                    "security-chip-boost",
                    "[trash]: Chosen icebreaker(s) gain +1 strength per link this run",
                    do("boost_breakers_per_link"),
                    trash_self=True,
                    windows=["runner_action_paw"],
                    usable_by_runner=True,
                    require_during_run=True,
                )
            ],
        )

    if cid == "security-nexus":
        return base(
            c,
            subtypes=["console"],
            unique=True,
            muBonus=1,
            link=1,
            paidAbilities=[
                paid(
                    "security-nexus-trace",
                    "Once per turn → On encounter: Corp traces[5]; success tag+ETR, fail bypass",
                    do("trace_bypass_or_tag_etr"),
                    once_per_turn=True,
                    windows=["runner_action_paw"],
                    usable_by_runner=True,
                    require_during_run=True,
                )
            ],
        )

    if cid == "gs-striker-m1":
        return cloud_breaker(c, "code gate")

    if cid == "gs-shrike-m2":
        return cloud_breaker(c, "sentry")

    if cid == "gs-sherman-m3":
        return cloud_breaker(c, "barrier")

    if cid == "globalsec-security-clearance":
        return base(
            c,
            subtypes=["virtual"],
            installRequiresLinkGte=2,
            onTurnBegin=may(
                seq(
                    do("lose_clicks", side="runner", amount=1),
                    do("reveal_top_of_rd"),
                ),
                label="Lose [click]: Look at the top card of R&D",
                decline_side="runner",
            ),
        )

    if cid == "jak-sinclair":
        return base(
            c,
            subtypes=["connection"],
            installCostReductionPerLink=1,
            onTurnBegin=may(
                do("jak_sinclair_run_without_programs"),
                label="Make a run (cannot use programs)",
                decline_side="runner",
            ),
        )

    # --- Neutral runner ---
    if cid == "employee-strike":
        return base(
            c,
            subtypes=["current"],
            lingerAsCurrent=True,
            currentTrashOnAgendaScored=True,
            blankCorpIdentityPrintedAbilities=True,
        )

    if cid == "windfall":
        return base(
            c,
            onPlay=do("shuffle_trash_top_gain_install_cost"),
        )

    if cid == "technical-writer":
        return base(
            c,
            hostedCreditsOnProgramOrHardwareInstall=1,
            paidAbilities=[
                paid(
                    "technical-writer-take",
                    "[click],[trash]: Take all credits from Technical Writer",
                    do("take_hosted_credits", amount=99),
                    clicks=1,
                    trash_self=True,
                    windows=["runner_action_paw"],
                    usable_by_runner=True,
                )
            ],
        )

    card = base(c)
    card["unsupported"] = [f"Unmapped dad card: {cid}"]
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
    if len(clear_written) != EXPECTED - len(REPRINTS):
        missing = [cid for cid in written if cid not in clear_written]
        print("UNCLEARED=" + json.dumps(missing))
        sys.exit(1)


if __name__ == "__main__":
    main()
