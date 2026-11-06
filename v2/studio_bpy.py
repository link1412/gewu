"""The studio: runs inside Blender. One scene.json in, one linear float image (.npy) out.

    blender -b --factory-startup --python-exit-code 1 -P v2/studio_bpy.py -- scene.json

Units: 1 Blender unit = 1 cm. Everything the picture needs is in scene.json; see kit.shoot().
"""

import json
import sys
import time

import bpy
import numpy as np


def grid_mesh(name, P, attrs, mat):
    """A pixel-dense quad grid from (rows, cols, 3) positions; per-vertex attributes, no texture files."""
    ny, nx = P.shape[:2]
    nv, nf = nx * ny, (nx - 1) * (ny - 1)
    idx = np.arange(nv, dtype=np.int32).reshape(ny, nx)
    loops = np.stack([idx[:-1, :-1], idx[1:, :-1], idx[1:, 1:], idx[:-1, 1:]], -1).ravel()
    me = bpy.data.meshes.new(name)
    me.vertices.add(nv)
    me.vertices.foreach_set("co", P.reshape(-1).astype(np.float32))
    me.loops.add(nf * 4)
    me.loops.foreach_set("vertex_index", loops)
    me.polygons.add(nf)
    me.polygons.foreach_set("loop_start", np.arange(nf, dtype=np.int32) * 4)
    me.update(calc_edges=False)
    me.polygons.foreach_set("use_smooth", np.ones(nf, dtype=bool))
    for k, v in attrs.items():
        if v.ndim == 3:
            at = me.attributes.new(k, "FLOAT_COLOR", "POINT")
            rgba = np.concatenate([v, np.ones(v.shape[:2] + (1,), v.dtype)], -1)
            at.data.foreach_set("color", rgba.reshape(-1).astype(np.float32))
        else:
            at = me.attributes.new(k, "FLOAT", "POINT")
            at.data.foreach_set("value", v.reshape(-1).astype(np.float32))
    me.update()
    me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    return ob


def soup_mesh(name, V, F, attrs, mat, smooth=False):
    """Closed solids as triangles with flat facets and hard edges (crystals). Per-vertex attributes: 1D float, (N, 3) vector. smooth: shared-vertex meshes of millions of triangles (surface nets), smooth shaded, no edge table."""
    nv, nf = len(V), len(F)
    me = bpy.data.meshes.new(name)
    me.vertices.add(nv)
    me.vertices.foreach_set("co", V.reshape(-1).astype(np.float32))
    me.loops.add(nf * 3)
    me.loops.foreach_set("vertex_index", F.reshape(-1).astype(np.int32))
    me.polygons.add(nf)
    me.polygons.foreach_set("loop_start", np.arange(nf, dtype=np.int32) * 3)
    me.update(calc_edges=not smooth)
    me.polygons.foreach_set("use_smooth", np.full(nf, smooth, dtype=bool))
    for k, v in attrs.items():
        if v.ndim == 2:
            me.attributes.new(k, "FLOAT_VECTOR", "POINT").data.foreach_set("vector", v.reshape(-1).astype(np.float32))
        else:
            me.attributes.new(k, "FLOAT", "POINT").data.foreach_set("value", v.astype(np.float32))
    me.update()
    me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    return ob


