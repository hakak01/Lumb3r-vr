// Lumbar landmarks measured on the loaded meshes (model space = app.root local, metres, +x patient left, +y up,
// +z anterior): disc frames, pedicle centres, canal and foramen centres, clip snaps, part groups for the Parts tab.
import * as THREE from 'three';

export const VERTS = ['L3', 'L4', 'L5', 'S1'], DISCS = ['L3-4', 'L4-5', 'L5-S1'];
const ABOVE = { L3: 'L2-3', L4: 'L3-4', L5: 'L4-5', S1: 'L5-S1' }, BELOW = { L3: 'L3-4', L4: 'L4-5', L5: 'L5-S1' };
const UPPER = { 'L2-3': 'L2', 'L3-4': 'L3', 'L4-5': 'L4', 'L5-S1': 'L5' }, LOWER = { 'L3-4': 'L4', 'L4-5': 'L5', 'L5-S1': 'S1' };
const discName = (d) => 'Annulus fibrosus ' + d.replace(/^L(\d)-(\d)$/, 'L$1-L$2');

// Parts tab: [label, test(struct)]; PLANNED (now empty) are shown greyed when the model has none yet.
const P = (part) => (s) => s.part === part;
export const GROUPS = [
  ['Body', P('body')], ['Pedicle', P('pedicle')], ['Pars interarticularis', P('pars interarticularis')], ['Lamina', P('lamina')],
  ['Sup. articular process', P('superior articular process')], ['Inf. articular process', P('inferior articular process')],
  ['Transverse process', P('transverse process')], ['Spinous process', P('spinous process')], ['Sacral ala', P('ala')],
  ['Rest of sacrum', P('rest of sacrum')], ['Facet joint', (s) => /facet/i.test(s.name)], ['Annulus fibrosus', P('annulus fibrosus')],
  ['Nucleus pulposus', P('nucleus pulposus')], ['Endplate', (s) => /endplate/i.test(s.name)],
  ['Ant. longitudinal lig.', P('anterior longitudinal ligament')], ['Post. longitudinal lig.', P('posterior longitudinal ligament')],
  ['Ligamentum flavum', P('ligamentum flavum')], ['Interspinous lig.', P('interspinous ligament')],
  ['Supraspinous lig.', P('supraspinous ligament')], ['Intertransverse lig.', P('intertransverse ligament')],
  ['Dura', (s) => /\bdura|arachnoid/i.test(s.name) && !/\(old\)/.test(s.name)], ['Cord & filum', (s) => /filum|spinal cord/i.test(s.name)],
  ['Roots', (s) => s.layer === 'neural' && /(^| )root$/.test(s.part)], ['Ganglia', (s) => /ganglion/i.test(s.part || s.name)],
  ['Spinal nerves', (s) => s.part === 'spinal nerve'],
  ['Medial branch / SVN', (s) => /medial branch|dorsal ramus|sinuvertebral/.test(s.part)],
  ['Epidural & foraminal fat', (s) => s.layer === 'epidural_fat' || s.part === 'prelaminar band'],
  ['Vertebral venous plexus', (s) => /venous plexus|basivertebral|intervertebral vein/.test(s.part)],
  ['Vessels', (s) => s.layer === 'artery' || s.layer === 'vein'],
  ['Muscles & fascia', (s) => s.layer === 'muscle' || s.layer === 'fascia_retinacula'],
  ['Landmarks', (s) => s.layer === 'landmark'],
  ['Old (superseded)', (s) => s.part === 'superseded'],
];
export const PLANNED = new Set();   // Phase C2 built the last planned parts (facet joints, endplates)

export class Spine {
  constructor(app) {
    this.app = app; this.A = app.anatomy; this.root = app.root;
    this.disc = {}; this.ped = {}; this.canal = {}; this.foramen = {};
    for (const d of ['L2-3', ...DISCS]) this.disc[d] = this.discFrame(d);
    for (const v of ['L3', 'L4', 'L5']) for (const sd of ['left', 'right']) this.ped[v + sd] = this.box(`${v} pedicle (${sd})`);
    for (const d of DISCS) {
      this.canal[d] = this.canalCentre(d);
      for (const sd of ['left', 'right']) this.foramen[d + sd] = this.foramenCentre(d, sd);
    }
  }
  get(name) { return this.A.byName.get(name); }
  get toModel() { this.root.updateMatrixWorld(true); return new THREE.Matrix4().copy(this.root.matrixWorld).invert(); }
  // structures of a level (any of the given parts)
  of(level, test) { return this.A.structs.filter((s) => s.level === level && test(s)); }

  // model-space vertices of a structure (every k-th)
  verts(s, max = 6000) {
    const out = [], v = new THREE.Vector3(), M = new THREE.Matrix4(), W = this.toModel;
    const n = s.meshes.reduce((a, m) => a + m.geometry.attributes.position.count, 0), k = Math.max(1, Math.floor(n / max));
    for (const m of s.meshes) {
      M.multiplyMatrices(W, m.matrixWorld); const p = m.geometry.attributes.position;
      for (let i = 0; i < p.count; i += k) out.push(v.fromBufferAttribute(p, i).applyMatrix4(M).clone());
    }
    return out;
  }
  box(name) {
    const s = this.get(name); if (!s) return null;
    const b = new THREE.Box3().setFromPoints(this.verts(s));
    return { c: b.getCenter(new THREE.Vector3()), min: b.min, max: b.max };
  }

