"""Canonical initial conditions for three-tape CMCA verifications."""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import numpy as np

from three_tape_cmca import GLIDER_CELLS, ThreeTapeCMCA, make_ether

PSC_WINDINGS = (0, 2, 3, 4, 6)


def ether_background(L: int) -> np.ndarray:
    return make_ether(L)


def _xor_glider(tape: np.ndarray, center: int, cells: Tuple[int, ...] = GLIDER_CELLS) -> None:
    L = len(tape)
    for xp in cells:
        tape[(center + xp - 128) % L] ^= 1


def ic_vacuum(cmca: ThreeTapeCMCA) -> None:
    cmca.reset()


def ic_glider_x(cmca: ThreeTapeCMCA, position: Optional[int] = None) -> None:
    """Glider on tape_x: ether background with localized XOR on outer_plus and inner_clock."""
    cmca.reset()
    if position is None:
        position = cmca.center
    _xor_glider(cmca.outer_plus_x, position)
    _xor_glider(cmca.inner_clock_x, position)


def ic_glider_r124(cmca: ThreeTapeCMCA, position: Optional[int] = None) -> None:
    """Left-chiral glider on outer_minus_x."""
    cmca.reset()
    if position is None:
        position = cmca.center
    _xor_glider(cmca.outer_minus_x, position)
    _xor_glider(cmca.inner_clock_x, position)


def sm_uniform_triple(L: int, w: int) -> Dict[str, np.ndarray]:
    """Uniform winding w on all three outer_plus tapes."""
    ether = make_ether(L)
    bit = 1 if (w // 2) % 2 else 0
    tape = ether.copy()
    if w % 2 == 1 or w in (1, 3, 5):
        tape ^= 1
    if w in (2, 4, 6):
        for i in range(0, L, 14):
            tape[i] ^= 1
    return {
        "outer_plus_x": tape.copy(),
        "outer_plus_y": tape.copy(),
        "outer_plus_z": tape.copy(),
        "outer_minus_x": ether.copy(),
        "outer_minus_y": ether.copy(),
        "outer_minus_z": ether.copy(),
        "inner_clock_x": ether.copy(),
        "inner_clock_y": ether.copy(),
        "inner_clock_z": ether.copy(),
    }


def apply_sm_uniform(cmca: ThreeTapeCMCA, w: int) -> None:
    cmca.reset()
    ether = cmca.ether
    op = ether.copy()
    for p in range(cmca.L):
        target_w = ((int(op[p] ^ ether[p]) * 2) % 7)
        if target_w != w:
            op[p] ^= 1
    for j in "xyz":
        setattr(cmca, f"outer_plus_{j}", op.copy())


def ic_sm_particles(cmca: ThreeTapeCMCA) -> Dict[int, str]:
    """Map PSC windings to uniform-triple labels."""
    cmca.reset()
    return {w: f"uniform_triple_{w}" for w in PSC_WINDINGS}


def ic_gravity_source(cmca: ThreeTapeCMCA) -> np.ndarray:
    cmca.reset()
    cmca.setup_gravity_source()
    return cmca.gravity_potential()


def compact_z7_source(
    cmca: ThreeTapeCMCA,
    y_offset: int = 5,
    z_offset: int = -5,
) -> np.ndarray:
    cmca.reset()
    cmca.setup_gravity_source(y_offset=y_offset, z_offset=z_offset)
    return cmca.gravity_potential()


def ic_proton_triple(cmca: ThreeTapeCMCA) -> None:
    """(2,2,6) proton content at center — u,u,d windings per tape."""
    cmca.reset()
    center = cmca.center
    for j, w in zip("xyz", (2, 2, 6)):
        op = cmca.ether.copy()
        for xp in GLIDER_CELLS:
            if w in (2, 6):
                op[(center + xp - 128) % cmca.L] ^= 1
        setattr(cmca, f"outer_plus_{j}", op)


def ic_soliton(cmca: ThreeTapeCMCA, p_ic: int = 120, p_op: int = 134) -> None:
    """Ether-period resonance IC at lattice indices p_ic, p_op (P45 canonical)."""
    cmca.reset()
    cmca.inner_clock_x[p_ic % cmca.L] ^= 1
    cmca.outer_plus_x[p_op % cmca.L] ^= 1


def sm_vertex_table() -> List[Tuple[str, int, int, int]]:
    """
    33 SM charged-current vertices: (label, w_in, w_a, w_b) with w_in ≡ w_a + w_b (mod 7).
    """
    raw: List[Tuple[str, int, int]] = []
    for wu in (2, 6):
        for ww in (3, 4):
            raw.append((f"quark_W_{wu}_{ww}", wu, ww))
    for wl in (3, 4):
        raw.append((f"lepton_W_{wl}", wl, 4))
    for w in (2, 3, 4, 6):
        raw.append((f"Z_{w}", w, 0))
    for g1 in (0, 2, 3, 4, 6):
        for g2 in (0, 2, 3, 4, 6):
            if g1 == 0 and g2 == 0:
                continue
            raw.append((f"gluon_{g1}_{g2}", g1, g2))
    for w in (0, 2, 3, 4, 6):
        raw.append((f"photon_{w}", w, (7 - w) % 7))
    raw.append(("Higgs_1", 3, 4))
    raw.append(("Higgs_2", 4, 3))
    for w1 in (1, 5):
        for w2 in (2, 3, 4, 6):
            raw.append((f"anti_{w1}_{w2}", w1, w2))

    seen: set = set()
    vertices: List[Tuple[str, int, int, int]] = []
    for label, wa, wb in raw:
        wi = (wa + wb) % 7
        key = (wi, wa, wb)
        if key in seen:
            continue
        seen.add(key)
        vertices.append((label, wi, wa, wb))
    return vertices[:33]
