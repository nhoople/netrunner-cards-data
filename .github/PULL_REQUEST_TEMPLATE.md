## Summary

<!-- What changed and why (1–3 bullets). -->

## Proof

<!-- How the maintainer can see this working without reading code: a played match or the part of one this changes, a before-and-after screenshot or recording, or a test whose name states the behavior in plain words. Docs, tooling, or dependency-only PRs: `n/a — <reason>`. -->

## Review

<!-- For a code change: the `/code-review` level, what it found, and what was fixed or why not. Otherwise: `none — <reason>`. -->

## Found, not fixed

<!-- Each thing noticed that this PR does not change: what it is, where it went (issue, plan, or a fix-now session), and why. See "Findings" in https://github.com/nhoople/netrunner/blob/main/docs/how-we-work.md. Write `none` if nothing. -->

## CR adherence gate (required for Effect IR / card mapping)

For any PR that adds Effect IR or marks cards fully mapped for engine consumption: fill the recording template ([cr-adherence-gate.md](https://github.com/nhoople/netrunner-engine/blob/master/docs/cr-adherence-gate.md) in the engine repository). Do **not** delete this section.

Pure schema / pool / generate / validate / docs changes: leave the template and write `Verdict: n/a — <one-line reason>`.

```text
CR gate (v26.03) — <pack>
Cards: <ids>
Timing windows: <list or n/a>
Defined terms / keywords: <list>
Cannot / prevent interactions: <none | cites>
Cite additions: <CR.* keys or none>
Fail-closed / unsupported left: <none | bullets>
Verdict: clear | clear-with-debt | blocked | n/a — <reason>
```

### Checklist

- [ ] Effect IR / card mapping: CR gate filled above (or `n/a` with reason)
- [ ] `ruff format --check scripts tests` passes
- [ ] `python3 scripts/validate_cards.py` passes (includes supported-wave empty-`unsupported` invariant)
- [ ] The `tests/` checks and `python3 scripts/check_labels.py --report` pass (the full CI list is in `AGENTS.md`)
- [ ] If keeping non-empty `unsupported` on a `supported` wave card: entry + reason in `bookkeeping/supported-unsupported-allowlist.json`

## Release

- [ ] None: tests, docs, tooling, or dependencies only
- [ ] Maintenance release `<tag>` (engine `src/` change); the game pin and the [pin table](https://github.com/nhoople/netrunner#readme) follow
- [ ] Set-complete pair `<tag>` (cards and engine share the semver)
