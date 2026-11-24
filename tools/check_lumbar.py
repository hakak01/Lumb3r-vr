"""Phase A step 7: measure the normal model for docs/CHECKS.md (measures only; changes nothing).
Run from the repo root after tools/build_assets.py:  python3 -I tools/check_lumbar.py
Reads data/raw/lumbar_raw.glb (world coordinates); writes data/raw/checks.json and prints a summary."""
import os, sys, json
import numpy as np
from scipy import ndimage
from scipy.spatial import cKDTree
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
from lgeom import MM, load, pca, frame, to_local, to_world, ray, section, holes, chord, samples, unit

G = load(os.path.join(ROOT, 'data/raw/lumbar_raw.glb'))
OUT = {}
DISCS = {'L2-3': ('Intervertebral disc L2-L3', 'Vertebra L2', 'Vertebra L3'),
         'L3-4': ('Intervertebral disc L3-L4', 'Vertebra L3', 'Vertebra L4'),
         'L4-5': ('Intervertebral disc L4-L5', 'Vertebra L4', 'Vertebra L5'),
         'L5-S1': ('Intervertebral disc L5-S1', 'Vertebra L5', 'Sacrum')}
LEVELS = ['L3-4', 'L4-5', 'L5-S1']
r1 = lambda x: None if x is None else round(float(x), 1)


def disc_frame(k):
    P, _ = samples(*G[DISCS[k][0]], spacing=0.5 * MM)
    c, U, _ = pca(P)
    return frame(U[:, 2], c)


DF = {k: disc_frame(k) for k in DISCS}


def first(V, F, o, d):
    t = ray(V, F, o, d)
    return t[0] if len(t) else np.nan


# ---- 1. disc heights (rays along the disc axis at 10 %, 50 %, 90 % of the midsagittal AP depth) ----
for k in LEVELS:
    Fr, (dn, up, lo) = DF[k], DISCS[k]
    o, n, a = Fr['o'], Fr['n'], Fr['a']
    tp, ta = first(*G[dn], o, a), first(*G[dn], o, -a)
    depth = tp + ta
    res = dict(ap_depth=r1(depth / MM))
    for nm, s in (('anterior', -ta + 0.1 * depth), ('middle', (tp - ta) / 2), ('posterior', tp - 0.1 * depth)):
        p = o + s * a
        du, dd = first(*G[dn], p, n), first(*G[dn], p, -n)
        bu, bd = first(*G[up], p, n), first(*G[lo], p, -n)
        res[nm] = dict(disc=r1((du + dd) / MM), bone_gap=r1((bu + bd) / MM),
                       gap_top=r1((bu - du) / MM), gap_bottom=r1((bd - dd) / MM))
    OUT.setdefault(k, {})['disc_height'] = res
    OUT[k]['disc_centre'] = [round(float(x), 5) for x in o]

# ---- 2. pedicles. Pedicle mid-height = centre of the pedicle's coronal cut 3 mm behind the body wall.
#      On the axial cut there, each row (along AP) is scanned from the canal outward; the bone run = pedicle.
#      Axis = line through the run midpoints around the narrowest row; transverse width = narrowest run x cos(angle). ----
VERT = {'L3': ('Vertebra L3', 'L2-3', 'L3-4'), 'L4': ('Vertebra L4', 'L3-4', 'L4-5'), 'L5': ('Vertebra L5', 'L4-5', 'L5-S1')}
VF, PED = {}, {}
HALF = 45 * MM


def side_comp(img, px, half, sg):
    lab, k = ndimage.label(img)
    best = None
    for c in range(1, k + 1):
        ii, jj = np.nonzero(lab == c)
        l = jj.mean() * px - half
        if sg * l > 4 * MM and (best is None or len(ii) > len(best[0])):
            best = (ii, jj)
    return best


