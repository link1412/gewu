"""Run inside Blender: pour the coals with Bullet and write where they came to rest. s69_mutan.py calls it.

    blender -b --factory-startup --python-exit-code 1 -P s69_pile_bpy.py -- in.npz out.json

in.npz: n; box, half sizes (x, y) of the walls that keep the pour together; frames, walls_off: the walls go at that frame and the pile slumps to rest with nothing holding it, or coals would be left leaning on something that is not in the picture; V{i}, F{i}, the hull of coal i in its own frame; R{i}, t{i}, where it starts. Units are cm taken as Blender units, so gravity is strong for the size and the pour is quick; only the resting state is used. Each collision shape is the coal's convex hull, so a coal cannot nest in another's hollow.
out.json: a list of {"R": 3 x 3, "t": 3}, world = R p + t; and the largest movement over the last frames, to show that it had stopped.
"""

import json
import sys

import bpy
import numpy as np

a = sys.argv[sys.argv.index("--") + 1 :]
d = np.load(a[0])
n = int(d["n"])
FRAMES = int(d["frames"])
WALLS_OFF = int(d["walls_off"])

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
vl = bpy.context.view_layer
bpy.ops.rigidbody.world_add()
rw = scene.rigidbody_world
rw.substeps_per_frame = 8
rw.solver_iterations = 25
rw.point_cache.frame_start = 1
rw.point_cache.frame_end = FRAMES
scene.frame_start, scene.frame_end = 1, FRAMES


def add(name, V, F, passive=False):
    me = bpy.data.meshes.new(name)
    me.from_pydata(V.tolist(), [], F.tolist())
    me.update()
    ob = bpy.data.objects.new(name, me)
    scene.collection.objects.link(ob)
    vl.objects.active = ob
    ob.select_set(True)
    bpy.ops.rigidbody.object_add(type="PASSIVE" if passive else "ACTIVE")
    ob.select_set(False)
    rb = ob.rigid_body
    rb.friction = 0.9
    rb.restitution = 0.0
    rb.use_margin = True
    rb.collision_margin = 0.01
    if passive:
        rb.collision_shape = "BOX"
    else:
        rb.collision_shape = "CONVEX_HULL"
        rb.mesh_source = "BASE"
        rb.linear_damping = 0.6
        rb.angular_damping = 0.7
    return ob


def box(name, c, h):
    """Blender's box shape is centred on the object's origin: so is this mesh."""
    V = np.array([[x, y, z] for z in (-1, 1) for y in (-1, 1) for x in (-1, 1)], float) * np.array(h)
    ob = add(name, V, np.array([[0, 1, 3, 2], [4, 5, 7, 6], [0, 1, 5, 4], [2, 3, 7, 6], [0, 2, 6, 4], [1, 3, 7, 5]]), passive=True)
    ob.location = c
    return ob


# the floor, its top at z = 0, and the walls
BX, BY = (float(v) for v in d["box"])
box("floor", (0, 0, -5), (200, 200, 5))
walls = [box("wx0", (-BX - 5, 0, 60), (5, 200, 60)), box("wx1", (BX + 5, 0, 60), (5, 200, 60)), box("wy0", (0, -BY - 5, 60), (200, 5, 60)), box("wy1", (0, BY + 5, 60), (200, 5, 60))]
for w in walls:
    w.rigid_body.kinematic = True  # moved by hand when they go

obs = []
for i in range(n):
    ob = add(f"c{i}", d[f"V{i}"], d[f"F{i}"])
    M = np.eye(4)
    M[:3, :3], M[:3, 3] = d[f"R{i}"], d[f"t{i}"]
    ob.matrix_world = M.T.tolist()
    ob.rigid_body.mass = float(d[f"m{i}"])
    obs.append(ob)
vl.update()


def now():
    dg = bpy.context.evaluated_depsgraph_get()
    return [np.array(o.evaluated_get(dg).matrix_world) for o in obs]


last = None
for f in range(1, FRAMES + 1):
    if f == WALLS_OFF:
        for k, w in enumerate(walls):
            w.location = (2000.0 + 500.0 * k, 2000.0, 2000.0)
    scene.frame_set(f)
    if f == FRAMES - 24:
        last = now()
M = now()
moved = max(float(np.linalg.norm(p[:3, 3] - q[:3, 3])) for p, q in zip(M, last))
json.dump({"moved": moved, "poses": [{"R": m[:3, :3].tolist(), "t": m[:3, 3].tolist()} for m in M]}, open(a[1], "w"))
print(f"pile: {n} coals, moved at most {moved:.4f} over the last 24 frames, top {max(m[2, 3] for m in M):.1f}")
