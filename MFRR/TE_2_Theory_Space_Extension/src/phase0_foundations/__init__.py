"""Phase 0: Foundations - T_PSC definition and equivalence relation."""

from .theory_space_definition import (
    TheoryParams,
    TheorySpace,
    GaugeGroup,
    GaugeGroupType,
    Representation,
    MatterField,
    GAUGE_GROUPS_CATALOG,
    SM_MATTER_CONTENT,
    create_standard_model_theory,
    enumerate_gauge_groups,
)

from .physical_equivalence import (
    EquivalenceType,
    EquivalenceTransformation,
    PhysicalEquivalenceChecker,
    QuotientTheorySpace,
    are_gauge_isomorphic,
)

from .psc_admissibility import (
    PSCAdmissibilityChecker,
    ConstraintResult,
    GaugeStructureConstraint,
    EFTLocalityConstraint,
    ConsistencyConstraint,
    PSCClosureConstraint,
    SRRGRegularityConstraint,
)

__all__ = [
    'TheoryParams',
    'TheorySpace',
    'GaugeGroup',
    'create_standard_model_theory',
    'PhysicalEquivalenceChecker',
    'QuotientTheorySpace',
    'PSCAdmissibilityChecker',
]
