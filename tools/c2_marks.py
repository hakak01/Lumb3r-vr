"""Phase C2 step 7: landmark patches (thin translucent sheets, approx; layer "landmark").
- Kambin's triangle L3-4, L4-5, L5-S1 L/R: hypotenuse = exiting root (L3/L4/L5), base = superior endplate of the lower
  vertebra, medial side = traversing root (L4/L5/S1) sleeve / dural sac. Lies on the posterolateral disc surface.
- Lateral recess (L4, L5, S1 L/R): axial patch at the upper border of the lower pedicle (S1: 9 mm below mid-disc),
  bounded by body/disc, pedicle, SAP and the dural sac (the space of the traversing root).
- Foraminal entry / middle / exit zones (L3-4, L4-5, L5-S1 L/R): the free foramen in sagittal planes at the medial
  border, centre and lateral border of the pedicle above (Lee 1988-style zones).
- Axilla and shoulder of each traversing root (L4, L5, S1 L/R): small discs below-medial (axilla) and above-lateral
  (shoulder) of the sleeve where it leaves the sac.
Units mm (Z-Anatomy world)."""
import numpy as np
import gapgeom as G
import c1_roots, c2_fat, c2_geom as CG

T = 0.3                                                       # patch thickness (mm)
FO = (('L3-4', 'L3', 'L4'), ('L4-5', 'L4', 'L5'), ('L5-S1', 'L5', 'S1'))


def root(roots, lv, side):
    return next(r for r in roots if r['level'] == lv and r['side'] == side)


def onto_disc(F, P, sg):
    """Move points anteriorly until 0.4 mm from bone/disc (the posterolateral disc surface), then back 0.4 mm."""
    out = []
    for p in P:
        d = G.unit(np.array([-0.35 * sg, -1.0, 0.0]))
        t = np.arange(0, 12, 0.2); cl = F(p + np.outer(t, d)); h = np.flatnonzero(cl < 0.4)
        out.append(p + d * (t[h[0]] if len(h) else 0.0))
    return np.array(out)


def kambin(F, roots, lev, ex, tr, side, z_base, sac_x):
    sg = 1 if side == 'left' else -1
    E = root(roots, ex, side)['paths']; Tp = root(roots, tr, side)['paths']
    ep = np.vstack([E['dors'][E['nI']:], E['nerve']])
    # medial border: lateral edge of the traversing sleeve / root at the base level
    tpath = np.vstack([Tp['sleeve'], Tp['dors'][Tp['nI']:]]); k = int(np.argmin(np.abs(tpath[:, 2] - z_base)))
    xb = tpath[k, 0] + sg * (Tp['srad'].max() if k < len(Tp['sleeve']) else 1.0)
    xb = sg * max(sg * xb, sac_x)                                # never inside the dural sac
    B = np.array([xb, tpath[k, 1], z_base])
    # C: on the exiting root above B; A: where the exiting root reaches the base level (or its lowest lateral point)
    lat = ep[sg * ep[:, 0] > sg * xb]
    C = lat[np.argmin(np.abs(lat[:, 0] - xb))] if len(lat) else ep[np.argmin(np.abs(ep[:, 0] - xb))]
    C = C - np.array([0, 0, 1.0])                              # lower edge of the root
    C[0] = xb; C[2] = min(C[2], E['P']['zc'] - 7.0)             # apex no higher than the lower pedicle border (approx)
    below = lat[lat[:, 2] <= z_base + 1.0]
    A = below[0] if len(below) else lat[np.argmin(lat[:, 2])] * [1, 1, 0] + [0, 0, z_base]
    A = A + np.array([0, 0, 0.0])
    if sg * (A[0] - B[0]) < 3:
        A = B + np.array([sg * 6.0, 0, 0])
    n = 8; s = np.linspace(0, 1, n)[:, None, None]; t = np.linspace(0, 1, n)[None, :, None]
    Pg = C + s * ((1 - t) * A + t * B - C)
    Q = onto_disc(F, Pg.reshape(-1, 3), sg).reshape(n, n, 3)
    Q = G.smooth1d(G.smooth1d(Q, 0.8, 0), 0.8, 1)
    nrm = G.unit(np.array([0.35 * sg, 1.0, 0]))
    area = 0.5 * np.linalg.norm(np.cross(A - C, B - C))
    return CG.grid_slab(Q + nrm * T, Q), dict(A=A, B=B, C=C, area=round(float(area), 1),
                                              base=round(float(abs(A[0] - B[0])), 1), height=round(float(C[2] - z_base), 1))


def polar_patch(F, c, e1, e2, rmax=12.0, stop=None, na=24):
    """Star-shaped free region round seed c in the plane (e1, e2), as a thin slab."""
    ph = np.linspace(0, 2 * np.pi, na, endpoint=False); R = np.zeros(na)
    t = np.arange(0.2, rmax, 0.2)
    for j, a in enumerate(ph):
        d = np.cos(a) * e1 + np.sin(a) * e2; P = c + np.outer(t, d)
        bad = F(P) < 0.25
        if stop is not None:
            bad |= stop(P)
        h = np.flatnonzero(bad); R[j] = t[h[0]] - 0.2 if len(h) else t[-1]
    R = np.maximum(np.minimum(R, CG.smooth_polar(R, 1.0)), 0.5)
    rho = np.array([0.5, 1.0])[:, None]
    ring = c + (rho * R)[..., None] * (np.cos(ph)[:, None] * e1 + np.sin(ph)[:, None] * e2)[None]
    nrm = np.cross(e1, e2)
    area = 0.5 * np.sum(R ** 2) * (2 * np.pi / na)
    return CG.polar_slab(ring + nrm * T / 2, ring - nrm * T / 2, c + nrm * T / 2, c - nrm * T / 2), round(float(area), 0)


