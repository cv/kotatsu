// The FEA heat maps' colour scale, shared by the 3-D view (web/fea3d.js) and the Frame parts tab (web/app.js).
// No three.js here, so the 2-D tab doesn't pull it in.
// share of strength (Tsai-Hill) -> colour: blue (idle) .. yellow (half) .. red (all of it) .. purple (past it)
const STOPS = [[0, [44, 123, 182]], [0.25, [120, 190, 220]], [0.5, [250, 240, 160]], [0.75, [253, 160, 80]],
  [1.0, [215, 25, 28]], [1.5, [110, 10, 120]]];
export const LOCAL = [150, 150, 150]; // right at a pad or contact: bearing peaks, not bending (see the legend)

export function heat(u) {
  if (!(u > 0)) u = 0;
  for (let i = 1; i < STOPS.length; i++) {
    const [b, cb] = STOPS[i], [a, ca] = STOPS[i - 1];
    if (u <= b) { const f = (u - a) / (b - a); return ca.map((c, j) => (c + (cb[j] - c) * f) / 255); }
  }
  return STOPS[STOPS.length - 1][1].map((c) => c / 255);
}

export const GRADIENT = `linear-gradient(to right, ${STOPS.map(([u, c]) => `rgb(${c}) ${(u / 1.5) * 100}%`).join(", ")})`;

