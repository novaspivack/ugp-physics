#!/usr/bin/env python3
"""
Clean reordering of appendices in MFRR manuscript.
Fixes: C/D swap, duplicate P, starred sections, proper wrapping.
"""

def reorder_appendices(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Find key line numbers
    appendix_start = None
    d_input_line = None
    proof_sketches_start = None
    proof_sketches_end = None
    h_start = None
    i_input_line = None
    l_start = None
    m_start = None
    n_start = None
    p_start = None
    p_end = None
    u_start = None
    bib_line = None
    
    for i, line in enumerate(lines):
        if '\\appendix' in line and appendix_start is None:
            appendix_start = i
        elif '\\input{APPENDIX_D_STATISTICAL_MECHANICS_RLB}' in line:
            d_input_line = i
        elif line.strip() == '\\section{Proof Sketches and Technical Lemmas}':
            proof_sketches_start = i
        elif proof_sketches_start and line.strip().startswith('\\section{') and 'Minimal Reflexive Loop' in line:
            proof_sketches_end = i - 1
            h_start = i
        elif '\\input{APPENDIX_I_PR0_SUMMARY}' in line:
            i_input_line = i
        elif '\\section*{Appendix L:' in line:
            l_start = i
        elif '\\section*{Appendix M:' in line:
            m_start = i
        elif '\\section*{Appendix N:' in line:
            n_start = i
        elif '\\section*{Appendix P: Proofs and Technical Lemmas}' in line:
            p_start = i
        elif '\\section*{Appendix U:' in line:
            if p_start and not p_end:
                p_end = i - 1
            u_start = i
        elif '\\bibliography{references}' in line:
            bib_line = i
    
    print(f"Found structure:")
    print(f"  Appendix command: line {appendix_start}")
    print(f"  D input: line {d_input_line}")
    print(f"  Proof Sketches (C): lines {proof_sketches_start}-{proof_sketches_end}")
    print(f"  H (Toy Model): line {h_start}")
    print(f"  I input: line {i_input_line}")
    print(f"  L (starred): line {l_start}")
    print(f"  M (starred): line {m_start}")
    print(f"  N (starred): line {n_start}")
    print(f"  P (duplicate): lines {p_start}-{p_end}")
    print(f"  U (starred): line {u_start}")
    print(f"  Bibliography: line {bib_line}")
    
    # Build new structure
    result = []
    
    # Everything up to D input (but not including it)
    result.extend(lines[:d_input_line])
    
    # Insert Proof Sketches (C) BEFORE D
    result.extend(lines[proof_sketches_start:proof_sketches_end+1])
    result.append('\n')
    
    # Now D input
    result.append(lines[d_input_line])
    result.append('\n')
    
    # Everything from after Proof Sketches end to before H start (skip the moved block)
    # This skips lines that were moved
    
    # H section (already correct format)
    result.extend(lines[h_start:i_input_line])
    
    # I - wrap the input
    result.append('\\section{PR-0 Summary and Validation}\n')
    result.append('\\label{app:pr0-summary}\n')
    result.append(lines[i_input_line])
    result.append('\n')
    
    # L - convert from starred to normal
    for i in range(l_start, m_start):
        line = lines[i]
        line = line.replace('\\section*{Appendix L: Elliptic Solver', '\\section{Elliptic Solver')
        result.append(line)
    
    # M - convert from starred to normal
    for i in range(m_start, n_start):
        line = lines[i]
        line = line.replace('\\section*{Appendix M: Reflexive Fluctuation', '\\section{Reflexive Fluctuation')
        result.append(line)
    
    # N - convert from starred to normal
    for i in range(n_start, p_start):
        line = lines[i]
        line = line.replace('\\section*{Appendix N: Analytic Correspondence', '\\section{Analytic Correspondence')
        result.append(line)
    
    # Skip P entirely (duplicate, will merge into C later if needed)
    
    # U - convert from starred to normal
    for i in range(u_start, bib_line):
        line = lines[i]
        line = line.replace('\\section*{Appendix U: Units and Normalization', '\\section{Units and Normalization')
        result.append(line)
    
    # Bibliography and end
    result.extend(lines[bib_line:])
    
    # Write output
    with open(output_file, 'w', encoding='utf-8') as f:
        f.writelines(result)
    
    print(f"\n✅ Wrote reorganized file to {output_file}")
    print(f"   Total lines: {len(result)}")

if __name__ == '__main__':
    reorder_appendices(
        'The_Mathematical_Foundations_of_Reflexive_Reality.tex',
        'The_Mathematical_Foundations_of_Reflexive_Reality_REORDERED.tex'
    )

