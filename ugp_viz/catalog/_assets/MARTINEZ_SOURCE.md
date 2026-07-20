# Martinez Rule 110 Phase Catalog — Source

`listPhasesR110.txt` is a verbatim mirror of Genaro J. Martinez's
public glider-phase catalog for Rule 110:

> Genaro J. Martinez, *Phases fi_1 for gliders in Rule 110*,
> ESCOM-IPN (Mexico), September 2001 / updated September 2004.
> <http://comunidad.escom.ipn.mx/genaro/rule110/listPhasesR110.txt>

It lists the bit patterns of every periodic glider phase (ether, A, B,
B-, B^, C1, C2, C3, D1, D2, E, E-, F, G, H, Gun) for the family that
underpins Cook's 2004 universality construction. We use it as the
authoritative ingestion source for VIZLAB's Rule 110 catalog (matches
the corresponding ingestion in `rule110-lean`'s
`Rule110.MartinezPhasesCatalog`).

The companion Cook reference data (named gliders, indexed families
`Bbar`/`Bhat`/`En`/`Gn`, periods, ω-coefficients) is taken from:

> Matthew Cook, *Universality in Elementary Cellular Automata*,
> Complex Systems **15**(1) (2004), Figure 5,
> <https://content.wolfram.com/sites/13/2018/02/15-1-1.pdf>

VIZLAB packs Martinez phases into JSON catalog entries via
`ugp_viz/catalog/build_r110_catalog.py`. Re-run that script if the
upstream text file is updated.
