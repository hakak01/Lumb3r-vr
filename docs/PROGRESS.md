# PROGRESS (updated 2026-11-24, Phase C2 done except step 8 colours; next = C2 step 8, then Phase D)
Repo: github.com/hakak01/Lumb3r-vr. Spec: docs/SPEC.md. lumbar.glb 240 objects 380k tris; gaps.glb 162 objects 208k tris, 1.4 MB (total 588k ≤ 600k; 12k spare).
## Done (C2, all "rules (approx)"; numbers in docs/CHECKS.md §9, data/raw/c2_checks.json)
- Endplates (6): outer face = bony endplate, 0.46 mm centre → 1.0 mm AP rim / 0.78 lateral (mean 0.71); edge 3.5 mm inside disc outline; 70 % of disc face.
- Facet joints L3-4..L5-S1 L/R: cartilage fills bone gap (1.6–2.8 mm) minus 0.4 mm joint space, thins at margin; capsule 1 mm, recesses +3 mm sup/inf, open anteromedially ~125° (flavum).
- Epidural fat: posterior pads per level (19–26 mm long, depth 3.4–6.5), prelaminar bands L3, L4, S1; foraminal fat L3–L5 L/R (1.5–2.8 mm). New layer "epidural_fat" (on).
- Veins: anterior internal plexus L/R (z 1072→959, r 0.3–1.3, 35° body / 55° disc from midline), basivertebral L3–L5, 6 intervertebral veins to lumbar/asc. lumbar/iliolumbar; posterior plexus hidden.
- Nerves: L3/L4 dorsal ramus + medial branch over L4/L5 TP–SAP junction; L5 dorsal ramus in ala–SAP groove; SVN L3–L5 L/R (asc 12, desc 5 mm).
- Landmarks (42): Kambin's triangle, lateral recess, foraminal entry/middle/exit zones, axilla/shoulder of traversing roots.
- Viewer: Parts groups Medial branch / SVN, Epidural & foraminal fat, Vertebral venous plexus, Landmarks; "(Phase C)" entries gone. Disc-level filter includes small nerves.
- Fixed: "epidural" matched the dura colour rule (now \bdura); landmark names with "root" got nerve colour (landmarks keep their look).
## Decisions
- Endplate overlaps the outer ~0.4 mm of the disc (disc touches bone, median gap 0.3 mm). Ring apophysis 3.5 mm, recess 3 mm, capsule 1 mm: approx.
- Medial branch at the TP of the vertebra BELOW (L3 MB at L4), as for RF targets. Small nerves keep ≥0.1 mm (field) from bone/disc/ligament/neural parts.
- Second clearance field (F2) includes dura, roots, DRG, sleeves, spinal nerves (c2_build.neural_field).
## Known problems
- Step 8 colours NOT done: Bassett photo site blocked (403). Upload the 3 images to data/upload/ (links in the session report).
- Kambin L5-S1 large (403/472 mm², height 27–30 mm). Prelaminar band L5 missing. Foraminal fat L3 39–41 mm long (includes lateral recess).
- Venous channels touch bone in ~2 % of points at L5; SVNs touch PLL; medial branches lie 0.6–0.8 mm off bone, not on it. No S1/S2 foraminal fat.
- Carried over: S1 not the shortest root; S1/S2 nerves graze sacral foramina; facet L3-4 R/L angle 29/41°; not yet tested on a Quest.
## Next step
- User tests C2 (desktop + Quest 3) and uploads the Bassett photos → C2 step 8 (dura, arachnoid, epidural fat, vein colours in tissues.json cadaver/realistic). Then Phase D.
## Key files
- tools/c2_build.py (called by build_gaps.py) → c2_endplate, c2_facet, c2_fat, c2_veins, c2_nerves, c2_marks, c2_geom (mesh helpers).
- Rebuild: `python3 -I tools/build_gaps.py` (~50 s; needs data/raw/lumbar_raw.glb). Log data/raw/gaps_log.txt. Viewer: js/spine.js, menu2.js, looks.js, tissues.js; assets/look.json.
