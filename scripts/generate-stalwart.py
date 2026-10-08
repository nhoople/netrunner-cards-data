#!/usr/bin/env python3
"""Generate Stalwart (st) card JSON from pinned pack `st`.

Fetch: python3 scripts/nsg_catalog.py fetch st
Spin cycle after Opening Moves (floor v1.95.0 → v1.96.0).
"""
from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

from nsg_catalog import load_pack_cards

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "stalwart"
WAVE = "stalwart"
PACK = "st"
EXPECTED = 20

REPRINTS = {
    "prepaid-voicepad",
    "swordsman",
    "elizabeth-mills",
}


def slugify(title: str) -> str:
    t = title.replace("™", "").replace("®", "").replace("©", "")
    t = unicodedata.normalize("NFKD", t)
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = t.lower()
    t = t.replace(""", "").replace(""", "").replace('"', "")
    t = t.replace("'", "").replace("'", "").replace("ʼ", "")
    t = t.replace(".", "-").replace(":", " ").replace("!", "").replace("*", "")
    t = t.replace("(", " ").replace(")", " ")
    t = re.sub(r"[^a-z0-9]+", "-", t)
    return t.strip("-")


def strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text or "")


def do(kind: str, **kwargs):
    return {"op": "do", "action": {"kind": kind, **kwargs}}


def seq(*effects):
    return {"op": "seq", "effects": list(effects)}


def gain(side: str, n: int):
    return do("gain_credits", side=side, amount=n)


def etr_unless_pay_runner(amount: int):
    return do(
        "unless",
        payer="runner",
        cost=do("lose_credits", side="runner", amount=amount),
        instruction=do("end_the_run"),
    )


def etr_unless_trash_program():
    return {
        "op": "choose",
        "chooser": "runner",
        "options": [
            {
                "id": "trash",
                "label": "Trash 1 installed program",
                "effect": do("trash_program", pick="choose"),
            },
            {
                "id": "etr",
                "label": "End the run",
                "effect": do("end_the_run"),
            },
        ],
    }


def etr_unless_core(amount: int):
    return do(
        "unless",
        payer="runner",
        cost=do("core_damage", amount=amount),
        instruction=do("end_the_run"),
    )


def trace_sub(strength: int, on_success, on_failure=None):
    action = {"kind": "trace", "strength": strength, "onSuccess": on_success}
    if on_failure:
        action["onFailure"] = on_failure
    return {"op": "do", "action": action}


def base(c, **extra):
    subtypes = []
    if c.get("keywords"):
        subtypes = [s.strip().lower() for s in c["keywords"].split(" - ")]
    card = {
        "id": slugify(c["title"]),
        "title": c["title"],
        "wave": WAVE,
        "nrdbCode": c["code"],
        "type": c["type_code"],
        "side": "runner" if c["side_code"] == "runner" else "corp",
        "unsupported": [],
    }
    if c.get("faction_code"):
        card["faction"] = c["faction_code"]
    if subtypes:
        card["subtypes"] = subtypes
    if c.get("cost") is not None:
        if c["type_code"] in ("event", "operation"):
            card["playCost"] = c["cost"]
        elif c["type_code"] in ("ice", "asset", "upgrade"):
            card["installCost"] = c["cost"]
            card["rezCost"] = c["cost"]
        else:
            card["installCost"] = c["cost"]
    if c.get("trash_cost") is not None:
        card["trashCost"] = c["trash_cost"]
    if c.get("strength") is not None:
        card["strength"] = c["strength"]
    if c.get("memory_cost") is not None:
        card["memoryCost"] = c["memory_cost"]
    if c.get("advancement_cost") is not None:
        card["advancementRequirement"] = c["advancement_cost"]
    if c.get("agenda_points") is not None:
        card["agendaPoints"] = c["agenda_points"]
    if c.get("uniqueness"):
        card["unique"] = True
    card.update(extra)
    return card


