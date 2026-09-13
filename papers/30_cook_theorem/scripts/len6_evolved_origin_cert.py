#!/usr/bin/env python3
"""
L=6 evolved-origin list certificate (Phase B cross-check).

Mirrors `len6Tail420ComposeOriginOk` / `len6FastCompose420OriginOk` in
`rule110-lean/Rule110/CookLen6TailEvolution.lean`: at each of six slot origins,
420 bounded list steps from the phased `[true]` encode agree with 30 steps from
the post-390 evolved list.

Usage:
  python3 len6_evolved_origin_cert.py [--init PATH] [--out PATH]

Default init tape: ../data/len6_true_phased_support_init.json (exported from Lean via
`rule110-lean/scripts/export_len6_phased_init.lean`).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

C2_SIM_BOUND = 2500
CTS_TAPE_ORIGIN = 1000
CTS_GLIDER_SPACING = 42
M390 = 390
M30 = 30
M420 = M390 + M30
NUM_SLOTS = 6

# Rule 110 (Wolfram code 110): index 4*L + 2*C + R
RULE110 = (
    False, True, True, True, False, True, True, False,
)


def cook_ether(i: int) -> bool:
    bits = (
        True, False, False, True, True, False, True, True,
        True, True, True, False, False, False,
    )
    return bits[i % 14]


def neighborhood_index(left: bool, center: bool, right: bool) -> int:
    return (4 * int(left)) + (2 * int(center)) + int(right)


def rule110_output(left: bool, center: bool, right: bool) -> bool:
    return RULE110[neighborhood_index(left, center, right)]


def c2_sim_left(tape: list[bool], i: int) -> bool:
    if i == 0:
        return False
    return tape[i - 1]


def c2_sim_right(tape: list[bool], i: int) -> bool:
    if i + 1 < len(tape):
        return tape[i + 1]
    return cook_ether(i + 1)


def c2_sim_step(tape: list[bool]) -> list[bool]:
    return [
        rule110_output(
            c2_sim_left(tape, i),
            tape[i],
            c2_sim_right(tape, i),
        )
        for i in range(len(tape))
    ]


def c2_sim_run(n: int, tape: list[bool]) -> list[bool]:
    out = tape
    for _ in range(n):
        out = c2_sim_step(out)
    return out


def c2_sim_origin(slot: int) -> int:
    return CTS_TAPE_ORIGIN + slot * CTS_GLIDER_SPACING


def load_init(path: Path) -> list[bool]:
    raw = json.loads(path.read_text())
    if not isinstance(raw, list):
        raise ValueError(f"init tape must be a JSON array: {path}")
    init = [bool(x) for x in raw]
    if len(init) != C2_SIM_BOUND:
        raise ValueError(f"expected {C2_SIM_BOUND} cells, got {len(init)} from {path}")
    return init


def verify_compose(init: list[bool]) -> dict:
    evolved390 = c2_sim_run(M390, init)
    fin420 = c2_sim_run(M420, init)
    evolved30 = c2_sim_run(M30, evolved390)
    slots = []
    ok = True
    for slot in range(NUM_SLOTS):
        origin = c2_sim_origin(slot)
        v420 = fin420[origin]
        v30 = evolved30[origin]
        match = v420 == v30
        ok = ok and match
        slots.append({
            "slot": slot,
            "origin": origin,
            "fin420": v420,
            "evolved30": v30,
            "match": match,
        })
    return {"ok": ok, "slots": slots}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify L=6 evolved-origin list certificate.")
    parser.add_argument(
        "--init",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "data" / "len6_true_phased_support_init.json",
        help="Path to phased support init tape JSON (2500 booleans)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "data" / "len6_evolved_origin_cert.json",
        help="Output certificate JSON path",
    )
    args = parser.parse_args()

    if not args.init.is_file():
        print(
            f"Missing init tape: {args.init}\n"
            "Export from Lean:\n"
            "  cd rule110-lean && lake env lean --run scripts/export_len6_phased_init.lean\n"
            "  cp len6_true_phased_support_init.json papers/30_cook_theorem/data/",
            file=sys.stderr,
        )
        return 1

    init = load_init(args.init)
    result = verify_compose(init)
    payload = {
        "certificate": "len6Tail420ComposeOriginOk",
        "M1": M390,
        "M2": M30,
        "compose_M": M420,
        "c2SimBound": C2_SIM_BOUND,
        "init_tape_sha256": sha256_file(args.init),
        "init_tape_path": str(args.init),
        "result": result,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    cert_hash = sha256_file(args.out)

    print(f"Certificate: {'PASS' if result['ok'] else 'FAIL'}")
    print(f"Wrote {args.out}")
    print(f"SHA-256: {cert_hash}")
    for row in result["slots"]:
        status = "ok" if row["match"] else "MISMATCH"
        print(f"  slot {row['slot']} origin {row['origin']}: {status}")
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
