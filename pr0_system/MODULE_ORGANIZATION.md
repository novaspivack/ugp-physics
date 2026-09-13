# PR-0 System Module Organization

**Date**: October 31, 2025  
**Purpose**: Map old flat structure → new organized hierarchy  
**Companion Docs**: [PR0_SYSTEM_TECHNICAL_OVERVIEW.md](./PR0_SYSTEM_TECHNICAL_OVERVIEW.md), [PR0_SYSTEM_NOVELTY_AND_ARCHITECTURE.md](./PR0_SYSTEM_NOVELTY_AND_ARCHITECTURE.md)

---

## Directory Structure

```
pr0_system/
├── __init__.py
├── core/
│   ├── __init__.py
│   ├── lattice.py          ← NEW (square/hex lattice)
│   ├── fields.py           ← NEW (ψ, χ, history data structures)
│   └── update.py           ← NEW (reversible update operators)
│
├── evolution/
│   ├── __init__.py
│   ├── ablowitz_ladik.py   ← src/pr0_ablowitz_final.py
│   ├── mediator.py         ← EXTRACTED from ablowitz
│   └── damping.py          ← EXTRACTED from ablowitz
│
├── bootstrap/
│   ├── __init__.py
│   ├── dissonance.py       ← src/pr0_sds_dissonance_bootstrap.py
│   ├── meta_learn.py       ← shared annealing utilities
│   └── annealing.py        ← shared annealing utilities
│
├── forces/
│   ├── __init__.py
│   ├── strong.py           ← src/pr0_bootstrap_binding.py
│   ├── em.py               ← src/pr0_bootstrap_em_final.py
│   ├── weak.py             ← src/pr0_bootstrap_weak_final.py
│   └── gravity.py          ← src/pr0_bootstrap_gravity_simple.py
│
└── analysis/
    ├── __init__.py
    ├── diagnostics.py      ← NEW (energy, momentum, etc.)
    ├── clustering.py       ← NEW (soliton detection)
    └── visualization.py    ← EXTRACTED from various test files
```

---

## File Mapping (Old → New)

### Core Module

**NEW FILES** (to be created):
- `core/lattice.py` - Lattice/graph abstraction
- `core/fields.py` - Field data structures (ψ, χ, π)
- `core/update.py` - Base update operators

### Evolution Module

**FROM**: `src/pr0_ablowitz_final.py`
**TO**: 
- `evolution/ablowitz_ladik.py` - AL equation
- `evolution/mediator.py` - χ field evolution
- `evolution/damping.py` - Adaptive damping

### Bootstrap Module

**FROM**: `src/pr0_sds_dissonance_bootstrap.py`
**TO**:
- `bootstrap/dissonance.py` - D-operator
- `bootstrap/meta_learn.py` - Parameter evolution
- `bootstrap/annealing.py` - Simulated annealing

### Forces Module

**FROM**:
- `src/pr0_bootstrap_binding.py` → `forces/strong.py`
- `src/pr0_bootstrap_em_final.py` → `forces/em.py`
- `src/pr0_bootstrap_weak_final.py` → `forces/weak.py`
- `src/pr0_bootstrap_gravity_simple.py` → `forces/gravity.py`

### Analysis Module

**NEW FILES** (to be created from various sources):
- `analysis/diagnostics.py` - Energy, momentum, charge
- `analysis/clustering.py` - Soliton detection
- `analysis/visualization.py` - Plotting, animations

---

## Import Structure

### Old (flat):
```python
from pr0_ablowitz_final import AblowitzLadik
from pr0_sds_dissonance_bootstrap import compute_ontological_dissonance
from pr0_bootstrap_binding import BootstrapBinding
```

### New (organized):
```python
from pr0_system.evolution import AblowitzLadik
from pr0_system.bootstrap import compute_ontological_dissonance
from pr0_system.forces import BootstrapStrong
```

---

## Next Steps

1. ✅ Create directory structure
2. ⏳ Copy and refactor files into new structure
3. ⏳ Update imports and cross-references
4. ⏳ Create comprehensive __init__.py files
5. ⏳ Add tests for each module
6. ⏳ Create examples/ directory with usage examples
7. ⏳ Update documentation with new import paths

---

## Benefits

✅ **Clean separation of concerns**  
✅ **Easy to navigate and maintain**  
✅ **Professional package structure**  
✅ **Ready for PyPI distribution**  
✅ **Matches technical specification**  

---

**Status**: In Progress  
**Target Completion**: .10

