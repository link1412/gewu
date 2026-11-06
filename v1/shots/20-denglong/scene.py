"""Shot 20 v1 (shader shot, DESIGN §3.8): a large red silk lantern seen close, against a warm lit wall. Runs inside
Blender (Cycles); the shot does not move (spec: moves false), so it is rendered once:

    blender -b --factory-startup --python-exit-code 1 -P scene.py -- --out $PWD/x.exr [--spp N --res WxH --device GPU|CPU]

Everything [A] (chosen by eye, not measured):
- the lantern: a sphere ~1 m across (a big festival lantern), its top silhouette is the spec arc (apex 0.476/0.482,
  radius 1.31 frame widths) seen from 1.2 m with a 100 mm lens; the camera looks just over its shoulder;
- silk: thin red silk on 36 bamboo ribs along the meridians. Translucent BSDF (the light that reaches the camera comes
  through the silk) plus a little diffuse; a thin glowing shell looks brighter and redder toward its limb (the path
  through the silk grows as 1/cos), modelled as the translucency growing with the Layer Weight facing term; a faint
  weave mottle. The ribs are opaque dark bamboo: dark lines against the glow;
- light: the wall behind is an emitter (group "sky"), brighter behind the lantern's top (a lamp washing the wall);
  a lamp inside the lantern (group "lamp"). Colours and levels are fitted afterwards (tools/shotkit.py: lightfit, codefit) [F];
- lens: 100 mm f/2, focused behind the lantern (1.6 m): its edge is soft, as in the original (sharpness cutoff
  ~0.09 cycles/px at 960).
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

FOCAL_MM, SENSOR_MM, FNUM = 100.0, 36.0, 2.0
FOCUS = 0.74                                              # just in front of the outline: it blurs ~100 px at 1080; the original's sky -> red
                                                          # transition takes ~160 px (rows 420-580)
DC = 1.2                                                  # camera -> lantern centre, m
R_IMG = 1.45 * SENSOR_MM / FOCAL_MM                       # image radius of the outline, in tan units (spec radius/width)
RL = R_IMG * DC / math.sqrt(1 + R_IMG ** 2)               # sphere radius whose outline subtends that
AZ = math.atan((0.476 - 0.5) * SENSOR_MM / FOCAL_MM)
EL_APEX = math.atan((0.5 - 0.457) * SENSOR_MM * 9 / 16 / FOCAL_MM)
EL_C = EL_APEX - math.asin(RL / DC)
# r1b: apex aimed 0.025 above the spec's 0.482 and the radius 1.31 -> 1.45 widths: the spec's arc sits at the dark
# core; the original's sky gives way (G at half) 40-90 px higher than ours did, flatter toward the sides [M]
CENTRE = Vector((DC * math.cos(EL_C) * math.sin(AZ), DC * math.cos(EL_C) * math.cos(AZ), DC * math.sin(EL_C)))
NRIB = 36
GROUPS = ["sky", "spot", "lamp"]


def args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--spp", type=int, default=256)
    ap.add_argument("--res", default="960x540")
    ap.add_argument("--device", default="GPU")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--frame", type=int, default=0)
    return ap.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])


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
    s.cycles.max_bounces = 12
    s.cycles.transmission_bounces = 12
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


def node(nt, kind, **inputs):
    n = nt.nodes.new(kind)
    for k, v in inputs.items():
        n.inputs[k].default_value = v
    return n


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


def silk_material():
    m = bpy.data.materials.new("silk")
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Object"], sep.inputs["Vector"])
    # ribs along the meridians: |sin(NRIB/2 * longitude)| near 0 on a rib
    lon = math_node(nt, "ARCTAN2", sep.outputs["Y"], sep.outputs["X"])
    s = math_node(nt, "ABSOLUTE", math_node(nt, "SINE", math_node(nt, "MULTIPLY", lon, NRIB / 2)))
    sm = nt.nodes.new("ShaderNodeMapRange")
    sm.interpolation_type = "SMOOTHSTEP"
    sm.inputs["From Min"].default_value = 0.08
    sm.inputs["From Max"].default_value = 0.30
    nt.links.new(s, sm.inputs["Value"])
    silk = sm.outputs["Result"]
    # limb: the translucency grows toward the outline (facing -> 1)
    lw = node(nt, "ShaderNodeLayerWeight", Blend=0.5)
    limb = math_node(nt, "MULTIPLY_ADD", None, None)
    ln = limb.node
    f = lw.outputs["Facing"]
    p2 = math_node(nt, "ADD", math_node(nt, "MULTIPLY", math_node(nt, "POWER", f, 2.0), 0.6 / 36.0),
                   math_node(nt, "POWER", f, 4.0))
    nt.links.new(p2, ln.inputs[0])
    # the original's halo (rows 480-540 at 1080: R stays ~170 while G falls 53 -> 23) is the blur of a bright red
    # limb; only facing > 0.8 lies within ~50 px of the outline, so the gain sits there: ~30x the body's [A]
    ln.inputs[1].default_value = 36.0                                   # gain 0.5 + 0.6 f^2 + 36 f^4 (r1b: 3x, the rim was dimmer than the body's top): the original's red band
    ln.inputs[2].default_value = 0.5                                    # (rows 540-620: R 110-118, G 20) sits under the outline
    # pleats and the silk's own streaks: noise stretched along the meridians (vertical in the frame), squared for
    # contrast: bright and dark dashes between the ribs, as the original's body [A]
    # in (longitude, latitude): stretched along the meridians wherever the surface is
    rxy = math_node(nt, "SQRT", math_node(nt, "ADD", math_node(nt, "MULTIPLY", sep.outputs["X"], sep.outputs["X"]),
                                           math_node(nt, "MULTIPLY", sep.outputs["Y"], sep.outputs["Y"])))
    lat = math_node(nt, "ARCTAN2", sep.outputs["Z"], rxy)
    cv = nt.nodes.new("ShaderNodeCombineXYZ")
    nt.links.new(math_node(nt, "MULTIPLY", lon, 60.0), cv.inputs["X"])
    nt.links.new(math_node(nt, "MULTIPLY", lat, 6.0), cv.inputs["Y"])
    mp = nt.nodes.new("ShaderNodeMapping")
    nt.links.new(cv.outputs[0], mp.inputs["Vector"])
    nz = node(nt, "ShaderNodeTexNoise", Scale=1.0, Detail=4.0)
    nt.links.new(mp.outputs["Vector"], nz.inputs["Vector"])
    q = math_node(nt, "POWER", nz.outputs["Fac"], 3.0)
    mot = math_node(nt, "MULTIPLY_ADD", q, 4.0)
    mot.node.inputs[2].default_value = 0.25
    gain = math_node(nt, "MULTIPLY", limb, mot)
    col = nt.nodes.new("ShaderNodeMix")
    col.data_type = "RGBA"
    col.blend_type = "MULTIPLY"
    col.inputs["Factor"].default_value = 1.0
    # r1b: 0.95 -> 0.15: the wall's orange through the silk dominated the body and read brown (bottom B -7.6); the
    # original's body is the lamp's crimson, so the glow carries it and the wall shows through only faintly [A]
    col.inputs["A"].default_value = (0.15, 0.15, 0.15, 1)             # the dye is in the Beer-Lambert term below
    # Beer-Lambert through the dyed sheet along the view: path L = 1/|N.V| (1 - Facing), so the body (short path)
    # passes some green and blue (the original's body: G/R ~0.25 linear) and the limb (long path) is pure red (~0.04)
    ndv = math_node(nt, "MAXIMUM", math_node(nt, "SUBTRACT", 1.0, f), 0.06)
    L = math_node(nt, "DIVIDE", 1.0, ndv)
    cg = nt.nodes.new("ShaderNodeCombineColor")
    # in sensor RGB (the chain's input): the original's dark body inverts to raw G/R ~0.88, B/R ~0.56 (the camera
    # matrix lifts saturation a lot), its halo to ~0.38 / 0.13 [M]; sigma (0.03, 0.10, 0.35) gives ~(1, .86, .58) at
    # the body (L ~1.7) and ~(1, .48, .07) at the limb (L ~8)
    # crimson: under the outline the original is (110-118, 20, 24) codes, B ~ G (sigma_B 0.08 read as plum)
    # r1b: (0.03, 0.09, 0.27): the glow basis with G = B pushed B up and G down as it was raised (bottom band +16 B, -3 G
    # at 0.01); the body (L ~2.4) needs G/R 0.88, B/R 0.56 and the limb (L ~16) G/R ~0.4 [M targets, A fit by hand]
    for c, sig in (("Red", 0.03), ("Green", 0.09), ("Blue", 0.27)):
        t = math_node(nt, "EXPONENT", math_node(nt, "MULTIPLY", L, -sig))
        nt.links.new(math_node(nt, "MULTIPLY", t, gain), cg.inputs[c])
    nt.links.new(cg.outputs[0], col.inputs["B"])
    tr = nt.nodes.new("ShaderNodeBsdfTranslucent")
    nt.links.new(col.outputs["Result"], tr.inputs["Color"])
    df = node(nt, "ShaderNodeBsdfDiffuse", Color=(0.30, 0.10, 0.10, 1))   # dyed silk's surface: a less saturated sheen
    sh = nt.nodes.new("ShaderNodeMixShader")
    sh.inputs["Fac"].default_value = 0.85
    nt.links.new(df.outputs[0], sh.inputs[1])
    nt.links.new(tr.outputs[0], sh.inputs[2])
    # the glow (group "lamp", the lantern object's group): the lit silk as an emitter, same limb gain, streaks and
    # Beer-Lambert colour as the transmitted term. A point lamp inside was fitted to ~0 (its light reaches the camera
    # only through the diffuse/translucent lobes, spread flat); an emitting shell puts the glow where the original has
    # it: the red limb and the warm dashes [A]
    em = nt.nodes.new("ShaderNodeEmission")
    nt.links.new(cg.outputs[0], em.inputs["Color"])
    em.inputs["Strength"].default_value = 1.0
    add = nt.nodes.new("ShaderNodeAddShader")
    nt.links.new(sh.outputs[0], add.inputs[0])
    nt.links.new(em.outputs[0], add.inputs[1])
    sh = add
    rib = node(nt, "ShaderNodeBsdfDiffuse", Color=(0.04, 0.025, 0.015, 1))   # bamboo, opaque
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(silk, mix.inputs["Fac"])
    nt.links.new(rib.outputs[0], mix.inputs[1])
    nt.links.new(sh.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs["Surface"])
    return m


def wall_material():
    """Emitter, the wall's lower part (a vertical ramp) [A]."""
    m = bpy.data.materials.new("wall")
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Object"], sep.inputs["Vector"])
    d2 = math_node(nt, "ADD", math_node(nt, "MULTIPLY", sep.outputs["X"], sep.outputs["X"]),
                   math_node(nt, "MULTIPLY", sep.outputs["Y"], sep.outputs["Y"]))
    # r1b: a ramp, 0 at the frame's top edge to 1 at the outline and below (the wall's lower part, its own colour,
    # fitted): the original's sky is bluer toward the lantern (B 31 at the top, 36-37 above the halo) [M]; one wall
    # colour left the top band B +4 and the middle B -6
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = 0.42
    mr.inputs["From Max"].default_value = 0.0
    nt.links.new(sep.outputs["Y"], mr.inputs["Value"])
    st = mr.outputs["Result"]
    em = node(nt, "ShaderNodeEmission", Color=(1, 1, 1, 1))
    nt.links.new(st, em.inputs["Strength"])
    nt.links.new(em.outputs[0], out.inputs["Surface"])
    return m


