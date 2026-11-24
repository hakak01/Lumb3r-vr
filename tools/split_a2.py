"""Phase A2 (SPEC step 4): split bones, ligaments, roots/ganglia and discs into named parts.
Called from tools/build_assets.py after smoothing. Works on the build's item dicts."""
import os, json, re
import bpy, bmesh
import numpy as np
import bparts, bsplit, meshfix
from lgeom import MM, pca, frame, samples

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DISCS = ['L2-L3', 'L3-L4', 'L4-L5', 'L5-S1']


def arrays(me):
    me.calc_loop_triangles()
    v = np.array([x.co for x in me.vertices])
    f = np.array([x.vertices for x in me.loop_triangles])
    return v, f


def disc_frames(by):
    F = {}
    for d in DISCS:
        P, _ = samples(*arrays(by['Intervertebral disc ' + d]['obj'].data), 0.5 * MM)
        c, U, _ = pca(P)
        F[d] = frame(U[:, 2], c)
    return F


def new_item(it, name, side, me, part, level, context=False):
    o = bpy.data.objects.new(name, me)
    assert o.name == name, (o.name, name)
    it['obj'].users_collection[0].objects.link(o)
    me.polygons.foreach_set('use_smooth', [True] * len(me.polygons))
    return dict(it, obj=o, name=name, side=side, part=part, level=level, src=it['src'], context=context, remove=False)


def check_parts(parts, v0, log):
    vs = 0
    for name, side, me in parts:
        bm = bmesh.new(); bm.from_mesh(me)
        st = meshfix.stats(bm)
        bm.free()
        islands = len(me.polygons) and bsplit.islands(me)
        v = bsplit.volume(me); vs += v
        log('   %-42s %6.2f cm3  tris %6d  open/non-manifold %s  pieces %d' % (name, v * 1e6, len(me.polygons), st[:2], islands))
    log('   sum of parts %.3f cm3 vs bone %.3f cm3 (%.3f %%)' % (vs * 1e6, v0 * 1e6, 100 * (vs - v0) / v0))


def split_bones(items, log):
    by = {it['name']: it for it in items}
    DF = disc_frames(by)
    LM = {}
    spec = {'L3': ('L2-L3', 'L3-L4', 'Vertebra L2', 'Vertebra L4'), 'L4': ('L3-L4', 'L4-L5', 'Vertebra L3', 'Vertebra L5'),
            'L5': ('L4-L5', 'L5-S1', 'Vertebra L4', 'Sacrum')}
    out = []
    for v, (d1, d2, ab, be) in spec.items():
        it = by['Vertebra ' + v]
        Fr = frame(DF[d1]['n'] + DF[d2]['n'], (DF[d1]['o'] + DF[d2]['o']) / 2)
        V, F = arrays(it['obj'].data)
        L = bparts.vertebra(V, F, Fr, arrays(by[ab]['obj'].data), arrays(by[be]['obj'].data))
        LM[v] = dict(frame={k: list(map(float, x)) for k, x in Fr.items()}, landmarks=_js(L))
        log('split %s' % v)
        parts = bsplit.split(it['obj'].data, Fr, bparts.vertebra_regions(L, v), log)
        parts = bsplit.merge_fragments(parts, Fr, log)
        check_parts(parts, bsplit.volume(it['obj'].data), log)
        for name, side, me in parts:
            out.append(new_item(it, name, side, me, name[len(v) + 1:].replace(' (%s)' % side, ''), v))
        it['remove'] = True
    it = by['Sacrum']
    V, F = arrays(it['obj'].data)
    L = bparts.sacrum(V, F, DF['L5-S1'], arrays(by['Intervertebral disc L5-S1']['obj'].data), arrays(by['Vertebra L5']['obj'].data))
    Fr = L['frame']
    LM['S1'] = dict(frame={k: list(map(float, x)) for k, x in Fr.items()}, landmarks=_js({k: x for k, x in L.items() if k != 'frame'}))
    log('split S1')
    parts = bsplit.merge_fragments(bsplit.split(it['obj'].data, Fr, bparts.sacrum_regions(L), log), Fr, log)
    check_parts(parts, bsplit.volume(it['obj'].data), log)
    for name, side, me in parts:
        lev = 'S2-5' if name == 'Sacrum (rest)' else 'S1'
        out.append(new_item(it, name, side, me, 'rest of sacrum' if lev == 'S2-5' else name[3:].replace(' (%s)' % side, ''), lev))
    it['remove'] = True
    json.dump(dict(LM, discs={k: {a: list(map(float, x)) for a, x in f.items()} for k, f in DF.items()}),
              open(os.path.join(ROOT, 'data/raw/a2_landmarks.json'), 'w'), indent=1)
    return [it for it in items if not it.get('remove')] + out


def _js(x):
    if isinstance(x, dict):
        return {k: _js(v) for k, v in x.items()}
    if isinstance(x, (list, tuple, np.ndarray)):
        return [_js(v) for v in x]
    return None if x is None else float(x)


