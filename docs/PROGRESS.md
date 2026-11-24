# PROGRESS (updated 2026-11-24, Phase C1 done; next = Phase C2)
Repo: github.com/hakak01/Lumb3r-vr. Spec: docs/SPEC.md (Phase C replaced by C1/C2 text). lumbar.glb 240 objects 380k tris; gaps.glb 60 objects 146k tris, 0.9 MB (total 526k ≤ 600k).
## Done (C1: neural parts + ligamentum flavum, all "rules (approx)")
- Canal measured in slices ⟂ its centreline every 1 mm (z 1128 → 878), polar wall distances (tools/c1_canal.py).
- Dural sac z 1128 → rounded tip z 943 (upper S2, 11 % down S2); arachnoid 0.2 mm inside; filum internum conus (z 1055) → tip; dural filum → back of coccyx.
- Sac area at mid-disc L2-3/L3-4/L4-5/L5-S1: 176/202/236/217 mm² (all >100). Margins: front 1.0, back 0.8 (3.0 at midline fat pad), sides 2.5 mm; width cap 17 mm.
- Roots L3–S2 L/R: ventral + dorsal + DRG + dural sleeve + spinal nerve (50 parts). Template = Z-Anatomy L2 (ventral r 0.47, dorsal 0.535, ganglion 5.1×2.7 mm) scaled to DRG width. Leave sac at z 1065/1029/995/964/951.
- DRG L3/L4 medial zone, L5 lateral zone, S1/S2 in the sacral canal at their foramen opening. Narrowest gap to bone/disc/ligament 0.76 mm (S2); lumbar ≥0.93.
- Flavum L3-4, L4-5, L5-S1 L/R solid, 3.09 mm at half length; L5-S1 reaches S1. Supraspinous absent at L5-S1 marked normal (GAPS).
- 21 old parts renamed "(old)", hidden (old roots L3–S4, central cauda bundle, old flavum sheets): tools/c1_old.py (run once after build_assets).
- Viewer: Parts groups Roots/Ganglia/Spinal nerves/Cord & filum/Old (superseded); "(Phase C)" now only Facet joint, Endplate; info source "rules (approx)"; manifest "hidden" honoured; Show all keeps old parts hidden.
## Decisions
- Z-Anatomy "Spinal dura" is a sheath on the cord/conus (2 mm wide at z 1066), not a sac: the new sac starts at the region top and contains it (no join at mid-L3 possible).
- S1 DRG 7.0×12 mm, S2 5.0×8 mm: approx (SPEC gives no numbers). DRG axis lumbar (lat, -0.35 ant, -0.45 down); sacral along the canal toward the opening.
- Spinal nerves end on the nearest Z-Anatomy plexus nerve (L3 obturator, L4/L5 nerve to quadratus femoris, S1/S2 old root end).
## Known problems
- S1 not the shortest root (27.4 mm vs L4 25.6); S1/S2 spinal nerves graze bone in the sacral foramina (−0.4 mm); S1/S2 DRGs partly overlap the tapering sac tip.
- Sac above L2 slightly bumpy (context level). Arachnoid not in sleeves. S3–S5 roots now only as hidden "(old)". Lumbosacral trunk still missing.
- Not yet tested on a Quest. Colours of new dura/arachnoid = old dura estimate (C2 step 8).
## Next step
- User tests C1 in the viewer; then Phase C2 (endplates, facet joints, epidural fat, venous plexus, medial branches, sinuvertebral nerves, landmarks, photo colours).
## Key files
- tools/build_gaps.py (runs c1_canal, c1_flavum, c1_dura, c1_space, c1_cauda, c1_roots), c1_old.py · assets/gaps.glb, gaps.json · log data/raw/gaps_log.txt, numbers data/raw/c1_checks.json
- Rebuild: `python3 -I tools/build_gaps.py` (~40 s; needs data/raw/lumbar_raw.glb). Viewer: js/spine.js (groups), menu2.js, anatomy.js, menu.js.
