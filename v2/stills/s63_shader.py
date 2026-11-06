"""Shaders for shot 63. Selected by params["kind"]. Everything is evaluated per pixel in the bead's own frame, so it turns with the bead.

stone    Principled with true random-walk subsurface for the light. For what the eye sees: see stone(). The depth of its pattern is a stand-in for a heterogeneous medium: layers looked at along the refracted view ray, no absorption along it. No emission.
thread   Dark red twisted silk: a low specular, a little sheen.
lacquer  Black lacquer: rough slowly uneven, slow waves, very fine scratches of use.
All numbers are ESTIMATES set by eye against ref/nanhong; none was measured.

Also here: rigid_take, which make() puts in place of studio_bpy.take when the scene has "anim". The studio's take moves the camera, the lights and one spun group; this strand needs every bead and every span of thread to be its own rigid object, keyed frame by frame, so that the BVH stays and the motion blur is real (see s63_nanhong.scene). A local patch, of the same kind as softsheet's smooth soups: if the studio's take changes it may need changing too.
"""

import sys

import bpy
import numpy as np


class G:
    def __init__(self, nt):
        self.nt = nt

    def attr(self, name, out="Vector"):
        a = self.nt.nodes.new("ShaderNodeAttribute")
        a.attribute_name = name
        return a.outputs[out]

    def put(self, sock, v):
        if isinstance(v, (int, float)):
            sock.default_value = v
        elif isinstance(v, (tuple, list)):
            sock.default_value = (*v, 1)[: len(sock.default_value)]
        else:
            self.nt.links.new(v, sock)

    def m(self, op, a, b=None, c=None):
        n = self.nt.nodes.new("ShaderNodeMath")
        n.operation = op
        for i, x in enumerate((a, b, c)):
            if x is not None:
                self.put(n.inputs[i], x)
        return n.outputs[0]

    def noise(self, v, scale, detail=2.0, rough=0.5):
        n = self.nt.nodes.new("ShaderNodeTexNoise")
        self.put(n.inputs["Vector"], v)
        n.inputs["Scale"].default_value = scale
        n.inputs["Detail"].default_value = detail
        n.inputs["Roughness"].default_value = rough
        return n.outputs[0]

    def vor(self, v, scale):
        n = self.nt.nodes.new("ShaderNodeTexVoronoi")
        self.put(n.inputs["Vector"], v)
        n.inputs["Scale"].default_value = scale
        return n.outputs["Distance"], n.outputs["Color"]

    def ss(self, x, a, b, lo=0.0, hi=1.0):
        n = self.nt.nodes.new("ShaderNodeMapRange")
        n.interpolation_type = "SMOOTHSTEP"
        self.put(n.inputs["Value"], x)
        n.inputs["From Min"].default_value = a
        n.inputs["From Max"].default_value = b
        self.put(n.inputs["To Min"], lo)
        self.put(n.inputs["To Max"], hi)
        return n.outputs[0]

    def mix(self, f, a, b):
        n = self.nt.nodes.new("ShaderNodeMixRGB")
        self.put(n.inputs[0], f)
        self.put(n.inputs[1], a)
        self.put(n.inputs[2], b)
        return n.outputs[0]

    def vec(self, op, a, b):
        n = self.nt.nodes.new("ShaderNodeVectorMath")
        n.operation = op
        self.put(n.inputs[0], a)
        self.put(n.inputs[1], b)
        return n.outputs["Value" if op == "DOT_PRODUCT" else "Vector"]

    def bump(self, h, dist, normal=None, strength=1.0):
        n = self.nt.nodes.new("ShaderNodeBump")
        self.put(n.inputs["Height"], h)
        n.inputs["Distance"].default_value = dist
        n.inputs["Strength"].default_value = strength
        if normal is not None:
            self.put(n.inputs["Normal"], normal)
        return n.outputs[0]

    def rgb_scale(self, c, s):
        return self.vec("MULTIPLY", c, s)


