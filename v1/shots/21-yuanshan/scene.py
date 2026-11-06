"""Shot 21 v1 (shader shot, DESIGN §3.8): a ridge at dusk, silhouetted against the sky. Runs inside Blender (Cycles),
run by tools/shotkit.py (python3 -I tools/shotkit.py look|run 21; was ridge.py before S10):

    blender -b --factory-startup --python-exit-code 1 -P scene.py -- --out $PWD/x.exr [--spp N --res WxH --device GPU|CPU]

Nothing in the shot moves (the original's 10 frames are a still: spec motion 0), so ONE render feeds all frames; the
per-frame sensor noise comes from tools/camera.py develop.

Everything is procedural and [A] (chosen by eye against the original, not measured):
- camera 135 mm on full frame, f/2.0, focused 4 cm in front of the crest 1 m away: a miniature scale, picked only for the shallow
  depth of field the original has (the crest soft, the body lumps blurred);
- the hill: a height field whose crest is a circle in the image (spec arc: radius 1.21 frame widths, apex at the
  centre), fBm on top; ~2000 noise-displaced rocks half buried along the crest and on the slope facing us; a few small
  pines and shrubs (stacked jagged cones, sphere clusters) on the right shoulder;
- the sky: stacked emitting planes behind the hill, each Add(Transparent, Emission(basis image)) in its own light
  group, so tools/lightfit.py mixes the gradient per channel [F]; they also back-light the rocks. A low sun from
  behind upper left (group "sun") gives the rim; a dim area light behind the camera (group "fill") the body.
Writes OUT (combined), OUT.<group>.exr for every group, OUT.albedo.exr, OUT.normal.exr (unflipped: Blender's
orientation is the image's) and OUT.json.
"""

import argparse
import json
import math
import os
import sys
import time

import bpy
import numpy as np
from mathutils import Vector

FOCAL_MM, SENSOR_MM, FNUM = 135.0, 36.0, 2.0
D = 1.0                                                   # camera -> crest (m) [A]
W = 2 * D * SENSOR_MM / 2 / FOCAL_MM                      # frame width at the crest
R_ARC = 0.989 * W                                         # spec arc 1.21 W, tightened by the measured sag ratios of two tries (1.21 W: 0.707; 0.855 W: 1.175) (the rocks flatten the outline) [F]
X_APEX = 0.0 * W                                        # apex 0.489 of the width [F]
Z_CREST = -0.0018                                         # crest apex below the axis; the rocks stand on it [A, tuned to the arc]
SKY_Y = D + 1.0
RNG = np.random.default_rng(21)


def args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--spp", type=int, default=512)
    ap.add_argument("--res", default="960x540")
    ap.add_argument("--device", default="GPU")
    ap.add_argument("--seed", type=int, default=0)
    return ap.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])


# --- noise ----------------------------------------------------------------------------------------
class Noise:
    """fBm as sums of random plane waves (cheap, smooth, isotropic enough at these sizes)."""
    def __init__(self, dim, octaves, base, waves=7, gain=0.5, seed=0):
        r = np.random.default_rng(seed)
        self.terms = []
        for o in range(octaves):
            k = r.normal(size=(waves, dim))
            k /= np.linalg.norm(k, axis=1, keepdims=True)
            self.terms.append((k * base * 2 ** o * r.uniform(0.8, 1.25, (waves, 1)), r.uniform(0, 2 * np.pi, waves),
                               gain ** o / math.sqrt(waves)))

    def __call__(self, p):
        return sum(a * np.cos(p @ k.T + ph).sum(-1) for k, ph, a in self.terms)


def crest_z(x):
    return Z_CREST - R_ARC + np.sqrt(np.maximum(R_ARC ** 2 - (x - X_APEX) ** 2, 0.0))


N2 = Noise(2, 6, 40.0, seed=1)