# ---------------- soft tissue (SPEC 4b-4d) ----------------
LIG = {'Anterior longitudinal ligament': 'body', 'Posterior longitudinal ligament': 'body', 'Ligamenta flava': 'lamina',
       'Interspinous ligaments': 'spinous process', 'Supraspinous ligament': 'spinous process',
       'Intertransverse ligaments (left)': 'transverse process', 'Intertransverse ligaments (right)': 'transverse process'}
SEG = [('L1-3', True), ('L3-4', False), ('L4-5', False), ('L5-S1', False), ('S1-5', True)]   # (level, context)


def centroid(me):
    v, f = arrays(me)
    return v[f].mean(1).mean(0)


def halves(me, co, no):
    """(below, above) closed copies of me split by the plane (no points 'above')."""
    lo, hi = me.copy(), me.copy()
    n1 = meshfix.crop_plane(lo, co, no)
    n2 = meshfix.crop_plane(hi, co, -np.asarray(no))
    return (lo if n1 else None), (hi if n2 else None)


def split_soft(items, log):
    by = {it['name']: it for it in items}
    A2 = json.load(open(os.path.join(ROOT, 'data/raw/a2_landmarks.json')))
    DF = {k: {a: np.array(x) for a, x in f.items()} for k, f in A2['discs'].items()}
    VN = {v: np.array(A2[v]['frame']['n']) for v in ('L3', 'L4', 'L5')}
    VN['S1'] = DF['L5-S1']['n']
    out = []

    def cen(v, part):                                    # centre of a bone part (both sides averaged)
        ms = [it['obj'].data for it in items if it.get('level') == v and it.get('part', '').startswith(part)]
        return np.mean([centroid(m) for m in ms], 0)
    # 4b ligaments: cut at the middle of the bony element of L3, L4, L5, S1
    for lig, el in LIG.items():
        it = by.get(lig)
        if not it:
            continue
        side = it['side']
        rest = it['obj'].data
        pieces = []
        for v in ('L3', 'L4', 'L5', 'S1'):
            e = {'body': 'body', 'lamina': 'lamina', 'spinous process': 'lamina' if v == 'S1' else 'spinous process',
                 'transverse process': 'ala' if v == 'S1' else 'transverse process'}[el]
            co = cen(v, e)
            if lig == 'Ligamenta flava':                   # LF k/k+1 inserts on the upper margin of lamina k+1
                lm = A2[v]['landmarks']                      # (insertion zone: 4 mm below its upper edge)
                top = (lm['ring_n'][1] if v == 'S1' else lm['n_lam'][1]) - 0.004
                co = co + (top - (co - np.array(A2[v]['frame']['o'])) @ VN[v]) * VN[v]
            lo, hi = halves(rest, co, VN[v])
            pieces.append(hi)
            rest = lo
            if rest is None:
                break
        pieces.append(rest)
        base = lig.replace(' (left)', '').replace(' (right)', '').replace('Ligamenta flava', 'Ligamentum flavum')
        base = base.replace('ligaments', 'ligament')
        for (lev, ctx), me in zip(SEG, pieces):
            if me is None or len(me.polygons) == 0:
                continue
            nm = '%s %s' % (base, lev)
            if lig == 'Ligamenta flava':                  # also left / right
                F = DF.get({'L1-3': 'L2-L3', 'L3-4': 'L3-L4', 'L4-5': 'L4-L5', 'L5-S1': 'L5-S1', 'S1-5': 'L5-S1'}[lev])
                r, l = halves(me, F['o'], F['l'])
                for sd, m in (('right', r), ('left', l)):
                    if m is not None:
                        out.append(new_item(it, '%s (%s)' % (nm, sd), sd, m, 'ligamentum flavum', lev, ctx))
            else:
                out.append(new_item(it, nm + (' (%s)' % side if side != 'mid' else ''), side, me,
                                    base.lower(), lev, ctx))
        log('ligament split %-36s -> %d pieces' % (lig, sum(p is not None for p in pieces)))
        it['remove'] = True
    # 4d discs: annulus = disc minus nucleus
    for d in ('L1-L2', 'L2-L3', 'L3-L4', 'L4-L5', 'L5-S1'):
        it, nu = by.get('Intervertebral disc ' + d), by.get('Nucleus pulposus ' + d)
        if not it or not nu:
            continue
        me = bsplit.boolean(it['obj'].data, nu['obj'].data, 'DIFFERENCE')
        v0, v1, vn = bsplit.vol0(it['obj'].data), bsplit.vol0(me), bsplit.vol0(nu['obj'].data)
        log('annulus %s: disc %.2f - nucleus %.2f = %.2f cm3 (check %.3f)' % (d, v0 * 1e6, vn * 1e6, v1 * 1e6, (v0 - vn - v1) * 1e6))
        out.append(new_item(it, 'Annulus fibrosus ' + d, 'mid', me, 'annulus fibrosus', it['level'], it['layer'] == 'context_bone'))
        nu['part'] = 'nucleus pulposus'
        it['remove'] = True
    out += split_roots(items, by, log)
    return [it for it in items if not it.get('remove')] + out


