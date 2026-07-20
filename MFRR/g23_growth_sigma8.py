#!/usr/bin/env python3
"""
E7 (MFRR table): linear structure growth / fσ8(z) validation.

The monograph lists this filename in `tab:computational-artifacts-1`. The full
implementation and figure output live in `e15_growth.py` (writes
`e15_growth_outputs/`). This module is the **canonical entrypoint name**—it
delegates to that implementation without duplicating numerics.

See also: `Mathematical_Foundations_of_Reflexive_Reality.tex` (E7 row).
"""

from __future__ import annotations

import runpy
from pathlib import Path

_IMPL = Path(__file__).resolve().parent / "e15_growth.py"


def main() -> None:
    runpy.run_path(str(_IMPL), run_name="__main__")


if __name__ == "__main__":
    main()
