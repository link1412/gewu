"""Blender-side helpers for shader shots (plan A, S10). tools/shotkit.py copies this file next to each scene.py.

A kit scene runs inside Blender:

    blender -b --factory-startup --python-exit-code 1 -P scene.py -- --out $PWD/f00/x.exr --res 960x540 --spp 256 \
        --seed 0 --device GPU [--frame K] [the scene's own args]

and writes OUT (combined), OUT.<group>.exr for every light group, OUT.albedo.exr, OUT.normal.exr and OUT.json.
With this module a scene is only its subject:

    import kit_bpy as K
    a = K.args(lambda ap: ap.add_argument("--tex"))     # also reads shot.spec.json (the shot's spec/shots.json entry)
    K.setup(a)                                            # Cycles, device, resolution, samples, filter, Standard view
    K.world(group="sky", strength=0.5)
    m, b, nt = K.principled("glaze", (0.6, 0.7, 0.8), 0.1)
    K.mesh("dish", V, F, m, uv=UV, smooth=True)
    K.area("key", (0.3, -0.2, 0.5), (0, 0, 0), 0.4, "key")
    K.camera(loc, target, focal_mm=100, fnum=8)
    K.render(a)

Light groups: every light, every emitting object (mesh(..., group=)) and the world carry `.lightgroup`; render()
registers the groups it finds and writes one pass per group. Lights are 1 W / emitters strength 1 and white unless
the scene says otherwise: each group's colour and level come from the fit afterwards (tools/shotkit.py) [F].
Blender is right-handed, z up. A camera with no target looks down -z with the image top along +y.
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

HERE = os.path.dirname(os.path.abspath(__file__))


# --- arguments and render settings --------------------------------------------------------------------------
def args(extra=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--res", default="960x540")
    ap.add_argument("--spp", type=int, default=256)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--device", default="GPU")
    ap.add_argument("--frame", type=int, default=0, help="0-based frame of the shot (per-frame shots)")
    if extra:
        extra(ap)
    a = ap.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    a.W, a.H = map(int, a.res.split("x"))
    p = os.path.join(HERE, "shot.spec.json")
    a.shot = json.load(open(p)) if os.path.exists(p) else None
    a.t0 = time.time()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    return a


def setup(a, bounces=8, transmission=None, volume=0, filter_width=1.5):
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
    s.render.resolution_x, s.render.resolution_y = a.W, a.H
    s.render.resolution_percentage = 100
    s.cycles.samples = a.spp
    s.cycles.use_adaptive_sampling = False
    s.cycles.use_denoising = False
    s.cycles.max_bounces = bounces
    if transmission is not None:
        s.cycles.transmission_bounces = transmission
    s.cycles.volume_bounces = volume
    s.cycles.seed = a.seed + 7919 * a.frame
    s.cycles.pixel_filter_type = "GAUSSIAN"
    s.cycles.filter_width = filter_width
    s.cycles.sample_clamp_direct = s.cycles.sample_clamp_indirect = 0.0
    s.view_settings.view_transform = "Standard"
    return s


def world(color=(1, 1, 1), strength=0.0, group="sky", camera_visible=True):
    """A uniform world. strength 0 leaves the group black (a black studio) but keeps the pass."""
    w = bpy.data.worlds.new(group or "world")
    w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (*color, 1)
    bg.inputs["Strength"].default_value = strength
    if group:
        w.lightgroup = group
    w.cycles_visibility.camera = camera_visible
    bpy.context.scene.world = w
    return w


# --- geometry -----------------------------------------------------------------------------------------------
def mesh(name, V, F, mat=None, uv=None, smooth=False, group=None, attrs=None):
    """V (n,3), F list of index tuples (or an (m,k) array), uv (n,2) per vertex, attrs {name: (n,) float} per vertex."""
    V = np.asarray(V, np.float64)
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in V], [], [tuple(int(i) for i in f) for f in F])
    me.update()
    if uv is not None:
        uv = np.asarray(uv, np.float32)
        lay = me.uv_layers.new()
        vi = np.empty(len(me.loops), np.int32)
        me.loops.foreach_get("vertex_index", vi)
        lay.data.foreach_set("uv", uv[vi].ravel())
    for k, v in (attrs or {}).items():
        at = me.attributes.new(k, "FLOAT", "POINT")
        at.data.foreach_set("value", np.asarray(v, np.float32))
    me.polygons.foreach_set("use_smooth", [smooth] * len(me.polygons))
    if mat is not None:
        me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    if group:
        ob.lightgroup = group
    return ob


def grid(nx, ny, x0, x1, y0, y1, z=None):
    """A regular grid of quads over [x0,x1]x[y0,y1]: V (with z(x, y) or 0), F, UV in [0,1]."""
    xs, ys = np.linspace(x0, x1, nx + 1), np.linspace(y0, y1, ny + 1)
    X, Y = np.meshgrid(xs, ys)
    Z = z(X, Y) if z else np.zeros_like(X)
    V = np.stack([X, Y, Z], -1).reshape(-1, 3)
    UV = np.stack([(X - x0) / (x1 - x0), (Y - y0) / (y1 - y0)], -1).reshape(-1, 2)
    i = np.arange((nx + 1) * (ny + 1)).reshape(ny + 1, nx + 1)
    F = np.stack([i[:-1, :-1], i[:-1, 1:], i[1:, 1:], i[1:, :-1]], -1).reshape(-1, 4)
    return V, F, UV


def lathe(r, z, n=256):
    """A surface of revolution about z from a profile (r[i], z[i]): V, F, UV (u around, v along the profile)."""
    r, z = np.asarray(r, float), np.asarray(z, float)
    t = np.linspace(0, 2 * np.pi, n, endpoint=False)
    V = np.stack([r[:, None] * np.cos(t), r[:, None] * np.sin(t), np.broadcast_to(z[:, None], (len(r), n))], -1).reshape(-1, 3)
    m = len(r)
    i = np.arange(m * n).reshape(m, n)
    j = np.roll(i, -1, 1)
    F = np.stack([i[:-1], j[:-1], j[1:], i[1:]], -1).reshape(-1, 4)
    s = np.r_[0, np.cumsum(np.hypot(np.diff(r), np.diff(z)))]
    UV = np.stack([np.broadcast_to(t / (2 * np.pi), (m, n)), np.broadcast_to((s / max(s[-1], 1e-12))[:, None], (m, n))], -1).reshape(-1, 2)
    return V, F, UV


# --- materials ----------------------------------------------------------------------------------------------
def node(nt, kind, **inputs):
    n = nt.nodes.new(kind)
    for k, v in inputs.items():
        n.inputs[k].default_value = v
    return n


def link(nt, out, inp):
    nt.links.new(out, inp)


def math_node(nt, op, a=None, b=None):
    n = nt.nodes.new("ShaderNodeMath")
    n.operation = op
    for i, v in enumerate((a, b)):
        if v is None:
            continue
        if isinstance(v, (int, float)):
            n.inputs[i].default_value = v
        else:
            nt.links.new(v, n.inputs[i])
    return n.outputs[0]


def principled(name, color, rough, metallic=0.0, **inputs):
    """(material, Principled BSDF node, node tree). inputs: other Principled inputs by name, e.g. Coat_Weight=0.5
    (underscores for spaces)."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metallic
    for k, v in inputs.items():
        b.inputs[k.replace("_", " ")].default_value = v
    return m, b, nt


