"""Shot 27 v1 (shader shot, DESIGN §3.8): a heap of crumpled hand-beaten gold leaf, flakes tumbling down onto it out of
the dark. Runs inside Blender (Cycles), one film frame per run:

    blender -b --factory-startup --python-exit-code 1 -P scene.py -- --frame K --out $PWD/x.exr [--spp N --res WxH --device GPU|CPU]

K = 0..7 is film frame 325 + K. The camera is still (spec: drift 0, zoom 1); what moves [A]:
- every flake of the heap flutters a little (its tilt walks ~3 deg a frame, air from the falling leaf): the glints
  move from flake to flake, as the original's glitter does (spec: mean |diff| 6.9 codes a frame, no drift);
- ~70 loose flakes fall through the dark and tumble (a few degrees to ~40 deg a frame each).
Everything [A] (chosen by eye, not measured):
- scale: built at frame width 9 cm (flakes 0.3-1.6 mm, x10 real), then scaled x10 about the camera (crest 2.5 m away, 100 mm, f/2.8)
  so the heap's face keeps its detail (at 25 cm the depth of field was ~2 mm); the glitter grain
  is 8-30 px at 1080, the original's;
- the heap: a height field whose crest is the spec arc in the image (radius 0.88 frame widths, apex 0.492, 0.467),
  covered by ~52000 flakes, each a 5x5 grid crumpled by noise (gold leaf is ~0.1 um: no thickness modelled), tilted
  up to ~40 deg off the surface (crumpled), random spin;
- gold: Principled metallic, base colour gold [A], roughness 0.14, anisotropy 0.6 along the flake's own UV (the
  beating direction: each flake has its own), a stretched-noise bump for the hammer/beating marks;
- light: a soft key from front-top-left (group "key"), a hard rim from behind-top (group "rim": the crest glitter
  and the sparkle of the falling flakes against black), a dim fill (world, group "fill"). Colours and levels are
  fitted per channel afterwards (tools/shotkit.py: lightfit, then codefit) [F].
Writes OUT, OUT.<group>.exr, OUT.albedo.exr, OUT.normal.exr, OUT.json (Blender's orientation).
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

FOCAL_MM, SENSOR_MM, FNUM = 100.0, 36.0, 1.2        # r2: shallower focus band, top and bottom go to bokeh
SC = 10.0                                                 # the model below is built at 1/10 and scaled up about the camera (image unchanged):
                                                          # at 25 cm the depth of field was ~2 mm and the heap's face a blur
D = 0.25                                                  # camera -> crest, model units (x SC = 2.5 m)
W = D * SENSOR_MM / FOCAL_MM                              # frame width at the crest
H = W * 9 / 16
R_ARC = 0.88 * W                                          # spec radius_over_width
X_APEX = (0.492 - 0.5) * W
Z_APEX = (0.5 - 0.467) * H - 0.0015                       # spec apex y; the flakes stand ~1.5 mm proud of the base [A]
CAM_Z = 0.0
SEED = 27


def args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--frame", type=int, required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--spp", type=int, default=256)
    ap.add_argument("--res", default="960x540")
    ap.add_argument("--device", default="GPU")
    ap.add_argument("--seed", type=int, default=0)
    return ap.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])


class Noise:
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


N2 = Noise(2, 5, 120.0, seed=1)


def crest_z(x):
    return Z_APEX - R_ARC + np.sqrt(np.maximum(R_ARC ** 2 - (x - X_APEX) ** 2, 0.0))


def ground(x, y):
    dy = y - D
    slope = np.where(dy < 0, 1.6, 6.0) * dy ** 2 + np.where(dy < 0, 0.12, 0.05) * np.abs(dy)
    return crest_z(x) - slope + 0.0008 * N2(np.stack([x, y], -1))


def ground_normal(x, y, e=1e-4):
    gx = (ground(x + e, y) - ground(x - e, y)) / (2 * e)
    gy = (ground(x, y + e) - ground(x, y - e)) / (2 * e)
    n = np.stack([-gx, -gy, np.ones_like(gx)], -1)
    return n / np.linalg.norm(n, axis=-1, keepdims=True)


def rot_matrices(axis, ang):
    """Rodrigues, batched: axis (N,3) unit, ang (N,) -> (N,3,3)."""
    K = np.zeros((len(axis), 3, 3))
    K[:, 0, 1], K[:, 0, 2], K[:, 1, 2] = -axis[:, 2], axis[:, 1], -axis[:, 0]
    K[:, 1, 0], K[:, 2, 0], K[:, 2, 1] = axis[:, 2], -axis[:, 1], axis[:, 0]
    s, c = np.sin(ang)[:, None, None], np.cos(ang)[:, None, None]
    return np.eye(3)[None] + s * K + (1 - c) * (K @ K)


def frame_from_normal(n, spin):
    """Orthonormal (t, b, n) per flake, t spun by `spin` about n."""
    a = np.where(np.abs(n[:, 2:3]) < 0.9, [[0, 0, 1.0]], [[1.0, 0, 0]])
    t = np.cross(a, n)
    t /= np.linalg.norm(t, axis=1, keepdims=True)
    b = np.cross(n, t)
    c, s = np.cos(spin)[:, None], np.sin(spin)[:, None]
    return c * t + s * b, -s * t + c * b, n


G = 5                                                     # flake grid


def flakes(centre, t, b, n, size, crumple, rng):
    """Batched crumpled flakes: (N,) centres/frames -> V (N*G*G, 3), F, UV."""
    N = len(centre)
    u = np.linspace(-0.5, 0.5, G)
    U, Vv = np.meshgrid(u, u)
    U, Vv = U.ravel(), Vv.ravel()
    # torn, irregular outline: stretch each flake, push the corners in or out a little
    sx = size * rng.uniform(0.7, 1.3, N)
    sy = size * rng.uniform(0.5, 1.1, N)
    jit = rng.uniform(-0.18, 0.18, (N, G * G, 2))
    h = crumple[:, None] * size[:, None] * rng.normal(0, 1, (N, G * G))
    ux = (U[None] + jit[..., 0] * (np.abs(U[None]) > 0.3)) * sx[:, None]
    vy = (Vv[None] + jit[..., 1] * (np.abs(Vv[None]) > 0.3)) * sy[:, None]
    V = centre[:, None] + ux[..., None] * t[:, None] + vy[..., None] * b[:, None] + h[..., None] * n[:, None]
    q = np.arange(G - 1)[:, None] * G + np.arange(G - 1)[None]
    q = q.ravel()
    f1 = np.stack([q, q + 1, q + G + 1], 1)
    f2 = np.stack([q, q + G + 1, q + G], 1)
    F0 = np.concatenate([f1, f2])
    F = (F0[None] + (np.arange(N) * G * G)[:, None, None]).reshape(-1, 3)
    UV = np.tile(np.stack([U + 0.5, Vv + 0.5], 1), (N, 1))
    return V.reshape(-1, 3), F, UV


def add_mesh(name, V, F, UV, mat):
    me = bpy.data.meshes.new(name)
    me.vertices.add(len(V))
    me.vertices.foreach_set("co", V.astype(np.float32).ravel())
    me.loops.add(F.size)
    me.loops.foreach_set("vertex_index", F.astype(np.int32).ravel())
    me.polygons.add(len(F))
    me.polygons.foreach_set("loop_start", np.arange(0, F.size, 3, dtype=np.int32))
    me.update()
    if UV is not None:
        lay = me.uv_layers.new(name="UVMap")
        lay.data.foreach_set("uv", UV[F.ravel()].astype(np.float32).ravel())
    me.polygons.foreach_set("use_smooth", np.ones(len(F), bool))
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    ob.data.materials.append(mat)
    return ob


def gold_material(name, rough):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (1.0, 0.78, 0.34, 1)          # gold [A]; tint is fitted in the lights
    # r2 [A]: two gold-leaf alloys, deeper (22K-like) on the near face, paler (18K, "lemon gold") toward the crest,
    # ramped by the view elevation z/y (frame bottom ~ -0.10, crest ~ 0); both stay saturated, around gold's F0
    # (1, .78, .34). One shared light colour left the middle band too orange and the bottom too yellow (B -5 / +2.5).
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(geo.outputs["Position"], sep.inputs["Vector"])
    dv = nt.nodes.new("ShaderNodeMath"); dv.operation = "DIVIDE"
    nt.links.new(sep.outputs["Z"], dv.inputs[0]); nt.links.new(sep.outputs["Y"], dv.inputs[1])
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = -0.09
    mr.inputs["From Max"].default_value = -0.01
    nt.links.new(dv.outputs[0], mr.inputs["Value"])
    mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = "RGBA"
    mx.inputs["A"].default_value = (1.0, 0.71, 0.23, 1)
    mx.inputs["B"].default_value = (1.0, 0.84, 0.45, 1)
    nt.links.new(mr.outputs["Result"], mx.inputs["Factor"])
    nt.links.new(mx.outputs["Result"], b.inputs["Base Color"])
    b.inputs["Metallic"].default_value = 1.0
    b.inputs["Roughness"].default_value = rough
    b.inputs["Anisotropic"].default_value = 0.6
    tg = nt.nodes.new("ShaderNodeTangent")
    tg.direction_type = "UV_MAP"
    tg.uv_map = "UVMap"
    nt.links.new(tg.outputs["Tangent"], b.inputs["Tangent"])
    uv = nt.nodes.new("ShaderNodeUVMap")
    uv.uv_map = "UVMap"
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (2.0, 30.0, 1.0)                # beating marks: stretched along the flake's u
    nt.links.new(uv.outputs["UV"], mp.inputs["Vector"])
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 3.0
    nz.inputs["Detail"].default_value = 4.0
    nt.links.new(mp.outputs["Vector"], nz.inputs["Vector"])
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.35
    bump.inputs["Distance"].default_value = 0.0001 * SC
    nt.links.new(nz.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    return m


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
    s.cycles.max_bounces = 6
    s.cycles.seed = a.seed
    s.cycles.pixel_filter_type = "GAUSSIAN"
    s.cycles.filter_width = 1.5
    s.cycles.sample_clamp_direct = s.cycles.sample_clamp_indirect = 0.0
    s.view_settings.view_transform = "Standard"
    w = bpy.data.worlds.new("fill")
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs["Color"].default_value = (1, 1, 1, 1)
    # r2: no fill. Metal under a uniform environment reads as matte paint (r2 preview: fill fitted 10x the rim, the
    # heap looked like gold paper); gold leaf is black where it mirrors the dark studio, bright where it mirrors a light
    w.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.0
    w.lightgroup = "fill"
    s.world = w
    w.cycles_visibility.camera = False                                   # black behind (the original's sky is ~5)


def area(name, loc, target, size, group):
    ld = bpy.data.lights.new(name, "AREA")
    ld.energy = 1.0
    ld.shape = "DISK"
    ld.size = size
    ob = bpy.data.objects.new(name, ld)
    bpy.context.collection.objects.link(ob)
    ob.location = loc
    ob.rotation_euler = (-(Vector(target) - Vector(loc)).normalized()).to_track_quat("Z", "Y").to_euler()
    ob.lightgroup = group
    return ob


def main():
    a = args()
    t0 = time.time()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    setup(a)
    s = bpy.context.scene
    k = a.frame
    rng = np.random.default_rng(SEED)                                    # the same heap every frame
    # base under the flakes (gaps): duller gold
    nx, ny = 500, 200
    xs = np.linspace(-0.075, 0.075, nx)
    ys = np.linspace(D - 0.17, D + 0.03, ny)
    X, Y = np.meshgrid(xs, ys)
    Vb = np.stack([X, Y, ground(X, Y)], -1).reshape(-1, 3)
    i = (np.arange(ny - 1)[:, None] * nx + np.arange(nx - 1)[None]).ravel()
    Fb = np.concatenate([np.stack([i, i + 1, i + nx + 1], 1), np.stack([i, i + nx + 1, i + nx], 1)])
    UVb = np.stack([(Vb[:, 0] + 0.075) / 0.15 * 40, (Vb[:, 1] - D) / 0.2 * 40], 1)
    add_mesh("base", Vb, Fb, UVb, gold_material("gold_base", 0.45))
    # heap flakes
    n = 30000
    x = rng.uniform(-0.07, 0.07, n)
    y = D - 0.16 * rng.power(0.6, n) + rng.uniform(-0.004, 0.012, n)   # denser towards the crest
    # r2: larger, flatter flakes lying with the slope [A]: big mirror faces that catch the backlight as continuous streaks
    size = np.exp(rng.uniform(np.log(0.0008), np.log(0.003), n))
    lift = rng.uniform(0.0, 0.0012, n)
    nrm = ground_normal(x, y)
    tilt_axis = np.cross(nrm, rng.normal(size=(n, 3)))
    tilt_axis /= np.linalg.norm(tilt_axis, axis=1, keepdims=True)
    tilt = np.abs(rng.normal(0, math.radians(9), n))
    glint = rng.random(n) < 0.08                                        # a few stand up: point glints from the small lights
    tilt[glint] = rng.uniform(math.radians(20), math.radians(55), glint.sum())
    # flutter: each flake's tilt walks a little per frame [A]
    walk = np.cumsum(rng.normal(0, math.radians(1.5), (8, n)), 0)
    ang = tilt + walk[k]
    Rm = rot_matrices(tilt_axis, ang)
    nn = np.einsum("nij,nj->ni", Rm, nrm)
    # beating direction roughly along the arc (x), +-25 deg: the anisotropic sheen streaks sideways like the original's
    t_, b_, nn = frame_from_normal(nn, np.zeros(n))
    ax = np.stack([np.ones(n), np.zeros(n), np.zeros(n)], 1)
    ax -= (ax * nn).sum(1, keepdims=True) * nn
    ax /= np.linalg.norm(ax, axis=1, keepdims=True)
    sp = rng.normal(0, math.radians(25), n)[:, None]
    t_ = np.cos(sp) * ax + np.sin(sp) * np.cross(nn, ax)
    b_ = np.cross(nn, t_)
    c = np.stack([x, y, ground(x, y) + lift], 1)
    V, F, UV = flakes(c, t_, b_, nn, size, rng.uniform(0.01, 0.05, n), rng)
    gold = gold_material("gold", 0.05)
    add_mesh("heap", V, F, UV, gold)
    # falling flakes: their own generator, positions are a function of the frame
    rf = np.random.default_rng(SEED + 1)
    m = 420
    x0 = rf.uniform(-0.075, 0.075, m)
    # r2: small specks off the focus plane (in front and behind) -> soft bright points, as in the original
    y0 = D + np.where(rf.random(m) < 0.5, rf.uniform(-0.09, -0.035, m), rf.uniform(0.02, 0.08, m))
    z0 = rf.uniform(crest_z(x0) + 0.001, H * 0.42, m) * y0 / D           # spread over the frame at their own depth, below the top 6% (top60 band)
    vz = rf.uniform(0.0006, 0.0022, m)                                  # m per frame (~2-8 px at 1080)
    sway = rf.uniform(0.0002, 0.0008, m)
    ph = rf.uniform(0, 2 * np.pi, m)
    zk = z0 - vz * k
    keep = zk > (crest_z(x0) + 0.0005) * y0 / D
    xk = x0 + sway * np.sin(ph + 0.9 * k)
    axis = rf.normal(size=(m, 3))
    axis /= np.linalg.norm(axis, axis=1, keepdims=True)
    spin = rf.uniform(math.radians(3), math.radians(40), m) * k + rf.uniform(0, 2 * np.pi, m)
    nf = np.einsum("nij,j->ni", rot_matrices(axis, spin), np.array([0, 0, 1.0]))
    tf, bf, nf = frame_from_normal(nf, rf.uniform(0, 2 * np.pi, m))
    sf = np.exp(rf.uniform(np.log(0.00012), np.log(0.0004), m))        # 2-8 px at 1080
    Vf, Ff, UVf = flakes(np.stack([xk, y0, zk], 1)[keep], tf[keep], bf[keep], nf[keep], sf[keep],
                         rf.uniform(0.1, 0.3, m)[keep], rf)
    if len(Vf):
        add_mesh("falling", Vf, Ff, UVf, gold)
    # lights [A]
    area("key", (-0.25, D - 0.35, 0.25), (0, D - 0.03, 0), 0.45, "key")              # r2: a big softbox
    # glints: two small hot lights with the key (front-top, either side), 0.06 across, ~170x its radiance
    for gx in (-0.12, 0.18):
        g = area("glint", (gx, D - 0.30, 0.30), (0, D - 0.03, 0), 0.06, "rim")
        g.data.energy = 6.0                                             # bright enough to clip; small hot ones (0.025) left fireflies OIDN smeared (+26 codes)
    # r2 rim: a flake tilted t toward the camera mirrors elevation 2t behind the heap, so the streaks come from a
    # large backlight high behind the crest (~35 deg), not from the front key
    area("rim", (0.0, D + 0.40, 0.28), (0, D - 0.03, 0), 0.6, "rim")
    # r2: a low, wide backlight (~9 deg) in group "fill": the near-flat flakes of the crest mirror it (the band around
    # the crest was 6 codes dark with the high rim alone)
    area("low", (0.0, D + 0.60, 0.10), (0, D, 0), 0.6, "fill")
    for ob in list(bpy.data.objects):                                   # scale the model up about the camera (origin)
        ob.location = ob.location * SC
        if ob.type == "MESH":
            ob.scale = (SC, SC, SC)
        elif ob.type == "LIGHT":
            ob.data.size *= SC
    for g in ("key", "rim", "fill"):
        s.view_layers[0].lightgroups.add(name=g)
    cd = bpy.data.cameras.new("cam")
    cd.lens, cd.sensor_width, cd.sensor_fit = FOCAL_MM, SENSOR_MM, "HORIZONTAL"
    cd.clip_start, cd.clip_end = 0.05, 100
    cd.dof.use_dof = True
    cd.dof.focus_distance = SC * D                              # r2: on the crest; the near face goes to bokeh (the original's bottom is a soft orange blanket)
    cd.dof.aperture_fstop = FNUM
    cam = bpy.data.objects.new("cam", cd)
    bpy.context.collection.objects.link(cam)
    cam.location = (0, 0, CAM_Z)
    cam.rotation_euler = (math.pi / 2, 0, 0)
    s.camera = cam
    t1 = time.time()
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
    groups = ["key", "rim", "fill"]
    want = {out: "Combined", stem + ".albedo.exr": "Denoising Albedo", stem + ".normal.exr": "Denoising Normal",
            **{f"{stem}.{g}.exr": f"Combined_{g}" for g in groups}}
    for path, name in want.items():
        kk = f"{vl}.{name}"
        if kk not in parts:
            raise SystemExit(f"{layers}: no pass {kk} (has {sorted(parts)})")
        arr = np.ascontiguousarray(parts[kk][:, :, :3], np.float32)
        spec = oiio.ImageSpec(arr.shape[1], arr.shape[0], 3, oiio.FLOAT)
        spec.attribute("compression", "zip")
        o = oiio.ImageOutput.create(path)
        if o is None or not o.open(path, spec) or not o.write_image(arr):
            raise SystemExit(f"{path}: could not write")
        o.close()
    os.remove(layers)
    info = {"frame": k, "device": a.device, "res": a.res, "spp": a.spp, "seed": a.seed, "groups": groups,
            "falling_in_frame": int(keep.sum()), "seconds_build": round(t1 - t0, 1), "seconds_render": round(t2 - t1, 1),
            "blender": bpy.app.version_string}
    json.dump(info, open(stem + ".json", "w"), indent=1)
    print("CYCLES_DONE", json.dumps(info))


main()
