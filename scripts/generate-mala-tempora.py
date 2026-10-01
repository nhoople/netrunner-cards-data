#!/usr/bin/env python3
"""Generate Mala Tempora (mt) card JSON from pinned pack `mt`.

Fetch: python3 scripts/nsg_catalog.py fetch mt
Spin cycle after Stalwart (floor v1.96.0 → v1.97.0).
"""
from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

from nsg_catalog import load_pack_cards

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "mala-tempora"
WAVE = "mala-tempora"
PACK = "mt"
EXPECTED = 20

REPRINTS = {
    "reina-roja-freedom-fighter",
    "sundew",
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


def do(kind: str, **kwargs):
    return {"op": "do", "action": {"kind": kind, **kwargs}}


def seq(*effects):
    return {"op": "seq", "effects": list(effects)}


def gain(side: str, n: int):
    return do("gain_credits", side=side, amount=n)


def trace_sub(strength: int, on_success):
    return do("trace", strength=strength, onSuccess=on_success)


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

    if cid == "deep-red":
        return base(
            c,
            muBonus=3,
            muBonusOnlyForCaissaPrograms=True,
            triggerCaissaClickAbilityOnCaissaInstall=True,
        )

    if cid == "knight":
        return base(
            c,
            installOnIce=True,
            paidAbilities=[
                {
                    "id": "knight-break",
                    "label": "2[credit]: Break 1 subroutine on host ice",
                    "clickCost": 0,
                    "creditCost": 2,
                    "cost": {"credits": 2},
                    "windows": ["encounter_paw"],
                    "effect": do("break_host_subroutine"),
                },
                {
                    "id": "knight-host",
                    "label": "[click]: Host on ice not hosting a Caïssa program",
                    "clickCost": 1,
                    "creditCost": 0,
                    "cost": {"clicks": 1},
                    "windows": ["runner_action_paw"],
                    "effect": do("caissa_rook_host"),
                },
            ],
        )

    if cid == "running-interference":
        return base(
            c,
            playAdditionalClick=True,
            runEvent={
                "servers": "any",
                "iceRezAdditionalCostEqualsPrintedRezCost": True,
            },
        )

    if cid == "expert-schedule-analyzer":
        return base(
            c,
            paidAbilities=[
                {
                    "id": "expert-run-hq",
                    "label": "[click]: Run HQ; on success may reveal all cards in HQ instead of breaching",
                    "clickCost": 1,
                    "creditCost": 0,
                    "cost": {"clicks": 1},
                    "windows": ["runner_action_paw"],
                    "effect": gain("runner", 0),
                    "startsRun": {
                        "servers": "hq",
                        "onSuccessfulRun": do(
                            "expert_schedule_analyzer_may_instead_of_breach"
                        ),
                    },
                }
            ],
        )

    if cid == "grifter":
        return base(
            c,
            onRunnerTurnEnd={
                "op": "if",
                "cond": {"op": "successful_run_this_turn"},
                "then": gain("runner", 1),
                "else": do("trash_self"),
            },
        )

    if cid == "torch":
        return base(
            c,
            breaker={
                "breaksSubtype": "code gate",
                "strength": 0,
                "breakCredits": 1,
                "breakMaxSubs": 1,
                "pumpCredits": 1,
                "pumpStrength": 1,
            },
        )

    if cid == "woman-in-the-red-dress":
        return base(
            c,
            onTurnBegin=do("reveal_top_rd_corp_may_draw"),
        )

    if cid == "raymond-flint":
        return base(
            c,
            onEachCorpBadPublicityTake=do("raymond_flint_breach_hq_no_root"),
            paidAbilities=[
                {
                    "id": "raymond-expose",
                    "label": "[trash]: Expose 1 card",
                    "clickCost": 0,
                    "creditCost": 0,
                    "cost": {"trashSelf": True},
                    "windows": ["runner_action_paw"],
                    "effect": do("expose", pick="choose"),
                }
            ],
        )

    if cid == "isabel-mcguire":
        return base(
            c,
            paidAbilities=[
                {
                    "id": "isabel-to-hq",
                    "label": "[click]: Add 1 of your installed cards to HQ",
                    "clickCost": 1,
                    "creditCost": 0,
                    "cost": {"clicks": 1},
                    "windows": ["corp_action_paw"],
                    "effect": do("return_installed_corp_to_hq", pick="choose"),
                }
            ],
        )

    if cid == "hudson-1-0":
        cap = do("cap_run_access_remaining", max=1)
        return base(
            c,
            paidAbilities=[
                {
                    "id": "hudson-break",
                    "label": "Lose [click]: Break 1 subroutine on Hudson 1.0",
                    "clickCost": 1,
                    "creditCost": 0,
                    "cost": {"clicks": 1},
                    "windows": ["encounter_paw"],
                    "usableByRunnerOnSelfIce": True,
                    "effect": do("break_subroutine_on_self", amount=1),
                }
            ],
            subroutines=[
                {
                    "id": "hudson-cap-1",
                    "text": "The Runner cannot access more than 1 card during this run.",
                    "effect": cap,
                },
                {
                    "id": "hudson-cap-2",
                    "text": "The Runner cannot access more than 1 card during this run.",
                    "effect": cap,
                },
            ],
        )

    if cid == "accelerated-diagnostics":
        return base(c, onPlay=do("accelerated_diagnostics"))

    if cid == "unorthodox-predictions":
        return base(c, onScore=do("unorthodox_predictions_on_score"))

    if cid == "city-surveillance":
        return base(
            c,
            onRunnerTurnBegin={
                "op": "choose",
                "chooser": "runner",
                "options": [
                    {
                        "id": "pay",
                        "label": "Pay 1[credit]",
                        "effect": do("lose_credits", side="runner", amount=1),
                    },
                    {
                        "id": "tag",
                        "label": "Take 1 tag",
                        "effect": do("give_tags", amount=1),
                    },
                ],
            },
        )

    if cid == "snoop":
        return base(
            c,
            onEncounter=do("reveal_grip"),
            paidAbilities=[
                {
                    "id": "snoop-counter-reveal",
                    "label": "Hosted power counter: Reveal grip; trash 1 card",
                    "clickCost": 0,
                    "creditCost": 0,
                    "cost": {"powerCounters": 1},
                    "windows": ["encounter_paw"],
                    "effect": do("reveal_grip_may_trash_one"),
                }
            ],
            subroutines=[
                {
                    "id": "snoop-trace",
                    "text": "Trace[3]. If successful, place 1 power counter on Snoop.",
                    "effect": trace_sub(
                        3,
                        on_success=do("add_power_counter", amount=1),
                    ),
                }
            ],
        )

    if cid == "ireress":
        return base(
            c,
            subroutines=[
                {
                    "id": "ireress-lose",
                    "text": "The Runner loses 1[credit] for each bad publicity the Corp has.",
                    "effect": do("runner_lose_credits_equal_corp_bad_publicity"),
                }
            ],
        )

    if cid == "power-shutdown":
        return base(
            c,
            playRequiresRunnerMadeRunLastTurn=True,
            onPlay=do("power_shutdown"),
        )

    if cid == "paper-wall":
        return base(
            c,
            trashSelfWhenFullyBrokenByRunner=True,
            subroutines=[
                {
                    "id": "paper-etr",
                    "text": "End the run.",
                    "effect": do("end_the_run"),
                }
            ],
        )

    if cid == "interns":
        return base(
            c,
            playAdditionalClick=True,
            onPlay=do("install_from_hq_or_archives"),
        )

    card = base(c)
    text = (c.get("text") or "")[:240]
    card["unsupported"] = [f"Full text not yet mapped to IR: {text}"]
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
            f"Mala Tempora (mt) set-complete v1.97.0. Wrote {len(written)}; "
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
