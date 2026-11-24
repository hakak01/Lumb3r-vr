"""Phase C1: free space round the canal and foramina. Obstacles = bone, discs, ligaments (incl. the new flavum).
Voxel clearance field (0.5 mm, Euclidean distance transform) for placing roots and ganglia, and exact clearance
checks of finished meshes (oriented surface samples, gapgeom.Solid). Units mm (Z-Anatomy world)."""
import numpy as np
from scipy import ndimage
from scipy.spatial import cKDTree
import lgeom, gapgeom as G

BOX = (np.array([-40.0, 0.0, 900.0]), np.array([40.0, 90.0, 1135.0]))
VX = 0.5


def obstacles(D, flav):
    """{group: [(V, F)]} of closed meshes the neural parts must not touch."""
    out = {'bone': [], 'disc': [], 'ligament': []}
    for n, vf in D.items():
        if n.startswith(('Vertebra L1', 'Vertebra L2', 'L3 ', 'L4 ', 'L5 ', 'S1 ', 'Sacrum', 'Coccyx', 'Hip bone')) \
                and not any(k in n for k in ('root', 'ganglion')):
            out['bone'].append(vf)
        elif n.startswith(('Annulus fibrosus', 'Nucleus pulposus')):
            out['disc'].append(vf)
        elif any(n.startswith(k) for k in ('Posterior longitudinal', 'Anterior longitudinal', 'Interspinous',
                                           'Supraspinous', 'Intertransverse', 'Iliolumbar ligament',
                                           'Interosseous sacro', 'Anterior sacro', 'Posterior sacro')):
            out['ligament'].append(vf)
    for f in flav:
        out['ligament'].append((f['V'], f['F']))
    return out