def free_seed(F, c, r=4.0):
    g = np.mgrid[-r:r:0.5, -r:r:0.5, -r:r:0.5].reshape(3, -1).T
    P = c + g; v = F(P) - 0.05 * np.linalg.norm(g, axis=1)
    return P[int(np.argmax(v))]


def build(K, F, sac, roots, endplates, log=print):
    out = []
    ep = {(e['bone'], e['which']): e for e in endplates}
    for lev, ex, tr in FO:
        e = ep[(tr, 'superior')]; geo = e['geo']
        for side, sg in (('left', 1), ('right', -1)):
            # base level: superior endplate of the lower vertebra at its posterolateral rim
            j = int(np.argmin(np.abs(geo['ph'] - np.radians(90 - sg * 45))))
            rim = geo['Fr']['o'] + geo['Fr']['n'] * (-geo['H'][-1, j])
            kb = c2_fat.kz(K, rim[2]); sac_x = sg * K['C'][kb, 0] + sac['r'][kb, 0 if sg > 0 else 180]
            m, st = kambin(F, roots, lev, ex, tr, side, float(rim[2]), float(sac_x))
            log("  Kambin's triangle %s %-5s: base %.1f mm, height %.1f mm, area %.0f mm2" % (lev, side, st['base'], st['height'], st['area']))
            out.append(dict(name="Kambin's triangle %s (%s)" % (lev, side), level=lev, side=side, mesh=m, part='Kambin triangle', stats=st))
            # foraminal zones in sagittal planes at the pedicle borders of the vertebra above
            P = root(roots, ex, side)['paths']['P']; fc = c1_roots.foramen(lev, side)
            for zn, x in (('entry', P['xm']), ('middle', 0.5 * (P['xm'] + P['xl'])), ('exit', P['xl'])):
                c = free_seed(F, np.array([x, fc[1], fc[2]])); c[0] = x
                m2, area = polar_patch(F, c, np.array([0, 1.0, 0]), np.array([0, 0, 1.0]))
                out.append(dict(name='Foraminal %s zone %s (%s)' % (zn, lev, side), level=lev, side=side, mesh=m2,
                                part='foraminal zone', area=area))
            log('  foraminal zones %s %-5s: planes at x %.1f / %.1f / %.1f' % (lev, side, P['xm'], 0.5 * (P['xm'] + P['xl']), P['xl']))
            # lateral recess of the traversing root
            Tp = root(roots, tr, side)['paths']
            zr = e['geo']['Fr']['o'][2] - 9.0                         # ~ upper border of the lower pedicle (approx)
            k = c2_fat.kz(K, zr); path = np.vstack([Tp['sleeve'], Tp['dors'][Tp['nI']:]])
            th = 270 + sg * 60; ti = int(round(th)) % 360; a = np.radians(th)
            seed = K['C'][k] + 0.5 * (sac['r'][k, ti] + K['R'][k, ti]) * (np.cos(a) * K['L'][k] + np.sin(a) * K['A'][k])
            def in_sac(Pp, k=k):
                d = Pp - K['C'][k]; u, v = d @ K['L'][k], d @ K['A'][k]
                th = np.degrees(np.arctan2(v, u)) % 360
                return np.hypot(u, v) < np.interp(th, np.arange(360), sac['r'][k])
            m3, area = polar_patch(F, seed, K['L'][k], K['A'][k], rmax=10.0, stop=in_sac)
            log('  lateral recess %s %-5s: axial patch at z %.0f, area %.0f mm2' % (tr, side, seed[2], area))
            out.append(dict(name='Lateral recess %s (%s)' % (tr, side), level=tr, side=side, mesh=m3, part='lateral recess', area=area))
            # axilla and shoulder of the traversing root
            Ep = Tp['E']; sl = Tp['sleeve']; d = G.unit(sl[min(8, len(sl) - 1)] - sl[3])
            kE = c2_fat.kz(K, Ep[2]); up = K['N'][kE]; rr = float(Tp['srad'][:6].mean())
            for nm, pos in (('axilla', Ep - up * (rr + 1.6) + d * 1.0), ('shoulder', Ep + up * (rr + 1.4) + d * 2.0)):
                nrm = G.unit(K['A'][kE] + 0.5 * sg * K['L'][kE])
                e1 = G.unit(np.cross(nrm, up)); e2 = np.cross(nrm, e1)
                ph = np.linspace(0, 2 * np.pi, 12, endpoint=False)
                ring = pos + 1.3 * (np.cos(ph)[:, None] * e1 + np.sin(ph)[:, None] * e2)
                out.append(dict(name='%s %s of the traversing root (%s)' % (tr, nm, side), level=lev, side=side,
                                part='root ' + nm, mesh=CG.polar_slab(ring[None] + nrm * T / 2, ring[None] - nrm * T / 2,
                                                                     pos + nrm * T / 2, pos - nrm * T / 2)))
    return out
