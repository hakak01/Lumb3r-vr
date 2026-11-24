"""Phase C2 step 2: facet (zygapophysial) joints L3-4, L4-5, L5-S1, left and right.
Joint frame from the facing parts of the upper inferior articular process (IAP) and the lower superior articular process
(SAP): mid-surface = quadratic fit through the midpoints of facing bone points; n = joint normal (IAP -> SAP). On a polar
grid over the overlap, rays from the mid-surface give the two bony articular surfaces. Cartilage on both facets fills the
measured bone gap and leaves a joint space JS (approx); it thins towards the margin. Fibrous capsule CAP_T thick (approx)
over the posterior, superior and inferior margins, bulging into superior and inferior recesses; the anteromedial margin
is left open (there the ligamentum flavum is the capsule). Units mm (Z-Anatomy world)."""
import numpy as np
from scipy.spatial import cKDTree
import lgeom, gapgeom as G
import c2_geom as CG

JS = 0.4                  # joint space (approx 0.3-0.5 mm)
CAP_T = 1.0               # capsule thickness (approx)
BULGE, RECESS = 1.2, 3.0  # capsule bulge beyond the margin; extra at the superior/inferior recesses (mm, approx)
GAP_MAX = 4.0             # a grid point belongs to the joint if the bone gap is <= this
NA, NR, RSTEP, RMAX = 28, 6, 0.5, 14.0
LEVELS = (('L3-4', 'L3', 'L4'), ('L4-5', 'L4', 'L5'), ('L5-S1', 'L5', 'S1'))


def joint_frame(I, S):
    pi, _ = lgeom.samples(*I, spacing=0.3); ps, _ = lgeom.samples(*S, spacing=0.3)
    d, j = cKDTree(ps).query(pi)
    m = d < 3.5
    M = 0.5 * (pi[m] + ps[j[m]])
    c, U, _ = lgeom.pca(M)
    n = U[:, 2] if U[:, 2] @ (ps[j[m]] - pi[m]).mean(0) > 0 else -U[:, 2]
    p = U[:, 0]; q = np.cross(n, p)
    L = (M - c) @ np.c_[p, q]; h = (M - c) @ n
    A = np.c_[np.ones(len(L)), L, L ** 2, L[:, :1] * L[:, 1:]]
    coef = np.linalg.lstsq(A, h, rcond=None)[0]
    mid = lambda u, v: c + np.outer(u, p) + np.outer(v, q) + np.outer(
        coef[0] + coef[1] * u + coef[2] * v + coef[3] * u * u + coef[4] * v * v + coef[5] * u * v, n)
    return dict(c=c, n=n, p=p, q=q, mid=mid)


def gaps_at(J, I, S, u, v):
    O = J['mid'](u, v)
    hi = CG.heights(*I, O, -J['n']); hs = CG.heights(*S, O, J['n'])
    return O, hi, hs


def domain(J, I, S):
    """Joint radius per angle: contiguous run of valid points from the centre (both surfaces hit, gap <= GAP_MAX)."""
    ph = np.linspace(0, 2 * np.pi, NA, endpoint=False); r = np.arange(1, int(RMAX / RSTEP) + 1) * RSTEP
    U = np.outer(np.cos(ph), r).ravel(); V = np.outer(np.sin(ph), r).ravel()
    _, hi, hs = gaps_at(J, I, S, U, V)
    ok = (np.isfinite(hi) & np.isfinite(hs) & (hi + hs <= GAP_MAX) & (hi < 3) & (hs < 3)).reshape(NA, -1)
    first_bad = np.where(ok.all(1), len(r), np.argmin(ok, 1))
    R = np.maximum(first_bad, 2) * RSTEP
    R = np.minimum(R, CG.smooth_polar(R, 1.0))
    return ph, R


