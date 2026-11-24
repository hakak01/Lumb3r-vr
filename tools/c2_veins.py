"""Phase C2 step 4: internal vertebral venous plexus (Groen 1997: anterior part constant, posterior very variable).
- Anterior internal plexus: paired longitudinal channels in the anterior epidural space behind the vertebral bodies,
  lateral to the PLL (PHI_BODY deg from the anterior midline behind each body, PHI_DISC at each disc, approx), centred
  in the gap between dural sac and canal wall, radius = half the gap (0.4-1.5 mm).
- Basivertebral vein of L3, L4, L5: Y-shaped vein inside the body, out through the basivertebral foramen (posterior
  midline, mid-height) into a transverse retrocorporeal anastomosis joining both channels (under the PLL).
- Intervertebral veins L3-4, L4-5, L5-S1: from each channel through the foramen to the nearest Z-Anatomy lumbar /
  ascending lumbar / iliolumbar vein of the same side.
- Posterior internal plexus: one simple thin pair (r 0.4 mm) behind the sac; hidden by default.
Every vessel keeps >= 0.1 mm off bone, disc, ligament and neural parts (voxel field). Units mm."""
import numpy as np
from scipy.spatial import cKDTree
import gapgeom as G
import c1_roots, c2_fat

PHI_BODY, PHI_DISC = 35.0, 55.0
Z0, Z1 = 1072.0, 958.0                       # plexus from mid-L3 body to the upper sacral canal (approx)
DISC_Z = (1066.0, 1031.0, 997.0, 962.0)
BODIES = (('L3', 1049.0), ('L4', 1014.0), ('L5', 980.0))


def channel_angle(z):
    d = min(abs(z - dz) for dz in DISC_Z)
    f = np.clip(1 - d / 8.0, 0, 1)                # near a disc -> lateral
    return PHI_BODY + (PHI_DISC - PHI_BODY) * f


def at(K, k, th, r):
    a = np.radians(th)
    return K['C'][k] + r * (np.cos(a) * K['L'][k] + np.sin(a) * K['A'][k])


def channels(K, sac, Rw, F2):
    ks = range(c2_fat.kz(K, Z0), c2_fat.kz(K, Z1) + 1)
    out = {}
    for side, sg in (('left', 1), ('right', -1)):
        P, R = [], []
        for k in ks:
            th = 270 + sg * channel_angle(K['C'][k, 2]); i = int(round(th)) % 360
            r_in = np.interp(th % 360, np.arange(360), sac['r'][k]) + 0.2; r_out = Rw[k, i] - 0.2
            if r_out > r_in + 6:
                r_out = r_in + 3.0
            P.append(at(K, k, th, 0.5 * (r_in + r_out))); R.append(np.clip(0.5 * (r_out - r_in) - 0.1, 0.4, 1.5))
        P = G.smooth1d(np.array(P), 2.0); R = G.smooth1d(np.array(R), 2.0)
        P = F2.relax(P, R, clear=0.1, keep=(), iters=80)
        R = np.maximum(np.minimum(R, G.smooth1d(F2(P) - 0.45, 1.0)), 0.3)          # shrink where the gap is tight
        out[side] = (P, R)
    return out


def basivertebral(K, D, ch, F2):
    out = []
    for v, z in BODIES:
        k = c2_fat.kz(K, z); rb = K['R'][k, 270]
        hole = at(K, k, 270, rb + 0.3)                                # just inside the posterior cortex
        Bc = D['%s body' % v][0].mean(0); Bc[0] = 0.0
        fw = G.unit(Bc - hole); deep = hole + fw * 6.0
        Y = [G.catmull(np.array([deep + sg * 5 * K['L'][k] + fw * 3, deep, hole]), 6) for sg in (1, -1)]
        legs = []
        for side in ('left', 'right'):
            P, R = ch[side]; j = int(np.argmin(np.linalg.norm(P - hole, axis=1)))
            mid = 0.5 * (hole + P[j]) + K['A'][k] * 0.2
            legs.append(G.catmull(np.array([hole, mid, P[j]]), 6))
        parts = [G.tube(p, 0.6, 8) for p in Y] + [G.tube(p, 0.6, 8) for p in legs]
        out.append(dict(name='%s basivertebral vein' % v, level=v, mesh=G.merge(parts)))
    return out