def attr_material(name, spec):
    """Principled driven by per-vertex attributes. spec maps Principled inputs to attribute names or constants."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    for inp, val in spec.items():
        if isinstance(val, str):
            a = nt.nodes.new("ShaderNodeAttribute")
            a.attribute_name = val
            is_color = inp in ("Base Color", "Emission Color", "Subsurface Radius")
            nt.links.new(a.outputs["Color" if is_color else "Fac"], b.inputs[inp])
        elif isinstance(val, list):
            b.inputs[inp].default_value = (*val, 1)[: len(b.inputs[inp].default_value)]
        else:
            b.inputs[inp].default_value = val
    return m


def backdrop(cfg):
    """A big plane far out of focus: the 'sky' of the picture, lit by the same lights."""
    me = bpy.data.meshes.new("backdrop")
    c, s = np.array(cfg["center"], float), float(cfg["size"])
    u = np.array(cfg.get("u", [1, 0, 0]), float) * s
    v = np.array(cfg.get("v", [0, 1, 0]), float) * s
    me.from_pydata([tuple(c - u - v), tuple(c + u - v), tuple(c + u + v), tuple(c - u + v)], [], [(0, 1, 2, 3)])
    m = bpy.data.materials.new("backdrop")
    m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (*cfg["rgb"], 1)
    b.inputs["Roughness"].default_value = cfg.get("rough", 0.9)
    b.inputs["Specular IOR Level"].default_value = cfg.get("spec", 0.0)  # a matte cloth, or it mirrors the lights
    me.materials.append(m)
    ob = bpy.data.objects.new("backdrop", me)
    bpy.context.collection.objects.link(ob)


def aim(ob, loc, target, roll_deg=0.0):
    from mathutils import Vector

    ob.location = loc
    d = Vector(target) - Vector(loc)
    q = d.to_track_quat("-Z", "Y")
    ob.rotation_mode = "QUATERNION"
    ob.rotation_quaternion = q
    if roll_deg:
        from mathutils import Quaternion

        ob.rotation_quaternion = q @ Quaternion((0, 0, 1), np.radians(roll_deg))


def gradient_light(cfg):
    """A scrim: an emissive plane whose radiance falls off as a Gaussian, so its reflection has no edge."""
    sx, sy = cfg["size"]
    me = bpy.data.meshes.new(cfg["name"])
    me.from_pydata([(-sx / 2, -sy / 2, 0), (sx / 2, -sy / 2, 0), (sx / 2, sy / 2, 0), (-sx / 2, sy / 2, 0)], [], [(0, 1, 2, 3)])
    m = bpy.data.materials.new(cfg["name"])
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Object"], sep.inputs[0])

    def m1(op, a, b=None):
        n = nt.nodes.new("ShaderNodeMath")
        n.operation = op
        for i, x in enumerate((a, b)):
            if x is None:
                continue
            if isinstance(x, (int, float)):
                n.inputs[i].default_value = x
            else:
                nt.links.new(x, n.inputs[i])
        return n.outputs[0]

    gx = m1("POWER", m1("DIVIDE", sep.outputs["X"], cfg["sigma"][0]), 2.0)
    gy = m1("POWER", m1("DIVIDE", sep.outputs["Y"], cfg["sigma"][1]), 2.0)
    g = m1("EXPONENT", m1("MULTIPLY", m1("ADD", gx, gy), -1.0))
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*cfg.get("rgb", [1, 1, 1]), 1)
    nt.links.new(m1("MULTIPLY", g, cfg["L"]), em.inputs["Strength"])
    nt.links.new(em.outputs[0], out.inputs["Surface"])
    me.materials.append(m)
    ob = bpy.data.objects.new(cfg["name"], me)
    bpy.context.collection.objects.link(ob)
    aim(ob, cfg["loc"], cfg.get("target", [0, 0, 0]))
    ob.visible_camera = False
    if cfg.get("hide_in_gloss"):
        ob.visible_glossy = False
    if cfg.get("hide_in_diffuse"):
        ob.visible_diffuse = False


def light(cfg):
    kind = cfg.get("type", "area")
    if kind == "gradient":
        return gradient_light(cfg)
    if kind == "sun":  # strength: irradiance on a surface facing it; angle: the disc's full width in degrees. It stays at infinity, in the direction loc -> target
        li = bpy.data.lights.new(cfg["name"], "SUN")
        li.angle = np.radians(cfg.get("angle", 0.53))
        li.energy = cfg["strength"]
        li.color = cfg.get("rgb", [1, 1, 1])
        ob = bpy.data.objects.new(cfg["name"], li)
        bpy.context.collection.objects.link(ob)
        aim(ob, cfg["loc"], cfg.get("target", [0, 0, 0]))
        return
    if kind == "area":
        li = bpy.data.lights.new(cfg["name"], "AREA")
        li.shape = "RECTANGLE"
        li.size, li.size_y = cfg["size"][0], cfg["size"][1]
        if "spread" in cfg:
            li.spread = np.radians(cfg["spread"])
    else:
        li = bpy.data.lights.new(cfg["name"], "POINT")
        li.shadow_soft_size = cfg.get("radius", 0.1)
    li.energy = cfg["watts"]
    li.color = cfg.get("rgb", [1, 1, 1])
    ob = bpy.data.objects.new(cfg["name"], li)
    bpy.context.collection.objects.link(ob)
    aim(ob, cfg["loc"], cfg.get("target", [0, 0, 0]))
    ob.visible_camera = False
    if cfg.get("hide_in_gloss"):
        ob.visible_glossy = False
    if cfg.get("hide_in_transmission"):
        ob.visible_transmission = False


def volume(vc):
    """cfg["volumes"] item, {"name", "vdb", "shader_py", "params", "clipping"}: a heterogeneous medium read from an OpenVDB file, in world space (1 unit = 1 cm). Cycles wraps the active voxels in a hull, so the medium does not touch the surfaces around it."""
    v = bpy.data.volumes.new(vc["name"])
    v.filepath = vc["vdb"]
    v.render.clipping = vc.get("clipping", 0.0)
    v.render.precision = vc.get("precision", "FULL")
    ns = {}
    exec(compile(open(vc["shader_py"]).read(), vc["shader_py"], "exec"), ns)
    v.materials.append(ns["make"](vc["name"], vc.get("params", {})))
    ob = bpy.data.objects.new(vc["name"], v)
    bpy.context.collection.objects.link(ob)
    return ob


def _pose_camera(co, cam, f):
    aim(co, f["loc"], f["target"], f.get("roll", 0.0))
    cam.lens = f["lens_mm"]
    if "focus_distance" in f:
        cam.dof.focus_distance = f["focus_distance"]


def _deform_setup(dc):
    """cfg["deform"] = {"npy", "extent": [x0, x1, y0, y1], "mesh"}: a stack of displacements (frames, ny, nx, 3), its nodes evenly spaced over the extent in the xy plane, row 0 at y0.
    Each frame the named mesh's rest vertices get the bilinearly sampled displacement. The mesh changes, its BVH is rebuilt for that frame, and the upload is once. No deformation motion blur: the mesh has no keyframes.
    cfg["deform"] = {"npy", "vertex": [mesh names]}: the stack holds every vertex of these meshes, one after the other, (frames, verts, 3), in world space."""
    if dc.get("vertex"):
        obs = [bpy.data.objects[n] for n in dc["vertex"]]
        counts = [len(o.data.vertices) for o in obs]
        stack = np.load(dc["npy"], mmap_mode="r")
        if stack.shape[1] != sum(counts):
            raise SystemExit(f"deform: {stack.shape[1]} vertices in the stack, {sum(counts)} in the meshes")
        for o in obs:
            o.cycles.use_deform_motion = False

        def pose_vertices(k):
            a = 0
            for o, c in zip(obs, counts):
                o.data.vertices.foreach_set("co", np.asarray(stack[k, a : a + c], np.float32).reshape(-1))
                o.data.update()
                a += c

        return pose_vertices
    ob = bpy.data.objects[dc["mesh"]]
    ob.cycles.use_deform_motion = False
    me = ob.data
    n = len(me.vertices)
    rest = np.empty(n * 3, np.float32)
    me.vertices.foreach_get("co", rest)
    rest = rest.reshape(-1, 3)
    stack = np.load(dc["npy"], mmap_mode="r")
    _, ny, nx, _ = stack.shape
    x0, x1, y0, y1 = dc["extent"]
    fx = np.clip((rest[:, 0] - x0) / (x1 - x0) * (nx - 1), 0, nx - 1 - 1e-3)
    fy = np.clip((rest[:, 1] - y0) / (y1 - y0) * (ny - 1), 0, ny - 1 - 1e-3)
    ix, iy = fx.astype(np.int32), fy.astype(np.int32)
    wx, wy = (fx - ix)[:, None], (fy - iy)[:, None]

    def pose(k):
        d = np.asarray(stack[k], np.float32)
        p = rest + (d[iy, ix] * (1 - wx) + d[iy, ix + 1] * wx) * (1 - wy) + (d[iy + 1, ix] * (1 - wx) + d[iy + 1, ix + 1] * wx) * wy
        me.vertices.foreach_set("co", p.reshape(-1))
        me.update()

    return pose


def take(cfg, s, co, cam, t0):
    """A moving take: one scene, many frames. Only the camera, the lights and whole objects change, so the BVH stays (persistent data), and the
    motion blur costs almost nothing. Each frame: <out>_NNN.npy, float16 scene-linear, skipped if it is already there (a GPU hang resumes).
    cfg["spin"] turns some meshes about an axis, with real motion blur; the mesh's vertices are in world space, so it turns about pt by rotating and moving the object."""
    import os

    from mathutils import Quaternion, Vector

    frames = cfg["frames"]
    s.render.use_persistent_data = True
    s.frame_start, s.frame_end = 0, len(frames)
    shutter = cfg.get("shutter", 0.5)
    if shutter:
        s.render.use_motion_blur = True
        s.render.motion_blur_shutter = shutter
        s.render.motion_blur_position = "CENTER"
        co.rotation_mode = "QUATERNION"
        for i, f in enumerate(frames):
            _pose_camera(co, cam, f)
            co.keyframe_insert("location", frame=i)
            co.keyframe_insert("rotation_quaternion", frame=i)
    spin = cfg.get("spin")
    spun = []
    if spin:
        names = spin["meshes"]
        meshes = [o for o in bpy.data.objects if o.type == "MESH"]
        spun = [o for o in meshes if o.name not in names["except"]] if isinstance(names, dict) else [bpy.data.objects[n] for n in names]
        if not spun:
            raise SystemExit("spin: no meshes")
        pt, axis = Vector(spin["pt"]), Vector(spin["axis"]).normalized()

        def spin_pose(deg):
            q = Quaternion(axis, np.radians(deg))
            for o in spun:
                o.rotation_mode = "QUATERNION"
                o.rotation_quaternion = q
                o.location = pt - q @ pt

        if shutter:
            for i, f in enumerate(frames):
                spin_pose(f["spin_deg"])
                for o in spun:
                    o.keyframe_insert("location", frame=i)
                    o.keyframe_insert("rotation_quaternion", frame=i)
    lights = {o.name: o for o in bpy.data.objects if o.name != "cam"}
    deform_pose = _deform_setup(cfg["deform"]) if cfg.get("deform") else None
    # cfg["emit_stack"] = {mesh name: npy of (frames, verts, 3)}: what the mesh's "emit" attribute is on each frame. Nothing moves, so the triangles and the BVH stay
    emit_stacks = [(bpy.data.objects[n].data, np.load(fp, mmap_mode="r")) for n, fp in cfg.get("emit_stack", {}).items()]
    if cfg.get("fresh"):  # a killed run's frames are of the scene it had then: a killed green take once came back as the first 24 frames of the blue one
        for i in range(len(frames)):
            npy = f"{cfg['out']}_{i:03d}.npy"
            if os.path.exists(npy):
                os.remove(npy)
    for i, f in enumerate(frames):
        npy = f"{cfg['out']}_{i:03d}.npy"
        if os.path.exists(npy) or ("only" in cfg and i not in cfg["only"]):
            continue
        t1 = time.time()
        s.frame_set(i)
        _pose_camera(co, cam, f)
        if spin:
            spin_pose(f["spin_deg"])
        if deform_pose:
            deform_pose(f.get("deform_i", i))
        for me, st in emit_stacks:
            me.attributes["emit"].data.foreach_set("vector", np.asarray(st[i], np.float32).reshape(-1))
            me.update()
        if "seed" in f:
            s.cycles.seed = f["seed"]
        if "spp" in f:
            s.cycles.samples = f["spp"]
        for name, l in f.get("lights", {}).items():
            aim(lights[name], l["loc"], l["target"])
        s.render.filepath = f"{cfg['out']}_{i:03d}.exr"
        bpy.ops.render.render(write_still=True)
        img = bpy.data.images.load(s.render.filepath)
        W, H = img.size
        px = np.empty(W * H * img.channels, np.float32)
        img.pixels.foreach_get(px)
        px = px.reshape(H, W, img.channels)[::-1, :, :3]
        np.save(npy + ".tmp.npy", px.astype(np.float16))
        os.replace(npy + ".tmp.npy", npy)
        bpy.data.images.remove(img)
        os.remove(s.render.filepath)
        print(f"[studio] frame {i} rendered in {time.time() - t1:.1f} s", flush=True)
    print(f"[studio] done take of {len(frames)} frames, total {time.time() - t0:.1f} s", flush=True)