def stone(g, b, p):
    """The 17:15 stone chosen (frame012_final): persimmon body, slow clouds, gathered cinnabar points, a thin pale band on a few beads; waxy polish. What this version adds: the clouds and points are looked at along the refracted ray, so they lie in the stone and move against the surface; a faint turbid floc in the deep layer."""
    nt = g.nt
    lp0 = g.attr("lp")
    base = g.attr("col", "Color")
    par = nt.nodes.new("ShaderNodeSeparateXYZ")
    g.put(par.inputs[0], g.attr("par"))
    band_k, dots_k, crack_k = par.outputs[0], par.outputs[1], par.outputs[2]

    # the refracted view ray, in the bead's frame. T = -eta I + (eta cos - sqrt(1 - eta^2 (1 - cos^2))) N
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    I, N = geo.outputs["Incoming"], geo.outputs["Normal"]
    eta = 1.0 / 1.54
    cosi = g.vec("DOT_PRODUCT", I, N)
    root = g.m("SQRT", g.m("SUBTRACT", 1.0, g.m("MULTIPLY", eta * eta, g.m("SUBTRACT", 1.0, g.m("MULTIPLY", cosi, cosi)))))
    a = g.m("SUBTRACT", g.m("MULTIPLY", eta, cosi), root)
    sI = nt.nodes.new("ShaderNodeVectorMath")
    sI.operation = "SCALE"
    g.put(sI.inputs[0], I)
    sI.inputs["Scale"].default_value = -eta
    sN = nt.nodes.new("ShaderNodeVectorMath")
    sN.operation = "SCALE"
    g.put(sN.inputs[0], N)
    g.put(sN.inputs["Scale"], a)
    T = g.vec("ADD", sI.outputs["Vector"], sN.outputs["Vector"])
    cos_t = g.m("MAXIMUM", g.m("MULTIPLY", g.vec("DOT_PRODUCT", T, N), -1.0), 0.3)
    xf = nt.nodes.new("ShaderNodeVectorTransform")
    xf.vector_type = "VECTOR"
    xf.convert_from = "WORLD"
    xf.convert_to = "OBJECT"
    g.put(xf.inputs[0], T)
    To = xf.outputs[0]

    def at(depth):
        sc = nt.nodes.new("ShaderNodeVectorMath")
        sc.operation = "SCALE"
        g.put(sc.inputs[0], To)
        g.put(sc.inputs["Scale"], g.m("DIVIDE", depth, cos_t))
        return g.vec("ADD", lp0, sc.outputs["Vector"])

    deep, mid = at(p.get("d_deep", 0.2)), at(p.get("d_mid", 0.06))

    # slow clouds in the body, deeper and lighter: this stone is not one flat red
    c1 = g.noise(deep, 0.9, 3.0, 0.5)
    c2 = g.noise(deep, 3.2, 3.0, 0.55)
    col = g.mix(g.ss(c1, 0.36, 0.66), g.vec("MULTIPLY", base, (0.62, 0.42, 0.5)), g.vec("MULTIPLY", base, (1.18, 1.35, 1.1)))
    col = g.mix(g.m("MULTIPLY", g.ss(c2, 0.5, 0.72), 0.35), col, g.vec("MULTIPLY", base, (1.3, 1.9, 1.5)))
    # a turbid floc: small soft patches, paler, deep in the stone and never at the surface
    fl = g.ss(g.noise(deep, 6.5, 4.0, 0.62), 0.54, 0.74)
    fl = g.m("MULTIPLY", g.m("MULTIPLY", fl, g.ss(g.noise(deep, 1.3, 2.0, 0.5), 0.42, 0.62)), p.get("floc", 0.42))
    col = g.mix(fl, col, g.vec("MULTIPLY", base, (1.32, 2.5, 2.5)))

    # cinnabar: fine deep-red points, thick where they gather, a coarse and a fine size
    gather = g.ss(g.noise(mid, 1.6, 2.0, 0.5), 0.38, 0.58)
    d1, r1 = g.vor(mid, p.get("dot1", 15.0))
    d2, r2 = g.vor(mid, p.get("dot2", 30.0))
    s1 = nt.nodes.new("ShaderNodeSeparateColor")
    g.put(s1.inputs[0], r1)
    s2 = nt.nodes.new("ShaderNodeSeparateColor")
    g.put(s2.inputs[0], r2)
    dot1 = g.m("MULTIPLY", g.ss(d1, 0.46, 0.16), g.ss(s1.outputs[0], 0.3, 0.45))
    dot2 = g.m("MULTIPLY", g.ss(d2, 0.46, 0.18), g.ss(s2.outputs[0], 0.25, 0.4))
    dots = g.m("MAXIMUM", g.m("MULTIPLY", dot1, 0.9), dot2)
    dots = g.m("MULTIPLY", g.m("MULTIPLY", dots, gather), dots_k)
    col = g.mix(dots, col, g.vec("MULTIPLY", base, (0.42, 0.22, 0.28)))

    # a pale agate band, wandering; at most one or two on a bead
    warp = g.m("MULTIPLY", g.m("SUBTRACT", g.noise(lp0, 1.4, 3.0, 0.5), 0.5), 0.12)
    along = g.m("ADD", g.vec("DOT_PRODUCT", lp0, g.attr("ax")), warp)
    ph = g.m("ABSOLUTE", g.m("SINE", g.m("MULTIPLY", along, 1.9)))
    band = g.m("MULTIPLY", g.m("ADD", g.ss(ph, 0.075, 0.03), g.m("MULTIPLY", g.ss(g.m("ABSOLUTE", g.m("SUBTRACT", ph, 0.11)), 0.018, 0.006), 0.6)), band_k)
    col = g.mix(band, col, (0.66, 0.3, 0.16))

    # a healed crack: where a smooth noise crosses one level, in a few places only
    n3 = g.noise(lp0, 2.4, 3.0, 0.45)
    line = g.ss(g.m("ABSOLUTE", g.m("SUBTRACT", n3, 0.5)), 0.0035, 0.0012)
    line = g.m("MULTIPLY", g.m("MULTIPLY", line, crack_k), g.ss(g.noise(lp0, 1.0, 1.0, 0.5), 0.48, 0.58))
    col = g.mix(g.m("MULTIPLY", line, 0.32), col, (0.72, 0.36, 0.2))

    # the mouth of the hole: dark with wear and the grime of the thread
    wear = g.attr("wear", "Fac")
    col = g.mix(wear, col, g.vec("MULTIPLY", base, (0.12, 0.08, 0.08)))
    g.put(b.inputs["Base Color"], col)

    # wax polish: the roughness wanders; a crack and a worn mouth are rougher
    r = g.m("ADD", p.get("rough", 0.2), g.m("MULTIPLY", g.ss(g.noise(lp0, 1.8, 3.0, 0.55), 0.35, 0.68), 0.16))
    r = g.m("ADD", r, g.m("MULTIPLY", g.ss(g.noise(lp0, 11.0, 2.0, 0.5), 0.45, 0.65), 0.05))
    r = g.m("ADD", r, g.m("ADD", g.m("MULTIPLY", wear, 0.3), g.m("MULTIPLY", line, 0.25)))
    g.put(b.inputs["Roughness"], r)

    h = g.m("ADD", g.noise(lp0, 5.0, 3.0, 0.5), g.m("MULTIPLY", g.noise(lp0, 45.0, 2.0, 0.5), 0.1))
    h = g.m("SUBTRACT", h, g.m("MULTIPLY", line, 0.1))
    g.put(b.inputs["Normal"], g.bump(h, p.get("bump", 0.004)))
    b.subsurface_method = "RANDOM_WALK"
    b.inputs["Subsurface Weight"].default_value = 1.0
    b.inputs["Subsurface Radius"].default_value = p.get("radius", (0.34, 0.05, 0.03))
    b.inputs["Subsurface Scale"].default_value = 1.0
    b.inputs["IOR"].default_value = 1.54


