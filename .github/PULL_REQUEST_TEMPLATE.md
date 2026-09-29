## Summary

<!-- What changed and why (1–3 bullets). -->

## CR adherence gate (required for IR / clear slices)

For any PR that adds/clears Effect IR or marks a card clear for engine consumption: fill the recording template (Project Context `docs/cr-adherence-gate.md`). Do **not** delete this section.

Pure schema / pool / generate / validate / docs changes: leave the template and write `Verdict: n/a — <one-line reason>`.

```text
CR gate (v26.03) — <pack> / <slice tag>
Cards: <ids>
Timing windows: <list or n/a>
Defined terms / keywords: <list>
Cannot / prevent interactions: <none | cites>
Cite additions: <CR.* keys or none>
Fail-closed / unsupported left: <none | bullets>
Verdict: clear | clear-with-debt | blocked | n/a — <reason>
```

### Checklist

- [ ] IR / clear slice: CR gate filled above (or `n/a` with reason)
- [ ] `python3 scripts/validate-cards.py` passes (includes supported-wave empty-`unsupported` invariant)
- [ ] If keeping non-empty `unsupported` on a `supported` wave card: entry + reason in `data/supported-unsupported-allowlist.json`
