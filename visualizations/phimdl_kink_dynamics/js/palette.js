// Seven distinguishable hues for the seven vacua Phi_k = 2*pi*k/7.

export const VACUUM_COLORS = [
  [78, 121, 167],   // k=0  blue
  [89, 161, 79],    // k=1  green
  [242, 142, 43],   // k=2  orange
  [225, 87, 89],    // k=3  red
  [176, 122, 161],  // k=4  purple
  [237, 201, 72],   // k=5  yellow
  [118, 183, 178],  // k=6  teal
];

export const VACUUM_CSS = VACUUM_COLORS.map(c => `rgb(${c[0]},${c[1]},${c[2]})`);

const TWO_PI = 2 * Math.PI;

// Vacuum index k = round(7*Phi/2pi) mod 7 (non-negative).
export function vacuumIndex(phi) {
  const k = Math.round((7 * phi) / TWO_PI) % 7;
  return k < 0 ? k + 7 : k;
}
