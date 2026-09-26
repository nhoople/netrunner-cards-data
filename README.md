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
| [`data/pool.json`](data/pool.json) | Declared supported corpus / wave order |
| [`data/stubs/`](data/stubs/) | Synthetic demo ice/breakers |
| [`data/wave1/`](data/wave1/), [`data/wave2/`](data/wave2/) | Early corpus waves |
| [`data/system-gateway/`](data/system-gateway/) | System Gateway (NRDB `sg`) |
| [`data/system-update-2021/`](data/system-update-2021/) | System Update 2021 (NRDB `su21`) |

**Corpus order:** stubs → wave1 → wave2 → System Gateway → System Update 2021 → later releases.

Partial cards list unimplemented clauses in an `unsupported` array — never silent wrong behavior.

### Pin by tag (engine)

Consumers should pin a release tag (e.g. `v0.1.0`), not `master`.

The engine declares the pin in [`data/cards-pin.json`](https://github.com/nhoople/netrunner-engine/blob/master/data/cards-pin.json) and fetches with:

```bash
npm run fetch-cards   # → vendor/cards-data/
```

Example raw URL base:

```text
https://raw.githubusercontent.com/nhoople/netrunner-cards-data/v0.1.0/data
```

JavaScript — load the pool and one card from a tagged release:

```js
const base =
  "https://raw.githubusercontent.com/nhoople/netrunner-cards-data/v0.1.0/data";
const pool = await fetch(`${base}/pool.json`).then((r) => r.json());
const crowbar = await fetch(`${base}/stubs/crowbar.json`).then((r) => r.json());
console.log(pool.corpusOrder, crowbar.title);
```

## Current corpus

| Wave | Count | Notes |
|------|------:|-------|
| stubs | 6 | Barrier ice + Crowbar fracter (demos) |
| wave1 | 8 | IDs, Hedge Fund / Easy Mark, PAD, Data Raven, … |
| wave2 | 13 | Ice diversity, Gordian/Ninja, Sure Gamble, … |
| system-gateway | 77 | Null Signal System Gateway (fully supported) |
| system-update-2021 | 82 | Null Signal System Update 2021 (fully supported) |

## Versioning

Tag dataset releases as `vMAJOR.MINOR.PATCH` (e.g. `v0.1.0`). Bump when card JSON, pool, or schema that consumers rely on changes.

## License

MIT for schema and tooling — see [`LICENSE`](LICENSE). Card text: see [`NOTICE`](NOTICE).

This project is not associated with, produced by, or endorsed by Null Signal Games, Fantasy Flight Games, R. Talsorian Games, or Wizards of the Coast.
