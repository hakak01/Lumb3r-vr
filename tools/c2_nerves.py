"""Phase C2 steps 5-6: small nerves (approx courses, radius from typical sizes).
- Dorsal ramus + medial branch L3 and L4 (Bogduk): the dorsal ramus leaves the spinal nerve just outside the foramen,
  crosses the upper border of the transverse process of the vertebra BELOW at its junction with the superior articular
  process (L3 medial branch at L4, L4 at L5: the radiofrequency target), runs caudally in the groove at the root of the
  SAP (under the mamillo-accessory ligament) and ends medially in multifidus.
- L5 dorsal ramus: crosses the sacral ala in the groove between the ala and the S1 superior articular process.
- Sinuvertebral nerve L3, L4, L5: from the ventral ramus just beyond the DRG, back through the foramen anterior to the
  DRG, across the back of the disc below the pedicle (L4 -> L4-5) to the lateral edge of the PLL, then an ascending
  branch (ASC mm along the PLL behind the body above) and a short descending branch (DESC mm).
Paths keep >= 0.1 mm off bone, disc, ligament and neural parts (voxel field F2). Units mm."""
import numpy as np
from scipy.spatial import cKDTree
import lgeom, gapgeom as G
import c1_roots, c2_fat

R_DR, R_MB, R_SVN = 0.6, 0.4, 0.25
ASC, DESC = 12.0, 5.0
MB = (('L3', 'L4', 'L4 transverse process', 'L4 superior articular process'),
      ('L4', 'L5', 'L5 transverse process', 'L5 superior articular process'),
      ('L5', 'S1', 'S1 ala', 'S1 superior articular process'))
DISC = {'L3': 1031.0, 'L4': 997.0, 'L5': 962.0}


def along(P, dist):
    d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]
    return P[min(int(np.searchsorted(d, dist)), len(P) - 1)]


def groove(D, tp, sap, side):
    T, Tn = lgeom.samples(*D['%s (%s)' % (tp, side)], spacing=0.4); A = lgeom.samples(*D['%s (%s)' % (sap, side)], spacing=0.4)[0]
    d, _ = cKDTree(A).query(T)
    sg = 1 if side == 'left' else -1
    m = (d < 3) & (Tn[:, 1] > 0.3) & (sg * T[:, 0] > sg * A[:, 0].mean() + 1)   # dorsal TP surface, lateral to the SAP
    Q, N = T[m], Tn[m]
    i = int(np.argmax(Q[:, 2])); W1 = Q[i] + 0.9 * N[i]  # upper border at the junction
    low = (Q[:, 2] < Q[i, 2] - 3) & (Q[:, 2] > Q[i, 2] - 9)
    if low.any():
        j = np.flatnonzero(low)[np.argmax(Q[low, 1])]; W2 = Q[j] + 0.9 * N[j]   # most dorsal point lower in the groove
    else:
        W2 = W1 + np.array([0, 1.0, -4.0])
    return W1, W2