def spot_material():
    """The wall's hotspot behind the lantern (group "spot", its own colour): emission exp(-(d/1.6 m)^2) (a narrow 0.6 m one brightened the middle band's sky: +10 codes) over a clear
    plane just in front of the wall [A]."""
    m = bpy.data.materials.new("spot")
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Object"], sep.inputs["Vector"])
    d2 = math_node(nt, "ADD", math_node(nt, "MULTIPLY", sep.outputs["X"], sep.outputs["X"]),
                   math_node(nt, "MULTIPLY", sep.outputs["Y"], sep.outputs["Y"]))
    g = math_node(nt, "EXPONENT", math_node(nt, "MULTIPLY", d2, -1 / 1.6 ** 2))
    em = node(nt, "ShaderNodeEmission", Color=(1, 1, 1, 1))
    nt.links.new(g, em.inputs["Strength"])
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    add = nt.nodes.new("ShaderNodeAddShader")
    nt.links.new(tr.outputs[0], add.inputs[0])
    nt.links.new(em.outputs[0], add.inputs[1])
    nt.links.new(add.outputs[0], out.inputs["Surface"])
    return m


def main():
    a = args()
    t0 = time.time()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    setup(a)
    s = bpy.context.scene
    w = s.world
    w.lightgroup = "sky"                                                 # black, but a group must exist for it
    bpy.ops.mesh.primitive_uv_sphere_add(segments=256, ring_count=128, radius=RL, location=CENTRE)
    lan = bpy.context.active_object
    lan.name = "lantern"
    bpy.ops.object.shade_smooth()
    lan.data.materials.append(silk_material())
    lan.lightgroup = "lamp"                                              # the silk's glow (emission)
    # wall 4 m away, facing the camera, centred behind the lantern's top
    bpy.ops.mesh.primitive_plane_add(size=1, location=(CENTRE.x, 4.0, (CENTRE.z + RL) * 4.0 / DC))
    wall = bpy.context.active_object
    wall.name = "wall"
    wall.scale = (8, 6, 1)
    wall.rotation_euler = (math.pi / 2, 0, 0)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)   # object coords in metres
    wall.data.materials.append(wall_material())
    wall.lightgroup = "sky"
    bpy.ops.mesh.primitive_plane_add(size=1, location=(CENTRE.x, 3.95, (CENTRE.z + RL) * 3.95 / DC))
    sp = bpy.context.active_object
    sp.name = "spot"
    sp.scale = (8, 6, 1)
    sp.rotation_euler = (math.pi / 2, 0, 0)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    sp.data.materials.append(spot_material())
    sp.lightgroup = "spot"
    # the room in front (behind the camera): a soft light on the silk's face, its colour fitted (group "front") [A]:
    # the original's body is less saturated (G/R ~0.25 linear) than its limb (~0.04), so some light is reflected
    for g in GROUPS:
        s.view_layers[0].lightgroups.add(name=g)
    cd = bpy.data.cameras.new("cam")
    cd.lens, cd.sensor_width, cd.sensor_fit = FOCAL_MM, SENSOR_MM, "HORIZONTAL"
    cd.clip_start, cd.clip_end = 0.05, 100
    cd.dof.use_dof = True
    cd.dof.focus_distance = FOCUS
    cd.dof.aperture_fstop = FNUM
    cam = bpy.data.objects.new("cam", cd)
    bpy.context.collection.objects.link(cam)
    cam.location = (0, 0, 0)
    cam.rotation_euler = (math.pi / 2, 0, 0)
    s.camera = cam
    k = 0
    keep = np.zeros(0)
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
    groups = GROUPS
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
            "seconds_build": round(t1 - t0, 1), "seconds_render": round(t2 - t1, 1),
            "blender": bpy.app.version_string}
    json.dump(info, open(stem + ".json", "w"), indent=1)
    print("CYCLES_DONE", json.dumps(info))


main()
