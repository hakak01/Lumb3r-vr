// Phase D headless test of the kit as ANOTHER repo would use it (not part of the site). Needs Playwright and a local
// three@0.170.0 copy (the CDN is blocked in the cloud session). Put this repo and the other repo side by side and
// serve their parent folder:  python3 -m http.server 8765 --bind 127.0.0.1   (from the folder that holds Lumb3r-vr/)
// Run:  node tools/check_kit.mjs <dir with node_modules/three> <kit path, e.g. /Lumb3r-vr/kit/v1/> [screenshot.png] [live.json]
// live.json: the kit's own measurements of the unchanged model (tools/build_levels.py copies them into levels.json).
import { createRequire } from 'module'; const { chromium } = createRequire(import.meta.url)('playwright');
import fs from 'fs';
const [S, KIT, SHOT, LIVE] = process.argv.slice(2), HOST = 'http://127.0.0.1:8765';
const page = `<!doctype html><html><head><script type="importmap">{ "imports": {
  "three": "https://cdn.jsdelivr.net/npm/three@0.170.0/build/three.module.js",
  "three/addons/": "https://cdn.jsdelivr.net/npm/three@0.170.0/examples/jsm/" } }</script></head>
<body style="margin:0"><canvas id="c" style="width:900px;height:700px"></canvas><script type="module">
import * as THREE from 'three';
import { loadLumbar, DISCS } from '${KIT}js/kit.js';
const renderer = new THREE.WebGLRenderer({ canvas: document.getElementById('c') }); renderer.setSize(900, 700);
renderer.toneMapping = THREE.NeutralToneMapping;
const scene = new THREE.Scene(), camera = new THREE.PerspectiveCamera(45, 900 / 700, 0.01, 50);
camera.position.set(0.18, 0.05, -0.2); camera.lookAt(0, 0, 0);
window.T = { THREE, renderer, scene, camera, DISCS };
window.kit = await loadLumbar({ renderer, scene, camera });
</script></body></html>`;
const b = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
const p = await b.newPage({ viewport: { width: 900, height: 700 } });
const errs = [];
p.on('console', (m) => { if (m.type() === 'error') errs.push(m.text().slice(0, 200)); });
p.on('pageerror', (e) => errs.push('pageerror: ' + e.message.slice(0, 300)));
await p.route('https://cdn.jsdelivr.net/npm/three@0.170.0/**', (r) => {
  const f = S + '/node_modules/three/' + r.request().url().split('three@0.170.0/')[1];
  r.fulfill({ body: fs.readFileSync(f), contentType: f.endsWith('.js') ? 'text/javascript' : 'application/octet-stream' });
});
await p.route(HOST + '/other-repo/test.html', (r) => r.fulfill({ body: page, contentType: 'text/html' }));
await p.goto(HOST + '/other-repo/test.html');
try { await p.waitForFunction(() => window.kit, null, { timeout: 120000 }); } catch (e) { console.log('LOAD FAILED\n' + errs.join('\n')); process.exit(1); }
const out = await p.evaluate(async () => {
  const { THREE, DISCS } = T, r = {}, V = (a) => new THREE.Vector3(...a);
  r.structures = kit.names().length; r.levels = Object.keys(kit.levels).join(',');
  r.get = !!kit.get('Dural sac') + '/' + kit.find('flavum L4-5').length;
  r.where = kit.where({ level: 'L4', side: 'left', layer: 'bone' }).map((s) => s.part).join(',');
  r.roots = kit.where({ group: 'Roots', side: 'right' }).length;
  kit.hide({ level: 'L4-5', group: 'Ligamentum flavum' }); r.hide = kit.get('Ligamentum flavum L4-5 (left)').meshes.every((m) => !m.visible);
  kit.show({ level: 'L4-5', group: 'Ligamentum flavum' }); r.show = kit.get('Ligamentum flavum L4-5 (left)').meshes.every((m) => m.visible);
  kit.isolate({ level: 'L4' }); r.isolate = kit.get('Dural sac').meshes.every((m) => !m.visible); kit.isolate(null);
  kit.ghost('L4 lamina (left)'); r.ghost = kit.get('L4 lamina (left)').meshes[0].material.opacity < 0.5; kit.ghost('L4 lamina (left)', false);
  const num = (o) => Object.fromEntries(Object.entries(o).filter(([, x]) => typeof x === 'number'));
  r.live = {};
  for (const d of DISCS) {
    const f = kit.discFrame(d), B = kit.levels[d].disc_frame, c = kit.measureCanal(d), L = kit.levels[d];
    r['frame ' + d] = `Δcentre ${(1000 * f.centre.distanceTo(V(B.centre))).toFixed(2)} mm, Δaxis ${(Math.acos(Math.min(1, f.cranial.dot(V(B.cranial)))) * 57.3).toFixed(1)}°`;
    r['canal ' + d] = `AP ${c.canal_ap_mm} (json ${L.canal_ap_mm}), sac ${c.sac_area_mm2} mm² ${c.sac_width_mm}x${c.sac_ap_mm} (json ${L.dural_sac.area_mm2} ${L.dural_sac.width_mm}x${L.dural_sac.ap_mm})`;
    r.live[d] = { canal: num(c), foramen: {}, foramen_soft: {} };
    for (const sd of ['left', 'right']) {
      const fo = kit.measureForamen(d, sd), fs = kit.measureForamen(d, sd, true), J = L.foramen[sd];
      r.live[d].foramen[sd] = num(fo); r.live[d].foramen_soft[sd] = num(fs);
      r[`foramen ${d} ${sd[0]}`] = `h ${fo.height_mm} w ${fo.width_mm} (soft w ${fs.width_mm}); json h ${J.height_max_mm}/${J.height_under_pedicle_mm} w ${J.width_mid_disc_mm}`;
    }
  }
  const at = V(kit.levels['L4-5'].disc_frame.centre).add(new THREE.Vector3(0.015, 0.02, -0.03));
  const scr = new THREE.Mesh(new THREE.CylinderGeometry(0.003, 0.003, 0.04), new THREE.MeshStandardMaterial({ color: 'silver' }));
  scr.position.copy(at); const s = kit.addMesh(scr, { bone: 'L4', name: 'Test screw', layer: 'implant', side: 'left' });
  const wp = (o) => { kit.root.updateMatrixWorld(true); return o.getWorldPosition(new THREE.Vector3()); };
  r.addMesh = `${s.bone}, offset ${(1000 * wp(scr).distanceTo(kit.toWorld(at))).toFixed(4)} mm, by level ${kit.where({ level: 'L4', layer: 'implant' }).length}`;
  kit.root.position.set(0.1, 1.2, -0.3); kit.root.rotation.y = 0.5; kit.update();
  r.moveRoot = `${(1000 * wp(scr).distanceTo(kit.toWorld(at))).toFixed(4)} mm`;
  kit.root.position.set(0, 0, 0); kit.root.rotation.y = 0; kit.update();
  r.rootOrigin_mm = (1000 * kit.toWorld(kit.center).length()).toFixed(4);
  kit.clipLevel('L4-5'); r.clip = kit.anatomy.clip.mode; kit.setClip('off');
  const sa = kit.sectionArea('Dural sac', V(kit.levels['L4-5'].disc_frame.centre).add(new THREE.Vector3(0, 0, -0.03)), new THREE.Vector3(0, 1, 0));
  r.sectionArea = sa && sa.area_mm2;
  r.pick = (() => { T.camera.updateMatrixWorld(); const rc = new THREE.Raycaster(); rc.setFromCamera(new THREE.Vector2(0, 0), T.camera); const h = kit.pick(rc); return h ? h.struct.name : null; })();
  kit.removeMesh('Test screw'); r.removed = !kit.get('Test screw') && !scr.parent;
  await kit.setView('realistic'); r.view = kit.realism.view;
  kit.update(); T.renderer.render(T.scene, T.camera);
  return r;
});
if (LIVE) fs.writeFileSync(LIVE, JSON.stringify(out.live, null, 1)); delete out.live;
for (const [k, v] of Object.entries(out)) console.log(k.padEnd(18), v);
if (SHOT) { await p.waitForTimeout(500); await p.locator('#c').screenshot({ path: SHOT }); console.log('screenshot', SHOT); }
console.log('errors', errs.length ? errs.slice(0, 8).join('\n') : 'none');
await b.close();