def vertebra_z(by, DF):
    """Approximate body-centre heights (m) of T12-L5 for level assignment."""
    d = {k: DF[k]['o'][2] for k in DF}
    d['L1-L2'] = centroid(by['Intervertebral disc L1-L2']['obj'].data)[2]
    z = {'L2': (d['L1-L2'] + d['L2-L3']) / 2, 'L3': (d['L2-L3'] + d['L3-L4']) / 2,
         'L4': (d['L3-L4'] + d['L4-L5']) / 2, 'L5': (d['L4-L5'] + d['L5-S1']) / 2}
    sp = d['L1-L2'] - d['L2-L3']
    z['L1'] = d['L1-L2'] + sp / 2
    z['T12'] = z['L1'] + sp
    return z


def disc_list(by, DF):
    """Top-down [(upper vertebra, disc frame)], T12-L1 extrapolated from L1-L2 and L2-L3."""
    P, _ = samples(*arrays(by['Intervertebral disc L1-L2']['obj'].data), 0.5 * MM)
    c, U, _ = pca(P)
    f12 = frame(U[:, 2], c)
    t12 = dict(f12, o=f12['o'] + (f12['o'] - DF['L2-L3']['o']))
    return [('T12', t12), ('L1', f12), ('L2', DF['L2-L3']), ('L3', DF['L3-L4']), ('L4', DF['L4-L5']), ('L5', DF['L5-S1'])]


def level_at(DL, p):
    """Root k leaves through the foramen just above disc k/k+1: the first disc (going down) that p lies above."""
    for v, F in DL:
        if (p - F['o']) @ F['n'] > 0:
            return v
    return None                                              # below L5-S1: sacral


def foramen_point(v):
    """Where a root passes the foramen (|x| 16-20 mm from the midline); else its most lateral point."""
    m = (np.abs(v[:, 0]) > 0.016) & (np.abs(v[:, 0]) < 0.020)
    return v[m].mean(0) if m.any() else v[np.argmax(np.abs(v[:, 0]))]


def split_roots(items, by, log):
    A2 = json.load(open(os.path.join(ROOT, 'data/raw/a2_landmarks.json')))
    DF = {k: {a: np.array(x) for a, x in f.items()} for k, f in A2['discs'].items()}
    DL = disc_list(by, DF)
    out = []
    kinds = {'Anterior root of spinal nerve': 'ventral root', 'Posterior root of spinal nerve': 'dorsal root',
             'Spinal ganglion': 'spinal ganglion'}
    for src, part in kinds.items():
        for side in ('left', 'right'):
            it = by.get('%s (%s)' % (src, side))
            if not it:
                continue
            groups = {}
            for m in bsplit.separate(it['obj'].data):
                v = np.array([x.co for x in m.vertices])
                lev = level_at(DL, v.mean(0) if part == 'spinal ganglion' else foramen_point(v)) or 'S1'
                if lev in groups:
                    bsplit.join(groups[lev], m)
                else:
                    groups[lev] = m
            for lev, m in groups.items():
                out.append(new_item(it, '%s %s (%s)' % (lev, part, side), side, m, part, lev, True))
            log('%s (%s): levels %s' % (src, side, sorted(groups)))
            it['remove'] = True
    it = by.get('Cauda equina')
    if it:
        pcs = [m for m in bsplit.separate(it['obj'].data) if len(m.polygons) >= 10]
        info = []
        for m in pcs:
            v = np.array([x.co for x in m.vertices])
            info.append(dict(m=m, v=v, top=v[np.argmax(v[:, 2])], bot=v[np.argmin(v[:, 2])],
                             side='right' if v[:, 0].mean() < 0 else 'left'))
        trunk = [x for x in info if np.ptp(x['v'][:, 2]) > 0.06 and np.ptp(x['v'][:, 0]) < 0.008]
        br = sorted([x for x in info if x not in trunk], key=lambda x: -x['top'][2])
        sacral = {'right': 0, 'left': 0}
        for x in br:                                       # continuation curve: starts where another branch ends
            par = [y for y in br if y is not x and 'lev' in y and y['side'] == x['side']
                   and np.linalg.norm(y['bot'] - x['top']) < 1.5 * MM]
            if par:
                x['lev'] = par[0]['lev']
                continue
            lev = level_at(DL, foramen_point(x['v']))
            if lev is None:
                sacral[x['side']] += 1
                lev = 'S%d' % sacral[x['side']]
            x['lev'] = lev
        groups = {}
        for x in br:
            k = (x['lev'], x['side'])
            if k in groups:
                bsplit.join(groups[k], x['m'])
            else:
                groups[k] = x['m']
        for (lev, side), m in sorted(groups.items()):
            out.append(new_item(it, '%s root (%s)' % (lev, side), side, m, 'root (cauda equina branch)', lev,
                                lev not in ('L3', 'L4', 'L5', 'S1', 'S2')))
        tm = trunk[0]['m']
        for x in trunk[1:]:
            bsplit.join(tm, x['m'])
        out.append(new_item(it, 'Cauda equina (central bundle)', 'mid', tm, 'cauda equina', ''))
        log('cauda equina: trunk pieces %d, roots %s' % (len(trunk), sorted(groups)))
        it['remove'] = True
    return out
