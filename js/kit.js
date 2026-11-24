// Shoulder kit: load the normal right shoulder & arm into any three.js scene (how to use: docs/KIT.md).
// Coordinates ("file coordinates") = the glTF files = Z-Anatomy world: metres, +X = patient's left, +Y = up,
// +Z = anterior; the right GH joint is at model.center. kit.root (a Group you may move/scale) puts the GH joint at its origin.
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { MeshoptDecoder } from 'three/addons/libs/meshopt_decoder.module.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import { Anatomy } from './anatomy.js';
import { Realism } from './tissues.js';

export const KIT_BASE = new URL('../', import.meta.url).href;   // the folder that holds assets/

export async function loadShoulder(opt) {
  const base = opt.base || KIT_BASE, url = (f) => base + 'assets/' + f;
  const get = (f) => fetch(url(f), { cache: 'no-cache' }).then((r) => r.ok ? r.json() : []).catch(() => []);
  const model = await get('model.json'), js = (g) => g.replace(/\.glb$/, '.json');
  const [look, manifest, gapsMan, markMan] = await Promise.all(['look.json', 'manifest.json',
    js(model.gaps), js(model.landmarks)].map(get));
  const loader = new GLTFLoader().setMeshoptDecoder(MeshoptDecoder), got = [0, 0, 0], tot = [6e6, 4e5, 1.4e5];
  const prog = (i) => (e) => { got[i] = e.loaded; if (e.total) tot[i] = e.total;
    opt.onProgress && opt.onProgress(Math.min(1, (got[0] + got[1] + got[2]) / (tot[0] + tot[1] + tot[2]))); };
  const [gltf, gaps, marks] = await Promise.all([model.glb, model.gaps, model.landmarks].map((f, i) =>
    loader.loadAsync(url(f), prog(i))));
  for (const g of [gaps, marks]) for (const n of [...g.scene.children]) gltf.scene.add(n);
  const kit = new Kit(opt, base, gltf.scene, { model, look, manifest: manifest.concat(gapsMan, markMan) });
  if (opt.view && opt.view !== 'present') await kit.setView(opt.view);
  return kit;
}

class Kit {
  constructor(o, base, model, d) {
    const { renderer, scene } = o;
    this.root = new THREE.Group(); this.root.name = 'shoulder-kit'; (o.parent || scene).add(this.root);
    if (!scene.environment) { const pm = new THREE.PMREMGenerator(renderer); scene.environment = pm.fromScene(new RoomEnvironment(), 0.04).texture; pm.dispose(); }
    const lights = { hemi: new THREE.HemisphereLight(0xffffff, 0x445566, 0.6), sun: new THREE.DirectionalLight(0xffffff, 1.4) };
    lights.sun.position.set(0.5, 1, 1.2);
    if (o.lights !== false) scene.add(lights.hemi, lights.sun);
    renderer.localClippingEnabled = true;
    this.model = model; this.center = d.model.center; this.data = d;
    const app = this.app = { base, renderer, scene, camera: o.camera, root: this.root, lights, onPose: () => this.onPose(this) };
    this.anatomy = app.anatomy = new Anatomy(this.root, model, d.manifest, d.look, d.model.center);
    this.realism = app.realism = new Realism(app);
    this.onPose = () => {};
  }

  // ---- structures (names as in assets/manifest.json, gaps.json, landmarks.json) ----
  names(layer) { return this.anatomy.structs.filter((s) => !layer || s.layer === layer).map((s) => s.name); }
  get(name) { return this.anatomy.byName.get(name) || null; }   // {name, layer, kind, approx, node, meshes, hidden, ghost}
  find(text) { return this.anatomy.search(text); }
  _s(x) { const s = typeof x === 'string' ? this.get(x) : x; if (!s) console.warn('kit: no structure', x); return s; }
  show(name, on = true) { const s = this._s(name); if (s) { s.hidden = !on; this.anatomy.apply(); } return this; }
  ghost(name, on = true) { const s = this._s(name); if (s) { s.ghost = on; this.anatomy.apply(); } return this; }
  select(name) { this.anatomy.select(name ? this._s(name) : null); return this; }
  isolate(names) {          // array of names, or null to end isolation
    const A = this.anatomy;
    A.isolated = names ? new Set(names.map((n) => this._s(n)).filter(Boolean)) : null;
    if (A.isolated) for (const s of A.isolated) { A.layers[s.layer].on = true; s.hidden = false;
      if (s.kind === 'origin') A.showOrigins = true; if (s.kind === 'insertion') A.showInsertions = true; }
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
  setClip(mode, pos = 0.5, flip = false) { Object.assign(this.anatomy.clip, { pos, flip }); this.anatomy.setClip(mode); return this; }
  pick(raycaster) { return this.anatomy.pick(raycaster); }   // {struct, distance, point} or null
  setView(v) { return this.realism.setView(v); }             // 'present' | 'realistic' | 'cadaver' (Promise)

  // call once per frame before renderer.render
  update() {
    const xr = this.app.renderer.xr.isPresenting; if (this.app.camera || xr) this.realism.update();
    this.root.updateMatrixWorld(); this.anatomy.updateClip();
  }
  // ---- coordinates ----
  toWorld(p) { this.root.updateMatrixWorld(true); return this.model.localToWorld(p.clone()); }
  fromWorld(p) { this.root.updateMatrixWorld(true); return this.model.worldToLocal(p.clone()); }

  // Add your own mesh made in file coordinates (fixed to the model). With a name it becomes a structure.
  addMesh(mesh, { name = mesh.name, layer = 'custom' } = {}) {
    mesh.updateMatrix(); this.model.add(mesh);
    if (!name) return null;
    const A = this.anatomy;
    if (!A.layers[layer]) A.layers[layer] = { label: layer, on: true, opacity: 1 };
    const s = { name, layer, kind: null, approx: false, source: 'custom', custom: true, node: mesh, meshes: [], hidden: false, ghost: false };
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
