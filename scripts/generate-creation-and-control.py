#!/usr/bin/env python3
"""Generate Creation and Control card JSON from pinned pack `cac`.

Catalog source: Null-Signal-Games/netrunner-cards-json (see data/nsg-catalog-pin.json).
Fetch with: python3 scripts/nsg_catalog.py fetch cac

Deluxe expansion after Future Proof set-complete (floor v1.93.0).
Titles already clear under earlier waves are treated as reprints: skip emitting
duplicate files; list their ids in pool.json.

Hand-mapped Effect IR only — empty unsupported for set-complete.

Usage: python3 scripts/generate-creation-and-control.py
"""
from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

from nsg_catalog import load_pack_cards

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "creation-and-control"
WAVE = "creation-and-control"
PACK = "cac"
EXPECTED = 55

REPRINTS = {
    "cerebral-overwriter",
    "rielle-kit-peddler-transhuman",
    "atman",
    "paricia",
    "self-modifying-code",
    "professional-contacts",
    "ice-analyzer",
    "dirty-laundry",
    "daily-casts",
}


def slugify(title: str) -> str:
    t = title.replace("™", "").replace("®", "").replace("©", "")
    t = unicodedata.normalize("NFKD", t)
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = t.lower()
    t = t.replace("“", "").replace("”", "").replace('"', "")
    t = t.replace("'", "").replace("’", "").replace("ʼ", "")
    t = t.replace(".", "-").replace(":", " ").replace("!", "").replace("*", "")
    t = t.replace("(", " ").replace(")", " ")
    t = re.sub(r"[^a-z0-9]+", "-", t)
    return t.strip("-")


def strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text or "")


def etr():
    return {"op": "do", "action": {"kind": "end_the_run"}}


def gain(side: str, n: int):
    return {"op": "do", "action": {"kind": "gain_credits", "side": side, "amount": n}}


def draw(side: str, n: int):
    return {"op": "do", "action": {"kind": "draw", "side": side, "amount": n}}


def seq(*effects):
    return {"op": "seq", "effects": list(effects)}


def decline(side: str = "runner"):
    return {"id": "decline", "label": "Decline", "effect": gain(side, 0)}


def do(kind: str, **kwargs):
    return {"op": "do", "action": {"kind": kind, **kwargs}}


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


def bioroid_break_subs(amount: int):
    """Printed lose-click break text is host-handled via bioroid subtype + bioroidBreakMaxSubs."""
    return amount


