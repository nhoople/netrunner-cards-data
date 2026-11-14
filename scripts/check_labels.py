#!/usr/bin/env python3
"""Printed-text label report (CR audit tool 1.4).

Reports three gaps and keeps them in a shrink-only baseline,
`scripts/baselines/labels.json`:

- unlabelled: conditional and play abilities with no `label`.
- drift: printed wording on an ability (`label` on paid abilities, `text`
  on subroutines) whose normalized form is not found in the card's
  normalized `data/printed/<id>.json` `strippedText` (or any face's).
- unsupported: cards with a non-empty `unsupported` list.

Wording differences are a report. CI fails only when the current entries and
the baseline differ: a new entry is a regression, and an entry that went away
means the baseline needs regenerating so it keeps shrinking.

    python3 scripts/check_labels.py            # compare with the baseline
    python3 scripts/check_labels.py --write    # regenerate the baseline
    python3 scripts/check_labels.py --report   # also list the worst drift
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
BASELINE = ROOT / "scripts" / "baselines" / "labels.json"
REGENERATE = "python3 scripts/check_labels.py --write"

LABEL_FIELD = {"paid": "label", "subroutine": "text"}
NEEDS_LABEL = ("conditional", "play")

_TAG = re.compile(r"<[^>]+>")
_SYMBOL = re.compile(r"\[([a-z][a-z-]*)\]")
_APOSTROPHE = re.compile(r"['’ʼ‘]")
_CREDITS = re.compile(r"\bcredits\b")
_NON_WORD = re.compile(r"[^a-z0-9]+")


def normalize(text: str) -> str:
    """Fold printed or label wording to lowercase words split by single spaces.

    Symbol tokens (`[click]` or `{click}`), `¢`, `->`/`→`, HTML, accents,
    apostrophes and punctuation all collapse, and "credits" folds to
    "credit", so "1[credit]", "1¢" and "1 credit" compare equal, and
    "[click], [trash]:" equals "click,trash:".
    """
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower()
    text = _TAG.sub(" ", text)
    text = text.replace("{", "[").replace("}", "]")
    text = _SYMBOL.sub(lambda m: " " + m.group(1).replace("-", " ") + " ", text)
    text = text.replace("¢", " credit ").replace("→", " ").replace("->", " ")
    text = _APOSTROPHE.sub("", text)
    text = _NON_WORD.sub(" ", text)
    text = _CREDITS.sub("credit", text)
    return " ".join(text.split())


def printed_texts(printed: dict) -> list[str]:
    """Normalized strippedText of the card and of each face."""
    texts = [printed.get("strippedText", "")]
    texts += [face.get("strippedText", "") for face in printed.get("faces") or []]
    return [normalize(t) for t in texts if t]


def label_found(label: str, printed: dict) -> bool:
    needle = f" {normalize(label)} "
    return any(needle in f" {hay} " for hay in printed_texts(printed))


def missing_words(label: str, printed: dict) -> list[str]:
    """Label words that appear nowhere in the printed text."""
    vocab = set(" ".join(printed_texts(printed)).split())
    return [w for w in normalize(label).split() if w not in vocab]


def drift_rank(label: str, printed: dict) -> tuple[int, float]:
    """Sort key, worst first: more missing words, then lower word coverage."""
    words = normalize(label).split()
    missing = len(missing_words(label, printed))
    return (-missing, 1 - missing / len(words) if words else 0.0)


def card_paths() -> list[Path]:
    return sorted(DATA.glob("corp/*/*.json")) + sorted(DATA.glob("runner/*/*.json"))


def collect() -> tuple[dict, dict[str, dict]]:
    """Current entries (baseline shape) and the printed record per card id."""
    unlabelled: dict[str, list[str]] = {}
    drift: dict[str, list[str]] = {}
    unsupported: list[str] = []
    printed_by_id: dict[str, dict] = {}
    for path in card_paths():
        card = json.loads(path.read_text(encoding="utf-8"))
        cid = card["id"]
        printed_path = DATA / "printed" / f"{cid}.json"
        printed = json.loads(printed_path.read_text(encoding="utf-8")) if printed_path.is_file() else {}
        printed_by_id[cid] = printed
        if card.get("unsupported"):
            unsupported.append(cid)
        for index, ability in enumerate(card.get("abilities") or []):
            cls = ability.get("class")
            if cls in NEEDS_LABEL and not ability.get("label"):
                unlabelled.setdefault(cid, []).append(f"{index}:{cls}")
            field = LABEL_FIELD.get(cls)
            wording = ability.get(field) if field else None
            if wording and not label_found(wording, printed):
                drift.setdefault(cid, []).append(wording)
    entries = {
        "unlabelled": {k: sorted(v) for k, v in sorted(unlabelled.items())},
        "drift": {k: sorted(set(v)) for k, v in sorted(drift.items())},
        "unsupported": sorted(unsupported),
    }
    return entries, printed_by_id


def flatten(entries: dict) -> dict[str, set[str]]:
    out: dict[str, set[str]] = {}
    for section in ("unlabelled", "drift"):
        out[section] = {f"{cid} {item}" for cid, items in entries.get(section, {}).items() for item in items}
    out["unsupported"] = set(entries.get("unsupported", []))
    return out


def counts(entries: dict) -> dict[str, int]:
    return {section: len(items) for section, items in flatten(entries).items()}


def baseline_document(entries: dict) -> dict:
    return {
        "_comment": (
            "Shrink-only baseline for scripts/check_labels.py (CR audit tool 1.4). "
            f"Regenerate with `{REGENERATE}`; never add entries by hand."
        ),
        "counts": counts(entries),
        **entries,
    }


def worst_drift(entries: dict, printed_by_id: dict[str, dict], limit: int) -> list[tuple[list[str], str, str]]:
    """The `limit` drift entries with the most label words absent from the printed text."""
    rows = [
        (drift_rank(label, printed_by_id.get(cid, {})), cid, label)
        for cid, labels in entries["drift"].items()
        for label in labels
    ]
    rows.sort()
    return [(missing_words(label, printed_by_id.get(cid, {})), cid, label) for _, cid, label in rows[:limit]]


def compare(current: dict, baseline: dict) -> list[str]:
    """Problems that fail CI: new entries, and entries gone from the data."""
    problems: list[str] = []
    now, then = flatten(current), flatten(baseline)
    for section in ("unlabelled", "drift", "unsupported"):
        for item in sorted(now[section] - then[section]):
            problems.append(f"new {section} entry: {item}")
        for item in sorted(then[section] - now[section]):
            problems.append(f"{section} entry no longer present (regenerate the baseline): {item}")
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--write", action="store_true", help="regenerate the baseline")
    parser.add_argument("--report", type=int, nargs="?", const=10, default=0, metavar="N",
                        help="print the N worst drift entries (default 10)")
    args = parser.parse_args(argv)

    current, printed_by_id = collect()
    summary = counts(current)
    print(
        f"labels: {summary['unlabelled']} unlabelled conditional/play abilities, "
        f"{summary['drift']} labels not found in printed text, "
        f"{summary['unsupported']} cards with unsupported entries"
    )
    if args.report:
        for missing, cid, label in worst_drift(current, printed_by_id, args.report):
            print(f"  {cid}: {label}  [not printed: {' '.join(missing)}]")

    if args.write:
        BASELINE.parent.mkdir(parents=True, exist_ok=True)
        BASELINE.write_text(json.dumps(baseline_document(current), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"wrote {BASELINE.relative_to(ROOT)}")
        return 0

    if not BASELINE.is_file():
        print(f"baseline missing: {BASELINE.relative_to(ROOT)}. Run `{REGENERATE}`.")
        return 1
    baseline = json.loads(BASELINE.read_text(encoding="utf-8"))
    problems = compare(current, baseline)
    if baseline.get("counts") != summary and not problems:
        problems.append("baseline counts are stale")
    for line in problems:
        print(line)
    if problems:
        print(f"{len(problems)} label baseline mismatch(es). If the change is intended, run `{REGENERATE}` and commit the result.")
        return 1
    print("label baseline matches")
    return 0


if __name__ == "__main__":
    sys.exit(main())
