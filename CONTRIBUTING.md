# Contributing

## Catalog source

Pack extracts come from pinned [Null-Signal-Games/netrunner-cards-json](https://github.com/Null-Signal-Games/netrunner-cards-json) (NSG source of truth; NRDB is downstream). See README **Data pipeline / catalog extract source**. NRDB codes may appear as identifiers; do not ingest from the NRDB API. Watch new packs by diffing NSG against `data/pool.json`.

## Pack card work / Effect IR

1. Map printed text to Effect IR; list every deferred clause in `unsupported` (never silent wrong behavior).
2. Fill the **CR adherence gate** section in the PR template (`.github/PULL_REQUEST_TEMPLATE.md`). Full checklist: Netrunner Core Project store `docs/cr-adherence-gate.md`.
3. Pair with an engine PR that wires/tests the new IR when host support is required.
4. Prefer pack-level PRs (or a coherent pack subset). Do not publish a GitHub Release until the wave is set-complete (or an explicit manual release is requested).

## Pool invariant (`supported` waves)

A wave with `status: "supported"` in `data/pool.json` must have **empty** `unsupported: []` on every listed card.

Rare explicit deferrals while keeping `supported` require an entry in [`data/supported-unsupported-allowlist.json`](data/supported-unsupported-allowlist.json) (card id → reason with CR cite / tracking note). Prefer leaving the wave non-`supported` until the pack is fully mapped.

CI runs `python3 scripts/validate-cards.py`, which enforces schema, pool consistency, and this invariant.

## Set-complete

When marking a wave `supported`, keep README pairing + `pool.json` in sync with the matching engine same-semver tag. Interaction smoke at set-complete is required for each **new** pack (Project `docs/interaction-smoke-samples.md`); Gateway → Vantage Point already passed once via engine [#193](https://github.com/nhoople/netrunner-engine/pull/193).

**Current floor:** Magnum Opus `supported` at **`v1.143.0`** (pair with engine `v1.143.2`; corpus unchanged from `v1.142.2`; `mor` absorbed; fixtures wave removed). Idle until next NSG pack after VP or a CR bump. Skip `napd`/draft/championship; defer `tdc`. CR pin in the engine is `v26.03`.