for v, (bn, d1, d2) in VERT.items():
    VF[v] = Fr = frame(DF[d1]['n'] + DF[d2]['n'], (DF[d1]['o'] + DF[d2]['o']) / 2)
    V, F = G[bn]
    wall = first(V, F, Fr['o'], Fr['a'])                     # posterior wall of the body (midline)
    PED[v] = {}
    for side, sg in (('right', -1), ('left', 1)):
        nc = None
        for amm in np.arange(1.0, 8.01, 0.5):                  # first coronal cut where this side is separate
            img, px = section([G[bn]], to_world(Fr, [0, wall + amm * MM, 0]), Fr['l'], Fr['n'], 40 * MM)
            c = side_comp(img, px, 40 * MM, sg)
            if c is not None and np.ptp(c[1]) * px < 30 * MM:
                nc = ((c[0].min() + c[0].max()) / 2) * px - 40 * MM
                break
        if nc is None:
            PED[v][side] = None
            continue
        res = []
        HP = 62 * MM                                            # L5 transverse processes reach +-53 mm
        for dz in range(-6, 7):
            img, px = section([G[bn]], to_world(Fr, [0, 0, nc + dz * MM]), Fr['l'], Fr['a'], HP)
            j0 = int(HP / px)
            rows = []
            for i in range(int((wall + HP) / px) + 1, int((wall + 16 * MM + HP) / px)):
                if img[i, j0]:
                    continue                                    # midline must be canal
                j = j0
                while 0 < j < img.shape[1] - 1 and not img[i, j]:
                    j += sg
                a_ = j
                while 0 < j < img.shape[1] - 1 and img[i, j]:
                    j += sg
                if 0 < j < img.shape[1] - 1:
                    rows.append((i, abs(j - a_) * px, (a_ + j) / 2))
            if len(rows) < 8:
                continue
            R = np.array(rows)
            R = R[np.argmax(R[:, 1] >= 1.5 * MM):]                 # skip slivers at the body corner
            k, t = 0, 0                                         # walk back from the body; stop at the TP flare
            for t in range(len(R)):
                if t and (R[t, 0] - R[t - 1, 0]) > 3:
                    break
                if R[t, 1] < R[k, 1]:
                    k = t
                if R[t, 1] > R[k, 1] + 3 * MM:
                    break
            R = R[:t + 1]
            near = np.abs(R[:, 0] - R[k, 0]) * px <= 4 * MM
            pa, pl = R[near, 0] * px, R[near, 2] * px
            slope = np.polyfit(pa, pl, 1)[0] if near.sum() > 3 else 0.0   # dl/da
            ang = np.degrees(np.arctan(abs(slope)))
            medial = slope * sg > 0                             # moving posterior, axis goes lateral
            behind = R[k, 0] * px - HP - wall
            if R[k, 1] > 15 * MM or behind < 1.5 * MM:            # pedicle merged with the TP / body at this height
                continue
            res.append(dict(dz=dz, width=R[k, 1] * np.cos(np.radians(ang)) / MM, angle=ang, medial=bool(medial),
                            centre_local=np.array([R[k, 2] * px - HP, R[k, 0] * px - HP, nc + dz * MM]),
                            run=R[k, 1] / MM))
        if not res:
            PED[v][side] = None
            continue
        mid = [r for r in res if r['dz'] == 0]
        r = mid[0] if mid else max(res, key=lambda x: x['width'])
        near2 = [x['width'] for x in res if abs(x['dz'] - r['dz']) <= 2]
        r['range'] = [r1(min(near2)), r1(max(near2))]
        r['valid_dz'] = [x['dz'] for x in res]
        PED[v][side] = r
    OUT.setdefault(v, {})['pedicle'] = {s: (None if r is None else dict(
        transverse_width=r1(r['width']), width_range_pm2mm=r['range'], transverse_angle=r1(r['angle']),
        medial=r['medial'], isthmus_behind_body_wall_mm=r1((r['centre_local'][1] - wall) / MM), slice_dz_mm=r['dz'], valid_dz_mm=r['valid_dz'],
        mid_height_mm=r1(r['centre_local'][2] / MM))) for s, r in PED[v].items()}
    R_, L_ = PED[v]['right'], PED[v]['left']
    if R_ and L_:
        q = (R_['centre_local'] + L_['centre_local']) / 2
        t = ray(V, F, to_world(Fr, [0, 0, q[2]]), Fr['a'])      # body wall exit, then lamina inner surface
        OUT[v]['bony_canal'] = dict(interpedicular=r1((L_['centre_local'][0] - R_['centre_local'][0]
                                                       - (L_['run'] + R_['run']) / 2 * MM) / MM),
                                    ap_midline_at_pedicle=r1((t[1] - t[0]) / MM) if len(t) > 1 else None)

