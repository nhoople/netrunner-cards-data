#!/usr/bin/env python3
"""Generate System Core 2019 card JSON from pinned pack `sc19`.

Catalog source: Null-Signal-Games/netrunner-cards-json (see data/nrdb-catalog-pin.json).
Fetch with: python3 scripts/nrdb_catalog.py fetch sc19

System Core 2019 is the next legacy-backwards wave after Downfall. Magnum Opus
(`mo`) and Magnum Opus Reprint (`mor`) are skipped/absorbed — not corpus waves.

Titles already clear under System Gateway / System Update 2021 are treated as
reprints: skip emitting duplicate files; list their ids in pool.json (SU21 pattern).

Hand-mapped Effect IR only where existing primitives fully cover the card;
everything else lists honest unsupported notes — never invent IR.

Usage: python3 scripts/generate-system-core-2019.py
"""
from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

from nrdb_catalog import load_pack_cards

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "system-core-2019"
WAVE = "system-core-2019"
PACK = "sc19"
EXPECTED = 147

# Already defined (and clear) under system-gateway / system-update-2021.
# Do not emit duplicate files; pool.json still lists these ids for the wave.
REPRINTS = {
    "abagnale",
    "aesops-pawnshop",
    "archer",
    "archived-memories",
    "atman",
    "biotic-labor",
    "career-fair",
    "celebrity-gift",
    "corroder",
    "crisium-grid",
    "daily-business-show",
    "diesel",
    "dirty-laundry",
    "earthrise-hotel",
    "eli-1-0",
    "emergency-shutdown",
    "enigma",
    "femme-fatale",
    "gordian-blade",
    "hedge-fund",
    "hokusai-grid",
    "hortum",
    "hostile-takeover",
    "ice-carver",
    "ice-wall",
    "imp",
    "inside-job",
    "jinteki-personal-evolution",
    "legwork",
    "liberated-account",
    "lotus-field",
    "marilyn-campaign",
    "mimic",
    "networking",
    "nisei-mk-ii",
    "oaktown-renovation",
    "pad-campaign",
    "pop-up-window",
    "professional-contacts",
    "project-atlas",
    "project-beale",
    "project-vitruvius",
    "psychographics",
    "punitive-counterstrike",
    "quetzal-free-spirit",
    "reina-roja-freedom-fighter",
    "retrieval-run",
    "reversed-accounts",
    "rielle-kit-peddler-transhuman",
    "ronin",
    "rototurret",
    "scrubber",
    "snare",
    "sneakdoor-beta",
    "sure-gamble",
    "swordsman",
    "test-run",
    "the-makers-eye",
    "tollbooth",
    "trick-of-light",
    "weyland-consortium-building-a-better-world",
    "wraparound",
    "xanadu",
}


def slugify(title: str) -> str:
    t = title.replace("™", "").replace("®", "").replace("©", "")
    t = unicodedata.normalize("NFKD", t)
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = t.lower()
    t = t.replace("“", "").replace("”", "").replace('"', "")
    t = t.replace("'", "").replace("’", "").replace("ʼ", "")
    t = t.replace(".", "-").replace(":", " ").replace("!", "")
    t = t.replace("(", " ").replace(")", " ")
    t = re.sub(r"[^a-z0-9]+", "-", t)
    return t.strip("-")


def strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text or "")


def etr():
    return {"op": "do", "action": {"kind": "end_the_run"}}


def gain(side: str, n: int):
    return {"op": "do", "action": {"kind": "gain_credits", "side": side, "amount": n}}


def net(n: int):
    return {"op": "do", "action": {"kind": "net_damage", "amount": n}}


def draw(side: str, n: int):
    return {"op": "do", "action": {"kind": "draw", "side": side, "amount": n}}


def seq(*effects):
    return {"op": "seq", "effects": list(effects)}


