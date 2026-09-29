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
