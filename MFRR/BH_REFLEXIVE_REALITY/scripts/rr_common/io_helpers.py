#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
I/O helpers for BH computational tests.

Reference: MFRR Paper, Appendix: Computational Tests for Black Holes
Date: November 4, 2025
"""

import csv
from pathlib import Path

def write_csv(path, header, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        for r in rows:
            w.writerow(r)