def breaker_card(
    c,
    subtype,
    strength,
    break_c,
    pump_c=None,
    pump_s=None,
    break_max=None,
    duration=None,
    **extra,
):
    br = {
        "breaksSubtype": subtype,
        "strength": strength,
        "breakCredits": break_c,
    }
    if break_max is not None:
        br["breakMaxSubs"] = break_max
    if pump_c is not None:
        br["pumpCredits"] = pump_c
        br["pumpStrength"] = pump_s if pump_s is not None else 1
    paid = list(extra.pop("paidAbilities", []) or [])
    if pump_c is not None:
        pump_eff = {
            "op": "do",
            "action": {
                "kind": "pump_strength",
                "amount": pump_s if pump_s is not None else 1,
            },
        }
        if duration:
            pump_eff["action"]["duration"] = duration
        label_dur = (
            " for the remainder of this run" if duration == "run" else ""
        )
        paid.append(
            {
                "id": f"{slugify(c['title'])}-pump",
                "label": (
                    f"Pump {c['title']} +{pump_s if pump_s is not None else 1} "
                    f"strength{label_dur}"
                ),
                "clickCost": 0,
                "creditCost": pump_c,
                "cost": {"credits": pump_c},
                "windows": ["encounter_paw"],
                "effect": pump_eff,
            }
        )
    return base(c, breaker=br, paidAbilities=paid, **extra)


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
    if c.get("base_link") is not None:
        card["link"] = c["base_link"]
    if c.get("uniqueness"):
        card["unique"] = True
    card.update(extra)
    return card


