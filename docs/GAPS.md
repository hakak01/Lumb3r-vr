# GAPS — model vs REQUIRED STRUCTURES (docs/SPEC.md), updated after Phase C1
Build: `tools/build_assets.py` (+ `split_a2.py`, `bparts.py`, `bsplit.py`) → assets/lumbar.glb (240 objects, 380,463 triangles, 2.9 MB) + manifest.json (fields: name, layer, source, approx, triangles, level, side, part, context).
Phase C1: `tools/build_gaps.py` → assets/gaps.glb (60 objects, 146k triangles, 0.9 MB) + gaps.json (source "rules (approx)"). **APPROX** = built here by rules.
Status: **OK** = present from the source · **PART** = present but incomplete/coarse · **MISSING** = not in the source (phase named).
z = Z-Anatomy height in mm (mid-disc: L2–3 1066, L3–4 1031, L4–5 997, L5–S1 962).

## Bones (A2 split done: closed parts, flat cut faces; parts of one bone add up to its volume within 0.003 %)
| Structure | Status | Note |
|---|---|---|
| L3, L4, L5 | OK | BodyParts3D. 14 parts each: body, spinous process, and left/right pedicle, pars interarticularis, lamina, superior articular process (SAP), inferior articular process (IAP), transverse process (TP). |
| Sacrum / S1 | OK | Z-Anatomy. S1 body, S1 ala, S1 SAP, S1 lamina (left/right) + "Sacrum (rest)" (level S2-5). S1 lower limit = S1 foramina level (31 mm below the endplate). The S1 "pedicle" region goes with the ala (lateral mass). |
| L1, L2, hip bones, coccyx | OK | Context (not split). |
- Cut rules: body | pedicle at the coronal level where the two pedicles separate from the body; pedicle | arch at the canal's AP centre; TP at the pedicle's lateral wall (L5: at the body's half-width, because the L5 TP joins the pedicle); SAP above the lowest point of the upper facet contact (L5: 2 mm; L3–L4: 1–3 mm in the vertebra frame); IAP below the highest point of the lower facet contact; pars = lateral column between them (lateral to the medial pedicle wall); lamina = medial part, split in the midline; spinous process = behind the posterior lamina surface, within 10 mm of the midline.
- Small boolean fragments were added to the part they touch (as a touching shell). Slivers under 0.5 mm³ were dropped (≤0.32 mm³ per bone).

## Joints
| Structure | Status | Note |
|---|---|---|
| Discs L3–4, L4–5, L5–S1 | OK | "Annulus fibrosus L4-L5" = disc minus nucleus (exact) + "Nucleus pulposus L4-L5". L1–2, L2–3 the same (context). |
| Nucleus pulposus | PART | L3–4 nucleus only 6.2 mm across (0.13 cm³); L4–5 0.98 cm³, L5–S1 1.40 cm³. |
| Cartilaginous endplates | MISSING | Phase C. |
| Facet cartilage + capsule | MISSING | Phase C. Bone-to-bone facet gap 1.9–2.7 mm. |
| Sacroiliac joints (context) | PART | Only the SI ligaments. |

## Ligaments (A2: split per level; cut at the middle of the body, spinous process or TP of L3, L4, L5, S1; flavum 4 mm below each lamina's upper edge, then left/right)
| Structure | Status | Note |
|---|---|---|
| ALL | OK | L3-4, L4-5, L5-S1 + context L1-3, S1-5. |
| PLL | OK | L3-4, L4-5, L5-S1 + context L1-3 (ends at z 958). |
| Ligamentum flavum | APPROX | C1: L3-4, L4-5, L5-S1 left/right rebuilt as solid ligaments, 3.1 mm at half length, front of the lower half of the upper lamina → upper edge of the lower lamina, laterally over the front of the facet joint to the foramen; L5-S1 reaches S1. Old 0.6 mm sheets: "(old)", hidden. L1-3: source (context). |
| Interspinous | OK | L3-4, L4-5, L5-S1 + context. |
| Supraspinous | OK | L3-4, L4-5 + context; none at L5-S1 = **normal** (ends at L4 in 73 %, routinely absent at L5-S1; Bogduk, from Rissanen 1960, Heylings 1978). Not added. |
| Intertransverse | OK | L3-4, L4-5, L5-S1 per side + context. |
| Iliolumbar, SI ligaments | OK | Not split (single-level). |

## Neural (A2: split per level by the foramen each passes)
| Structure | Status | Note |
|---|---|---|
| Dural sac | APPROX | C1 "Dural sac": one closed tube from the top of the region (z 1128, L1) to a rounded tip at upper S2 (z 943), inside the measured canal; "Filum terminale externum (dural filum)" to the back of the coccyx. Z-Anatomy "Spinal dura" is only a sheath on the cord/conus (2 mm wide at z 1066), not a sac, so the new sac starts at the region top and contains it. |
| Arachnoid | APPROX | "Arachnoid mater" 0.2 mm inside the sac. Not in the root sleeves. |
| Cauda equina | APPROX | L3–S2 ventral and dorsal roots from the conus surface; crescent rule (next to exit anterolateral, lower roots posteromedial, ventral anteromedial to dorsal). "Filum terminale internum" conus tip (z 1055) → sac tip, dorsal midline. Old "L3 root" … "S4 root" and "Cauda equina (central bundle)": "(old)", hidden. S3–S5 and coccygeal roots: MISSING. |
| Ventral/dorsal roots, DRG, root sleeves L3–S2 | APPROX | Template Z-Anatomy L2 roots/ganglion scaled to the DRG sizes; own dural sleeve from the disc above its foramen to the DRG. T12–L2 roots/ganglia: source (context). |
| Spinal nerves | APPROX | L3–S2 from just beyond the DRG to the nearest Z-Anatomy plexus nerve (L3 → obturator n., L4/L5 → nerve to quadratus femoris, S1/S2 → old root end at the sacral plexus). Ventral rami as such: PART (plexus branches only). |
| Lumbosacral trunk, dorsal rami, medial branches, sinuvertebral nerves | MISSING | Phase C. |
| Spinal cord (conus) | OK | Ends z 1055 (L2–L3). |

## Vessels
| Structure | Status | Note |
|---|---|---|
| Aorta + bifurcation (z ≈1030, L3–4), IVC + confluence (z ≈1031), common iliacs, median sacral a. | OK | |
| Lumbar arteries/veins (4 per side, lowest at L3–4), iliolumbar vessels (+ branches), ascending lumbar veins, lateral sacral veins | OK | |
| Internal vertebral venous plexus, basivertebral veins | MISSING | Phase C. |

## Muscles, fascia, skin, fat
| Structure | Status | Note |
|---|---|---|
| Multifidus, erector spinae (iliocostalis lumborum, longissimus, spinalis), interspinales, QL, psoas, TLF (3 layers) | OK | Not split (SPEC asks only for whole muscles). |
| Intertransversarii | PART | Lateral only; medial not in source. Rotatores added. |
| Skin | PART | Coarse (92–206 triangles per region). |
| Subcutaneous, epidural, foraminal fat | MISSING | Phase C. |
