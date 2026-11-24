"""Phase D: write assets/levels.json = measured baseline of each detailed disc level (L3-4, L4-5, L5-S1).
Disease modules start from these values and change them. Measures only; changes no mesh.
  python3 -I tools/build_levels.py      (after tools/check_lumbar.py and tools/build_gaps.py)
Inputs: data/raw/checks.json (Phase A: disc heights, foramina, frames), c1_checks.json (dural sac, flavum),
c2_checks.json (facet joint angle), data/raw/lumbar_raw.glb + gaps_raw.glb (nucleus centre, disc size, canal AP now).
Output positions/axes are FILE coordinates (glTF metres: +x patient left, +y up, +z anterior); sizes in mm."""
import os, sys, json
import numpy as np
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
from lgeom import MM, load, ray, samples

RAW = os.path.join(ROOT, 'data/raw')
CK = json.load(open(os.path.join(RAW, 'checks.json')))
C1 = json.load(open(os.path.join(RAW, 'c1_checks.json')))
C2 = json.load(open(os.path.join(RAW, 'c2_checks.json')))
G = load(os.path.join(RAW, 'lumbar_raw.glb'))
G.update(load(os.path.join(RAW, 'gaps_raw.glb')))
LEVELS = {'L3-4': ('L3-L4', 'L3', 'L4'), 'L4-5': ('L4-L5', 'L4', 'L5'), 'L5-S1': ('L5-S1', 'L5', 'S1')}
r1 = lambda x: None if x is None or not np.isfinite(x) else round(float(x), 1)
gl = lambda v: [round(float(v[0]), 5), round(float(v[2]), 5), round(float(-v[1]), 5)]   # Z-Anatomy -> glTF
glv = lambda v: [round(float(v[0]), 4), round(float(v[2]), 4), round(float(-v[1]), 4)]


def mesh(names):
    V, F, o = [], [], 0
    for n in names:
        if n not in G: continue
        v, f = G[n]; V.append(v); F.append(f + o); o += len(v)
    return np.vstack(V), np.vstack(F)


def canal_ap(k, Fr):
    """Midsagittal canal AP at mid-disc on the CURRENT model: from the back of the disc/PLL to the first posterior
    wall (Phase C1 solid flavum, laminae, spinous processes), along the disc's posterior axis."""
    zd, up, lo = LEVELS[k]
    o, a = Fr['o'], Fr['a']                          # a = posterior (lgeom.frame)
    front = mesh([f'Annulus fibrosus {zd}', f'Posterior longitudinal ligament {k}'])
    t = ray(*front, o, a); t = t[t < 0.04]
    if not len(t): return None, None
    A = o + t[-1] * a
    post = [e['name'] for e in MAN if e.get('level') in (up, lo) and e['layer'] == 'bone' and e.get('part') != 'body']
    walls = mesh(post + [f'Ligamentum flavum {k} (left)', f'Ligamentum flavum {k} (right)']
                 + [e['name'] for e in MAN if e['name'].startswith('Interspinous ligament')])
    t2 = ray(*walls, A + 0.2 * MM * a, a)
    sac = ray(*G['Dural sac'], A, a); sac = sac[sac < 0.03]
    sac_ap = (sac[-1] - sac[0]) / MM if len(sac) >= 2 else np.nan
    return (t2[0] / MM + 0.2) if len(t2) else np.nan, sac_ap


MAN = json.load(open(os.path.join(ROOT, 'assets/manifest.json')))
CK_FOR = json.load(open(os.path.join(ROOT, 'assets/model.json'))).get('foramen', {})   # Phase A centres (glTF)
out = {'_help': 'Baseline of the normal model per disc level, measured (tools/build_levels.py). Positions and axes: '
       'file coordinates (glTF metres; +x patient left, +y up, +z anterior; same as lumbar.glb/gaps.glb). '
       'Sizes mm, angles degrees. Disease modules copy a level and change its values. Methods: see "_methods".',
       '_methods': {
           'disc_height_mm': 'rays along the disc cranial axis, midline, at 10/50/90 % of the AP depth (Phase A, check_lumbar.py)',
           'nucleus_centre': 'centroid of the nucleus pulposus mesh', 'nucleus_size_mm': 'extent along left, cranial, anterior',
           'dural_sac': 'Phase C1 dural sac cut perpendicular to the canal axis at mid-disc (area, width, AP)',
           'canal_ap_mm': 'midsagittal, back of disc/PLL to the first posterior wall on the current model; flavum halves leave a 0.25 mm midline cleft, so the wall is the upper lamina/spinous process (L3-4, L4-5) or the interspinous ligament (L5-S1)',
           'foramen': 'parasagittal cut through the upper pedicle centre: height = max (Hasegawa 1995) and under the pedicle; '
                      'width = AP at the disc mid-plane (bone)',
           'flavum_thickness_mm': 'Phase C1 solid ligament at half its length (rule value 3.1 mm)',
           'facet_angle_deg': 'joint line from the sagittal plane, axial cut at mid-joint (Phase C2 joint space)',
           'disc_frame': 'PCA of the annulus: centre = middle of its extent; axes are unit vectors; size = width, height, AP'},
       'levels': {}}