def map_card(c: dict) -> dict | None:
    cid = slugify(c["title"])
    if cid in REPRINTS:
        return None

    text = strip_html(c.get("text") or "")
    plain = re.sub(r"\s+", " ", text).strip()

    # --- v1.59.0 kickoff: existing IR only ---

    if cid == "easy-mark":
        return base(c, onPlay=gain("runner", 3), unsupported=[])

    if cid == "beanstalk-royalties":
        return base(c, onPlay=gain("corp", 3), unsupported=[])

    if cid == "wall-of-static":
        return base(
            c,
            subroutines=[
                {
                    "id": "wall-of-static-etr",
                    "text": "End the run.",
                    "effect": etr(),
                }
            ],
            unsupported=[],
        )

    if cid == "akamatsu-mem-chip":
        return base(c, muBonus=1, unsupported=[])

    if cid == "spiderweb":
        return base(
            c,
            subroutines=[
                {
                    "id": "spiderweb-etr-1",
                    "text": "End the run.",
                    "effect": etr(),
                },
                {
                    "id": "spiderweb-etr-2",
                    "text": "End the run.",
                    "effect": etr(),
                },
                {
                    "id": "spiderweb-etr-3",
                    "text": "End the run.",
                    "effect": etr(),
                },
            ],
            unsupported=[],
        )

    # --- v1.60.0 A-slice: existing IR only ---

    if cid == "neural-katana":
        return base(
            c,
            subroutines=[
                {
                    "id": "neural-katana-net",
                    "text": "Do 3 net damage.",
                    "effect": net(3),
                }
            ],
            unsupported=[],
        )

    if cid == "wall-of-thorns":
        return base(
            c,
            subroutines=[
                {
                    "id": "wall-of-thorns-net",
                    "text": "Do 2 net damage.",
                    "effect": net(2),
                },
                {
                    "id": "wall-of-thorns-etr",
                    "text": "End the run.",
                    "effect": etr(),
                },
            ],
            unsupported=[],
        )

    if cid == "armitage-codebusting":
        return base(
            c,
            hostedCreditsOnInstall=12,
            paidAbilities=[
                {
                    "id": "armitage-codebusting-take",
                    "label": "Take 2¢",
                    "clickCost": 1,
                    "creditCost": 0,
                    "cost": {"clicks": 1},
                    "windows": ["runner_action_paw"],
                    "effect": {
                        "op": "do",
                        "action": {"kind": "take_hosted_credits", "amount": 2},
                    },
                }
            ],
            unsupported=[],
        )

    if cid == "hadrians-wall":
        return base(
            c,
            canAdvance=True,
            strengthPerAdvancement=1,
            subroutines=[
                {
                    "id": "hadrians-wall-etr-1",
                    "text": "End the run.",
                    "effect": etr(),
                },
                {
                    "id": "hadrians-wall-etr-2",
                    "text": "End the run.",
                    "effect": etr(),
                },
            ],
            unsupported=[],
        )

    if cid == "ipo":
        return base(
            c,
            endsActionPhase=True,
            onPlay=gain("corp", 13),
            unsupported=[],
        )

    # --- v1.61.0 B-slice: existing IR only ---

    if cid == "battering-ram":
        return breaker_card(
            c,
            "barrier",
            3,
            2,
            1,
            1,
            break_max=2,
            duration="run",
            unsupported=[],
        )

    if cid == "force-of-nature":
        return breaker_card(
            c,
            "code gate",
            1,
            2,
            1,
            1,
            break_max=2,
            unsupported=[],
        )

    if cid == "pipeline":
        return breaker_card(
            c,
            "sentry",
            1,
            1,
            2,
            1,
            break_max=1,
            duration="run",
            unsupported=[],
        )

    if cid == "blue-level-clearance":
        return base(
            c,
            playAdditionalClick=True,
            onPlay=seq(gain("corp", 5), draw("corp", 2)),
            unsupported=[],
        )

    if cid == "adonis-campaign":
        return base(
            c,
            hostedCreditsOnInstall=12,
            onTurnBegin={
                "op": "do",
                "action": {"kind": "take_hosted_credits", "amount": 3},
            },
            unsupported=[],
        )

    # --- v1.62.0 C-slice: existing IR only ---

    if cid == "demara":
        card = breaker_card(
            c,
            "barrier",
            1,
            2,
            2,
            3,
            break_max=2,
            unsupported=[],
        )
        card["paidAbilities"] = list(card.get("paidAbilities") or []) + [
            {
                "id": "demara-bypass",
                "label": "Trash Demara: bypass encountered barrier",
                "clickCost": 0,
                "creditCost": 0,
                "cost": {"trashSelf": True},
                "windows": ["encounter_paw"],
                "requireEncounterSubtype": "barrier",
                "effect": {
                    "op": "do",
                    "action": {
                        "kind": "bypass_current_ice",
                        "requireSubtype": "barrier",
                    },
                },
            }
        ]
        return card

    if cid == "himitsu-bako":
        return base(
            c,
            paidAbilities=[
                {
                    "id": "himitsu-bako-hq",
                    "label": "1¢: Add Himitsu-Bako to HQ",
                    "clickCost": 0,
                    "creditCost": 1,
                    "cost": {"credits": 1},
                    "windows": ["corp_action_paw", "encounter_paw"],
                    "effect": {
                        "op": "do",
                        "action": {"kind": "return_source_to_hq"},
                    },
                }
            ],
            subroutines=[
                {
                    "id": "himitsu-bako-etr",
                    "text": "End the run.",
                    "effect": etr(),
                }
            ],
            unsupported=[],
        )

    if cid == "marked-accounts":
        return base(
            c,
            onTurnBegin={
                "op": "do",
                "action": {"kind": "take_hosted_credits", "amount": 1},
            },
            paidAbilities=[
                {
                    "id": "marked-accounts-load",
                    "label": "[click]: Place 3¢ on Marked Accounts",
                    "clickCost": 1,
                    "creditCost": 0,
                    "cost": {"clicks": 1},
                    "windows": ["corp_action_paw"],
                    "effect": {
                        "op": "do",
                        "action": {"kind": "place_hosted_credits", "amount": 3},
                    },
                }
            ],
            unsupported=[],
        )

    if cid == "modded":
        return base(
            c,
            onPlay={
                "op": "do",
                "action": {
                    "kind": "install_from_grip_discount",
                    "types": ["program", "hardware"],
                    "discount": 3,
                },
            },
            unsupported=[],
        )

    if cid == "chaos-theory-wunderkind":
        return base(c, muBonus=1, unsupported=[])

    # --- v1.63.0 D-slice: existing IR only ---

    if cid == "hunter":
        return base(
            c,
            subroutines=[
                {
                    "id": "hunter-trace-tag",
                    "text": "Trace[3]. If successful, give the Runner 1 tag.",
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "trace",
                            "strength": 3,
                            "onSuccess": {
                                "op": "do",
                                "action": {
                                    "kind": "give_tags",
                                    "amount": 1,
                                },
                            },
                        },
                    },
                }
            ],
            unsupported=[],
        )

    if cid == "caduceus":
        return base(
            c,
            subroutines=[
                {
                    "id": "caduceus-trace-gain",
                    "text": "Trace[3]. If successful, the Corp gains 3[credit].",
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "trace",
                            "strength": 3,
                            "onSuccess": gain("corp", 3),
                        },
                    },
                },
                {
                    "id": "caduceus-trace-etr",
                    "text": "Trace[2]. If successful, end the run.",
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "trace",
                            "strength": 2,
                            "onSuccess": etr(),
                        },
                    },
                },
            ],
            unsupported=[],
        )

    if cid == "yagura":
        return base(
            c,
            subroutines=[
                {
                    "id": "yagura-look",
                    "text": "Look at the top card of R&D. You may add that card to the bottom of R&D.",
                    "effect": {
                        "op": "do",
                        "action": {"kind": "look_top_rd_may_bottom"},
                    },
                },
                {
                    "id": "yagura-net",
                    "text": "Do 1 net damage.",
                    "effect": net(1),
                },
            ],
            unsupported=[],
        )

    if cid == "viktor-1-0":
        return base(
            c,
            subroutines=[
                {
                    "id": "viktor-1-0-core",
                    "text": "Do 1 core damage.",
                    "effect": {
                        "op": "do",
                        "action": {"kind": "core_damage", "amount": 1},
                    },
                },
                {
                    "id": "viktor-1-0-etr",
                    "text": "End the run.",
                    "effect": etr(),
                },
            ],
            unsupported=[],
        )

    if cid == "special-order":
        return base(
            c,
            onPlay={
                "op": "do",
                "action": {"kind": "search_stack_icebreaker"},
            },
            unsupported=[],
        )

    # --- v1.64.0 E-slice: existing IR only ---

    if cid == "heimdall-1-0":
        return base(
            c,
            subroutines=[
                {
                    "id": "heimdall-1-0-core",
                    "text": "Do 1 core damage.",
                    "effect": {
                        "op": "do",
                        "action": {"kind": "core_damage", "amount": 1},
                    },
                },
                {
                    "id": "heimdall-1-0-etr-1",
                    "text": "End the run.",
                    "effect": etr(),
                },
                {
                    "id": "heimdall-1-0-etr-2",
                    "text": "End the run.",
                    "effect": etr(),
                },
            ],
            unsupported=[],
        )

    if cid == "ichi-1-0":
        return base(
            c,
            subroutines=[
                {
                    "id": "ichi-1-0-trash-1",
                    "text": "Trash 1 installed program.",
                    "effect": {
                        "op": "do",
                        "action": {"kind": "trash_program", "pick": "choose"},
                    },
                },
                {
                    "id": "ichi-1-0-trash-2",
                    "text": "Trash 1 installed program.",
                    "effect": {
                        "op": "do",
                        "action": {"kind": "trash_program", "pick": "choose"},
                    },
                },
                {
                    "id": "ichi-1-0-trace",
                    "text": "Trace[1]. If successful, do 1 core damage and give the Runner 1 tag.",
                    "effect": {
                        "op": "do",
                        "action": {
                            "kind": "trace",
                            "strength": 1,
                            "onSuccess": seq(
                                {
                                    "op": "do",
                                    "action": {
                                        "kind": "core_damage",
                                        "amount": 1,
                                    },
                                },
                                {
                                    "op": "do",
                                    "action": {
                                        "kind": "give_tags",
                                        "amount": 1,
                                    },
                                },
                            ),
                        },
                    },
                },
            ],
            unsupported=[],
        )

    if cid == "sea-source":
        return base(
            c,
            playRequiresSuccessfulRunLastTurn=True,
            onPlay={
                "op": "do",
                "action": {
                    "kind": "trace",
                    "strength": 3,
                    "onSuccess": {
                        "op": "do",
                        "action": {"kind": "give_tags", "amount": 1},
                    },
                },
            },
            unsupported=[],
        )

    if cid == "product-placement":
        return base(
            c,
            mustRevealWhenAccessedFromRd=True,
            skipOnAccessFromArchives=True,
            onAccess=gain("corp", 2),
            unsupported=[],
        )

    if cid == "notoriety":
        return base(
            c,
            playRequiresSuccessfulAllCentralsThisTurn=True,
            onPlay={
                "op": "do",
                "action": {
                    "kind": "add_to_runner_score_as_agenda",
                    "agendaPoints": 1,
                },
            },
            unsupported=[],
        )

    card = base(c)
    card["unsupported"] = [
        f"Full text not yet mapped to IR: {plain[:200]}"
    ]
    return card


