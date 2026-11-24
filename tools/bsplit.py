"""Blender side of Phase A2: cut a closed mesh into parts with convex regions (exact boolean).
Neighbouring parts come from the same cutter face, so they meet with no gap and no overlap."""
import bpy, bmesh
import numpy as np
from mathutils import Vector

BIG = 0.25


def region_mesh(Fr, halfspaces, mat):
    """Convex polytope {x : n.x <= d for all (n, d)} (local l, a, n coords) -> world-space Blender mesh."""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=2 * BIG)
    for nrm, off in halfspaces:
        nn = np.asarray(nrm, float)
        co = nn * off / (nn @ nn)
        geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
        r = bmesh.ops.bisect_plane(bm, geom=geom, dist=1e-9, plane_co=Vector(co), plane_no=Vector(nn),
                                   clear_outer=True, clear_inner=False)
        cut = [e for e in r['geom_cut'] if isinstance(e, bmesh.types.BMEdge) and e.is_valid and e.is_boundary]
        if cut:
            bmesh.ops.holes_fill(bm, edges=cut, sides=0)
    M = np.c_[Fr['l'], Fr['a'], Fr['n']]
    for v in bm.verts:
        v.co = Vector(Fr['o'] + M @ np.array(v.co))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new('cutter')
    bm.to_mesh(me)
    bm.free()
    me.materials.append(mat)
    return me


def boolean(me, cutter_me, op, use_self=True):
    """New mesh = me (op) cutter, exact solver; cut faces take the cutter's material."""
    a = bpy.data.objects.new('_t', me)
    b = bpy.data.objects.new('_c', cutter_me)
    col = bpy.context.scene.collection
    col.objects.link(a)
    col.objects.link(b)
    m = a.modifiers.new('b', 'BOOLEAN')
    m.operation, m.object, m.solver = op, b, 'EXACT'
    m.use_self = use_self
    m.material_mode = 'TRANSFER'
    dg = bpy.context.evaluated_depsgraph_get()
    out = bpy.data.meshes.new_from_object(a.evaluated_get(dg), depsgraph=dg)
    bpy.data.objects.remove(a)
    bpy.data.objects.remove(b)
    return out


def clean(me):
    """Remove zero-area slivers and edges shared by >2 faces that the boolean can leave; refill the tiny holes."""
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-8)
    bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=1e-8)
    for _ in range(3):
        bad = {f for e in bm.edges if len(e.link_faces) > 2 for f in e.link_faces}
        bad |= {f for f in bm.faces if f.calc_area() < 1e-13}
        if bad:
            bmesh.ops.delete(bm, geom=list(bad), context='FACES')
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
        bnd = [e for e in bm.edges if e.is_boundary]
        if bnd:
            bmesh.ops.holes_fill(bm, edges=bnd, sides=0)
        if not bad and not bnd:
            break
    bmesh.ops.triangulate(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()


def vol0(me):
    return volume(me) if len(me.polygons) else 0.0


def cut(rem, Fr, H, mat, log, name):
    """(part, rest) = rem ∩ region, rem − region; retries with the region moved 0.02 mm if volumes do not add up."""
    convex = H if isinstance(H[0], list) else [H]          # a region may be a union of convex blocks
    tries = [(sh, us, 0) for us in (True, False) for sh in (0.0, 2e-5, -2e-5, 5e-5)] + \
            [(sh, us, 1) for us in (True, False) for sh in (0.0, 3e-5, -3e-5)]
    for k, (shift, use_self, weld) in enumerate(tries):
        if weld and tries[k - 1][2] == 0:                   # last resort: weld the leftover at 1 um, drop slivers
            bm = bmesh.new()
            bm.from_mesh(rem)
            bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
            bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=1e-6)
            bm.to_mesh(rem)
            bm.free()
            clean(rem)
        v = vol0(rem)
        c = region_mesh(Fr, [(n, d + shift) for n, d in convex[0]], mat)
        for extra in convex[1:]:
            c2 = region_mesh(Fr, [(n, d + shift) for n, d in extra], mat)
            u = boolean(c, c2, 'UNION')
            bpy.data.meshes.remove(c)
            bpy.data.meshes.remove(c2)
            c = u
        part, rest = boolean(rem, c, 'INTERSECT', use_self), boolean(rem, c, 'DIFFERENCE', use_self)
        bpy.data.meshes.remove(c)
        clean(part)
        clean(rest)
        if abs(vol0(part) + vol0(rest) - v) < 1e-4 * v:
            if k:
                log('  %s: boolean retried (moved %.2f mm, self-check %s, welded %s)' % (name, shift * 1000, use_self, bool(weld)))
            return part, rest
        bpy.data.meshes.remove(part)
        bpy.data.meshes.remove(rest)
    raise RuntimeError('boolean failed for ' + name)


def split(me, Fr, regions, log):
    """regions: [(name, side, halfspaces)], the last one takes the rest. Returns [(name, side, mesh)]."""
    bone_mat = me.materials[0]
    rem, out = me.copy(), []
    for name, side, H in regions:
        if not H:
            out.append((name, side, rem))
            continue
        part, rest = cut(rem, Fr, H, bone_mat, log, name)
        bpy.data.meshes.remove(rem)
        rem = rest
        if len(part.polygons) == 0:
            log('  EMPTY part:', name)
            continue
        out.append((name, side, part))
    return out