def image(nt, path, colorspace="Non-Color", interpolation="Cubic", uv=None):
    """An image texture node (path relative to the scene's directory); returns the node."""
    t = nt.nodes.new("ShaderNodeTexImage")
    t.image = bpy.data.images.load(path if os.path.isabs(path) else os.path.join(HERE, path))
    t.image.colorspace_settings.name = colorspace
    t.interpolation = interpolation
    if uv is not None:
        nt.links.new(uv, t.inputs["Vector"])
    return t


def emission(name, color=(1, 1, 1), strength=1.0, transparent=False):
    """An emitting material (a sky plane, a glowing panel). transparent: emission added on a transparent surface, so
    stacked planes can each be one basis of a sky gradient (skill-notes 150)."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    e = node(nt, "ShaderNodeEmission", Color=(*color, 1), Strength=strength)
    if transparent:
        add = nt.nodes.new("ShaderNodeAddShader")
        tr = nt.nodes.new("ShaderNodeBsdfTransparent")
        link(nt, tr.outputs[0], add.inputs[0])
        link(nt, e.outputs[0], add.inputs[1])
        link(nt, add.outputs[0], out.inputs["Surface"])
    else:
        link(nt, e.outputs[0], out.inputs["Surface"])
    return m, e, nt


# --- lights and camera --------------------------------------------------------------------------------------
def _aim(ob, loc, target):
    ob.location = loc
    ob.rotation_euler = (Vector(loc) - Vector(target)).normalized().to_track_quat("Z", "Y").to_euler()


def area(name, loc, target, size, group, shape="DISK", size_y=None, energy=1.0, spread=None):
    ld = bpy.data.lights.new(name, "AREA")
    ld.energy = energy
    ld.shape = shape
    ld.size = size
    if size_y is not None:
        ld.size_y = size_y
    if spread is not None:
        ld.spread = math.radians(spread)
    ob = bpy.data.objects.new(name, ld)
    bpy.context.collection.objects.link(ob)
    _aim(ob, loc, target)
    ob.lightgroup = group
    return ob


def point(name, loc, group, radius=0.0, energy=1.0):
    ld = bpy.data.lights.new(name, "POINT")
    ld.energy = energy
    ld.shadow_soft_size = radius
    ob = bpy.data.objects.new(name, ld)
    bpy.context.collection.objects.link(ob)
    ob.location = loc
    ob.lightgroup = group
    return ob


def sun(name, direction, group, angle_deg=0.5, strength=1.0):
    """direction: where the light travels TO (e.g. (0, 1, -0.2) from behind the camera)."""
    ld = bpy.data.lights.new(name, "SUN")
    ld.energy = strength
    ld.angle = math.radians(angle_deg)
    ob = bpy.data.objects.new(name, ld)
    bpy.context.collection.objects.link(ob)
    ob.rotation_euler = (-Vector(direction)).normalized().to_track_quat("Z", "Y").to_euler()
    ob.lightgroup = group
    return ob


def camera(loc, target=None, focal_mm=100.0, fnum=8.0, focus=None, sensor_mm=36.0, roll_deg=0.0):
    """Camera at loc looking at target (or straight down -z, image top +y). focus: distance in m (default: to target)."""
    cd = bpy.data.cameras.new("cam")
    cd.lens, cd.sensor_width, cd.sensor_fit = focal_mm, sensor_mm, "HORIZONTAL"
    d = (Vector(target) - Vector(loc)).length if target is not None else None
    cd.clip_start, cd.clip_end = 1e-3, 1e3
    cd.dof.use_dof = fnum is not None
    if fnum is not None:
        cd.dof.focus_distance = focus if focus is not None else (d or 1.0)
        cd.dof.aperture_fstop = fnum
    ob = bpy.data.objects.new("cam", cd)
    bpy.context.collection.objects.link(ob)
    ob.location = loc
    if target is not None:
        q = (Vector(loc) - Vector(target)).normalized().to_track_quat("Z", "Y")
        ob.rotation_euler = q.to_euler()
    if roll_deg:
        ob.rotation_euler.rotate_axis("Z", math.radians(roll_deg))
    bpy.context.scene.camera = ob
    return ob


def arc(a):
    """The shot's arc from spec/shots.json [M]: apex (x, y) as fractions of width and height from the top-left,
    sagitta (of the width), radius (of the width). None for a hand-measured arc."""
    t = (a.shot or {}).get("arc")
    if not t:
        return None
    return {"apex": (t["apex_x"], t["apex_y"]), "sagitta": t["sagitta_of_width"], "radius": t["radius_over_width"]}


def frame_on_circle(a, R, focal_mm=100.0, sensor_mm=36.0):
    """Straight-down camera for a circular rim of radius R (m) at z=0 centred at the origin, whose far edge (+y) is
    the shot's arc: the frame width is R / radius_over_width, the apex lands at the spec's (x, y). Returns
    (camera location, frame width at z=0). For tilted views use tools/../optics/framing.py's solve offline."""
    t = arc(a)
    if t is None:
        raise SystemExit("frame_on_circle: the shot's arc is hand-measured; place the camera yourself")
    W = R / t["radius"]
    dist = focal_mm / sensor_mm * W
    x = -(t["apex"][0] - 0.5) * W
    y = R - (0.5 - t["apex"][1]) * W * a.H / a.W
    return (x, y, dist), W


