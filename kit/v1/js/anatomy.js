// Registry of structures + visibility / ghost / isolate / clip / highlight state.
import * as THREE from 'three';
import { lookKey, makeMaterial } from './looks.js';
import { Labels } from './labels.js';

const GHOST = 0.25, XRAY = 0.12;
const BONE = new Set(['bone', 'context_bone']);
// drawn from both sides so they stay visible from inside (fly-in): dura, roots, discs, canal walls
const DOUBLE = (s) => ['neural', 'disc'].includes(s.layer) || /annulus|nucleus|flavum|posterior longitudinal/i.test(s.name);
const RIM = { vertexShader: `#include <common>
#include <clipping_planes_pars_vertex>
varying vec3 vN, vV;
void main() {
#include <begin_vertex>
#include <project_vertex>
#include <clipping_planes_vertex>
  vN = normalize(normalMatrix * normal); vV = normalize(-mvPosition.xyz); }`,
  fragmentShader: `#include <common>
#include <clipping_planes_pars_fragment>
uniform vec3 uColor; varying vec3 vN, vV;
void main() {
#include <clipping_planes_fragment>
  float r = pow(1.0 - abs(dot(normalize(vN), normalize(vV))), 2.2); gl_FragColor = vec4(uColor * r, r); }` };
const mats = (m) => { const { present, real } = m.userData.mats; return real && real !== present ? [present, real] : [present]; };
const AXES = { sagittal: new THREE.Vector3(1, 0, 0), axial: new THREE.Vector3(0, 1, 0), coronal: new THREE.Vector3(0, 0, 1) };

export class Anatomy {
  // root: Group that the user moves. gltfScene: loaded scene. manifest: list. look: look.json
  // centre: [x,y,z] in glTF metres put at the origin (GH joint); default = bounding-box centre
  constructor(root, gltfScene, manifest, look, centre) {
    this.root = root; this.look = look;
    this.layers = JSON.parse(JSON.stringify(look.layers));
    this.showOrigins = this.showInsertions = this.layers.attachment.on;
    this.structs = []; this.byName = new Map();
    this.isolated = null; this.selected = null; this.onChange = () => {};
    this.worldPlane = new THREE.Plane(new THREE.Vector3(0, 1, 0), 1e6);
    this.clipPlanes = [this.worldPlane];
    this.clip = { mode: 'off', pos: 0.5, flip: false, frame: null };   // frame: {p, n, span} = snapped plane (model space)
    this.hideGhost = 0; this.xray = false;   // hideGhost: opacity of hidden parts (0-0.6)
    this.skinTone = look.skinTone ?? 0.2;
    this.highlight = new THREE.Color(look.highlight);

    // centre the model on the given point (glenohumeral joint) or its bounding box
    const box = new THREE.Box3().setFromObject(gltfScene);
    this.center = new THREE.Group();
    this.center.position.copy(centre ? new THREE.Vector3(...centre) : box.getCenter(new THREE.Vector3())).negate();
    this.center.add(gltfScene); root.add(this.center);
    root.updateMatrixWorld(true);
    this.box = box.clone().translate(this.center.position);   // model-space box (centred)

    const info = new Map(manifest.map((e) => [e.name, e]));
    const sanitize = (s) => s.replace(/\s/g, '_').replace(/[\[\]\.:\/]/g, '');
    const bySan = new Map(manifest.map((e) => [sanitize(e.name), e]));
    const gone = new Set(manifest.map((e) => e.replaces).filter(Boolean));   // replaced by a gaps.glb structure
    const inv = new THREE.Matrix4().copy(root.matrixWorld).invert();
    for (const node of [...gltfScene.children]) {
      const raw = node.userData.name || node.name, e = info.get(raw) || bySan.get(node.name) ||
        info.get(raw.replace(/\.\d{3}$/, ''));   // Blender duplicate suffix, e.g. 'Vertebra C4.001'
      if (/^rig:?[a-z]/.test(raw)) continue;   // skeleton (rig.js)
      if (!e) { console.warn('not in manifest', node.name); continue; }
      if (gone.has(e.name)) { node.removeFromParent(); continue; }
      const s = { name: e.name, layer: e.layer, kind: e.kind || null, approx: !!e.approx, source: e.source, label: e.label,
        level: e.level || '', side: e.side || '', part: e.part || '', context: !!e.context, node, meshes: [], hidden: !!e.hidden, ghost: false };
      node.traverse((m) => {
        if (!m.isMesh) return;
        const key = lookKey(e.layer, m.material && m.material.name, s.kind, e.name);
        const nm = new THREE.Matrix4().multiplyMatrices(inv, m.matrixWorld);
        m.userData.gltfMat = m.material && m.material.name;
        m.material = makeMaterial(look, key, m, nm, this.clipPlanes);
        m.userData.mats = { present: m.material };   // 'real' is added by tissues.js
        if (DOUBLE(s)) { m.material.side = THREE.DoubleSide; m.material.userData.dbl = true; m.material.userData.u.uBack.value = 0; }
        m.userData.struct = s;
        s.meshes.push(m);
      });
      this.structs.push(s); this.byName.set(s.name, s);
    }
    this.structs.sort((a, b) => a.name.localeCompare(b.name));
    this.labels = new Labels(this, look.landmarkLabels ?? false);
    this.setSkinTone(this.skinTone);
    this.apply();
  }

