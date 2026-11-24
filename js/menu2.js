// Lumbar tabs of the wrist menu: Parts (hide by level/side/part), Cut (X-ray, isolate, clip snaps), Views.
import { GROUPS, PLANNED, VERTS, DISCS } from './spine.js';
import { VIEWS } from './views.js';

const LEVELS = [...VERTS, ...DISCS, 'All'], dash = (s) => s.replace('-', '–');
const ends = (L) => { const [a, b] = L.split('-'); return [a, /^\d$/.test(b) ? 'L' + b : b]; };   // 'L4-5' -> L4, L5

// Does a structure belong to the chosen level / side? Roots of a disc level = the exiting and the traversing root.
export function inLevel(s, L) {
  if (L === 'All' || !s.level || s.level === L) return true;
  return L.includes('-') && s.layer === 'neural' && /(^| )root|ganglion/.test(s.part) && ends(L).includes(s.level);
}
const inSide = (s, sd) => sd === 'both' || !s.side || s.side === 'mid' || s.side === sd;

export const LumbarTabs = {
  partMatches(test) { return this.A.structs.filter((s) => test(s) && inLevel(s, this.pLevel) && inSide(s, this.pSide)); },

  tab_parts(p) {
    const A = this.A; let y = 84;
    this.pLevel ??= 'All'; this.pSide ??= 'both';
    p.text(20, y + 10, 'Level', { size: 19, color: '#9aa' }); y += 24;
    LEVELS.forEach((l, i) => p.button(15 + i * 77.5, y, 72, 50, dash(l), () => { this.pLevel = l; A.apply(); this.refresh(); },
      { active: this.pLevel === l, size: 20 }));
    y += 58;
    [['left', 'Left'], ['right', 'Right'], ['both', 'Both sides']].forEach(([k, t], i) =>
      p.button(15 + i * 205, y, 200, 48, t, () => { this.pSide = k; this.refresh(); }, { active: this.pSide === k, size: 21 }));
    y += 60;
    const pct = () => 'Hidden parts shown at ' + Math.round(A.hideGhost * 100) + '%';
    p.text(20, y + 8, pct(), { size: 19, color: '#bcd' }); const t = p.items[p.items.length - 1]; y += 20;
    p.slider(15, y, 610, 44, A.hideGhost / 0.6, (v) => { A.setHideGhost(v * 0.6); t.label = pct(); });
    y += 54;
    let i = 0;
    for (const [label, test] of GROUPS) {
      const ss = this.partMatches(test);
      if (!ss.length && !(PLANNED.has(label) && this.pLevel !== 'S1')) continue;
      const x = 15 + (i % 2) * 307, yy = y + Math.floor(i / 2) * 48; i++;
      if (!ss.length) { p.button(x, yy, 302, 42, label + ' (Phase C)', null, { size: 18, color: '#444' }); continue; }
      const on = ss.some((s) => !s.hidden && A.layers[s.layer] && A.layers[s.layer].on);
      p.button(x, yy, 302, 42, (on ? '✓ ' : '    ') + label + ' (' + ss.length + ')', () => {
        for (const s of ss) { s.hidden = on; if (!on) A.layers[s.layer].on = true; if (on && A.selected === s) A.selected = null; }
        A.apply(); this.refresh();
      }, { active: on, size: 18 });
    }
  },

  tab_cut(p) {
    const A = this.A, S = this.app.spine, c = A.clip; let y = 84;
    const snap = (key, mode, pt, n, flip) => { this.snapKey = key; A.snapClip(mode, pt, n, flip); this.refresh(); };
    const sb = (x, w, key, label, f) => p.button(x, y, w, 46, label, f, { active: c.frame && this.snapKey === key, size: 19 });
    p.text(20, y + 10, 'See-through', { size: 22, bold: true }); y += 28;
    p.button(15, y, 200, 50, 'X-ray', () => { A.setXray(!A.xray); this.refresh(); }, { active: A.xray, size: 21 });
    p.button(220, y, 200, 50, 'Isolate selected', () => { if (A.selected) A.isolate(A.selected); this.refresh(); },
      { active: !!A.isolated, size: 20 });
    p.button(425, y, 200, 50, 'Show all', () => { A.showAll(); this.refresh(); }, { size: 20 });
    y += 66;
    p.text(20, y + 10, 'Cut plane', { size: 22, bold: true }); y += 28;
    ['off', 'axial', 'sagittal', 'coronal'].forEach((m, i) =>
      p.button(15 + i * 154, y, 148, 48, m[0].toUpperCase() + m.slice(1), () => { this.snapKey = null; A.setClip(m); this.refresh(); },
        { active: c.mode === m && !c.frame, size: 21 }));
    y += 58;
    p.text(20, y + 8, 'Axial at mid-disc (parallel to the disc)', { size: 18, color: '#9aa' }); y += 20;
    DISCS.forEach((d, i) => sb(15 + i * 205, 200, 'd' + d, dash(d), () => { const F = S.disc[d]; snap('d' + d, 'axial', F.o, F.n, false); }));
    y += 54;
    p.text(20, y + 8, 'Axial at mid-pedicle (S1 estimated from L5)', { size: 18, color: '#9aa' }); y += 20;
    VERTS.forEach((v, i) => sb(15 + i * 154, 148, 'p' + v, v, () => { const P = S.pedicleSnap(v); snap('p' + v, 'axial', P.p, P.n, false); }));
    y += 54;
    p.text(20, y + 8, 'Sagittal: midline, or through a foramen', { size: 18, color: '#9aa' }); y += 20;
    sb(15, 610, 'mid', 'Midline (keeps the right half)', () => { const F = S.disc['L4-5']; snap('mid', 'sagittal', F.o, F.l, true); });
    y += 52;
    for (const sd of ['left', 'right']) {
      p.text(20, y + 23, sd === 'left' ? 'Left' : 'Right', { size: 19 });
      DISCS.forEach((d, i) => sb(110 + i * 172, 166, sd + d, dash(d), () => {
        const F = S.disc[d]; snap(sd + d, 'sagittal', S.foramen[d + sd].c, F.l, sd === 'left');
      }));
      y += 52;
    }
    y += 6;
    p.slider(15, y, 460, 50, c.pos, (v) => { c.pos = v; A.updateClip(); });
    p.button(490, y, 135, 50, 'Flip', () => { c.flip = !c.flip; A.updateClip(); this.refresh(); }, { active: c.flip });
    y += 58;
    p.text(20, y + 8, c.frame ? 'Slider / right thumbstick: move ±3 cm' : 'Right thumbstick also moves the plane.', { size: 18, color: '#9aa' });
  },

  tab_views(p) {
    const V = this.app.views, R = this.app.ruler, xr = this.app.inXR(); let y = 84;
    p.text(20, y + 10, 'Level for views', { size: 19, color: '#9aa' }); y += 24;
    DISCS.forEach((d, i) => p.button(15 + i * 205, y, 200, 46, dash(d), () => { V.level = d; this.refresh(); }, { active: V.level === d, size: 21 }));
    y += 58;
    p.text(20, y + 10, 'Views', { size: 22, bold: true }); y += 28;
    VIEWS.forEach(([k, t], i) => p.button(15 + (i % 2) * 307, y + Math.floor(i / 2) * 56, 302, 50, t, () => V.apply(k),
      { active: V.name === k, size: 21 }));
    p.button(322, y + 112, 302, 50, 'Reset view', () => V.apply('start'), { size: 21 });
    y += 176;
    p.text(20, y + 10, 'Fly in (put your head inside)', { size: 22, bold: true }); y += 28;
    p.button(15, y, 302, 52, 'Inside canal at L4–5', () => V.apply('canal'), { active: V.name === 'canal', size: 20 });
    p.button(322, y, 302, 52, 'Inside left L5–S1 foramen', () => V.apply('inForamen'), { active: V.name === 'inForamen', size: 19 });
    y += 68;
    p.text(20, y + 10, 'Zoom' + (xr ? '  (now ×' + this.app.root.scale.x.toFixed(1) + ')' : ''), { size: 22, bold: true }); y += 28;
    p.button(15, y, 200, 52, 'Zoom −', () => { V.zoom(1 / 1.5); this.refresh(); });
    p.button(220, y, 200, 52, 'Life size', () => { V.lifeSize(); this.refresh(); });
    p.button(425, y, 200, 52, 'Zoom +', () => { V.zoom(1.5); this.refresh(); });
    y += 58;
    p.text(20, y + 8, xr ? 'Left thumbstick zooms; squeeze both grips to grab-zoom.' : 'Mouse wheel / pinch zooms.', { size: 18, color: '#9aa' });
    y += 34;
    p.text(20, y + 10, 'Ruler', { size: 22, bold: true }); y += 28;
    p.button(15, y, 302, 52, R.on ? 'Ruler ON (tap 2 points)' : 'Ruler off', () => { R.set(!R.on); this.refresh(); }, { active: R.on, size: 20 });
    p.button(322, y, 302, 52, 'Clear ruler', () => { R.clear(); this.refresh(); }, { size: 20 });
    y += 62;
    p.text(20, y + 12, R.mm != null ? 'Distance: ' + R.mm.toFixed(1) + ' mm' : R.on ? (R.pts.length ? 'Tap the second point' : 'Tap the first point') : '',
      { size: 26, bold: true, color: '#ffd23f' });
    y += 40;
    if (xr) p.button(15, y, 610, 56, 'Exit VR / MR', () => this.app.exitXR(), { active: true, color: '#b03030' });
  },
};