# ---- 3. foramina (Hasegawa 1995): parasagittal cut through the upper pedicle centre.
#      height = upper pedicle lower edge to lower pedicle upper edge; width = AP gap from the back of the
#      disc/body to the facet (SAP/IAP), narrowest and widest, between the disc mid-plane and the upper pedicle ----
for k in LEVELS:
    Fr, (dn, up, lo) = DF[k], DISCS[k]
    v = up.split()[-1]
    tp = first(*G[dn], Fr['o'], Fr['a'])
    OUT[k]['posterior_disc_height_edge'] = r1((first(*G[up], Fr['o'] + (tp - MM) * Fr['a'], Fr['n'])
                                               + first(*G[lo], Fr['o'] + (tp - MM) * Fr['a'], -Fr['n'])) / MM)
    OUT[k]['foramen'] = {}
    for side in ('right', 'left'):
        r = PED[v][side]
        if r is None:
            continue
        cq = to_local(Fr, to_world(VF[v], r['centre_local']))
        H = 40 * MM
        bones, px = section([G[up], G[lo]], to_world(Fr, [cq[0], 0, 0]), Fr['a'], Fr['n'], H)
        full, _ = section([G[dn], G[up], G[lo]], to_world(Fr, [cq[0], 0, 0]), Fr['a'], Fr['n'], H)
        full = ndimage.binary_closing(full, iterations=5)      # close 0.5 mm slivers between disc and endplates
        hgt, edges = [], []
        for amm in np.arange(-2, 2.01, 0.5):
            j = int((cq[1] + amm * MM + H) / px); i = int((cq[2] + H) / px)
            if not bones[i, j]:
                continue
            while i > 0 and bones[i, j]:
                i -= 1
            top = i
            while i > 0 and not bones[i, j]:
                i -= 1
            if i > 0:
                hgt.append((top - i) * px)
                edges.append(((top + 1) * px - H, (i + 1) * px - H))
        wid = []
        i_lo, i_hi = int(H / px), int((cq[2] + H) / px)
        for i in range(i_lo, i_hi):
            j = int(H / px)
            while j < full.shape[1] - 1 and full[i, j]:
                j += 1
            j0 = j
            while j < full.shape[1] - 1 and not full[i, j]:
                j += 1
            wid.append((j - j0) * px if j < full.shape[1] - 1 and 1.5 * MM < (j - j0) * px < 25 * MM else np.nan)
        if os.environ.get('PROFILE') == k + side:
            print('width profile (n mm, width mm):', [(r1((i - H / px) * px / MM), r1(w / MM)) for i, w in zip(range(i_lo, i_hi), wid)][::5])
        wid = np.array(wid)
        ok = ~np.isnan(wid)
        OUT[k]['foramen'][side] = dict(height=r1(max(hgt) / MM) if hgt else None,
                                       width_narrowest=r1(wid[ok].min() / MM) if ok.any() else None,
                                       narrowest_at_n_mm=r1(np.flatnonzero(ok)[np.argmin(wid[ok])] * px / MM) if ok.any() else None,
                                       width_at_mid_disc=r1(wid[0] / MM) if ok[0] else None,
                                       width_widest=r1(wid[ok].max() / MM) if ok.any() else None, plane_l_mm=r1(cq[0] / MM),
                                       pedicle_lower_edge_n_mm=r1(np.median([e[0] for e in edges]) / MM) if edges else None)

