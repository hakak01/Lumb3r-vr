# CHECKS — measurements vs ANATOMY CHECKS (docs/SPEC.md), updated after Phase C1
Measured by `python3 -I tools/check_lumbar.py` on data/raw/lumbar_raw.glb (numbers: data/raw/checks.json). Nothing was changed to fit.
One adult male body (Z-Anatomy soft tissue; BodyParts3D L1–L5 and hip bones). **FLAG** = big difference from the reference.
Frames: disc axis = its thinnest direction (PCA); vertebra axis = mean of the discs above and below.
A2 note: a slicing bug (rows outside the cut window could fill a whole row) was fixed; A1 values below were re-measured.

## 0. Phase A2 split integrity
| Bone | Parts | Sum of part volumes vs bone | Open / non-manifold edges | Dropped slivers |
|---|---|---|---|---|
| L3 / L4 / L5 | 14 each | +0.001 / +0.002 / +0.003 % | 0 | 0.18 / 0.04 / 0.32 mm³ |
| Sacrum | 8 (S1 ×7 + rest) | −0.002 % | 0 (5 edges closed) | 0.06 mm³ |
- Part volumes (cm³, R/L): L4 body 36.9, pedicle 0.79/0.79, pars 0.80/0.90, lamina 1.04/1.00, SAP 1.56/1.30, IAP 1.04/0.99, TP 1.07/0.84, spinous 2.66. L5: body 41.6, pedicle 1.14/1.04, pars 0.40/0.54, TP 3.59/2.91. S1: body 39.7, ala 27.8/27.8, SAP 1.36/1.24, lamina 1.64/1.64; rest 79.9.
- Annulus = disc − nucleus: volume check within 0.001 cm³ at every level.

## 1. Disc height (mm; disc / bone-to-bone gap; rays along the disc axis, midline, at 10 %, 50 %, 90 % of AP depth)
| Level | Anterior | Middle | Posterior | Reference (Zhou 2000; Asian range 2018) | Result |
|---|---|---|---|---|---|
| L3–4 | 6.7 / 6.4 | 6.4 / 6.8 | 6.1 / 6.3 | 11.6 ± 1.8; 7.4–13.3 | **FLAG: thin** |
| L4–5 | 8.9 / 9.2 | 12.9 / 12.6 | 7.0 / 7.1 | 11.3 ± 2.1; 7.8–14.6 | OK; anterior > posterior |
| L5–S1 | 11.5 / 11.7 | 14.0 / 14.0 | 14.7 / 15.1 | 10.7 ± 2.1; 7.1–13.1 | **FLAG: posterior > anterior**; middle slightly high |
- Disc–endplate fit −0.2 to +0.5 mm. Nucleus: L3–4 6.2 mm sphere (**FLAG** small), L4–5 12.3 mm, L5–S1 13.9 mm.

## 2. Pedicle (on the separate pedicle part; axial cut at its mid-height; centreline from front to back quarter of the section)
| Level | Width R / L (mm) | Range ±2 mm height | Transverse angle R / L | Reference | Result |
|---|---|---|---|---|---|
| L3 | 8.8 / 8.0 | 8.1–8.8 / 7.0–8.1 | 32.5° / 30.8°, medial | 7.2 ± 0.87 (Mohanty); >7 (Acharya); ~7.8 (Silverstein) | width OK; angle high |
| L4 | 9.4 / 9.3 | 7.3–10.2 / 7.6–9.8 | 30.9° / 32.4°, medial | ~8.8 | width OK; angle high |
| L5 | 11.0 / 11.6 | 9.9–11.2 / 10.5–11.7 | 19.3° / 21.1°, medial | ~9.7; ~30° (most medial at L5) | width OK; **FLAG: angle order reversed** (L5 should be the most medial) |
- All medially directed and >7 mm (Acharya). Caveats: the pedicle part is only 5–7 mm long, so the angle is a short-baseline estimate; the L5 lateral border is the TP cut (body half-width), not a cortex.
- Interpedicular distance L3 24.8, L4 25.8, L5 30.5 mm.

