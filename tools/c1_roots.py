"""Phase C1 steps 3-4: L3-S2 ventral and dorsal roots, dural root sleeves, dorsal root ganglia and spinal nerves.
Shapes copied from the Z-Anatomy L2 templates (ventral root, dorsal root, spinal ganglion) and scaled per level to the
DRG sizes of docs/SPEC.md ANATOMY CHECKS. Course: sac -> own sleeve at the disc above its foramen -> lateral recess
medial to its own pedicle -> under the pedicle (DRG: medial foraminal zone at L3/L4, lateral at L5; S1/S2 in the
sacral canal at their foramen) -> spinal nerve -> existing Z-Anatomy plexus nerve. Clearance >= 0.5 mm from bone,
disc and ligament is enforced on a voxel field and measured exactly. Units mm (Z-Anatomy world)."""
import json, os
import numpy as np
import gapgeom as G
import c1_cauda as CA

TV, TD, TW = 0.47, 0.535, 2.73        # template radii (ventral, dorsal) and ganglion width (mm), Z-Anatomy L2
TL = 5.09                             # template ganglion length (mm)
# DRG width/length (mm): L3-L5 from ANATOMY CHECKS; S1 "largest", S2 smaller: approx values (no number in SPEC)
LEV = [dict(n='L3', ped='L3', fo='L3-4', exit_z=1066, start_z=1098, zone=1 / 6, w=5.1, l=7.0),
       dict(n='L4', ped='L4', fo='L4-5', exit_z=1031, start_z=1088, zone=1 / 6, w=5.95, l=8.5),
       dict(n='L5', ped='L5', fo='L5-S1', exit_z=997, start_z=1078, zone=5 / 6, w=6.35, l=11.5),
       dict(n='S1', ped=None, sac=0, exit_z=966, start_z=1068, w=7.0, l=12.0),
       dict(n='S2', ped=None, sac=1, exit_z=954, start_z=1060, w=5.0, l=8.0)]
PLEXUS_SKIP = ('root', 'ganglion', 'Spinal', 'White matter', 'Cauda')
_MAN = json.load(open(os.path.join(os.path.dirname(__file__), '..', 'assets/manifest.json')))
NERVES = {e['name'] for e in _MAN if e['layer'] == 'nerve'}


def resample(P, step=0.7):
    d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]
    t = np.linspace(0, d[-1], max(int(d[-1] / step), 2))
    return np.stack([np.interp(t, d, P[:, k]) for k in range(3)], 1)


def kz(K, z):
    return int(np.argmin(np.abs(K['C'][:, 2] - z)))


def ring_dir(K, k, th):
    return np.cos(np.radians(th)) * K['L'][k] + np.sin(np.radians(th)) * K['A'][k]


def pedicle(K, D, lev, side):
    V = D['%s pedicle (%s)' % (lev, side)][0]; sg = 1 if side == 'left' else -1
    zc = V[:, 2].mean(); k = kz(K, zc)
    th = 0 if sg > 0 else 180
    kk = k - 8 + int(np.argmin(K['R'][k - 8:k + 9, th]))                 # narrowest point = medial pedicle wall
    xm = (K['C'][kk] + K['R'][kk, th] * ring_dir(K, kk, th))[0]
    band = V[np.abs(V[:, 2] - zc) < 2]
    xl = np.percentile(band[:, 0], 98) if sg > 0 else np.percentile(band[:, 0], 2)
    low = lambda x: V[np.abs(V[:, 0] - x) < 1.5, 2].min()
    return dict(xm=float(xm), xl=float(xl), low=low, zc=zc)


def foramen(lev_fo, side):
    m = json.load(open(os.path.join(os.path.dirname(__file__), '..', 'assets/model.json')))['foramen']
    p = m['%s %s' % (lev_fo, side)]
    return np.array([p[0], -p[2], p[1]]) * 1000


