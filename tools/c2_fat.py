"""Phase C2 step 3: epidural fat (Reina 2019) and foraminal fat.
- Posterior fat pad per level (L3-4, L4-5, L5-S1): fills the posterior midline space between the dural sac and the
  canal wall (flavum / lamina) from the upper margin of the lower lamina to halfway under the upper lamina; truncated
  pyramid: wide at the lower lamina (+-W_BOT deg), narrow at the top (+-W_TOP deg), thinning to its sides. Separate per
  level (not continuous between levels or round the sac).
- Prelaminar fibrous band in front of the upper half of each lamina (L3, L4, L5, S1): thin midline band, dura -> lamina.
- Anterior fat: very little; not built (the anterior space holds the venous plexus).
- Foraminal fat L3-L5: a hollow sleeve round the root sleeve / DRG / spinal nerve from the medial pedicle line to past
  the lateral pedicle line, filling the free foramen up to FAT_R mm from the nerve, stopping 0.3 mm from bone, disc and
  ligament (clearance field of c1_space). S1/S2 DRGs lie in the sacral canal: no foraminal fat built there.
Units mm (Z-Anatomy world)."""
import numpy as np
import gapgeom as G
import c1_dura, c2_geom as CG

W_BOT, W_TOP, BAND_W = 34.0, 16.0, 7.0        # angular half-widths (deg, approx)
FAT_R, NSEG = 3.5, 14                           # foraminal fat: max thickness beyond the nerve (mm, approx); ring points


def kz(K, z):
    return int(np.argmin(np.abs(K['C'][:, 2] - z)))


def lamina_z(D, v):
    names = ['S1 lamina (left)', 'S1 lamina (right)'] if v == 'S1' else ['%s lamina (%s)' % (v, s) for s in ('left', 'right')]
    P = np.vstack([D[n][0] for n in names]); P = P[np.abs(P[:, 0]) < 9]
    return float(P[:, 2].min()), float(P[:, 2].max())


def wall(K, flav):
    R = K['R'].astype(float)
    return np.minimum(R, c1_dura.flavum_polar(K, flav, R.shape[1]))


def posterior_sheet(K, r_sac, Rw, k0, k1, half_w, shape):
    """Grid (slices k0..k1, angles round 90 deg) between the sac (+0.15) and the wall (-0.15)."""
    ks = np.arange(k0, k1 + 1); nt = 13
    Top, Bot = [], []
    for i, k in enumerate(ks):
        f = i / max(len(ks) - 1, 1)
        w = half_w(f); th = 90 + np.linspace(-w, w, nt)
        ti = np.round(th).astype(int) % 360
        r_in = np.interp(th, np.arange(360), r_sac[k]) + 0.15
        r_out = np.minimum(Rw[k, ti] - 0.35, r_in + 8.0)
        t = np.maximum(r_out - r_in, 0.25) * shape(np.linspace(-1, 1, nt), f)
        t = np.maximum(t, 0.12)
        a = np.radians(th)
        d = np.cos(a)[:, None] * K['L'][k] + np.sin(a)[:, None] * K['A'][k]
        Bot.append(K['C'][k] + r_in[:, None] * d); Top.append(K['C'][k] + (r_in + t)[:, None] * d)
    Top, Bot = np.array(Top), np.array(Bot)
    depth = float(np.max(np.linalg.norm(Top - Bot, axis=2)))
    return CG.grid_slab(Top, Bot), depth


def pads(K, D, sac, flav, log):
    Rw = wall(K, flav); r = sac['r']; out = []
    for lev, up, lo in (('L3-4', 'L3', 'L4'), ('L4-5', 'L4', 'L5'), ('L5-S1', 'L5', 'S1')):
        zl0, zl1 = lamina_z(D, lo); zu0, zu1 = lamina_z(D, up)
        k0, k1 = kz(K, 0.5 * (zu0 + zu1)), kz(K, zl1)
        hw = lambda f: W_TOP + (W_BOT - W_TOP) * f
        shp = lambda x, f: (1 - 0.8 * x ** 2) * np.clip(0.55 + 3 * f, 0, 1) * np.clip(0.5 + 3 * (1 - f), 0, 1)
        mesh, depth = posterior_sheet(K, r, Rw, k0, k1, hw, shp)
        L = float(np.linalg.norm(K['C'][k1] - K['C'][k0]))
        log('  posterior epidural fat pad %s: z %.0f -> %.0f (%.0f mm long), max depth %.1f mm' % (
            lev, K['C'][k0, 2], K['C'][k1, 2], L, depth))
        out.append(dict(name='Posterior epidural fat pad %s' % lev, level=lev, mesh=mesh, length=round(L, 1),
                        depth=round(depth, 1)))
    for v in ('L3', 'L4', 'L5', 'S1'):
        z0, z1 = lamina_z(D, v)
        k0, k1 = kz(K, z1), kz(K, 0.5 * (z0 + z1))
        lab = {'L3': 2, 'L4': 3, 'L5': 4, 'S1': 5}[v]
        ok = [k for k in range(k0, k1 + 1) if K['Lb'][k, 90] == lab and K['R'][k, 90] < 25]
        if len(ok) < 3 or ok[-1] >= sac['k_tip']:
            continue
        k0, k1 = ok[0], ok[-1]
        mesh, depth = posterior_sheet(K, r, Rw, k0, k1, lambda f: BAND_W, lambda x, f: np.ones_like(x))
        log('  prelaminar fibrous band %s: z %.0f -> %.0f, dura -> lamina %.1f mm' % (v, K['C'][k0, 2], K['C'][k1, 2], depth))
        out.append(dict(name='Prelaminar fibrous band %s' % v, level=v, mesh=mesh, depth=round(depth, 1)))
    return out


