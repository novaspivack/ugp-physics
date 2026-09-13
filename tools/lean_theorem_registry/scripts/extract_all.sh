#!/usr/bin/env bash
# Extract probe-lean JSON for public Lean repos (EPIC_090).
# Usage: extract_all.sh [--tier 1|2|3|all] [--repo SLUG] [--skip-build]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TOOL_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
UGP_PHYSICS="$(cd "$TOOL_ROOT/../.." && pwd)"
CONFIG="$TOOL_ROOT/config/ltr_repos.yaml"
PROBE_DIR="$UGP_PHYSICS/data/ltr/probes"
LOG_DIR="$UGP_PHYSICS/data/ltr/logs"
TIMEOUT_SECONDS="${LTR_EXTRACT_TIMEOUT:-3600}"

TIER_FILTER="all"
SINGLE_REPO=""
SKIP_BUILD=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --tier) TIER_FILTER="$2"; shift 2 ;;
    --repo) SINGLE_REPO="$2"; shift 2 ;;
    --skip-build) SKIP_BUILD=1; shift ;;
    *) echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

mkdir -p "$PROBE_DIR" "$LOG_DIR"

export PATH="$PATH:${HOME}/.local/bin"
if ! command -v probe-lean >/dev/null 2>&1; then
  echo "probe-lean not found; running install_probe_lean.sh" >&2
  bash "$SCRIPT_DIR/install_probe_lean.sh"
fi

# Dependency order for Tier 2+3 (Tier 1 handled separately)
read -r -d '' EXTRACT_ORDER <<'ORDER' || true
aps-undecidability-interfaces-lean
aps-rice-lean
viable-continuation-lean
representational-incompleteness-lean
novelty-theory-lean
infinity-compression-lean
aps-recursion-composition-uniformity-lean
aps-recursion-uniformization-lean
nems-lean
transputation-lean
reflective-fold-obstruction-lean
reflexive-closure-lean
sentience-lean
phenomenology-lean
reflexive-architecture-lean
adequacy-architecture-lean
observer-non-exhaustability-lean
reflexive-architecture-non-exhaustibility-lean
ugp-physics-lean
ugp-lean
srrg-lean
rule110-lean
reflexive-reality-lean
ORDER

TIER1_ORDER="rule110-lean ugp-physics-lean ugp-lean srrg-lean"

resolve_path() {
  python3 - "$CONFIG" "$1" <<'PY'
import os, sys
try:
    import yaml
except ImportError:
    sys.exit("PyYAML required")
cfg = yaml.safe_load(open(sys.argv[1]))
repo = cfg["repos"][sys.argv[2]]
path = repo["path"]
path = os.path.expandvars(path.replace("${LTR_CLONE_ROOT:-/Users/nova}", os.environ.get("LTR_CLONE_ROOT", "/Users/nova")))
print(path)
PY
}

repo_meta() {
  python3 - "$CONFIG" "$1" <<'PY'
import json, os, sys
import yaml
cfg = yaml.safe_load(open(sys.argv[1]))
r = cfg["repos"][sys.argv[2]]
path = r["path"]
path = os.path.expandvars(path.replace("${LTR_CLONE_ROOT:-/Users/nova}", os.environ.get("LTR_CLONE_ROOT", "/Users/nova")))
print(json.dumps({
  "tier": r.get("tier", 1),
  "default_library": r.get("default_library", r.get("package", "")),
  "path": path,
}))
PY
}

should_extract() {
  local slug="$1"
  local tier
  tier=$(python3 -c "import yaml; print(yaml.safe_load(open('$CONFIG'))['repos']['$slug']['tier'])")
  if [[ -n "$SINGLE_REPO" ]]; then
    [[ "$slug" == "$SINGLE_REPO" ]]
    return
  fi
  case "$TIER_FILTER" in
    1) [[ "$tier" == "1" ]] ;;
    2) [[ "$tier" == "2" ]] ;;
    3) [[ "$tier" == "3" ]] ;;
    all) return 0 ;;
    *) echo "Invalid tier: $TIER_FILTER" >&2; exit 1 ;;
  esac
}

