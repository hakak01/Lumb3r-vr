"""Phase C1 step 6: ligamentum flavum L3-4, L4-5, L5-S1 (left/right) as solid ligaments, built in the canal slices
of c1_canal.py (polar columns round the canal centreline; theta 90 = posterior midline, 0 = patient left).
Per column the posterior wall (first bone hit) is bridged across the interlaminar gap; the ligament lies on the front
of the lower half of the upper lamina, crosses the gap 3.1 mm thick (normal 3.1 +- 0.8 mm, AJNR 2010;31:1813) and
inserts on the upper edge of the lower lamina. Laterally it covers the front of the facet joint to the foramen.
Units mm (Z-Anatomy world)."""
import numpy as np
import gapgeom as G

T_GAP = 3.1          # thickness across the interlaminar gap (mm)
F_TOP, F_BOT = 0.5, 2.7   # protrusion in front of the upper lamina at its mid-height and at its lower edge (mm)
EMBED = 0.4          # depth inside the bone at the attachments (mm)
RLIM = 22.0          # a wall hit farther than this from the centreline is not posterior wall
LEVELS = (('L3-4', 1, 2, 1031), ('L4-5', 2, 3, 997), ('L5-S1', 3, 4, 962))   # name, upper/lower vertebra index, mid-disc z


def _runs(col):
    """Interpolate missing values (nan) of a column linearly, constant at the ends."""
    x = np.arange(len(col)); ok = ~np.isnan(col)
    return np.interp(x, x[ok], col[ok]) if ok.sum() >= 2 else np.full(len(col), np.nan)


def level(K, name, iu, iw, zdisc, side, log):
    s, C, L, A, Rv = K['s'], K['C'], K['L'], K['A'], K['Rv']
    kd = int(np.argmin(np.abs(C[:, 2] - zdisc)))
    th = np.arange(0, 91) if side == 'left' else 180 - np.arange(0, 91)          # theta index per |angle from lateral|
    win = slice(max(kd - 40, 0), min(kd + 30, len(s)))
    ru = Rv[win, iu][:, th]; rw = Rv[win, iw][:, th]
    k0 = win.start
    hu = ru < RLIM; hw = rw < RLIM
    # upper lamina: rows of upper-vertebra hits above the disc + 15 mm; lower lamina: hits below the disc - 3 mm
    rows = np.arange(ru.shape[0]) + k0
    hu &= (rows < kd + 15)[:, None]; hw &= (rows > kd - 3)[:, None]
    med = slice(60, 85)                                                       # paramedian columns (deg from lateral)
    ubot = np.array([rows[np.flatnonzero(hu[:, j])[-1]] if hu[:, j].any() else -1 for j in range(91)])
    wtop = np.array([rows[np.flatnonzero(hw[:, j] & (rows > max(ubot[j], kd - 3)))[0]]
                     if (hw[:, j] & (rows > max(ubot[j], kd - 3))).any() else -1 for j in range(91)])
    tops = []
    for j in range(60, 85):
        h = np.flatnonzero(hu[:, j])
        if len(h):
            run = h[-1]
            while run - 1 in h:
                run -= 1
            tops.append(rows[run])
    s_a = int(round((np.median(tops) + np.median(ubot[med])) / 2))           # mid-height of the upper lamina
    s_b = int(np.median(wtop[med])) + 2                                      # 2 mm into the lower lamina's upper edge
    # joint rows: lateral theta (12 deg from lateral) wall deeper than 14 mm -> facet region begins
    deep = [k for k in range(s_a, s_b) if ru[k - k0, 12] > 14 or np.isnan(ru[k - k0, 12])]
    s_jt = deep[0] if deep else s_a + 6
    # wall w(s, theta) = nearer of the two vertebrae, gaps interpolated along s
    W = np.where(hu | hw, np.minimum(np.where(hu, ru, 99), np.where(hw, rw, 99)), np.nan)[s_a - k0:s_b - k0 + 1]
    W = np.stack([_runs(W[:, j]) for j in range(91)], 1)
    good = ~np.isnan(W).any(0)
    W = G.smooth1d(G.smooth1d(np.where(np.isnan(W), 20.0, W), 1.5, 0), 1.5, 1)
    srow = np.arange(s_a, s_b + 1)
    # lateral limit (deg from lateral): 30 above the facet joint, 4 at and below it
    lat = np.interp(srow, [s_a, s_jt - 3, s_jt + 1, s_b], [30, 30, 4, 4])
    lat = np.maximum(lat, np.min(np.flatnonzero(good)) if good.any() else 30)
    nu = 26
    front, back = [], []
    for i, k in enumerate(srow):
        u = np.linspace(89.5, lat[i], nu)                                    # medial -> lateral
        w = np.interp(u, np.arange(91), W[i])
        ub = np.interp(u, np.arange(91), ubot.astype(float)); wt = np.interp(u, np.arange(91), wtop.astype(float))
        ub = np.where(ub < 0, s_b - 6, ub); wt = np.where(wt < 0, s_b - 2, np.maximum(wt, ub))
        f = np.where(k <= ub, F_TOP + (F_BOT - F_TOP) * np.clip((k - s_a) / np.maximum(ub - s_a, 1), 0, 1),
                     F_BOT * np.clip((wt - k) / np.maximum(wt - ub, 1), 0, 1))
        T = np.where(k <= ub, np.minimum(f + EMBED + (k - s_a) * 0.25, T_GAP),
                     np.where(k <= wt, T_GAP, T_GAP - (T_GAP - 1.2) * np.clip((k - wt) / 2.0, 0, 1)))
        T = np.maximum(T, f + EMBED)
        ang = np.radians(u if side == 'left' else 180 - u)
        d = np.cos(ang)[:, None] * L[k] + np.sin(ang)[:, None] * A[k]
        front.append(C[k] + (w - f)[:, None] * d); back.append(C[k] + (w - f + T)[:, None] * d)
    Fg, Bg = np.array(front), np.array(back)                                 # (rows, nu, 3)
    Fg = G.smooth1d(G.smooth1d(Fg, 1.0, 0), 1.0, 1); Bg = G.smooth1d(G.smooth1d(Bg, 1.0, 0), 1.0, 1)
    V, F = G.slab(Fg, Bg)
    half = (s_a + s_b) // 2
    thick = np.linalg.norm(Bg - Fg, axis=2)
    log('flavum %s %-5s rows s %d-%d (z %.0f-%.0f), facet from s %d, thickness at half length %.2f mm (paramedian %.2f)'
        % (name, side, s_a, s_b, C[s_a, 2], C[s_b, 2], s_jt, np.median(thick[half - s_a]), thick[half - s_a, 8]))
    return dict(V=V, F=F, front=Fg, back=Bg, rows=srow, half=half, thick_half=float(np.median(thick[half - s_a])))


def build(K, log=print):
    out = []
    for name, iu, iw, zd in LEVELS:
        for side in ('left', 'right'):
            r = level(K, name, iu, iw, zd, side, log)
            r.update(name='Ligamentum flavum %s (%s)' % (name, side), level=name, side=side)
            out.append(r)
    return out
