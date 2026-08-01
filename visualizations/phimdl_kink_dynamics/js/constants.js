// Physical constants for the Z7 scalar kink field (natural units m = 1 internally).

export const M_PHI_MEV = 1776.86;                    // field mass scale (SCC)
export const HBARC_MEV_FM = 197.3269804;
export const LENGTH_UNIT_FM = HBARC_MEV_FM / M_PHI_MEV; // fm per unit of 1/m  (~0.11105)
export const TIME_UNIT_FM_C = LENGTH_UNIT_FM;           // fm/c per unit of 1/m
export const M_KINK_MEV = (8 / 49) * M_PHI_MEV;         // BPS kink mass, 290.10 MeV
export const STEP = (2 * Math.PI) / 7;                  // vacuum spacing 2*pi/7
export const N_VACUA = 7;

// SCC-parametrized unit conversions, used only by the "Explore: what if the
// SCC weren't satisfied?" panel. m_phi = m_tau = M_PHI_MEV is a DERIVED
// result (the Self-Consistency Condition, SCC), not a free parameter --
// these functions let the UI show, numerically, how the derived length/
// mass scale would change for a hypothetical departure from that value,
// without altering the constants above (which remain the actual derived
// SCC value used everywhere else in the app by default).
export function lengthUnitFmFor(mPhiMeV) { return HBARC_MEV_FM / mPhiMeV; }
export function kinkMassMevFor(mPhiMeV) { return (8 / 49) * mPhiMeV; }

// Winding sector -> particle identification (Z7 charge Q = w_c/3, w_c = w or w-7).
export const SECTORS = [
  { w: 0, name: 'vacuum',           charge: '0',    note: '' },
  { w: 1, name: 'dark sector',      charge: '—',    note: 'PSC-forbidden' },
  { w: 2, name: 'up-type quarks',   charge: '+2/3', note: '' },
  { w: 3, name: 'W+ / positron',    charge: '+1',   note: '' },
  { w: 4, name: 'charged leptons',  charge: '−1',   note: 'realized as 3 antikinks' },
  { w: 5, name: 'dark sector',      charge: '—',    note: 'PSC-forbidden' },
  { w: 6, name: 'down-type quarks', charge: '−1/3', note: '' },
];
