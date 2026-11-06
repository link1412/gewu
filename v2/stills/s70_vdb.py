"""Shot 70: the solver's grids to an OpenVDB file, run by Blender's own Python (its openvdb is the one Cycles reads).

    LD_LIBRARY_PATH=$B/lib $B/5.2/python/bin/python3.13 v2/stills/s70_vdb.py SIM_DIR TIME     SIM_DIR/TIME.vdb

Two grids, `fine` and `coarse`, each with its own voxel size; the shader adds them. Arrays come as (nz, ny, nx) with samples at voxel centres; a VDB's index point i sits at i * h, so the transform moves by half a voxel past the box's corner.
"""

import glob
import json
import os
import sys

B = os.environ.get("GEWU_BLENDER_ROOT", "blender-5.2.1-linux-x64")
sys.path[:0] = glob.glob(os.path.join(B, "*", "python", "lib", "python*", "site-packages"))

import numpy as np
import openvdb as vdb

d, t = sys.argv[1], sys.argv[2]
gc = json.load(open(os.path.join(d, "params.json")))["grid"]
x0, _, y0, _, z0, _ = gc["box"]
out = []
for name, h in (("fine", gc["fine"]), ("coarse", gc["coarse"])):
    # .copy(): the binding reads the buffer as C order and ignores strides, so a bare transpose comes out scrambled, in stripes
    a = np.load(os.path.join(d, f"{name}_{t}.npy")).astype(np.float32).transpose(2, 1, 0).copy()
    g = vdb.FloatGrid()
    g.copyFromArray(a, tolerance=gc["thresh"])
    g.prune(tolerance=gc["thresh"])
    g.name = name
    tr = vdb.createLinearTransform(voxelSize=h)
    tr.postTranslate((x0 + h / 2, y0 + h / 2, z0 + h / 2))
    g.transform = tr
    print(f"{name}: {a.shape}, max {float(a.max()):.3f}, {g.activeVoxelCount()/1e6:.2f} M active", flush=True)
    out.append(g)
vdb.write(os.path.join(d, f"{t}.vdb"), grids=out)