def medial_branches(D, roots, F2, log):
    out = []
    for lv, below, tp, sap in MB:
        for side, sg in (('left', 1), ('right', -1)):
            r = next(x for x in roots if x['level'] == lv and x['side'] == side)
            S0 = along(r['paths']['nerve'], 3.0)
            W1, W2 = groove(D, tp, sap, side)
            W0 = 0.5 * (S0 + W1) + np.array([0, 2.0, 1.0])
            W3 = W2 + np.array([-sg * 7.0, 3.0, -6.0])          # medially, dorsally and down into multifidus
            segs = [S0[None]]
            for A, B in ((S0, W0), (W0, W1), (W1, W2), (W2, W3)):         # free routes between the waypoints
                sgm = F2.route(A, B, R_DR, clear=0.1, margin=5.0)
                segs.append((sgm if sgm is not None else G.catmull(np.array([A, B]), 6))[1:])
            P = c1_roots.resample(G.smooth1d(np.vstack(segs), 1.5), 1.0)
            P = c1_roots.resample(F2.relax(P, R_DR, clear=0.1, keep=(0,), iters=60), 1.0)
            i1 = int(np.argmin(np.linalg.norm(P - W1, axis=1)))
            rad = np.where(np.arange(len(P)) < i1, R_DR, R_MB) if lv != 'L5' else np.full(len(P), R_DR)
            rad = G.smooth1d(rad.astype(float), 2.0)
            gap = float(np.linalg.norm(P[i1] - W1))
            name = ('%s dorsal ramus (%s)' if lv == 'L5' else '%s medial branch (%s)') % (lv, side)
            where = 'ala / S1 SAP groove' if lv == 'L5' else '%s TP / SAP junction' % below
            log('  %s: crosses the %s (moved %.1f mm from the target), %.0f mm long' % (
                name, where, gap, np.linalg.norm(np.diff(P, axis=0), axis=1).sum()))
            out.append(dict(name=name, level=lv, side=side, mesh=G.tube(P, rad, 8), target=W1, path=P))
    return out


def sinuvertebral(K, roots, F2, Rw, log):
    out = []
    for lv, zd in DISC.items():
        for side, sg in (('left', 1), ('right', -1)):
            r = next(x for x in roots if x['level'] == lv and x['side'] == side)
            Gc, u, a = r['drg'], r['paths']['u'], r['w'] / 2
            S0 = along(r['paths']['nerve'], 2.0) + np.array([0, -1.2, 0])         # ventral side of the ventral ramus
            ant = G.unit(np.array([0, -1.0, 0]) - (u @ [0, -1.0, 0]) * u)
            S1 = Gc + ant * (a + 1.2)                                             # anterior to the DRG
            k = c2_fat.kz(K, zd)
            def wall_pt(th, z_k):
                i = int(round(th)) % 360
                return K['C'][z_k] + (Rw[z_k, i] - 0.45) * (np.cos(np.radians(th)) * K['L'][z_k] + np.sin(np.radians(th)) * K['A'][z_k])
            S2 = wall_pt(270 + sg * 62, k); S3 = wall_pt(270 + sg * 24, k)
            ku = c2_fat.kz(K, zd + ASC); kd = c2_fat.kz(K, zd - DESC)
            asc = [wall_pt(270 + sg * 22, kk) for kk in np.linspace(k, ku, 5).astype(int)]
            des = [wall_pt(270 + sg * 26, kk) for kk in np.linspace(k, kd, 3).astype(int)]
            trunk = c1_roots.resample(G.catmull(np.array([S0, S1, S2, S3] + asc[1:]), 10), 0.5)
            for _ in range(2):
                trunk = c1_roots.resample(F2.relax(trunk, R_SVN, clear=0.1, keep=(0,), iters=60), 1.0)
            j = int(np.argmin(np.linalg.norm(trunk - S3, axis=1)))
            br = c1_roots.resample(G.catmull(np.array([trunk[j]] + des[1:]), 10), 1.0)
            br = F2.relax(br, R_SVN, clear=0.1, keep=(0,), iters=60)
            mesh = G.merge([G.tube(trunk, R_SVN, 6), G.tube(br, R_SVN * 0.8, 6)])
            log('  %s sinuvertebral nerve (%s): %.0f mm to the PLL, ascending branch to z %.0f, descending to z %.0f' % (
                lv, side, np.linalg.norm(np.diff(trunk[:j + 1], axis=0), axis=1).sum(), trunk[-1, 2], br[-1, 2]))
            out.append(dict(name='%s sinuvertebral nerve (%s)' % (lv, side), level=lv, side=side, mesh=mesh))
    return out


def build(K, D, flav, roots, F2, log=print):
    Rw = c2_fat.wall(K, flav)
    return medial_branches(D, roots, F2, log), sinuvertebral(K, roots, F2, Rw, log)