class Field:
    """Clearance (mm) from the nearest obstacle on a 0.5 mm grid; lookup by trilinear interpolation."""
    def __init__(self, obs, log=print):
        lo, hi = BOX
        n = np.ceil((hi - lo) / VX).astype(int)
        occ = np.zeros(n, bool)
        meshes = [m for g in obs.values() for m in g]
        half = max(hi[0] - lo[0], hi[1] - lo[1]) / 2
        cx, cy = (lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2
        for kz in range(n[2]):
            z = lo[2] + (kz + 0.5) * VX
            near = [(V, F) for V, F in meshes if V[:, 2].min() < z < V[:, 2].max()]
            if not near:
                continue
            img, px = lgeom.section([G.merge(near)], np.array([cx, cy, z]), np.array([1.0, 0, 0]), np.array([0, 1.0, 0]), half, VX)
            m = img.shape[0]; ox = int(round((lo[0] - (cx - half)) / VX)); oy = int(round((lo[1] - (cy - half)) / VX))
            occ[:, :, kz] = img[oy:oy + n[1], ox:ox + n[0]].T[:n[0], :n[1]]
        self.occ = occ; self.lo = lo; self.n = n
        self.d = ndimage.distance_transform_edt(~occ) * VX - VX / 2
        log('clearance field %s voxels, %.1f %% occupied' % (tuple(n), 100 * occ.mean()))

    def __call__(self, P):
        g = (np.atleast_2d(P) - self.lo) / VX - 0.5
        return ndimage.map_coordinates(self.d, g.T, order=1, mode='nearest')

    def grad(self, P, h=0.5):
        P = np.atleast_2d(P)
        return np.stack([(self(P + h * e) - self(P - h * e)) / (2 * h) for e in np.eye(3)], 1)

    def relax(self, path, rad, clear=0.5, iters=40, keep=(0, -1), smooth=1.0):
        """Move path points until clearance >= rad + clear (+0.4 voxel safety); fixed points stay."""
        path = path.copy(); rad = np.broadcast_to(np.asarray(rad, float), (len(path),))
        fixed = np.zeros(len(path), bool); fixed[list(keep)] = True
        for _ in range(iters):
            need = rad + clear + 0.4 - self(path)
            m = (need > 0) & ~fixed
            if not m.any():
                break
            g = G.unit(self.grad(path[m]))
            path[m] += g * np.minimum(need[m], 0.5)[:, None]
            if smooth:
                sm = G.smooth1d(path, smooth)
                path[~fixed] = 0.5 * path[~fixed] + 0.5 * sm[~fixed]
        return path


    def route(self, A, B, rad, clear=0.5, margin=8.0):
        """Shortest free path A -> B keeping >= rad + clear (+voxel safety); cost favours open space. None if blocked."""
        from scipy.sparse import coo_matrix
        from scipy.sparse.csgraph import dijkstra
        lo = np.maximum(np.minimum(A, B) - margin, self.lo); hi = np.minimum(np.maximum(A, B) + margin,
                                                                            self.lo + self.n * VX - VX)
        i0 = np.floor((lo - self.lo) / VX).astype(int); i1 = np.ceil((hi - self.lo) / VX).astype(int)
        sub = self.d[i0[0]:i1[0], i0[1]:i1[1], i0[2]:i1[2]]
        need = rad + clear + 0.3
        free = sub >= need
        idx = -np.ones(sub.shape, int); idx[free] = np.arange(free.sum())
        pts = np.argwhere(free)
        def node(P):
            g = np.round((P - self.lo) / VX - 0.5).astype(int) - i0
            d = np.linalg.norm(pts - g, axis=1); return int(np.argmin(d))
        a, b = node(A), node(B)
        rows, cols, w = [], [], []
        for off in [(1, 0, 0), (0, 1, 0), (0, 0, 1), (1, 1, 0), (1, -1, 0), (1, 0, 1), (1, 0, -1), (0, 1, 1), (0, 1, -1)]:
            q = pts + off
            ok = (q >= 0).all(1) & (q < sub.shape).all(1)
            j = np.full(len(pts), -1); j[ok] = idx[tuple(q[ok].T)]
            m = j >= 0
            c = np.linalg.norm(off) * (1 + 1.5 / sub[tuple(pts[m].T)])
            rows.append(np.flatnonzero(m)); cols.append(j[m]); w.append(c)
        M = coo_matrix((np.concatenate(w), (np.concatenate(rows), np.concatenate(cols))), shape=(len(pts),) * 2).tocsr()
        dist, pred = dijkstra(M, directed=False, indices=a, return_predecessors=True)
        if not np.isfinite(dist[b]):
            return None
        path = [b]
        while path[-1] != a:
            path.append(pred[path[-1]])
        P = self.lo + (pts[path[::-1]] + i0 + 0.5) * VX
        P = np.vstack([A, P[1:-1], B])
        return G.smooth1d(P, 2.0)


class Exact:
    """Signed distance to each obstacle group from dense oriented surface samples (0.25 mm; negative = inside)."""
    def __init__(self, obs, lo=BOX[0] - 5, hi=BOX[1] + 5):
        self.g = {}
        for k, ms in obs.items():
            P, N = [], []
            for V, F in ms:
                c = V[F].mean(1); keep = ((c > lo) & (c < hi)).all(1)
                if keep.any():
                    p, n = lgeom.samples(V, F[keep], spacing=0.25)
                    P.append(p); N.append(n)
            if P:
                self.g[k] = (cKDTree(np.vstack(P)), np.vstack(N))

    def signed(self, X, k):
        tree, N = self.g[k]
        d, i = tree.query(X, k=4)
        s = np.einsum('ikj,ikj->ik', X[:, None] - tree.data[i], N[i]).mean(1)
        return np.where((s < 0) & (d[:, 0] < 3.0), -d[:, 0], d[:, 0])   # inside only near the surface

    def min_clear(self, V):
        best, who = np.inf, ''
        for k in self.g:
            d = self.signed(V, k)
            if d.min() < best:
                best, who = float(d.min()), k
        return best, who