def ground(x, y):
    dy = y - D
    slope = np.where(dy < 0, 2.2, 4.0) * dy ** 2 + np.where(dy < 0, 0.08, 0.02) * np.abs(dy)
    return crest_z(x) - slope + 0.0035 * N2(np.stack([x, y], -1))


# --- meshes ---------------------------------------------------------------------------------------
def mesh(name, V, F, mat, group=None):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in V], [], [tuple(f) for f in F])
    me.update()
    for p in me.polygons:
        p.use_smooth = True
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    ob.data.materials.append(mat)
    if group:
        ob.lightgroup = group
    return ob


def icosphere(sub):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=sub, radius=1.0)
    ob = bpy.context.active_object
    V = np.array([v.co[:] for v in ob.data.vertices])
    F = np.array([p.vertices[:] for p in ob.data.polygons])
    bpy.data.objects.remove(ob)
    return V, F


def hill(mat):
    nx, ny = 900, 360
    xs = np.linspace(-0.24, 0.24, nx)
    ys = np.linspace(D - 0.45, D + 0.2, ny)
    X, Y = np.meshgrid(xs, ys)
    Z = ground(X, Y)
    V = np.stack([X, Y, Z], -1).reshape(-1, 3)
    i = np.arange(ny - 1)[:, None] * nx + np.arange(nx - 1)[None]
    i = i.ravel()
    F = np.concatenate([np.stack([i, i + 1, i + nx + 1], 1), np.stack([i, i + nx + 1, i + nx], 1)])
    # winding: normals up (+z) — (x+1) x (y+1) points up
    return mesh("hill", V, F, mat)


def rocks(mat):
    V0, F0 = icosphere(3)
    N3 = Noise(3, 4, 2.2, seed=2)
    Vs, Fs, off = [], [], 0
    specs = []
    # crest: dense, the silhouette; slope: sparser lumps toward us
    for n, ylo, yhi, smin, smax in ((1600, -0.035, 0.02, 0.0012, 0.0050), (2500, -0.3, -0.03, 0.0008, 0.0035)):
        x = RNG.uniform(-0.2, 0.2, n)
        y = D + RNG.uniform(ylo, yhi, n)
        s = np.exp(RNG.uniform(np.log(smin), np.log(smax), n))
        specs.append((x, y, s))
    x, y, s = (np.concatenate(v) for v in zip(*specs))
    for k in range(len(x)):
        d = V0 * (1 + 0.35 * N3(V0 + RNG.normal(0, 10, 3)))[:, None]
        sc = s[k] * np.array([RNG.uniform(0.8, 1.5), RNG.uniform(0.8, 1.5), RNG.uniform(0.55, 1.0)])
        a = RNG.uniform(0, 2 * np.pi)
        rot = np.array([[math.cos(a), -math.sin(a), 0], [math.sin(a), math.cos(a), 0], [0, 0, 1]])
        p = (d * sc) @ rot.T + [x[k], y[k], ground(np.array(x[k]), np.array(y[k])) - RNG.uniform(0.25, 0.55) * sc[2]]
        Vs.append(p)
        Fs.append(F0 + off)
        off += len(V0)
    return mesh("rocks", np.concatenate(Vs), np.concatenate(Fs), mat)


def cone_ring(cx, cy, z0, r, h, n, jag):
    """A jagged cone (one pine tier): ring of n points at z0 with radius r*(1 +- jag), apex at z0 + h."""
    t = np.linspace(0, 2 * np.pi, n, endpoint=False)
    rr = r * (1 + jag * RNG.uniform(-1, 1, n)) * np.where(np.arange(n) % 2, 1.0, 0.55)
    ring = np.stack([cx + rr * np.cos(t), cy + rr * np.sin(t), z0 + RNG.uniform(-0.15, 0.1, n) * h], 1)
    V = np.vstack([ring, [[cx, cy, z0 + h]], [[cx, cy, z0]]])
    F = [(i, (i + 1) % n, n) for i in range(n)] + [((i + 1) % n, i, n + 1) for i in range(n)]
    return V, np.array(F)