def thread(g, b, p):
    g.put(b.inputs["Base Color"], g.attr("col", "Color"))
    b.inputs["Roughness"].default_value = 0.62
    b.inputs["Specular IOR Level"].default_value = 0.2
    b.inputs["Sheen Weight"].default_value = 0.35
    b.inputs["Sheen Tint"].default_value = (0.5, 0.05, 0.05, 1)


def lacquer(g, b, p):
    tc = g.nt.nodes.new("ShaderNodeTexCoord").outputs["Object"]
    b.inputs["Specular IOR Level"].default_value = 0.5
    b.inputs["IOR"].default_value = 1.5

    # scratches of use: long, very thin, three directions; only here and there
    def scratch(angle, seed, sc):
        turn = g.nt.nodes.new("ShaderNodeMapping")  # first turn, then stretch: one node does scale first, and every scratch then runs exactly along x, a dead straight line across the frame that seams.py finds
        g.put(turn.inputs["Vector"], tc)
        turn.inputs["Rotation"].default_value = (0, 0, angle)
        n = g.nt.nodes.new("ShaderNodeMapping")
        g.nt.links.new(turn.outputs[0], n.inputs["Vector"])
        n.inputs["Scale"].default_value = (0.25, sc, 1.0)
        n.inputs["Location"].default_value = (seed, seed * 3.1, 0.0)
        return g.ss(g.noise(n.outputs[0], 1.0, 1.0, 0.3), 0.73, 0.78)

    s = g.m("MAXIMUM", g.m("MAXIMUM", scratch(0.21, 3.0, 55.0), scratch(-0.55, 11.0, 70.0)), scratch(1.25, 23.0, 45.0))
    s = g.m("MULTIPLY", s, g.ss(g.noise(tc, 0.28, 2.0, 0.5), 0.44, 0.62))
    b.inputs["Base Color"].default_value = (0.0032, 0.0028, 0.0028, 1)
    g.put(b.inputs["Base Color"], g.mix(g.m("MULTIPLY", s, 0.8), (0.0032, 0.0028, 0.0028), (0.03, 0.028, 0.027)))
    g.put(b.inputs["Roughness"], g.m("ADD", g.m("ADD", 0.05, g.m("MULTIPLY", g.ss(g.noise(tc, 0.35, 3.0, 0.5), 0.35, 0.68), 0.05)), g.m("MULTIPLY", s, 0.22)))
    h = g.m("ADD", g.m("MULTIPLY", g.noise(tc, 0.12, 2.0, 0.4), 1.0), g.m("MULTIPLY", g.noise(tc, 1.3, 2.0, 0.45), 0.07))
    h = g.m("SUBTRACT", h, g.m("MULTIPLY", s, 0.003))
    g.put(b.inputs["Normal"], g.bump(h, p.get("bump", 0.05)))