  visibleOf(s) {
    const L = this.layers[s.layer];
    if (!L || !L.on || (s.hidden && this.hideGhost < 0.01)) return false;
    if (s.kind === 'origin' && !this.showOrigins) return false;
    if (s.kind === 'insertion' && !this.showInsertions) return false;
    if (this.isolated && !this.isolated.has(s)) return false;
    return L.opacity > 0.01;
  }

  apply() {
    for (const s of this.structs) {
      const vis = this.visibleOf(s), f = this.layers[s.layer].opacity * (s.ghost ? GHOST : 1) * (s.hidden ? this.hideGhost : 1)
        * (this.xray && BONE.has(s.layer) && s !== this.selected ? XRAY : 1);
      for (const m of s.meshes) {
        m.visible = vis; if (m.userData.rim) m.userData.rim.visible = this.xray;
        for (const mat of mats(m)) {
          const op = mat.userData.baseOpacity * f, tr = op < 0.999;
          mat.opacity = op;
          if (mat.transparent !== tr) { mat.transparent = tr; mat.depthWrite = !tr; mat.needsUpdate = true; }
          if (mat.emissive) mat.emissive.copy(s === this.selected ? this.highlight : new THREE.Color(0)).multiplyScalar(0.35);
        }
      }
    }
    this.pickables = this.structs.filter((s) => this.visibleOf(s)).flatMap((s) => s.meshes);
    if (this.labels) this.labels.update();
    this.onChange();
  }

  setLayer(layer, on) {
    this.layers[layer].on = on;
    if (layer === 'attachment') this.showOrigins = this.showInsertions = on;
    this.apply();
  }
  setLayerOpacity(layer, v) { this.layers[layer].opacity = v; this.apply(); }
  setFootprints(origins, insertions) {
    this.showOrigins = origins; this.showInsertions = insertions;
    this.layers.attachment.on = origins || insertions; this.apply();
  }
  setHideGhost(v) { this.hideGhost = v; this.apply(); }
  // X-ray: bones ghosted, with a bright rim (outline) drawn on top
  setXray(on) {
    this.xray = on;
    if (on && !this.rimMat) {
      this.rimMat = new THREE.ShaderMaterial({ ...RIM, uniforms: { uColor: { value: new THREE.Color(0x9fd8ff) } }, transparent: true,
        depthWrite: false, blending: THREE.AdditiveBlending, side: THREE.DoubleSide, clipping: true, clippingPlanes: this.clipPlanes });
      for (const s of this.structs) if (BONE.has(s.layer)) for (const m of s.meshes) {
        const r = new THREE.Mesh(m.geometry, this.rimMat); r.renderOrder = 5; r.raycast = () => {}; m.add(r); m.userData.rim = r;
      }
    }
    this.apply();
  }
  select(s) { this.selected = s; this.apply(); }
  hide(s) { s.hidden = true; if (this.selected === s) this.selected = null; this.apply(); }
  toggleGhost(s) { s.ghost = !s.ghost; this.apply(); }
  isolate(s) {
    this.isolated = new Set([s]);
    if (!this.layers[s.layer].on) this.layers[s.layer].on = true;
    if (s.kind === 'origin') this.showOrigins = true;
    if (s.kind === 'insertion') this.showInsertions = true;
    s.hidden = false; this.apply();
  }
  showAll() {
    this.isolated = null;
    for (const s of this.structs) { s.hidden = s.part === 'superseded'; s.ghost = false; }   // old parts stay hidden
    for (const k in this.layers) if (k !== 'attachment' && k !== 'fat') { this.layers[k].on = true; if (this.layers[k].opacity < 0.05) this.layers[k].opacity = 1; }
    this.apply();
  }
  search(q) {
    const words = q.toLowerCase().split(/\s+/).filter(Boolean);
    if (!words.length) return this.structs;
    return this.structs.filter((s) => words.every((w) => s.name.toLowerCase().includes(w)));
  }
  setSkinTone(t) {
    this.skinTone = t;
    const a = new THREE.Color(this.look.looks.skin.color), b = new THREE.Color(this.look.looks.skin.colorDark);
    const R = this.skinReal, ra = R && new THREE.Color(R.color), rb = R && new THREE.Color(R.colorDark || R.color);
    for (const s of this.structs) for (const m of s.meshes) for (const mat of mats(m)) {
      if (mat.userData.key !== 'skin') continue;
      if (mat.isMeshPhysicalMaterial) mat.color.lerpColors(ra, rb, t); else mat.color.lerpColors(a, b, t);
      mat.userData.u.uCut.value.copy(mat.color).multiplyScalar(0.8);
    }
  }
  // 'present' or 'realistic' (realistic materials must already exist, see tissues.js)
  setView(v) {
    this.view = v;
    for (const s of this.structs) for (const m of s.meshes) m.material = (v === 'realistic' && m.userData.mats.real) || m.userData.mats.present;
    this.setSkinTone(this.skinTone); this.apply();
  }

