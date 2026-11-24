"""Phase C1 step 5: keep the old schematic cauda equina roots (below mid-L3) and the old 0.6 mm flavum sheets in
assets/lumbar.glb, renamed "... (old)", hidden by default (manifest: hidden true, part "superseded").
Edits only the names in the GLB JSON chunk and assets/manifest.json. Idempotent.  python3 -I tools/c1_old.py"""
import json, os, struct
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GLB, MAN = os.path.join(ROOT, 'assets/lumbar.glb'), os.path.join(ROOT, 'assets/manifest.json')
OLD = ['%s root (%s)' % (l, s) for l in ('L3', 'L4', 'L5', 'S1', 'S2', 'S3', 'S4') for s in ('left', 'right')] + \
      ['Ligamentum flavum %s (%s)' % (l, s) for l in ('L3-4', 'L4-5', 'L5-S1') for s in ('left', 'right')] + \
      ['Cauda equina (central bundle)']


def main():
    b = bytearray(open(GLB, 'rb').read())
    n = struct.unpack('<I', b[12:16])[0]
    j = json.loads(b[20:20 + n]); rest = b[20 + n:]
    done = 0
    for key in ('nodes', 'meshes'):
        for o in j.get(key, []):
            if o.get('name') in OLD:
                o['name'] += ' (old)'; done += 1
    js = json.dumps(j, separators=(',', ':')).encode()
    js += b' ' * (-len(js) % 4)
    out = struct.pack('<III', 0x46546C67, 2, 12 + 8 + len(js) + len(rest)) + struct.pack('<II', len(js), 0x4E4F534A) + js + rest
    open(GLB, 'wb').write(out)
    man = json.load(open(MAN))
    for e in man:
        if e['name'] in OLD:
            e['name'] += ' (old)'; e['hidden'] = True; e['part'] = 'superseded'
    json.dump(man, open(MAN, 'w'), indent=1)
    print('renamed %d GLB names; manifest entries now "(old)": %d' % (done, sum(e['name'].endswith('(old)') for e in man)))


if __name__ == '__main__':
    main()
