#!/usr/bin/env python3
"""
nubase_stability_lookup.py
==========================
Empirical nuclear stability lookup for Z=1-118, from NUBASE2020.

Categories:
  'stable'     — element has ≥1 truly stable isotope (infinite half-life in NUBASE2020)
  'primordial' — no stable isotopes, but ≥1 isotope with half-life > 1 Gy;
                 effectively stable on human/geological timescales
  'long_lived' — no stable/primordial isotopes, but ≥1 isotope with t½ > 1 My
  'radioactive' — no stable isotopes; longest-lived t½ < 1 My

Note on Bi (Z=83): Bi-209 has t½ = 2.0×10¹⁹ y (alpha decay). Historically treated
as stable, now known radioactive but effectively primordial.

Note on Tc (Z=43) and Pm (Z=61): the ONLY two elements below Bi with NO stable
and NO primordial isotopes. Their longest-lived isotopes are Tc-97 (4.21 My)
and Pm-145 (17.7 y). Both are in the 'long_lived' or 'radioactive' category
depending on threshold, but neither has anything close to stable isotopes.

Sources: NUBASE2020 (Kondev et al., Chinese Physics C 45, 030001, 2021)
         Wikipedia List of elements by stability of isotopes (cross-checked)
"""

from typing import Dict

# ── Stability categories ────────────────────────────────────────────────────────
STABLE     = 'stable'
PRIMORDIAL = 'primordial'   # radioactive but >> age of universe
LONG_LIVED = 'long_lived'   # radioactive, longest t½ > 1 My but < 1 Gy
RADIOACTIVE = 'radioactive'  # longest known t½ < 1 My