def map_card(c: dict) -> dict | None:
    cid = slugify(c["title"])
    if cid in REPRINTS:
        return None

    # --- Identities ---
    if cid == "cerebral-imaging-infinite-frontiers":
        return base(c, handSizeEqualsCredits=True, unsupported=[])

    if cid == "custom-biotics-engineered-for-success":
        # Deckbuilding-only (cannot include Jinteki) — Ampere-class clear.
        return base(c, unsupported=[])

    if cid == "next-design-guarding-the-net":
        return base(
            c,
            onGameStart=seq(
                do("next_design_may_install_ice", remaining=3, usedServerIds=[]),
                do("draw_until_hq_has", amount=5),
            ),
            unsupported=[],
        )

    if cid == "the-professor-keeper-of-knowledge":
        # Deckbuilding-only (first copy of each program free influence).
        return base(c, unsupported=[])

    if cid == "exile-streethawk":
        return base(
            c,
            onInstallProgramFromHeap=draw("runner", 1),
            unsupported=[],
        )

    # --- Agendas ---
    if cid == "director-haas-pet-project":
        return base(
            c,
            deckLimit=1,
            onScore=do("haas_pet_project_setup", remaining=3),
            unsupported=[],
        )

    if cid == "efficiency-committee":
        return base(
            c,
            onScore=do("add_agenda_counter", amount=3),
            paidAbilities=[
                {
                    "id": "ec-clicks",
                    "label": "[click], hosted agenda counter: Gain [click][click]",
                    "clickCost": 1,
                    "creditCost": 0,
                    "cost": {"clicks": 1, "agendaCounters": 1},
                    "windows": ["corp_action_paw"],
                    "effect": seq(
                        do("gain_clicks", side="corp", amount=2),
                        do("forbid_advance_this_turn"),
                    ),
                }
            ],
            unsupported=[],
        )

    if cid == "project-wotan":
        return base(
            c,
            onScore=do("add_agenda_counter", amount=3),
            paidAbilities=[
                {
                    "id": "wotan-etr",
                    "label": (
                        "Hosted agenda counter: approached rezzed bioroid "
                        "gains ETR subroutine this run"
                    ),
                    "clickCost": 0,
                    "creditCost": 0,
                    "cost": {"agendaCounters": 1},
                    "windows": ["approach_paw"],
                    "effect": do(
                        "grant_approached_rezzed_bioroid_etr_subroutine_this_run"
                    ),
                }
            ],
            unsupported=[],
        )

    if cid == "sentinel-defense-program":
        return base(
            c,
            onSufferCoreDamage=do("net_damage", amount=1),
            unsupported=[],
        )

    if cid == "gila-hands-arcology":
        return base(
            c,
            paidAbilities=[
                {
                    "id": "gila-gain",
                    "label": "[click], [click]: Gain 3¢",
                    "clickCost": 2,
                    "creditCost": 0,
                    "cost": {"clicks": 2},
                    "windows": ["corp_action_paw"],
                    "effect": gain("corp", 3),
                }
            ],
            unsupported=[],
        )

    # --- Assets ---
    if cid == "alix-t4lb07":
        return base(
            c,
            powerCounterOnAnyCorpInstall=1,
            paidAbilities=[
                {
                    "id": "alix-cash",
                    "label": "[click], [trash]: Gain 2¢ per power counter",
                    "clickCost": 1,
                    "creditCost": 0,
                    "cost": {"clicks": 1, "trashSelf": True},
                    "windows": ["corp_action_paw"],
                    "effect": do(
                        "gain_credits",
                        side="corp",
                        amount=0,
                        tally={
                            "count": "source_power_counters",
                            "per": 2,
                            "side": "source",
                        },
                    ),
                }
            ],
            unsupported=[],
        )

    if cid == "director-haas":
        return base(
            c,
            unique=True,
            allottedClicksBonus=1,
            onTrashWhileAccessed=do(
                "add_to_runner_score_as_agenda", agendaPoints=2
            ),
            unsupported=[],
        )

    if cid == "haas-arcology-ai":
        return base(
            c,
            canAdvance=True,
            paidAbilities=[
                {
                    "id": "haai-clicks",
                    "label": (
                        "[click], hosted advancement counter: Gain [click][click]"
                    ),
                    "clickCost": 1,
                    "creditCost": 0,
                    "cost": {"clicks": 1, "advancementTokens": 1},
                    "windows": ["corp_action_paw"],
                    "oncePerTurn": True,
                    "effect": do("gain_clicks", side="corp", amount=2),
                }
            ],
            unsupported=[],
        )

    if cid == "thomas-haas":
        return base(
            c,
            canAdvance=True,
            paidAbilities=[
                {
                    "id": "thomas-cash",
                    "label": "[trash]: Gain 2¢ per advancement token",
                    "clickCost": 0,
                    "creditCost": 0,
                    "cost": {"trashSelf": True},
                    "windows": ["corp_action_paw"],
                    "effect": do(
                        "gain_credits",
                        side="corp",
                        amount=0,
                        tally={
                            "count": "source_advancement_tokens",
                            "per": 2,
                            "side": "source",
                        },
                    ),
                }
            ],
            unsupported=[],
        )

    if cid == "levy-university":
        return base(
            c,
            paidAbilities=[
                {
                    "id": "levy-u-search",
                    "label": "[click], 1¢: Search R&D for ice → HQ",
                    "clickCost": 1,
                    "creditCost": 1,
                    "cost": {"clicks": 1, "credits": 1},
                    "windows": ["corp_action_paw"],
                    "effect": do("search_rd_type_to_hq", cardType="ice"),
                }
            ],
            unsupported=[],
        )

    if cid == "server-diagnostics":
        return base(
            c,
            trashSelfOnCorpIceInstall=True,
            onTurnBegin=gain("corp", 2),
            unsupported=[],
        )

    # --- Operations ---
    if cid == "bioroid-efficiency-research":
        return base(
            c,
            subtypes=["condition"],
            onPlay=do("ber_rez_bioroid_and_host"),
            onHostFullyBrokenThisEncounter=do("trash_self_and_derez_host"),
            unsupported=[],
        )

    if cid == "successful-demonstration":
        return base(
            c,
            playRequiresUnsuccessfulRunLastTurn=True,
            onPlay=gain("corp", 7),
            unsupported=[],
        )

    # --- Ice ---
    if cid == "heimdall-2-0":
        return base(
            c,
            bioroidBreakMaxSubs=2,
            subroutines=[
                {
                    "id": "heimdall-2-0-core",
                    "text": "Do 1 core damage.",
                    "effect": do("core_damage", amount=1),
                },
                {
                    "id": "heimdall-2-0-core-etr",
                    "text": "Do 1 core damage and end the run.",
                    "effect": seq(do("core_damage", amount=1), etr()),
                },
                {
                    "id": "heimdall-2-0-etr",
                    "text": "End the run.",
                    "effect": etr(),
                },
            ],
            unsupported=[],
        )

    if cid == "howler":
        return base(
            c,
            subroutines=[
                {
                    "id": "howler-install",
                    "text": (
                        "You may install and rez 1 bioroid ice from HQ or "
                        "Archives directly inward, ignoring all costs."
                    ),
                    "effect": do("howler_install_rez_bioroid_inward"),
                }
            ],
            unsupported=[],
        )

    if cid == "ichi-2-0":
        return base(
            c,
            bioroidBreakMaxSubs=2,
            subroutines=[
                {
                    "id": "ichi-2-0-trash-1",
                    "text": "Trash 1 installed program.",
                    "effect": do("trash_own_program"),
                },
                {
                    "id": "ichi-2-0-trash-2",
                    "text": "Trash 1 installed program.",
                    "effect": do("trash_own_program"),
                },
                {
                    "id": "ichi-2-0-trace",
                    "text": (
                        "Trace[3]. If successful, do 1 core damage and "
                        "give the Runner 1 tag."
                    ),
                    "effect": do(
                        "trace",
                        strength=3,
                        onSuccess=seq(
                            do("core_damage", amount=1),
                            do("give_tags", amount=1),
                        ),
                    ),
                },
            ],
            unsupported=[],
        )

    if cid == "minelayer":
        return base(
            c,
            subroutines=[
                {
                    "id": "minelayer-install",
                    "text": (
                        "You may install 1 ice from HQ protecting this "
                        "server, ignoring the install cost."
                    ),
                    "effect": do(
                        "may_install_ice_from_hq_protecting_this_server_ignore_costs"
                    ),
                }
            ],
            unsupported=[],
        )

    if cid == "viktor-2-0":
        return base(
            c,
            bioroidBreakMaxSubs=2,
            paidAbilities=[
                {
                    "id": "viktor-2-0-core",
                    "label": "Hosted power counter: Do 1 core damage",
                    "clickCost": 0,
                    "creditCost": 0,
                    "cost": {"powerCounters": 1},
                    "windows": [
                        "corp_action_paw",
                        "approach_paw",
                        "encounter_paw",
                        "approach_server_paw",
                    ],
                    "effect": do("core_damage", amount=1),
                }
            ],
            subroutines=[
                {
                    "id": "viktor-2-0-trace",
                    "text": (
                        "Trace[2]. If successful, place 1 power counter "
                        "on this ice."
                    ),
                    "effect": do(
                        "trace",
                        strength=2,
                        onSuccess=do("add_power_counter", amount=1),
                    ),
                },
                {
                    "id": "viktor-2-0-etr",
                    "text": "End the run.",
                    "effect": etr(),
                },
            ],
            unsupported=[],
        )

    if cid == "zed-1-0":
        return base(
            c,
            subroutines=[
                {
                    "id": "zed-1-0-core-1",
                    "text": (
                        "If the Runner has lost [click] to break a "
                        "subroutine during this run, do 1 core damage."
                    ),
                    "requireLostClickToBreakThisRun": True,
                    "effect": do("core_damage", amount=1),
                },
                {
                    "id": "zed-1-0-core-2",
                    "text": (
                        "If the Runner has lost [click] to break a "
                        "subroutine during this run, do 1 core damage."
                    ),
                    "requireLostClickToBreakThisRun": True,
                    "effect": do("core_damage", amount=1),
                },
            ],
            unsupported=[],
        )

    if cid == "bastion":
        return base(
            c,
            subroutines=[
                {
                    "id": "bastion-etr",
                    "text": "End the run.",
                    "effect": etr(),
                }
            ],
            unsupported=[],
        )

    if cid == "datapike":
        return base(
            c,
            subroutines=[
                {
                    "id": "datapike-pay",
                    "text": (
                        "The Runner must pay 2¢, if able. If they cannot, "
                        "end the run."
                    ),
                    "effect": do("pay_credits_or_etr", side="runner", amount=2),
                },
                {
                    "id": "datapike-etr",
                    "text": "End the run.",
                    "effect": etr(),
                },
            ],
            unsupported=[],
        )

    # --- Upgrades ---
    if cid == "awakening-center":
        return base(
            c,
            hostsBioroidIceIgnoreInstallCost=True,
            unsupported=[],
        )

    if cid == "tyrs-hand":
        return base(
            c,
            preventSubroutineBreakOnBioroidByTrash=True,
            paidAbilities=[
                {
                    "id": "tyrs-hand-prevent",
                    "label": (
                        "[trash]: Prevent 1 subroutine from being broken "
                        "on bioroid ice protecting this server"
                    ),
                    "clickCost": 0,
                    "creditCost": 0,
                    "cost": {"trashSelf": True},
                    "windows": ["break_interrupt_paw"],
                    "effect": do("prevent_pending_subroutine_break"),
                }
            ],
            unsupported=[],
        )

    # --- Runner events ---
    if cid == "escher":
        return base(
            c,
            runEvent={
                "servers": "hq",
                "onSuccessfulRun": do("escher_may_instead_of_breach"),
            },
            unsupported=[],
        )

    if cid == "exploratory-romp":
        return base(
            c,
            runEvent={
                "servers": "any",
                "onSuccessfulRun": do(
                    "exploratory_romp_may_instead_of_breach", amount=3
                ),
            },
            unsupported=[],
        )

    if cid == "freelance-coding-contract":
        return base(
            c,
            onPlay=do(
                "trash_up_to_grip_cards_gain_credits_each",
                remaining=5,
                per=2,
                types=["program"],
            ),
            unsupported=[],
        )

    if cid == "scavenge":
        return base(
            c,
            playAdditionalCost=do("trash_own_program"),
            onPlay=do("scavenge_install_program"),
            unsupported=[],
        )

    if cid == "levy-ar-lab-access":
        return base(
            c,
            onPlay=seq(
                do("shuffle_grip_and_heap_into_stack"),
                draw("runner", 5),
                do("rfg_self"),
            ),
            unsupported=[],
        )

    # --- Hardware ---
    if cid == "monolith":
        return base(
            c,
            subtypes=["console"],
            unique=True,
            muBonus=3,
            onInstall=do(
                "install_up_to_n_programs_from_grip_discount",
                remaining=3,
                discount=4,
            ),
            paidAbilities=[
                {
                    "id": "monolith-prevent",
                    "label": (
                        "[interrupt] → Trash 1 program from grip: Prevent "
                        "1 core or net damage"
                    ),
                    "clickCost": 0,
                    "creditCost": 0,
                    "cost": {"trashProgramFromGrip": True},
                    "windows": ["damage_interrupt_paw"],
                    "requirePendingDamageTypes": ["core", "net"],
                    "effect": do("prevent_pending_damage", amount=1),
                }
            ],
            unsupported=[],
        )

    if cid == "feedback-filter":
        return base(
            c,
            paidAbilities=[
                {
                    "id": "ff-net",
                    "label": "[interrupt] → 3¢: Prevent 1 net damage",
                    "clickCost": 0,
                    "creditCost": 3,
                    "cost": {"credits": 3},
                    "windows": ["damage_interrupt_paw"],
                    "requirePendingDamageTypes": ["net"],
                    "effect": do("prevent_pending_damage", amount=1),
                },
                {
                    "id": "ff-core",
                    "label": "[interrupt] → [trash]: Prevent up to 2 core damage",
                    "clickCost": 0,
                    "creditCost": 0,
                    "cost": {"trashSelf": True},
                    "windows": ["damage_interrupt_paw"],
                    "requirePendingDamageTypes": ["core"],
                    "effect": do("prevent_pending_damage", amount=2),
                },
            ],
            unsupported=[],
        )

    if cid == "clone-chip":
        return base(
            c,
            paidAbilities=[
                {
                    "id": "clone-chip-install",
                    "label": "[trash]: Install a program from your heap",
                    "clickCost": 0,
                    "creditCost": 0,
                    "cost": {"trashSelf": True},
                    "windows": ["runner_action_paw"],
                    "effect": do("may_install_from_heap", types=["program"]),
                }
            ],
            unsupported=[],
        )

    if cid == "omni-drive":
        return base(
            c,
            hostsAnyProgramMemoryCostLte=1,
            recurringCreditsMax=1,
            recurringSpendFor=["use_program"],
            unsupported=[],
        )

    # --- Programs ---
    if cid == "cloak":
        return base(
            c,
            subtypes=["stealth"],
            recurringCreditsMax=1,
            recurringSpendFor=["use_program"],
            unsupported=[],
        )

    if cid == "dagger":
        return base(
            c,
            paidAbilitiesUseStealthCreditsOnly=True,
            breaker={
                "breaksSubtype": "sentry",
                "strength": 0,
                "breakCredits": 1,
                "breakMaxSubs": 1,
                "pumpCredits": 1,
                "pumpStrength": 5,
            },
            unsupported=[],
        )

    if cid == "chakana":
        return base(
            c,
            onSuccessfulRunOnRd=do("add_virus_counter", amount=1),
            agendaAdvancementRequirementBonusIfVirusCountersGte={
                "threshold": 3,
                "bonus": 1,
            },
            unsupported=[],
        )

    if cid == "cyber-cypher":
        return base(
            c,
            onInstall=do("choose_server_runner"),
            interfaceRequiresChosenServer=True,
            breaker={
                "breaksSubtype": "code gate",
                "strength": 0,
                "breakCredits": 1,
                "breakMaxSubs": 1,
                "pumpCredits": 1,
                "pumpStrength": 1,
            },
            unsupported=[],
        )

    if cid == "sahasrara":
        return base(
            c,
            recurringCreditsMax=2,
            recurringSpendFor=["install_program"],
            unsupported=[],
        )

    if cid == "inti":
        return base(
            c,
            strength=1,
            breaker={
                "breaksSubtype": "barrier",
                "strength": 1,
                "breakCredits": 1,
                "breakMaxSubs": 1,
            },
            paidAbilities=[
                {
                    "id": "inti-pump",
                    "label": "2¢: +1 strength for the remainder of this run",
                    "clickCost": 0,
                    "creditCost": 2,
                    "cost": {"credits": 2},
                    "windows": ["encounter_paw"],
                    "effect": do("pump_strength", amount=1, duration="run"),
                }
            ],
            unsupported=[],
        )

    # --- Resources ---
    if cid == "borrowed-satellite":
        return base(c, link=1, handSizeBonus=1, unsupported=[])

    if cid == "same-old-thing":
        return base(
            c,
            paidAbilities=[
                {
                    "id": "sot-play",
                    "label": "[click], [click], [trash]: Play an event from heap",
                    "clickCost": 2,
                    "creditCost": 0,
                    "cost": {"clicks": 2, "trashSelf": True},
                    "windows": ["runner_action_paw"],
                    "effect": do("may_play_event_from_heap"),
                }
            ],
            unsupported=[],
        )

    if cid == "the-source":
        return base(
            c,
            unique=True,
            agendaAdvancementRequirementBonus=1,
            stealAdditionalCreditsWhileRezzed=3,
            onAgendaScoredOrStolen=do("trash_self"),
            unsupported=[],
        )

    card = base(c)
    text = strip_html(c.get("text") or "")
    plain = re.sub(r"\s+", " ", text).strip()
    card["unsupported"] = [f"Full text not yet mapped to IR: {plain[:240]}"]
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
    clear_written = [
        cid
        for cid in written
        if not json.loads((OUT / f"{cid}.json").read_text()).get("unsupported")
    ]
    partial_written = [cid for cid in written if cid not in clear_written]

    manifest = {
        "pack": WAVE,
        "nrdbPackCode": PACK,
        "count": EXPECTED,
        "written": len(written),
        "reprintSkipped": len(skipped),
        "status": "supported",
        "notes": (
            "Creation and Control (cac) set-complete from floor "
            f"v1.93.0 → v1.94.0. Wrote {len(written)} files; skipped "
            f"{len(skipped)} reprints. Full clears among written: "
            f"{len(clear_written)}; partial: {len(partial_written)}. "
            ""
        ),
        "cards": pool_ids,
        "reprintIdsFromEarlierWaves": sorted(skipped),
        "clears": clear_written,
        "partialMapped": partial_written,
    }
    (OUT / "_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"
    )

    print(f"Wrote {len(written)} cards to {OUT}")
    print(f"Skipped reprints/shared: {len(skipped)}")
    print(
        f"Among written: full={len(clear_written)} "
        f"partial={len(partial_written)}"
    )
    if partial_written:
        print("PARTIAL=" + json.dumps(partial_written))
    print("CLEARS=" + json.dumps(clear_written))
    print("POOL_IDS=" + json.dumps(pool_ids))


if __name__ == "__main__":
    main()
