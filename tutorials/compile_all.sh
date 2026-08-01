#!/bin/bash
# Compile all tutorials twice and collect results
BASE="/Users/nova/ugp-physics/tutorials"
LATEX="pdflatex -interaction=nonstopmode"

TUTORIALS="
polynomial_cheatsheet/polynomial_cheatsheet.tex
uwca_tutorial/uwca_tutorial.tex
ugp_gte_masses/ugp_gte_masses_tutorial.tex
psc_mdl/psc_mdl_tutorial.tex
mdl_selection/mdl_selection_tutorial.tex
phimdl_field/phimdl_field_tutorial.tex
quantum_numbers/quantum_numbers_tutorial.tex
strong_cp/strong_cp_tutorial.tex
weinberg_angle/weinberg_angle_tutorial.tex
gravity/gravity_tutorial.tex
born_rule/born_rule_tutorial.tex
cosmological_constant/cc_tutorial.tex
defect_cosmology/defect_cosmology_tutorial.tex
transputation/transputation_tutorial.tex
three_tape_cmca/three_tape_cmca_tutorial.tex
levels_of_theory/levels_tutorial.tex
universality_undecidability/universality_tutorial.tex
golden_quadratic/golden_quadratic_tutorial.tex
"

echo "=== COMPILE PASS 1 ==="
for texfile in $TUTORIALS; do
  dir=$(dirname "$texfile")
  fname=$(basename "$texfile")
  key=$(basename "$dir")
  echo -n "  $key ... "
  cd "$BASE/$dir"
  if $LATEX "$fname" > compile_pass1.log 2>&1; then
    echo "OK"
  else
    echo "ERRORS"
    grep -E "^!" compile_pass1.log | head -3
  fi
  cd "$BASE"
done

echo ""
echo "=== COMPILE PASS 2 (TOC update) ==="
for texfile in $TUTORIALS; do
  dir=$(dirname "$texfile")
  fname=$(basename "$texfile")
  key=$(basename "$dir")
  echo -n "  $key ... "
  cd "$BASE/$dir"
  if $LATEX "$fname" > compile_pass2.log 2>&1; then
    echo "OK"
  else
    echo "ERRORS"
    grep -E "^!" compile_pass2.log | head -3
  fi
  cd "$BASE"
done

echo ""
echo "=== OVERFULL REPORT ==="
for texfile in $TUTORIALS; do
  dir=$(dirname "$texfile")
  fname=$(basename "$texfile")
  key=$(basename "$dir")
  logfile="$BASE/$dir/${fname%.tex}.log"
  count=$(grep -c "Overfull .hbox" "$logfile" 2>/dev/null || echo 0)
  worst=""
  if [ "$count" -gt 0 ] 2>/dev/null; then
    worst=$(grep "Overfull .hbox" "$logfile" 2>/dev/null | \
      sed 's/.*(\([0-9.]*\)pt too wide).*/\1/' | \
      grep -v "Overfull" | sort -rn | head -1)
    echo "  $key: $count overfulls, worst=${worst}pt"
  else
    echo "  $key: clean"
  fi
done

echo ""
echo "=== PAGE COUNT ==="
for texfile in $TUTORIALS; do
  dir=$(dirname "$texfile")
  fname=$(basename "$texfile")
  key=$(basename "$dir")
  pdffile="$BASE/$dir/${fname%.tex}.pdf"
  if [ -f "$pdffile" ]; then
    pages=$(python3 -c "
import subprocess, re
r = subprocess.run(['pdfinfo', '$pdffile'], capture_output=True, text=True)
m = re.search(r'Pages:\s+(\d+)', r.stdout)
print(m.group(1) if m else '?')
" 2>/dev/null || echo "?")
    echo "  $key: $pages pages"
  fi
done
