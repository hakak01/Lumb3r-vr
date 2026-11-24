// Lumbar kit: load the normal lumbosacral spine (L3-S1 in detail) into any three.js scene (how to use: docs/KIT.md).
// File coordinates = the glTF files: metres, +x = patient's left, +y = up, +z = anterior. kit.root (a Group you may
// move/scale) has the L4-5 disc centre (kit.center, file coordinates) at its origin. All kit inputs/outputs that are
// points or axes use FILE coordinates (THREE.Vector3); sizes are mm.
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { MeshoptDecoder } from 'three/addons/libs/meshopt_decoder.module.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import { Anatomy } from './anatomy.js';
import { Realism } from './tissues.js';
import { Spine, GROUPS, VERTS, DISCS } from './spine.js';
import { Measure } from './measure.js';

export const KIT_BASE = new URL('../', import.meta.url).href;   // the folder that holds assets/
export { VERTS, DISCS };

export async function loadLumbar(opt) {
  const base = opt.base || KIT_BASE, url = (f) => base + 'assets/' + f;
  const get = (f) => fetch(url(f), { cache: 'no-cache' }).then((r) => r.ok ? r.json() : null).catch(() => null);
  const model = await get('model.json'), js = (g) => g.replace(/\.glb$/, '.json');
  const [look, manifest, gapsMan, levels] = await Promise.all(['look.json', 'manifest.json', js(model.gaps), 'levels.json'].map(get));
  const loader = new GLTFLoader().setMeshoptDecoder(MeshoptDecoder), got = [0, 0], tot = [2.9e6, 1.4e6];
  const prog = (i) => (e) => { got[i] = e.loaded; if (e.total) tot[i] = e.total;
    opt.onProgress && opt.onProgress(Math.min(1, (got[0] + got[1]) / (tot[0] + tot[1]))); };
  const [gltf, gaps] = await Promise.all([model.glb, model.gaps].map((f, i) => loader.loadAsync(url(f), prog(i))));
  for (const n of [...gaps.scene.children]) gltf.scene.add(n);
  const kit = new Kit(opt, base, gltf.scene, { model, look, levels, manifest: manifest.concat(gapsMan || []) });
  if (opt.view && opt.view !== 'present') await kit.setView(opt.view);
  return kit;
}

class Kit {
  constructor(o, base, model, d) {
    const { renderer, scene } = o;
    this.root = new THREE.Group(); this.root.name = 'lumbar-kit'; (o.parent || scene).add(this.root);
    if (!scene.environment) { const pm = new THREE.PMREMGenerator(renderer); scene.environment = pm.fromScene(new RoomEnvironment(), 0.04).texture; pm.dispose(); }
    const lights = { hemi: new THREE.HemisphereLight(0xffffff, 0x445566, 0.6), sun: new THREE.DirectionalLight(0xffffff, 1.4) };
    lights.sun.position.set(0.5, 1, 1.2);
    if (o.lights !== false) scene.add(lights.hemi, lights.sun);
    renderer.localClippingEnabled = true;
    this.model = model; this.center = new THREE.Vector3(...d.model.center); this.data = d;
    this.levels = d.levels ? d.levels.levels : {};   // assets/levels.json baseline (read-only reference)
    const app = this.app = { base, renderer, scene, camera: o.camera, root: this.root, lights, model: d.model };
    this.anatomy = app.anatomy = new Anatomy(this.root, model, d.manifest, d.look, d.model.center);
    this.realism = app.realism = new Realism(app);
    this.spine = app.spine = new Spine(app);
    this.measure = new Measure(this);
  }

  // ---- structures (names as in assets/manifest.json and gaps.json) ----
  names(layer) { return this.anatomy.structs.filter((s) => !layer || s.layer === layer).map((s) => s.name); }
  get(name) { return this.anatomy.byName.get(name) || null; }   // {name, layer, level, side, part, approx, source, node, meshes, hidden, ghost}
  find(text) { return this.anatomy.search(text); }
  // Filter {level, side, part, group, layer, name}: level/side/layer = string or array; part = manifest part
  // ('pedicle', 'ligamentum flavum'...); group = a Parts-menu label ('Roots', 'Facet joint'...); name = RegExp.
  where(q = {}) {
    const has = (v, x) => v === undefined || (Array.isArray(v) ? v.includes(x) : v === x);
    const g = q.group && GROUPS.find(([label]) => label === q.group);
    if (q.group && !g) console.warn('kit: no group', q.group, GROUPS.map((x) => x[0]));
    return this.anatomy.structs.filter((s) => has(q.level, s.level) && has(q.side, s.side) && has(q.part, s.part) &&
      has(q.layer, s.layer) && (!g || g[1](s)) && (!q.name || q.name.test(s.name)));
  }
  groups() { return GROUPS.map((g) => g[0]); }
  _list(x) { return (typeof x === 'string' ? [this.get(x)] : Array.isArray(x) ? x.map((n) => this._s(n)) : this.where(x)).filter(Boolean); }
  _s(x) { const s = typeof x === 'string' ? this.get(x) : x; if (!s) console.warn('kit: no structure', x); return s; }
  // x = name, array of names/structs, or a where() filter
  show(x, on = true) { for (const s of this._list(x)) { s.hidden = !on; if (on) this.anatomy.layers[s.layer].on = true; } this.anatomy.apply(); return this; }
  hide(x) { return this.show(x, false); }
  ghost(x, on = true) { for (const s of this._list(x)) s.ghost = on; this.anatomy.apply(); return this; }
  setHiddenOpacity(v) { this.anatomy.setHideGhost(v); return this; }   // 0 = hidden parts invisible, up to 0.6
  select(name) { this.anatomy.select(name ? this._s(name) : null); return this; }
  isolate(x) {          // name / array / filter, or null to end isolation
    const A = this.anatomy, L = x ? this._list(x) : null;
    A.isolated = L ? new Set(L) : null;
    if (L) for (const s of L) { A.layers[s.layer].on = true; s.hidden = false; }
    A.apply(); return this;
  }
  showAll() { this.anatomy.showAll(); return this; }
  setLayer(layer, on, opacity) {
    const L = this.anatomy.layers[layer]; if (!L) return console.warn('kit: no layer', layer), this;
    if (opacity !== undefined) L.opacity = opacity;
    this.anatomy.setLayer(layer, on); return this;
  }
  layers() { return Object.keys(this.anatomy.layers); }
  labels(on) { this.anatomy.labels.set(on); return this; }
  pick(raycaster) { return this.anatomy.pick(raycaster); }   // {struct, distance, point} or null
  setView(v) { return this.realism.setView(v); }             // 'present' | 'realistic' | 'cadaver' (Promise)