def rigid_take(cfg, s, co, cam, t0):
    """As studio_bpy.take, but cfg["anim"] = {object: [[x, y, z, w, qx, qy, qz, scale_z], ...]} moves whole objects, with cfg["anim_pad"] keys before the first frame and after the last, so those frames have their blur too."""
    import os
    import time

    prefs = bpy.context.preferences.edit
    prefs.keyframe_new_interpolation_type = "LINEAR"
    frames, pad = cfg["frames"], cfg.get("anim_pad", 1)
    s.render.use_persistent_data = True
    shutter = cfg.get("shutter", 0.5)
    s.frame_start, s.frame_end = 0, len(frames) + 2 * pad
    if shutter:
        s.render.use_motion_blur = True
        s.render.motion_blur_shutter = shutter
        s.render.motion_blur_position = "CENTER"
    for name, track in cfg["anim"].items():
        o = bpy.data.objects[name]
        o.rotation_mode = "QUATERNION"
        for j, t in enumerate(track):
            o.location = t[:3]
            o.rotation_quaternion = t[3:7]
            o.scale = (1.0, 1.0, t[7])
            o.keyframe_insert("location", frame=j)
            o.keyframe_insert("rotation_quaternion", frame=j)
            o.keyframe_insert("scale", frame=j)
    only = cfg.get("anim_only")
    for i in range(len(frames)):
        npy = f"{cfg['out']}_{i:03d}.npy"
        t1 = time.time()
        s.frame_set((only if only is not None else i) + pad)
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


def _patch_studio():
    g = sys._getframe(2).f_globals
    if "take" not in g or getattr(g["take"], "_rigid", False):
        return
    g["take"] = rigid_take
    rigid_take._rigid = True
    old = g["soup_mesh"]

    def soft(name, V, F, attrs, mat):
        ob = old(name, V, F, attrs, mat)
        ob.data.polygons.foreach_set("use_smooth", np.ones(len(F), dtype=bool))
        ob.data.update()
        return ob

    g["soup_mesh"] = soft


def make(name, p):
    _patch_studio()
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    {"stone": stone, "thread": thread, "lacquer": lacquer}[p["kind"]](G(nt), b, p)
    return m