def plants(mat):
    Vs, Fs, off = [], [], 0
    V0, F0 = icosphere(2)

    def add(V, F):
        nonlocal off
        Vs.append(V)
        Fs.append(F + off)
        off += len(V)
    # pines [A]: small, on the right shoulder and one on the left, at the crest's depth
    for cx, hgt in ((0.072, 0.011), (0.081, 0.0075), (0.098, 0.009), (-0.105, 0.007)):
        cy = D + RNG.uniform(-0.01, 0.01)
        z = float(ground(np.array(cx), np.array(cy))) - 0.001
        add(*cone_ring(cx, cy, z, 0.0004, hgt, 6, 0.0))                     # trunk
        tiers = 5
        for t in range(tiers):
            f = t / tiers
            add(*cone_ring(cx, cy, z + hgt * (0.25 + 0.6 * f), hgt * (0.32 - 0.22 * f), hgt * 0.32, 14, 0.5))
    # shrubs: clusters of small spheres
    for cx in RNG.uniform(-0.17, 0.17, 26):
        cy = D + RNG.uniform(-0.02, 0.01)
        z = float(ground(np.array(cx), np.array(cy)))
        r0 = RNG.uniform(0.0012, 0.0028)
        for _ in range(9):
            o = RNG.normal(0, 1, 3) * [r0, r0 * 0.5, r0 * 0.6]
            add(V0 * r0 * RNG.uniform(0.35, 0.7) + [cx + o[0], cy + o[1], z + r0 * 0.6 + abs(o[2])], F0)
    return mesh("plants", np.concatenate(Vs), np.concatenate(Fs), mat)


