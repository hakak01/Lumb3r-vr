// Preset views (desktop and VR), fly-in places, zoom and life size.
// A view = target point + the direction to the eye + screen-up, all in model space (see spine.js).
import * as THREE from 'three';

export const MIN_S = 0.5, MAX_S = 40;
const Y = new THREE.Vector3(0, 1, 0), X = new THREE.Vector3(1, 0, 0);

export const VIEWS = [['surgeon', 'Surgeon (prone)'], ['mriAxial', 'MRI axial'], ['mriSag', 'MRI sagittal'],
  ['foramen', 'Foramen (lateral)'], ['kambin', 'Posterolateral 45°']];

export class Views {
  constructor(app) { this.app = app; this.level = 'L4-5'; this.name = 'start'; }

  // eye = direction from target to eye; up = screen up; dist = desktop camera distance (m); scale = VR size
  def(name, d = this.level) {
    const S = this.app.spine, F = S.disc[d], fl = (S.foramen[d + 'left'] || {}).c || F.o, back = F.a.clone().negate();
    switch (name) {
      case 'surgeon': return { target: F.o, eye: back, up: X.clone().negate(), dist: 0.42, scale: 1, flat: true };
      case 'mriAxial': return { target: F.o, eye: F.n.clone().negate(), up: F.a, dist: 0.2, scale: 3, clip: ['axial', F.o, F.n, false] };
      case 'mriSag': return { target: F.o, eye: F.l, up: Y, dist: 0.32, scale: 1.5, clip: ['sagittal', F.o, F.l, true] };
      case 'foramen': return { target: fl, eye: F.l, up: Y, dist: 0.11, scale: 4 };
      case 'kambin': return { target: fl, eye: F.l.clone().add(back), up: F.n, dist: 0.14, scale: 3 };
      case 'canal': { const c = S.canal['L4-5'], G = S.disc['L4-5'];
        return { target: c.c, eye: G.n, up: G.a.clone().negate(), dist: 0.002, scale: 20, inside: true }; }
      case 'inForamen': { const G = S.disc['L5-S1'];
        return { target: S.foramen['L5-S1left'].c, eye: G.l.clone().negate(), up: G.n, dist: 0.002, scale: 25, inside: true }; }
      default: return { target: F.o, eye: back.clone().add(F.l.clone().multiplyScalar(0.7)).addScaledVector(Y, 0.25), up: Y, dist: 0.42, scale: 1 };
    }
  }
  // rotation that turns the model so that eye -> +Z (towards the viewer) and up -> +Y
  rot(v) {
    const e = v.eye.clone().normalize(), r = v.up.clone().cross(e).normalize(), u = e.clone().cross(r);
    return new THREE.Quaternion().setFromRotationMatrix(new THREE.Matrix4().makeBasis(r, u, e)).invert();
  }

  apply(name = 'start', d) {
    if (d) this.level = d;
    const app = this.app, A = app.anatomy, v = this.def(name), q = this.rot(v), root = app.root;
    this.name = name;
    if (v.clip) A.snapClip(v.clip[0], v.clip[1], v.clip[2], v.clip[3]); else if (A.clip.mode !== 'off') A.setClip('off');
    if (app.inXR()) {
      const { head, f } = this.head(), yaw = new THREE.Quaternion().setFromAxisAngle(Y, Math.atan2(-f.x, -f.z));
      if (v.flat) yaw.multiply(new THREE.Quaternion().setFromAxisAngle(X, -Math.PI / 2));   // lying on a table, back up
      const anchor = v.inside ? head : head.clone().addScaledVector(f, v.flat ? 0.45 : 0.5).add(new THREE.Vector3(0, v.flat ? -0.45 : -0.1, 0));
      root.scale.setScalar(v.scale); root.quaternion.copy(yaw.multiply(q));
      root.position.copy(anchor).sub(v.target.clone().multiplyScalar(v.scale).applyQuaternion(root.quaternion));
    } else {
      const cam = app.camera, ctl = app.controls;
      root.scale.setScalar(1); root.quaternion.copy(q);
      root.position.copy(v.target).applyQuaternion(q).negate();
      cam.up.set(0, 1, 0); cam.position.set(0, 0, v.dist); ctl.target.set(0, 0, 0); ctl.update();
    }
    app.menus && app.menus.refresh();
  }

  head() {
    const cam = this.app.renderer.xr.getCamera(), head = new THREE.Vector3(), q = new THREE.Quaternion();
    cam.getWorldPosition(head); cam.getWorldQuaternion(q);
    const gaze = new THREE.Vector3(0, 0, -1).applyQuaternion(q), f = gaze.clone().setY(0);
    if (f.lengthSq() < 1e-6) f.set(0, 0, -1);
    return { head, gaze, f: f.normalize() };
  }
  // Zoom by factor k (VR: about a point 30 cm in front of the eyes, or the eyes when inside; desktop: camera distance)
  zoom(k) {
    const app = this.app, root = app.root;
    if (!app.inXR()) {
      const c = app.camera, t = app.controls.target, d = c.position.clone().sub(t);
      c.position.copy(t).addScaledVector(d, THREE.MathUtils.clamp(d.length() / k, 0.001, 3) / d.length()); app.controls.update(); return;
    }
    const s0 = root.scale.x, s = THREE.MathUtils.clamp(s0 * k, MIN_S, MAX_S), { head, gaze } = this.head();
    const pivot = s0 > 8 ? head : head.clone().addScaledVector(gaze, 0.3);
    root.updateMatrixWorld(true);
    const local = root.worldToLocal(pivot.clone());
    root.scale.setScalar(s); root.position.copy(pivot).sub(local.multiplyScalar(s).applyQuaternion(root.quaternion));
  }
  // VR: true size (1:1). Desktop: camera 0.5 m from the target.
  lifeSize() {
    if (this.app.inXR()) return this.zoom(1 / this.app.root.scale.x);
    const c = this.app.camera, t = this.app.controls.target;
    c.position.sub(t).setLength(0.5).add(t); this.app.controls.update();
  }
}
