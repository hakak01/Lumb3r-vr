"""Phase C1 step 3 (inside the sac): cauda equina arrangement of the L3-S2 ventral and dorsal roots, slice by slice.
Rule: the root that leaves next lies anterolateral; lower roots lie progressively more posteromedial (a crescent);
each ventral root anteromedial to its dorsal root. Roots start on the conus surface (ventral anterolateral, dorsal
posterolateral) and are kept apart, inside the arachnoid and off the cord by a small 2-D relaxation per slice.
Units mm, slice coordinates (u = patient left, v = posterior) round the canal centreline."""
import numpy as np
import gapgeom as G


def cord_slices(K, D):
    """Cord centre (u, v) and radius per slice (None below the conus)."""
    W = D['White matter of spinal cord'][0]
    out = []
    for k in range(len(K['s'])):
        d = (W - K['C'][k]) @ K['N'][k]
        P = W[np.abs(d) < 0.6]
        if len(P) < 6:
            out.append(None); continue
        u, v = (P - K['C'][k]) @ K['L'][k], (P - K['C'][k]) @ K['A'][k]
        out.append((u.mean(), v.mean(), 0.5 * max(u.max() - u.min(), v.max() - v.min()) + 0.2))
    return out


def arrange(K, D, sac_r, roots, log=print):
    """roots: list of dict(name, side, k0, k1, rv, rd). Adds 'uv_v', 'uv_d' arrays (k0..k1, 2) for each root."""
    cords = cord_slices(K, D)
    NT = sac_r.shape[1]
    for side in ('left', 'right'):
        sg = 1.0 if side == 'left' else -1.0
        R = [r for r in roots if r['side'] == side]
        for r in R:
            r['uv_v'] = np.zeros((r['k1'] - r['k0'] + 1, 2)); r['uv_d'] = np.zeros_like(r['uv_v'])
        kmin, kmax = min(r['k0'] for r in R), max(r['k1'] for r in R)
        prev = {}
        worst = 0.0
        for k in range(kmin, kmax + 1):
            act = sorted([r for r in R if r['k0'] <= k <= r['k1']], key=lambda r: r['k1'])
            if not act:
                continue
            def sac(th):                                              # usable radius inside the arachnoid
                return np.interp(np.degrees(th) % 360, np.arange(NT + 1), np.r_[sac_r[k], sac_r[k, :1]]) - 0.45
            T, rad, pair = [], [], []
            for i, r in enumerate(act):
                phi = np.radians(-35 + 28 * i); rho = 0.80 - 0.12 * i
                th = phi if side == 'left' else np.pi - phi
                c = rho * sac(th) * np.array([np.cos(th), np.sin(th)])
                n = G.unit(np.array([-0.45 * sg, -1.0]))                 # anteromedial
                tv, td = c + n * (r['rv'] + 0.15), c - n * (r['rd'] + 0.15)
                t0 = (k - r['k0']) / 8.0
                cd = cords[k] if cords[k] is not None else cords[r['k0']]
                if t0 < 1 and cd is not None:                              # leaving the conus surface
                    cu, cv, cr = cd
                    sv = np.array([cu, cv]) + (cr + r['rv'] + 0.1) * np.array([0.8 * sg, -0.6])
                    sd = np.array([cu, cv]) + (cr + r['rd'] + 0.1) * np.array([0.8 * sg, 0.6])
                    tv, td = (1 - t0) * sv + t0 * tv, (1 - t0) * sd + t0 * td
                T += [tv, td]; rad += [r['rv'], r['rd']]; pair.append((2 * i, 2 * i + 1, r['rv'] + r['rd'] + 0.3))
            T, rad = np.array(T), np.array(rad)
            X = np.array([prev.get((id(a), j), T[2 * i + j]) for i, a in enumerate(act) for j in (0, 1)])
            X = 0.6 * X + 0.4 * T
            cd = cords[k]
            for _ in range(80):
                X += 0.08 * (T - X)
                d = X[:, None] - X[None]; dist = np.linalg.norm(d, axis=2) + np.eye(len(X))
                need = rad[:, None] + rad[None] + 0.12 - dist; np.fill_diagonal(need, 0)
                m = need > 0
                if m.any():
                    X += 0.5 * (np.where(m[..., None], d / dist[..., None] * need[..., None], 0)).sum(1)
                for a, b, L0 in pair:                                     # keep each pair together
                    dv = X[b] - X[a]; L1 = np.linalg.norm(dv)
                    if L1 > L0:
                        X[a] += 0.5 * (L1 - L0) * dv / L1; X[b] -= 0.5 * (L1 - L0) * dv / L1
                if cd is not None:                                        # off the cord
                    dc = X - cd[:2]; dn = np.linalg.norm(dc, axis=1)
                    m = dn < cd[2] + rad + 0.1
                    X[m] += dc[m] / dn[m, None] * (cd[2] + rad[m] + 0.1 - dn[m])[:, None]
                th = np.arctan2(X[:, 1], X[:, 0]); rr = np.linalg.norm(X, axis=1); lim = sac(th) - rad
                m = rr > lim
                X[m] *= (lim[m] / rr[m])[:, None]
            d = np.linalg.norm(X[:, None] - X[None], axis=2) + 99 * np.eye(len(X))
            worst = max(worst, float((rad[:, None] + rad[None] - d).max()))
            for i, r in enumerate(act):
                r['uv_v'][k - r['k0']] = X[2 * i]; r['uv_d'][k - r['k0']] = X[2 * i + 1]
                prev[(id(r), 0)], prev[(id(r), 1)] = X[2 * i], X[2 * i + 1]
        for r in R:
            r['uv_v'] = G.smooth1d(r['uv_v'], 2.0); r['uv_d'] = G.smooth1d(r['uv_d'], 2.0)
        log('cauda equina %s: largest root overlap in the sac %.2f mm (before smoothing)' % (side, max(worst, 0)))
    return roots


def to3d(K, k0, uv):
    k = np.arange(k0, k0 + len(uv))
    return K['C'][k] + uv[:, :1] * K['L'][k] + uv[:, 1:] * K['A'][k]