def axis_clear(F, P, u, a, l):
    """Clearance minus the ganglion's half-width at points along its axis (ends narrower)."""
    t = np.linspace(-(l / 2 - a), l / 2 - a, 5)
    Q = P[:, None] + t[None, :, None] * u
    half = a * np.sqrt(np.clip(1 - (t / (l / 2)) ** 2, 0.3, 1))
    return (F(Q.reshape(-1, 3)).reshape(len(P), -1) - half).min(1)


def place_drg(F, K, L, side, sac_fo, log):
    sg = 1 if side == 'left' else -1; a, l = L['w'] / 2, L['l']
    if L['ped']:
        u = G.unit(np.array([sg, -0.35, -0.45]))
        P = L['P']; xt = P['xm'] + L['zone'] * (P['xl'] - P['xm']); Fc = foramen(L['fo'], side); zl = P['low'](xt)
        y, z = np.meshgrid(np.arange(Fc[1] - 9, Fc[1] + 9, 0.5), np.arange(zl - 16, zl - a - 0.4, 0.5), indexing='ij')
        X = np.c_[np.full(y.size, xt), y.ravel(), z.ravel()]
        c = axis_clear(F, X, u, a, l); ok = c >= 0.9
        if ok.any():
            zz = X[ok, 2]; top = ok.copy(); top[ok] = zz >= zz.max() - 0.6
            i = np.flatnonzero(top)[np.argmax(c[top])]
        else:
            i = int(np.argmax(c))
        Gc = X[i]
        log('  DRG %s %-5s zone x %.1f (pedicle medial %.1f, lateral %.1f), %.1f mm below the pedicle, field clearance %.2f'
            % (L['n'], side, xt, P['xm'], P['xl'], zl - Gc[2], c[i]))
        return Gc, u, dict(zone='medial' if L['zone'] < 0.5 else 'lateral', x=xt, xm=P['xm'], xl=P['xl'],
                           below=float(zl - Gc[2]))
    k = int(round(sac_fo[L['sac']])); th = 0 if sg > 0 else 180
    rl = float(K['R'][k - 8:k + 9, th][K['R'][k - 8:k + 9, th] < 20].min())          # canal wall beside the opening
    u = G.unit(sg * 0.55 * K['L'][k] - 0.1 * K['A'][k] - 0.8 * K['N'][k])        # down the canal towards the opening
    best = None
    for dz in np.arange(2, 12.1, 0.5):                                               # lower end at the opening
        for lat in np.arange(rl + 2, 2, -0.5):                                        # as far lateral as fits
            P = K['C'][k] + sg * lat * K['L'][k] + dz * K['N'][k]
            c = axis_clear(F, P[None], u, a, l)[0]
            if c >= 0.9:
                best = (P, lat, dz, c); break
        if best:
            break
    if best is None:
        P = K['C'][k] + sg * 4 * K['L'][k]; best = (P, 4.0, 0.0, axis_clear(F, P[None], u, a, l)[0])
    log('  DRG %s %-5s sacral canal at its foramen: centre %.1f mm lateral (canal wall %.1f), %.1f mm above the opening, '
        'field clearance %.2f' % (L['n'], side, best[1], rl, best[2], best[3]))
    return best[0], u, dict(zone='sacral canal at the foramen opening', lateral=float(best[1]), wall=rl)


def plexus_join(D, L, side, T):
    sg = 1 if side == 'left' else -1
    if not L['ped']:                                                  # sacral: the old root's distal end
        V = D['%s root (%s)' % (L['n'], side)][0]
        return V[np.argmax(V[:, 0] * sg)], 'old root end'
    best = (1e9, None, '')
    for n, (V, F) in D.items():
        if n not in NERVES or any(k in n for k in PLEXUS_SKIP) or not n.endswith('(%s)' % side):
            continue
        d = np.linalg.norm(V - T, axis=1); i = int(np.argmin(d))
        if d[i] < best[0] and V[i, 0] * sg > T[0] * sg - 6:
            best = (d[i], V[i], n)
    return (best[1], best[2]) if best[0] < 14 else (T, 'none within 14 mm')