# ---- 4. canal and ligamentum flavum at mid-disc (axial cut in the disc frame) ----
for k in LEVELS:
    Fr, (dn, up, lo) = DF[k], DISCS[k]
    v = up.split()[-1]
    tp = first(*G[dn], Fr['o'], Fr['a'])
    R_, L_ = PED[v]['right'], PED[v]['left']
    img, px = section([G[dn], G[up], G[lo], G['Posterior longitudinal ligament'], G['Ligamenta flava']],
                      Fr['o'], Fr['l'], Fr['a'], HALF)
    n = img.shape[0]
    cR = to_local(Fr, to_world(VF[v], R_['centre_local'] + [R_['run'] / 2 * MM, 0, 0]))[0]
    cL = to_local(Fr, to_world(VF[v], L_['centre_local'] - [L_['run'] / 2 * MM, 0, 0]))[0]
    jc = int(((cR + cL) / 2 + HALF) / px); hw = int((cL - cR) / 2 / px)
    walled = img.copy(); walled[:, max(jc - hw, 0)] = True; walled[:, min(jc + hw, n - 1)] = True
    lab, hs = holes(walled)
    i0 = int((tp + 4 * MM + HALF) / px)
    h = lab[i0, jc]
    canal = {}
    if h and h in hs:
        m = lab == h
        col = np.nonzero(m[:, jc])[0]
        canal = dict(area_mm2=r1(m.sum() * px * px / MM / MM), ap_midline=r1(len(col) * px / MM),
                     lateral_walls='medial pedicle walls of ' + v)
    else:
        canal = 'not enclosed'
    OUT[k]['canal_mid_disc'] = canal
    lf, _ = section([G['Ligamenta flava']], Fr['o'], Fr['l'], Fr['a'], HALF)
    I, J = np.nonzero(lf)
    OUT[k]['ligamentum_flavum'] = {}
    for side, sgn in (('right', -1), ('left', 1)):
        m = sgn * (J - jc) > 0
        if m.sum() < 50:
            OUT[k]['ligamentum_flavum'][side] = 'not cut'
            continue
        P = np.c_[J[m], I[m]] * px
        c, U, _ = pca(P)
        t, s = (P - c) @ U[:, 0], (P - c) @ U[:, 1]
        mid = (t.min() + t.max()) / 2
        st = s[np.abs(t - mid) < 0.3 * MM]
        OUT[k]['ligamentum_flavum'][side] = dict(thickness=r1((st.max() - st.min() + px) / MM),
                                                 length=r1((t.max() - t.min()) / MM))

# ---- 5. facet joints: gap between upper IAP and lower SAP; joint line on an axial cut at mid-joint ----
for k in LEVELS:
    Fr, (dn, up, lo) = DF[k], DISCS[k]
    tp = first(*G[dn], Fr['o'], Fr['a'])
    Pl, Nl = samples(*G[lo], spacing=0.3 * MM)
    Pu, _ = samples(*G[up], spacing=0.3 * MM, seed=1)
    d, idx = cKDTree(Pl).query(Pu)
    s = ((Pu - Pl[idx]) * Nl[idx]).sum(1)
    M = (Pu + Pl[idx]) / 2
    q = to_local(Fr, M)
    near = (d < 4 * MM) & (q[:, 1] > tp + 2 * MM) & (np.abs(q[:, 0]) > 5 * MM)
    OUT[k]['facet'] = {}
    for side, sgn in (('right', -1), ('left', 1)):
        m = near & (sgn * q[:, 0] > 0)
        if m.sum() < 20:
            OUT[k]['facet'][side] = 'no contact zone'
            continue
        zm = np.median(q[m, 2])
        mm_ = m & (np.abs(q[:, 2] - zm) < 1.5 * MM)
        c, U, _ = pca(q[mm_][:, :2])
        ang = np.degrees(np.arctan2(abs(U[0, 0]), abs(U[1, 0])))
        ov = s[m] < 0
        OUT[k]['facet'][side] = dict(angle_from_sagittal=r1(ang), gap_median=r1(np.median(d[m & (s >= 0)]) / MM) if (m & (s >= 0)).any() else None,
                                     overlap_fraction=round(float(ov.mean()), 2),
                                     overlap_max=r1(-s[m][ov].min() / MM) if ov.any() else 0.0,
                                     mid_joint_height_mm=r1(zm / MM))