extract_repo() {
  local slug="$1"
  local meta path lib commit short_sha out_json summary_json log_file
  meta=$(repo_meta "$slug")
  path=$(echo "$meta" | python3 -c "import json,sys; print(json.load(sys.stdin)['path'])")
  lib=$(echo "$meta" | python3 -c "import json,sys; print(json.load(sys.stdin)['default_library'])")

  if [[ ! -d "$path" ]]; then
    echo "FAIL $slug: path missing: $path" >&2
    python3 - "$slug" "path missing: $path" <<'PY' > "$PROBE_DIR/${slug}_summary.json"
import json, sys, datetime
print(json.dumps({
  "repo_slug": sys.argv[1],
  "extract_status": "failed",
  "error": sys.argv[2],
  "extracted_at": datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
}, indent=2))
PY
    return 1
  fi

  commit=$(git -C "$path" rev-parse HEAD 2>/dev/null || echo "unknown")
  short_sha="${commit:0:7}"
  out_json="$PROBE_DIR/${slug}_${short_sha}.json"
  summary_json="$PROBE_DIR/${slug}_summary.json"
  log_file="$LOG_DIR/${slug}_extract.log"

  echo "=== Extracting $slug ($path) library=$lib ==="

  {
    echo "repo=$slug path=$path commit=$commit"
    cd "$path"
    if [[ "$SKIP_BUILD" -eq 0 ]]; then
      echo "Running: lake build $lib"
      lake build "$lib"
    else
      echo "Skipping lake build (--skip-build)"
    fi
    echo "Running: probe-lean extract $path -o $out_json --library $lib"
    probe-lean extract "$path" -o "$out_json" --library "$lib"
  } > "$log_file" 2>&1 &
  local pid=$!
  local elapsed=0
  while kill -0 "$pid" 2>/dev/null; do
    if [[ "$elapsed" -ge "$TIMEOUT_SECONDS" ]]; then
      echo "TIMEOUT: $slug exceeded ${TIMEOUT_SECONDS}s" | tee -a "$log_file"
      kill -TERM "$pid" 2>/dev/null || true
      sleep 2
      kill -KILL "$pid" 2>/dev/null || true
      python3 - "$slug" "$TIMEOUT_SECONDS" <<'PY' > "$summary_json"
import json, sys, datetime
print(json.dumps({
  "repo_slug": sys.argv[1],
  "extract_status": "failed",
  "error": f"timeout after {sys.argv[2]}s",
  "extracted_at": datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
}, indent=2))
PY
      return 1
    fi
    sleep 5
    elapsed=$((elapsed + 5))
  done
  wait "$pid" || {
    echo "FAIL $slug: see $log_file" >&2
    tail -20 "$log_file" >&2
    python3 - "$slug" "extract failed; see log" "$log_file" <<'PY' > "$summary_json"
import json, sys, datetime
print(json.dumps({
  "repo_slug": sys.argv[1],
  "extract_status": "failed",
  "error": sys.argv[2],
  "log": sys.argv[3],
  "extracted_at": datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
}, indent=2))
PY
    return 1
  }

  cp -f "$out_json" "$PROBE_DIR/${slug}_latest.json"
  python3 - "$out_json" "$summary_json" "$slug" "$commit" <<'PY'
import json, sys, datetime
out_path, summary_path, slug, commit = sys.argv[1:5]
data = json.load(open(out_path))
if data.get("schema") != "probe-lean/extract" or data.get("schema-version") != "2.0":
    raise SystemExit(f"Invalid schema in {out_path}")
atoms = data.get("data") or {}
if not atoms:
    raise SystemExit(f"Zero declarations in {out_path}")
decls = [a for a in atoms.values() if a.get("is-in-package", True)]
sorry = sum(1 for a in decls if a.get("verification-status") == "unverified")
axiom = sum(1 for a in decls if a.get("verification-status") == "trusted" and a.get("trusted-reason") == "axiom")
by_kind = {}
for a in decls:
    k = a.get("kind", "unknown")
    by_kind[k] = by_kind.get(k, 0) + 1
summary = {
  "repo_slug": slug,
  "commit": commit,
  "extract_status": "success",
  "extracted_at": datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
  "probe_json": out_path,
  "declaration_count": len(decls),
  "sorry_count": sorry,
  "axiom_count": axiom,
  "theorem_count": by_kind.get("theorem", 0),
  "lemma_count": by_kind.get("lemma", 0),
  "by_kind": by_kind,
}
json.dump(summary, open(summary_path, "w"), indent=2)
print(json.dumps(summary, indent=2))
PY

  echo "OK $slug: $(python3 -c "import json; print(json.load(open('$summary_json'))['declaration_count'])") declarations"
}

FAILURES=0
SUCCESSES=0

run_order() {
  local slug
  for slug in "$@"; do
    if should_extract "$slug"; then
      if extract_repo "$slug"; then
        SUCCESSES=$((SUCCESSES + 1))
      else
        FAILURES=$((FAILURES + 1))
      fi
    fi
  done
}

if [[ "$TIER_FILTER" == "1" || "$TIER_FILTER" == "all" ]]; then
  run_order $TIER1_ORDER
fi

if [[ "$TIER_FILTER" == "2" || "$TIER_FILTER" == "3" || "$TIER_FILTER" == "all" ]]; then
  while IFS= read -r slug; do
    [[ -z "$slug" ]] && continue
    if should_extract "$slug"; then
      if extract_repo "$slug"; then
        SUCCESSES=$((SUCCESSES + 1))
      else
        FAILURES=$((FAILURES + 1))
      fi
    fi
  done <<< "$EXTRACT_ORDER"
fi

echo "=== Extraction complete: $SUCCESSES succeeded, $FAILURES failed ==="
if [[ "$TIER_FILTER" == "1" && "$FAILURES" -gt 0 && -z "$SINGLE_REPO" ]]; then
  echo "ERROR: Tier 1 extraction had failures" >&2
  exit 1
fi
exit 0
