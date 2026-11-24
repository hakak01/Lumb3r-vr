"""Phase C: approximate structures missing from the source, built inside this model's bony canal and foramina
-> assets/gaps.glb + assets/gaps.json (approx: true, source "rules (approx)"). Phase C1: dural sac, arachnoid, filum
terminale, L3-S2 ventral/dorsal roots, dural root sleeves, DRG, spinal nerves, ligamentum flavum L3-4..L5-S1.
Run from the repo root:  python3 -I tools/build_gaps.py   (~1 min; then python3 -I tools/c1_old.py once)
Needs: numpy, scipy; data/raw/lumbar_raw.glb (build_assets.py); Node.js (npx) for meshopt.
Log: data/raw/gaps_log.txt; measurements: data/raw/c1_checks.json (written into docs/CHECKS.md by hand)."""
import os, sys, json, subprocess, time
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import numpy as np
import glbio, c1_canal, c1_flavum, c1_dura, c1_space, c1_roots

RAW_OUT = os.path.join(ROOT, 'data/raw/gaps_raw.glb')
OUT = os.path.join(ROOT, 'assets')
LOG = os.path.join(ROOT, 'data/raw/gaps_log.txt')
SRC = 'rules (approx)'


def gltf(V):
    """Z-Anatomy mm (z up) -> glTF metres (y up)."""
    return np.c_[V[:, 0], V[:, 2], -V[:, 1]] / 1000.0


def main():
    t0 = time.time()
    log_f = open(LOG, 'w')
    log = lambda *a: (print(*a, file=log_f, flush=True), print(*a))
    K = c1_canal.build(log=log); D = c1_canal.load()
    items = []
    def add(name, mesh, layer, mat, level='', side='mid', part='', note=''):
        items.append(dict(name=name, mesh=mesh, layer=layer, mat=mat, level=level, side=side, part=part, note=note))
    fl = c1_flavum.build(K, log)
    for f in fl:
        add(f['name'], (f['V'], f['F']), 'ligament_capsule', 'Ligament', f['level'], f['side'], 'ligamentum flavum')
    sac = c1_dura.build(K, fl, D, log)
    add('Dural sac', sac['dura'], 'neural', 'Fascia', part='dura')
    add('Arachnoid mater', sac['arach'], 'neural', 'Fascia', part='arachnoid')
    add('Filum terminale internum', sac['fil_int'], 'neural', 'Nerve', part='filum terminale')
    add('Filum terminale externum (dural filum)', sac['fil_ext'], 'neural', 'Fascia', part='filum terminale')
    obs = c1_space.obstacles(D, fl)
    F = c1_space.Field(obs, log); EX = c1_space.Exact(obs)
    roots = c1_roots.build(K, D, sac, F, EX, log)
    for r in roots:
        lv, sd, m = r['level'], r['side'], r['meshes']
        add('%s ventral root (%s)' % (lv, sd), m['vent'], 'neural', 'Nerve', lv, sd, 'ventral root')
        add('%s dorsal root (%s)' % (lv, sd), m['dors'], 'neural', 'Nerve', lv, sd, 'dorsal root')
        add('%s spinal ganglion (%s)' % (lv, sd), m['drg'], 'neural', 'Nerve', lv, sd, 'spinal ganglion')
        add('%s dural root sleeve (%s)' % (lv, sd), m['sleeve'], 'neural', 'Fascia', lv, sd, 'dural sleeve')
        add('%s spinal nerve (%s)' % (lv, sd), m['nerve'], 'neural', 'Nerve', lv, sd, 'spinal nerve')
    gj = []
    for it in items:
        V, Fc = it['mesh']
        e = dict(name=it['name'], layer=it['layer'], source=SRC, approx=True, triangles=int(len(Fc)),
                 level=it['level'], side=it['side'], part=it['part'])
        gj.append(e)
    glbio.write(RAW_OUT, [(it['name'], [(gltf(it['mesh'][0]), it['mesh'][1], it['mat'])]) for it in items])
    json.dump(gj, open(os.path.join(OUT, 'gaps.json'), 'w'), indent=1)
    subprocess.run('npx -y -q @gltf-transform/cli meshopt "%s" "%s" --level medium' % (
        RAW_OUT, os.path.join(OUT, 'gaps.glb')), shell=True, check=True, stdout=subprocess.DEVNULL)
    checks = dict(sac=dict(areas=sac['areas'], tip_z=sac['tip_z'], k_tip=sac['k_tip'],
                           foramina_z=[float(K['C'][int(round(f)), 2]) for f in sac['fo']]),
                  flavum={f['name']: round(f['thick_half'], 2) for f in fl},
                  roots=[dict(level=r['level'], side=r['side'], w=r['w'], l=r['l'], rv=round(r['rv'], 2),
                              rd=round(r['rd'], 2), exit_z=round(r['exit_z'], 1), info=r['info'], join=r['join'],
                              sleeve_len=r['sleeve_len'], angle=r['angle'],
                              drg=[round(float(x), 1) for x in r['drg']],
                              clear={k: [round(v[0], 2), v[1]] for k, v in r['clear'].items()},
                              nerve_clear=round(r['nerve_clear'][0], 2)) for r in roots])
    json.dump(checks, open(os.path.join(ROOT, 'data/raw/c1_checks.json'), 'w'), indent=1, default=float)
    log('items %d, triangles %d, GLB MB raw %.2f, compressed %.2f, %.0f s' % (
        len(items), sum(e['triangles'] for e in gj), os.path.getsize(RAW_OUT) / 1e6,
        os.path.getsize(os.path.join(OUT, 'gaps.glb')) / 1e6, time.time() - t0))


if __name__ == '__main__':
    main()