# ---- 6. root topography: Z-Anatomy L3-S1 roots exist only as the cauda equina branch curves ----
try:
    import bpy
    bpy.ops.wm.open_mainfile(filepath=os.path.join(ROOT, 'data/raw/zblend/Z-Anatomy/Startup.blend'))
    o = bpy.data.objects['Cauda equina']
    paths = []
    for sp in o.data.splines:
        bp = sp.bezier_points
        if len(bp) < 2:
            continue
        pts = []
        for p0, p1 in zip(bp[:-1], bp[1:]):
            P = [np.array(x) for x in (p0.co, p0.handle_right, p1.handle_left, p1.co)]
            for t in np.linspace(0, 1, 40):
                pts.append((1 - t) ** 3 * P[0] + 3 * (1 - t) ** 2 * t * P[1] + 3 * (1 - t) * t * t * P[2] + t ** 3 * P[3])
        paths.append(np.array(pts))
    for P in paths:                                   # join continuation curves (start == another's end)
        for Q in paths:
            if Q is not P and len(Q) and len(P) and np.linalg.norm(Q[0] - P[-1]) < 1e-4:
                P.resize(0, refcheck=False) if False else None
    M = np.array(o.matrix_world)
    roots = []
    for P in paths:
        if abs(P[0][0]) > 0.006 or np.ptp(P[:, 2]) > 0.1:   # branches start at the midline trunk; skip the trunk
            continue
        for sg, side in ((1, 'right'), (-1, 'left')):
            Q = P * [sg, 1, 1] if sg == -1 else P
            W = (np.c_[Q, np.ones(len(Q))] @ M.T)[:, :3]
            for k in LEVELS:
                f = OUT[k]['foramen'].get(side)
                if not isinstance(f, dict):
                    continue
                q = to_local(DF[k], W)
                c = np.flatnonzero(np.abs(q[:-1, 0]) < abs(f['plane_l_mm']) * MM) 
                c = [i for i in c if abs(q[i + 1, 0]) >= abs(f['plane_l_mm']) * MM]
                if not c:
                    continue
                n_cross = q[c[0], 2] / MM
                if -15 < n_cross < 30:
                    up = DISCS[k][1].split()[-1]
                    nxt = {'L3-4': 'L2-3', 'L4-5': 'L3-4', 'L5-S1': 'L4-5'}[k]
                    roots.append(dict(level=k, side=side, root=up + ' (exits ' + k + ' foramen)',
                                      cross_above_mid_disc_mm=r1(n_cross),
                                      below_upper_pedicle_edge_mm=r1(f['pedicle_lower_edge_n_mm'] - n_cross) if f.get('pedicle_lower_edge_n_mm') is not None else None,
                                      leaves_trunk_n_vs_this_disc_mm=r1(to_local(DF[k], W[:1])[0, 2] / MM),
                                      leaves_trunk_n_vs_disc_above_mm=r1(to_local(DF[nxt], W[:1])[0, 2] / MM)))
    OUT['roots'] = roots
except ImportError:
    OUT['roots'] = 'bpy not available'

# ---- 7. source z-ranges of long structures (what each level actually has) ----
OUT['z_ranges_mm'] = {n: [r1(G[n][0][:, 2].min() / MM), r1(G[n][0][:, 2].max() / MM)] for n in
                      ['Anterior longitudinal ligament', 'Posterior longitudinal ligament', 'Ligamenta flava',
                       'Interspinous ligaments', 'Supraspinous ligament', 'Intertransverse ligaments (right)',
                       'Spinal dura', 'Spinal ganglion (right)', 'Anterior root of spinal nerve (right)',
                       'Posterior root of spinal nerve (right)', 'Cauda equina', 'White matter of spinal cord']}
OUT['disc_mid_z_mm'] = {k: r1(DF[k]['o'][2] / MM) for k in DISCS}
for k in LEVELS:
    OUT[k]['nucleus_size_mm'] = [r1(x / MM) for x in np.ptp(to_local(DF[k], G['Nucleus pulposus ' + DISCS[k][0].split()[-1]][0]), 0)]
json.dump(dict(OUT, _frames={k: {a: [float(x) for x in DF[k][a]] for a in 'olan'} for k in DISCS}),
          open(os.path.join(ROOT, 'data/raw/checks.json'), 'w'), indent=1)
print(json.dumps({k: v for k, v in OUT.items()}, indent=None)[:6000])
