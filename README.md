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
| [`data/system-gateway/`](data/system-gateway/) | System Gateway (NRDB `sg`) |
| [`data/system-update-2021/`](data/system-update-2021/) | System Update 2021 (NRDB `su21`) |
| [`data/midnight-sun/`](data/midnight-sun/) | Midnight Sun (NRDB `ms`) — in progress |

**Corpus order:** System Gateway → System Update 2021 → Midnight Sun → later releases.

Partial cards list unimplemented clauses in an `unsupported` array — never silent wrong behavior.

### Cards ↔ engine pairing

Match this dataset and [netrunner-engine](https://github.com/nhoople/netrunner-engine) by the **same semver tag**. Pin a **release tag**, not `master`.

| Pairing | cards-data | engine |
|---------|------------|--------|
| **Current** | [`v0.35.0`](https://github.com/nhoople/netrunner-cards-data/releases/tag/v0.35.0) | [`v0.35.0`](https://github.com/nhoople/netrunner-engine/releases/tag/v0.35.0) |

Incremental wave tags are the day-to-day IR/wiring contract. A set-complete **milestone** GitHub Release is cut only when a wave’s pool status → `supported` (advertised host floor for that set).

The engine declares the pin in [`data/cards-pin.json`](https://github.com/nhoople/netrunner-engine/blob/master/data/cards-pin.json) and fetches with:

```bash
npm run fetch-cards   # → vendor/cards-data/
```

Example raw URL base:

```text
https://raw.githubusercontent.com/nhoople/netrunner-cards-data/v0.16.0/data
```

JavaScript — load the pool and one card from a tagged release:

```js
const base =
  "https://raw.githubusercontent.com/nhoople/netrunner-cards-data/v0.16.0/data";
const pool = await fetch(`${base}/pool.json`).then((r) => r.json());
const marjanah = await fetch(`${base}/system-gateway/marjanah.json`).then((r) =>
  r.json(),
);
console.log(pool.corpusOrder, marjanah.title);
```

## Current corpus

| Release | Count | Notes |
|---------|------:|-------|
| system-gateway | 77 | Null Signal System Gateway (fully supported) |
| system-update-2021 | 82 | Null Signal System Update 2021 (fully supported) |
| midnight-sun | 65 | Null Signal Midnight Sun (`ms`); `msbp` titles absorbed; status `in-progress` |

Synthetic stubs and early wave1/wave2 dirs were removed in `v0.2.0`. Reprints that previously lived only under those waves now ship under their Null Signal release directories.

Midnight Sun extract lists unimplemented clauses (including sabotage / mark / charge) in each card’s `unsupported` array. Do not treat the wave as fully supported until those notes are cleared or explicitly deferred.

## Versioning

Tag dataset releases as `vMAJOR.MINOR.PATCH` (e.g. `v0.16.0`). Bump when card JSON, pool, or schema that consumers rely on changes. Keep the README pairing line in sync after each pin bump (no new tag for README-only).

## License

MIT for schema and tooling — see [`LICENSE`](LICENSE). Card text: see [`NOTICE`](NOTICE).

This project is not associated with, produced by, or endorsed by Null Signal Games, Fantasy Flight Games, R. Talsorian Games, or Wizards of the Coast.