## 3. Foramen (parasagittal cut through the upper pedicle centre, l ≈ ±17–21 mm)
| Level | Max height R / L (Hasegawa) | Height under the pedicle | AP width at mid-disc | Widest | Result |
|---|---|---|---|---|---|
| L3–4 | 18.6 / 18.5 | 18.6 / 18.5 | 11.7 / 10.1 | 18.8 / 19.2 | OK (>15; width ref ~7.5) |
| L4–5 | 19.4 / 19.6 | 16.5 / 18.2 | 10.4 / 11.8 | 14.0 / 15.9 | OK (width ref ~8.5) |
| L5–S1 | 17.9 / 17.0 | 11.3 / 11.1 | 8.8 / 8.5 | 16.3 / 16.9 | OK (width ref ~8.7). Under the L5 pedicle the S1 SAP tip rises to 5 mm above mid-disc. |
- Posterior disc height (10 % inside the posterior margin): 6.1 / 7.0 / 14.7 mm, all above Hasegawa's 4 mm.

## 4. Dorsal root ganglia (Phase C1, gaps.glb; numbers: data/raw/c1_checks.json)
Shape = Z-Anatomy "L2 spinal ganglion" (5.1 × 2.7 mm) scaled to the reference size. Zone = thirds between the medial and lateral pedicle walls.
| DRG | Width × length (mm) | Reference | Position (R / L) | Reference | Narrowest gap R / L (mm) |
|---|---|---|---|---|---|
| L3 | 5.1 × 7.0 | 4.9–5.3 × ~7 | medial zone, 3.5 / 3.5 mm below the pedicle | medial zone | 1.80 / 2.05 |
| L4 | 5.95 × 8.5 | 5.8–6.1 × ~8.5 | medial zone, 7.5 / 4.0 mm below the pedicle | medial zone | 1.48 / 1.40 |
| L5 | 6.35 × 11.5 | 6.2–6.5 × ~11.5 | lateral zone, 4.5 / 4.5 mm below the pedicle | lateral zone | 1.70 / 1.83 |
| S1 | 7.0 × 12.0 (approx, "largest") | no number | in the sacral canal, 5.2 mm from the axis, at the S1 foramen opening | often in the canal | 1.47 / 1.54 |
| S2 | 5.0 × 8.0 (approx) | no number | in the sacral canal at the S2 foramen opening | — | 1.36 / 1.37 |
- Sizes are inputs (scaled to the reference), so they match by construction; positions come from free space in this model's foramina.

## 5. Canal and dural sac at mid-disc
| Level | Canal area (mm²) | Canal AP (mm) | Dural sac area (mm²) | Sac width × AP (mm) | Result |
|---|---|---|---|---|---|
| L2–3 | – | – | 176 | 19.8 × 13.2 | OK (>100) |
| L3–4 | 412 | 21.0 | 202 | 17.0 × 16.2 | OK |
| L4–5 | 439 | 20.4 | 236 | 17.1 × 16.2 | OK |
| L5–S1 | 573 | 19.5 | 217 | 17.0 × 13.7 | OK |
- Sac = canal wall minus 1.0 mm in front, 0.8 mm (3.0 mm at the posterior midline fat pad) behind, 2.5 mm at the sides; width capped at 17 mm (approx). Cut perpendicular to the canal axis.
- Sac tip z 943.1 = upper S2: 1.8 mm below the S1 foramen opening (z 944.9), S2 opening z 929.1 → 11 % down S2. OK (Senoglu 2013).

## 6. Ligamentum flavum (Phase C1 solid ligament; thickness at half its length, perpendicular to the canal axis)
| Level | Right / Left (mm) | Reference | Result |
|---|---|---|---|
| L3–4 | 3.09 / 3.09 | 3.1 ± 0.8 (AJNR 2010) | OK (rule value) |
| L4–5 | 3.09 / 3.09 | 3.1 ± 0.8 | OK |
| L5–S1 | 3.09 / 3.09 | 3.1 ± 0.8 | OK; now reaches the S1 lamina (z 956) |
- Old 0.6 mm sheets kept as "... (old)", hidden.

## 7. Facet orientation (upper IAP vs lower SAP parts; axial cut at mid-joint)
| Level | Right / Left | Reference (2013 CT) | Bone-to-bone gap R / L | Result |
|---|---|---|---|---|
| L3–4 | 28.1° / 44.0° | 38.7° | 2.4 / 1.9 mm | **FLAG: 16° left–right difference** |
| L4–5 | 41.3° / 48.0° | 47° | 2.0 / 2.7 mm | OK |
| L5–S1 | 43.9° / 45.4° | 47.3° | 2.4 / 2.2 mm | OK (left: 4 % of points overlap, max 0.4 mm) |