def main():
    argv = sys.argv[sys.argv.index("--") + 1 :]
    cfg = json.load(open(argv[0]))
    on_cpu = cfg.get("device") == "CPU" or "CPU" in argv[1:]
    t0 = time.time()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    s = bpy.context.scene

    # --- device
    s.render.engine = "CYCLES"
    prefs = bpy.context.preferences.addons["cycles"].preferences
    api = cfg.get("gpu_api", "METAL")
    prefs.compute_device_type = api
    prefs.get_devices()
    for d in prefs.devices:
        d.use = d.type == api and not on_cpu
    s.cycles.device = "GPU" if any(d.use for d in prefs.devices) else "CPU"

    # --- sampling
    s.render.resolution_x, s.render.resolution_y = cfg["res"]
    s.render.resolution_percentage = 100
    s.cycles.samples = cfg["spp"]
    s.cycles.use_adaptive_sampling = False
    s.cycles.seed = cfg.get("seed", 1)
    s.cycles.pixel_filter_type = "BLACKMAN_HARRIS"
    s.cycles.filter_width = cfg.get("filter", 1.3)
    s.cycles.max_bounces = cfg.get("bounces", 8)
    s.cycles.diffuse_bounces = cfg.get("diffuse_bounces", 4)
    s.cycles.glossy_bounces = cfg.get("glossy_bounces", 6)
    s.cycles.transmission_bounces = cfg.get("transmission_bounces", 12)
    s.cycles.volume_bounces = cfg.get("volume_bounces", 2)
    s.cycles.transparent_max_bounces = 16
    s.cycles.sample_clamp_direct = 0.0
    s.cycles.sample_clamp_indirect = cfg.get("clamp_indirect", 20.0)
    s.cycles.use_denoising = bool(cfg.get("denoise", True))
    if s.cycles.use_denoising:
        s.cycles.denoiser = "OPENIMAGEDENOISE"
        s.cycles.denoising_input_passes = "RGB_ALBEDO_NORMAL"
        s.cycles.denoising_prefilter = "ACCURATE"
    s.view_settings.view_transform = "Raw"
    s.view_settings.look = "None"

    # --- world
    w = bpy.data.worlds.new("w")
    w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (*cfg.get("world", [0, 0, 0]), 1)
    bg.inputs["Strength"].default_value = 1.0
    s.world = w
    if cfg.get("env"):
        # a room, seen only in reflections (kit.room_env): an equirectangular float image generated in numpy, no photograph
        e = np.load(cfg["env"]["npy"]).astype(np.float32)
        eh, ew = e.shape[:2]
        im = bpy.data.images.new("room", ew, eh, alpha=False, float_buffer=True)
        im.colorspace_settings.name = "Non-Color"
        im.pixels.foreach_set(np.concatenate([e[::-1], np.ones((eh, ew, 1), np.float32)], -1).ravel())
        im.pack()
        tx = w.node_tree.nodes.new("ShaderNodeTexEnvironment")
        tx.image = im
        w.node_tree.links.new(tx.outputs["Color"], bg.inputs["Color"])
        v = w.cycles_visibility
        v.camera = False
        v.diffuse = bool(cfg["env"].get("diffuse", False))
        v.scatter = False
        v.transmission = bool(cfg["env"].get("transmission", True))
        v.glossy = True
        if cfg["env"].get("no_diffuse_paths"):
            # stricter than v.diffuse = False: a ray that left a diffuse surface does not see the room even after going out through water, where it counts as transmission
            lp = w.node_tree.nodes.new("ShaderNodeLightPath")
            lt = w.node_tree.nodes.new("ShaderNodeMath")
            lt.operation = "LESS_THAN"
            lt.inputs[1].default_value = 0.5
            w.node_tree.links.new(lp.outputs["Diffuse Depth"], lt.inputs[0])
            w.node_tree.links.new(lt.outputs[0], bg.inputs["Strength"])
    if cfg.get("world_refraction_only"):
        # a world seen only by rays that refract out of a clear solid: it fills a crystal with light and leaves its mirror-like faces black
        v = w.cycles_visibility
        v.camera = v.diffuse = v.glossy = v.scatter = False

    # --- geometry
    for mc in cfg.get("meshes", []):
        d = np.load(mc["npz"])
        if "shader_py" in mc:
            ns = {}
            exec(compile(open(mc["shader_py"]).read(), mc["shader_py"], "exec"), ns)
            mat = ns["make"](mc["name"], mc.get("params", {}))
        else:
            mat = attr_material(mc["name"], mc["material"])
        if "F" in d.files:
            ob = soup_mesh(mc["name"], d["V"], d["F"], {k: d[k] for k in d.files if k not in ("V", "F")}, mat, smooth=mc.get("smooth", False))
        else:
            attrs = {k: d[k] for k in d.files if k != "P"}
            ob = grid_mesh(mc["name"], d["P"], attrs, mat)
        for ray, on in mc.get("visible", {}).items():  # e.g. the painted sky: seen by the camera and in reflections, gives no light to diffuse surfaces
            setattr(ob, f"visible_{ray}", on)
    for vc in cfg.get("volumes", []):
        volume(vc)
    if "backdrop" in cfg:
        backdrop(cfg["backdrop"])

    # --- lights
    for lc in cfg.get("lights", []):
        light(lc)

    # --- camera
    c = cfg["camera"]
    cam = bpy.data.cameras.new("cam")
    cam.lens = c["lens_mm"]
    cam.sensor_width = 36.0
    cam.clip_start, cam.clip_end = 0.1, 1e4
    if c.get("aperture_mm"):
        cam.dof.use_dof = True
        cam.dof.focus_distance = c["focus_distance"]
        # Cycles takes the aperture as lens_mm * 1e-3 / fstop in scene units, as if 1 unit were 1 m; here it is 1 cm.
        cam.dof.aperture_fstop = c["lens_mm"] / c["aperture_mm"] / 100.0
        cam.dof.aperture_blades = c.get("blades", 0)
        if c.get("blades"):
            cam.dof.aperture_rotation = np.radians(c.get("blade_rot", 12.0))
    co = bpy.data.objects.new("cam", cam)
    bpy.context.collection.objects.link(co)
    aim(co, c["loc"], c["target"], c.get("roll", 0.0))
    if "shift" in c:
        cam.shift_x, cam.shift_y = c["shift"]
    s.camera = co

    print(f"[studio] scene built in {time.time() - t0:.1f} s", flush=True)

    # --- render
    s.render.image_settings.file_format = "OPEN_EXR"
    s.render.image_settings.color_depth = "32"
    s.render.image_settings.color_mode = "RGB"
    if cfg.get("frames"):
        return take(cfg, s, co, cam, t0)
    s.render.filepath = cfg["out"] + ".exr"
    t1 = time.time()
    bpy.ops.render.render(write_still=True)
    print(f"[studio] rendered in {time.time() - t1:.1f} s", flush=True)

    img = bpy.data.images.load(cfg["out"] + ".exr")
    W, H = img.size
    px = np.empty(W * H * img.channels, np.float32)
    img.pixels.foreach_get(px)
    px = px.reshape(H, W, img.channels)[::-1, :, :3]
    np.save(cfg["out"] + ".npy", px)
    print(f"[studio] done {W}x{H} total {time.time() - t0:.1f} s", flush=True)


main()