  // ---- clipping: one plane; the side the normal points to is kept ----
  setClip(mode, pos = 0.5, flip = false) { Object.assign(this.anatomy.clip, { pos, flip }); this.anatomy.setClip(mode); return this; }   // 'off'|'axial'|'sagittal'|'coronal'
  clipPlane(point, normal, flip = false) { this.anatomy.snapClip('axial', this._m(point), normal, flip); return this; }
  clipLevel(level, flip = false) {   // axial cut through a disc ('L4-5') or a pedicle ('L4') level
    const S = this.spine, F = S.disc[level], p = F ? { p: F.o, n: F.n } : S.pedicleSnap(level);
    this.anatomy.snapClip('axial', p.p, p.n, flip); return this;
  }

  // ---- levels ----
  // Live disc frame of the loaded meshes: {centre, cranial, left, anterior, size_mm:{width,height,ap}}
  discFrame(level) {
    const F = this.spine.disc[level]; if (!F) return null;
    return { centre: this._f(F.o), cranial: F.n.clone(), left: F.l.clone(), anterior: F.a.clone(),
      size_mm: { width: F.size[0] * 1e3, height: F.size[1] * 1e3, ap: F.size[2] * 1e3 } };
  }
  baseline(level) { return this.levels[level] ? JSON.parse(JSON.stringify(this.levels[level])) : null; }   // copy of levels.json
  measureCanal(level) { return this.measure.canal(level); }            // {canal_ap_mm, sac_area_mm2, sac_width_mm, sac_ap_mm, front, back}
  measureForamen(level, side, soft = false) { return this.measure.foramen(level, side, soft); }   // {height_mm, width_mm, ...}
  sectionArea(name, point, normal) { return this.measure.section(this._s(name), point, normal); }  // mm² of a closed mesh cut

  // call once per frame before renderer.render
  update() {
    const xr = this.app.renderer.xr.isPresenting; if (this.app.camera || xr) this.realism.update();
    this.root.updateMatrixWorld(); this.anatomy.updateClip();
  }
  // ---- coordinates: file <-> world, file <-> model space (root local) ----
  toWorld(p) { this.root.updateMatrixWorld(true); return this.model.localToWorld(p.clone()); }
  fromWorld(p) { this.root.updateMatrixWorld(true); return this.model.worldToLocal(p.clone()); }
  _m(p) { return p.clone().add(this.anatomy.center.position); }   // file -> model space
  _f(p) { return p.clone().sub(this.anatomy.center.position); }   // model space -> file

  // Add your own mesh made in file coordinates. bone = a bone part name ('L4 pedicle (left)') or a level ('L4', 'S1'):
  // the mesh is attached to that bone's node, so it stays fixed to it. With a name it becomes a structure.
  addMesh(mesh, { name = mesh.name, layer = 'custom', bone, level = '', side = '', part = '' } = {}) {
    mesh.updateMatrix(); this.model.add(mesh);
    const b = bone && (this.get(bone) || this.where({ level: bone, layer: 'bone', part: bone === 'S1' ? undefined : 'body' })[0]
      || this.where({ level: bone, layer: 'bone' })[0]);
    if (bone && !b) console.warn('kit: no bone', bone);
    if (b) { this.root.updateMatrixWorld(true); b.node.attach(mesh); }
    if (!name) return null;
    const A = this.anatomy;
    if (!A.layers[layer]) A.layers[layer] = { label: layer, on: true, opacity: 1 };
    const s = { name, layer, kind: null, approx: false, source: 'custom', custom: true, bone: b ? b.name : null,
      level: level || (b ? b.level : ''), side, part, node: mesh, meshes: [], hidden: false, ghost: false };
    mesh.traverse((m) => {
      if (!m.isMesh) return;
      m.userData.mats = { present: m.material }; m.userData.struct = s; s.meshes.push(m);
      m.material.userData.baseOpacity ??= m.material.opacity; m.material.clippingPlanes = A.clipPlanes;
    });
    A.structs.push(s); A.byName.set(name, s); A.apply();
    return s;
  }
  removeMesh(name) {
    const A = this.anatomy, s = A.byName.get(name); if (!s || !s.custom) return;
    s.node.removeFromParent(); A.structs.splice(A.structs.indexOf(s), 1); A.byName.delete(name);
    if (A.selected === s) A.selected = null; if (A.isolated) A.isolated.delete(s); A.apply();
  }
}
