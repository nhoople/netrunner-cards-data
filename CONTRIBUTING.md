# Contributing

## Card clears / IR slices

1. Map printed text to Effect IR; list every deferred clause in `unsupported` (never silent wrong behavior).
2. Fill the **CR adherence gate** section in the PR template (`.github/PULL_REQUEST_TEMPLATE.md`). Full checklist: Netrunner Core Project store `docs/cr-adherence-gate.md`.
3. Pair with an engine PR that wires/tests the new IR when host support is required.

## Pool invariant (`supported` waves)

A wave with `status: "supported"` in `data/pool.json` must have **empty** `unsupported: []` on every listed card.

Rare explicit deferrals while keeping `supported` require an entry in [`data/supported-unsupported-allowlist.json`](data/supported-unsupported-allowlist.json) (card id → reason with CR cite / tracking note). Prefer leaving the wave non-`supported` until clears land.

CI runs `python3 scripts/validate-cards.py`, which enforces schema, pool consistency, and this invariant.
