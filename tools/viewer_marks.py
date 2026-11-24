"""Phase B: write the foramen centres measured in Phase A (data/raw/checks.json, check_lumbar.py) into assets/model.json
for the viewer (Foramen / Posterolateral views, sagittal snaps, fly-in). glTF metres (+x left, +y up, +z anterior).
Centre = parasagittal plane of the measurement (plane_l), AP position of the tallest gap (height_max_at_a),
halfway down from the upper pedicle's lower edge (pedicle_lower_edge_n - height_max / 2).
Run: python3 -I tools/viewer_marks.py"""
import json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lgeom import frame, to_world

R = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
C = json.load(open(os.path.join(R, 'data/raw/checks.json')))
L = json.load(open(os.path.join(R, 'data/raw/a2_landmarks.json')))['discs']
MP = os.path.join(R, 'assets/model.json')
M = json.load(open(MP))
out = {}
for d, k in (('L3-4', 'L3-L4'), ('L4-5', 'L4-L5'), ('L5-S1', 'L5-S1')):
    Fr = frame(np.array(L[k]['n']), C[d]['disc_centre'])
    for side, f in C[d]['foramen'].items():
        q = np.array([f['plane_l_mm'], f['height_max_at_a_mm'], f['pedicle_lower_edge_n_mm'] - f['height_max'] / 2]) / 1000
        p = to_world(Fr, q)
        out[f'{d} {side}'] = [round(float(p[0]), 5), round(float(p[2]), 5), round(float(-p[1]), 5)]
        print(d, side, 'local mm', np.round(q * 1000, 1), 'height', f['height_max'])
M['foramen'] = out
M['_help'] = ('center = centre of the L4-5 disc; foramen = foramen centres from Phase A (tools/viewer_marks.py). '
              'glTF metres: +x patient left, +y up, +z anterior; the viewer puts center at the origin.')
json.dump(M, open(MP, 'w'), indent=1)
