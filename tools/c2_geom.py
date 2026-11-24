"""Phase C2: shared mesh helpers (closed slabs from two surface grids, frames, ray height fields). Units mm."""
import numpy as np
import gapgeom as G
import lgeom


def quads(idx, wrap=False):
    """Triangles of a (n, m) index grid; wrap joins the last column to the first."""
    n, m = idx.shape; F = []
    for i in range(n - 1):
        for j in range(m if wrap else m - 1):
            a, b = idx[i, j], idx[i, (j + 1) % m]; c, d = idx[i + 1, j], idx[i + 1, (j + 1) % m]
            F += [[a, b, d], [a, d, c]]
    return F


def polar_slab(Out, In, cOut, cIn):
    """Closed disc-shaped solid. Out/In: (nr, na, 3) rings from the centre outwards; cOut/cIn: centre points."""
    nr, na = Out.shape[:2]; k = nr * na
    V = np.vstack([Out.reshape(-1, 3), In.reshape(-1, 3), cOut[None], cIn[None]])
    io = np.arange(k).reshape(nr, na); ii = io + k
    F = quads(io, True) + [f[::-1] for f in quads(ii, True)]
    for j in range(na):
        F += [[2 * k, io[0, (j + 1) % na], io[0, j]], [2 * k + 1, ii[0, j], ii[0, (j + 1) % na]]]
    F += quads(np.stack([io[-1], ii[-1]]), True)
    return G.orient(V, np.array(F))


def grid_slab(Top, Bot):
    """Closed box-like solid between two (n, m, 3) surface grids with the same layout."""
    n, m = Top.shape[:2]; k = n * m
    V = np.vstack([Top.reshape(-1, 3), Bot.reshape(-1, 3)])
    it = np.arange(k).reshape(n, m); ib = it + k
    F = quads(it) + [f[::-1] for f in quads(ib)]
    for e in (lambda a: a[0], lambda a: a[:, -1], lambda a: a[-1, ::-1], lambda a: a[::-1, 0]):
        F += [f[::-1] for f in quads(np.stack([e(it), e(ib)]))]
    return G.orient(V, np.array(F))


def heights(V, F, O, d, pick='first'):
    """Distance along d from each origin in O to the mesh (first or last hit); nan where missed."""
    tri = V[F]; lo, hi = tri.min(1), tri.max(1)
    out = np.full(len(O), np.nan)
    for i, o in enumerate(O):
        # cheap prefilter: triangles whose box meets the ray's line (d close to an axis is not assumed)
        p = o + np.outer([0, 60.0], d); bl, bh = p.min(0) - 0.5, p.max(0) + 0.5
        m = ((hi >= bl) & (lo <= bh)).all(1)
        t = lgeom.ray(V, F[m], o, d) if m.any() else []
        if len(t):
            out[i] = t[0] if pick == 'first' else t[-1]
    return out


def smooth_polar(r, s=2.0):
    return G.smooth1d(r, s, 0, wrap=True)


def frame_pca(P, up=None):
    """Centre and axes (largest, middle, smallest variance); smallest flipped to point along `up`."""
    c, U, sd = lgeom.pca(P)
    if up is not None and U[:, 2] @ up < 0:
        U = U.copy(); U[:, 2] *= -1
    return c, U, sd
