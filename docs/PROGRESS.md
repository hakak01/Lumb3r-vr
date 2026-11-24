# PROGRESS (updated 2026-11-24, Phase A2 done; next = Phase B viewer)
Repo: github.com/hakak01/Lumb3r-vr. Spec: docs/SPEC.md. Pipeline/viewer copied from Shoul3er-vr (no rig/wrap/ropes/move menu).
## Done
- A1: LUMBAR region (both sides, top of L1 z 1.134 → coccyx 0.830), BodyParts3D bones L1–L5 + hips (ICP mean ≤0.82 mm), sacrum/coccyx Z-Anatomy, all bones watertight, curves → meshes, one Loop subdivision of soft structures, docs/GAPS.md, CHECKS.md.
- A2 (SPEC step 4): assets/lumbar.glb 240 objects, 380,463 triangles, 2.9 MB (assets/ 13 MB). Manifest adds "part" and "context".
  - L3/L4/L5 → 14 parts each, S1 → 7 parts + "Sacrum (rest)" (tools/bparts.py landmarks + regions, tools/bsplit.py exact booleans). Part volumes sum to the bone within 0.003 %; all parts closed.
  - Ligaments split at mid body / spinous / TP of L3, L4, L5, S1 (flavum: 4 mm below each lamina's upper edge, + left/right) → "<ligament> L4-5", context pieces L1-3, S1-5.
  - Roots/ganglia split by foramen: T12–L2 ventral/dorsal roots + ganglia (source objects); cauda equina → central bundle + "L3 root" … "S4 root" per side.
  - "Annulus fibrosus Lx-Ly" = disc − nucleus (exact); nucleus kept.
- CHECKS re-measured on parts (tools/check_lumbar.py; slicing bug fixed in lgeom.section).
## Decisions
- World coordinates kept (Z-Anatomy metres, +x left, +y posterior, +z up; GLB y-up). Layers: bone, context_bone (L1, L2, hips, coccyx, discs L1–3), disc, neural, nerve, ligament_capsule, muscle, fascia_retinacula, attachment, artery, vein, skin.
- Boolean fragments are joined to the part they touch (touching shell, exact); slivers <0.5 mm³ dropped; failed booleans retried with a 0.02–0.05 mm shift / no self-check.
- Root level = first disc (going down) whose mid-plane the root's foramen crossing lies above.
## Known problems (source; to fix in Phase C)
- No dura/arachnoid below mid-L3; no separate roots or DRG at L3–S1 (cauda equina = schematic tubes, no traversing course).
- Flavum 0.6 mm sheet, L5–S1 only a strip on L5; supraspinous ends at L4–5; L3–4 disc 6.4 mm and nucleus 6 mm; L5–S1 posterior > anterior height.
- Pedicle angles 31° (L3–L4) vs 20° (L5): order reversed vs literature (short parts). L3–4 facets differ 16° L/R.
## Next step
- Phase B (viewer) per SPEC; then C (gaps), D (kit).
## Key files
- tools/region.py, zsel.py, build_assets.py, split_a2.py, bparts.py, bsplit.py, meshfix.py, boneswap.py, check_lumbar.py, lgeom.py · assets/lumbar.glb, manifest.json · data/raw/a2_landmarks.json, build_log.txt (git-ignored)
- Rebuild: Z-Anatomy.zip → data/raw/zblend/; BodyParts3D STLs FMA13072-6, 16202, 16586-7 → data/raw/bp3d/assets/BodyParts3D_data/stl/; `pip install bpy scipy`; `python3 -I tools/build_assets.py` (~5 min) `&& python3 -I tools/check_lumbar.py`.
