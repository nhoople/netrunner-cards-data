# Netrunner cards data

Part of [nhoople/netrunner](https://github.com/nhoople/netrunner). These repositories stay separate and are consumed by release tag.

Unofficial, machine-readable **card definitions** for Android: Netrunner, authored for the [nhoople/netrunner-engine](https://github.com/nhoople/netrunner-engine) rules library.

This is a **consumer dataset**, in the same spirit as [netrunner-comprehensive-rules-data](https://github.com/nhoople/netrunner-comprehensive-rules-data) and [netrunner-cards-json](https://github.com/Null-Signal-Games/netrunner-cards-json). It is not a rules engine and not a game client.

**Cards are pure data.** Each JSON file is a card definition (stats, subtypes, abilities as Effect IR). Executable evaluation lives in the engine; this repo does not contain IR/eval code.

See [`NOTICE`](NOTICE) for affiliation and trademark notes. Toolchain/schema are MIT; printed card text remains Null Signal Games reference material.

## Consume the data

Files under [`data/`](data/) are the API. Clone the repo or fetch a **tagged** release (do not pin `master`).

| Path | Use |
| --- | --- |
| [`data/schema.json`](data/schema.json) | JSON Schema for card definitions |
| [`data/pool.json`](data/pool.json) | Declared corpus. `corpusOrder` is the release order; every wave there is `supported` |

Every directory under `data/` that `corpusOrder` names is supported. The order is FFG Core through Kitara, Reign and Reverie, Magnum Opus (`mor` absorbed), System Core 2019, Downfall, Uprising, then Gateway through Vantage Point. Floor **`v1.146.0`**.

**Not in this repository:**

| Item | Policy |
|------|--------|
| NAPD (`napd`) | Skip |
| Draft | Skip |
| Championship | Skip |
| Terminal Directive campaign (`tdc`) | Deferred. The `td` card pack is supported |
| Salvaged Memories (`sm`) | Reprints only; no new titles |

**Formats:** unique-title play is covered for NSG Netrunner Core Sets, Standard, Startup, Eternal, and Random Access Memories. Ban lists are out of scope.

Partial cards list unimplemented clauses in an `unsupported` array — never silent wrong behavior. A wave marked `supported` in [`data/pool.json`](data/pool.json) must keep those arrays empty unless the card is listed with a reason in [`data/supported-unsupported-allowlist.json`](data/supported-unsupported-allowlist.json) (enforced by `scripts/validate-cards.py`). See [`CONTRIBUTING.md`](CONTRIBUTING.md) for the CR gate PR template.

### Cards ↔ engine pairing

Match this dataset and [netrunner-engine](https://github.com/nhoople/netrunner-engine) by the **same semver tag**. Pin a **release tag**, not `master`.

| Pairing | cards-data | engine |
|---------|------------|--------|
| **Current** | [`v1.146.0`](https://github.com/nhoople/netrunner-cards-data/releases/tag/v1.146.0) | [`v1.146.0`](https://github.com/nhoople/netrunner-engine/releases/tag/v1.146.0) (each printed ability is a Comprehensive Rules 9.3 record; printed corpus unchanged from v1.143.0) |

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
https://raw.githubusercontent.com/nhoople/netrunner-cards-data/v1.146.0/data
```

JavaScript — load the pool and one card from a tagged release:

```js
const base =
  "https://raw.githubusercontent.com/nhoople/netrunner-cards-data/v1.146.0/data";
const pool = await fetch(`${base}/pool.json`).then((r) => r.json());
const marjanah = await fetch(`${base}/system-gateway/marjanah.json`).then((r) =>
  r.json(),
);
console.log(pool.corpusOrder, marjanah.title);
```

## Current corpus

**Authoritative list:** [`data/pool.json`](data/pool.json) — **68/68** waves `supported` (`corpusOrder`, each wave’s `status`, and its card counts). The summary above is the boundary. Pack directories and card counts live in the pool.

**Floor `v1.146.0`:** Magnum Opus complete (**8/8**; `mor` absorbed). Fixtures wave removed (Plascrete under WLA). FFG Core-forward through Kitara, RaR, SC19→VP all `supported`. Eternal + RAM unique-title Magnum Opus gaps closed. Core Sets / Standard / Startup already full. Printed corpus unchanged from `v1.143.0`. Each printed ability is a Comprehensive Rules 9.3 record. Paired with engine `v1.146.0`.

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