  // world-space centre + size of a structure
  bounds(s) {
    const b = new THREE.Box3();
    for (const m of s.meshes) b.expandByObject(m);
    return { center: b.getCenter(new THREE.Vector3()), size: b.getSize(new THREE.Vector3()).length() };
  }

  setClip(mode) {
    const wasOn = this.clip.mode !== 'off', on = mode !== 'off';
    this.clip.mode = mode; this.clip.frame = null;
    if (wasOn !== on) for (const s of this.structs) for (const m of s.meshes) for (const mat of mats(m)) {
      mat.side = on || mat.userData.dbl ? THREE.DoubleSide : THREE.FrontSide; mat.needsUpdate = true;
      if (mat.userData.dbl) mat.userData.u.uBack.value = on ? 1 : 0;   // cut faces filled only while clipping
    }
    this.updateClip();
  }
  updateClip() {
    const c = this.clip;
    if (c.mode === 'off') { this.worldPlane.set(new THREE.Vector3(0, 1, 0), 1e6); return; }
    if (c.frame) {
      const n = c.frame.n.clone().multiplyScalar(c.flip ? -1 : 1), p = c.frame.p.clone().addScaledVector(c.frame.n, (c.pos - 0.5) * c.frame.span);
      this.worldPlane.setFromNormalAndCoplanarPoint(n, p).applyMatrix4(this.root.matrixWorld); return;
    }
    const n = AXES[c.mode].clone(), k = c.mode === 'sagittal' ? 'x' : c.mode === 'axial' ? 'y' : 'z';
    const p = new THREE.Vector3(); p[k] = this.box.min[k] + c.pos * (this.box.max[k] - this.box.min[k]);
    if (c.flip) n.negate();
    this.worldPlane.setFromNormalAndCoplanarPoint(n, p).applyMatrix4(this.root.matrixWorld);
  }
  // Plane through model-space point p with normal n (kept side = n); slider/thumbstick move it ±span/2.
  snapClip(mode, p, n, flip = false, span = 0.06) {
    this.setClip(mode); Object.assign(this.clip, { frame: { p: p.clone(), n: n.clone().normalize(), span }, pos: 0.5, flip });
    this.updateClip();
  }
  // Is a world point on the visible side of the clip plane?
  kept(pt) { return this.clip.mode === 'off' || this.worldPlane.distanceToPoint(pt) >= 0; }

  pick(raycaster) {
    const hits = raycaster.intersectObjects(this.pickables, false).filter((h) => this.kept(h.point));
    const solid = hits.find((h) => h.object.material.opacity > 0.5 && !h.object.userData.struct.hidden);
    const h = solid || hits[0];
    return h ? { struct: h.object.userData.struct, distance: h.distance, point: h.point } : null;
  }
}
