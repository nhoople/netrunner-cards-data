# Netrunner cards data

Unofficial, machine-readable **card definitions** for Android: Netrunner, authored for the [nhoople/netrunner-engine](https://github.com/nhoople/netrunner-engine) rules library.

This is a **consumer dataset**, in the same spirit as [netrunner-comprehensive-rules-data](https://github.com/nhoople/netrunner-comprehensive-rules-data) and [netrunner-cards-json](https://github.com/Null-Signal-Games/netrunner-cards-json). It is not a rules engine and not a game client.

**Cards are pure data.** Each JSON file is a card definition (stats, subtypes, abilities as Effect IR). Executable evaluation lives in the engine; this repo does not contain IR/eval code.

See [`NOTICE`](NOTICE) for affiliation and trademark notes. Toolchain/schema are MIT; printed card text remains Null Signal Games reference material.

## Consume the data

Files under [`data/`](data/) are the API. Clone the repo or fetch a **tagged** release (do not pin `master`).

| Path | Use |
| --- | --- |
| [`data/schema.json`](data/schema.json) | JSON Schema for card definitions |
| [`data/pool.json`](data/pool.json) | Declared supported corpus / release order |
| [`data/reign-and-reverie/`](data/reign-and-reverie/) | Reign and Reverie (NRDB `rar`) — **in-progress** (legacy backwards) |
| [`data/system-core-2019/`](data/system-core-2019/) | System Core 2019 (NRDB `sc19`) — **supported** (legacy backwards) |
| [`data/downfall/`](data/downfall/) | Downfall (NRDB `df`) — **supported** (legacy backwards) |
| [`data/uprising/`](data/uprising/) | Uprising (NRDB `ur`) — **supported** (legacy backwards) |
| [`data/system-gateway/`](data/system-gateway/) | System Gateway (NRDB `sg`) |
| [`data/system-update-2021/`](data/system-update-2021/) | System Update 2021 (NRDB `su21`) |
| [`data/midnight-sun/`](data/midnight-sun/) | Midnight Sun (NRDB `ms`) |
| [`data/parhelion/`](data/parhelion/) | Parhelion (NRDB `ph`) — supported |
| [`data/the-automata-initiative/`](data/the-automata-initiative/) | The Automata Initiative (NRDB `tai`) — **supported** |
| [`data/rebellion-without-rehearsal/`](data/rebellion-without-rehearsal/) | Rebellion Without Rehearsal (NRDB `rwr`) — **supported** |
| [`data/elevation/`](data/elevation/) | Elevation (NRDB `elev`) — **supported** |
| [`data/vantage-point/`](data/vantage-point/) | Vantage Point (NRDB `vp`) — **supported** |
| [`data/fixtures/`](data/fixtures/) | CR-example / host-test cards outside corpus order (e.g. Plascrete) |

**Corpus order:** Reign and Reverie (legacy backwards, in-progress) → System Core 2019 (legacy backwards, supported) → Downfall (legacy backwards, supported) → Uprising (legacy backwards, supported) → System Gateway → System Update 2021 → Midnight Sun → Parhelion → The Automata Initiative → Rebellion Without Rehearsal → Elevation → Vantage Point → later releases.

Partial cards list unimplemented clauses in an `unsupported` array — never silent wrong behavior. A wave marked `supported` in [`data/pool.json`](data/pool.json) must keep those arrays empty unless the card is listed with a reason in [`data/supported-unsupported-allowlist.json`](data/supported-unsupported-allowlist.json) (enforced by `scripts/validate-cards.py`). See [`CONTRIBUTING.md`](CONTRIBUTING.md) for the CR gate PR template.

### Cards ↔ engine pairing

Match this dataset and [netrunner-engine](https://github.com/nhoople/netrunner-engine) by the **same semver tag**. Pin a **release tag**, not `master`.

| Pairing | cards-data | engine |
|---------|------------|--------|
| **Current** | [`v1.81.0`](https://github.com/nhoople/netrunner-cards-data/releases/tag/v1.81.0) | engine same-semver pin `v1.81.0` |
| RaR E-slice | [`v1.80.0`](https://github.com/nhoople/netrunner-cards-data/releases/tag/v1.80.0) | engine same-semver pin `v1.80.0` |
| RaR D-slice | [`v1.79.0`](https://github.com/nhoople/netrunner-cards-data/releases/tag/v1.79.0) | engine same-semver pin `v1.79.0` |
| RaR C-slice | [`v1.78.0`](https://github.com/nhoople/netrunner-cards-data/releases/tag/v1.78.0) | engine same-semver pin `v1.78.0` |
| RaR B-slice | [`v1.77.0`](https://github.com/nhoople/netrunner-cards-data/releases/tag/v1.77.0) | engine same-semver pin `v1.77.0` |
| RaR A-slice | [`v1.76.0`](https://github.com/nhoople/netrunner-cards-data/releases/tag/v1.76.0) | engine same-semver pin `v1.76.0` |
| RaR kickoff | [`v1.75.0`](https://github.com/nhoople/netrunner-cards-data/releases/tag/v1.75.0) | engine same-semver pin `v1.75.0` |
| SC19 milestone | [`v1.74.0`](https://github.com/nhoople/netrunner-cards-data/releases/tag/v1.74.0) | [`v1.74.0`](https://github.com/nhoople/netrunner-engine/releases/tag/v1.74.0) |
| Downfall milestone | [`v1.58.0`](https://github.com/nhoople/netrunner-cards-data/releases/tag/v1.58.0) | [`v1.58.0`](https://github.com/nhoople/netrunner-engine/releases/tag/v1.58.0) |
| Uprising milestone | [`v1.46.0`](https://github.com/nhoople/netrunner-cards-data/releases/tag/v1.46.0) | [`v1.46.0`](https://github.com/nhoople/netrunner-engine/releases/tag/v1.46.0) |
| Post-VP maintenance | [`v1.34.0`](https://github.com/nhoople/netrunner-cards-data/releases/tag/v1.34.0) | [`v1.34.0`](https://github.com/nhoople/netrunner-engine/releases/tag/v1.34.0) |
| Vantage Point milestone | [`v1.33.0`](https://github.com/nhoople/netrunner-cards-data/releases/tag/v1.33.0) | [`v1.33.0`](https://github.com/nhoople/netrunner-engine/releases/tag/v1.33.0) |
| Elevation milestone | [`v1.12.0`](https://github.com/nhoople/netrunner-cards-data/releases/tag/v1.12.0) | [`v1.12.0`](https://github.com/nhoople/netrunner-engine/releases/tag/v1.12.0) |
| RWR milestone | [`v1.00.0`](https://github.com/nhoople/netrunner-cards-data/releases/tag/v1.00.0) | [`v1.00.0`](https://github.com/nhoople/netrunner-engine/releases/tag/v1.00.0) |

Incremental wave tags are the day-to-day IR/wiring contract. A set-complete **milestone** GitHub Release is cut only when a wave’s pool status → `supported` (advertised host floor for that set). Maintenance / quality tags (e.g. `v1.34.0`) still publish GitHub Releases when consumers should pin past a prior milestone.

The engine declares the pin in [`data/cards-pin.json`](https://github.com/nhoople/netrunner-engine/blob/master/data/cards-pin.json) and fetches with:

```bash
# in netrunner-engine
npm run fetch-cards   # → vendor/cards-data/ (from this tag)
npm run fetch-cr      # → vendor/cr-data/ (CR pin; citations / timing IDs)
npm run prepare-data  # both fetches
npm test
npm run demo:library  # createGame → queryLegality → applyIntent → getPublicView
```

Example raw URL base (match the **current** pairing tag):

```text
https://raw.githubusercontent.com/nhoople/netrunner-cards-data/v1.38.0/data
```

JavaScript — load the pool and one card from a tagged release:

```js
const base =
  "https://raw.githubusercontent.com/nhoople/netrunner-cards-data/v1.38.0/data";
const pool = await fetch(`${base}/pool.json`).then((r) => r.json());
const marjanah = await fetch(`${base}/system-gateway/marjanah.json`).then((r) =>
  r.json(),
);
console.log(pool.corpusOrder, marjanah.title);
```

## Current corpus

| Release | Count | Notes |
|---------|------:|-------|
| reign-and-reverie | 58 | Null Signal Reign and Reverie (`rar`); **in-progress** (F-slice `v1.81.0`; 35/56 RaR-only clears; 2 SC19 reprints absorbed) |
| system-core-2019 | 147 | Null Signal System Core 2019 (`sc19`); **supported** (wave gate `v1.74.0`; 84/147 SC19-only; 63 Gateway/SU21 reprints absorbed; skip `mo`/`mor`) |
| downfall | 65 | Null Signal Downfall (`df`); Ashes set 1; **supported** (**65/65** mapped; wave gate `v1.58.0`; skip `mor`) |
| uprising | 65 | Null Signal Uprising (`ur`); Ashes set 2; **supported** (**65/65** mapped; wave gate `v1.46.0`; `urbp` absorbed) |
| system-gateway | 77 | Null Signal System Gateway (fully supported) |
| system-update-2021 | 82 | Null Signal System Update 2021 (fully supported) |
| midnight-sun | 65 | Null Signal Midnight Sun (`ms`); `msbp` titles absorbed; fully supported |
| parhelion | 63 | Null Signal Parhelion (`ph`); status `supported` (wave gate `v0.71.0`; all 63 clear) |
| the-automata-initiative | 65 | Null Signal The Automata Initiative (`tai`); status `supported` (wave gate `v0.86.0`) |
| rebellion-without-rehearsal | 65 | Null Signal Rebellion Without Rehearsal (`rwr`); status `supported` (**65/65** mapped; wave gate `v1.00.0`) |
| elevation | 82 | Null Signal Elevation (`elev`); status `supported` (**82/82** mapped; wave gate `v1.12.0`) |
| vantage-point | 66 | Null Signal Vantage Point (`vp`); status `supported` (`v1.33.0`; **66/66** mapped) |

Synthetic stubs and early wave1/wave2 dirs were removed in `v0.2.0`. Reprints that previously lived only under those waves now ship under their Null Signal release directories.

Parhelion is fully supported (wave gate `v0.71.0`). The Automata Initiative is fully supported (wave gate `v0.86.0`). Rebellion Without Rehearsal is fully supported (wave gate `v1.00.0`). Elevation is fully supported (wave gate `v1.12.0`). Vantage Point is fully supported (wave gate `v1.33.0`). Uprising is fully supported (wave gate `v1.46.0`). **Downfall** is fully supported (wave gate `v1.58.0`, **65/65**). **System Core 2019** is fully supported (wave gate `v1.74.0`, **84/147** SC19-only). **Reign and Reverie** kickoff is in progress (pin `v1.75.0`).

**Next:** Clear Reign and Reverie toward set-complete, then further legacy backwards or forward after VP when a new NSG pack or CR bump lands. Pair every clear with the engine CR adherence gate; at set-complete, run interaction smoke.

## Versioning

Tag dataset releases as `vMAJOR.MINOR.PATCH` (e.g. `v1.35.0`). Bump when card JSON, pool, or schema that consumers rely on changes. Keep the README pairing line in sync after each pin bump (no new tag for README-only).

## Catalog extract source

Pack metadata for generate/extract scripts comes from the pinned [Null-Signal-Games/netrunner-cards-json](https://github.com/Null-Signal-Games/netrunner-cards-json) repo (`pack/{code}.json`), **not** the live NetrunnerDB public API.

| Path | Use |
| --- | --- |
| [`data/nrdb-catalog-pin.json`](data/nrdb-catalog-pin.json) | Upstream repo URL + commit SHA pin |
| [`scripts/nrdb_catalog.py`](scripts/nrdb_catalog.py) | Fetch helper (caches under `tmp/nrdb-catalog/`) |

```bash
python3 scripts/nrdb_catalog.py show-pin
python3 scripts/nrdb_catalog.py fetch rar sc19 df ur sg su21 ms msbp ph tai rwr elev vp
# then: python3 scripts/generate-<set>.py
```

To bump the catalog: set `ref` in the pin to a newer commit SHA on `main`, clear `tmp/nrdb-catalog/`, and re-fetch. Effect IR remains hand-authored in this repo.

## License

MIT for schema and tooling — see [`LICENSE`](LICENSE). Card text: see [`NOTICE`](NOTICE).

This project is not associated with, produced by, or endorsed by Null Signal Games, Fantasy Flight Games, R. Talsorian Games, or Wizards of the Coast.
