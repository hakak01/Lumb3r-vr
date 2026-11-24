# KIT — normal lumbosacral spine for simulators (kit/v1, frozen; read only this file)
**Load from the site, never copy:** `https://hakak01.github.io/Lumb3r-vr/kit/v1/` (repo is Lumb3r-vr, not Lumbar-vr). Full viewer: `.../kit/v1/index.html`. kit/v1 is never edited (`python3 -I tools/freeze_kit.py v1 --check`); changes go to kit/v2. Headless tests: clone this repo beside yours, serve the parent folder, import `/Lumb3r-vr/kit/v1/js/kit.js` (see tools/check_kit.mjs; the CDN is blocked in the cloud, so route three to a local three@0.170.0).
```html
<script type="importmap">{ "imports": { "three": "https://cdn.jsdelivr.net/npm/three@0.170.0/build/three.module.js",
  "three/addons/": "https://cdn.jsdelivr.net/npm/three@0.170.0/examples/jsm/" } }</script>
<script type="module">
import * as THREE from 'three';
import { loadLumbar, DISCS, VERTS } from 'https://hakak01.github.io/Lumb3r-vr/kit/v1/js/kit.js';
const kit = await loadLumbar({ renderer, scene, camera, parent, view: 'present', lights: true, onProgress: (f) => {} });
renderer.setAnimationLoop(() => { kit.update(); renderer.render(scene, camera); });   // kit.update() every frame
</script>
```
**Coordinates.** File coordinates = the glTF files = Z-Anatomy world in metres: **+x patient's left, +y up, +z anterior**. Every point/axis a kit function takes or returns is in file coordinates (THREE.Vector3); sizes are mm. `kit.root` (a Group you may move/rotate/scale, e.g. to place in XR) has the L4-5 disc centre `kit.center` at its origin. `kit.toWorld(p)` / `kit.fromWorld(p)` convert file ↔ scene world.
**Structures** (names in assets/manifest.json + gaps.json; 402): `kit.names(layer)`, `kit.get(name)` → `{name, layer, level, side, part, approx, source, node, meshes, hidden, ghost}`, `kit.find('flavum L4-5')`.
- Levels: `L3 L4 L5 S1` (bones, roots), discs `L3-4 L4-5 L5-S1`; context `L1 L2 Co`…; side `left|right|mid`. Bones are split into parts: body, pedicle, pars interarticularis, lamina, superior/inferior articular process, transverse process, spinous process (S1: ala, rest of sacrum), e.g. `L4 pedicle (left)`.
- Layers: `kit.layers()` (bone, context_bone, disc, fat, ligament_capsule, neural, nerve, epidural_fat, artery, vein, muscle, fascia_retinacula, skin, landmark, attachment). Groups (Parts menu): `kit.groups()` e.g. 'Roots', 'Ganglia', 'Facet joint', 'Endplate', 'Ligamentum flavum', 'Dura'.
- Filter `q = {level, side, part, group, layer, name: /re/}` (level/side/layer may be arrays): `kit.where(q)`.
- `kit.show(x, on)`, `kit.hide(x)`, `kit.ghost(x, on)`, `kit.isolate(x | null)`, `kit.showAll()`, `kit.select(name)`; x = name, array of names, or a filter q. `kit.setHiddenOpacity(0..0.6)`, `kit.setLayer(layer, on, opacity)`, `kit.labels(on)`, `kit.pick(raycaster)` → `{struct, point}`, `await kit.setView('present'|'realistic'|'cadaver')`.
**Clip** (one plane; the normal side is kept): `kit.setClip('axial'|'sagittal'|'coronal'|'off', pos 0..1, flip)`, `kit.clipPlane(point, normal, flip)`, `kit.clipLevel('L4-5' | 'L4', flip)` = axial cut through a disc or mid-pedicle.
**Levels.** `kit.levels[d]` = assets/levels.json (read-only baseline, `kit.baseline(d)` returns a copy you may change). Per disc: `disc_height_mm {anterior, middle, posterior}`, `nucleus_centre`, `nucleus_size_mm`, `dural_sac {area_mm2, width_mm, ap_mm}`, `canal_ap_mm`, `foramen {left/right: height_max_mm, height_under_pedicle_mm, width_mid_disc_mm, centre}`, `flavum_thickness_mm {left, right}`, `facet_angle_deg {left, right}`, `disc_frame {centre, anterior, left, cranial, size_mm}`, `kit_measures` (below). Methods: `_methods` in the file. L4-5 example: disc 8.9/12.9/7.0 mm, sac 236 mm², canal AP 19.4 mm, flavum 3.1 mm, facets L 46.1° R 40.8°.
**Live measures** (run on the current meshes, so they see your changes; hidden parts count):
- `kit.discFrame(d)` → `{centre, cranial, left, anterior, size_mm}` (within 0.4 mm / 2° of levels.json).
- `kit.measureCanal(d)` → `{canal_ap_mm, sac_area_mm2, sac_width_mm, sac_ap_mm, front, back}` (midsagittal AP from back of disc/PLL to first posterior wall; sac cut in the disc plane).
- `kit.measureForamen(d, side, soft)` → `{height_mm, width_mm, up_mm, down_mm, front_mm, back_mm, centre}` (rays through the Phase A foramen centre; soft = also stop at flavum/facet cartilage/capsule).
- `kit.sectionArea(name, point, normal)` → `{area_mm2, width_mm, ap_mm}` of any closed mesh.
- Compare a changed model with `kit.levels[d].kit_measures` (same live method on the unchanged model), not with the Phase A/C values.
**Your own meshes** (implants, prolapse, osteophyte): build in file coordinates, then `kit.addMesh(mesh, {name, layer: 'implant', bone: 'L4' | 'L4 pedicle (left)', level, side, part})` → attached to that bone's node (stays fixed to it if you move the bone node or kit.root) and becomes a structure (works with where/show/ghost/pick). `kit.removeMesh(name)`. To change an existing structure, edit `kit.get(name).meshes[i].geometry` (then `geometry.computeBoundingSphere()`) and call the live measures again.
**Files in kit/v1:** index.html (viewer), js/*.js, assets/{lumbar.glb, gaps.glb, manifest.json, gaps.json, model.json, levels.json, look.json, tissues.json}, assets/tex/*.ktx2, assets/env/*.hdr, ATTRIBUTION.md (CC BY-SA 4.0: Z-Anatomy, BodyParts3D), FILES.json (sha256). three@0.170.0 only.
