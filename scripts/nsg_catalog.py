#!/usr/bin/env python3
"""Fetch the pinned Null Signal Games v2 catalog for card extract scripts.

Upstream: Null-Signal-Games/netrunner-cards-json (see data/nsg-catalog-pin.json).
Titles live at v2/cards/<id>.json and printings at v2/printings/<set>.json
on the pinned ref. The pack/{code}.json export is no longer read.

Usage:
  python3 scripts/nsg_catalog.py fetch sg
  python3 scripts/nsg_catalog.py fetch ms msbp
  python3 scripts/nsg_catalog.py show-pin
  python3 scripts/nsg_catalog.py check

Generators import load_set_cards(code) from the pinned NSG v2 catalog
(not the live NRDB API). Fails closed on missing pin, HTTP errors, or
invalid JSON.
"""
from __future__ import annotations

import argparse
import io
import json
import re
import sys
import tarfile
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PIN_PATH = ROOT / "data" / "nsg-catalog-pin.json"
# Printed facts a catalog update can change. Ability records stay hand-authored.
FACT_FIELDS = ("faction_id", "cost", "strength", "text")
# Corpus ids minted before the v2 id convention settled. Every other title
# converts by replacing underscores with hyphens (and back).
OUR_ID_EXCEPTIONS = {
    "o_shortage": "o2-shortage",
    "the_wizards_chest": "the-wizard-s-chest",
}
NSG_ID_EXCEPTIONS = {our: nsg for nsg, our in OUR_ID_EXCEPTIONS.items()}
PACK_CODE_RE = re.compile(r"pack\s+\(?([a-z0-9]+)", re.IGNORECASE)