def map_card(c: dict) -> dict | None:
    cid = slugify(c["title"])
    if cid in REPRINTS:
        return None

    if cid == "bishop":
        return base(
            c,
            installOnIce=True,
            hostStrengthModifier=-2,
            paidAbilities=[
                {
                    "id": "bishop-host",
                    "label": "[click]: Host on ice not hosting a Caïssa program",
                    "clickCost": 1,
                    "creditCost": 0,
                    "cost": {"clicks": 1},
                    "windows": ["runner_action_paw"],
                    "effect": do("caissa_bishop_host"),
                }
            ],
        )

    if cid == "scheherazade":
        return base(
            c,
            hostsAnyProgramMemoryCostLte=99,
            maxHostedCards=99,
            gainCreditsWhenRunnerHostsProgramOnSelf=1,
        )

    if cid == "hard-at-work":
        return base(
            c,
            onTurnBegin=seq(
                gain("runner", 2),
                do("lose_clicks", side="runner", amount=1),
            ),
        )

    if cid == "recon":
        return base(
            c,
            runEvent={
                "servers": "any",
                "mayJackOutOnFirstIceEncounter": True,
            },
        )

    if cid == "copycat":
        return base(
            c,
            onPassRezzedIce={
                "op": "choose",
                "chooser": "runner",
                "options": [
                    {
                        "id": "decline",
                        "label": "Decline",
                        "effect": gain("runner", 0),
                    },
                    {
                        "id": "jump",
                        "label": "Trash Copycat and continue from another rezzed copy",
                        "effect": do("copycat_jump_to_rezzed_copy"),
                    },
                ],
            },
        )

    if cid == "leviathan":
        return base(
            c,
            breaker={
                "breaksSubtype": "code gate",
                "strength": 0,
                "breakCredits": 3,
                "breakMaxSubs": 3,
                "pumpCredits": 3,
                "pumpStrength": 5,
            },
            paidAbilities=[
                {
                    "id": "leviathan-pump",
                    "label": "Pump Leviathan +5 strength",
                    "clickCost": 0,
                    "creditCost": 3,
                    "cost": {"credits": 3},
                    "windows": ["encounter_paw"],
                    "effect": do("pump_strength", amount=5),
                }
            ],
        )

    if cid == "eureka":
        return base(
            c,
            playAdditionalClick=True,
            onPlay=do("eureka_reveal_install_or_trash", discount=10),
        )

    if cid == "record-reconstructor":
        return base(
            c,
            onSuccessfulRun=do("record_reconstructor_archives_instead_of_breach"),
        )

    if cid == "wotan":
        return base(
            c,
            subroutines=[
                {
                    "id": "wotan-clicks",
                    "text": "End the run unless the Runner spends [click][click].",
                    "effect": do(
                        "unless",
                        payer="runner",
                        cost=do("lose_clicks", side="runner", amount=2),
                        instruction=do("end_the_run"),
                    ),
                },
                {
                    "id": "wotan-pay",
                    "text": "End the run unless the Runner pays 3[credit].",
                    "effect": etr_unless_pay_runner(3),
                },
                {
                    "id": "wotan-trash",
                    "text": "End the run unless the Runner trashes 1 installed program.",
                    "effect": etr_unless_trash_program(),
                },
                {
                    "id": "wotan-core",
                    "text": "End the run unless the Runner suffers 1 core damage.",
                    "effect": etr_unless_core(1),
                },
            ],
        )

    if cid == "hellion-alpha-test":
        return base(
            c,
            playRequiresRunnerInstalledResourceLastTurn=True,
            onPlay=trace_sub(
                2,
                on_success=do("add_installed_resource_to_stack_top"),
                on_failure=do("give_bad_publicity", amount=1),
            ),
        )

    if cid == "clone-retirement":
        return base(
            c,
            onScore={
                "op": "choose",
                "chooser": "corp",
                "options": [
                    {
                        "id": "decline",
                        "label": "Decline",
                        "effect": gain("corp", 0),
                    },
                    {
                        "id": "remove-bp",
                        "label": "Remove 1 bad publicity",
                        "effect": do("remove_bad_publicity", amount=1),
                    },
                ],
            },
            onSteal=do("give_bad_publicity", amount=1),
        )

    if cid == "shipment-from-sansan":
        return base(
            c,
            playAdditionalClick=True,
            onPlay=do("place_advancements", amount=2),
        )

    if cid == "muckraker":
        return base(
            c,
            onRez=do("give_bad_publicity", amount=1),
            subroutines=[
                {
                    "id": "muck-1",
                    "text": "Trace[1]. If successful, give the Runner 1 tag.",
                    "effect": trace_sub(
                        1,
                        on_success=do("give_tags", amount=1),
                    ),
                },
                {
                    "id": "muck-2",
                    "text": "Trace[2]. If successful, give the Runner 1 tag.",
                    "effect": trace_sub(
                        2,
                        on_success=do("give_tags", amount=1),
                    ),
                },
                {
                    "id": "muck-3",
                    "text": "Trace[3]. If successful, give the Runner 1 tag.",
                    "effect": trace_sub(
                        3,
                        on_success=do("give_tags", amount=1),
                    ),
                },
                {
                    "id": "muck-etr",
                    "text": "End the run if the Runner is tagged.",
                    "effect": {
                        "op": "if",
                        "cond": {"op": "runner_tagged"},
                        "then": do("end_the_run"),
                    },
                },
            ],
        )

    if cid == "the-cleaners":
        return base(c, whileScoredMeatDamageIncrease=1)

    if cid == "off-the-grid":
        return base(
            c,
            remoteOnly=True,
            blocksRunnerRunsOnHostServer=True,
            trashSelfOnCorpSuccessfulHqRun=True,
        )

    if cid == "profiteering":
        return base(c, onScore=do("profiteering_on_score"))

    if cid == "restructure":
        return base(c, onPlay=gain("corp", 15))

    card = base(c)
    text = strip_html(c.get("text") or "")
    card["unsupported"] = [f"Full text not yet mapped to IR: {text[:240]}"]
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
        path = OUT / f"{cid}.json"
        path.write_text(json.dumps(mapped, indent=2, ensure_ascii=False) + "\n")
        written.append(cid)

    pool_ids = [slugify(c["title"]) for c in pack]
    clear_written = [
        cid
        for cid in written
        if not json.loads((OUT / f"{cid}.json").read_text()).get("unsupported")
    ]

    manifest = {
        "pack": WAVE,
        "nrdbPackCode": PACK,
        "count": EXPECTED,
        "written": len(written),
        "reprintSkipped": len(skipped),
        "status": "supported",
        "notes": (
            f"Stalwart (st) set-complete v1.96.0. Wrote {len(written)}; "
            f"skipped {len(skipped)} reprints. Clears: {len(clear_written)}."
        ),
        "cards": pool_ids,
        "reprintIdsFromEarlierWaves": sorted(skipped),
        "clears": clear_written,
    }
    (OUT / "_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"
    )
    print(f"Wrote {len(written)} cards; skipped {len(skipped)}")
    print("CLEARS=" + json.dumps(clear_written))


if __name__ == "__main__":
    main()
