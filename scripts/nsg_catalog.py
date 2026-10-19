#!/usr/bin/env python3
"""Fetch pinned Null Signal Games pack JSON for card extract scripts.

Upstream: Null-Signal-Games/netrunner-cards-json (see data/nsg-catalog-pin.json).
Pack files live at pack/{code}.json on the pinned ref.

Usage:
  python3 scripts/nsg_catalog.py fetch sg
  python3 scripts/nsg_catalog.py fetch ms msbp
  python3 scripts/nsg_catalog.py show-pin
  python3 scripts/nsg_catalog.py check

Generators import load_pack_cards(code) from the pinned NSG pack JSON (not the live NRDB API).
Fails closed on missing pin, HTTP errors, or invalid JSON.
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
POOL_PATH = ROOT / "data" / "pool.json"
# Printed facts a catalog update can change. Ability records stay hand-authored.
FACT_FIELDS = ("faction_code", "cost", "strength", "text")
# Documented non-corpus packs. A new code outside this set is a new set.
OUTSIDE_CORPUS = {"napd", "tdc", "sm"}
PACK_CODE_RE = re.compile(r"pack\s+\(?([a-z0-9]+)", re.IGNORECASE)


def load_pin() -> dict:
    if not PIN_PATH.is_file():
        raise SystemExit(f"Catalog pin missing: {PIN_PATH}")
    try:
        pin = json.loads(PIN_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise SystemExit(f"Invalid catalog pin JSON ({PIN_PATH}): {e}") from e
    for key in ("repo", "ref", "rawUrlTemplate", "cacheDir", "packPathTemplate"):
        if not pin.get(key):
            raise SystemExit(f"Catalog pin missing required field {key!r}: {PIN_PATH}")
    return pin


def pack_url(pin: dict, code: str) -> str:
    return (
        pin["rawUrlTemplate"]
        .replace("{ref}", pin["ref"])
        .replace("{code}", code)
    )


def cache_path(pin: dict, code: str) -> Path:
    return ROOT / pin["cacheDir"] / pin["ref"] / "pack" / f"{code}.json"


def fetch_pack_ref(code: str, ref: str, *, force: bool = False) -> Path:
    """Download pack/{code}.json at ref into the local cache."""
    if not code or "/" in code or ".." in code or not ref or "/" in ref:
        raise SystemExit(f"Invalid pack code or ref: {code!r} {ref!r}")

    pin = load_pin()
    dest = ROOT / pin["cacheDir"] / ref / "pack" / f"{code}.json"
    if dest.is_file() and not force:
        return dest

    url = pin["rawUrlTemplate"].replace("{ref}", ref).replace("{code}", code)
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        body = http_bytes(url)
    except urllib.error.HTTPError as e:
        raise SystemExit(
            f"Failed to fetch pack {code!r} at {ref} (HTTP {e.code}): {url}"
        ) from e
    except urllib.error.URLError as e:
        raise SystemExit(f"Failed to fetch pack {code!r} at {ref}: {url}\n{e}") from e

    try:
        data = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        raise SystemExit(f"Pack {code!r} at {ref} is not valid JSON ({url}): {e}") from e
    if not isinstance(data, list):
        raise SystemExit(
            f"Pack {code!r} at {ref} must be a JSON array of cards; "
            f"got {type(data).__name__}: {url}"
        )
    dest.write_bytes(body)
    return dest


def fetch_pack(code: str, *, force: bool = False) -> Path:
    """Download pack/{code}.json for the pinned ref into the local cache.

    Returns the cache path. Exits non-zero on any fetch/parse failure.
    """
    return fetch_pack_ref(code, load_pin()["ref"], force=force)


def read_pack(path: Path) -> list[dict]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise SystemExit(f"Corrupt cached pack JSON ({path}): {e}") from e
    if not isinstance(data, list):
        raise SystemExit(f"Cached pack is not a JSON array: {path}")
    return data


def load_pack_cards(code: str, *, force: bool = False) -> list[dict]:
    """Return card objects from the pinned pack/{code}.json (fetching if needed)."""
    return read_pack(fetch_pack(code, force=force))


CATALOG_PREFIXES = (
    "v2/rulings/",
    "v2/formats/",
    "v2/card_pools/",
    "v2/restrictions/",
    "v2/card_sets.json",
    "v2/card_cycles.json",
    "rotations.json",
)


def fetch_catalog_archive(*, force: bool = False) -> Path:
    """Cache the pinned catalog files this repo copies. The rulings snapshot is included."""
    pin = load_pin()
    root = ROOT / pin["cacheDir"] / pin["ref"]
    marker = root / "v2" / "card_sets.json"
    if marker.is_file() and any((root / "v2" / "rulings").glob("*.json")) and not force:
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


def corpus_pack_codes(pool: dict) -> set[str]:
    return pack_codes_from_pool(pool) | generator_pack_codes()


def pack_blobs(tree: dict) -> dict[str, str]:
    """Map pack code to git blob sha from a recursive Git tree."""
    blobs: dict[str, str] = {}
    for entry in tree.get("tree") or []:
        if entry.get("type") != "blob":
            continue
        path = entry.get("path") or ""
        if path.startswith("pack/") and path.endswith(".json"):
            blobs[Path(path).stem] = entry.get("sha") or ""
    return blobs


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


def diff_pack_facts(old_cards: list[dict], new_cards: list[dict]) -> list[tuple[str, str, list[str]]]:
    old = {str(card["code"]): card for card in old_cards if card.get("code")}
    new = {str(card["code"]): card for card in new_cards if card.get("code")}
    rows: list[tuple[str, str, list[str]]] = []
    for code in sorted(set(old) | set(new)):
        changes = diff_card_facts(old.get(code), new.get(code))
        if not changes:
            continue
        sample = new.get(code) or old[code]
        rows.append((code, str(sample.get("title") or code), changes))
    return rows


def cmd_show_pin(_: argparse.Namespace) -> int:
    pin = load_pin()
    print(json.dumps(pin, indent=2, ensure_ascii=False))
    return 0


def local_cards_by_code() -> dict[str, Path]:
    """Map a printing code to the rules file for that title."""
    from card_layout import card_file

    found: dict[str, Path] = {}
    directory = ROOT / "data" / "printings"
    if not directory.is_dir():
        return found
    for path in directory.glob("*.json"):
        try:
            printing = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        code = printing.get("code")
        card_id = printing.get("cardId")
        if isinstance(code, str) and isinstance(card_id, str):
            found[code] = card_file(card_id)
    return found


def cmd_check(_: argparse.Namespace) -> int:
    """Compare the pinned catalog with current main. Prints a report. Does not edit cards."""
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
        raise SystemExit("GitHub tree listing was truncated; the pack diff is incomplete")

    old_blobs = pack_blobs(pin_tree)
    new_blobs = pack_blobs(main_tree)
    pool = json.loads(POOL_PATH.read_text(encoding="utf-8"))
    known = corpus_pack_codes(pool)
    local = local_cards_by_code()

    added = sorted(set(new_blobs) - set(old_blobs))
    removed = sorted(set(old_blobs) - set(new_blobs))
    modified = sorted(
        code for code in set(old_blobs) & set(new_blobs) if old_blobs[code] != new_blobs[code]
    )
    findings = 0

    new_sets = [code for code in added if code not in known and code not in OUTSIDE_CORPUS]
    if new_sets:
        findings += len(new_sets)
        print("New packs not in pool.json:")
        for code in new_sets:
            print(f"  {code}")
    outside = [code for code in added if code in OUTSIDE_CORPUS]
    if outside:
        print("New packs already outside the corpus: " + ", ".join(outside))
    if removed:
        known_removed = [code for code in removed if code in known]
        other_removed = [code for code in removed if code not in known]
        if known_removed:
            findings += len(known_removed)
            print("Corpus packs removed since the pin: " + ", ".join(known_removed))
        if other_removed:
            print("Packs removed since the pin: " + ", ".join(other_removed))

    changed_known = [code for code in modified if code in known]
    if not changed_known:
        if findings:
            print(f"{findings} catalog change(s) to review. Card files were not edited.")
            return 1
        print("No corpus pack changed faction, cost, strength, or printed text.")
        return 0

    for code in changed_known:
        old_cards = read_pack(fetch_pack_ref(code, pinned))
        new_cards = read_pack(fetch_pack_ref(code, head_sha))
        rows = diff_pack_facts(old_cards, new_cards)
        if not rows:
            print(f"{code}: pack file changed; faction, cost, strength, and text are unchanged")
            continue
        findings += len(rows)
        print(f"{code}:")
        for card_code, title, changes in rows:
            print(f"  {card_code} {title}")
            for change in changes:
                print(f"    {change}")
            path = local.get(card_code)
            if path is not None:
                print(f"    card file: {path.relative_to(ROOT)}")
            if "text changed" in changes:
                print("    re-read the ability record; the printed text changed")

    if findings:
        print(f"{findings} catalog change(s) to review. Card files were not edited.")
        return 1
    print("No corpus pack changed faction, cost, strength, or printed text.")
    return 0


def cmd_fetch(args: argparse.Namespace) -> int:
    for code in args.codes:
        path = fetch_pack(code, force=args.force)
        cards = load_pack_cards(code)
        print(f"{code}: {len(cards)} cards → {path}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_show = sub.add_parser("show-pin", help="Print data/nsg-catalog-pin.json")
    p_show.set_defaults(func=cmd_show_pin)

    p_fetch = sub.add_parser(
        "fetch", help="Download pack/{code}.json for the pinned ref"
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
