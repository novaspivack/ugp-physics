#!/usr/bin/env bash
# Install probe-lean binary for the Lean toolchain used by target repos.
# See: https://github.com/Beneficial-AI-Foundation/probe-lean
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TOOL_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PROJECT="${1:-${LTR_PROBE_FROM_PROJECT:-/Users/nova/ugp-lean}}"

if command -v probe-lean >/dev/null 2>&1; then
  echo "probe-lean already installed: $(probe-lean --version 2>/dev/null || echo ok)"
  exit 0
fi

echo "Installing probe-lean from project toolchain: $PROJECT"
if ! curl -sSfL https://raw.githubusercontent.com/Beneficial-AI-Foundation/probe-lean/main/tools/bash/install.sh \
  | bash -s -- --from-project "$PROJECT"; then
  echo "Official installer failed; building probe-lean from source for detected toolchain..." >&2
  DETECTED=$(grep -o 'v[0-9.]*' "$PROJECT/lean-toolchain" | head -1)
  SRC="${HOME}/.local/src/probe-lean"
  if [ ! -d "$SRC/.git" ]; then
    git clone --depth 1 https://github.com/Beneficial-AI-Foundation/probe-lean.git "$SRC"
  else
    git -C "$SRC" fetch origin main --quiet && git -C "$SRC" checkout origin/main --quiet
  fi
  cd "$SRC"
  echo "leanprover/lean4:${DETECTED}" > lean-toolchain
  sed -i '' 's/rev = "v[^"]*"/rev = "v4.29.0"/' lakefile.toml 2>/dev/null || \
    sed -i 's/rev = "v[^"]*"/rev = "v4.29.0"/' lakefile.toml
  rm -rf .lake lake-manifest.json
  lake build
  mkdir -p "${HOME}/.local/bin" "${HOME}/.local/lib/probe-lean-${DETECTED}"
  cp .lake/build/bin/probe-lean "${HOME}/.local/bin/probe-lean-${DETECTED}"
  chmod +x "${HOME}/.local/bin/probe-lean-${DETECTED}"
  rm -rf "${HOME}/.local/lib/probe-lean-${DETECTED:?}"/*
  cp -r .lake/build/lib/lean/ProbeLean* "${HOME}/.local/lib/probe-lean-${DETECTED}/"
  ln -sf "probe-lean-${DETECTED}" "${HOME}/.local/bin/probe-lean"
fi

export PATH="$PATH:${HOME}/.local/bin"
if ! command -v probe-lean >/dev/null 2>&1; then
  echo "ERROR: probe-lean not found after install. Add ~/.local/bin to PATH." >&2
  exit 1
fi

echo "probe-lean installed: $(probe-lean --version 2>/dev/null || echo ok)"
