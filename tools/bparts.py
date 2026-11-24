"""Phase A2: anatomical landmarks and cutting regions for L3-L5 and S1 (numpy; Z-Anatomy world, metres).
Each part = remaining bone ∩ a convex region (half-spaces in the bone's local frame: l = patient left,
a = posterior, n = up). Regions are applied in order, so neighbouring parts share the same cut face.
Rules (SPEC 4a): body | pedicle = the narrowest bridge from body to arch | SAP above the pedicle top |
IAP below the lamina's lower edge | pars = lateral column between SAP and IAP | lamina = medial part | TP lateral."""
import numpy as np
from scipy import ndimage
from scipy.spatial import cKDTree
from lgeom import MM, to_world, to_local, ray, section, unit, samples

BIG = 0.2


def intervals(V, F, o, d, start=-0.06):
    """Bone intervals (entry, exit) along o + t d, t measured from o."""
    t = ray(V, F, o + start * d, d) + start
    t = t[: len(t) // 2 * 2]
    return t.reshape(-1, 2)


def side_comp(img, px, half, sg, min_l=4 * MM):
    lab, k = ndimage.label(img)
    best = None
    for c in range(1, k + 1):
        ii, jj = np.nonzero(lab == c)
        if sg * (jj.min() * px - half) > -1 * MM and sg * (jj.mean() * px - half) > min_l and \
                (best is None or len(ii) > len(best[0])):
            best = (ii, jj)
    return best


def facet_zone(Vb, Fb, Vo, Fo, Fr, wall):
    """Facet contact of bone b with neighbour o: b's surface points within 4 mm of o, behind the bodies.
    Returns {side: (l, a, n) local points} in b's frame."""
    Pb, _ = samples(Vb, Fb, 0.4 * MM)
    Po, _ = samples(Vo, Fo, 0.4 * MM, seed=1)
    d, _ = cKDTree(Po).query(Pb)
    q = to_local(Fr, Pb[d < 4 * MM])
    q = q[(q[:, 1] > wall + 5 * MM) & (np.abs(q[:, 0]) > 5 * MM)]
    return {'right': q[q[:, 0] < 0], 'left': q[q[:, 0] > 0]}


def vertebra(V, F, Fr, above, below):
    """Landmarks of a lumbar vertebra in its frame (metres). above/below = neighbour bones (V, F)."""
    o, a = Fr['o'], Fr['a']
    L = dict(wall=intervals(V, F, o, a)[0][1])
    wall = L['wall']
    # lamina: paramedian rays (l = +-7 mm) at heights -30..+15 mm; first interval starting behind the canal
    lam = []
    for n in np.arange(-30, 15.1, 1.0):
        for l in (-7, 7):
            iv = intervals(V, F, to_world(Fr, [l * MM, 0, n * MM]), a)
            iv = [x for x in iv if wall + 8 * MM < x[0] < wall + 35 * MM]
            if iv:
                lam.append((n * MM, iv[0][0], iv[0][1]))
    lam = np.array(lam)
    L['n_lam'] = [lam[:, 0].min(), lam[:, 0].max()]
    L['a_lam_ant'], L['a_lam_post'] = np.median(lam[:, 1]), np.median(lam[:, 2])
    L['a_cc'] = (wall + lam[:, 1].min()) / 2                      # canal AP centre
    # top endplate and body half-width 4 mm below it
    top, bot = intervals(V, F, o, Fr['n'])[0][1], -intervals(V, F, o, -Fr['n'])[0][1]
    hw = []
    for nn in (top - 4 * MM, bot + 4 * MM):                     # body half-width; the smaller avoids the TP roots
        img, px = section([(V, F)], to_world(Fr, [0, 0, nn]), Fr['l'], Fr['a'], 60 * MM)
        lab, _ = ndimage.label(img)
        c = lab[int(60 * MM / px), int(60 * MM / px)]
        jj = np.nonzero(lab == c)[1]
        hw.append(max(abs(jj.min() * px - 60 * MM), abs(jj.max() * px - 60 * MM)))
    L['top'], L['bottom'], L['body_hw'] = top, bot, min(hw)
    sup, inf = facet_zone(V, F, *above, Fr, wall), facet_zone(V, F, *below, Fr, wall)
    for side, sg in (('right', -1), ('left', 1)):
        P = {}
        for x in np.arange(0.5, 10.01, 0.5):                      # body-pedicle boundary: sides separate
            img, px = section([(V, F)], to_world(Fr, [0, wall + x * MM, 0]), Fr['l'], Fr['n'], 60 * MM)
            cmp_ = side_comp(img, px, 60 * MM, sg)
            if cmp_ is not None and sg * (cmp_[1].min() * px - 60 * MM) > 2 * MM:
                P['a_bp'] = wall + x * MM
                break
        img, px = section([(V, F)], to_world(Fr, [0, P['a_bp'] + 1.5 * MM, 0]), Fr['l'], Fr['n'], 60 * MM)
        ii, jj = side_comp(img, px, 60 * MM, sg)
        lm = jj * px - 60 * MM
        inner = sg * lm < sg * lm.mean()                           # medial half of the component = pedicle
        P['n_p'] = [ii[inner].min() * px - 60 * MM, ii[inner].max() * px - 60 * MM]
        npc = sum(P['n_p']) / 2
        # axial scan at pedicle mid-height: medial wall, isthmus run, lateral wall
        img, px = section([(V, F)], to_world(Fr, [0, 0, npc]), Fr['l'], Fr['a'], 62 * MM)
        j0, rows = int(62 * MM / px), []
        for i in range(int((P['a_bp'] + 62 * MM) / px), int((L['a_cc'] + 62 * MM) / px)):
            if img[i, j0]:
                continue
            j = j0
            while 0 < j < img.shape[1] - 1 and not img[i, j]:
                j += sg
            j1 = j
            while 0 < j < img.shape[1] - 1 and img[i, j]:
                j += sg
            if 0 < j < img.shape[1] - 1:
                rows.append((j1 * px - 62 * MM, j * px - 62 * MM))
        R = np.array(rows)
        P['l_med'] = np.median(R[:, 0]) if len(R) else sg * 10 * MM
        run = np.abs(R[:, 1] - R[:, 0]) if len(R) else np.array([1.0])
        k = int(np.argmin(run))
        ok = len(R) and run[k] < 15 * MM and sg * R[k, 1] > sg * P['l_med'] + 4 * MM
        P['l_lat'] = R[k, 1] if ok else None                        # None: TP merges with the pedicle (L5)
        P['l_root'] = (P['l_lat'] + sg * 0.5 * MM) if P['l_lat'] is not None else sg * L['body_hw']
        P['a_pe'] = max(L['a_cc'], P['a_bp'] + 3 * MM)                  # pedicle posterior end
        # transverse process: bone lateral to the root plane, in front of the SAP (a <= a_pe + 6 mm)
        q = to_local(Fr, V)
        P['a_tp'] = wall - 6 * MM if P['l_lat'] is None else P['a_bp'] - 1 * MM   # L5 TP reaches the body side
        m = (sg * q[:, 0] > sg * P['l_root'] + 1 * MM) & (q[:, 1] - 0.6 * sg * (q[:, 0] - P['l_root']) < P['a_pe'] + 6 * MM) & (q[:, 1] > P['a_tp'])
        P['n_tp'] = [q[m, 2].min(), q[m, 2].max()] if m.any() else P['n_p']
        # articular processes from the facet contact zones (SAP: with the bone above; IAP: with the bone below)
        P['n_sap'] = min(P['n_p'][1], np.percentile(sup[side][:, 2], 5)) if len(sup[side]) > 20 else P['n_p'][1]
        P['n_iap'] = np.percentile(inf[side][:, 2], 95) if len(inf[side]) > 20 else L['n_lam'][0]
        P['l_iap'] = (np.percentile(sg * inf[side][:, 0], 5) - 6 * MM) * sg if len(inf[side]) > 20 else sg * 8 * MM
        L[side] = P
    return L


def hs(normal, offset):
    """Half-space {x : normal . x <= offset} in local (l, a, n) coordinates."""
    return (np.asarray(normal, float), float(offset))


def vertebra_regions(L, name):
    """Ordered (part name, side, [half-spaces]); the last region takes the rest."""
    out = [('%s spinous process' % name, 'mid', [hs([0, -1, 0], -L['a_lam_post']), hs([1, 0, 0], 10 * MM), hs([-1, 0, 0], 10 * MM)])]
    for side, sg in (('right', -1), ('left', 1)):
        P = L[side]
        out.append(('%s transverse process (%s)' % (name, side), side,
                    [hs([-sg, 0, 0], -sg * P['l_root']), hs([0, 0, 1], P['n_tp'][1] + 1 * MM),
                     hs([0, 0, -1], -(P['n_tp'][0] - 1 * MM)), hs([0, -1, 0], -P['a_tp']),
                     hs([-0.6 * sg, 1, 0], P['a_pe'] + 6 * MM - 0.6 * sg * P['l_root'])]))   # back edge slopes: TP tips point back
    a_bp = min(L['right']['a_bp'], L['left']['a_bp'])
    # body + the lower posterior rim just behind the cut (union of two convex blocks)
    out.append(('%s body' % name, 'mid', [[hs([0, 1, 0], a_bp)],
                                          [hs([0, 1, 0], a_bp + 4 * MM), hs([0, 0, 1], L['bottom'] + 4 * MM),
                                           hs([1, 0, 0], 16 * MM), hs([-1, 0, 0], 16 * MM)]]))
    for side, sg in (('right', -1), ('left', 1)):
        P = L[side]
        out.append(('%s pedicle (%s)' % (name, side), side,
                    [hs([-sg, 0, 0], 0), hs([0, 1, 0], P['a_pe']), hs([0, 0, 1], P['n_p'][1] + 3 * MM),
                     hs([0, 0, -1], -(P['n_p'][0] - 4 * MM))]))
    for side, sg in (('right', -1), ('left', 1)):
        P = L[side]
        out.append(('%s superior articular process (%s)' % (name, side), side,
                    [hs([-sg, 0, 0], -(sg * P['l_med'] - 3 * MM)), hs([0, 0, -1], -P['n_sap'])]))
    for side, sg in (('right', -1), ('left', 1)):
        P = L[side]
        out.append(('%s inferior articular process (%s)' % (name, side), side,
                    [hs([-sg, 0, 0], -sg * P['l_iap']), hs([0, 0, 1], P['n_iap'])]))
    for side, sg in (('right', -1), ('left', 1)):
        P = L[side]
        out.append(('%s pars interarticularis (%s)' % (name, side), side, [hs([-sg, 0, 0], -sg * P['l_med'])]))
    out.append(('%s lamina (right)' % name, 'right', [hs([1, 0, 0], 0)]))
    out.append(('%s lamina (left)' % name, 'left', []))
    return out


def sacrum(V, F, Fr, disc, l5):
    """S1 landmarks. Fr: frame of the L5-S1 disc (moved to the S1 endplate centre here). disc, l5 = (V, F)."""
    o, n = Fr['o'], Fr['n']
    t = intervals(V, F, o, -n)
    Fr = dict(Fr, o=o - t[0][0] * n)                         # S1 endplate centre
    L = dict(frame=Fr)
    L['hw'] = max(intervals(*disc, Fr['o'] + 3 * MM * n, Fr['l'])[0][1],
                  intervals(*disc, Fr['o'] + 3 * MM * n, -Fr['l'])[0][1])          # S1 endplate half-width
    L['wall'] = intervals(V, F, to_world(Fr, [0, 0, -5 * MM]), Fr['a'])[0][1]   # posterior wall of S1 body
    # canal: enclosed hole behind the body on axial cuts
    rings = []
    for nn in np.arange(-3, -40, -1.0):
        img, px = section([(V, F)], to_world(Fr, [0, 0, nn * MM]), Fr['l'], Fr['a'], 60 * MM)
        lab, k = ndimage.label(~img)
        border = set(np.unique(np.r_[lab[0], lab[-1], lab[:, 0], lab[:, -1]]))
        for c in range(1, k + 1):
            if c in border:
                continue
            ii, jj = np.nonzero(lab == c)
            if len(ii) * px * px > 40 * MM * MM and abs(jj.mean() * px - 60 * MM) < 5 * MM and ii.mean() * px - 60 * MM > L['wall']:
                rings.append((nn * MM, ii.min() * px - 60 * MM, ii.max() * px - 60 * MM,
                              (jj.max() - jj.min()) * px / 2))
    R = np.array(rings)
    L['ring_n'] = [R[:, 0].min(), R[:, 0].max()]
    L['canal_a'] = [np.median(R[:, 1]), np.median(R[:, 2])]
    L['canal_hw'] = np.median(R[:, 3])
    # S1 anterior foramina: highest holes lateral to the midline on coronal cuts in front of the canal
    L['n_s12'], L['l_for'] = -28 * MM, None
    for da in (8, 5, 12, 16, 3):
        img, px = section([(V, F)], to_world(Fr, [0, L['wall'] - da * MM, 0]), Fr['l'], Fr['n'], 70 * MM)
        lab, k = ndimage.label(~img)
        border = set(np.unique(np.r_[lab[0], lab[-1], lab[:, 0], lab[:, -1]]))
        holes = []
        for c in range(1, k + 1):
            if c in border:
                continue
            ii, jj = np.nonzero(lab == c)
            l, nn = jj.mean() * px - 70 * MM, ii.mean() * px - 70 * MM
            if 10 * MM < abs(l) < 50 * MM and -60 * MM < nn < -10 * MM and len(ii) * px * px > 8 * MM * MM:
                holes.append((nn, l, np.abs(jj * px - 70 * MM).min()))
        if holes:
            top = max(h[0] for h in holes)
            s1 = [h for h in holes if h[0] > top - 8 * MM]
            L['n_s12'] = float(np.mean([h[0] for h in s1]))
            L['l_for'] = float(np.min([h[2] for h in s1]))
            L['for_cut_a'] = L['wall'] - da * MM
            break
    zone = facet_zone(V, F, *l5, Fr, L['wall'] - 5 * MM)
    for side, sg in (('right', -1), ('left', 1)):
        z = zone[side]
        L[side] = dict(n_sap=np.percentile(z[:, 2], 5) if len(z) > 20 else -5 * MM,
                       l_sap=np.percentile(np.abs(z[:, 0]), 98) + 4 * MM if len(z) > 20 else L['canal_hw'] + 15 * MM)
    return L


def sacrum_regions(L):
    out = []
    a0, a1 = L['canal_a']
    for side, sg in (('right', -1), ('left', 1)):
        out.append(('S1 superior articular process (%s)' % side, side,
                    [hs([-sg, 0, 0], -(L['canal_hw'] - 3 * MM)), hs([sg, 0, 0], L[side]['l_sap']),
                     hs([0, 0, -1], -L[side]['n_sap']), hs([0, -1, 0], -(a0 + 3 * MM))]))
    for side, sg in (('right', -1), ('left', 1)):
        out.append(('S1 lamina (%s)' % side, side,
                    [hs([-sg, 0, 0], 0), hs([sg, 0, 0], L['canal_hw'] + 6 * MM), hs([0, -1, 0], -(a0 + a1) / 2),
                     hs([0, 0, -1], -L['n_s12'])]))
    out.append(('S1 body', 'mid', [[hs([1, 0, 0], L['hw'] + 1 * MM), hs([-1, 0, 0], L['hw'] + 1 * MM),
                                    hs([0, 0, -1], -L['n_s12']), hs([0, 1, 0], a0 + 1 * MM)],
                                   [hs([1, 0, 0], L['canal_hw']), hs([-1, 0, 0], L['canal_hw']),       # canal floor
                                    hs([0, 0, -1], -L['n_s12']), hs([0, 1, 0], (a0 + a1) / 2)]]))
    for side, sg in (('right', -1), ('left', 1)):
        out.append(('S1 ala (%s)' % side, side, [[hs([-sg, 0, 0], -(L['hw'] + 1 * MM)), hs([0, 0, -1], -L['n_s12'])],
                                                 [hs([-sg, 0, 0], -L['canal_hw']), hs([0, -1, 0], -(a0 + 1 * MM)),
                                                  hs([0, 0, -1], -L['n_s12'])]]))   # lateral mass incl. the S1 pedicle
    out.append(('Sacrum (rest)', 'mid', []))
    return out