def ring_frame(T):
    ref = np.array([0, 0, 1.0]) if abs(T[0, 2]) < 0.9 else np.array([1.0, 0, 0])
    N = G.unit(np.cross(T[0], ref)); out = []
    for t in T:
        N = G.unit(N - (N @ t) * t); out.append((N, np.cross(t, N)))
    return out


def foraminal(F, roots, log):
    out = []
    for r in roots:
        P = r['paths'].get('P')
        if not P:
            continue
        sg = 1 if r['side'] == 'left' else -1
        pth = r['paths']; dors, vent = pth['dors'], pth['vent']
        x0, x1 = P['xm'] - sg * 1.0, P['xl'] + sg * 3.0
        sel = (sg * dors[:, 0] > sg * x0) & (sg * dors[:, 0] < sg * x1)
        idx = np.flatnonzero(sel)
        if len(idx) < 4:
            continue
        nv = np.vstack([dors[idx], pth['nerve'][:4]]) if sg * pth['nerve'][0, 0] < sg * x1 else dors[idx]
        C = G.smooth1d(CG_resample(nv, 1.0), 1.0)
        T = G.unit(np.gradient(C, axis=0)); fr = ring_frame(T)
        Gc, u, a, l = r['drg'], pth['u'], r['w'] / 2, r['l']
        from scipy.spatial import cKDTree
        tv = cKDTree(vent); td = cKDTree(dors)
        ang = np.linspace(0, 2 * np.pi, NSEG, endpoint=False)
        Out, In = [], []
        for c, (N, B) in zip(C, fr):
            s = (c - Gc) @ u
            core = a * np.sqrt(max(1 - (s / (l / 2)) ** 2, 0)) if abs(s) < l / 2 else 0.0
            core = max(core, r['rd'], td.query(c)[0] + r['rd'], tv.query(c)[0] + r['rv']) + 0.15
            D = np.outer(np.cos(ang), N) + np.outer(np.sin(ang), B)
            ro = np.full(NSEG, core + FAT_R); ri = np.full(NSEG, core)
            t = np.arange(0.0, core + FAT_R + 0.01, 0.25)
            for j in range(NSEG):
                hit = np.flatnonzero(F(c + np.outer(t, D[j])) < 0.55)
                if len(hit):
                    ro[j] = t[hit[0]]; ri[j] = min(core, ro[j] - 0.05)
            ro = np.minimum(G.smooth1d(ro, 1.0, wrap=True), ro)
            In.append(c + ri[:, None] * D); Out.append(c + np.maximum(ro, ri + 0.05)[:, None] * D)
        Out, In = np.array(Out), np.array(In)
        V, Fc = annulus_tube(Out, In)
        th = float(np.median(np.linalg.norm(Out - In, axis=2)))
        log('  foraminal fat %s %-5s: %.0f mm along the root, median thickness %.1f mm' % (
            r['level'], r['side'], len(C), th))
        out.append(dict(name='Foraminal fat %s (%s)' % (r['fo_name'], r['side']), level=r['fo_name'], side=r['side'],
                        mesh=(V, Fc), thick=round(th, 1)))
    return out


def CG_resample(P, step):
    d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]
    t = np.linspace(0, d[-1], max(int(d[-1] / step), 2))
    return np.stack([np.interp(t, d, P[:, k]) for k in range(3)], 1)


def annulus_tube(Out, In):
    """Closed hollow tube between ring grids Out and In (n, m, 3): outer, inner and two end annuli."""
    n, m = Out.shape[:2]; k = n * m
    V = np.vstack([Out.reshape(-1, 3), In.reshape(-1, 3)])
    io = np.arange(k).reshape(n, m); ii = io + k
    F = CG.quads(io, True) + [f[::-1] for f in CG.quads(ii, True)]
    F += [f[::-1] for f in CG.quads(np.stack([io[0], ii[0]]), True)] + CG.quads(np.stack([io[-1], ii[-1]]), True)
    return G.orient(V, np.array(F))


def build(K, D, sac, flav, F, roots, log=print):
    return pads(K, D, sac, flav, log), foraminal(F, roots, log)
