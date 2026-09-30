#!/usr/bin/env python3
"""Generate Daedalus Complex (dc) card JSON from pinned pack `dc`.

Fetch: python3 scripts/nrdb_catalog.py fetch dc
Red Sand #1 after Quorum / Flashpoint closer (floor v1.127.0 → v1.128.0).
Reprint skips: none (20/20 new clears).
Follow NRDB stripped_text (not IR-hint paraphrases).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from nrdb_catalog import load_pack_cards
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

OUT = Path(__file__).resolve().parents[1] / "data" / "daedalus-complex"
WAVE = "daedalus-complex"
PACK = "dc"
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
    only_during_archives_run: bool = False,
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
    if only_during_archives_run:
        ab["onlyDuringArchivesRun"] = True
    if require_pending_damage_types:
        ab["requirePendingDamageTypes"] = require_pending_damage_types
    return ab


def trace_sub(strength: int, on_success, on_failure=None) -> dict:
    action: dict = {"kind": "trace", "strength": strength, "onSuccess": on_success}
    if on_failure is not None:
        action["onFailure"] = on_failure
    return {"op": "do", "action": action}


def meat(n: int) -> dict:
    return do("meat_damage", amount=n)


def map_card(c: dict) -> dict | None:
    cid = slugify(c["title"])
    if cid in REPRINTS:
        return None

    if cid == "pushing-the-envelope":
        return base(
            c,
            subtypes=["run"],
            runEvent={
                "servers": "any",
                "icebreakerStrengthBonusIfGripLte": {"gripMax": 2, "bonus": 2},
            },
        )

    if cid == "maw":
        return base(
            c,
            subtypes=["console"],
            unique=True,
            muBonus=2,
            mawFirstAccessNotArchivesNoStealOrTrashForceCorpTrashHq=True,
        )

    if cid == "the-archivist":
        return base(
            c,
            subtypes=["connection"],
            unique=True,
            link=1,
            archivistOnCorpScoresInitiativeOrSecurityTrace=1,
        )

    if cid == "exploit":
        return base(
            c,
            playRequiresSuccessfulAllCentralsThisTurn=True,
            onPlay=do("derez_up_to_ice", max=3),
        )

    if cid == "spot-the-prey":
        return base(
            c,
            onPlay=do("spot_the_prey_expose_non_ice_then_run"),
        )

    if cid == "bio-modeled-network":
        return base(
            c,
            subtypes=["virtual"],
            paidAbilities=[
                paid(
                    "bio-modeled-prevent",
                    "[interrupt] → [trash]: Prevent all but 1 net damage",
                    do("prevent_all_but_n_pending_damage", leave=1),
                    cost={"trashSelf": True},
                    windows=["damage_interrupt_paw"],
                    usable_by_runner=True,
                    require_pending_damage_types=["net"],
                ),
            ],
        )

    if cid == "network-exchange":
        return base(
            c,
            subtypes=["virtual"],
            iceNotInnermostInstallCostIncrease=1,
        )

    if cid == "mad-dash":
        return base(
            c,
            subtypes=["run"],
            runEvent={
                "servers": "any",
                "onRunEnd": do("mad_dash_on_run_end"),
            },
        )

    if cid == "next-wave-2":
        return base(
            c,
            subtypes=["next"],
            onScore=do("next_wave_2_may_core_if_rezzed_next_ice"),
        )

    if cid == "zed-2-0":
        return base(
            c,
            subtypes=["sentry", "bioroid", "ap", "destroyer"],
            bioroidBreakMaxSubs=2,
            subroutines=[
                {
                    "id": "zed-2-0-trash-hw-1",
                    "text": "Trash 1 installed piece of hardware.",
                    "effect": do("trash_hardware", pick="choose"),
                },
                {
                    "id": "zed-2-0-trash-hw-2",
                    "text": "Trash 1 installed piece of hardware.",
                    "effect": do("trash_hardware", pick="choose"),
                },
                {
                    "id": "zed-2-0-core",
                    "text": "If the Runner has lost [click] to break a subroutine during this run, do 2 core damage.",
                    "requireLostClickToBreakThisRun": True,
                    "effect": core(2),
                },
            ],
        )

    if cid == "defense-construct":
        return base(
            c,
            canAdvance=True,
            paidAbilities=[
                paid(
                    "defense-construct-archives",
                    "[trash]: Add 1 facedown card from Archives to HQ per advancement (Archives run)",
                    do("defense_construct_add_facedown_archives_to_hq_per_advancement"),
                    trash_self=True,
                    windows=["corp_action_paw", "approach_paw", "encounter_paw", "approach_server_paw"],
                    require_during_run=True,
                    only_during_archives_run=True,
                ),
            ],
        )

    if cid == "synth-dna-modification":
        return base(
            c,
            synthDnaFirstApSubBrokenEachTurnNetDamage=1,
        )

    if cid == "kakugo":
        return base(
            c,
            subtypes=["barrier", "ap"],
            onPass=net(1),
            subroutines=[
                {
                    "id": "kakugo-etr",
                    "text": "End the run.",
                    "effect": etr(),
                },
            ],
        )

    if cid == "net-analytics":
        return base(
            c,
            netAnalyticsMayDrawWhenRunnerAvoidsOrRemovesTags=True,
        )

    if cid == "sync-bre":
        return base(
            c,
            subtypes=["sentry", "tracer"],
            subroutines=[
                {
                    "id": "sync-bre-tag",
                    "text": "Trace[4]. If successful, give the Runner 1 tag.",
                    "effect": trace_sub(4, do("give_tags", amount=1)),
                },
                {
                    "id": "sync-bre-access",
                    "text": "Trace[2]. If successful, whenever the Runner breaches a server for the remainder of this run, they access 1 fewer card.",
                    "effect": trace_sub(
                        2, do("reduce_breach_access_remainder_of_run", amount=1)
                    ),
                },
            ],
        )

    if cid == "jemison-astronautics-sacrifice-audacity-success":
        return base(
            c,
            subtypes=["corp"],
            jemisonOnForfeitPlaceAdvancementsEqualAgendaPointsPlus1=True,
        )

    if cid == "quarantine-system":
        return base(
            c,
            paidAbilities=[
                paid(
                    "quarantine-rez",
                    "Forfeit an agenda: Rez up to 3 pieces of ice, lowering each by 2¢ per printed AP",
                    do("quarantine_system_rez_up_to_3_ice_discount"),
                    cost={"forfeitAgenda": True},
                    windows=["corp_action_paw"],
                ),
            ],
        )

    if cid == "oberth-protocol":
        return base(
            c,
            unique=True,
            rezAdditionalCostForfeitAgenda=True,
            oberthFirstAdvanceThisServerAdditionalAdvancement=1,
        )

    if cid == "khondi-plaza":
        return base(
            c,
            subtypes=["ritzy"],
            unique=True,
            recurringCreditsMaxEqualsRemoteServers=True,
            recurringSpendFor=["rez_ice_protecting_this_server"],
        )

    if cid == "signal-jamming":
        return base(
            c,
            paidAbilities=[
                paid(
                    "signal-jamming-forbid",
                    "[trash]: Cards cannot be installed until the end of the run (run on this server)",
                    do("signal_jamming_forbid_installs_until_run_end"),
                    trash_self=True,
                    windows=["corp_action_paw", "approach_paw", "encounter_paw", "approach_server_paw"],
                    require_during_run=True,
                    require_this_server=True,
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
