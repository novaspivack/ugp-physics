# Lean Theorem Registry (LTR)

Internal tooling for EPIC_090: federated catalog of Lean 4 declarations across Nova's
**22 public** Lean repos.

## Prerequisites

- Lean 4 (`elan`, `lake`) — same toolchain as target repos
- [probe-lean](https://github.com/Beneficial-AI-Foundation/probe-lean) 0.4.x+ (Schema 2.0)
- Python 3.11+ with PyYAML (stdlib otherwise)

## Quick start

```bash
cd ugp-physics/tools/lean_theorem_registry

# Install probe-lean (auto-detects Lean version from ugp-lean)
./scripts/install_probe_lean.sh

# Phase A: Tier 1 repos (ugp-lean, ugp-physics-lean, srrg-lean, rule110-lean)
./scripts/extract_all.sh --tier 1

# Phase B: remaining public repos
./scripts/extract_all.sh --tier all

# Merge probe JSON → SQLite
PYTHONPATH=. python3 -m ltr_index merge -o ../../data/ltr/ltr.db

# Metadata (best-effort)
PYTHONPATH=. python3 -m ltr_index metadata ingest --sources all

# Query
PYTHONPATH=. python3 -m ltr_index query stats
PYTHONPATH=. python3 -m ltr_index query deps \
  "ugp-lean:UgpLean.GTE.Evolution.canonical_orbit_triples" --max-depth 5

# Regenerate THEOREMS.md (ugp-lean-exp during dev)
PYTHONPATH=. python3 -m ltr_index export markdown --repo ugp-lean \
  --output /Users/nova/ugp-lean-exp/docs/THEOREMS.md
```

## Outputs

| Path | Description |
|------|-------------|
| `data/ltr/probes/<repo>_latest.json` | Latest probe-lean extract per repo |
| `data/ltr/probes/<repo>_summary.json` | Declaration/sorry/axiom counts |
| `data/ltr/ltr.db` | SQLite primary store |
| `data/ltr/unresolved_metadata.jsonl` | Unresolved metadata name log |

All under `data/ltr/` are gitignored.

## Configuration

- `config/ltr_repos.yaml` — repo paths, namespaces, tiers, Lake deps
- `config/mathlib_stub.yaml` — Mathlib/Std stub collapse rules

Set `LTR_CLONE_ROOT` if repos live outside `/Users/nova`.

## Extraction policy

- Wall-clock timeout: 3600s per repo (`LTR_EXTRACT_TIMEOUT` to override)
- Sorry detection enabled (no `--skip-verify`)
- Failed repos recorded in `*_summary.json` with `extract_status: failed`
- ugp-lean ↔ ugp-physics-lean cyclic dep: extract independently using local `.lake` cache

## Global IDs

```
<repo_slug>:<Lean.Fully.Qualified.Name>
```

Example: `ugp-lean:UgpLean.GTE.Evolution.canonical_orbit_triples`
