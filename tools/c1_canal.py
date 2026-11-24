"""Phase C1: the bony canal of this model, measured from lumbar_raw.glb.
Canal centreline (mid-L2 to the sacral hiatus), slice frames perpendicular to it every 1 mm, and in each slice the polar
distance from the centreline to the first wall (bone / disc / PLL) with its label. Units: mm, Z-Anatomy world
(+x patient left, +y posterior, +z up). Cached in data/raw/c1_canal.npz.  python3 -I tools/c1_canal.py"""
import os, sys
import numpy as np
from scipy import ndimage
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import lgeom, gapgeom as G

RAW = os.path.join(ROOT, 'data/raw/lumbar_raw.glb')
CACHE = os.path.join(ROOT, 'data/raw/c1_canal.npz')
NT, RMAX, STEP = 360, 26.0, 0.1                     # polar bins (1 deg), max ray (mm), ray step (mm)
# wall groups -> label id (1-6 vertebrae: L2, L3, L4, L5, sacrum, coccyx)
VERT = ['L2',   # L2 label also holds L1
        'L3', 'L4', 'L5', 'S', 'Co']
LAB = dict(zip(VERT, range(1, 7)), disc=7, pll=8, flavum=9, other=10)


def load():
    """{name: (V mm, F)} in Z-Anatomy coordinates."""
    return {n: (V * 1000.0, F) for n, (V, F) in lgeom.load(RAW).items()}


def groups(D):
    """Closed wall meshes per label (merged)."""
    g = {k: [] for k in LAB}
    for n, vf in D.items():
        if n in ('Vertebra L1', 'Vertebra L2'):
            g['L2'].append(vf)
        elif n.startswith(('L3 ', 'L4 ', 'L5 ')) and not any(k in n for k in ('root', 'ganglion')):
            g[n[:2]].append(vf)
        elif n.startswith('S1 ') and 'root' not in n or n == 'Sacrum (rest)':
            g['S'].append(vf)
        elif n == 'Coccyx':
            g['Co'].append(vf)
        elif n.startswith(('Annulus fibrosus L1', 'Nucleus pulposus L1', 'Annulus fibrosus L2', 'Annulus fibrosus L3', 'Annulus fibrosus L4', 'Annulus fibrosus L5',
                           'Nucleus pulposus L2', 'Nucleus pulposus L3', 'Nucleus pulposus L4', 'Nucleus pulposus L5')):
            g['disc'].append(vf)
        elif n.startswith('Posterior longitudinal ligament'):
            g['pll'].append(vf)
        elif n.startswith(('Interspinous ligament', 'Intertransverse ligament', 'Supraspinous ligament')):
            g['other'].append(vf)
    return {k: G.merge(v) for k, v in g.items() if v}


def label_image(gm, o, e1, e2, half, px, skip=()):
    lab = None
    for k, (V, F) in gm.items():
        if k in skip:
            continue
        img, _ = lgeom.section([(V, F)], o, e1, e2, half, px)
        if lab is None:
            lab = np.zeros(img.shape, np.uint8)
        lab[img & (lab == 0)] = LAB[k]
    return lab


def polar(lab, half, px, centre_uv=(0.0, 0.0)):
    """First wall hit along NT rays: (r mm, label). r = RMAX if nothing is hit."""
    th = np.radians(np.arange(NT))
    t = np.arange(1, int(RMAX / STEP) + 1) * STEP
    u = centre_uv[0] + np.cos(th)[:, None] * t; v = centre_uv[1] + np.sin(th)[:, None] * t
    i = np.clip(((v + half) / px).astype(int), 0, lab.shape[0] - 1)
    j = np.clip(((u + half) / px).astype(int), 0, lab.shape[1] - 1)
    L = lab[i, j]
    hit = L > 0
    k = np.where(hit.any(1), hit.argmax(1), len(t) - 1)
    r = np.where(hit.any(1), t[k], RMAX)
    return r, np.where(hit.any(1), L[np.arange(NT), k], 0)


def centreline(gm, z0=1128.0, z1=878.0, start=(0.0, 37.0)):
    """Canal centres on horizontal slices (largest free area round the previous centre), smoothed."""
    half, px = 20.0, 0.2
    c = np.array(start); out = []
    for z in np.arange(z0, z1 - 0.1, -1.0):
        o = np.array([c[0], c[1], z])
        lab = label_image(gm, o, np.array([1.0, 0, 0]), np.array([0, 1.0, 0]), half, px, skip=('other',))
        n = lab.shape[0]; yy, xx = (np.mgrid[:n, :n] + 0.5) * px - half
        free = (lab == 0) & (xx ** 2 + yy ** 2 < 11.0 ** 2)
        cl, k = ndimage.label(free)
        if k == 0:
            out.append([c[0], c[1], z]); continue
        dist = ndimage.distance_transform_edt(free)
        best = cl[np.unravel_index(dist.argmax(), dist.shape)]
        m = cl == best
        new = np.array([0.0, c[1] + yy[m].mean()])   # midline by construction (x = 0, the model is symmetric)
        c = c + np.clip(new - c, -1.5, 1.5)
        out.append([0.0, c[1], z])
    P = np.array(out)
    P[:, 1] = G.smooth1d(P[:, 1], 5.0)
    return P


def frames(P, step=1.0):
    """Resample the centreline by arclength; frames: t (down the canal), l (patient left), a (posterior)."""
    d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]
    s = np.arange(0, d[-1], step)
    C = np.stack([np.interp(s, d, P[:, k]) for k in range(3)], 1)
    T = G.unit(np.gradient(C, axis=0))
    n = -T                                         # cranial direction
    L = np.tile([1.0, 0, 0], (len(C), 1))
    L = G.unit(L - (L * n).sum(1, keepdims=True) * n)
    A = np.cross(n, L)                             # (left x up) -> posterior? check sign below
    A *= np.sign(A[:, 1:2].mean())                 # make +a posterior (+y)
    return s, C, L, A, n


def build(save=True, log=print):
    D = load(); gm = groups(D)
    P = centreline(gm)
    s, C, L, A, N = frames(P)
    half, px = RMAX, 0.15
    R = np.zeros((len(s), NT), np.float32); Lb = np.zeros((len(s), NT), np.uint8)
    Rv = np.full((len(s), 6, NT), RMAX, np.float32)           # first hit of each vertebra alone
    for k in range(len(s)):
        lab = label_image(gm, C[k], L[k], A[k], half, px)
        R[k], Lb[k] = polar(lab, half, px)
        for v in range(6):
            if (lab == v + 1).any():
                Rv[k, v] = polar(np.where(lab == v + 1, lab, 0), half, px)[0]
    if save:
        np.savez_compressed(CACHE, s=s, C=C, L=L, A=A, N=N, R=R, Lb=Lb, Rv=Rv)
    log('canal: %d slices, centreline z %.0f -> %.0f mm' % (len(s), C[0, 2], C[-1, 2]))
    return dict(s=s, C=C, L=L, A=A, N=N, R=R, Lb=Lb, Rv=Rv)


def get(log=print):
    if os.path.exists(CACHE):
        z = np.load(CACHE)
        return {k: z[k] for k in z.files}
    return build(log=log)


if __name__ == '__main__':
    K = build()
    for k in range(0, len(K['s']), 10):
        r, lb = K['R'][k], K['Lb'][k]
        print('s %3d  z %6.1f y %5.1f  ant %4.1f post %4.1f  L %4.1f R %4.1f  labels a/p %d/%d' % (
            K['s'][k], K['C'][k, 2], K['C'][k, 1], r[270], r[90], r[0], r[180], lb[270], lb[90]))
