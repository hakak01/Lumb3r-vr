"""Phase C2: adds endplates, facet joints, epidural/foraminal fat, internal vertebral venous plexus, medial branches /
L5 dorsal ramus, sinuvertebral nerves and landmark patches to the gaps item list (called from build_gaps.py).
Measurements -> data/raw/c2_checks.json (written into docs/CHECKS.md by hand)."""
import json, os
import numpy as np
import c1_space, c2_endplate, c2_facet, c2_fat, c2_veins, c2_nerves, c2_marks

FO_NAME = {'L3': 'L3-4', 'L4': 'L4-5', 'L5': 'L5-S1', 'S1': 'S1', 'S2': 'S2'}


def neural_field(D, fl, sac, roots, log):
    """Clearance field that also treats the dural sac, roots, sleeves, DRGs and spinal nerves as obstacles."""
    obs = c1_space.obstacles(D, fl)
    obs['neural'] = [sac['dura']] + [r['meshes'][k] for r in roots for k in ('vent', 'dors', 'drg', 'sleeve', 'nerve')]
    return c1_space.Field(obs, log)


def build(K, D, fl, sac, F, EX, roots, add, log, out_json):
    for r in roots:
        r['fo_name'] = FO_NAME[r['level']]
    log('C2 step 1: cartilaginous endplates')
    eps = c2_endplate.build(D, log)
    for e in eps:
        add(e['name'], e['mesh'], 'disc', 'Cartilage', e['level'], 'mid', 'endplate')
    log('C2 step 2: facet joints')
    fac = c2_facet.build(D, log)
    for f in fac:
        lv, sd, P = f['level'], f['side'], f['parts']
        add('%s facet cartilage, %s inferior facet (%s)' % (lv, f['up'], sd), P['IAP'], 'ligament_capsule', 'Cartilage', lv, sd, 'facet cartilage')
        add('%s facet cartilage, %s superior facet (%s)' % (lv, f['lo'], sd), P['SAP'], 'ligament_capsule', 'Cartilage', lv, sd, 'facet cartilage')
        add('%s facet joint capsule (%s)' % (lv, sd), P['capsule'], 'ligament_capsule', 'Ligament', lv, sd, 'facet capsule')
    log('C2 step 3: epidural and foraminal fat')
    pads, fora = c2_fat.build(K, D, sac, fl, F, roots, log)
    for p in pads:
        band = 'band' in p['name']
        add(p['name'], p['mesh'], 'ligament_capsule' if band else 'epidural_fat', 'Ligament' if band else 'Fat',
            p['level'], 'mid', 'prelaminar band' if band else 'epidural fat')
    for p in fora:
        add(p['name'], p['mesh'], 'epidural_fat', 'Fat', p['level'], p['side'], 'foraminal fat')
    log('C2 step 4: internal vertebral venous plexus (neural clearance field)')
    F2 = neural_field(D, fl, sac, roots, log)
    veins = c2_veins.build(K, D, sac, fl, F2, log)
    for v in veins:
        part = 'basivertebral vein' if 'basiv' in v['name'] else 'intervertebral vein' if 'Intervert' in v['name'] else 'venous plexus'
        add(v['name'], v['mesh'], 'vein', 'Vein', v.get('level', ''), v.get('side', 'mid'), part, hidden=v.get('hidden', False))
    log('C2 steps 5-6: medial branches, L5 dorsal ramus, sinuvertebral nerves')
    mbs, svn = c2_nerves.build(K, D, fl, roots, F2, log)
    for n in mbs + svn:
        part = 'sinuvertebral nerve' if 'sinu' in n['name'] else 'dorsal ramus' if 'ramus' in n['name'] else 'medial branch'
        add(n['name'], n['mesh'], 'nerve', 'Nerve', n['level'], n['side'], part)
    log('C2 step 7: landmark patches')
    marks = c2_marks.build(K, F, sac, roots, eps, log)
    for m in marks:
        add(m['name'], m['mesh'], 'landmark', 'Landmark', m['level'], m['side'], m['part'])
    clear = {}
    for nm, items in (('facet', [(f['level'] + ' ' + f['side'], f['parts']['capsule'][0]) for f in fac]),
                      ('veins', [(v['name'], v['mesh'][0]) for v in veins if 'basiv' not in v['name']]),
                      ('nerves', [(n['name'], n['mesh'][0]) for n in mbs + svn]),
                      ('fat', [(p['name'], p['mesh'][0]) for p in pads + fora])):
        clear[nm] = {k: [round(c[0], 2), c[1]] for k, V in items for c in [EX.min_clear(V)]}
    checks = dict(endplates={e['name']: e['stats'] for e in eps},
                  facets={f['level'] + ' ' + f['side']: f['stats'] for f in fac},
                  fat={p['name']: {k: p[k] for k in ('length', 'depth', 'thick') if k in p} for p in pads + fora},
                  kambin={m['name']: {k: m['stats'][k] for k in ('base', 'height', 'area')} for m in marks if 'stats' in m},
                  recess={m['name']: m['area'] for m in marks if m['part'] == 'lateral recess'},
                  clearance_to_bone_disc_ligament=clear)
    json.dump(checks, open(out_json, 'w'), indent=1, default=float)
