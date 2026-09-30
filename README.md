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
| [`data/core/`](data/core/) | FFG Core Set (NRDB `core`) — **supported** (Core-forward) |
| [`data/what-lies-ahead/`](data/what-lies-ahead/) | What Lies Ahead (NRDB `wla`) — **supported** (Genesis) |
| [`data/trace-amount/`](data/trace-amount/) | Trace Amount (NRDB `ta`) — **supported** (Genesis) |
| [`data/cyber-exodus/`](data/cyber-exodus/) | Cyber Exodus (NRDB `ce`) — **supported** (Genesis) |
| [`data/a-study-in-static/`](data/a-study-in-static/) | A Study in Static (NRDB `asis`) — **supported** (Genesis) |
| [`data/humanitys-shadow/`](data/humanitys-shadow/) | Humanity's Shadow (NRDB `hs`) — **supported** (Genesis) |
| [`data/future-proof/`](data/future-proof/) | Future Proof (NRDB `fp`) — **supported** (Genesis) |
| [`data/creation-and-control/`](data/creation-and-control/) | Creation and Control (NRDB `cac`) — **supported** |
| [`data/opening-moves/`](data/opening-moves/) | Opening Moves (NRDB `om`) — **supported** (Spin) |
| [`data/stalwart/`](data/stalwart/) | Stalwart (NRDB `st`) — **supported** (Spin) |
| [`data/mala-tempora/`](data/mala-tempora/) | Mala Tempora (NRDB `mt`) — **supported** (Spin) |
| [`data/true-colors/`](data/true-colors/) | True Colors (NRDB `tc`) — **supported** (Spin) |
| [`data/fear-and-loathing/`](data/fear-and-loathing/) | Fear and Loathing (NRDB `fal`) — **supported** (Spin) |
| [`data/double-time/`](data/double-time/) | Double Time (NRDB `dt`) — **supported** (Spin) |
| [`data/honor-and-profit/`](data/honor-and-profit/) | Honor and Profit (NRDB `hap`) — **supported** (deluxe) |
| [`data/upstalk/`](data/upstalk/) | Upstalk (NRDB `up`) — **supported** (Lunar) |
| [`data/the-spaces-between/`](data/the-spaces-between/) | The Spaces Between (NRDB `tsb`) — **supported** (Lunar) |
| [`data/first-contact/`](data/first-contact/) | First Contact (NRDB `fc`) — **supported** (Lunar) |
| [`data/up-and-over/`](data/up-and-over/) | Up and Over (NRDB `uao`) — **supported** (Lunar) |
| [`data/all-that-remains/`](data/all-that-remains/) | All That Remains (NRDB `atr`) — **supported** (Lunar) |
| [`data/the-source/`](data/the-source/) | The Source (NRDB `ts`) — **supported** (Lunar) |
| [`data/order-and-chaos/`](data/order-and-chaos/) | Order and Chaos (NRDB `oac`) — **supported** (deluxe) |
| [`data/the-valley/`](data/the-valley/) | The Valley (NRDB `val`) — **supported** (SanSan) |
| [`data/breaker-bay/`](data/breaker-bay/) | Breaker Bay (NRDB `bb`) — **supported** (SanSan) |
| [`data/chrome-city/`](data/chrome-city/) | Chrome City (NRDB `cc`) — **supported** (SanSan) |
| [`data/the-underway/`](data/the-underway/) | The Underway (NRDB `uw`) — **supported** (SanSan) |
| [`data/old-hollywood/`](data/old-hollywood/) | Old Hollywood (NRDB `oh`) — **supported** (SanSan) |
| [`data/the-universe-of-tomorrow/`](data/the-universe-of-tomorrow/) | The Universe of Tomorrow (NRDB `uot`) — **supported** (SanSan) |
| [`data/data-and-destiny/`](data/data-and-destiny/) | Data and Destiny (NRDB `dad`) — **supported** (deluxe) |
| [`data/kala-ghoda/`](data/kala-ghoda/) | Kala Ghoda (NRDB `kg`) — **supported** (Mumbad) |
| [`data/business-first/`](data/business-first/) | Business First (NRDB `bf`) — **supported** (Mumbad) |
| [`data/democracy-and-dogma/`](data/democracy-and-dogma/) | Democracy and Dogma (NRDB `dag`) — **supported** (Mumbad) |
| [`data/salsette-island/`](data/salsette-island/) | Salsette Island (NRDB `si`) — **supported** (Mumbad) |
| [`data/the-liberated-mind/`](data/the-liberated-mind/) | The Liberated Mind (NRDB `tlm`) — **supported** (Mumbad) |
| [`data/fear-the-masses/`](data/fear-the-masses/) | Fear the Masses (NRDB `ftm`) — **supported** (Mumbad) |
| [`data/twenty-three-seconds/`](data/twenty-three-seconds/) | 23 Seconds (NRDB `23s`) — **supported** (Flashpoint) |
| [`data/blood-money/`](data/blood-money/) | Blood Money (NRDB `bm`) — **supported** (Flashpoint) |
| [`data/reign-and-reverie/`](data/reign-and-reverie/) | Reign and Reverie (NRDB `rar`) — **supported** (legacy backwards) |
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