## 8. Root topography (Phase C1 roots; old schematic roots kept as "... (old)", hidden)
| Root | Leaves the sac (z) | Disc above its foramen (mid z) | Sleeve exit → DRG centre (mm) | Angle to canal axis | Narrowest gap ventral / dorsal, R / L (mm) |
|---|---|---|---|---|---|
| L3 | 1065 | L2–3 (1066) | 35.6 / 33.5 | 4° | 1.01, 1.22 / 1.08, 1.14 |
| L4 | 1029 | L3–4 (1031) | 25.6 / 25.7 | 13° / 19° | 0.94, 2.06 / 0.96, 2.51 |
| L5 | 995 | L4–5 (997) | 27.3 / 28.6 | 48° / 47° | 1.01, 0.95 / 0.93, 1.13 |
| S1 | 964 | L5–S1 (962), upper half | 27.4 / 27.4 | 22° | 0.91, 1.15 / 0.93, 1.18 |
| S2 | 951 | (S1 level) | 34.6 / 34.5 | 19° | 0.76, 0.99 / 0.76, 0.91 |
- All roots and DRGs keep ≥0.5 mm from bone, disc and ligament (narrowest 0.76 mm, S2). Exiting roots run under their own pedicle; traversing roots sit in the lateral recess at the disc (cut at mid L4–5: L5 sleeves anterolateral to the sac).
- S1 leaves more cephalad and more vertically than L5 (22° vs 47°). **Not the shortest**: S1 27.4 mm vs L4 25.6 and L5 28 mm (Hasegawa 1996 says shortest) — reported, not forced.
- Spinal nerves (not in the ≥0.5 mm rule): L3–L5 1.8–4.8 mm; S1 −0.4 mm and S2 −0.1 mm (graze bone inside the sacral foramina).
- Intrathecal arrangement: largest overlap between neighbouring roots 0.4 mm before smoothing (packing rule; roots of 0.9–1.4 mm radius).

## 9. Phase C2 parts (rules (approx); numbers in data/raw/c2_checks.json)
| Item | Value (this model) | Reference / rule | Result |
|---|---|---|---|
| Cartilaginous endplates (6) | mean 0.71 mm (0.46 centre – 1.00 AP rim, 0.78 lateral rim); cover 70–72 % of the disc face (1012–1174 mm²) | 0.3–1 mm, mean 0.74 (DeLucca 2016; Berg-Johansen 2018) | OK (rule value) |
| Facet bone gap (median, R / L) | L3–4 2.60 / 1.62 · L4–5 1.80 / 2.71 · L5–S1 2.75 / 2.03 mm | filled by cartilage + 0.4 mm space | cartilage 0.48–1.14 mm per facet |
| Facet angle (mid-joint normal, R / L) | L3–4 29.2° / 40.9° · L4–5 40.8° / 46.1° · L5–S1 46.1° / 47.3° | 38.7 / 47 / 47.3° | **FLAG L3–4: 12° left–right** (as section 7) |
| Facet articular area (R / L) | L3–4 116 / 121 · L4–5 140 / 157 · L5–S1 171 / 112 mm² | — | report |
| Posterior fat pad: length, max depth | L3–4 19, 4.1 · L4–5 20, 3.4 · L5–S1 26, 6.5 mm | Reina 2019: one pad per level, not continuous | OK |
| Foraminal fat (median thickness round the nerve) | L3 2.7–2.8 · L4 2.7–2.8 · L5 1.5–2.2 mm | — | report |
| Kambin's triangle base × height, area (R / L) | L3–4 14.3×8.0, 62 / 7.1×9.1, 41 · L4–5 14.2×14.7, 126 / 14.7×18.7, 171 · L5–S1 23.0×30.4, 472 / 22.7×27.3, 403 mm² | — | **FLAG L5–S1 large** (tall L5–S1 foramen, tilted sacrum) |
| Lateral recess patch area (R / L) | L4 26 / 30 · L5 66 / 57 · S1 15 / 16 mm² | — | report |
- Clearance to bone/disc/ligament (exact): medial branches 0.68–0.76, L5 dorsal rami 0.58–0.72 mm. SVNs touch the PLL (−0.07 to −0.33 mm; they end in it). Venous channels touch bone in ~2 % of points (≤1.7 mm, L5 body, where the sac fills the canal); L4–5 left intervertebral vein −2.2 mm at its join with the ascending lumbar vein (which lies on bone). Capsules are anchored 0.8 mm into bone by design. Fat: L5–S1 pad −0.2 mm into flavum; prelaminar band L4 and left L3–4 foraminal fat: a few vertices into the flavum at its midline seam / lateral edge.
