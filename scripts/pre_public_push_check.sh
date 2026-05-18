#!/bin/bash
# pre_public_push_check.sh
#
# Pre-flight safety check before pushing to the PUBLIC ugp-physics repo.
# Run this before: git push origin clean-main:main
#
# Exit code 0 = all clear. Exit code 1 = issues found — do NOT push.
#
# Usage:
#   bash scripts/pre_public_push_check.sh
#   bash scripts/pre_public_push_check.sh --verbose

set -euo pipefail

REPO_DIR="$(git rev-parse --show-toplevel)"
cd "$REPO_DIR"

VERBOSE=0
[[ "${1:-}" == "--verbose" ]] && VERBOSE=1

ISSUES=0
WARNINGS=0

_ok()   { echo "  OK:   $*"; }
_warn() { echo "  WARN: $*"; WARNINGS=$((WARNINGS + 1)); }
_fail() { echo "  FAIL: $*"; ISSUES=$((ISSUES + 1)); }

echo ""
echo "======================================================="
echo " Pre-push check — ugp-physics PUBLIC repo"
echo "======================================================="
echo ""

# ------------------------------------------------------------------
# CHECK 1: specs/ — must have ZERO tracked files
# ------------------------------------------------------------------
echo "[1] specs/ — no tracked files"
specs_count=$(git ls-files specs/ 2>/dev/null | wc -l | tr -d ' ')
if [ "$specs_count" -gt 0 ]; then
  _fail "specs/ has $specs_count tracked files — these would go public!"
  git ls-files specs/ | head -10
  echo "    Fix: git rm --cached -r specs/ && git commit"
else
  _ok "specs/ is untracked (gitignored)"
fi

# ------------------------------------------------------------------
# CHECK 2: .cursor/ — must have ZERO tracked files
# ------------------------------------------------------------------
echo "[2] .cursor/ — no tracked files"
cursor_count=$(git ls-files .cursor/ 2>/dev/null | wc -l | tr -d ' ')
if [ "$cursor_count" -gt 0 ]; then
  _fail ".cursor/ has $cursor_count tracked files — IDE rules contain private paths/config"
  git ls-files .cursor/
  echo "    Fix: git rm --cached -r .cursor/ && git commit"
else
  _ok ".cursor/ is untracked (gitignored)"
fi

# ------------------------------------------------------------------
# CHECK 3: vyra_analysis/ — must have ZERO tracked files
# ------------------------------------------------------------------
echo "[3] vyra_analysis/ — no tracked files"
vyra_count=$(git ls-files vyra_analysis/ 2>/dev/null | wc -l | tr -d ' ')
if [ "$vyra_count" -gt 0 ]; then
  _fail "vyra_analysis/ has $vyra_count tracked files"
  git ls-files vyra_analysis/ | head -5
else
  _ok "vyra_analysis/ is untracked (gitignored)"
fi

# ------------------------------------------------------------------
# CHECK 4: NOVA_PUBLISHING_HANDOFF files — must not be tracked anywhere
# ------------------------------------------------------------------
echo "[4] NOVA_PUBLISHING_HANDOFF files — none tracked"
handoff_files=$(git ls-files | grep -i "NOVA_PUBLISHING" 2>/dev/null || true)
if [ -n "$handoff_files" ]; then
  handoff_count=$(echo "$handoff_files" | wc -l | tr -d ' ')
  _fail "$handoff_count NOVA_PUBLISHING files are tracked"
  echo "$handoff_files"
else
  _ok "No NOVA_PUBLISHING files tracked"
fi

# ------------------------------------------------------------------
# CHECK 5: Private email address not in any tracked file
# ------------------------------------------------------------------
echo "[5] Private email (nova@novaspivack.com) — not in tracked files"
email_files=$(git ls-files | grep -v "scripts/pre_public_push_check.sh" | xargs grep -l "nova@novaspivack\.com" 2>/dev/null || true)
if [ -n "$email_files" ]; then
  _fail "Private email found in tracked files:"
  echo "$email_files" | head -10 | sed 's/^/    /'
else
  _ok "No private email in tracked files"
fi

# ------------------------------------------------------------------
# CHECK 6: Local machine paths in paper .tex files
# ------------------------------------------------------------------
echo "[6] Local paths (/Users/nova/) — not in paper .tex files"
tex_files=$(git ls-files papers/ | grep "\.tex$" || true)
if [ -n "$tex_files" ]; then
  path_files=$(echo "$tex_files" | xargs grep -l "/Users/nova/" 2>/dev/null || true)
  if [ -n "$path_files" ]; then
    _warn "Local machine paths found in .tex files:"
    echo "$path_files" | head -10 | sed 's/^/    /'
  else
    _ok "No local paths in paper .tex files"
  fi
