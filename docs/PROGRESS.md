# PROGRESS (updated 2026-11-24, Phase B done; next = Phase C gaps)
Repo: github.com/hakak01/Lumb3r-vr. Spec: docs/SPEC.md. A1/A2 (assets): lumbar.glb 240 objects, 380k tris, 2.9 MB; parts per level/side (see git log).
## Done (Phase B viewer)
- assets/model.json: glb, gaps, title, center = L4-5 disc centre [0.00001, 0.99703, -0.00529] (glTF m) → origin; "foramen" = 6 foramen centres from Phase A (tools/viewer_marks.py).
- Starts in Realistic; skin, fat, muscles AND fascia hidden (posterior TLF would cover the spine). New layers disc, neural; looks/tissues dura, annulus, nucleus.
- Menu tabs: Layers · Parts (level L3…All, side, one toggle per part, ghost slider 0–60 %) · Cut (X-ray rim outlines, isolate, clip snaps) · Views · Search · Tools.
- Clip snaps: axial mid-disc (plane parallel to the disc, PCA normal) L3-4/L4-5/L5-S1; mid-pedicle L3/L4/L5/S1; sagittal midline and through each foramen (L/R). Slider/right stick move ±3 cm.
- Views: start, Surgeon (prone, back up, head to your left = you stand on the patient's left), MRI axial (from the feet, patient right on screen left, cut at mid-disc), MRI sagittal (from the left, anterior on screen left, midline cut), Foramen (lateral), Posterolateral 45° (parallel to the disc). Level chooser L3-4/L4-5/L5-S1.
- Fly-in: max zoom 40×, near plane 1 mm, dura/roots/discs/flavum/PLL double-sided; "Inside canal at L4-5" (20×) and "Inside left L5-S1 foramen" (25×). Left thumbstick zoom, Zoom ±, Life size (VR 1:1).
- Ruler (true mm at any zoom), info panel with level/side/source, labels for the chosen level (88 auto labels).
- Headless check: node tools/check_viewer.mjs <dir with node_modules/three> <out dir> (serve repo on :8766). No errors; ruler 38.07 = 38.07 mm.
## Decisions
- Disc frames measured in the viewer (PCA of annulus): tilt from vertical L3-4 6.4°, L4-5 13.3°, L5-S1 27.1°. Canal centre = midway back of disc/PLL ↔ flavum/arch; AP 16.9/18.3/15.4 mm (Phase A midline 21.0/20.4/19.5 measured to the lamina).
- S1 has no pedicle part: its mid-pedicle plane copies L5's pedicle offset from the disc above (marked "estimated").
- Hidden parts = s.hidden; the ghost slider shows them at 0–60 % and they stay pickable (solid parts win).
- Runtime foramen search from the pedicle parts failed (pedicle part boxes reach the midline), so Phase A values are baked into model.json.
## Known problems
- Source ligaments: interspinous/intertransverse/supraspinous are long opaque sheets that hide the spinous processes from behind (hide with Parts or X-ray).
- No facet joints, endplates, L3-S1 ganglia, dura below mid-L3 yet → shown greyed "(Phase C)". kit.js still the shoulder API (Phase D).
- New dura/annulus/nucleus colours are estimates (not photo-measured like the others). Not tested on a Quest yet.
## Next step
- Phase C (gaps.glb) per SPEC; then D (kit).
## Key files
- js/spine.js (landmarks, part groups), views.js, ruler.js, menu2.js (Parts/Cut/Views), anatomy.js (ghost, X-ray, snaps), main.js, xr.js · assets/model.json, look.json, tissues.json · tools/viewer_marks.py, check_viewer.mjs
- Phase A rebuild: Z-Anatomy.zip → data/raw/zblend/; BodyParts3D STLs → data/raw/bp3d/…/stl/; `pip install bpy scipy`; `python3 -I tools/build_assets.py && python3 -I tools/check_lumbar.py && python3 -I tools/viewer_marks.py`.
