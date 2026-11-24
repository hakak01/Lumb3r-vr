// Phase B headless check of the viewer (not part of the site). Needs Playwright and a local three@0.170.0
// (the CDN is blocked in the cloud session). Serve this repo:  python3 -m http.server 8766 --bind 127.0.0.1
// Run:  node tools/check_viewer.mjs <dir with node_modules/three> <out dir for screenshots>
import { createRequire } from 'module'; const { chromium } = createRequire(import.meta.url)('playwright');
import fs from 'fs';
const [S, OUT] = process.argv.slice(2), HOST = 'http://127.0.0.1:8766';
const b = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
const p = await b.newPage({ viewport: { width: 1000, height: 760 } });
const errs = [];
p.on('console', (m) => { if (m.type() === 'error' && !/404|gaps/.test(m.text())) errs.push(m.text().slice(0, 200)); });
p.on('pageerror', (e) => errs.push('pageerror: ' + e.message.slice(0, 300)));
await p.route('https://cdn.jsdelivr.net/npm/three@0.170.0/**', (r) => {
  const f = S + '/node_modules/three/' + r.request().url().split('three@0.170.0/')[1];
  r.fulfill({ body: fs.readFileSync(f), contentType: f.endsWith('.js') ? 'text/javascript' : 'application/octet-stream' });
});
await p.goto(HOST + '/index.html');
try { await p.waitForFunction(() => window.app && app.menus && app.realism && app.realism.view === 'realistic', null, { timeout: 180000 }); }
catch (e) { console.log('LOAD FAILED\n' + errs.join('\n')); process.exit(1); }
const out = await p.evaluate(() => {
  const A = app.anatomy, S = app.spine, r = {}, mm = (v) => v.toArray().map((x) => +(x * 1000).toFixed(1));
  r.structs = A.structs.length; r.view = app.realism.view;
  r.layersOff = Object.entries(A.layers).filter(([, L]) => !L.on).map(([k]) => k).join(',');
  for (const d of ['L3-4', 'L4-5', 'L5-S1']) {
    const F = S.disc[d], c = S.canal[d];
    r[d] = { centre: mm(F.o), tiltFromVertical: +(Math.acos(F.n.y) * 180 / Math.PI).toFixed(1), nz: +F.n.z.toFixed(3), sizeWHD: F.size.map((x) => +(x * 1000).toFixed(1)),
      canalAP: +(c.ap * 1000).toFixed(1), canal: mm(c.c), forL: mm(S.foramen[d + 'left'].c), forR: mm(S.foramen[d + 'right'].c) };
  }
  r.pedS1 = mm(S.pedicleSnap('S1').p); r.pedL5 = mm(S.pedicleSnap('L5').p);
  // parts: hide left L4 lamina, ghost slider
  const lam = A.byName.get('L4 lamina (left)'); lam.hidden = true; A.apply(); r.hidden = lam.meshes.every((m) => !m.visible);
  A.setHideGhost(0.4); r.ghost = lam.meshes[0].visible && +lam.meshes[0].material.opacity.toFixed(2); A.setHideGhost(0); lam.hidden = false; A.apply();
  // ruler: two known points
  const R = app.ruler; app.views.apply('start'); app.root.updateMatrixWorld(true);
  const a = S.disc['L4-5'].o.clone(), b2 = S.disc['L5-S1'].o.clone();
  R.add(app.root.localToWorld(a.clone())); R.add(app.root.localToWorld(b2.clone()));
  r.ruler = [+R.mm.toFixed(2), +(a.distanceTo(b2) * 1000).toFixed(2)]; R.clear();
  r.labels = A.labels.items.length;
  return r;
});
console.log(JSON.stringify(out, null, 0).replace(/\},"/g, '},\n"'));
const hide = (h) => p.evaluate((h) => { for (const id of ['menuCanvas', 'infoCanvas', 'top', 'menuBtn', 'credit']) document.getElementById(id).style.display = h ? 'none' : ''; }, h);
const snap = async (name, js) => { await p.evaluate(js); await p.waitForTimeout(600); await p.screenshot({ path: `${OUT}/${name}.png` }); };
await hide(true);
for (const v of ['start', 'surgeon', 'mriAxial', 'mriSag', 'foramen', 'kambin', 'canal', 'inForamen'])
  await snap('view_' + v, `app.views.apply('${v}')`);
await snap('xray', `app.views.apply('start'); app.anatomy.setXray(true)`);
await snap('pedicleL4', `app.anatomy.setXray(false); const P = app.spine.pedicleSnap('L4'); app.anatomy.snapClip('axial', P.p, P.n); app.views.apply('mriAxial'); const Q = app.spine.pedicleSnap('L4'); app.anatomy.snapClip('axial', Q.p, Q.n)`);
await snap('labels', `app.anatomy.setClip('off'); app.views.apply('start'); app.menus.pLevel = 'L4'; app.anatomy.labels.set(true)`);
await hide(false);
for (const t of ['parts', 'cut', 'views', 'layers']) { await p.evaluate((t) => { app.menus.tab = t; app.menus.refresh(); }, t);
  await p.locator('#menuCanvas').screenshot({ path: `${OUT}/menu_${t}.png` }); }
console.log(errs.length ? 'ERRORS\n' + errs.join('\n') : 'no errors');
await b.close();