# ── Empirical stability by element (Z=1 to Z=118) ─────────────────────────────
# Based on NUBASE2020. Every entry is verified against the known nuclear chart.
NUBASE_STABILITY: Dict[int, str] = {
    # Period 1
    1:  STABLE,      # H  — H-1 and H-2 stable; H-3 (tritium) 12.3y
    2:  STABLE,      # He — He-3, He-4 stable

    # Period 2
    3:  STABLE,      # Li — Li-6, Li-7 stable
    4:  STABLE,      # Be — Be-9 stable (Be-10 has t½=1.39My but Be-9 is stable)
    5:  STABLE,      # B  — B-10, B-11 stable
    6:  STABLE,      # C  — C-12, C-13 stable
    7:  STABLE,      # N  — N-14, N-15 stable
    8:  STABLE,      # O  — O-16, O-17, O-18 stable
    9:  STABLE,      # F  — F-19 only stable (monoisotopic)
    10: STABLE,      # Ne — Ne-20, Ne-21, Ne-22 stable

    # Period 3
    11: STABLE,      # Na — Na-23 stable (monoisotopic)
    12: STABLE,      # Mg — Mg-24, Mg-25, Mg-26 stable
    13: STABLE,      # Al — Al-27 stable (monoisotopic)
    14: STABLE,      # Si — Si-28, Si-29, Si-30 stable
    15: STABLE,      # P  — P-31 stable (monoisotopic)
    16: STABLE,      # S  — S-32, S-33, S-34, S-36 stable
    17: STABLE,      # Cl — Cl-35, Cl-37 stable
    18: STABLE,      # Ar — Ar-36, Ar-38, Ar-40 stable

    # Period 4
    19: STABLE,      # K  — K-39, K-41 stable; K-40 radioactive (t½=1.25Gy) but K is stable
    20: STABLE,      # Ca — Ca-40,42,43,44,46,48 stable
    21: STABLE,      # Sc — Sc-45 stable (monoisotopic)
    22: STABLE,      # Ti — Ti-46,47,48,49,50 stable
    23: STABLE,      # V  — V-51 stable; V-50 very weakly radioactive (t½=1.4×10¹⁷y) but V-51 is stable
    24: STABLE,      # Cr — Cr-50,52,53,54 stable
    25: STABLE,      # Mn — Mn-55 stable (monoisotopic)
    26: STABLE,      # Fe — Fe-54,56,57,58 stable
    27: STABLE,      # Co — Co-59 stable (monoisotopic)
    28: STABLE,      # Ni — Ni-58,60,61,62,64 stable
    29: STABLE,      # Cu — Cu-63, Cu-65 stable
    30: STABLE,      # Zn — Zn-64,66,67,68,70 stable
    31: STABLE,      # Ga — Ga-69, Ga-71 stable
    32: STABLE,      # Ge — Ge-70,72,73,74,76 stable
    33: STABLE,      # As — As-75 stable (monoisotopic)
    34: STABLE,      # Se — Se-74,76,77,78,80,82 stable
    35: STABLE,      # Br — Br-79, Br-81 stable
    36: STABLE,      # Kr — Kr-78,80,82,83,84,86 stable

    # Period 5
    37: STABLE,      # Rb — Rb-85 stable; Rb-87 radioactive (t½=49Gy) but Rb-85 is stable
    38: STABLE,      # Sr — Sr-84,86,87,88 stable
    39: STABLE,      # Y  — Y-89 stable (monoisotopic)
    40: STABLE,      # Zr — Zr-90,91,92,94,96 stable
    41: STABLE,      # Nb — Nb-93 stable (monoisotopic)
    42: STABLE,      # Mo — Mo-92,94,95,96,97,98,100 stable
    43: LONG_LIVED,  # Tc — NO stable isotopes; Tc-97 t½=4.21My, Tc-98 t½=4.2My, Tc-99 t½=211ky
    44: STABLE,      # Ru — Ru-96,98,99,100,101,102,104 stable
    45: STABLE,      # Rh — Rh-103 stable (monoisotopic)
    46: STABLE,      # Pd — Pd-102,104,105,106,108,110 stable
    47: STABLE,      # Ag — Ag-107, Ag-109 stable
    48: STABLE,      # Cd — Cd-106,108,110,111,112,113,114,116 stable
    49: STABLE,      # In — In-113 stable; In-115 radioactive (t½=4.4×10¹⁴y) but In-113 stable
    50: STABLE,      # Sn — 10 stable isotopes (most of any element)
    51: STABLE,      # Sb — Sb-121, Sb-123 stable
    52: STABLE,      # Te — Te-120,122,123,124,125,126,128,130 stable (Te-128 very weakly α)
    53: STABLE,      # I  — I-127 stable (monoisotopic)
    54: STABLE,      # Xe — Xe-124,126,128,129,130,131,132,134,136 stable

    # Period 6
    55: STABLE,      # Cs — Cs-133 stable (monoisotopic)
    56: STABLE,      # Ba — Ba-130,132,134,135,136,137,138 stable
    57: STABLE,      # La — La-139 stable; La-138 radioactive (t½=1.05×10¹¹y) but La-139 stable
    58: STABLE,      # Ce — Ce-136,138,140,142 stable
    59: STABLE,      # Pr — Pr-141 stable (monoisotopic)
    60: STABLE,      # Nd — Nd-142,143,144,145,146,148,150 stable
    61: RADIOACTIVE, # Pm — NO stable isotopes; longest-lived Pm-145 t½=17.7y (<<1 My)
    62: STABLE,      # Sm — Sm-144,149,150,152,154 stable; Sm-147,148 α-radioactive but others stable
    63: STABLE,      # Eu — Eu-151, Eu-153 stable
    64: STABLE,      # Gd — Gd-154,155,156,157,158,160 stable
    65: STABLE,      # Tb — Tb-159 stable (monoisotopic)
    66: STABLE,      # Dy — Dy-156,158,160,161,162,163,164 stable
    67: STABLE,      # Ho — Ho-165 stable (monoisotopic)
    68: STABLE,      # Er — Er-162,164,166,167,168,170 stable
    69: STABLE,      # Tm — Tm-169 stable (monoisotopic)
    70: STABLE,      # Yb — Yb-168,170,171,172,173,174,176 stable
    71: STABLE,      # Lu — Lu-175 stable; Lu-176 radioactive (t½=3.76×10¹⁰y) but Lu-175 stable
    72: STABLE,      # Hf — Hf-174,176,177,178,179,180 stable
    73: STABLE,      # Ta — Ta-181 stable; Ta-180m is isomer, long-lived but Ta-181 stable
    74: STABLE,      # W  — W-180,182,183,184,186 stable
    75: STABLE,      # Re — Re-185 stable; Re-187 radioactive (t½=4.12×10¹⁰y) but Re-185 stable
    76: STABLE,      # Os — Os-184,186,187,188,189,190,192 stable
    77: STABLE,      # Ir — Ir-191, Ir-193 stable
    78: STABLE,      # Pt — Pt-190,192,194,195,196,198 stable
    79: STABLE,      # Au — Au-197 stable (monoisotopic)
    80: STABLE,      # Hg — Hg-196,198,199,200,201,202,204 stable
    81: STABLE,      # Tl — Tl-203, Tl-205 stable
    82: STABLE,      # Pb — Pb-204,206,207,208 stable (heaviest with stable isotopes)
    83: PRIMORDIAL,  # Bi — Bi-209 only; t½=2.0×10¹⁹y (α decay measured 2003). Effectively stable.
    84: RADIOACTIVE, # Po — longest-lived Po-209 t½=124y
    85: RADIOACTIVE, # At — longest-lived At-210 t½=8.1h
    86: RADIOACTIVE, # Rn — longest-lived Rn-222 t½=3.82d; Rn-222 most common
    87: RADIOACTIVE, # Fr — longest-lived Fr-223 t½=22min
    88: RADIOACTIVE, # Ra — longest-lived Ra-226 t½=1600y
    89: RADIOACTIVE, # Ac — longest-lived Ac-227 t½=21.8y
    90: PRIMORDIAL,  # Th — Th-232 t½=14.05Gy (primordial, 3× age of Earth)
    91: RADIOACTIVE, # Pa — longest-lived Pa-231 t½=32760y
    92: PRIMORDIAL,  # U  — U-238 t½=4.47Gy, U-235 t½=703My (both primordial)
    93: LONG_LIVED,  # Np — longest-lived Np-237 t½=2.14My (>1 My threshold)
    94: LONG_LIVED,  # Pu — longest-lived Pu-244 t½=80.8My (>1 My threshold)
    95: RADIOACTIVE, # Am — longest-lived Am-243 t½=7370y
    96: LONG_LIVED,  # Cm — longest-lived Cm-247 t½=15.6My (>1 My threshold)
    97: RADIOACTIVE, # Bk — longest-lived Bk-247 t½=1380y
    98: RADIOACTIVE, # Cf — longest-lived Cf-251 t½=898y
    99: RADIOACTIVE, # Es — longest-lived Es-252 t½=471.7d
    100: RADIOACTIVE,# Fm — longest-lived Fm-257 t½=100.5d
    101: RADIOACTIVE,# Md — longest-lived Md-258 t½=51.5d
    102: RADIOACTIVE,# No — longest-lived No-259 t½=58min
    103: RADIOACTIVE,# Lr — longest-lived Lr-266 t½=11h
    104: RADIOACTIVE,# Rf — longest-lived Rf-267 t½=1.3h
    105: RADIOACTIVE,# Db — longest-lived Db-268 t½=16h
    106: RADIOACTIVE,# Sg — longest-lived Sg-269 t½=14min
    107: RADIOACTIVE,# Bh — longest-lived Bh-270 t½=61s
    108: RADIOACTIVE,# Hs — longest-lived Hs-277 t½=~11min
    109: RADIOACTIVE,# Mt — longest-lived Mt-278 t½=~8s
    110: RADIOACTIVE,# Ds — longest-lived Ds-281 t½=~14s
    111: RADIOACTIVE,# Rg — longest-lived Rg-282 t½=~2min
    112: RADIOACTIVE,# Cn — longest-lived Cn-285 t½=~30s
    113: RADIOACTIVE,# Nh — longest-lived Nh-284 t½=~1min
    114: RADIOACTIVE,# Fl — longest-lived Fl-289 t½=~1.9s
    115: RADIOACTIVE,# Mc — longest-lived Mc-289 t½=~220ms
    116: RADIOACTIVE,# Lv — longest-lived Lv-293 t½=~60ms
    117: RADIOACTIVE,# Ts — longest-lived Ts-294 t½=~51ms
    118: RADIOACTIVE,# Og — longest-lived Og-294 t½=~0.7ms
}

