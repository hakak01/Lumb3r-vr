# PROGRESS (updated 2026-11-24, Phase A1 done; next = Phase A2)
Repo: github.com/hakak01/Lumb3r-vr. Spec: docs/SPEC.md. Copied pipeline/viewer from Shoul3er-vr (no rig/wrap/ropes/move menu).
## Done (A1 = SPEC Phase A steps 1–3, 5–7)
- tools/region.py LUMBAR (whitelist, both sides, top of L1 z 1.134 → coccyx z 0.830); zsel.py whitelist mode, names "X (left)/(right)", level/side.
- tools/build_assets.py → assets/lumbar.glb (meshopt 2.4 MB) + manifest.json: 143 objects, 338,566 triangles (no decimation needed).
- Bone swap (ICP, mean/max mm): L1 0.74/3.5, L2 0.73/4.1, L3 0.75/6.9, L4 0.64/4.4, L5 0.78/4.8, hips 0.82, 0.74 → BodyParts3D; sacrum 4.07 → kept Z-Anatomy; coccyx no BP3D.
- All 9 bones watertight (tools/meshfix.py: islands removed, holes filled). Disc–endplate fit −0.2…+0.5 mm.
- Long ligaments, rotatores, dura, roots, ganglia, cord, vertebral skin cut at z 1.134; pelvic nerves cut at z 0.870 (femoral n. under inguinal lig., sciatic n. under piriformis).
- Subdivided once (≤0.3 mm): ALL, PLL, flava, interspinous, supraspinous, roots, cauda equina, ganglia, dura, discs, nuclei.
- docs/GAPS.md, docs/CHECKS.md (tools/check_lumbar.py + lgeom.py; numbers in data/raw/checks.json).
## Decisions
- World coordinates kept (Z-Anatomy, metres, +x left, +y posterior, +z up; GLB is y-up). Layers: bone, context_bone (L1, L2, hips, coccyx, discs L1–3), disc, neural, nerve, ligament_capsule, muscle, fascia_retinacula, attachment, artery, vein, skin.
- Midline objects keep exact names (source objects renamed "[source]" to avoid ".001").
- Sacrum level "S1" until A2 split; un-split multi-level objects have level "".
## Known problems (source)
- No dura, roots or DRG below L2–L3; cauda equina = schematic 0.5 mm curves; no traversing root course → Phase C rebuild.
- Ligamentum flavum 0.6 mm sheet and absent at L5–S1; supraspinous ends at L4; L3–4 nucleus 6 mm; L3–4 disc 6.4 mm; L5–S1 posterior > anterior height.
- Checks still unreliable: L5 pedicle (TP merges on axial cuts), L5–S1 foramen height; pedicle angles read 39–51° (local method) → re-measure on A2 parts.
## Next step
- Phase A2 (new session): SPEC step 4 split (bone parts, ligaments per level/side, roots/ganglia per level, annulus), re-export, update GAPS.md and CHECKS.md.
## Key files
- tools/region.py, zsel.py, build_assets.py, meshfix.py, boneswap.py, check_lumbar.py, lgeom.py · assets/lumbar.glb, manifest.json · data/raw/build_log.txt (git-ignored)
- Rebuild: put Z-Anatomy.zip → data/raw/zblend/, BodyParts3D STLs FMA13072-6, 16202, 16586-7 → data/raw/bp3d/…; `pip install bpy scipy`; `python3 -I tools/build_assets.py && python3 -I tools/check_lumbar.py`.
