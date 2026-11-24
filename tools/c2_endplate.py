"""Phase C2 step 1: cartilaginous endplates (CEP), 6 parts (upper and lower face of the L3-4, L4-5, L5-S1 discs).
Outer face = the bony vertebral endplate (ray from the disc mid-plane along the disc axis); inner face = outer face moved
into the disc by the thickness t. t = 0.45 mm in the centre rising to 1.0 mm at the anterior/posterior rim and 0.78 mm
at the lateral rim (range 0.3-1 mm, mean 0.74 mm: DeLucca 2016, Berg-Johansen 2018). The CEP covers the disc inside the
ring apophysis: its edge is RING mm inside the disc outline at the face (approx). In this model the disc already touches
the bone (median gap 0.3 mm), so the CEP overlaps the outer ~0.4 mm of the annulus/nucleus. Units mm."""
import numpy as np
import lgeom, gapgeom as G
import c2_geom as CG

RING = 3.5                       # ring apophysis width (approx)
T0, T_AP, T_LAT = 0.45, 1.0, 0.78
NR, NA = 8, 40
DISCS = (('L3-4', 'L3-L4', 'L3', 'L4'), ('L4-5', 'L4-L5', 'L4', 'L5'), ('L5-S1', 'L5-S1', 'L5', 'S1'))


def disc_frame(D, dn):
    A = D['Annulus fibrosus ' + dn][0]
    c, U, _ = lgeom.pca(A)
    return lgeom.frame(U[:, 2], c), A


def outline(Fr, A, s):
    """Disc outline radius per angle near the face s (+1 upper, -1 lower)."""
    q = lgeom.to_local(Fr, A); h = q[:, 2] * s
    q = q[h > 0]
    ph = np.arctan2(q[:, 1], q[:, 0]); r = np.hypot(q[:, 0], q[:, 1])
    b = ((ph + np.pi) / (2 * np.pi) * NA).astype(int) % NA
    R = np.zeros(NA)
    np.maximum.at(R, b, r)
    R = np.where(R > 0, R, np.median(R[R > 0]))
    return np.roll(CG.smooth_polar(R, 1.5), 0), np.linspace(-np.pi, np.pi, NA, endpoint=False) + np.pi / NA


def thickness(rho, ph):
    return T0 + rho ** 2 * ((T_LAT - T0) + (T_AP - T_LAT) * np.abs(np.sin(ph)))


def plate(D, Fr, A, bone, s):
    R, ph = outline(Fr, A, s)
    Rin = np.maximum(R - RING, 3.0)
    rho = (np.arange(1, NR + 1) / NR)
    U = rho[:, None] * Rin[None] * np.cos(ph)[None]; W = rho[:, None] * Rin[None] * np.sin(ph)[None]
    Q = np.stack([np.r_[0.0, U.ravel()], np.r_[0.0, W.ravel()], np.zeros(1 + U.size)], 1)
    O = lgeom.to_world(Fr, Q)
    V, F = D[bone]
    h = CG.heights(V, F, O, Fr['n'] * s)
    ok = np.isfinite(h)
    if (~ok).any():                                           # fill misses from the nearest hits
        from scipy.spatial import cKDTree
        _, i = cKDTree(Q[ok, :2]).query(Q[~ok, :2]); h[~ok] = h[ok][i]
    hc, H = h[0], h[1:].reshape(NR, NA)
    H = G.smooth1d(CG.smooth_polar(H.T, 1.0).T, 0.7, 0)       # light smoothing of the bony surface
    t = thickness(rho[:, None], ph[None])
    to3 = lambda u, w, z: lgeom.to_world(Fr, np.stack([u, w, z], -1))
    Out = to3(U, W, H * s); In = to3(U, W, (H - t) * s)
    mesh = CG.polar_slab(Out, In, lgeom.to_world(Fr, np.array([0, 0, hc * s])),
                         lgeom.to_world(Fr, np.array([0, 0, (hc - T0) * s])))
    a = rho[:, None] * Rin[None] ** 2                         # area weight of each grid point (polar)
    face = 0.5 * np.trapezoid(np.r_[R, R[:1]] ** 2, np.r_[ph, ph[0] + 2 * np.pi])
    cov = 0.5 * np.trapezoid(np.r_[Rin, Rin[:1]] ** 2, np.r_[ph, ph[0] + 2 * np.pi])
    st = dict(mean=round(float((t * a).sum() / a.sum()), 2), min=round(float(t.min()), 2),
              max=round(float(t.max()), 2), area=round(float(cov), 0), cover=round(float(cov / face), 2),
              ap=round(float(Rin[NA // 4] + Rin[3 * NA // 4]), 1), width=round(float(Rin[0] + Rin[NA // 2]), 1))
    return mesh, st, dict(Fr=Fr, R=R, Rin=Rin, ph=ph, H=H, s=s)


def build(D, log=print):
    out = []
    for lev, dn, up, lo in DISCS:
        Fr, A = disc_frame(D, dn)
        A = lgeom.samples(*D['Annulus fibrosus ' + dn], spacing=0.5)[0]
        for bone, s, which in ((up + ' body', 1, 'inferior'), (lo + ' body', -1, 'superior')):
            mesh, st, geo = plate(D, Fr, A, bone, s)
            name = '%s %s cartilaginous endplate' % (bone.split()[0], which)
            log('  %s (%s): thickness mean %.2f (%.2f-%.2f) mm, covers %.0f mm2 = %.0f %% of the disc face, AP %.1f x W %.1f'
                % (name, lev, st['mean'], st['min'], st['max'], st['area'], 100 * st['cover'], st['ap'], st['width']))
            out.append(dict(name=name, level=lev, mesh=mesh, stats=st, geo=geo, bone=bone.split()[0], which=which))
    return out
