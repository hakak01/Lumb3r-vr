"""Phase C1 steps 1-2: dural sac (top of the region to the upper third of S2), arachnoid 0.2 mm inside it, internal
filum terminale (conus tip -> sac tip, dorsal midline) and dural filum (sac tip -> back of the coccyx).
Built in the canal slices of c1_canal.py: in each slice the sac = the canal wall (bone, disc, PLL, new flavum) minus
margins (thin anterior epidural space, posterior fat-pad space for C2, lateral recess for the root sleeves), smoothed.
Units mm (Z-Anatomy world)."""
import numpy as np
from scipy import ndimage
import gapgeom as G

M_ANT, M_POST, M_LAT, M_LAT_HIGH = 1.0, 3.0, 2.5, 2.5   # margins (mm): anterior, posterior midline, lateral (below / above L2-3)
HALF_W = 8.5                                         # max sac half-width below L2-3 (mm, approx)
Z_HIGH = 1066.0                                      # above mid L2-3 the smaller lateral margin
NR = 72                                              # points per ring


def flavum_polar(K, flav, NT):
    """Polar radius of the new flavum's front surface per slice (inf where none)."""
    S = len(K['s']); out = np.full((S, NT), np.inf)
    for fl in flav:
        for i, k in enumerate(fl['rows']):
            d = fl['front'][i] - K['C'][k]
            u, v = d @ K['L'][k], d @ K['A'][k]
            th = np.degrees(np.arctan2(v, u)) % 360; r = np.hypot(u, v)
            o = np.argsort(th); th, r = th[o], r[o]
            b = np.arange(int(np.ceil(th[0])), int(np.floor(th[-1])) + 1)
            out[k, b % NT] = np.minimum(out[k, b % NT], np.interp(b, th, r))
    gap = np.isinf(out) & np.isfinite(np.roll(out, 1, 1)) & np.isfinite(np.roll(out, -1, 1))   # midline seam
    out[gap] = np.minimum(np.roll(out, 1, 1), np.roll(out, -1, 1))[gap]
    return out


def sacral_foramina(K):
    """Arclength index of the S1, S2 (and S3) foramen openings in the sacral canal (lateral rays escape)."""
    R = K['R']; z = K['C'][:, 2]
    esc = (R[:, 0] > 20) & (R[:, 180] > 20) & (z < 950)
    lab, n = ndimage.label(esc)
    return [float(np.mean(np.flatnonzero(lab == i))) for i in range(1, n + 1)]


def sac_radius(K, flav, log):
    s, R, C = K['s'], K['R'].astype(float), K['C']
    NT = R.shape[1]; th = np.radians(np.arange(NT))
    fo = sacral_foramina(K)
    k_tip = int(round(fo[0] + (fo[1] - fo[0]) / 6))                 # middle of the upper third of S2
    Rw = np.minimum(R, flavum_polar(K, flav, NT))
    Rw[Rw >= 25] = np.nan                                            # open rays (gaps above L3, foramina): bridge along s
    x = np.arange(len(s))
    for j in range(NT):
        ok = ~np.isnan(Rw[:, j])
        Rw[:, j] = np.interp(x, x[ok], Rw[ok, j]) if ok.any() else 12.0
    c, sn = np.cos(th), np.sin(th)
    lat = np.where(C[:, 2:3] > Z_HIGH, M_LAT_HIGH, M_LAT)
    m = c ** 2 * lat + np.where(sn > 0, sn ** 2 * 0.8 + sn ** 8 * (M_POST - 0.8), sn ** 2 * M_ANT)   # fat pad: midline
    r1 = Rw - m
    wl = np.clip((np.abs(c) - 0.75) / 0.2, 0, 1)                      # lateral rays: no bulge into foramina
    r1 = wl * ndimage.minimum_filter1d(r1, 21, axis=0, mode='nearest') + (1 - wl) * r1
    r = G.smooth1d(G.smooth1d(r1, 4.0, 0), 5.0, 1, wrap=True)
    r = np.minimum(r, np.where(C[:, 2:3] > Z_HIGH, 99, HALF_W) / np.maximum(np.abs(c), 1e-3))   # transverse cap
    r = G.smooth1d(r, 3.0, 1, wrap=True)
    r = np.minimum(r, Rw - 0.6)
    r = G.smooth1d(r, 1.0, 1, wrap=True)
    log('sac: sacral foramen openings at s %s (z %s); tip at s %d z %.1f' % (
        [round(f, 1) for f in fo], [round(float(C[int(f), 2]), 1) for f in fo], k_tip, C[k_tip, 2]))
    return r, k_tip, fo