  // Disc frame from PCA of the annulus: n = cranial normal (least spread), l = patient left, a = anterior; o = centre.
  discFrame(d) {
    const s = this.get(discName(d)); if (!s) return null;
    const P = this.verts(s), o = P.reduce((a, p) => a.add(p), new THREE.Vector3()).divideScalar(P.length);
    const C = [0, 0, 0, 0, 0, 0];
    for (const p of P) { const x = p.x - o.x, y = p.y - o.y, z = p.z - o.z; C[0] += x * x; C[1] += x * y; C[2] += x * z; C[3] += y * y; C[4] += y * z; C[5] += z * z; }
    const mul = (a) => new THREE.Vector3(C[0] * a.x + C[1] * a.y + C[2] * a.z, C[1] * a.x + C[3] * a.y + C[4] * a.z, C[2] * a.x + C[4] * a.y + C[5] * a.z);
    const power = (a, not) => { for (let i = 0; i < 60; i++) { a = mul(a); if (not) a.addScaledVector(not, -a.dot(not)); a.normalize(); } return a; };
    const e1 = power(new THREE.Vector3(1, 0.1, 0.2)), e2 = power(new THREE.Vector3(0.1, 0.2, 1), e1);
    const n = e1.clone().cross(e2).normalize(); if (n.y < 0) n.negate();
    const l = new THREE.Vector3(1, 0, 0).addScaledVector(n, -n.x).normalize(), a = l.clone().cross(n);
    // centre = middle of the extent along each axis
    const ext = [l, n, a].map((ax) => { let lo = 1e9, hi = -1e9; for (const p of P) { const t = p.clone().sub(o).dot(ax); lo = Math.min(lo, t); hi = Math.max(hi, t); } return [lo, hi]; });
    const c = o.clone(); [l, n, a].forEach((ax, i) => c.addScaledVector(ax, (ext[i][0] + ext[i][1]) / 2));
    return { o: c, n, l, a, size: ext.map(([lo, hi]) => hi - lo) };   // size: width, height, AP depth (m)
  }

  // Ray in model space against structures (both faces); returns sorted distances + points.
  cast(from, dir, structs, far = 0.08) {
    const meshes = structs.filter(Boolean).flatMap((s) => s.meshes), saved = meshes.map((m) => m.material.side);
    meshes.forEach((m) => { m.material.side = THREE.DoubleSide; });
    const W = this.toModel, w = this.root.matrixWorld, o = from.clone().applyMatrix4(w), d = dir.clone().transformDirection(w);
    const rc = new THREE.Raycaster(o, d, 0, far * this.root.scale.x);
    const hits = rc.intersectObjects(meshes, false).map((h) => ({ d: h.distance / this.root.scale.x, p: h.point.applyMatrix4(W), s: h.object.userData.struct }));
    meshes.forEach((m, i) => { m.material.side = saved[i]; });
    return hits;
  }
  post(v) { return this.A.structs.filter((s) => s.level === v && s.layer === 'bone' && s.part !== 'body'); }

  // Canal centre at mid-disc: halfway between the back of the disc/PLL and the flavum/posterior arch (midline).
  canalCentre(d) {
    const F = this.disc[d]; if (!F) return null;
    const back = F.a.clone().negate();
    const disc = this.of(d, (s) => /annulus|nucleus|posterior longitudinal/.test(s.part));
    const h1 = this.cast(F.o, back, disc, 0.05); if (!h1.length) return null;
    const A = h1[h1.length - 1].p;
    const walls = [...this.of(d, (s) => /flavum|interspinous/.test(s.part)), ...this.post(UPPER[d]), ...this.post(LOWER[d])];
    const h2 = this.cast(A.clone().addScaledVector(back, 0.0005), back, walls, 0.04);
    const B = h2.length ? h2[0].p : A.clone().addScaledVector(back, 0.018);
    return { c: A.clone().add(B).multiplyScalar(0.5), ap: A.distanceTo(B) + (h2.length ? 0.0005 : 0), front: A, back: B };
  }

  // Foramen centre measured in Phase A (assets/model.json "foramen", tools/viewer_marks.py); else under the upper pedicle.
  foramenCentre(d, sd) {
    const g = ((this.app.model || {}).foramen || {})[d + ' ' + sd];
    if (g) return { c: new THREE.Vector3(...g).add(this.A.center.position), measured: true };
    const up = this.ped[UPPER[d] + sd], F = this.disc[d];
    return up && { c: up.c.clone().addScaledVector(F.n, -0.008) };
  }

  // Axial plane at mid-pedicle: pedicle centres, normal = mean of the discs above and below (S1: offset copied from L5).
  pedicleSnap(v) {
    const na = this.disc[ABOVE[v]], nb = this.disc[BELOW[v]];
    if (v !== 'S1') {
      const p = this.ped[v + 'left'].c.clone().lerp(this.ped[v + 'right'].c, 0.5);
      const n = na && nb ? na.n.clone().add(nb.n).normalize() : (na || nb).n.clone();
      return { p, n };
    }
    const L5 = this.ped.L5left.c.clone().lerp(this.ped.L5right.c, 0.5), F = this.disc['L4-5'], G = this.disc['L5-S1'];
    const off = L5.sub(F.o), p = G.o.clone().addScaledVector(G.l, off.dot(F.l)).addScaledVector(G.n, off.dot(F.n)).addScaledVector(G.a, off.dot(F.a));
    return { p, n: G.n.clone(), approx: true };
  }
}