def load_pin() -> dict:
    if not PIN_PATH.is_file():
        raise SystemExit(f"Catalog pin missing: {PIN_PATH}")
    try:
        pin = json.loads(PIN_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise SystemExit(f"Invalid catalog pin JSON ({PIN_PATH}): {e}") from e
    for key in ("repo", "ref", "cacheDir"):
        if not pin.get(key):
            raise SystemExit(f"Catalog pin missing required field {key!r}: {PIN_PATH}")
    return pin


def our_id(nsg_card_id: str) -> str:
    """The corpus title id for a catalog card id."""
    return OUR_ID_EXCEPTIONS.get(nsg_card_id, nsg_card_id.replace("_", "-"))


def nsg_id(our_card_id: str) -> str:
    """The catalog card id for a corpus title id."""
    return NSG_ID_EXCEPTIONS.get(our_card_id, our_card_id.replace("-", "_"))


def card_type(card: dict) -> str | None:
    """Stored type for a v2 card: corp_identity and runner_identity are identity."""
    value = card.get("card_type_id")
    if not isinstance(value, str):
        return None
    return value.removeprefix("corp_").removeprefix("runner_")


def faction_slug(card: dict) -> str | None:
    """Stored faction for a v2 card: haas_bioroid is haas-bioroid here."""
    value = card.get("faction_id")
    if not isinstance(value, str):
        return None
    return value.replace("_", "-")


_SUBTYPE_NAMES: dict[str, str] | None = None


def subtype_names(card: dict) -> list[str]:
    """Stored subtype names for a v2 card, spelled as the vocabulary names them.

    code_gate is written 'code gate' and g_mod is written 'g-mod', so the
    spelling comes from v2/card_subtypes.json rather than the id alone.
    """
    global _SUBTYPE_NAMES
    if _SUBTYPE_NAMES is None:
        _SUBTYPE_NAMES = {
            str(raw["id"]): str(raw["name"]).lower()
            for raw in load_v2_reference("card_subtypes.json")
        }
    return [
        _SUBTYPE_NAMES.get(name, name.replace("_", " "))
        for name in card.get("subtypes") or []
    ]


def read_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise SystemExit(f"Corrupt cached catalog JSON ({path}): {e}") from e


def load_v2_cards(*, force: bool = False) -> dict[str, dict]:
    """Every v2/cards record at the pin, keyed by catalog card id."""
    root = fetch_catalog_archive(force=force)
    cards: dict[str, dict] = {}
    for path in sorted((root / "v2" / "cards").glob("*.json")):
        record = read_json(path)
        card_id = record.get("id") if isinstance(record, dict) else None
        if not isinstance(card_id, str) or not card_id:
            raise SystemExit(f"{path}: v2 card record has no id")
        if card_id in cards:
            raise SystemExit(f"duplicate v2 card id {card_id}")
        cards[card_id] = record
    if not cards:
        raise SystemExit(f"Catalog archive has no v2/cards files: {root}")
    return cards


def load_v2_printings(*, force: bool = False) -> list[dict]:
    """Every v2/printings record at the pin, across all set files."""
    root = fetch_catalog_archive(force=force)
    printings: list[dict] = []
    for path in sorted((root / "v2" / "printings").glob("*.json")):
        records = read_json(path)
        if not isinstance(records, list):
            raise SystemExit(f"{path}: v2 printings file is not a list")
        printings.extend(records)
    if not printings:
        raise SystemExit(f"Catalog archive has no v2/printings files: {root}")
    return printings


def load_card_sets(*, force: bool = False) -> list[dict]:
    root = fetch_catalog_archive(force=force)
    sets = read_json(root / "v2" / "card_sets.json")
    if not isinstance(sets, list):
        raise SystemExit("v2/card_sets.json is not a list")
    return sets


def load_v2_reference(name: str, *, force: bool = False):
    """One top-level v2 reference file, such as factions.json."""
    root = fetch_catalog_archive(force=force)
    return read_json(root / "v2" / name)


def set_id_for_pack(code: str, sets: list[dict] | None = None) -> str:
    """The v2 set id whose legacy_code is a pack code such as sg."""
    for card_set in sets if sets is not None else load_card_sets():
        if card_set.get("legacy_code") == code:
            return str(card_set["id"])
    raise SystemExit(f"No v2 card set has legacy_code {code!r}")


def load_set_cards(code: str, *, force: bool = False) -> list[dict]:
    """v2 card records for one pack code, in printing position order."""
    set_id = set_id_for_pack(code)
    cards = load_v2_cards(force=force)
    ordered = [
        printing
        for printing in load_v2_printings(force=force)
        if printing.get("card_set_id") == set_id
    ]
    ordered.sort(key=lambda printing: printing.get("position", 0))
    found: list[dict] = []
    for printing in ordered:
        card_id = printing.get("card_id")
        record = cards.get(card_id) if isinstance(card_id, str) else None
        if record is None:
            raise SystemExit(f"{set_id}: printing {printing.get('id')!r} has no v2 card {card_id!r}")
        found.append(dict(record))
    return found


CATALOG_PREFIXES = (
    "v2/cards/",
    "v2/printings/",
    "v2/rulings/",
    "v2/formats/",
    "v2/card_pools/",
    "v2/restrictions/",
    "v2/card_sets.json",
    "v2/card_cycles.json",
    "v2/card_types.json",
    "v2/card_subtypes.json",
    "v2/card_set_types.json",
    "v2/card_layouts.json",
    "v2/factions.json",
    "v2/sides.json",
    "v2/ruling_sources.json",
    "rotations.json",
)


def fetch_catalog_archive(*, force: bool = False) -> Path:
    """Cache the pinned catalog files this repo copies. The rulings snapshot is included."""
    pin = load_pin()
    root = ROOT / pin["cacheDir"] / pin["ref"]
    marker = root / "v2" / "card_sets.json"
    if (
        marker.is_file()
        and any((root / "v2" / "rulings").glob("*.json"))
        and any((root / "v2" / "cards").glob("*.json"))
        and any((root / "v2" / "printings").glob("*.json"))
        and not force
    ):
        return root
    repo = pin["repo"].removeprefix("https://github.com/").removesuffix(".git")
    url = f"https://codeload.github.com/{repo}/tar.gz/{pin['ref']}"
    root.mkdir(parents=True, exist_ok=True)
    try:
        body = http_bytes(url, timeout=180)
    except urllib.error.HTTPError as e:
        raise SystemExit(f"Failed to fetch catalog archive (HTTP {e.code}): {url}") from e
    except urllib.error.URLError as e:
        raise SystemExit(f"Failed to fetch catalog archive: {url}\n{e}") from e
    written = 0
    with tarfile.open(fileobj=io.BytesIO(body), mode="r:gz") as archive:
        for member in archive.getmembers():
            if not member.isfile():
                continue
            name = member.name.split("/", 1)[1] if "/" in member.name else member.name
            if not any(name == prefix or name.startswith(prefix) for prefix in CATALOG_PREFIXES):
                continue
            if ".." in Path(name).parts:
                continue
            extracted = archive.extractfile(member)
            if extracted is None:
                continue
            dest = root / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(extracted.read())
            written += 1
    if written == 0:
        raise SystemExit(f"Catalog archive has none of the expected files: {url}")
    return root


def fetch_rulings(*, force: bool = False) -> Path:
    """Cache v2/rulings/*.json from the pinned catalog commit.

    Those files are the NetrunnerDB ruling snapshot the catalog copied in.
    """
    root = fetch_catalog_archive(force=force)
    dest = root / "v2" / "rulings"
    if not any(dest.glob("*.json")):
        raise SystemExit(f"Catalog archive has no v2/rulings files: {dest}")
    return dest


def http_bytes(url: str, timeout: int = 60) -> bytes:
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "netrunner-cards-data",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def github_json(url: str) -> dict:
    try:
        body = http_bytes(url)
    except urllib.error.HTTPError as e:
        raise SystemExit(f"GitHub request failed (HTTP {e.code}): {url}") from e
    except urllib.error.URLError as e:
        raise SystemExit(f"GitHub request failed: {url}\n{e}") from e
    try:
        data = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        raise SystemExit(f"GitHub response is not JSON ({url}): {e}") from e
    if not isinstance(data, dict):
        raise SystemExit(f"GitHub response is not an object: {url}")
    return data


def pack_codes_from_pool(pool: dict) -> set[str]:
    """Pack codes named in pool.json wave notes, such as 'NRDB pack sg'."""
    found: set[str] = set()
    waves = pool.get("waves") or {}
    if not isinstance(waves, dict):
        return found
    for wave in waves.values():
        if isinstance(wave, dict) and isinstance(wave.get("notes"), str):
            found.update(code.lower() for code in PACK_CODE_RE.findall(wave["notes"]))
    return found


def generator_pack_codes() -> set[str]:
    """Pack codes the extract scripts fetch from the pinned catalog."""
    found: set[str] = set()
    for path in (ROOT / "scripts").glob("generate-*.py"):
        for line in path.read_text(encoding="utf-8").splitlines():
            if "nsg_catalog.py fetch" not in line:
                continue
            tail = line.split("nsg_catalog.py fetch", 1)[1].strip()
            for token in tail.split():
                if re.fullmatch(r"[a-z0-9]+", token):
                    found.add(token)
    return found


def card_blobs(tree: dict) -> dict[str, str]:
    """Map catalog card id to git blob sha from a recursive Git tree."""
    blobs: dict[str, str] = {}
    for entry in tree.get("tree") or []:
        if entry.get("type") != "blob":
            continue
        path = entry.get("path") or ""
        if path.startswith("v2/cards/") and path.endswith(".json"):
            blobs[Path(path).stem] = entry.get("sha") or ""
    return blobs


def corpus_card_ids() -> set[str]:
    """Title ids with a rules file under data/<side>/<type>/."""
    return {path.stem for path in (ROOT / "data").glob("*/*/*.json")}


def fetch_card_ref(card_id: str, ref: str, repo: str) -> dict | None:
    """One v2/cards record at an arbitrary ref. None when it does not exist."""
    if not card_id or "/" in card_id or ".." in card_id:
        raise SystemExit(f"Invalid card id: {card_id!r}")
    url = f"https://raw.githubusercontent.com/{repo}/{ref}/v2/cards/{card_id}.json"
    try:
        body = http_bytes(url)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise SystemExit(f"Failed to fetch card {card_id!r} at {ref} (HTTP {e.code}): {url}") from e
    except urllib.error.URLError as e:
        raise SystemExit(f"Failed to fetch card {card_id!r} at {ref}: {url}\n{e}") from e
    try:
        record = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        raise SystemExit(f"Card {card_id!r} at {ref} is not valid JSON ({url}): {e}") from e
    if not isinstance(record, dict):
        raise SystemExit(f"Card {card_id!r} at {ref} is not an object: {url}")
    return record


def diff_card_facts(before: dict | None, after: dict | None) -> list[str]:
    """Changes to faction, cost, strength, or printed text. Empty when none."""
    if before is None:
        return ["added"]
    if after is None:
        return ["removed"]
    changes: list[str] = []
    for field in FACT_FIELDS:
        if before.get(field) == after.get(field):
            continue
        if field == "text":
            changes.append("text changed")
        else:
            changes.append(f"{field}: {before.get(field)!r} → {after.get(field)!r}")
    return changes


def diff_card_sets(old_cards: list[dict], new_cards: list[dict]) -> list[tuple[str, str, list[str]]]:
    """Fact changes between two lists of v2 card records, keyed by card id."""
    old = {str(card["id"]): card for card in old_cards if card.get("id")}
    new = {str(card["id"]): card for card in new_cards if card.get("id")}
    rows: list[tuple[str, str, list[str]]] = []
    for card_id in sorted(set(old) | set(new)):
        changes = diff_card_facts(old.get(card_id), new.get(card_id))
        if not changes:
            continue
        sample = new.get(card_id) or old[card_id]
        rows.append((card_id, str(sample.get("title") or card_id), changes))
    return rows


def cmd_show_pin(_: argparse.Namespace) -> int:
    pin = load_pin()
    print(json.dumps(pin, indent=2, ensure_ascii=False))
    return 0


def cmd_check(_: argparse.Namespace) -> int:
    """Compare the pinned catalog with current main. Prints a report. Does not edit cards."""
    from card_layout import card_file
    pin = load_pin()
    repo = pin["repo"].removeprefix("https://github.com/").removesuffix(".git")
    head = github_json(f"https://api.github.com/repos/{repo}/commits/main")
    head_sha = head.get("sha")
    if not isinstance(head_sha, str):
        raise SystemExit("GitHub did not return a main commit sha")
    pinned = pin["ref"]
    if head_sha == pinned:
        print(f"Catalog pin {pinned} matches main.")
        return 0

    print(f"Catalog pin {pinned}")
    print(f"main        {head_sha}")
    pin_tree = github_json(
        f"https://api.github.com/repos/{repo}/git/trees/{pinned}?recursive=1"
    )
    main_tree = github_json(
        f"https://api.github.com/repos/{repo}/git/trees/{head_sha}?recursive=1"
    )
    if pin_tree.get("truncated") or main_tree.get("truncated"):
        raise SystemExit("GitHub tree listing was truncated; the card diff is incomplete")

    old_blobs = card_blobs(pin_tree)
    new_blobs = card_blobs(main_tree)
    corpus = {nsg_id(card_id) for card_id in corpus_card_ids()}

    added = sorted(set(new_blobs) - set(old_blobs))
    removed = sorted(set(old_blobs) - set(new_blobs))
    modified = sorted(
        card_id
        for card_id in set(old_blobs) & set(new_blobs)
        if old_blobs[card_id] != new_blobs[card_id]
    )
    findings = 0

    new_titles = [card_id for card_id in added if card_id not in corpus]
    if new_titles:
        findings += len(new_titles)
        print("New catalog titles not in the corpus:")
        for card_id in new_titles:
            print(f"  {card_id}")
    if removed:
        known_removed = [card_id for card_id in removed if card_id in corpus]
        other_removed = [card_id for card_id in removed if card_id not in corpus]
        if known_removed:
            findings += len(known_removed)
            print("Corpus titles removed since the pin: " + ", ".join(known_removed))
        if other_removed:
            print("Titles removed since the pin: " + ", ".join(other_removed))

    changed_known = [card_id for card_id in modified if card_id in corpus]
    if not changed_known:
        if findings:
            print(f"{findings} catalog change(s) to review. Card files were not edited.")
            return 1
        print("No corpus card changed faction, cost, strength, or printed text.")
        return 0

    for card_id in changed_known:
        before = fetch_card_ref(card_id, pinned, repo)
        after = fetch_card_ref(card_id, head_sha, repo)
        changes = diff_card_facts(before, after)
        if not changes:
            print(f"{card_id}: card file changed; faction, cost, strength, and text are unchanged")
            continue
        findings += 1
        sample = after or before or {}
        print(f"{card_id} {sample.get('title') or ''}".rstrip())
        for change in changes:
            print(f"  {change}")
        try:
            path = card_file(our_id(card_id))
        except FileNotFoundError:
            continue
        print(f"  card file: {path.relative_to(ROOT)}")
        if "text changed" in changes:
            print("  re-read the ability record; the printed text changed")

    if findings:
        print(f"{findings} catalog change(s) to review. Card files were not edited.")
        return 1
    print("No corpus card changed faction, cost, strength, or printed text.")
    return 0


def cmd_fetch(args: argparse.Namespace) -> int:
    for code in args.codes:
        cards = load_set_cards(code, force=args.force)
        print(f"{code}: {len(cards)} cards in v2 set {set_id_for_pack(code)}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_show = sub.add_parser("show-pin", help="Print data/nsg-catalog-pin.json")
    p_show.set_defaults(func=cmd_show_pin)

    p_fetch = sub.add_parser(
        "fetch", help="Cache the v2 catalog and list the cards in one pack code's set"
    )
    p_fetch.add_argument("codes", nargs="+", help="Pack code(s), e.g. sg su21 rwr")
    p_fetch.add_argument(
        "--force", action="store_true", help="Re-download even if cached"
    )
    p_fetch.set_defaults(func=cmd_fetch)

    p_check = sub.add_parser(
        "check",
        help="Report catalog changes since the pin. Does not edit card files.",
    )
    p_check.set_defaults(func=cmd_check)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
