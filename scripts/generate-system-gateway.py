#!/usr/bin/env python3
"""Regenerate System Gateway card JSON from pinned pack `sg`.

Catalog source: Null-Signal-Games/netrunner-cards-json (see data/nrdb-catalog-pin.json).
Fetch with: python3 scripts/nrdb_catalog.py fetch sg

Hand-mapped Effect IR; unsupported clauses listed explicitly.
Reprints Sure Gamble (30030) and Hedge Fund (30075) are skipped (reuse wave defs).

Usage: python3 scripts/generate-system-gateway.py
"""
# NOTE: Full mapping lives in git history / data/system-gateway/*.json.
# This stub documents how the corpus was produced; prefer editing card JSON
# directly for fidelity fixes. Re-run only when refreshing from the pinned catalog.
print("Gateway cards are committed under data/system-gateway/.")
print("Catalog pin: data/nrdb-catalog-pin.json (netrunner-cards-json).")
print("Fetch pack: python3 scripts/nrdb_catalog.py fetch sg")
print("To refresh stubs, restore the generator from git history or re-author maps.")