def main():
    pack = sorted(
        load_pack_cards(PACK),
        key=lambda c: c.get("position", 0),
    )
    assert len(pack) == EXPECTED, len(pack)
    OUT.mkdir(parents=True, exist_ok=True)
    for p in OUT.glob("*.json"):
        p.unlink()

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
    clear_written = sum(
        1
        for cid in written
        if not json.loads((OUT / f"{cid}.json").read_text()).get("unsupported")
    )

    manifest = {
        "pack": WAVE,
        "nrdbPackCode": PACK,
        "count": EXPECTED,
        "written": len(written),
        "reprintSkipped": len(skipped),
        "status": "in-progress",
        "notes": (
            "System Core 2019 (sc19) kickoff v1.59.0. "
            f"Wrote {len(written)} files; skipped {len(skipped)} Gateway/SU21 reprints. "
            f"Kickoff clears among written: {clear_written}."
        ),
        "cards": pool_ids,
        "reprintIdsFromEarlierWaves": sorted(skipped),
        "kickoffClears": [
            "easy-mark",
            "beanstalk-royalties",
            "wall-of-static",
            "akamatsu-mem-chip",
            "spiderweb",
        ],
        "aSliceClears": [
            "neural-katana",
            "wall-of-thorns",
            "armitage-codebusting",
            "hadrians-wall",
            "ipo",
        ],
        "bSliceClears": [
            "battering-ram",
            "force-of-nature",
            "pipeline",
            "blue-level-clearance",
            "adonis-campaign",
        ],
        "cSliceClears": [
            "demara",
            "himitsu-bako",
            "marked-accounts",
            "modded",
            "chaos-theory-wunderkind",
        ],
        "dSliceClears": [
            "hunter",
            "caduceus",
            "yagura",
            "viktor-1-0",
            "special-order",
        ],
        "eSliceClears": [
            "heimdall-1-0",
            "ichi-1-0",
            "sea-source",
            "product-placement",
            "notoriety",
        ],
    }
    (OUT / "_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"
    )

    print(f"Wrote {len(written)} cards to {OUT}")
    print(f"Skipped reprints/shared: {len(skipped)}")
    print(f"Among written: full={clear_written} partial={len(written) - clear_written}")
    print("POOL_IDS=" + json.dumps(pool_ids))


if __name__ == "__main__":
    main()
