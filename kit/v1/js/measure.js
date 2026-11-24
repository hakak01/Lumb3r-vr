// Live measurements on the loaded (possibly changed) meshes, for the kit (docs/KIT.md). Work in model space
// (kit.root local); inputs/outputs to the kit user are file coordinates. Hidden structures are still measured.
import * as THREE from 'three';

const UPPER = { 'L3-4': 'L3', 'L4-5': 'L4', 'L5-S1': 'L5' }, LOWER = { 'L3-4': 'L4', 'L4-5': 'L5', 'L5-S1': 'S1' };
const mm = (x) => Math.round(x * 1e4) / 10;   // metres -> mm, 0.1 mm

export class Measure {
  constructor(kit) { this.kit = kit; this.S = kit.spine; }

  // Canal at mid-disc: midsagittal AP (back of disc/PLL to the first posterior wall) + dural sac cut in the disc plane.
  canal(d) {
    const S = this.S, F = S.discFrame(d), K = this.kit; if (!F) return null;
    S.disc[d] = F; const c = S.canalCentre(d); if (!c) return null;
    const sac = this._section(K.get('Dural sac'), c.c, F.n, F.l, F.a);
    return { canal_ap_mm: mm(c.ap), front: K._f(c.front), back: K._f(c.back),
      sac_area_mm2: sac && sac.area_mm2, sac_width_mm: sac && sac.width_mm, sac_ap_mm: sac && sac.ap_mm };
  }

  // Foramen at its Phase A centre (assets/model.json): height = rays up/down along the disc axis to the bone of the
  // upper/lower vertebra; width = rays forward to disc/vertebral body and back to the posterior elements
  // (soft = true also stops at flavum, facet cartilage and capsule).
  foramen(d, side, soft = false) {
    const S = this.S, K = this.kit, F = S.discFrame(d), fc = S.foramenCentre(d, side); if (!F || !fc) return null;
    const bone = (v, test) => K.where({ level: v, layer: 'bone' }).filter(test);
    const any = () => true, body = (s) => s.part === 'body', post = (s) => s.part !== 'body';
    const first = (dir, list) => { const h = S.cast(fc.c, dir, list, 0.04); return h.length ? h[0].d : NaN; };
    const neg = (v) => v.clone().negate();
    const up = first(F.n, bone(UPPER[d], any)), down = first(neg(F.n), bone(LOWER[d], any));
    const front = first(F.a, [...bone(UPPER[d], body), ...bone(LOWER[d], body), ...K.where({ level: d, layer: 'disc' })]);
    const backList = [...bone(UPPER[d], post), ...bone(LOWER[d], post)];
    if (soft) backList.push(...K.where({ level: d, side, name: /flavum|facet|capsule/i }));
    const back = first(neg(F.a), backList);
    return { height_mm: mm(up + down), width_mm: mm(front + back), up_mm: mm(up), down_mm: mm(down),
      front_mm: mm(front), back_mm: mm(back), centre: K._f(fc.c), soft };
  }

  // Area (mm²) of a structure's cut by the plane through point (file coords) with the given normal.
  section(s, point, normal) {
    const n = normal.clone().normalize(), u = new THREE.Vector3(1, 0, 0).cross(n);
    if (u.lengthSq() < 1e-6) u.set(0, 1, 0).cross(n);
    u.normalize(); return s ? this._section(s, this.kit._m(point), n, u, n.clone().cross(u)) : null;
  }

  // Loops of the plane cut; returns the largest loop that contains p (else the largest), with its size along u and v.
  _section(s, p, n, u, v) {
    if (!s) return null;
    const W = this.S.toModel, M = new THREE.Matrix4(), q = new THREE.Vector3(), loops = [], adj = new Map(), pt = new Map();
    const link = (x, y) => { if (!adj.has(x)) adj.set(x, []); adj.get(x).push(y); };
    for (const m of s.meshes) {   // cut points keyed by position (1 µm), so split vertices (seams) still join
      M.multiplyMatrices(W, m.matrixWorld);
      const pos = m.geometry.attributes.position, idx = m.geometry.index, N = pos.count;
      const P = new Float64Array(N * 3), D = new Float64Array(N);
      for (let i = 0; i < N; i++) { q.fromBufferAttribute(pos, i).applyMatrix4(M); P[3 * i] = q.x; P[3 * i + 1] = q.y; P[3 * i + 2] = q.z; D[i] = q.sub(p).dot(n); }
      const T = idx ? idx.array : Array.from({ length: N }, (_, i) => i);
      const cut = (a, b) => {
        if (D[a] > D[b]) [a, b] = [b, a];
        const t = D[a] / (D[a] - D[b]), c = [0, 1, 2].map((j) => P[3 * a + j] + t * (P[3 * b + j] - P[3 * a + j]));
        const k = c.map((x) => Math.round(x * 1e6)).join(); if (!pt.has(k)) pt.set(k, c); return k;
      };
      for (let t = 0; t < T.length; t += 3) {
        const e = [];
        for (const [a, b] of [[T[t], T[t + 1]], [T[t + 1], T[t + 2]], [T[t + 2], T[t]]]) if ((D[a] > 0) !== (D[b] > 0)) e.push(cut(a, b));
        if (e.length === 2 && e[0] !== e[1]) { link(e[0], e[1]); link(e[1], e[0]); }
      }
    }
    const seen = new Set();
    for (const k0 of adj.keys()) {
      if (seen.has(k0)) continue;
      const loop = []; let k = k0;
      while (k !== undefined && !seen.has(k)) { seen.add(k); loop.push(pt.get(k)); k = adj.get(k).find((x) => !seen.has(x)); }
      if (loop.length > 2) loops.push(loop.map((a) => { const r = new THREE.Vector3(...a).sub(p); return [r.dot(u), r.dot(v)]; }));
    }
    if (!loops.length) return null;
    const area = (L) => Math.abs(L.reduce((s, a, i) => { const b = L[(i + 1) % L.length]; return s + a[0] * b[1] - b[0] * a[1]; }, 0) / 2);
    const inside = (L) => { let c = false; for (let i = 0, j = L.length - 1; i < L.length; j = i++) {
      const [xi, yi] = L[i], [xj, yj] = L[j]; if ((yi > 0) !== (yj > 0) && 0 < (xj - xi) * (0 - yi) / (yj - yi) + xi) c = !c; } return c; };
    loops.sort((a, b) => area(b) - area(a));
    const L = loops.find(inside) || loops[0], ext = (j) => Math.max(...L.map((a) => a[j])) - Math.min(...L.map((a) => a[j]));
    return { area_mm2: Math.round(area(L) * 1e6), width_mm: mm(ext(0)), ap_mm: mm(ext(1)), loops: loops.length };
  }
}
