# Contributing

## Catalog source

Card extracts come from the `v2` catalog in pinned [Null-Signal-Games/netrunner-cards-json](https://github.com/Null-Signal-Games/netrunner-cards-json) (NSG source of truth; NRDB is downstream): `v2/cards/` for titles, `v2/printings/` for printings, and the reference vocabularies beside them. See README **Data pipeline / catalog extract source**. The `pack/{code}.json` export is not read. NRDB codes may appear as identifiers. Card text is not taken from the NRDB API. Verified rulings are copied from that catalog's `v2/rulings/` snapshot, which itself was fetched from the NRDB rulings API. Watch new packs with `python3 scripts/nsg_catalog.py check`.

Corpus title ids are this repo's own: convert a catalog id with `nsg_catalog.our_id`. Author ability wording from the catalog's `stripped_text`, and copy `text`/`stripped_text` into `data/printed/` verbatim through `scripts/build_catalog_facts.py`; do not derive a plain version from the marked-up text locally.

## Pack card work / Effect IR

1. Map printed text to Effect IR; list every deferred clause in `unsupported` (never silent wrong behavior).
2. Fill the **CR adherence gate** section in the PR template (`.github/PULL_REQUEST_TEMPLATE.md`). Full checklist: [cr-adherence-gate.md](https://github.com/nhoople/netrunner-engine/blob/master/docs/cr-adherence-gate.md) in the engine repository.
3. Pair with an engine PR that wires/tests the new IR when host support is required.
4. Prefer pack-level PRs (or a coherent pack subset). Do not publish a GitHub Release until the wave is set-complete (or an explicit manual release is requested).

## Pool invariant (`supported` waves)

A wave with `status: "supported"` in `data/pool.json` must have **empty** `unsupported: []` on every listed card.

Rare explicit deferrals while keeping `supported` require an entry in [`data/supported-unsupported-allowlist.json`](data/supported-unsupported-allowlist.json) (card id → reason with CR cite / tracking note). Prefer leaving the wave non-`supported` until the pack is fully mapped.

CI runs `python3 scripts/validate-cards.py`, which enforces schema, pool consistency, and this invariant.

## Set-complete

When marking a wave `supported`, keep README pairing + `pool.json` in sync with the matching engine same-semver tag. Interaction smoke at set-complete is required for each **new** pack ([interaction-smoke-samples.md](https://github.com/nhoople/netrunner-engine/blob/master/docs/interaction-smoke-samples.md) in the engine repository); Gateway → Vantage Point already passed once via engine [#193](https://github.com/nhoople/netrunner-engine/pull/193).

**Current floor:** **`v1.147.8`**. Cards are stored by side and type, with deck limits, printings, verified rulings, and format lists. Double-sided identity faces, uniqueness, and designer attribution match the pinned v2 catalog, guarded by the catalog-facts builder. The title corpus is the `v1.147.6` corpus. Paired engine release **`v1.147.11`** pins this tag. Idle until next NSG pack after VP or a CR bump. Skip `napd`/draft/championship; defer `tdc`. CR pin in the engine is `v26.03`.
