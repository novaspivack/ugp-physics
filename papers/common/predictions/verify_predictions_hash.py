#!/usr/bin/env python3
"""
Verify the SHA-256 hash of ugp_falsifiable_predictions_v1.md.

Reads ugp_falsifiable_predictions_v1.sha256 (companion file in the same directory),
recomputes the SHA-256 of ugp_falsifiable_predictions_v1.md, and compares them.

Exit code 0 = verified (hashes match).
Exit code 1 = mismatch or missing file.
"""

import hashlib
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
REGISTRY_FILE = SCRIPT_DIR / "ugp_falsifiable_predictions_v1.md"
HASH_FILE = SCRIPT_DIR / "ugp_falsifiable_predictions_v1.sha256"


def sha256_of_file(path: Path) -> str:
    raw = path.read_bytes()
    return hashlib.sha256(raw).hexdigest()


def main() -> int:
    for f in (REGISTRY_FILE, HASH_FILE):
        if not f.exists():
            print(f"ERROR: required file not found: {f}", file=sys.stderr)
            return 1

    recorded = HASH_FILE.read_text(encoding="utf-8").strip().split()[0]
    computed = sha256_of_file(REGISTRY_FILE)

    if computed == recorded:
        print(f"OK: SHA-256 verified")
        print(f"   file    : {REGISTRY_FILE.name}")
        print(f"   hash    : {computed}")
        return 0
    else:
        print("FAIL: hash mismatch", file=sys.stderr)
        print(f"   file    : {REGISTRY_FILE.name}", file=sys.stderr)
        print(f"   recorded: {recorded}", file=sys.stderr)
        print(f"   computed: {computed}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
