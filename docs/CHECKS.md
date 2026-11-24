# CHECKS — Phase A1 measurements vs ANATOMY CHECKS (docs/SPEC.md)
Measured by `python3 -I tools/check_lumbar.py` on data/raw/lumbar_raw.glb (raw numbers: data/raw/checks.json). Nothing was changed to fit.
One adult male body (Z-Anatomy soft tissue; BodyParts3D L1–L5 and hip bones). **FLAG** = big difference from the reference.
Frames: each disc's cranio-caudal axis = its thinnest direction (PCA); vertebra axis = mean of the discs above and below.

## 1. Disc height (mm; disc mesh / bone-to-bone gap; rays along the disc axis, midline, at 10 %, 50 %, 90 % of AP depth)
| Level | Anterior | Middle | Posterior | Reference (Zhou 2000; Asian range 2018) | Result |
|---|---|---|---|---|---|
| L3–4 | 6.7 / 6.4 | 6.4 / 6.8 | 6.1 / 6.3 | 11.6 ± 1.8; 7.4–13.3 | **FLAG: thin** (below both) |
| L4–5 | 8.9 / 9.2 | 12.9 / 12.7 | 7.0 / 7.1 | 11.3 ± 2.1; 7.8–14.6 | OK; anterior > posterior |
| L5–S1 | 11.5 / 11.7 | 14.0 / 14.0 | 14.8 / 15.2 | 10.7 ± 2.1; 7.1–13.1 | **FLAG: posterior > anterior** (no lordotic wedge); middle slightly high |
- Disc AP depth 36.0 / 38.4 / 38.5 mm. Disc–bone fit after the bone swap: −0.2 to +0.5 mm at all points (good).
- Nucleus size (mm, l/a/n): L3–4 6.2 × 6.2 × 6.2, L4–5 12.3³, L5–S1 13.9³ (spheres). **FLAG**: L3–4 nucleus very small.

## 2. Pedicle (axial cut at pedicle mid-height; isthmus = narrowest bone run from canal outward, × cos(angle))
| Level | Width R / L (mm) | Range ±2 mm height | Transverse angle R / L | Reference | Result |
|---|---|---|---|---|---|
| L3 | 7.2 / 6.5 | 5.3–7.9 / 5.7–7.1 | 39° / 44°, medial | 7.2 ± 0.87 (Mohanty); >7 (Acharya); ~7.8 (Silverstein) | width OK (L slightly <7); **FLAG angle** |
| L4 | 8.0 / 7.6 | 6.8–8.0 / 7.1–7.6 | 45° / 51°, medial | ~8.8 (Silverstein) | width OK; **FLAG angle** |
| L5 | not measured | — | — | ~9.7; angle ~30° | see note |
- Angle method is local (axis over ±4 mm around the isthmus) and reads higher than the 10–30° expected; it will be re-measured on the separate pedicle part in Phase A2 (full-length axis). Direction (medial) is correct.
- L5: on every axial cut the large transverse process joins the pedicle, so the isthmus cannot be found in a surface model yet. Re-measure after the A2 split.
- Interpedicular distance L3 24.6, L4 23.5 mm. Bony canal AP (midline, L3 pedicle level) 18.5 mm.

## 3. Foramen (parasagittal cut through the upper pedicle centre, l ≈ ±17 mm)
| Level | Height R / L | AP width at mid-disc R / L | Widest R / L | Reference | Result |
|---|---|---|---|---|---|
| L3–4 | 18.0 / 18.3 | 10.9 / 9.9 | 17.8 / 18.6 | height >15 (Hasegawa); width ~7.5 | OK |
| L4–5 | 19.9 / 19.8 | 10.1 / 11.3 | 13.1 / 14.7 | width ~8.5 | OK |
| L5–S1 | 9.8 / 10.4 (approx.) | 9.1 / 7.1 | 16.7 / 14.0 | width ~8.7 | **FLAG height <15**, but the cut plane comes from the unreliable L5 pedicle — re-measure in A2 |
- Posterior disc height (10 % inside the posterior margin): 6.1 / 7.0 / 14.8 mm — all clearly above Hasegawa's 4 mm.

## 4. Dorsal root ganglia
- **Not measurable**: no DRG at L3–S1 in the source (Z-Anatomy ganglia end at L2). Built in Phase C with the reference sizes/positions.

## 5. Canal at mid-disc (axial cut; disc + PLL in front, ligamentum flavum + bone behind, medial pedicle walls at the sides)
| Level | Area (mm²) | Midsagittal AP (mm) | Reference | Result |
|---|---|---|---|---|
| L3–4 | 409 | 20.9 | AP >12 | OK |
| L4–5 | 405 | 20.4 | AP >12 | OK |
| L5–S1 | 612 (approx., L5 pedicle walls) | 19.2 | AP >12 | OK |
- This is the whole canal (epidural space included), **not the dural sac**: the source has no dura below mid-L3, so dural sac area (>100 mm²) cannot be checked until Phase C.

## 6. Ligamentum flavum (thickness at half its length, axial cut at mid-disc)
| Level | Right / Left (mm) | Reference | Result |
|---|---|---|---|
| L3–4 | 0.6 / 0.6 | 3.1 ± 0.8 (AJNR 2010) | **FLAG: far too thin** (source is a 0.6 mm sheet) |
| L4–5 | 0.6 / 0.6 | 3.1 ± 0.8 | **FLAG** |
| L5–S1 | none | 3.1 ± 0.8 | **FLAG: missing** (source ligament ends at z 980) |

## 7. Facet orientation (axial cut at mid-joint; line through the mid-gap points)
| Level | Right / Left | Reference (2013 CT) | Bone-to-bone gap R / L | Result |
|---|---|---|---|---|
| L3–4 | 28.0° / 43.0° | 38.7° | 2.4 / 1.9 mm | **FLAG: 15° left–right difference** |
| L4–5 | 41.3° / 48.3° | 47° | 2.0 / 2.7 mm | OK (7° difference) |
| L5–S1 | 44.4° / 44.1° | 47.3° | 2.5 / 2.3 mm | OK |
- No bone overlap at the facets except L5–S1 left (4 % of points, max 0.4 mm).

## 8. Root topography (Z-Anatomy cauda equina branch curves)
| Root | Crosses foramen | Height above mid-disc | Below upper pedicle edge | Result |
|---|---|---|---|---|
| L3 (left; right not detected) | L3–4 | 3.3 mm | 9.3 mm | OK: under its pedicle, above the disc |
| L4 R / L | L4–5 | 6.7 / 6.6 mm | 5.8 / 5.8 mm | OK |
| L5 R / L | L5–S1 | 7.0 / 7.8 mm | 6.0 / 5.3 mm | OK |
- **FLAG: no traversing course.** Each branch leaves the midline trunk only 16–21 mm above the disc it exits at (11–17 mm below the disc above), so at the disc above it is still in the midline, not in the lateral recess. The S1 branch goes straight to the S1 foramen. Rebuild roots in Phase C as SPEC says.
