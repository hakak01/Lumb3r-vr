# PROGRESS (updated 2026-11-24, Phase D + C2 step 8 done; next = user test, then Phase E)
Repo: github.com/hakak01/Lumb3r-vr. Spec: docs/SPEC.md. Kit guide: docs/KIT.md (future sessions read only KIT.md). lumbar.glb 380k + gaps.glb 208k tris.
## Done (Phase D)
- assets/levels.json (tools/build_levels.py): per L3-4/L4-5/L5-S1 disc height ant/mid/post, nucleus centre+size, dural sac area/width/AP, canal AP, foramen height/width L/R + centre, flavum thickness, facet angle+gap L/R, disc frame (centre, anterior, left, cranial, size), kit_measures (live-method baseline), _methods.
- js/kit.js rewritten for the lumbar model (was the shoulder kit): loadLumbar, where/show/hide/ghost/isolate by name or {level, side, part, group, layer}, setClip/clipPlane/clipLevel, discFrame, baseline, measureCanal, measureForamen, sectionArea, addMesh(bone) / removeMesh. js/measure.js = live measures.
- kit/v1 frozen: 35 files, 14.1 MB, from commit c6e9b0f (FILES.json sha256). Check: python3 -I tools/freeze_kit.py v1 --check.
- Headless tests on kit/v1: tools/check_kit.mjs (all API calls OK, 0 errors); tools/check_viewer.mjs on kit/v1/index.html.
- C2 step 8 (after kit/v1, so main only): cadaver colours from Bassett #219-5/#219-6/#33-5 (Data/*.jpg): dura #af9fa9, arachnoid #9985a1, epidural+foraminal fat #e2a96f, epidural veins (internal plexus, basivertebral, intervertebral) #bc594f. New tissues arachnoid, epidural_fat, epidural_vein; prelaminar band -> ligament.
## Decisions
- Baseline values (mm): disc ant/mid/post L3-4 6.7/6.4/6.1, L4-5 8.9/12.9/7.0, L5-S1 11.5/14.0/14.7; sac 202/236/217 mm²; canal AP 21.0/19.4/15.1; flavum 3.1; facets L/R 40.9/29.2°, 46.1/40.8°, 47.3/46.1°.
- Canal AP = midline, back of disc/PLL to first posterior wall. Flavum halves leave a 0.25 mm midline cleft, so the wall is lamina/spinous (L3-4, L4-5) or the L5-S1 interspinous ligament (15.1 mm; it lies 0.7 mm behind the sac).
- Live measures differ from Phase A/C methods (sac cut in the disc plane not perpendicular to canal: 186/223/231 vs 202/236/217 mm²; foramen rays through the Phase A centre). Disease modules compare with levels[d].kit_measures.
- Live disc frame (vertex PCA) is within 0.31 mm / 1.7° of levels.json (surface-sample PCA).
- Step 8: median of masked pixels x 1.17 (gain matching photo fat+skin to the cadaver palette). Epidural fat was removed in the photos, so their subcutaneous fat is used. Bassett veins are red-latex injected (look like arteries). Living view unchanged (embalmed photos cannot give living colours).
- Site URL is hakak01.github.io/Lumb3r-vr/kit/v1/ (SPEC says Lumbar-vr; the repo name is Lumb3r-vr). GitHub Pages must be on (main, root).
## Known problems
- Bassett photos are phone screenshots in Data/ (6 MB). data/upload on GitHub is an empty FILE, so a folder data/upload/ cannot be made until it is deleted.
- kit/v1 has the OLD colours; freeze kit/v2 after Phase E corrections.
- Carried over: L3-4 disc thin (6.4 mm), L5-S1 posterior > anterior, L3-4 nucleus small, facet L3-4 R/L 29/41°, L5 pedicle angle low, Kambin L5-S1 large, no S1/S2 foraminal fat, not yet tested on a Quest.
## Next step
- User tests main site (new cadaver colours) and kit/v1 on desktop + Quest 3, then Phase E corrections, then freeze kit/v2.
## Key files
- tools/build_levels.py (needs data/raw/checks.json, c1_checks.json, c2_checks.json, kit_live.json, lumbar_raw.glb, gaps_raw.glb), tools/freeze_kit.py, tools/check_kit.mjs (4th arg writes data/raw/kit_live.json).
- js/kit.js, js/measure.js, js/spine.js (disc frames, canal centre, GROUPS). Rebuild order: build_gaps.py → build_levels.py → check_kit.mjs … kit_live.json → build_levels.py.