else
  _ok "No .tex files tracked (nothing to check)"
fi

# ------------------------------------------------------------------
# CHECK 7: Internal spec/epic reference IDs in paper .tex files
# ------------------------------------------------------------------
echo "[7] Internal SPEC_/EPIC_ IDs — not in paper .tex files"
if [ -n "$tex_files" ]; then
  spec_files=$(echo "$tex_files" | xargs grep -lE "SPEC_[0-9]|EPIC_[0-9]" 2>/dev/null || true)
  if [ -n "$spec_files" ]; then
    _fail "Internal spec/epic IDs found in paper .tex files:"
    echo "$spec_files" | head -10 | sed 's/^/    /'
  else
    _ok "No internal spec/epic IDs in paper .tex files"
  fi
else
  _ok "No .tex files tracked (nothing to check)"
fi

# ------------------------------------------------------------------
# CHECK 8: Large files > 50 MB that aren't LFS-tracked
# Uses git ls-tree for size rather than stat-ing each file on disk.
# ------------------------------------------------------------------
echo "[8] Oversized non-LFS files (>50 MB)"
# git ls-tree -r -l HEAD gives: mode type hash size path
# Skip files declared as LFS (their on-disk pointer is tiny; blob size in index ~130 bytes)
large_files=$(git ls-tree -r -l HEAD 2>/dev/null | awk '$4 > 52428800 {print $5, "(" int($4/1048576) "MB)"}' | while read -r fpath fsize; do
  # Confirm it's not an LFS pointer (LFS objects in index are ~130-200 bytes)
  if git check-attr filter -- "$fpath" 2>/dev/null | grep -q "filter: lfs"; then
    : # LFS-managed, skip
  else
    echo "$fpath $fsize"
  fi
done || true)
if [ -n "$large_files" ]; then
  _warn "Large non-LFS files found (may cause push failures):"
  echo "$large_files" | head -10 | sed 's/^/    /'
else
  _ok "No oversized non-LFS files"
fi

# ------------------------------------------------------------------
# CHECK 9: Orphan simulation — what git add -A would stage from sensitive dirs
# (Catches files that are untracked but not gitignored — a gitignore gap)
# ------------------------------------------------------------------
echo "[9] Gitignore gaps — no untracked sensitive files slipping through"
SENSITIVE_DIRS=("specs/" ".cursor/" "vyra_analysis/" "research_sandbox/")
gap_found=0
for dir in "${SENSITIVE_DIRS[@]}"; do
  if [ -d "$dir" ]; then
    leaked=$(git ls-files --others --exclude-standard "$dir" 2>/dev/null | head -3)
    if [ -n "$leaked" ]; then
      _fail "Gitignore gap: $dir has untracked-but-not-gitignored files:"
      echo "$leaked" | sed 's/^/    /'
      gap_found=1
    fi
  fi
done
[ "$gap_found" -eq 0 ] && _ok "No gitignore gaps in sensitive directories"

# ------------------------------------------------------------------
# CHECK 10: Confirm we are on the main branch (not clean-main)
# ------------------------------------------------------------------
echo "[10] Branch check — running from main (dev) branch"
current_branch=$(git rev-parse --abbrev-ref HEAD)
if [ "$current_branch" == "main" ]; then
  _ok "On 'main' branch"
elif [ "$current_branch" == "clean-main" ]; then
  _warn "On 'clean-main' branch — this check is most useful when run from 'main'"
else
  _warn "On branch '$current_branch' — expected 'main'"
fi

# ------------------------------------------------------------------
# VERBOSE: show what WOULD be in the public push (tracked public files)
# ------------------------------------------------------------------
if [ "$VERBOSE" -eq 1 ]; then
  echo ""
  echo "=== Verbose: tracked public files by top-level directory ==="
  git ls-files | sed 's|/.*||' | sort -u | while read -r topdir; do
    count=$(git ls-files "$topdir" 2>/dev/null | wc -l | tr -d ' ')
    echo "  $topdir/  ($count files)"
  done
fi

# ------------------------------------------------------------------
# SUMMARY
# ------------------------------------------------------------------
echo ""
echo "======================================================="
if [ "$ISSUES" -eq 0 ] && [ "$WARNINGS" -eq 0 ]; then
  echo " RESULT: ALL CHECKS PASSED — safe to push to public repo"
  echo "======================================================="
  echo ""
  exit 0
elif [ "$ISSUES" -eq 0 ]; then
  echo " RESULT: PASSED with $WARNINGS warning(s) — review before pushing"
  echo "======================================================="
  echo ""
  exit 0
else
  echo " RESULT: FAILED — $ISSUES issue(s), $WARNINGS warning(s)"
  echo " DO NOT push to public repo until all FAILs are resolved."
  echo "======================================================="
  echo ""
  exit 1
fi
