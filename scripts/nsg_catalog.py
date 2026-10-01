#!/usr/bin/env python3
"""Fetch pinned Null Signal Games pack JSON for card extract scripts.

Upstream: Null-Signal-Games/netrunner-cards-json (see data/nsg-catalog-pin.json).
Pack files live at pack/{code}.json on the pinned ref.

Usage:
  python3 scripts/nsg_catalog.py fetch sg
  python3 scripts/nsg_catalog.py fetch ms msbp
  python3 scripts/nsg_catalog.py show-pin

Generators import load_pack_cards(code) from the pinned NSG pack JSON (not the live NRDB API).
Fails closed on missing pin, HTTP errors, or invalid JSON.
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PIN_PATH = ROOT / "data" / "nsg-catalog-pin.json"


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


def fetch_pack(code: str, *, force: bool = False) -> Path:
    """Download pack/{code}.json for the pinned ref into the local cache.

    Returns the cache path. Exits non-zero on any fetch/parse failure.
    """
    if not code or "/" in code or ".." in code:
        raise SystemExit(f"Invalid pack code: {code!r}")

    pin = load_pin()
    dest = cache_path(pin, code)
    if dest.is_file() and not force:
        return dest

    url = pack_url(pin, code)
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        with urllib.request.urlopen(url, timeout=60) as resp:
            body = resp.read()
    except urllib.error.HTTPError as e:
        raise SystemExit(
            f"Failed to fetch pack {code!r} from pinned catalog "
            f"(HTTP {e.code}): {url}"
        ) from e
    except urllib.error.URLError as e:
        raise SystemExit(
            f"Failed to fetch pack {code!r} from pinned catalog: {url}\n{e}"
        ) from e

    try:
        data = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        raise SystemExit(
            f"Pinned pack {code!r} is not valid JSON ({url}): {e}"
        ) from e

    if not isinstance(data, list):
        raise SystemExit(
            f"Pinned pack {code!r} must be a JSON array of cards; "
            f"got {type(data).__name__}: {url}"
        )

    dest.write_bytes(body)
    return dest


def load_pack_cards(code: str, *, force: bool = False) -> list[dict]:
    """Return card objects from the pinned pack/{code}.json (fetching if needed)."""
    path = fetch_pack(code, force=force)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise SystemExit(f"Corrupt cached pack JSON ({path}): {e}") from e
    if not isinstance(data, list):
        raise SystemExit(f"Cached pack {code!r} is not a JSON array: {path}")
    return data


def cmd_show_pin(_: argparse.Namespace) -> int:
    pin = load_pin()
    print(json.dumps(pin, indent=2, ensure_ascii=False))
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

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
