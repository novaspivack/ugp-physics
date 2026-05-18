# MFRR first-party Python module count (`CLM-A-004`)

**Purpose:** Define what “code modules” means in the monograph abstract relative to a naive recursive `*.py` scan of the whole drive (which would include enormous dependency trees).

**Definition (2026-04-27):** Count of files ending in `.py` under the MFRR tree in this repository (`MFRR/` at the `ugp-physics` root), with `find` **pruning** directories named `__pycache__`, `.venv`, `venv`, or `site-packages`.

**Reproduce:**

```bash
cd MFRR
find . \( -name '__pycache__' -o -name '.venv' -o -name 'venv' -o -name 'site-packages' \) -prune -o -name '*.py' -print | wc -l
```

**Result:** **297** (same session as inventory file creation).

**Note:** Replacing earlier informal “276 modules” — the pinned count is **297** under this definition. If the definition changes, update this file and the abstract in lockstep.
