#!/usr/bin/env python3
"""The README's "Layout" section names every folder in the repo. No network.

Every folder that holds a tracked file, or a new file git does not ignore, must
be named in a row of the table under `## Layout` in README.md, and every folder a
row names must exist. Each folder is named in full: a `<placeholder>` row such as
`data/rules/corp/<type>/` is refused, because it would accept any new folder there.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
HEADING = "## Layout"


def repo_folders(root: Path = ROOT) -> set[str]:
    """Every folder holding a tracked file or a new file that git does not ignore."""
    listed = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    folders: set[str] = set()
    for path in filter(None, listed.split("\0")):
        parts = path.split("/")[:-1]
        for depth in range(1, len(parts) + 1):
            folders.add("/".join(parts[:depth]) + "/")
    return folders


def layout_section(readme: str) -> str:
    """The text from the `## Layout` heading to the next `## ` heading."""
    lines = readme.splitlines()
    try:
        start = lines.index(HEADING)
    except ValueError:
        raise SystemExit(f"README.md has no {HEADING!r} section") from None
    end = next(
        (i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")),
        len(lines),
    )
    return "\n".join(lines[start + 1 : end])


def map_entries(section: str) -> list[str]:
    """Folder paths in the first column of the section's table, such as `scripts/`."""
    entries: list[str] = []
    for line in section.splitlines():
        cells = line.split("|")
        if len(cells) < 3 or not line.lstrip().startswith("|"):
            continue
        entries.extend(
            path for path in re.findall(r"`([^`]+/)`", cells[1]) if path not in entries
        )
    return entries


def placeholders(entries: list[str]) -> list[str]:
    """Entries that use a `<placeholder>` instead of naming each folder."""
    return [entry for entry in entries if re.search(r"[<>]", entry)]


def compare(folders: set[str], entries: list[str]) -> tuple[list[str], list[str]]:
    """Folders no entry names, and entries that name no folder."""
    listed = set(entries)
    unlisted = sorted(folder for folder in folders if folder not in listed)
    stale = [entry for entry in entries if entry not in folders]
    return unlisted, stale


def test_placeholder_rows_are_refused() -> None:
    entries = ["data/rules/corp/<type>/", "data/rules/corp/ice/"]
    assert placeholders(entries) == ["data/rules/corp/<type>/"]
    # A placeholder row names no real folder, so it never covers a new one.
    unlisted, stale = compare({"data/rules/corp/made-up/"}, entries)
    assert unlisted == ["data/rules/corp/made-up/"], unlisted
    assert "data/rules/corp/<type>/" in stale, stale


def test_compare_reports_unlisted_and_stale() -> None:
    unlisted, stale = compare(
        {"scripts/", "scripts/generate/", "made-up/"},
        ["scripts/", "scripts/generate/", "gone/"],
    )
    assert unlisted == ["made-up/"], unlisted
    assert stale == ["gone/"], stale


def test_section_reads_only_the_layout_table() -> None:
    readme = (
        "# Title\n\n## Layout\n\n| Folder | Holds |\n| --- | --- |\n"
        "| `scripts/` | commands, not `ignored/` |\n| `a/`, `b/` | two |\n\n"
        "## Next\n\n| `other/` | not in the map |\n"
    )
    assert map_entries(layout_section(readme)) == ["scripts/", "a/", "b/"]


def test_readme_layout_names_every_folder() -> None:
    entries = map_entries(layout_section(README.read_text(encoding="utf-8")))
    unlisted, stale = compare(repo_folders(), entries)
    refused = placeholders(entries)
    stale = [entry for entry in stale if entry not in refused]
    problems = (
        [
            f"{entry}: uses a placeholder. Name each folder it stands for instead, "
            "so a new folder needs its own row."
            for entry in refused
        ]
        + [
            f"{folder}: not in the README's {HEADING!r} table. "
            "Add a row that names it and says what it holds."
            for folder in unlisted
        ]
        + [
            f"{entry}: listed in the README's {HEADING!r} table, but no such folder "
            "exists. Remove or fix the row."
            for entry in stale
        ]
    )
    assert not problems, "\n".join(problems)


def main() -> int:
    tests = [
        value for name, value in sorted(globals().items()) if name.startswith("test_")
    ]
    failed = 0
    for test in tests:
        try:
            test()
        except AssertionError as error:
            failed += 1
            print(f"FAIL {test.__name__}:\n{error}")
    if failed:
        return 1
    print(f"layout map: {len(tests)} tests passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