# ── Elements with no stable isotopes (Z=1-118) ────────────────────────────────
NO_STABLE_ISOTOPES = {Z for Z, cat in NUBASE_STABILITY.items()
                      if cat != STABLE}

# ── Color mapping for visualization ───────────────────────────────────────────
STABILITY_COLORS = {
    STABLE:     '#2ecc71',   # green
    PRIMORDIAL: '#f39c12',   # amber/gold — Bi, Th, U
    LONG_LIVED: '#e67e22',   # orange — Tc, Pm
    RADIOACTIVE: '#e74c3c',  # red
    'predicted_stable':   '#c0392b',  # dark red (Z>118 GTE-predicted stable)
    'predicted_unstable': '#7f8c8d',  # grey (Z>118 GTE-predicted unstable)
}

STABILITY_LABELS = {
    STABLE:     'Stable',
    PRIMORDIAL: 'Primordial\n(effectively stable)',
    LONG_LIVED: 'No stable isotopes\n(radioactive)',
    RADIOACTIVE: 'Radioactive\n(all isotopes)',
    'predicted_stable':   'Predicted stable\n(GTE, Category D)',
    'predicted_unstable': 'Predicted unstable\n(GTE, Category D)',
}


def get_stability(Z: int) -> str:
    """Return the empirical stability category for element Z.
    For Z > 118, raises ValueError — use GTE model predictions instead.
    """
    if Z < 1:
        raise ValueError(f"Z must be ≥ 1, got {Z}")
    if Z > 118:
        raise ValueError(f"Z={Z} > 118: use GTE model prediction, not empirical lookup")
    return NUBASE_STABILITY[Z]


