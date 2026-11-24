# GAPS — Phase A1 model vs REQUIRED STRUCTURES (docs/SPEC.md)
Build: `tools/build_assets.py` → assets/lumbar.glb (143 objects, 338,566 triangles, 2.4 MB) + assets/manifest.json.
Status words: **OK** = present from the source · **PART** = present but incomplete/coarse · **MISSING** = not in the source (to build, phase named) · **A2** = needs the Phase A2 split.
z values = Z-Anatomy height in mm (mid-disc: L2–3 1066, L3–4 1031, L4–5 997, L5–S1 962).

## Bones
| Structure | Status | Note |
|---|---|---|
| L3, L4, L5 | OK, A2 | BodyParts3D bones (ICP to Z-Anatomy, error ≤0.78 mm), watertight, 14.8k–17.3k triangles. Parts (body, pedicle, pars…) → A2. |
| Sacrum / S1 | OK, A2 | Z-Anatomy kept (BodyParts3D fit 4.07 mm > 1.5 mm limit); repaired to watertight (removed 3 loose flaps). S1 parts → A2. |
| L1, L2, hip bones | OK | BodyParts3D, watertight; context layer. |
| Coccyx | OK | Z-Anatomy (no BodyParts3D coccyx); watertight. |

## Joints
| Structure | Status | Note |
|---|---|---|
| Discs L3–4, L4–5, L5–S1 | OK, A2 | Smoothed (≤0.25 mm change). Annulus = disc minus nucleus → A2. Disc–endplate fit after the bone swap: −0.2 to +0.5 mm. |
| Nucleus pulposus ×3 | PART | L3–4 nucleus is only 6.2 mm across (L4–5 12.3, L5–S1 13.9 mm); real nucleus is much larger (see CHECKS). |
| Cartilaginous endplates | MISSING | Phase C. |
| Facet cartilage + capsule | MISSING | Phase C. Bone-to-bone facet gap is 1.9–2.7 mm, room for cartilage. |
| Sacroiliac joints (context) | PART | No joint object; only the SI ligaments (below). |

## Ligaments (long ones cut at the top of L1; split per level in A2)
| Structure | Status | Note |
|---|---|---|
| ALL | OK, A2 | down to z 929 (S2). |
| PLL | OK, A2 | down to z 958 (top of S1). |
| Ligamentum flavum | PART, A2 | Ends at z 980: **no L5–S1 ligamentum flavum**. A thin sheet, 0.6 mm thick (normal 3.1 mm). |
| Interspinous | OK, A2 | down to z 957. Very coarse source (smoothed). |
| Supraspinous | PART | Ends at z 1005 (L4 spinous process); none at L4–5/L5–S1. (It often ends at L4–L5 in life.) |
| Intertransverse | OK, A2 | per side, down to z 974 (L5). |
| Iliolumbar | OK | per side. |
| SI ligaments (context) | OK | anterior, interosseous, posterior; plus sacrococcygeal, intercornual. |

## Neural
| Structure | Status | Note |
|---|---|---|
| Dural sac | **MISSING at L3–S1** | "Spinal dura" ends at z 1055 (mid-L3). No "Spinal dura.001" in this blend. Build in Phase C. |
| Arachnoid | MISSING | Group "Arachnoid" is empty. |
| Cauda equina | PART | Schematic curves only (0.5 mm radius): one midline trunk + one branch per level. |
| Ventral/dorsal roots L3–S1 | **MISSING** | Root objects end at z 1068 (L2). Only the cauda equina branches exist below. Rebuild in Phase C (root sleeves). |
| DRG L3–S1 | **MISSING** | "Spinal ganglion" ends at z 1066 (L1–L2 ganglia only). |
| Spinal nerves / ventral rami | PART | Branches of the lumbar plexus present (iliohypogastric, ilio-inguinal, genitofemoral, LFCN, femoral, obturator) and sacral plexus (sciatic, pudendal, superior gluteal, PFCN, nerves to piriformis and quadratus femoris), cut where they leave the pelvis (z 870). Plexus formation inside psoas not modelled. |
| Lumbosacral trunk | MISSING | Phase C. |
| Dorsal rami, medial branches | MISSING | "Posterior rami" group empty. Phase C. |
| Sinuvertebral nerves | MISSING | Phase C. |
| Spinal cord (conus) | OK | White matter ends at z 1055 (L2–L3; low-normal conus). Kept (neural layer). |

## Vessels
| Structure | Status | Note |
|---|---|---|
| Aorta + bifurcation | OK | Bifurcation at z ≈1030 (L3–4 disc level; usually L4). |
| IVC + confluence | OK | Confluence at z ≈1031. |
| Common iliac arteries/veins, median sacral artery | OK | |
| Lumbar arteries / veins | OK | 4 per side, lowest at z 1026 / 1028 (L3–4). |
| Iliolumbar artery (+ iliacus, lumbar, spinal branches) and vein | OK | |
| Ascending lumbar veins | OK | left and right. Lateral sacral veins OK (no lateral sacral arteries in source). |
| Internal vertebral venous plexus, basivertebral veins | MISSING | Phase C. |

## Muscles, fascia, skin, fat
| Structure | Status | Note |
|---|---|---|
| Multifidus lumborum, interspinales lumborum, QL, psoas major (whole, to the femur) | OK | |
| Erector spinae (lumbar) | OK | iliocostalis lumborum, longissimus thoracis, spinalis thoracis (whole muscles) + origin/insertion patches on L1–L3 and ilium. |
| Intertransversarii | PART | Lateral (dorsal + ventral parts) OK; medial intertransversarii lumborum not in source. Rotatores (cut at top of L1) added. |
| Thoracolumbar fascia (3 layers) | OK | |
| Skin | PART | Lumbar, sacral and vertebral regions; very coarse (92–206 triangles each). Hidden by default (Phase B). |
| Subcutaneous fat | MISSING | Phase C (`gaps_fat.py`). |
| Epidural and foraminal fat | MISSING | Phase C. |
