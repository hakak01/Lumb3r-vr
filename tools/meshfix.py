"""Cut a Blender mesh at a horizontal plane and close the cut; make meshes watertight."""
import bmesh
from mathutils import Vector


def crop(me, z, keep='below'):
    """Remove the part above (keep='below') or below (keep='above') the plane z; fill the cut.
    Returns the number of faces left."""
    bm = bmesh.new()
    bm.from_mesh(me)
    no = Vector((0, 0, 1)) if keep == 'below' else Vector((0, 0, -1))
    geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
    r = bmesh.ops.bisect_plane(bm, geom=geom, dist=1e-7, plane_co=Vector((0, 0, z)), plane_no=no,
                               clear_outer=True, clear_inner=False)
    cut = [e for e in r['geom_cut'] if isinstance(e, bmesh.types.BMEdge) and e.is_valid and e.is_boundary]
    if cut:
        bmesh.ops.holes_fill(bm, edges=cut, sides=0)
    bmesh.ops.triangulate(bm, faces=bm.faces)
    n = len(bm.faces)
    bm.to_mesh(me)
    bm.free()
    return n


def stats(bm):
    """(boundary edges, non-manifold edges with >2 faces, loose verts)."""
    b = sum(1 for e in bm.edges if len(e.link_faces) == 1)
    nm = sum(1 for e in bm.edges if len(e.link_faces) > 2)
    lv = sum(1 for v in bm.verts if not v.link_faces)
    return b, nm, lv


def drop_islands(bm, frac=0.01):
    """Delete small pieces (faces joined by edges) holding < frac of all faces, e.g. loose flaps."""
    bm.faces.ensure_lookup_table()
    seen, small = set(), []
    for f0 in bm.faces:
        if f0 in seen:
            continue
        comp, stack = [], [f0]
        seen.add(f0)
        while stack:
            f = stack.pop()
            comp.append(f)
            for e in f.edges:
                for g in e.link_faces:
                    if g not in seen:
                        seen.add(g)
                        stack.append(g)
        if len(comp) < frac * len(bm.faces):
            small += comp
    if small:
        bmesh.ops.delete(bm, geom=small, context='FACES')
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    return len(small)


def watertight(me):
    """Merge duplicate vertices, drop loose parts, fill holes, fix normals.
    Returns (before, after) as (boundary, non-manifold, loose) edge/vert counts."""
    bm = bmesh.new()
    bm.from_mesh(me)
    before = stats(bm)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=1e-8)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    for _ in range(4):
        bad = {f for e in bm.edges if len(e.link_faces) > 2 for f in e.link_faces}
        if bad:                              # faces on edges shared by >2 faces: remove, then refill the hole
            bmesh.ops.delete(bm, geom=list(bad), context='FACES')
            bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
        drop_islands(bm)
        bnd = [e for e in bm.edges if e.is_boundary]
        if not bnd and not bad:
            break
        bmesh.ops.holes_fill(bm, edges=bnd, sides=0)
    bmesh.ops.triangulate(bm, faces=bm.faces)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    after = stats(bm)
    bm.to_mesh(me)
    bm.free()
    return before, after