def get_color(Z: int, gte_prediction: str = None) -> str:
    """Return the display color for element Z.
    For Z ≤ 118: uses empirical stability.
    For Z > 118: uses gte_prediction ('stable' or 'unstable').
    """
    if Z <= 118:
        cat = NUBASE_STABILITY[Z]
        return STABILITY_COLORS[cat]
    else:
        if gte_prediction == 'stable':
            return STABILITY_COLORS['predicted_stable']
        else:
            return STABILITY_COLORS['predicted_unstable']


# ── Validation ─────────────────────────────────────────────────────────────────
def validate():
    """Validate the lookup table against known facts."""
    assert len(NUBASE_STABILITY) == 118, f"Expected 118 entries, got {len(NUBASE_STABILITY)}"

    # Known stable elements
    assert NUBASE_STABILITY[26] == STABLE,  "Fe should be stable"
    assert NUBASE_STABILITY[82] == STABLE,  "Pb should be stable (heaviest with stable isotopes)"
    assert NUBASE_STABILITY[1]  == STABLE,  "H should be stable"

    # Known problem cases
    assert NUBASE_STABILITY[43] != STABLE,  "Tc should NOT be stable"
    assert NUBASE_STABILITY[61] != STABLE,  "Pm should NOT be stable"
    assert NUBASE_STABILITY[83] == PRIMORDIAL, "Bi should be primordial"
    assert NUBASE_STABILITY[84] == RADIOACTIVE, "Po should be radioactive"
    assert NUBASE_STABILITY[90] == PRIMORDIAL,  "Th should be primordial (Th-232, 14 Gy)"
    assert NUBASE_STABILITY[92] == PRIMORDIAL,  "U should be primordial (U-238, 4.47 Gy)"
    assert NUBASE_STABILITY[118] == RADIOACTIVE, "Og should be radioactive (t½=0.7ms)"

    # Check no gaps
    for Z in range(1, 119):
        assert Z in NUBASE_STABILITY, f"Z={Z} missing from lookup"

    # Count categories
    from collections import Counter
    counts = Counter(NUBASE_STABILITY.values())
    print("NUBASE stability validation passed:")
    for cat, n in sorted(counts.items()):
        print(f"  {cat}: {n} elements")
    print(f"  No stable isotopes: {sorted(NO_STABLE_ISOTOPES)}")
    print(f"  Total: {sum(counts.values())} elements")


if __name__ == '__main__':
    validate()
