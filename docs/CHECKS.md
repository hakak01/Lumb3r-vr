# CHECKS — measurements vs ANATOMY CHECKS (docs/SPEC.md), updated after Phase A2
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

## 4. Dorsal root ganglia
- **Not measurable**: no DRG at L3–S1 in the source (ganglia exist only for T12–L2). Phase C.

## 5. Canal at mid-disc (disc + PLL in front, flavum + bone behind, medial pedicle walls at the sides)
| Level | Area (mm²) | Midsagittal AP (mm) | Result |
|---|---|---|---|
| L3–4 | 412 | 21.0 | AP OK (>12) |
| L4–5 | 439 | 20.4 | AP OK |
| L5–S1 | 573 | 19.5 | AP OK |
- Whole canal, **not the dural sac** (no dura below mid-L3): the >100 mm² dural sac check waits for Phase C.

## 6. Ligamentum flavum (thickness at half its length, axial cut at mid-disc)
| Level | Right / Left (mm) | Reference | Result |
|---|---|---|---|
| L3–4 | 0.6 / 0.6 | 3.1 ± 0.8 (AJNR 2010) | **FLAG: far too thin** |
| L4–5 | 0.6 / 0.6 | 3.1 ± 0.8 | **FLAG** |
| L5–S1 | not in the cut | 3.1 ± 0.8 | **FLAG: missing** in the interlaminar space |

## 7. Facet orientation (upper IAP vs lower SAP parts; axial cut at mid-joint)
| Level | Right / Left | Reference (2013 CT) | Bone-to-bone gap R / L | Result |
|---|---|---|---|---|
| L3–4 | 28.1° / 44.0° | 38.7° | 2.4 / 1.9 mm | **FLAG: 16° left–right difference** |
| L4–5 | 41.3° / 48.0° | 47° | 2.0 / 2.7 mm | OK |
| L5–S1 | 43.9° / 45.4° | 47.3° | 2.4 / 2.2 mm | OK (left: 4 % of points overlap, max 0.4 mm) |

## 8. Root topography (cauda equina branches, now named "L3 root" … "S4 root")
| Root | Crosses | Height above mid-disc | Below upper pedicle edge | Result |
|---|---|---|---|---|
| L3 | L3–4 foramen | (A1: 3.3 mm) | (A1: 9.3 mm) | OK |
| L4 R / L | L4–5 foramen | 6.3 / 6.3 mm | 4.5 / 4.3 mm | OK |
| L5 R / L | L5–S1 foramen | 7.1 / 7.1 mm | 6.1 / 6.4 mm | OK |
- **FLAG: no traversing course.** Each branch leaves the midline bundle 11–17 mm below the disc above, so it is not in the lateral recess at that disc. Rebuild in Phase C.