**Corpus order:** FFG Core Set (Core-forward, supported) → What Lies Ahead (Genesis, supported) → Trace Amount (Genesis, supported) → Cyber Exodus (Genesis, supported) → A Study in Static (Genesis, supported) → Humanity's Shadow (Genesis, supported) → Future Proof (Genesis, supported) → Creation and Control (supported) → Reign and Reverie (legacy backwards, supported) → System Core 2019 (legacy backwards, supported) → Downfall (legacy backwards, supported) → Uprising (legacy backwards, supported) → System Gateway → System Update 2021 → Midnight Sun → Parhelion → The Automata Initiative → Rebellion Without Rehearsal → Elevation → Vantage Point → later releases.

Partial cards list unimplemented clauses in an `unsupported` array — never silent wrong behavior. A wave marked `supported` in [`data/pool.json`](data/pool.json) must keep those arrays empty unless the card is listed with a reason in [`data/supported-unsupported-allowlist.json`](data/supported-unsupported-allowlist.json) (enforced by `scripts/validate-cards.py`). See [`CONTRIBUTING.md`](CONTRIBUTING.md) for the CR gate PR template.

### Cards ↔ engine pairing

Match this dataset and [netrunner-engine](https://github.com/nhoople/netrunner-engine) by the **same semver tag**. Pin a **release tag**, not `master`.

| Pairing | cards-data | engine |
|---------|------------|--------|
| **Current** | [`v1.115.0`](https://github.com/nhoople/netrunner-cards-data/releases/tag/v1.115.0) | engine same-semver pin `v1.115.0` (Data and Destiny set-complete **54/54**) |
| The Universe of Tomorrow | [`v1.114.0`](https://github.com/nhoople/netrunner-cards-data/releases/tag/v1.114.0) | engine same-semver pin `v1.114.0` (The Universe of Tomorrow set-complete **18/18**) |
| Old Hollywood | [`v1.113.0`](https://github.com/nhoople/netrunner-cards-data/releases/tag/v1.113.0) | engine same-semver pin `v1.113.0` (Old Hollywood set-complete **19/19**) |
| The Underway | [`v1.112.0`](https://github.com/nhoople/netrunner-cards-data/releases/tag/v1.112.0) | engine same-semver pin `v1.112.0` (The Underway set-complete **17/17**) |
| Chrome City | [`v1.111.0`](https://github.com/nhoople/netrunner-cards-data/releases/tag/v1.111.0) | engine same-semver pin `v1.111.0` (Chrome City set-complete **18/18**) |
| Breaker Bay | [`v1.110.0`](https://github.com/nhoople/netrunner-cards-data/releases/tag/v1.110.0) | engine same-semver pin `v1.110.0` (Breaker Bay set-complete **18/18**) |
| The Valley | [`v1.109.0`](https://github.com/nhoople/netrunner-cards-data/releases/tag/v1.109.0) | engine same-semver pin `v1.109.0` (The Valley set-complete **19/19**) |
| Order and Chaos | [`v1.108.0`](https://github.com/nhoople/netrunner-cards-data/releases/tag/v1.108.0) | engine same-semver pin `v1.108.0` (Order and Chaos set-complete **55/55**) |
| The Source | [`v1.107.0`](https://github.com/nhoople/netrunner-cards-data/releases/tag/v1.107.0) | engine same-semver pin `v1.107.0` (The Source set-complete **19/19**) |
| All That Remains | [`v1.106.0`](https://github.com/nhoople/netrunner-cards-data/releases/tag/v1.106.0) | engine same-semver pin `v1.106.0` (All That Remains set-complete **17/17**) |
| Up and Over | [`v1.105.0`](https://github.com/nhoople/netrunner-cards-data/releases/tag/v1.105.0) | engine same-semver pin `v1.105.0` (Up and Over set-complete **18/18**) |
| First Contact | [`v1.104.0`](https://github.com/nhoople/netrunner-cards-data/releases/tag/v1.104.0) | engine same-semver pin `v1.104.0` (First Contact set-complete **18/18**) |
| The Spaces Between | [`v1.103.0`](https://github.com/nhoople/netrunner-cards-data/releases/tag/v1.103.0) | engine same-semver pin `v1.103.0` (The Spaces Between set-complete **20/20**) |
| Honor and Profit | [`v1.101.0`](https://github.com/nhoople/netrunner-cards-data/releases/tag/v1.101.0) | engine same-semver pin `v1.101.0` (Honor and Profit set-complete **50/50**) |
| Double Time | [`v1.100.0`](https://github.com/nhoople/netrunner-cards-data/releases/tag/v1.100.0) | engine same-semver pin `v1.100.0` (Double Time set-complete **19/19**) |
| Mala Tempora | [`v1.97.0`](https://github.com/nhoople/netrunner-cards-data/releases/tag/v1.97.0) | engine same-semver pin `v1.97.0` (Mala Tempora set-complete **18/18**) |
| Opening Moves / Stalwart | [`v1.96.0`](https://github.com/nhoople/netrunner-cards-data/releases/tag/v1.96.0) | engine same-semver pin `v1.96.0` (Stalwart set-complete **17/17**) |
| Opening Moves | [`v1.95.0`](https://github.com/nhoople/netrunner-cards-data/releases/tag/v1.95.0) | engine same-semver pin `v1.95.0` (Opening Moves set-complete **16/16**) |
| Creation and Control | [`v1.94.0`](https://github.com/nhoople/netrunner-cards-data/releases/tag/v1.94.0) | engine same-semver pin `v1.94.0` (Creation and Control set-complete **46/46**) |
| Humanity's Shadow | [`v1.92.0`](https://github.com/nhoople/netrunner-cards-data/releases/tag/v1.92.0) | engine same-semver pin `v1.92.0` (Humanity's Shadow set-complete **15/15**) |
| A Study in Static | [`v1.91.0`](https://github.com/nhoople/netrunner-cards-data/releases/tag/v1.91.0) | engine same-semver pin `v1.91.0` (A Study in Static set-complete **15/15**) |
| Cyber Exodus | [`v1.90.0`](https://github.com/nhoople/netrunner-cards-data/releases/tag/v1.90.0) | engine same-semver pin `v1.90.0` (Cyber Exodus set-complete **13/13**) |
| Trace Amount | [`v1.89.0`](https://github.com/nhoople/netrunner-cards-data/releases/tag/v1.89.0) | engine same-semver pin `v1.89.0` (Trace Amount set-complete **15/15**) |
| What Lies Ahead | [`v1.88.0`](https://github.com/nhoople/netrunner-cards-data/releases/tag/v1.88.0) | engine same-semver pin `v1.88.0` (What Lies Ahead set-complete **14/14**) |
| Core Set | [`v1.87.0`](https://github.com/nhoople/netrunner-cards-data/releases/tag/v1.87.0) | engine same-semver pin `v1.87.0` (Core Set set-complete **49/49**) |
| RaR set-complete | [`v1.86.0`](https://github.com/nhoople/netrunner-cards-data/releases/tag/v1.86.0) | engine same-semver pin `v1.86.0` (RaR set-complete **56/56**) |
| RaR J-slice | [`v1.85.0`](https://github.com/nhoople/netrunner-cards-data/releases/tag/v1.85.0) | engine same-semver pin `v1.85.0` |
| RaR I-slice | [`v1.84.0`](https://github.com/nhoople/netrunner-cards-data/releases/tag/v1.84.0) | engine same-semver pin `v1.84.0` |
| RaR H-slice | [`v1.83.0`](https://github.com/nhoople/netrunner-cards-data/releases/tag/v1.83.0) | engine same-semver pin `v1.83.0` |
| RaR G-slice | [`v1.82.0`](https://github.com/nhoople/netrunner-cards-data/releases/tag/v1.82.0) | engine same-semver pin `v1.82.0` |
| RaR F-slice | [`v1.81.0`](https://github.com/nhoople/netrunner-cards-data/releases/tag/v1.81.0) | engine same-semver pin `v1.81.0` |
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
| core | 113 | FFG Core Set (`core`); **supported** (wave gate `v1.87.0`; 49/49 Core-only; 64 Gateway/SU21/SC19 reprints absorbed) |
| what-lies-ahead | 20 | FFG What Lies Ahead (`wla`); **supported** (wave gate `v1.88.0`; 14/14 WLA-only; 6 reprints absorbed; never kick `mo`/`mor`) |
| trace-amount | 20 | FFG Trace Amount (`ta`); **supported** (wave gate `v1.89.0`; 15/15 TA-only; 5 reprints absorbed; never kick `mo`/`mor`) |
| cyber-exodus | 20 | FFG Cyber Exodus (`ce`); **supported** (wave gate `v1.90.0`; 13/13 CE-only; 7 reprints absorbed; never kick `mo`/`mor`) |
| a-study-in-static | 20 | FFG A Study in Static (`asis`); **supported** (wave gate `v1.91.0`; 15/15 ASIS-only; 5 reprints absorbed; never kick `mo`/`mor`) |
| reign-and-reverie | 58 | Null Signal Reign and Reverie (`rar`); **supported** (wave gate `v1.86.0`; 56/56 RaR-only; 2 SC19 reprints absorbed) |
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

Parhelion is fully supported (wave gate `v0.71.0`). The Automata Initiative is fully supported (wave gate `v0.86.0`). Rebellion Without Rehearsal is fully supported (wave gate `v1.00.0`). Elevation is fully supported (wave gate `v1.12.0`). Vantage Point is fully supported (wave gate `v1.33.0`). Uprising is fully supported (wave gate `v1.46.0`). **Downfall** is fully supported (wave gate `v1.58.0`, **65/65**). **System Core 2019** is fully supported (wave gate `v1.74.0`, **84/147** SC19-only). **Reign and Reverie** is fully supported (wave gate `v1.86.0`, **56/56**). **FFG Core Set** is fully supported (wave gate `v1.87.0`, **49/49** Core-only). **What Lies Ahead** is fully supported (wave gate `v1.88.0`, **14/14** WLA-only). **Trace Amount** is fully supported (wave gate `v1.89.0`, **15/15** TA-only). **Cyber Exodus** is fully supported (wave gate `v1.90.0`, **13/13** CE-only). **A Study in Static** is fully supported (wave gate `v1.91.0`, **15/15** ASIS-only).

**Next:** Genesis continue (`hs` → `fp`). Pair every clear with the engine CR adherence gate; GitHub Releases only at set-complete. Never kick `mo`/`mor`.

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
