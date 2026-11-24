"""Geometry helpers for lumbar measurements (tools/check_lumbar.py).
Coordinates: Z-Anatomy world, metres (+x patient left, +y posterior, +z up)."""
import numpy as np
from scipy import ndimage
import glbio

MM = 0.001


def load(path):
    """{node name: (V, F)} with V in Z-Anatomy coordinates (glTF y-up converted back to z-up)."""
    out = {}
    for name, prims in glbio.read(path).items():
        V, F, o = [], [], 0
        for v, f, _ in prims:
            V.append(np.c_[v[:, 0], -v[:, 2], v[:, 1]]); F.append(f + o); o += len(v)
        out[name] = (np.vstack(V), np.vstack(F))
    return out


def unit(v):
    return v / np.linalg.norm(v)


def pca(P):
    c = P.mean(0)
    w, U = np.linalg.eigh(np.cov((P - c).T))
    return c, U[:, ::-1], np.sqrt(np.maximum(w[::-1], 0))   # axes largest -> smallest


def frame(n, c):
    """Right-handed frame from a cranio-caudal axis n: l (patient left), a (posterior), n (up)."""
    n = unit(n if n[2] > 0 else -n)
    a = unit(np.array([0, 1.0, 0]) - n[1] * n)
    return dict(o=np.asarray(c, float), l=np.cross(a, n), a=a, n=n)


def to_local(Fr, P):
    d = np.asarray(P) - Fr['o']
    return np.stack([d @ Fr['l'], d @ Fr['a'], d @ Fr['n']], -1)


def to_world(Fr, q):
    q = np.asarray(q, float)
    return Fr['o'] + q[..., :1] * Fr['l'] + q[..., 1:2] * Fr['a'] + q[..., 2:3] * Fr['n']


def ray(V, F, o, d):
    """Sorted distances t>0 where the ray o + t d hits the mesh (Moller-Trumbore)."""
    A, B, C = V[F[:, 0]], V[F[:, 1]], V[F[:, 2]]
    e1, e2 = B - A, C - A
    p = np.cross(d, e2)
    det = (e1 * p).sum(1)
    ok = np.abs(det) > 1e-14
    inv = np.where(ok, 1 / np.where(ok, det, 1), 0)
    s = o - A
    u = (s * p).sum(1) * inv
    q = np.cross(s, e1)
    v = (q @ d) * inv
    t = (e2 * q).sum(1) * inv
    hit = ok & (u >= 0) & (v >= 0) & (u + v <= 1) & (t > 1e-7)
    return np.sort(t[hit])


def section(meshes, o, e1, e2, half, px=0.1 * MM):
    """Rasterise the cut of closed meshes by the plane through o spanned by e1, e2 (non-zero winding fill,
    robust to small self-overlaps; needs outward normals).
    Returns bool image [i along e2, j along e1] covering +-half, and px."""
    nrm = unit(np.cross(e1, e2))
    n = int(round(2 * half / px))
    img = np.zeros((n, n), bool)
    for V, F in meshes:
        d = (V - o) @ nrm
        df = d[F]
        cross = (df.min(1) < 0) & (df.max(1) > 0)
        segs = []
        for (i, j) in ((0, 1), (1, 2), (2, 0)):
            f = F[cross]
            a, b = df[cross][:, i], df[cross][:, j]
            m = (a < 0) != (b < 0)
            t = a[m] / (a[m] - b[m])
            P = V[f[m, i]] + t[:, None] * (V[f[m, j]] - V[f[m, i]])
            segs.append((np.flatnonzero(m), P))
        # each crossing triangle gives exactly two edge points
        idx = np.concatenate([s[0] for s in segs]); P = np.vstack([s[1] for s in segs])
        order = np.argsort(idx, kind='stable'); idx, P = idx[order], P[order]
        if len(idx) < 2:
            continue
        P = P.reshape(-1, 2, 3)
        U = np.stack([(P - o) @ e1, (P - o) @ e2], -1)        # (k, 2 points, (u, v))
        Fc = F[cross][idx[::2]]
        Nf = np.cross(V[Fc[:, 1]] - V[Fc[:, 0]], V[Fc[:, 2]] - V[Fc[:, 0]])
        wgt = -np.sign(Nf @ e1)                                # +1 entering material when moving along +u
        layer = np.zeros((n, n), bool)
        ys = -half + (np.arange(n) + 0.5) * px
        y1, y2 = U[:, 0, 1], U[:, 1, 1]
        lo, hi = np.minimum(y1, y2), np.maximum(y1, y2)
        for i, y in enumerate(ys):
            m = (lo <= y) & (hi > y)
            if m.sum() < 2:
                continue
            s = U[m]
            x = s[:, 0, 0] + (y - s[:, 0, 1]) / (s[:, 1, 1] - s[:, 0, 1]) * (s[:, 1, 0] - s[:, 0, 0])
            o_ = np.argsort(x); x, w = x[o_], wgt[m][o_]
            c = np.cumsum(w)                                   # non-zero winding: inside where count > 0
            for x0, x1 in zip(x[:-1][c[:-1] > 0], x[1:][c[:-1] > 0]):
                j0, j1 = int(np.ceil((x0 + half) / px - 0.5)), int(np.floor((x1 + half) / px - 0.5))
                if j1 >= j0:
                    layer[i, max(j0, 0):min(j1, n - 1) + 1] = True
        img |= layer
    return img, px


def pix(img, half, px, u, v):
    """Pixel index (i, j) of plane coordinates (u along e1, v along e2)."""
    return int((v + half) / px), int((u + half) / px)


def holes(img):
    """Labelled background components not touching the image border."""
    lab, k = ndimage.label(~img)
    border = set(np.unique(np.r_[lab[0], lab[-1], lab[:, 0], lab[:, -1]]))
    return lab, [c for c in range(1, k + 1) if c not in border]


def chord(img, i, j, ang, px):
    """Length (m) of the bone run through pixel (i, j) along direction ang (radians, in image j/i axes)."""
    di, dj = np.sin(ang), np.cos(ang)
    L = 0
    for sgn in (1, -1):
        s = 0
        while True:
            ii, jj = int(round(i + sgn * s * di)), int(round(j + sgn * s * dj))
            if not (0 <= ii < img.shape[0] and 0 <= jj < img.shape[1]) or not img[ii, jj]:
                break
            s += 1
        L += s
    return (L - 1) * px


def samples(V, F, spacing=0.3 * MM, seed=0):
    """Surface points and their face normals, about one per spacing^2."""
    A, B, C = V[F[:, 0]], V[F[:, 1]], V[F[:, 2]]
    N = np.cross(B - A, C - A); ar = np.linalg.norm(N, axis=1) / 2
    k = max(1000, int(ar.sum() / spacing ** 2))
    rng = np.random.default_rng(seed)
    f = rng.choice(len(F), k, p=ar / ar.sum())
    r1, r2 = rng.random(k), rng.random(k)
    flip = r1 + r2 > 1; r1[flip], r2[flip] = 1 - r1[flip], 1 - r2[flip]
    P = A[f] + r1[:, None] * (B - A)[f] + r2[:, None] * (C - A)[f]
    return P, N[f] / np.maximum(np.linalg.norm(N[f], axis=1), 1e-20)[:, None]
