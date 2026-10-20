#!/usr/bin/env python3
"""Generate The Devil and the Dragon (tdatd) card JSON from the pinned v2 set for pack `tdatd`.

Fetch: python3 scripts/nsg_catalog.py fetch tdatd
Kitara #4 after Council of the Crest (floor v1.138.0 → v1.139.0).
Reprint skips: none (20/20 new clears).
Follow NSG v2 stripped_text (not IR-hint paraphrases).
Slug via spin_common.slugify (419: Amoral Scammer→419-amoral-scammer,
Malia Z0L0K4→malia-z0l0k4, SSO Industries: Fueling Innovation→
sso-industries-fueling-innovation, Endless EULA→endless-eula).
"""
from __future__ import annotations

import json
from card_layout import card_file, manifest_file, write_card
from ability_record import classify_card
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from nsg_catalog import card_type, faction_slug, load_set_cards, our_id, subtype_names
from spin_common import (
    base,
    do,
    draw,
    etr,
    nested_unless,
    gain,
    seq,
    slugify,
    write_manifest,
)

OUT = Path(__file__).resolve().parents[1] / "data" / "the-devil-and-the-dragon"
WAVE = "the-devil-and-the-dragon"
PACK = "tdatd"
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
    cid = our_id(c["id"])
    if cid in REPRINTS:
        return None

    if cid == "glut-cipher":
        return base(
            c,
            subtypes=["run", "sabotage"],
            runEvent={
                "servers": "archives",
                "skipBreach": True,
                "onSuccessfulRun": do("tdatd_glut_cipher"),
            },
        )

    if cid == "knobkierie":
        return base(
            c,
            subtypes=["console"],
            muBonus=3,
            muBonusOnlyForVirusPrograms=True,
            unique=True,
            onFirstSuccessfulRunThisTurn=may(
                do("tdatd_knobkierie_place_virus"),
                label="Place 1 virus counter on an installed virus program",
            ),
        )

    if cid == "419-amoral-scammer":
        return base(
            c,
            subtypes=["natural"],
            link=c.get("base_link", 1),
            mayExposeFirstCorpInstallEachTurnUnlessCorpPays=1,
        )

    if cid == "falsified-credentials":
        return base(
            c,
            onPlay=do("tdatd_falsified_credentials"),
        )

    if cid == "rogue-trading":
        return base(
            c,
            subtypes=["job"],
            hostedCreditsOnInstall=18,
            trashWhenHostedCreditsEmpty=True,
            paidAbilities=[
                paid(
                    "rogue-trading-take",
                    "[click], [click]: Take 6¢ from Rogue Trading and take 1 tag",
                    seq(
                        do("take_hosted_credits", amount=6),
                        do("give_tags", amount=1),
                    ),
                    clicks=2,
                    windows=["runner_action_paw"],
                    usable_by_runner=True,
                ),
            ],
        )

    if cid == "because-i-can":
        return base(
            c,
            subtypes=["run"],
            runEvent={
                "servers": "remote",
                "skipBreach": True,
                "onSuccessfulRun": may(
                    do("shuffle_because_i_can_root"),
                    label="Force Corp to shuffle all cards in the root into R&D",
                ),
            },
        )

    if cid == "nyashia":
        return base(
            c,
            powerCountersOnInstall=3,
            maySpendPowerCountersForBonusRdAccess={"max": 1},
        )

    if cid == "consume":
        return base(
            c,
            subtypes=["virus"],
            mayPlaceVirusCounterWhenCorpCardTrashed=True,
            paidAbilities=[
                paid(
                    "consume-cash",
                    "[click]: Gain 2¢ for each hosted virus counter, then remove all virus counters",
                    seq(
                        do(
                            "gain_credits",
                            side="runner",
                            amount=0,
                            tally={
                                "count": "source_virus_counters",
                                "per": 2,
                                "side": "source",
                            },
                        ),
                        do("remove_virus_counters", amount=99),
                    ),
                    clicks=1,
                    windows=["runner_action_paw"],
                    usable_by_runner=True,
                ),
            ],
        )

    if cid == "malia-z0l0k4":
        return base(
            c,
            subtypes=["bioroid"],
            unique=True,
            onRez=do("choose_malia_resource"),
        )

    if cid == "kill-switch":
        return base(
            c,
            subtypes=["current"],
            lingerAsCurrent=True,
            currentTrashOnAgendaStolen=True,
            mustRevealAgendasAccessedFromRd=True,
            onAgendaAccessedOrScored=do(
                "trace",
                strength=3,
                onSuccess=do("core_damage", amount=1),
            ),
        )

    if cid == "tempus":
        return base(
            c,
            subtypes=["ambush"],
            mustRevealWhenAccessedFromRd=True,
            skipOnAccessFromArchives=True,
            onAccess=do(
                "trace",
                strength=3,
                onSuccess=do("resolve_tempus"),
            ),
        )

    if cid == "bio-vault":
        return base(
            c,
            subtypes=["off-site"],
            remoteOnly=True,
            canAdvance=True,
            paidAbilities=[
                paid(
                    "bio-vault-etr",
                    "[trash], 2 hosted advancement counters: End the run",
                    etr(),
                    trash_self=True,
                    cost={"advancementCounters": 2},
                    windows=[
                        "approach_paw",
                        "encounter_paw",
                        "approach_server_paw",
                        "other_priority_window",
                    ],
                ),
            ],
        )

    if cid == "sadaka":
        return base(
            c,
            subtypes=["trap"],
            subroutines=[
                {
                    "id": "sadaka-look",
                    "text": "Look at the top 3 cards of R&D and either arrange them in any order or shuffle R&D. You may draw 1 card.",
                    "effect": seq(
                        do("look_sadaka_top_3"),
                        may(draw("corp", 1), label="Draw 1 card", decline_side="corp"),
                    ),
                },
                {
                    "id": "sadaka-trash",
                    "text": "You may trash 1 card in HQ. If you do, trash 1 resource. Trash Sadaka.",
                    "effect": seq(
                        may(
                            do("trash_sadaka_hq_then_resource"),
                            label="Trash 1 card in HQ; if you do, trash 1 resource",
                            decline_side="corp",
                        ),
                        do("trash_self"),
                    ),
                },
            ],
        )

    if cid == "endless-eula":
        return base(
            c,
            subtypes=["barrier"],
            subroutines=[
                {
                    "id": f"endless-eula-{i}",
                    "text": "End the run unless the Runner pays 1¢.",
                    "effect": nested_unless(
                        "runner",
                        do("lose_credits", side="runner", amount=1),
                        etr(),
                    ),
                }
                for i in range(1, 7)
            ],
        )

    if cid == "sandman":
        return base(
            c,
            subtypes=["code gate"],
            subroutines=[
                {
                    "id": "sandman-bounce-1",
                    "text": "Add an installed Runner card to the grip.",
                    "effect": do("add_installed_runner_to_grip"),
                },
                {
                    "id": "sandman-bounce-2",
                    "text": "Add an installed Runner card to the grip.",
                    "effect": do("add_installed_runner_to_grip"),
                },
            ],
        )

    if cid == "amani-senai":
        return base(
            c,
            subtypes=["character"],
            unique=True,
            onAgendaScoredOrStolen=may(
                do("trace_amani"),
                label="Trace[X] (X = advancement requirement of the agenda)",
                decline_side="corp",
            ),
        )

    if cid == "sso-industries-fueling-innovation":
        return base(
            c,
            subtypes=["division"],
            onCorpTurnEnd=may(
                do("advance_sso_ice"),
                label="Place advancement tokens on ice with no advancements",
                decline_side="corp",
            ),
        )

    if cid == "city-works-project":
        return base(
            c,
            subtypes=["public"],
            installFaceup=True,
            onAccessRequiresInstalled=True,
            onAccess=do("tdatd_city_works_meat"),
        )

    if cid == "oduduwa":
        return base(
            c,
            subtypes=["code gate"],
            unique=True,
            onEncounter=do("tdatd_oduduwa_encounter"),
            subroutines=[
                {
                    "id": "oduduwa-etr-1",
                    "text": "End the run.",
                    "effect": etr(),
                },
                {
                    "id": "oduduwa-etr-2",
                    "text": "End the run.",
                    "effect": etr(),
                },
            ],
        )

    if cid == "rashida-jaheem":
        return base(
            c,
            subtypes=["character"],
            unique=True,
            onTurnBegin=may(
                seq(
                    do("trash_self"),
                    gain("corp", 3),
                    draw("corp", 3),
                ),
                label="Trash Rashida Jaheem to gain 3¢ and draw 3 cards",
                decline_side="corp",
            ),
        )

    card = base(c)
    card["unsupported"] = [f"Unmapped in card: {cid}"]
    return card


def main():
    pack = load_set_cards(PACK)
    assert len(pack) == EXPECTED, len(pack)
    written: list[str] = []
    skipped: list[str] = []
    for raw in pack:
        cid = our_id(raw["id"])
        mapped = map_card(raw)
        if mapped is None:
            skipped.append(cid)
            continue
        mapped["wave"] = WAVE
        write_card(classify_card(mapped))
        written.append(cid)

    pool_ids = [our_id(c["id"]) for c in pack]
    clear_written = [
        cid
        for cid in written
        if not json.loads(card_file(cid).read_text()).get("unsupported")
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
