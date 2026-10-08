#!/usr/bin/env python3
"""Generate Earth's Scion (eas) card JSON from pinned pack `eas`.

Fetch: python3 scripts/nsg_catalog.py fetch eas
Red Sand #3 after Terminal Directive Cards (floor v1.130.0 → v1.131.0).
Reprint skips: none (20/20 new clears).
Follow NSG pack stripped_text (not IR-hint paraphrases).
Slug via spin_common.slugify (Rosetta 2.0→rosetta-2-0,
AgInfusion: New Miracles for a New World→aginfusion-new-miracles-for-a-new-world).
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

OUT = Path(__file__).resolve().parents[1] / "data" / "earths-scion"
WAVE = "earths-scion"
PACK = "eas"
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
    if require_during_run:
        ab["requireDuringRun"] = True
    if require_this_server:
        ab["requireThisServer"] = True
    return ab


def breaker(
    c: dict,
    *,
    breaks: str,
    break_credits: int,
    break_max: int = 1,
    pump_credits: int | None = None,
    pump_strength: int | None = None,
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
    card["breaker"] = br
    return card


def map_card(c: dict) -> dict | None:
    cid = slugify(c["title"])
    if cid in REPRINTS:
        return None

    if cid == "berserker":
        return breaker(
            c,
            breaks="barrier",
            break_credits=2,
            break_max=2,
            strengthBonusPerSubroutineOnEncounteredBarrier=1,
        )

    if cid == "persephone":
        card = breaker(
            c,
            breaks="sentry",
            break_credits=2,
            break_max=1,
            pump_credits=1,
            pump_strength=1,
        )
        card["onPassRezzedIce"] = do(
            "may_trash_stack_top_then_trash_rd_per_resolved"
        )
        return card

    if cid == "rubicon-switch":
        return base(
            c,
            unique=True,
            paidAbilities=[
                paid(
                    "rubicon-switch-derez",
                    "Once per turn → [click], X¢: Derez 1 ice with printed rez cost X rezzed this turn",
                    do("derez_rezzed_this_turn"),
                    clicks=1,
                    once_per_turn=True,
                    usable_by_runner=True,
                ),
            ],
        )

    if cid == "aeneas-informant":
        return base(
            c,
            subtypes=["connection"],
            aeneasInformantRevealGainOnAccessWithoutTrash=True,
        )

    if cid == "rosetta-2-0":
        return base(
            c,
            subtypes=["virtual"],
            paidAbilities=[
                paid(
                    "rosetta-2-0-search",
                    "[click], remove an installed program from the game: Search stack for non-virus program, install lowering by RFG cost",
                    do("rosetta_rfg_program_search_install_non_virus"),
                    clicks=1,
                    usable_by_runner=True,
                ),
            ],
        )

    if cid == "adjusted-matrix":
        return base(
            c,
            subtypes=["mod"],
            onInstall=do(
                "gamedragon_may_host_on_icebreaker",
                allowAi=True,
                requireHost=True,
            ),
            hostGainsAiSubtype=True,
            hostGainsLoseClickBreakAnySubroutine=True,
        )

    if cid == "dedicated-processor":
        return base(
            c,
            subtypes=["mod"],
            onInstall=do(
                "gamedragon_may_host_on_icebreaker",
                allowAi=False,
                requireHost=True,
            ),
            hostGainsPumpAbility={"credits": 2, "strength": 4},
        )

    if cid == "inversificator":
        card = breaker(
            c,
            breaks="code gate",
            break_credits=1,
            break_max=1,
            pump_credits=1,
            pump_strength=1,
        )
        card["inversificatorSwapIceAfterFullyBrokeOncePerTurn"] = True
        return card

    if cid == "dadiana-chacon":
        return base(
            c,
            subtypes=["connection"],
            unique=True,
            onTurnBegin={
                "op": "if",
                "cond": {"op": "credits_lte", "side": "runner", "amount": 5},
                "then": gain("runner", 1),
            },
            trashSelfAndMeatDamageWhenCreditsZero=3,
        )

    if cid == "next-opal":
        return base(
            c,
            subtypes=["code gate", "observer", "next"],
            gainsSubroutinesPerRezzedIceWithSubtype={
                "subtype": "next",
                "subroutine": {
                    "id": "next-opal-install",
                    "text": "You may install 1 card from HQ.",
                    "effect": do("may_install_from_hq_paying_costs"),
                },
            },
            subroutines=[],
        )

    if cid == "bioroid-work-crew":
        return base(
            c,
            subtypes=["bioroid"],
            bioroidWorkCrewRequireAfterOperationPaidWindow=True,
            paidAbilities=[
                paid(
                    "bioroid-work-crew-install",
                    "[trash]: Install 1 card from HQ (after playing an operation)",
                    do("may_install_from_hq_paying_costs"),
                    trash_self=True,
                    windows=[
                        "corp_action_paw",
                        "approach_paw",
                        "encounter_paw",
                        "approach_server_paw",
                    ],
                ),
            ],
        )

    if cid == "aginfusion-new-miracles-for-a-new-world":
        return base(
            c,
            subtypes=["division"],
            paidAbilities=[
                paid(
                    "aginfusion-redirect",
                    "Once per turn → Trash approached unrezzed ice: move Runner to outermost of another server",
                    do("aginfusion_trash_approached_unrezzed_redirect"),
                    once_per_turn=True,
                    windows=[
                        "approach_paw",
                        "corp_action_paw",
                    ],
                ),
            ],
        )

    if cid == "bamboo-dome":
        return base(
            c,
            subtypes=["region"],
            installServers=["rd"],
            paidAbilities=[
                paid(
                    "bamboo-dome-arrange",
                    "[click]: Reveal top 3 of R&D; secretly add 1 to HQ; return others to top in any order",
                    do("reveal_top_3"),
                    clicks=1,
                ),
            ],
        )

    if cid == "ben-musashi":
        return base(
            c,
            subtypes=["clone"],
            unique=True,
            persistent=True,
            stealAdditionalCostFromProtectingServer=net(2),
        )

    if cid == "authenticator":
        return base(
            c,
            subtypes=["code gate"],
            onEncounter=may(
                seq(do("give_tags", amount=1), do("bypass_current_ice")),
                label="Take 1 tag to bypass",
            ),
            subroutines=[
                {
                    "id": "authenticator-gain",
                    "text": "The Corp gains 2 credits.",
                    "effect": gain("corp", 2),
                },
                {
                    "id": "authenticator-etr",
                    "text": "End the run.",
                    "effect": etr(),
                },
            ],
        )

    if cid == "henry-phillips":
        return base(
            c,
            subtypes=["sysop"],
            unique=True,
            gainCreditsOnBreakSubThisServerIfTagged=2,
        )

    if cid == "battlement":
        return base(
            c,
            subtypes=["barrier"],
            subroutines=[
                {
                    "id": "battlement-etr-1",
                    "text": "End the run.",
                    "effect": etr(),
                },
                {
                    "id": "battlement-etr-2",
                    "text": "End the run.",
                    "effect": etr(),
                },
            ],
        )

    if cid == "audacity":
        return base(
            c,
            playRequiresOtherCardsInHq=2,
            onPlay=do("trash_hq_place_total_2_advancements"),
        )

    if cid == "red-planet-couriers":
        return base(
            c,
            subtypes=["triple"],
            playAdditionalClicks=2,
            onPlay=do("move_all_advancements"),
        )

    if cid == "owl":
        return base(
            c,
            subtypes=["sentry"],
            subroutines=[
                {
                    "id": "owl-stack",
                    "text": "Add 1 installed program to the top of the stack.",
                    "effect": do("add_installed_program_to_stack_top"),
                },
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