def targets(D, side):
    keep = []
    for n, (V, F) in D.items():
        lo = n.lower()
        if 'vein' not in lo or 'cava' in lo or 'iliac' in lo:
            continue
        if ('(%s)' % side) in n or lo.startswith(side + ' ascending'):
            keep.append(V)
    return np.vstack(keep)


def intervertebral(D, ch, F2, log):
    out = []
    for fo in ('L3-4', 'L4-5', 'L5-S1'):
        for side, sg in (('left', 1), ('right', -1)):
            c = c1_roots.foramen(fo, side)
            P, R = ch[side]; j = int(np.argmin(np.linalg.norm(P - c, axis=1)))
            T = targets(D, side); B = T[cKDTree(T).query(c)[1]]
            X = c + np.array([sg * 9.0, -2.0, -1.5])                     # just outside the foramen, low (approx)
            seg = F2.route(P[j], X, 0.5, clear=0.1, margin=6.0)
            if seg is None:
                seg = G.catmull(np.array([P[j], c, X]), 6)
            Bb = np.clip(B, F2.lo + 1, F2.lo + F2.n * 0.5 - 1)
            seg2 = F2.route(X, Bb, 0.5, clear=0.1, margin=8.0)
            if seg2 is None:
                seg2 = G.catmull(np.array([X, 0.5 * (X + Bb), Bb]), 8)
            path = np.vstack([seg[:-1], seg2] + ([B[None]] if np.linalg.norm(B - Bb) > 0.5 else []))
            path = F2.relax(c1_roots.resample(path, 0.7), 0.5, clear=0.1, keep=(0, -1))
            rad = np.interp(np.arange(len(path)), [0, len(path) - 1], [min(R[j], 0.8), 1.0])
            log('  intervertebral vein %s %-5s: %.0f mm to the %s vein' % (
                fo, side, np.linalg.norm(np.diff(path, axis=0), axis=1).sum(), 'lumbar/ascending/iliolumbar'))
            out.append(dict(name='Intervertebral vein %s (%s)' % (fo, side), level=fo, side=side, mesh=G.tube(path, rad, 8)))
    return out


def posterior(K, sac, Rw, F2):
    ks = range(c2_fat.kz(K, Z0), c2_fat.kz(K, Z1) + 1); parts = []
    for sg in (1, -1):
        P = []
        for k in ks:
            th = 90 - sg * 42; i = int(round(th)) % 360
            r_in = np.interp(th, np.arange(360), sac['r'][k]) + 0.2; r_out = min(Rw[k, i] - 0.2, r_in + 3)
            P.append(at(K, k, th, 0.5 * (r_in + r_out)))
        P = F2.relax(G.smooth1d(np.array(P), 3.0), 0.4, clear=0.1, keep=())
        parts.append(G.tube(P, 0.4, 8))
    return G.merge(parts)


def build(K, D, sac, flav, F2, log=print):
    Rw = c2_fat.wall(K, flav)
    ch = channels(K, sac, Rw, F2)
    out = []
    for side in ('left', 'right'):
        P, R = ch[side]
        log('  anterior internal venous plexus %s: z %.0f -> %.0f, radius %.1f-%.1f mm, min clearance %.2f' % (
            side, P[0, 2], P[-1, 2], R.min(), R.max(), float((F2(P) - R).min())))
        out.append(dict(name='Anterior internal vertebral venous plexus (%s)' % side, side=side, mesh=G.tube(P, R, 10)))
    out += basivertebral(K, D, ch, F2)
    out += intervertebral(D, ch, F2, log)
    out.append(dict(name='Posterior internal vertebral venous plexus', mesh=posterior(K, sac, Rw, F2), hidden=True))
    return out
