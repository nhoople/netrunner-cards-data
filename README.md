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
| [`data/escalation/`](data/escalation/) | Escalation (NRDB `es`) — **supported** (Flashpoint) |
| [`data/intervention/`](data/intervention/) | Intervention (NRDB `in`) — **supported** (Flashpoint) |
| [`data/martial-law/`](data/martial-law/) | Martial Law (NRDB `ml`) — **supported** (Flashpoint) |
| [`data/quorum/`](data/quorum/) | Quorum (NRDB `qu`) — **supported** (Flashpoint) |
| [`data/daedalus-complex/`](data/daedalus-complex/) | Daedalus Complex (NRDB `dc`) — **supported** (Red Sand) |
| [`data/station-one/`](data/station-one/) | Station One (NRDB `so`) — **supported** (Red Sand) |
| [`data/terminal-directive/`](data/terminal-directive/) | Terminal Directive Cards (NRDB `td`) — **supported** (Red Sand deluxe; defer `tdc`) |
| [`data/earths-scion/`](data/earths-scion/) | Earth's Scion (NRDB `eas`) — **supported** (Red Sand) |
| [`data/blood-and-water/`](data/blood-and-water/) | Blood and Water (NRDB `baw`) — **supported** (Red Sand) |
| [`data/free-mars/`](data/free-mars/) | Free Mars (NRDB `fm`) — **supported** (Red Sand) |
| [`data/crimson-dust/`](data/crimson-dust/) | Crimson Dust (NRDB `cd`) — **supported** (Red Sand) |
| [`data/revised-core/`](data/revised-core/) | Revised Core Set (NRDB `core2`) — **supported** (132/132 reprints absorbed; 0 new titles) |
| [`data/sovereign-sight/`](data/sovereign-sight/) | Sovereign Sight (NRDB `ss`) — **supported** (Kitara) |
| [`data/down-the-white-nile/`](data/down-the-white-nile/) | Down the White Nile (NRDB `dtwn`) — **supported** (Kitara) |
| [`data/council-of-the-crest/`](data/council-of-the-crest/) | Council of the Crest (NRDB `cotc`) — **supported** (Kitara) |
| [`data/the-devil-and-the-dragon/`](data/the-devil-and-the-dragon/) | The Devil and the Dragon (NRDB `tdatd`) — **supported** (Kitara) |
| [`data/whispers-in-nalubaale/`](data/whispers-in-nalubaale/) | Whispers in Nalubaale (NRDB `win`) — **supported** (Kitara) |
| [`data/kampala-ascendent/`](data/kampala-ascendent/) | Kampala Ascendent (NRDB `ka`) — **supported** (Kitara) |
| [`data/reign-and-reverie/`](data/reign-and-reverie/) | Reign and Reverie (NRDB `rar`) — **supported** (legacy backwards) |
| [`data/magnum-opus/`](data/magnum-opus/) | Magnum Opus (NRDB `mo`) — **supported** (`mor` absorbed) |
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

**Corpus order:** FFG Core Set → Genesis → CAC → Spin → HAP → Lunar → OAC → SanSan → DAD → Mumbad → Flashpoint → Red Sand + `td` → `core2` → Kitara → RaR → **Magnum Opus** (`mor` absorbed) → SC19 → Downfall → Uprising → Gateway → SU21 → Midnight Sun → Parhelion → TAI → RWR → Elevation → Vantage Point. Floor **`v1.143.0`**. Skip `napd`/draft/championship; defer `tdc`.

Partial cards list unimplemented clauses in an `unsupported` array — never silent wrong behavior. A wave marked `supported` in [`data/pool.json`](data/pool.json) must keep those arrays empty unless the card is listed with a reason in [`data/supported-unsupported-allowlist.json`](data/supported-unsupported-allowlist.json) (enforced by `scripts/validate-cards.py`). See [`CONTRIBUTING.md`](CONTRIBUTING.md) for the CR gate PR template.

### Cards ↔ engine pairing

