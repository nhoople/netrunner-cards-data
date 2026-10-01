#!/usr/bin/env python3
"""Generate Whispers in Nalubaale (win) card JSON from pinned pack `win`.

Fetch: python3 scripts/nsg_catalog.py fetch win
Kitara #5 after The Devil and the Dragon (floor v1.139.0 → v1.140.0).
Reprint skips: none (20/20 new clears).
Follow NSG pack stripped_text (not IR-hint paraphrases).
Slug via spin_common.slugify (Jackpot!→jackpot, Kamali 1.0→kamali-1-0,
Freedom Khumalo: Crypto-Anarchist→freedom-khumalo-crypto-anarchist,
Mwanza City Grid→mwanza-city-grid, Overseer Matrix→overseer-matrix).
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
    net,
    seq,
    slugify,
    write_manifest,
)

OUT = Path(__file__).resolve().parents[1] / "data" / "whispers-in-nalubaale"
WAVE = "whispers-in-nalubaale"
PACK = "win"
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


def core_damage_unless_trash(card_type: str, label: str) -> dict:
    """Kamali-class: Do 1 core damage unless the Runner trashes 1 installed X."""
    trash_kind = {
        "resource": "trash_resource",
        "hardware": "trash_hardware",
        "program": "trash_program",
    }[card_type]
    return choose(
        "runner",
        [
            {
                "id": f"trash-{card_type}",
                "label": label,
                "effect": do(trash_kind, pick="choose"),
            },
            {
                "id": "core",
                "label": "Suffer 1 core damage",
                "effect": do("core_damage", amount=1),
            },
        ],
    )


def map_card(c: dict) -> dict | None:
    cid = slugify(c["title"])
    if cid in REPRINTS:
        return None

    if cid == "freedom-khumalo-crypto-anarchist":
        return base(
            c,
            subtypes=["cyborg"],
            link=c.get("base_link", 0),
            accessTrashNonAgendaWithVirusEqualPrintedCost=True,
        )

    if cid == "trypano":
        return base(
            c,
            subtypes=["virus", "trojan"],
            installOnIce=True,
            trashHostAtVirus=5,
            onTurnBegin=may(
                do("add_virus_counter", amount=1),
                label="Place 1 virus counter on Trypano",
            ),
        )

    if cid == "contaminate":
        return base(
            c,
            onPlay=do("win_contaminate"),
        )

    if cid == "embezzle":
        return base(
            c,
            subtypes=["run", "sabotage"],
            runEvent={
                "servers": "hq",
                "skipBreach": True,
                "onSuccessfulRun": do("win_embezzle"),
            },
        )

    if cid == "slipstream":
        return base(
            c,
            subtypes=["virtual"],
            onPassRezzedIce=may(
                do("win_slipstream"),
                label="Trash Slipstream to move to ice in the same position protecting a central",
            ),
        )

    if cid == "laamb":
        return base(
            c,
            subtypes=["icebreaker", "fracter"],
            breaker={
                "breaksSubtype": "barrier",
                "strength": c.get("strength", 2),
                "breakCredits": 2,
                "breakMaxSubs": 99,
                "pumpCredits": 3,
                "pumpStrength": 6,
            },
            onEncounterMayPayCreditsGrantIceSubtype={
                "credits": 2,
                "subtype": "barrier",
                "oncePerTurn": True,
            },
        )

    if cid == "gebrselassie":
        return base(
            c,
            subtypes=["mod"],
            unique=True,
            paidAbilities=[
                paid(
                    "gebrselassie-host",
                    "[click]: Host Gebrselassie on an installed non-AI icebreaker",
                    do("win_gebrselassie_host"),
                    clicks=1,
                    windows=["runner_action_paw"],
                    usable_by_runner=True,
                ),
            ],
            hostIcebreakerStrengthIncreasesLastRemainderOfTurn=True,
        )

    if cid == "compile":
        return base(
            c,
            subtypes=["run"],
            runEvent={
                "servers": "any",
                "onFirstEncounterThisRun": may(
                    do("win_compile_install_program"),
                    label="Search stack or heap for a program and install it, ignoring all costs",
                ),
                "onRunEnd": do("win_compile_bottom_of_stack"),
            },
        )

    if cid == "logic-bomb":
        return base(
            c,
            subtypes=["virtual"],
            paidAbilities=[
                paid(
                    "logic-bomb-bypass",
                    "[trash]: Bypass the ice you are encountering; lose remaining clicks",
                    seq(
                        do("win_bypass_encountered_ice"),
                        do("win_lose_remaining_clicks"),
                    ),
                    trash_self=True,
                    windows=["encounter_paw"],
                    usable_by_runner=True,
                ),
            ],
        )

    if cid == "jackpot":
        return base(
            c,
            onTurnBegin=may(
                do("win_jackpot_place_credit"),
                label="Place 1¢ on Jackpot!",
            ),
            onAgendaAddedToRunnerScore=may(
                do("win_jackpot_take_credits"),
                label="Take any number of credits from Jackpot! and trash it",
            ),
        )

    if cid == "remote-enforcement":
        return base(
            c,
            subtypes=["security"],
            onAgendaScored=may(
                do("win_remote_enforcement"),
                label="Search R&D for ice, install protecting a remote (paying install), rez ignoring rez cost, shuffle R&D",
                decline_side="corp",
            ),
        )

    if cid == "kamali-1-0":
        return base(
            c,
            subtypes=["sentry", "bioroid", "destroyer", "ap"],
            paidAbilities=[
                paid(
                    "kamali-break",
                    "Lose [click]: Break 1 subroutine on Kamali 1.0",
                    do("break_subroutine_on_self", amount=1),
                    clicks=1,
                    windows=["encounter_paw"],
                    usable_by_runner=True,
                ),
            ],
            subroutines=[
                {
                    "id": "kamali-resource",
                    "text": "Do 1 core damage unless the Runner trashes 1 installed resource.",
                    "effect": core_damage_unless_trash(
                        "resource", "Trash 1 installed resource"
                    ),
                },
                {
                    "id": "kamali-hardware",
                    "text": "Do 1 core damage unless the Runner trashes 1 installed piece of hardware.",
                    "effect": core_damage_unless_trash(
                        "hardware", "Trash 1 installed piece of hardware"
                    ),
                },
                {
                    "id": "kamali-program",
                    "text": "Do 1 core damage unless the Runner trashes 1 installed program.",
                    "effect": core_damage_unless_trash(
                        "program", "Trash 1 installed program"
                    ),
                },
            ],
        )

    if cid == "warden-fatuma":
        return base(
            c,
            subtypes=["character"],
            unique=True,
            bioroidIceGainsLoseClickSubroutineBeforeOthers=True,
        )

    if cid == "viral-weaponization":
        return base(
            c,
            subtypes=["research", "security"],
            onScoreTurnEnd=do("win_viral_weaponization"),
        )

    if cid == "envelope":
        return base(
            c,
            subtypes=["barrier", "ap"],
            subroutines=[
                {
                    "id": "envelope-net",
                    "text": "Do 1 net damage.",
                    "effect": net(1),
                },
                {
                    "id": "envelope-etr",
                    "text": "End the run.",
                    "effect": etr(),
                },
            ],
        )

    if cid == "mwanza-city-grid":
        return base(
            c,
            subtypes=["region"],
            hqOrRdRootOnly=True,
            bonusAccessOnHqBreach=3,
            bonusAccessOnRdBreach=3,
            gainCreditsPerCardAccessedDuringBreach=2,
            limitOnePerServer=True,
        )

    if cid == "standard-procedure":
        return base(
            c,
            playRequiresSuccessfulRunLastTurn=True,
            onPlay=do("win_standard_procedure"),
        )

    if cid == "intake":
        return base(
            c,
            subtypes=["ambush"],
            mustRevealWhenAccessedFromRd=True,
            skipOnAccessFromArchives=True,
            onAccess=do(
                "trace",
                strength=4,
                onSuccess=do("win_intake_bounce"),
            ),
        )

    if cid == "masvingo":
        return base(
            c,
            subtypes=["barrier"],
            canAdvance=True,
            onRez=do("win_place_advancement_on_self", amount=1),
            gainsSubroutinesPerAdvancement={
                "subroutine": {
                    "id": "masvingo-etr",
                    "text": "End the run.",
                    "effect": etr(),
                }
            },
            subroutines=[],
        )

    if cid == "overseer-matrix":
        return base(
            c,
            persistent=True,
            mayPayCreditsToTagWhenRunnerTrashesFromThisServerOrRoot={
                "credits": 1,
                "tags": 1,
            },
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
