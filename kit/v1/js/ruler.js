// Ruler: tap two points on the model; shows the true distance in mm (model space, so any zoom gives the real value).
import * as THREE from 'three';

const COLOR = 0xffd23f, R = 0.0022, H = 0.012;   // marker radius and label height in metres as seen (world)

export class Ruler {
  constructor(app) {
    this.app = app; this.on = false; this.pts = []; this.mm = null;
    this.group = new THREE.Group(); this.group.renderOrder = 30; app.root.add(this.group);
    const mat = new THREE.MeshBasicMaterial({ color: COLOR, depthTest: false, toneMapped: false });
    this.marks = [0, 1].map(() => { const m = new THREE.Mesh(new THREE.SphereGeometry(R, 16, 12), mat); m.renderOrder = 31; m.visible = false; this.group.add(m); return m; });
    this.line = new THREE.Line(new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(), new THREE.Vector3()]),
      new THREE.LineBasicMaterial({ color: COLOR, depthTest: false, toneMapped: false }));
    this.line.renderOrder = 31; this.line.visible = false; this.line.frustumCulled = false; this.group.add(this.line);
    this.canvas = document.createElement('canvas'); this.canvas.width = 256; this.canvas.height = 72;
    this.tex = new THREE.CanvasTexture(this.canvas); this.tex.colorSpace = THREE.SRGBColorSpace;
    this.label = new THREE.Sprite(new THREE.SpriteMaterial({ map: this.tex, depthTest: false, toneMapped: false }));
    this.label.renderOrder = 32; this.label.visible = false; this.group.add(this.label);
  }
  set(on) { this.on = on; if (!on) this.clear(); }
  clear() { this.pts = []; this.mm = null; this.marks.forEach((m) => { m.visible = false; }); this.line.visible = this.label.visible = false; }

  // world point from a pick
  add(world) {
    if (this.pts.length === 2) this.clear();
    const p = this.app.root.worldToLocal(world.clone()); this.pts.push(p);
    const m = this.marks[this.pts.length - 1]; m.position.copy(p); m.visible = true;
    if (this.pts.length === 2) {
      const [a, b] = this.pts; this.mm = a.distanceTo(b) * 1000;
      this.line.geometry.setFromPoints([a, b]); this.line.visible = true;
      const g = this.canvas.getContext('2d'); g.clearRect(0, 0, 256, 72);
      g.fillStyle = 'rgba(15,20,28,0.8)'; g.beginPath(); g.roundRect(0, 0, 256, 72, 14); g.fill();
      g.fillStyle = '#ffd23f'; g.font = 'bold 44px system-ui, sans-serif'; g.textAlign = 'center'; g.textBaseline = 'middle';
      g.fillText(this.mm.toFixed(1) + ' mm', 128, 38); this.tex.needsUpdate = true;
      this.label.position.copy(a).lerp(b, 0.5); this.label.visible = true;
    }
    this.app.menus && this.app.menus.refresh();
  }
  // keep markers and label the same size on screen at any zoom
  update() {
    if (!this.pts.length) return;
    const k = 1 / this.app.root.scale.x;
    this.marks.forEach((m) => m.scale.setScalar(k));
    this.label.scale.set(H * k * 256 / 72, H * k, 1);
    this.label.center.set(0.5, -0.4);
  }
}