# --- materials ------------------------------------------------------------------------------------
def rock_material():
    m = bpy.data.materials.new("rock")
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0.09, 0.09, 0.09, 1)        # grey: colour is the lights' [F]
    b.inputs["Roughness"].default_value = 0.75
    b.inputs["Specular IOR Level"].default_value = 0.4
    b.inputs["Sheen Weight"].default_value = 0.6                       # dust/crust: grazing back-light brightens the rim
    b.inputs["Sheen Roughness"].default_value = 0.4
    tex = nt.nodes.new("ShaderNodeTexNoise")
    tex.inputs["Scale"].default_value = 900.0
    tex.inputs["Detail"].default_value = 6.0
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.6
    bump.inputs["Distance"].default_value = 0.0004
    nt.links.new(tex.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    return m


SKY_BASES = {                         # over a sky plane: u 0..1 left to right, v 0..1 bottom to top (~1.45 frames)
    "s_const": lambda u, v, M: 1.0,
    "s_left": lambda u, v, M: M("SUBTRACT", 1.0, u),
    "s_left3": lambda u, v, M: M("POWER", M("SUBTRACT", 1.0, u), 3.0),
    "s_top": lambda u, v, M: v,
    "s_cut2": lambda u, v, M: M("DIVIDE", 1.0, M("ADD", 1.0, M("EXPONENT", M("DIVIDE", M("SUBTRACT", u, 0.58), 0.08)))),
    "s_glow2": lambda u, v, M: M("EXPONENT", M("MULTIPLY", -1 / 0.55 ** 2, M("ADD", M("POWER", u, 2.0),
                                                                           M("POWER", M("SUBTRACT", v, 1.0), 2.0)))),
    "s_cut": lambda u, v, M: M("DIVIDE", 1.0, M("ADD", 1.0, M("EXPONENT", M("DIVIDE", M("SUBTRACT", u, 0.68), 0.05)))),
    "s_glow": lambda u, v, M: M("EXPONENT", M("MULTIPLY", -1 / 0.3 ** 2, M("ADD", M("POWER", M("SUBTRACT", u, 0.05), 2.0),
                                                                          M("POWER", M("SUBTRACT", v, 1.0), 2.0)))),
    "s_haze": lambda u, v, M: M("EXPONENT", M("MULTIPLY", -1 / 0.08 ** 2, M("POWER", M("SUBTRACT", v, 0.54), 2.0))),
}


def emit_plane(name, basis, y, half_w, half_h, z0, group):
    """Add(Transparent, Emission(strength = basis(u, v))) built from math nodes on the plane's generated coordinates
    (images made in a background Blender 5.2 came out black: pixels set from Python did not stick)."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    add = nt.nodes.new("ShaderNodeAddShader")
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    tr.inputs["Color"].default_value = (1, 1, 1, 1)
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (1, 1, 1, 1)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Generated"], sep.inputs[0])

    def M(op, x, y_=None):
        n = nt.nodes.new("ShaderNodeMath")
        n.operation = op
        for i, val in enumerate((x, y_)):
            if val is None:
                continue
            if isinstance(val, (int, float)):
                n.inputs[i].default_value = float(val)
            else:
                nt.links.new(val, n.inputs[i])
        return n.outputs[0]
    val = basis(sep.outputs["X"], sep.outputs["Z"], M)
    if isinstance(val, float):
        em.inputs["Strength"].default_value = val
    else:
        nt.links.new(val, em.inputs["Strength"])
    nt.links.new(tr.outputs[0], add.inputs[0])
    nt.links.new(em.outputs[0], add.inputs[1])
    nt.links.new(add.outputs[0], out.inputs["Surface"])
    V = [(-half_w, y, z0 - half_h), (half_w, y, z0 - half_h), (half_w, y, z0 + half_h), (-half_w, y, z0 + half_h)]
    ob = mesh(name, V, [(0, 1, 2, 3)], m, group)
    for p in ob.data.polygons:
        p.use_smooth = False
    return ob


def setup(a):
    s = bpy.context.scene
    s.render.engine = "CYCLES"
    if a.device == "GPU":
        prefs = bpy.context.preferences.addons["cycles"].preferences
        prefs.compute_device_type = "METAL"
        prefs.get_devices()
        for d in prefs.devices:
            d.use = d.type == "METAL"
        if not any(d.use for d in prefs.devices):
            raise SystemExit("no Metal GPU")
    s.cycles.device = a.device
    s.render.resolution_x, s.render.resolution_y = map(int, a.res.split("x"))
    s.render.resolution_percentage = 100
    s.cycles.samples = a.spp
    s.cycles.use_adaptive_sampling = False
    s.cycles.use_denoising = False
    s.cycles.max_bounces = 8
    s.cycles.transparent_max_bounces = 32
    s.cycles.seed = a.seed
    s.cycles.pixel_filter_type = "GAUSSIAN"
    s.cycles.filter_width = 1.5
    s.cycles.sample_clamp_direct = s.cycles.sample_clamp_indirect = 0.0
    s.view_settings.view_transform = "Standard"
    w = bpy.data.worlds.new("black")
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.0
    s.world = w


def main():
    a = args()
    t0 = time.time()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    setup(a)
    s = bpy.context.scene
    rock = rock_material()
    hill(rock)
    rocks(rock)
    plants(rock)
    groups = []
    # sky planes: 2 m from the camera, ~1.45 frames wide/high there
    hw, hh = 1.45 * (SKY_Y * SENSOR_MM / 2 / FOCAL_MM), 1.45 * (SKY_Y * SENSOR_MM / 2 / FOCAL_MM) * 9 / 16
    for i, (g, fn) in enumerate(SKY_BASES.items()):
        emit_plane(g, fn, SKY_Y + 0.002 * i, hw, hh, 0.0, g)
        groups.append(g)
    # no backstop: the world is black, and a backstop would shadow the sun
    # sun: behind the hill, upper left, low [A]
    sd = bpy.data.lights.new("sun", "SUN")
    sd.energy = 1.0
    sd.angle = math.radians(1.0)
    sun = bpy.data.objects.new("sun", sd)
    bpy.context.collection.objects.link(sun)
    toward = Vector((0.4, -1.0, -0.18)).normalized()                  # the light's travel direction
    sun.rotation_euler = (-toward).to_track_quat("Z", "Y").to_euler()  # a sun shines along its -Z
    sun.lightgroup = "sun"
    groups.append("sun")
    fd = bpy.data.lights.new("fill", "AREA")
    fd.energy = 1.0
    fd.size = 1.0
    fill = bpy.data.objects.new("fill", fd)
    bpy.context.collection.objects.link(fill)
    fill.location = (0, -1.0, 0.3)
    fill.rotation_euler = (Vector((0, D, 0)) - fill.location).normalized().__neg__().to_track_quat("Z", "Y").to_euler()
    fill.lightgroup = "fill"
    groups.append("fill")
    for g in groups:
        s.view_layers[0].lightgroups.add(name=g)
    # camera
    cd = bpy.data.cameras.new("cam")
    cd.lens, cd.sensor_width, cd.sensor_fit = FOCAL_MM, SENSOR_MM, "HORIZONTAL"
    cd.clip_start, cd.clip_end = 0.01, 20
    cd.dof.use_dof = True
    cd.dof.focus_distance = D - 0.04                  # just in front of the crest: the crest soft, as the original [A]
    cd.dof.aperture_fstop = FNUM
    cam = bpy.data.objects.new("cam", cd)
    bpy.context.collection.objects.link(cam)
    cam.location = (0, 0, 0)
    cam.rotation_euler = (math.pi / 2, 0, 0)                            # looking along +y, z up
    s.camera = cam
    t1 = time.time()
    # render all passes
    import OpenImageIO as oiio
    s.view_layers[0].cycles.denoising_store_passes = True
    st = s.render.image_settings
    st.media_type = "MULTI_LAYER_IMAGE"
    st.file_format = "OPEN_EXR_MULTILAYER"
    st.color_depth = "32"
    st.exr_codec = "ZIP"
    out = os.path.abspath(a.out)
    stem = os.path.splitext(out)[0]
    layers = stem + ".layers.exr"
    s.render.filepath = layers
    bpy.ops.render.render(write_still=True)
    t2 = time.time()
    inp = oiio.ImageInput.open(layers)
    parts, i = {}, 0
    while inp.seek_subimage(i, 0):
        sp = inp.spec()
        parts[sp.getattribute("name")] = inp.read_image(i, 0, 0, sp.nchannels, oiio.FLOAT)
        i += 1
    inp.close()
    vl = s.view_layers[0].name
    want = {out: "Combined", stem + ".albedo.exr": "Denoising Albedo", stem + ".normal.exr": "Denoising Normal",
            **{f"{stem}.{g}.exr": f"Combined_{g}" for g in groups}}
    for path, name in want.items():
        key = f"{vl}.{name}"
        if key not in parts:
            raise SystemExit(f"{layers}: no pass {key} (has {sorted(parts)})")
        arr = np.ascontiguousarray(parts[key][:, :, :3], np.float32)
        spec = oiio.ImageSpec(arr.shape[1], arr.shape[0], 3, oiio.FLOAT)
        spec.attribute("compression", "zip")
        o = oiio.ImageOutput.create(path)
        if o is None or not o.open(path, spec) or not o.write_image(arr):
            raise SystemExit(f"{path}: could not write")
        o.close()
    os.remove(layers)
    info = {"device": a.device, "res": a.res, "spp": a.spp, "seed": a.seed, "groups": groups,
            "seconds_build": round(t1 - t0, 1), "seconds_render": round(t2 - t1, 1), "blender": bpy.app.version_string}
    json.dump(info, open(stem + ".json", "w"), indent=1)
    print("CYCLES_DONE", json.dumps(info))


main()