def rings(K, r, k_tip, inset=0.0, taper=14):
    """3D rings (k, NR, 3) from slice 0 to the tip; ellipsoidal rounding over the last `taper` mm."""
    NT = r.shape[1]; idx = np.linspace(0, NT, NR, endpoint=False)
    out, cen = [], []
    for k in range(0, k_tip + 1):
        rr = np.interp(idx, np.arange(NT + 1), np.r_[r[k], r[k, :1]]) - inset
        a = np.radians(idx)
        P = K['C'][k] + (rr * np.cos(a))[:, None] * K['L'][k] + (rr * np.sin(a))[:, None] * K['A'][k]
        out.append(P); cen.append(P.mean(0))
    out, cen = np.array(out), np.array(cen)
    cen = G.smooth1d(cen, 2.0)
    k0 = k_tip - taper
    for k in range(k0, k_tip + 1):
        t = (k - k0) / taper
        out[k] = cen[k] + (out[k] - cen[k]) * np.sqrt(max(1 - t * t, 0.0))
    return out, cen


def tube_mesh(Rg):
    """Closed tube from rings (n, NR, 3): sides + flat top cap + a tip vertex at the last ring's centre."""
    n, m = Rg.shape[:2]
    V = np.vstack([Rg.reshape(-1, 3), Rg[0].mean(0)[None], Rg[-1].mean(0)[None]])
    F = []
    for i in range(n - 1):
        for j in range(m):
            a, b = i * m + j, i * m + (j + 1) % m
            F += [[a, b + m, b], [a, a + m, b + m]]
    t0, t1 = n * m, n * m + 1
    for j in range(m):
        F += [[t0, j, (j + 1) % m], [t1, (n - 1) * m + (j + 1) % m, (n - 1) * m + j]]
    return G.orient(V, np.array(F))


def area(ring):
    c = ring.mean(0); d = ring - c
    return 0.5 * np.linalg.norm(np.cross(d, np.roll(d, -1, 0)).sum(0))


def build(K, flav, D, log=print):
    r, k_tip, fo = sac_radius(K, flav, log)
    dura, cen = rings(K, r, k_tip)
    arach, _ = rings(K, r, k_tip, inset=0.2)
    # internal filum: conus tip -> dorsal midline -> sac tip (inside the arachnoid)
    W = D['White matter of spinal cord'][0]; conus = W[W[:, 2].argmin()]
    kc = int(np.argmin(np.abs(K['C'][:, 2] - conus[2])))
    path = [conus]
    for k in range(kc + 6, k_tip - 3, 3):
        path.append(K['C'][k] + K['A'][k] * (0.55 * r[k, 90]))
    path.append(cen[k_tip - 1])
    fil_int = G.catmull(np.array(path), 6)
    # dural filum: sac tip -> along the canal -> back of the coccyx (first segment, dorsal midline)
    Co = D['Coccyx'][0]; top = Co[Co[:, 2] > Co[:, 2].max() - 6]
    back = top[np.argmax(top[:, 1] - 2 * np.abs(top[:, 0]))] + np.array([0, 0.6, 0])
    ks = list(range(k_tip, len(K['s']), 4))
    path2 = [dura[-1].mean(0)] + [K['C'][k] + K['A'][k] * 1.0 for k in ks[1:]] + [back]
    fil_ext = G.catmull(np.array(path2), 6)
    disc_z = {'L2-3': 1066, 'L3-4': 1031, 'L4-5': 997, 'L5-S1': 962}
    areas = {}
    for d, z in disc_z.items():
        k = int(np.argmin(np.abs(K['C'][:, 2] - z)))
        rg = dura[k]; u = (rg - K['C'][k]) @ K['L'][k]; v = (rg - K['C'][k]) @ K['A'][k]
        areas[d] = dict(area=round(area(rg), 1), width=round(u.max() - u.min(), 1), ap=round(v.max() - v.min(), 1))
    log('sac at mid-disc: %s' % areas)
    return dict(dura=tube_mesh(dura), arach=tube_mesh(arach), fil_int=G.tube(fil_int, 0.4, 8),
                fil_ext=G.tube(fil_ext, 0.5, 8), r=r, k_tip=k_tip, fo=fo, cen=cen, rings=dura, areas=areas,
                tip_z=float(dura[-1].mean(0)[2]), coccyx_point=back)