def ganglion(D, side, Gc, u, w, l):
    V, F = D['L2 spinal ganglion (%s)' % side]
    c = V.mean(0); _, U = np.linalg.eigh(np.cov((V - c).T)); U = U[:, ::-1]
    q = (V - c) @ U; q[:, 0] *= l / TL; q[:, 1:] *= w / TW
    b1 = G.unit(np.cross(u, [0, 0, 1.0])); b2 = np.cross(u, b1)
    return Gc + q[:, :1] * u + q[:, 1:2] * b1 + q[:, 2:3] * b2, F


def course(F, K, D, L, side, sac_r, sac_fo, log):
    sg = 1 if side == 'left' else -1; a = L['w'] / 2; rv, rd = L['rv'], L['rd']
    Gc, u, info = place_drg(F, K, L, side, sac_fo, log)
    kE = kz(K, L['exit_z']); thE = (335 if sg > 0 else 205)
    E = K['C'][kE + 1] + (sac_r[kE + 1, thE] + 0.2) * ring_dir(K, kE + 1, thE)
    if L['ped']:
        P = L['P']
        Pin = np.array([P['xm'] - sg * 1.0, Gc[1] + 1.5, P['low'](P['xm']) - 0.6 * a])
        Pin = F.relax(Pin[None], max(rv, rd) * 2, keep=())[0]
    else:
        Pin = None
    Gs, Ge = Gc - u * L['l'] / 2, Gc + u * L['l'] / 2
    J, jn = plexus_join(D, L, side, Ge + 8 * u)
    N0 = Ge + 1.5 * u
    if Pin is not None:
        R1 = 0.5 * (E + Pin)
        dors = G.catmull(np.array([E, R1, Pin, Gs, Gc, Ge, N0]), 8)
    else:                                                             # sacral canal: route through free space
        seg = F.route(E, Gs, rv + rd + 0.2)
        if seg is None:
            log('  %s %s: no free route from the sac to the DRG' % (L['n'], side))
        seg = resample(seg) if seg is not None else G.catmull(np.array([E, Gs]), 10)
        dors = np.vstack([seg[:-1], G.catmull(np.array([Gs, Gc, Ge, N0]), 8)])
    nd = len(dors)
    i_gs = int(np.argmin(np.linalg.norm(dors - Gs, axis=1))); i_ge = int(np.argmin(np.linalg.norm(dors - Ge, axis=1)))
    keep = list(range(i_gs, i_ge + 1)) + [nd - 1]
    dors = F.relax(dors, rd, keep=[0] + keep)
    T = G.unit(np.gradient(dors, axis=0))
    n = np.array([0, -1.0, -1.0]) - (T @ np.array([0, -1.0, -1.0]))[:, None] * T; n = G.unit(n)
    t = np.arange(nd)
    off = np.interp(t, [0, i_gs - 6, i_gs, i_ge, nd - 1], [rv + rd + 0.3, rv + rd + 0.3, a + rv + 0.3, a + rv + 0.3, 0])
    vent = F.relax(dors + n * off[:, None], rv, keep=[nd - 1])
    rn = np.sqrt(rv ** 2 + rd ** 2)
    nerve = F.route(N0, J, 0.5 * rn, clear=0.0)
    if nerve is None:
        nerve = F.route(N0, J, 0.0, clear=0.0)
    if nerve is None:
        log('  %s %s: no free route for the spinal nerve' % (L['n'], side))
    nerve = resample(nerve) if nerve is not None else G.catmull(np.array([N0, N0 + 0.5 * (J - N0) + 1.0 * u, J]), 10)
    nerve = np.vstack([N0 - 0.8 * u, nerve])
    return dict(dors=dors, vent=vent, G=Gc, u=u, i_gs=i_gs, nerve=nerve, join=jn, info=info, E=E, kE=kE)


def fix_exact(EX, path, rad, F, fixed=(), rounds=6):
    """Push tube rings that come closer than 0.5 mm to bone/disc/ligament (exact distance)."""
    nseg = 10
    for _ in range(rounds):
        V, _f = G.tube(path, rad, nseg)
        d = np.min([EX.signed(V[:len(path) * nseg], k) for k in EX.g], 0).reshape(len(path), nseg).min(1)
        bad = d < 0.55; bad[list(fixed)] = False
        if not bad.any():
            break
        g = G.unit(F.grad(path[bad]))
        path[bad] += g * (0.65 - d[bad])[:, None]
    return path