def volume(me):
    me.calc_loop_triangles()
    v = np.array([x.co for x in me.vertices])
    t = np.array([x.vertices for x in me.loop_triangles])
    return np.einsum('ij,ij->i', v[t[:, 0]], np.cross(v[t[:, 1]], v[t[:, 2]])).sum() / 6


def islands(me):
    """Number of edge-connected pieces."""
    bm = bmesh.new()
    bm.from_mesh(me)
    seen, k = set(), 0
    for f0 in bm.faces:
        if f0.index in seen:
            continue
        k += 1
        stack = [f0]
        seen.add(f0.index)
        while stack:
            f = stack.pop()
            for e in f.edges:
                for g in e.link_faces:
                    if g.index not in seen:
                        seen.add(g.index)
                        stack.append(g)
    bm.free()
    return k


def separate(me):
    """Split a mesh into edge-connected pieces -> list of meshes (largest volume first)."""
    bm = bmesh.new()
    bm.from_mesh(me)
    groups, seen = [], set()
    for f0 in bm.faces:
        if f0.index in seen:
            continue
        stack, g = [f0], []
        seen.add(f0.index)
        while stack:
            f = stack.pop()
            g.append(f.index)
            for e in f.edges:
                for h in e.link_faces:
                    if h.index not in seen:
                        seen.add(h.index)
                        stack.append(h)
        groups.append(set(g))
    bm.free()
    out = []
    for g in groups:
        m = me.copy()
        bm = bmesh.new()
        bm.from_mesh(m)
        bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.index not in g], context='FACES')
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
        bm.to_mesh(m)
        bm.free()
        out.append(m)
    return sorted(out, key=lambda m: -vol0(m))


def join(a, b):
    """Append mesh b's geometry to mesh a (exact; b becomes a second shell touching a)."""
    bm = bmesh.new()
    bm.from_mesh(a)
    slot = {m.name: i for i, m in enumerate(a.materials) if m}
    vs = [bm.verts.new(v.co) for v in b.vertices]
    for p in b.polygons:
        try:
            f = bm.faces.new([vs[i] for i in p.vertices])
        except ValueError:
            continue
        mb = b.materials[p.material_index] if p.material_index < len(b.materials) else None
        f.material_index = slot.get(mb.name, 0) if mb else 0
        f.smooth = True
    bm.to_mesh(a)
    bm.free()


def merge_fragments(parts, Fr, log):
    """Each smaller piece of a part is moved to the part it touches most (exact join, no boolean)."""
    from scipy.spatial import cKDTree
    parts = [list(p) for p in parts]
    frags = []
    for p in parts:
        pcs = separate(p[2])
        if len(pcs) > 1:
            bpy.data.meshes.remove(p[2])
            p[2] = pcs[0]
            frags += [(p[0], f) for f in pcs[1:]]
    tiny = [f for _, f in frags if abs(vol0(f)) < 5e-10]      # < 0.5 mm3: boolean slivers, not anatomy
    if tiny:
        log('   dropped %d boolean slivers (%.3f mm3 in all)' % (len(tiny), sum(abs(vol0(f)) for f in tiny) * 1e9))
    frags = [(o, f) for o, f in frags if abs(vol0(f)) >= 5e-10]
    for owner, f in frags:
        fv = np.array([v.co for v in f.vertices])
        best, nb = None, 0
        for p in parts:
            pv = np.array([v.co for v in p[2].vertices])
            k = int((cKDTree(pv).query(fv)[0] < 1e-6).sum())
            if k > nb:
                best, nb = p, k
        c = fv.mean(0) - Fr['o']
        loc = '(l %+.0f a %+.0f n %+.0f mm)' % tuple(1000 * (c @ Fr[k]) for k in 'lan')
        if best is None or best[0] == owner:
            log('   fragment %.3f cm3 of %s %s touches no other part - kept' % (vol0(f) * 1e6, owner, loc))
            best = [p for p in parts if p[0] == owner][0]
        else:
            log('   fragment %.3f cm3 of %s %s -> %s' % (vol0(f) * 1e6, owner, loc, best[0]))
        join(best[2], f)
        bpy.data.meshes.remove(f)
    for p in parts:                                          # close any small hole the cut clean-up left
        bm = bmesh.new()
        bm.from_mesh(p[2])
        bnd = [e for e in bm.edges if e.is_boundary]
        n0 = len(bnd)
        for _ in range(4):
            if not bnd:
                break
            bmesh.ops.holes_fill(bm, edges=bnd, sides=0)
            bnd = [e for e in bm.edges if e.is_boundary]
            if bnd:                                          # awkward hole: widen it by one ring, then fill
                ring = {f for e in bnd for v in e.verts for f in v.link_faces}
                bmesh.ops.delete(bm, geom=list(ring), context='FACES')
                bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
                bnd = [e for e in bm.edges if e.is_boundary]
        if n0:
            bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
            bm.to_mesh(p[2])
            log('   closed %d open edges in %s (left %d)' % (n0, p[0], len(bnd)))
        bm.free()
    return [tuple(p) for p in parts]