def build_joint(D, lev, up, lo, side, log):
    I = D['%s inferior articular process (%s)' % (up, side)]; S = D['%s superior articular process (%s)' % (lo, side)]
    J = joint_frame(I, S)
    ph, R = domain(J, I, S)
    rho = np.arange(1, NR + 1) / NR
    U = rho[:, None] * R[None] * np.cos(ph)[None]; W = rho[:, None] * R[None] * np.sin(ph)[None]
    O, hi, hs = gaps_at(J, I, S, np.r_[0, U.ravel()], np.r_[0, W.ravel()])
    for h in (hi, hs):                                          # rare misses: nearest hit
        bad = ~np.isfinite(h)
        if bad.any():
            P = np.c_[np.r_[0, U.ravel()], np.r_[0, W.ravel()]]
            _, k = cKDTree(P[~bad]).query(P[bad]); h[bad] = h[~bad][k]
    gap = hi + hs
    taper = np.r_[1.0, np.repeat(0.35 + 0.65 * np.clip((1 - rho) / 0.3, 0, 1) ** 0.5, NA)]
    n = J['n']; parts = {}
    for key, h, sg in (('IAP', hi, -1), ('SAP', hs, 1)):
        t = np.maximum((gap - JS) / 2, 0.15) * taper              # cartilage thickness
        bone = O + sg * (h + 0.1)[:, None] * n                    # 0.1 mm into the bone (no seam)
        face = O + sg * (h - t)[:, None] * n
        parts[key] = CG.polar_slab(bone[1:].reshape(NR, NA, 3), face[1:].reshape(NR, NA, 3), bone[0], face[0])
        parts[key + '_t'] = t
    # capsule over the margin, except the anteromedial arc (flavum)
    sg = 1 if side == 'left' else -1
    am = G.unit(np.array([-sg * 1.0, -1.0, 0.0]))               # anterior + medial
    E = np.outer(np.cos(ph), J['p']) + np.outer(np.sin(ph), J['q'])
    amw = G.unit(am - (am @ n) * n)
    keep = E @ amw < 0.45
    start = int(np.argmax(~keep & np.roll(keep, -1))) + 1             # first kept angle after the open arc
    order = [(start + i) % NA for i in range(NA) if keep[(start + i) % NA]]
    zp = G.unit(np.array([0, 0, 1.0]) - n[2] * n)
    k_out = np.arange(1, NR * NA + 1).reshape(NR, NA)[-1]          # outer ring indices into O/hi/hs
    tau = np.linspace(0, 1, 9)
    Out, In = [], []
    for j in order:
        e = E[j]; o = O[k_out[j]]
        a = o - (hi[k_out[j]] + 0.8) * n; b = o + (hs[k_out[j]] + 0.8) * n
        bul = BULGE + RECESS * abs(e @ zp) ** 3
        base = a[None] + np.outer(tau, b - a)
        C = base + np.outer(np.sin(np.pi * tau) * bul + 0.3, e)
        T = np.gradient(C, axis=0); Nn = G.unit(np.cross(T, np.cross(e, n)))
        Nn *= np.sign((Nn @ e).sum())
        Out.append(C); In.append(C - CAP_T * Nn)
    Out, In = np.array(Out), np.array(In)
    taper_c = np.minimum(1, np.minimum(np.arange(len(order)), np.arange(len(order))[::-1]) / 2 + 0.34)
    In = Out + (In - Out) * taper_c[:, None, None]
    parts['capsule'] = CG.grid_slab(Out, In)
    # facet angle from the sagittal plane (axial cut through the joint centre)
    hz = G.unit(np.array([n[0], n[1], 0.0]))
    line = np.array([-hz[1], hz[0], 0.0])
    ang = float(np.degrees(np.arccos(abs(line[1]))))
    area = 0.5 * np.trapezoid(np.r_[R, R[:1]] ** 2, np.r_[ph, 2 * np.pi])
    st = dict(gap_med=round(float(np.median(gap)), 2), gap_min=round(float(gap.min()), 2),
              cart_IAP=round(float(np.median(parts['IAP_t'])), 2), cart_SAP=round(float(np.median(parts['SAP_t'])), 2),
              area=round(float(area), 0), angle=round(ang, 1), open_arc=int((~keep).sum() * 360 / NA))
    log('  facet %s %-5s: bone gap median %.2f (min %.2f) mm, cartilage IAP/SAP %.2f/%.2f mm, joint space %.1f, '
        'area %.0f mm2, angle %.1f deg, capsule open anteromedially over %d deg' % (
            lev, side, st['gap_med'], st['gap_min'], st['cart_IAP'], st['cart_SAP'], JS, st['area'], st['angle'], st['open_arc']))
    return dict(parts=parts, stats=st, J=J, ph=ph, R=R)


def build(D, log=print):
    out = []
    for lev, up, lo in LEVELS:
        for side in ('left', 'right'):
            j = build_joint(D, lev, up, lo, side, log)
            j.update(level=lev, side=side, up=up, lo=lo)
            out.append(j)
    return out