def build(K, D, sac, F, EX, log=print):
    sac_r, sac_fo = sac['r'], sac['fo']
    roots = []
    for L0 in LEV:
        for side in ('left', 'right'):
            L = dict(L0); sc = L['w'] / TW; L['rv'], L['rd'] = TV * sc, TD * sc
            if L['ped']:
                L['P'] = pedicle(K, D, L['ped'], side)
            roots.append(dict(name=L['n'], side=side, L=L, k0=kz(K, L['start_z']), k1=kz(K, L['exit_z']) - 2,
                              rv=L['rv'], rd=L['rd']))
    CA.arrange(K, D, sac_r, roots, log)
    out = []
    for r in roots:
        L, side = r['L'], r['side']
        c = course(F, K, D, L, side, sac_r, sac_fo, log)
        vin, din = CA.to3d(K, r['k0'], r['uv_v']), CA.to3d(K, r['k0'], r['uv_d'])
        tr_d = G.catmull(np.array([din[-1], c['dors'][0]]), 4)[:-1]
        tr_v = G.catmull(np.array([vin[-1], c['vent'][0]]), 4)[:-1]
        dors = np.vstack([din[:-1], tr_d, c['dors']]); vent = np.vstack([vin[:-1], tr_v, c['vent']])
        dors, vent = G.smooth1d(dors, 1.0), G.smooth1d(vent, 1.0)
        nI = len(din) - 1
        dors = fix_exact(EX, dors, L['rd'], F, fixed=range(0, nI))
        vent = fix_exact(EX, vent, L['rv'], F, fixed=range(0, nI))
        gV, gF = ganglion(D, side, c['G'], c['u'], L['w'], L['l'])
        sl_end = nI + len(tr_d) + c['i_gs'] + 2
        mid = 0.5 * (dors[nI - 3:sl_end] + vent[nI - 3:sl_end])
        srad = 0.5 * np.linalg.norm(dors[nI - 3:sl_end] - vent[nI - 3:sl_end], axis=1) + max(L['rv'], L['rd']) + 0.25
        srad[-4:] = np.maximum(srad[-4:], np.linspace(srad[-5], L['w'] / 2 * 0.8, 4))
        meshes = dict(vent=G.tube(vent, L['rv'], 10), dors=G.tube(dors, L['rd'], 10), drg=(gV, gF),
                      sleeve=G.tube(mid, srad, 14),
                      nerve=G.tube(c['nerve'], np.sqrt(L['rv'] ** 2 + L['rd'] ** 2), 12))
        clear = {}
        for k in ('vent', 'dors', 'drg'):
            V = meshes[k][0]
            if k != 'drg':
                V = V[nI * 10:]                                           # outside the sac only
            clear[k] = EX.min_clear(V)
        cn = EX.min_clear(meshes['nerve'][0])
        log('  %s %-5s narrowest gap: ventral %.2f (%s), dorsal %.2f (%s), DRG %.2f (%s); spinal nerve %.2f; joins %s'
            % (r['name'], side, *clear['vent'], *clear['dors'], *clear['drg'], cn[0], c['join']))
        seg = dors[nI:nI + len(tr_d) + c['i_gs'] + 1]
        ln = float(np.linalg.norm(np.diff(seg, axis=0), axis=1).sum()) + L['l'] / 2
        ang = float(np.degrees(np.arccos(abs(G.unit(c['G'] - c['E']) @ K['N'][c['kE']]))))
        out.append(dict(level=r['name'], side=side, meshes=meshes, sleeve_len=round(ln, 1), angle=round(ang, 1), clear=clear, nerve_clear=cn, info=c['info'],
                        join=c['join'], w=L['w'], l=L['l'], rv=L['rv'], rd=L['rd'], exit_z=float(c['E'][2]),
                        drg=c['G']))
    return out