for k, (zd, up, lo) in LEVELS.items():
    f = CK['_frames'][k]; Fr = {x: np.array(f[x]) for x in 'olan'}
    P, _ = samples(*G[f'Annulus fibrosus {zd}'], spacing=0.5 * MM)
    q = P - Fr['o']; ext = [(q @ Fr[x]).min() for x in 'lna'], [(q @ Fr[x]).max() for x in 'lna']
    c = Fr['o'] + sum((lo_ + hi) / 2 * Fr[x] for x, lo_, hi in zip('lna', *ext))
    size = [r1((hi - lo_) / MM) for lo_, hi in zip(*ext)]
    Nv = G[f'Nucleus pulposus {zd}'][0]; nq = Nv - Nv.mean(0)
    dh, fo, sac = CK[k]['disc_height'], CK[k]['foramen'], C1['sac']['areas'][k]
    ap, sac_ap = canal_ap(k, Fr)
    lev = {
        'upper': up, 'lower': lo, 'disc': f'Annulus fibrosus {zd}', 'nucleus': f'Nucleus pulposus {zd}',
        'disc_height_mm': {s: dh[s]['disc'] for s in ('anterior', 'middle', 'posterior')},
        'bone_gap_mm': {s: dh[s]['bone_gap'] for s in ('anterior', 'middle', 'posterior')},
        'nucleus_centre': gl(Nv.mean(0)),
        'nucleus_size_mm': [r1(np.ptp(nq @ Fr[x]) / MM) for x in 'lna'],
        'dural_sac': {'area_mm2': sac['area'], 'width_mm': sac['width'], 'ap_mm': sac['ap'], 'ap_midline_ray_mm': r1(sac_ap)},
        'canal_ap_mm': r1(ap), 'canal_ap_phaseA_bone_mm': CK[k]['canal_mid_disc']['ap_midline'],
        'canal_area_phaseA_mm2': CK[k]['canal_mid_disc']['area_mm2'],
        'foramen': {s: {'height_max_mm': fo[s]['height_max'], 'height_under_pedicle_mm': fo[s]['height_at_pedicle_line'],
                        'width_mid_disc_mm': fo[s]['width_at_mid_disc'], 'width_narrowest_mm': fo[s]['width_narrowest'],
                        'centre': CK_FOR.get(f'{k} {s}')} for s in ('left', 'right')},
        'flavum_thickness_mm': {s: C1['flavum'][f'Ligamentum flavum {k} ({s})'] for s in ('left', 'right')},
        'facet_angle_deg': {s: C2['facets'][f'{k} {s}']['angle'] for s in ('left', 'right')},
        'facet_gap_mm': {s: C2['facets'][f'{k} {s}']['gap_med'] for s in ('left', 'right')},
        'disc_frame': {'centre': gl(c), 'anterior': glv(-Fr['a']), 'left': glv(Fr['l']), 'cranial': glv(Fr['n']),
                       'size_mm': {'width': size[0], 'height': size[1], 'ap': size[2]}},
    }
    out['levels'][k] = lev
    print(f"{k}: disc {lev['disc_height_mm']}, sac {sac['area']} mm2, canal AP {lev['canal_ap_mm']} "
          f"(Phase A {lev['canal_ap_phaseA_bone_mm']}), size {size}")
LIVE = os.path.join(RAW, 'kit_live.json')   # written by tools/check_kit.mjs (4th argument)
if os.path.exists(LIVE):
    for k, v in json.load(open(LIVE)).items(): out['levels'][k]['kit_measures'] = v
    out['_methods']['kit_measures'] = ('the kit\'s own live measures (kit.measureCanal / measureForamen, js/measure.js) on the '
        'unchanged model: compare a changed model with THESE (same method). Foramen = rays through the Phase A foramen centre.')
json.dump(out, open(os.path.join(ROOT, 'assets/levels.json'), 'w'), indent=1)
print('wrote assets/levels.json')
