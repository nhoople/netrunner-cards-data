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
| [`data/pool.json`](data/pool.json) | Declared corpus. `corpusOrder` is the release order; every wave there is `supported`. Each wave also has `dateRelease`, `cycle`, and `size` |
| [`data/printings/`](data/printings/) | One file per printing (`<code>.json`): title id, pack, flavor, illustrator, `quantity` (copies in that pack), and `position`. The image address is `https://card-images.netrunnerdb.com/v2/large/{code}.jpg` |
| [`data/printed/`](data/printed/) | One file per title (`<id>.json`): the current printed `text` and `strippedText`, errata included. The rules file keeps the Effect IR |
| [`data/rulings/`](data/rulings/) | One file per title with a rules-team-verified ruling (`<id>.json`). Taken from the pinned catalog's `v2/rulings/` snapshot of the NetrunnerDB rulings API. Unverified rulings are left out. A ruling explains the card text; an erratum changes the text itself |
| [`data/formats/`](data/formats/) | One file per format. Each snapshot names a card pool and, when the catalog has one, a restriction |
| [`data/card-pools/`](data/card-pools/) | The waves legal in one snapshot of a format |
| [`data/restrictions/`](data/restrictions/) | Ban lists, Most Wanted Lists, and balance updates: banned and restricted titles, influence points, and agenda caps |
| [`data/rotations.json`](data/rotations.json) | Rotation dates and the waves that left a format |

Card files live at `data/<side>/<type>/<id>.json` (for example `data/runner/program/marjanah.json`). `corpusOrder` in [`data/pool.json`](data/pool.json) is the release order, and every wave there is supported. The order is FFG Core through Kitara, Reign and Reverie, Magnum Opus (`mor` absorbed), System Core 2019, Downfall, Uprising, then Gateway through Vantage Point. Floor **`v1.147.7`**.

**Not in this repository:**

| Item | Policy |
|------|--------|
| NAPD (`napd`) | Skip |
| Draft | Skip |
| Championship | Skip |
| Terminal Directive campaign (`tdc`) | Deferred. The `td` card pack is supported |
| Salvaged Memories (`sm`) | Reprints only; no new titles |

**Formats:** unique-title play is covered for NSG Netrunner Core Sets, Standard, Startup, Eternal, and Random Access Memories. The legal pools, ban lists, and balance updates are the files above. The engine does not check a deck against them yet. Each rules file has `deckLimit`, the maximum copies of that title in a deck.

**Deferred catalog data.** These exist in the pinned Null Signal catalog and are not copied here:

| Item | Upstream | Why it waits |
| --- | --- | --- |
| Unverified rulings | `v2/rulings/` | Only rulings with `nsg_rules_team_verified` are kept |
| Ruling source names | `v2/ruling_sources.json` | The ruling text already names its source |
| Translations | `v2/translations/` | Locale display, not play |
| Designer credit, pronouns, pronunciation, narrative text | fields on `v2/cards/` | Not used by the engine or the table |
| Prebuilt decks | `prebuilts.json` | Six published deck lists |
| Second face and layout | `v2/printings/` | The pack files this corpus copies have a single face |

Partial cards list unimplemented clauses in an `unsupported` array — never silent wrong behavior. A wave marked `supported` in [`data/pool.json`](data/pool.json) must keep those arrays empty unless the card is listed with a reason in [`data/supported-unsupported-allowlist.json`](data/supported-unsupported-allowlist.json) (enforced by `scripts/validate-cards.py`). See [`CONTRIBUTING.md`](CONTRIBUTING.md) for the CR gate PR template.

### Cards ↔ engine pairing

Match this dataset and [netrunner-engine](https://github.com/nhoople/netrunner-engine) by the **same semver tag**. Pin a **release tag**, not `master`.

| Pairing | cards-data | engine |
|---------|------------|--------|
| **Current** | [`v1.147.7`](https://github.com/nhoople/netrunner-cards-data/releases/tag/v1.147.7) | [`v1.147.9`](https://github.com/nhoople/netrunner-engine/releases/tag/v1.147.9) still pins cards [`v1.147.6`](https://github.com/nhoople/netrunner-cards-data/releases/tag/v1.147.6) and loads pack directories |

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
https://raw.githubusercontent.com/nhoople/netrunner-cards-data/v1.147.7/data
```

JavaScript — load the pool and one card from a tagged release:

```js
const base =
  "https://raw.githubusercontent.com/nhoople/netrunner-cards-data/v1.147.7/data";
const pool = await fetch(`${base}/pool.json`).then((r) => r.json());
const marjanah = await fetch(`${base}/runner/program/marjanah.json`).then((r) =>
  r.json(),
);
console.log(pool.corpusOrder, marjanah.title);
```

## Current corpus

**Authoritative list:** [`data/pool.json`](data/pool.json) — **68/68** waves `supported` (`corpusOrder`, each wave’s `status`, and its card counts). The summary above is the boundary. Pack membership and card counts live in the pool. Card files are grouped by side and type.

**Floor `v1.147.7`:** Card files are grouped by side and type. Each title has `deckLimit` and a printed sentence. Printings, verified rulings, format pools, ban lists, and rotations are separate files. The title corpus is unchanged from `v1.147.6`: Magnum Opus complete (**8/8**; `mor` absorbed), FFG Core-forward through Kitara, RaR, SC19→VP all `supported`. Runner identities store base link (CR 2.9.1), identities store minimum deck size and influence limit (CR 2.11.1, CR 2.12.1), and other cards store influence cost when they have an influence bar (CR 2.14.1). Ice, assets, and upgrades keep `rezCost` and do not store `installCost` (CR 1.16.6b, CR 8.5.11a). Released engine `v1.147.9` still pins cards `v1.147.6`.

**Next:** Idle / absorb-only until next NSG pack after VP or CR bump. Skip `napd`/draft/championship; defer `tdc`. GitHub Releases only at set-complete or explicit manual — not per-slice.

## Versioning

Tag dataset releases as `vMAJOR.MINOR.PATCH` (e.g. `v1.35.0`). Bump when card JSON, pool, or schema that consumers rely on changes. Keep the README pairing line in sync after each pin bump (no new tag for README-only).

## Data pipeline / catalog extract source

**Pipeline:** pinned [Null-Signal-Games/netrunner-cards-json](https://github.com/Null-Signal-Games/netrunner-cards-json) (NSG source of truth; NRDB is downstream) → author Effect IR into this repo → [nhoople/netrunner-engine](https://github.com/nhoople/netrunner-engine) pins our tags.

Pack metadata for generate/extract scripts comes from that NSG repo (`pack/{code}.json`). The NetrunnerDB public API is **not** the preferred ingest. NRDB codes may still appear as identifiers (pack codes, card ids); that does not make NRDB the catalog source.

When you are about to take a new pack, or when you hear about an errata, run:

```bash
python3 scripts/nsg_catalog.py check
```

That compares the pinned commit with current `main`. It reports a pack code that is not in the corpus, and any change to `faction_code`, cost, strength, or printed text in a corpus pack. The corpus is every pack code named in `pool.json` or fetched by a `generate-*.py` script. `napd`, `tdc`, and `sm` stay outside it. The command does not edit card files. Copy an accepted fact onto the existing card. When the printed text changed, re-read that card's ability record. Then set `ref` in the pin to the reviewed commit, clear `tmp/nsg-catalog/`, and re-fetch.

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