Match this dataset and [netrunner-engine](https://github.com/nhoople/netrunner-engine) by the **same semver tag**. Pin a **release tag**, not `master`.

| Pairing | cards-data | engine |
|---------|------------|--------|
| **Current** | [`v1.143.0`](https://github.com/nhoople/netrunner-cards-data/releases/tag/v1.143.0) | [`v1.143.1`](https://github.com/nhoople/netrunner-engine/releases/tag/v1.143.1) (paired with engine mulligan floor; corpus unchanged from v1.142.2) |

Prior set-complete / maintenance tags: [cards Releases](https://github.com/nhoople/netrunner-cards-data/releases) · [engine Releases](https://github.com/nhoople/netrunner-engine/releases).

GitHub Releases are cut at **set-complete** (wave pool status → `supported`, advertised host floor) or by **explicit manual** release. Pack IR work lands as PR merges; pin consumers to a release tag, not `master`. Intermediate progress tags may still exist on GitHub history — prefer the **Current** floor tag above.

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
https://raw.githubusercontent.com/nhoople/netrunner-cards-data/v1.143.0/data
```

JavaScript — load the pool and one card from a tagged release:

```js
const base =
  "https://raw.githubusercontent.com/nhoople/netrunner-cards-data/v1.143.0/data";
const pool = await fetch(`${base}/pool.json`).then((r) => r.json());
const marjanah = await fetch(`${base}/system-gateway/marjanah.json`).then((r) =>
  r.json(),
);
console.log(pool.corpusOrder, marjanah.title);
```

## Current corpus

**Authoritative list:** [`data/pool.json`](data/pool.json) — **68/68** waves `supported` (see `corpusOrder` + each wave’s `status` / card counts). The directory table under **Consume the data** mirrors those wave dirs; do not treat any shorter summary table as the corpus.

**Floor `v1.143.0`:** Magnum Opus complete (**8/8**; `mor` absorbed). Fixtures wave removed (Plascrete under WLA). FFG Core-forward through Kitara, RaR, SC19→VP all `supported`. Eternal + RAM unique-title Magnum Opus gaps closed. Core Sets / Standard / Startup already full. Same corpus as `v1.142.2`; retagged to pair with engine mulligan floor.

**Next:** Idle / absorb-only until next NSG pack after VP or CR bump. Skip `napd`/draft/championship; defer `tdc`. GitHub Releases only at set-complete or explicit manual — not per-slice.

## Versioning

Tag dataset releases as `vMAJOR.MINOR.PATCH` (e.g. `v1.35.0`). Bump when card JSON, pool, or schema that consumers rely on changes. Keep the README pairing line in sync after each pin bump (no new tag for README-only).

## Data pipeline / catalog extract source

**Pipeline:** pinned [Null-Signal-Games/netrunner-cards-json](https://github.com/Null-Signal-Games/netrunner-cards-json) (NSG source of truth; NRDB is downstream) → author Effect IR into this repo → [nhoople/netrunner-engine](https://github.com/nhoople/netrunner-engine) pins our tags.

Pack metadata for generate/extract scripts comes from that NSG repo (`pack/{code}.json`). The NetrunnerDB public API is **not** the preferred ingest. NRDB codes may still appear as identifiers (pack codes, card ids); that does not make NRDB the catalog source. Watch new packs by diffing NSG against [`data/pool.json`](data/pool.json).

| Path | Use |
| --- | --- |
| [`data/nsg-catalog-pin.json`](data/nsg-catalog-pin.json) | Upstream NSG repo URL + commit SHA pin |
| [`scripts/nsg_catalog.py`](scripts/nsg_catalog.py) | Fetch helper (caches under `tmp/nsg-catalog/`) |

```bash
python3 scripts/nsg_catalog.py show-pin
python3 scripts/nsg_catalog.py fetch rar sc19 df ur sg su21 ms msbp ph tai rwr elev vp
# then: python3 scripts/generate-<set>.py
```

To bump the catalog: set `ref` in the pin to a newer commit SHA on `main`, clear `tmp/nsg-catalog/`, and re-fetch. Effect IR remains hand-authored in this repo.

## License

MIT for schema and tooling — see [`LICENSE`](LICENSE). Card text: see [`NOTICE`](NOTICE).

This project is not associated with, produced by, or endorsed by Null Signal Games, Fantasy Flight Games, R. Talsorian Games, or Wizards of the Coast.