# --- render -------------------------------------------------------------------------------------------------
def render(a):
    s = bpy.context.scene
    groups = sorted({o.lightgroup for o in bpy.data.objects if getattr(o, "lightgroup", "")} |
                    ({s.world.lightgroup} if s.world is not None and s.world.lightgroup else set()))
    if not groups:
        raise SystemExit("no light groups: give every light / emitter / the world a .lightgroup")
    vl = s.view_layers[0]
    for g in groups:
        if g not in vl.lightgroups:
            vl.lightgroups.add(name=g)
    vl.cycles.denoising_store_passes = True
    st = s.render.image_settings
    st.media_type = "MULTI_LAYER_IMAGE"
    st.file_format = "OPEN_EXR_MULTILAYER"
    st.color_depth = "32"
    st.exr_codec = "ZIP"
    out = os.path.abspath(a.out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    stem = os.path.splitext(out)[0]
    layers = stem + ".layers.exr"
    s.render.filepath = layers
    t1 = time.time()
    bpy.ops.render.render(write_still=True)
    t2 = time.time()
    import OpenImageIO as oiio
    inp = oiio.ImageInput.open(layers)
    parts, i = {}, 0
    while inp.seek_subimage(i, 0):
        sp = inp.spec()
        parts[sp.getattribute("name")] = inp.read_image(i, 0, 0, sp.nchannels, oiio.FLOAT)
        i += 1
    inp.close()
    want = {out: "Combined", stem + ".albedo.exr": "Denoising Albedo", stem + ".normal.exr": "Denoising Normal",
            **{f"{stem}.{g}.exr": f"Combined_{g}" for g in groups}}
    for path, name in want.items():
        k = f"{vl.name}.{name}"
        if k not in parts:
            raise SystemExit(f"{layers}: no pass {k} (has {sorted(parts)})")
        arr = np.ascontiguousarray(parts[k][:, :, :3], np.float32)
        if not np.isfinite(arr).all():
            raise SystemExit(f"{path}: NaN or inf in the pass")
        spec = oiio.ImageSpec(arr.shape[1], arr.shape[0], 3, oiio.FLOAT)
        spec.attribute("compression", "zip")
        o = oiio.ImageOutput.create(path)
        if o is None or not o.open(path, spec) or not o.write_image(arr):
            raise SystemExit(f"{path}: could not write")
        o.close()
    os.remove(layers)
    info = {"device": a.device, "res": a.res, "spp": a.spp, "seed": a.seed, "frame": a.frame, "groups": groups,
            "seconds_build": round(t1 - a.t0, 1), "seconds_render": round(t2 - t1, 1), "blender": bpy.app.version_string}
    json.dump(info, open(stem + ".json", "w"), indent=1)
    print("CYCLES_DONE", json.dumps(info))
