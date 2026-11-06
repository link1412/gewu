"""Render a camera-RGB scene (tools/rgbscene.py) with Blender Cycles; inside Blender:

    blender -b --factory-startup -P tools/cycles_scene.py -- DIR/scene.cycles.json --out DIR/cyc.exr \
        [--device GPU|CPU] [--spp N] [--adaptive THRESHOLD] [--denoise] [--res WxH] [--seed S] [--time-limit SEC]

Writes a float EXR of the camera's raw RGB in pbrt's orientation (tools/camera.py develops it like pbrt's
rawsensor film) and, next to it, a .json with the settings and the render time.

Matching pbrt (not more than the scene uses):
- an area light is one-sided, emits radiance E (camera RGB) on the side of its normal and reflects with
  its material (pbrt's default: diffuse 0.5) on both;
- a dielectric with a medium inside carries that medium as its volume (homogeneous coefficients, HG phase);
- thindielectric: specular reflection R + T^2 R / (1 - R^2) with R the Fresnel term at |cos| (pbrt's
  ThinDielectricBxDF), the rest straight through; built from math nodes, since a Glass BSDF refracts and
  flips its IOR on back faces;
- every BSDF node's colour is set or linked: Blender's defaults are not white (Glossy and Diffuse 0.8);
- a PLY mesh with vertex normals: the normals decide the front, as in pbrt; faces wound against them are turned over
  (orient_to_normals);
- textures (docs/textures.md), pbrt's semantics: float imagemaps on the UV map (default UV mapping, wrap, scale,
  invert; pbrt's t runs down the image and Blender's up, which a file loaded as is already agrees with), bump
  maps ("displacement", scene units; a Bump node fed the height in metres) on diffuse / dielectric /
  thindielectric / conductor, roughness maps on dielectric / conductor; Cycles has no MIP pyramid: it filters bilinearly, pbrt picks
  a level by its ray differentials;
- diffusetransmission (pbrt's): a Diffuse BSDF of colour R plus a Translucent BSDF of colour T, either one
  uniform or a familymap (a leaf, materials/yinxing/);
- ours, not pbrt's: a diffuse reflectance that runs through a family of spectra, looked up from the table
  rgbscene projected, by a float map c(u,v) (linear in c, clamped to the table's ends);
- Blender is right-handed and pbrt left-handed, so the same LookAt gives a mirrored picture: the render is
  flipped left-right before it is written.

Light groups (docs/optics.md): when the scene's emitters carry groups (pbrt's Attribute "light" "string group",
read by rgbscene), each group is a Blender light group and the one render also writes, beside OUT.exr,
OUT.<group>.exr per group (each group's light alone, the same paths and samples: they add up to OUT.exr) and
OUT.albedo.exr, OUT.normal.exr (Cycles' denoising albedo and normal, for denoising a mix of the groups later,
tools/cycles_denoise.py). All in pbrt's orientation. --denoise denoises OUT.exr only, never the groups.
"""

import json
import math
import os
import re
import sys
import time

import bpy
import numpy as np
from mathutils import Matrix, Vector


def args():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("scene")
    ap.add_argument("--out", required=True)
    ap.add_argument("--device", default="GPU", choices=["GPU", "CPU"])
    ap.add_argument("--spp", type=int)
    ap.add_argument("--adaptive", type=float, help="adaptive sampling noise threshold (off if not given)")
    ap.add_argument("--min-spp", type=int, default=0, help="adaptive sampling: samples before it may stop")
    ap.add_argument("--denoise", action="store_true", help="OpenImageDenoise with albedo and normal")
    ap.add_argument("--res")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--time-limit", type=float, default=0.0)
    return ap.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])


# --- nodes -----------------------------------------------------------------------------------
class Graph:
    def __init__(self, mat):
        mat.use_nodes = True
        self.nt = mat.node_tree
        self.nt.nodes.clear()
        self.out = self.nt.nodes.new("ShaderNodeOutputMaterial")

    def node(self, kind, **inputs):
        n = self.nt.nodes.new(kind)
        for k, v in inputs.items():
            self.link(v, n.inputs[k])
        return n

    def link(self, v, sock):
        if hasattr(v, "outputs"):
            self.nt.links.new(v.outputs[0], sock)
        elif isinstance(v, tuple) and len(v) == 2 and hasattr(v[0], "outputs"):
            self.nt.links.new(v[0].outputs[v[1]], sock)
        else:
            sock.default_value = v

    def math(self, op, a, b=0.0):
        n = self.nt.nodes.new("ShaderNodeMath")
        n.operation = op
        self.link(a, n.inputs[0])
        self.link(b, n.inputs[1])
        return n

    def vec(self, op, a, b=None, scale=None):
        """Vector math; DOT_PRODUCT gives its Value (output 1), the rest their Vector."""
        n = self.nt.nodes.new("ShaderNodeVectorMath")
        n.operation = op
        self.link(a, n.inputs[0])
        if b is not None:
            self.link(b, n.inputs[1])
        if scale is not None:
            self.link(scale, n.inputs[3])
        return (n, 1) if op == "DOT_PRODUCT" else (n, 0)

    def xyz(self, x, y, z=0.0):
        n = self.nt.nodes.new("ShaderNodeCombineXYZ")
        for i, v in enumerate((x, y, z)):
            self.link(v, n.inputs[i])
        return n

    def split(self, v):
        n = self.nt.nodes.new("ShaderNodeSeparateXYZ")
        self.link(v, n.inputs[0])
        return [(n, i) for i in range(3)]

    def tex(self, image, vector, interpolation, extension="EXTEND"):
        n = self.nt.nodes.new("ShaderNodeTexImage")
        n.image = image
        n.interpolation = interpolation
        n.extension = extension
        self.link(vector, n.inputs["Vector"])
        return (n, 0)


def rgba(c):
    return (c[0], c[1], c[2], 1.0)


def thin_dielectric(g, eta, normal=None):
    """Mix(transparent, sharp glossy) by pbrt's thin-slab reflectance at |cos theta|; `normal` (a bump map's)
    replaces the shading normal in both the cosine and the glossy lobe."""
    geo = g.node("ShaderNodeNewGeometry")
    dot = g.nt.nodes.new("ShaderNodeVectorMath")
    dot.operation = "DOT_PRODUCT"
    g.nt.links.new(geo.outputs["Incoming"], dot.inputs[0])
    if normal is None:
        g.nt.links.new(geo.outputs["Normal"], dot.inputs[1])
    else:
        g.link(normal, dot.inputs[1])
    c = g.math("MINIMUM", g.math("ABSOLUTE", (dot, "Value")), 1.0)
    s2t = g.math("DIVIDE", g.math("SUBTRACT", 1.0, g.math("MULTIPLY", c, c)), eta * eta)
    ct = g.math("SQRT", g.math("MAXIMUM", g.math("SUBTRACT", 1.0, s2t), 0.0))
    ec, et = g.math("MULTIPLY", c, eta), g.math("MULTIPLY", ct, eta)
    rpa = g.math("DIVIDE", g.math("SUBTRACT", ec, ct), g.math("MAXIMUM", g.math("ADD", ec, ct), 1e-9))
    rpe = g.math("DIVIDE", g.math("SUBTRACT", c, et), g.math("MAXIMUM", g.math("ADD", c, et), 1e-9))
    R = g.math("MULTIPLY", g.math("ADD", g.math("MULTIPLY", rpa, rpa), g.math("MULTIPLY", rpe, rpe)), 0.5)
    T = g.math("SUBTRACT", 1.0, R)
    R2 = g.math("ADD", R, g.math("DIVIDE", g.math("MULTIPLY", g.math("MULTIPLY", T, T), R),
                                    g.math("MAXIMUM", g.math("SUBTRACT", 1.0, g.math("MULTIPLY", R, R)), 1e-9)))
    tir = g.math("GREATER_THAN", s2t, 0.999999)          # total internal reflection: R = 1
    fac = g.math("MINIMUM", g.math("MAXIMUM", R2, tir), 1.0)
    glossy = g.node("ShaderNodeBsdfAnisotropic")        # the Glossy BSDF (its id since Blender 4.0)
    glossy.distribution = "GGX"
    glossy.inputs["Roughness"].default_value = 0.0
    # white: the node's default Color is 0.8 grey, which took a fifth of the light at every reflection off the film
    # (docs/slab.md, the film section); the reflectance is all in the mix factor
    glossy.inputs["Color"].default_value = (1.0, 1.0, 1.0, 1.0)
    if normal is not None:
        g.link(normal, glossy.inputs["Normal"])
    mix = g.node("ShaderNodeMixShader", Fac=fac)
    g.nt.links.new(g.node("ShaderNodeBsdfTransparent").outputs[0], mix.inputs[1])
    g.nt.links.new(glossy.outputs[0], mix.inputs[2])
    return mix


def float_image(name, arr):
    """A float, non-colour image from an (H, W, 3) array whose row 0 is the image's bottom row."""
    arr = np.asarray(arr, np.float32)
    H, W = arr.shape[:2]
    img = bpy.data.images.new(name, W, H, alpha=False, float_buffer=True)
    img.colorspace_settings.name = "Non-Color"
    px = np.ones((H, W, img.channels), np.float32)
    px[..., :3] = arr
    img.pixels.foreach_set(px.ravel())
    return img


_images = {}


def read_float_image(path, encoding):
    """A scalar image as pbrt's FloatImageTexture sees it: one channel, or the mean of three (alpha ignored; pbrt
    returns the alpha of a four-channel image, which is not handled), linear. Returns (H, W) with row 0 the
    BOTTOM row (Blender's order). EXR and PNG through Blender (read raw, "Non-Color"), PFM by hand."""
    key = (path, encoding)
    if key in _images:
        return _images[key]
    if not os.path.isfile(path):
        raise SystemExit(f"texture file {path} does not exist")
    if path.lower().endswith(".pfm"):
        with open(path, "rb") as f:
            kind = f.readline().strip()
            w, h = map(int, f.readline().split())
            sc = float(f.readline())
            nc = {b"PF": 3, b"Pf": 1}[kind]
            a = np.frombuffer(f.read(), "<f4" if sc < 0 else ">f4").reshape(h, w, nc).astype(np.float32)
        a = a.mean(2)                                   # PFM rows run bottom to top already
    else:
        img = bpy.data.images.load(path, check_existing=False)
        img.colorspace_settings.name = "Non-Color"
        w, h = img.size
        px = np.empty(w * h * img.channels, np.float32)
        img.pixels.foreach_get(px)
        a = px.reshape(h, w, img.channels)[..., :3].mean(2)
        bpy.data.images.remove(img)
    if encoding == "sRGB":
        a = np.where(a <= 0.04045, a / 12.92, ((np.maximum(a, 0) + 0.055) / 1.055) ** 2.4).astype(np.float32)
    _images[key] = a
    return a


def float_texture(g, t, base):
    """pbrt's FloatImageTexture on the UV map: st = (su u + du, sv v + dv), bilinear lookup with the image's
    top row at t = 1, value = scale * texel (or max(0, 1 - that) if inverted). Returns a Value socket."""
    a = read_float_image(os.path.join(base, t["file"]), t["encoding"])
    img = float_image(t["file"], np.repeat(a[..., None], 3, 2))
    u, v, _ = g.split((g.node("ShaderNodeTexCoord"), "UV"))
    st = g.xyz(g.math("ADD", g.math("MULTIPLY", u, t["su"]), t["du"]),
               g.math("ADD", g.math("MULTIPLY", v, t["sv"]), t["dv"]))
    val = g.split(g.tex(img, st, "Linear", "REPEAT" if t["wrap"] == "repeat" else "EXTEND"))[0]
    if t["scale"] != 1.0:
        val = g.math("MULTIPLY", val, t["scale"])
    if t["invert"]:
        val = g.math("MAXIMUM", g.math("SUBTRACT", 1.0, val), 0.0)
    return val


def family_colour(g, f, base):
    """Our familymap: the table (N, 3) at c(u,v), linear in c between the rows, clamped at the ends. The table
    is a small image looked up with linear filtering, which needs even spacing in c: uneven rows are resampled
    (4096 entries, the worst error against the exact piecewise-linear table is printed)."""
    c, T = np.array(f["c"], float), np.array(f["table"], float)
    if np.allclose(np.diff(c), (c[-1] - c[0]) / (len(c) - 1), rtol=1e-9, atol=0):
        lut = T
    else:
        cc = np.linspace(c[0], c[-1], 4096)
        lut = np.stack([np.interp(cc, c, T[:, k]) for k in range(3)], 1)
        fine = np.linspace(c[0], c[-1], 200001)
        lin = (fine - c[0]) / (c[-1] - c[0]) * 4095
        err = max(np.abs(np.interp(lin, np.arange(4096), lut[:, k]) - np.interp(fine, c, T[:, k])).max() for k in range(3))
        print(f"familymap: uneven c resampled to 4096 rows, worst error {err:.2e}")
    n = len(lut)
    cm = float_texture(g, f["map"], base)
    x = g.math("DIVIDE", g.math("SUBTRACT", g.math("MINIMUM", g.math("MAXIMUM", cm, c[0]), c[-1]), c[0]), c[-1] - c[0])
    at = g.xyz(g.math("DIVIDE", g.math("ADD", g.math("MULTIPLY", x, n - 1), 0.5), n), 0.5)
    return g.tex(float_image("family", lut[None]), at, "Linear")


def film(g, m, base, normal=None):
    """Ours (docs/coats.md): an absorbing film, a thindielectric of eta 1 with a "transmittance" (pbrt, as patched:
    T0^(1/|cos|) per crossing, straight through). A Transparent BSDF coloured by the table rgbscene wrote, T(c, mu)
    per channel at mu = |cos| between the ray and the normal (a bump map's, if given), linear in mu and in c,
    c clamped to the table's ends; uneven c rows are resampled to 4096 (the worst error is printed)."""
    geo = g.node("ShaderNodeNewGeometry")
    dot = g.nt.nodes.new("ShaderNodeVectorMath")
    dot.operation = "DOT_PRODUCT"
    g.nt.links.new(geo.outputs["Incoming"], dot.inputs[0])
    if normal is None:
        g.nt.links.new(geo.outputs["Normal"], dot.inputs[1])
    else:
        g.link(normal, dot.inputs[1])
    mu = g.math("MINIMUM", g.math("ABSOLUTE", (dot, "Value")), 1.0)
    if "transmittance" in m:
        t = m["transmittance"]
        T = np.array(t["table"], float)[None]                         # (1, M, 3)
        y = 0.5
    else:
        t = m["transmittance_family"]
        c, T = np.array(t["c"], float), np.array(t["table"], float)  # (N,), (N, M, 3)
        if not np.allclose(np.diff(c), (c[-1] - c[0]) / (len(c) - 1), rtol=1e-9, atol=0):
            cc = np.linspace(c[0], c[-1], 4096)
            fine = np.linspace(c[0], c[-1], 20001)
            lut = np.empty((4096,) + T.shape[1:])
            err = 0.0
            for j in range(T.shape[1]):
                for k in range(3):
                    lut[:, j, k] = np.interp(cc, c, T[:, j, k])
                    err = max(err, np.abs(np.interp(fine, cc, lut[:, j, k]) - np.interp(fine, c, T[:, j, k])).max())
            print(f"film: uneven c resampled to 4096 rows, worst error {err:.2e}")
            T = lut
        cm = float_texture(g, t["map"], base)
        x = g.math("DIVIDE", g.math("SUBTRACT", g.math("MINIMUM", g.math("MAXIMUM", cm, c[0]), c[-1]), c[0]), c[-1] - c[0])
        y = g.math("DIVIDE", g.math("ADD", g.math("MULTIPLY", x, T.shape[0] - 1), 0.5), T.shape[0])
    nm = len(t["mu"])
    if not np.allclose(t["mu"], np.linspace(0, 1, nm)):
        raise SystemExit("film: the table's cosines must be even from 0 to 1")
    xm = g.math("DIVIDE", g.math("ADD", g.math("MULTIPLY", mu, nm - 1), 0.5), nm)
    col = g.tex(float_image("film", T), g.xyz(xm, y), "Linear")
    return g.node("ShaderNodeBsdfTransparent", Color=col)


def nacre_inlay(g, m, base):
    """Shot 19's mother-of-pearl in black lacquer (tools/rgbscene.py nacre_inlay; the physics in
    shots/19-luodian/nacre.py). Per shading point, along the view ray traced backwards:
    refract into the shell at the polished surface (normal N, index n_o), reflect off the layers (normal L,
    from the maps), refract out (or lose it to total internal reflection). The light must come from that
    exit direction I, so the layers' lobe is a glossy lobe about H = normalize(V + I), coloured by the stack's
    table at (the piece's tablet thickness, b = n_o sin(angle to L)) and the surface's transmissions in and
    out, per polarisation. On top, the polished surface's own glossy lobe; where the mask is 0, lacquer."""
    M = np.load(os.path.join(base, m["maps"]))
    x0, x1, y0, y1 = [float(v) for v in M["extent"]]
    inlay = float_image("inlay", M["inlay"])
    layers = float_image("layers", M["layers"])
    ss, sp = np.array(m["stack_s"]), np.array(m["stack_p"])          # (n_d, n_b, 3)
    ts, tp = np.array(m["top_s"])[None], np.array(m["top_p"])[None]  # (1, n_mu, 3)
    st_s, st_p = float_image("stack_s", ss), float_image("stack_p", sp)
    tp_s, tp_p = float_image("top_s", ts), float_image("top_p", tp)
    n_d, n_b, n_mu = ss.shape[0], ss.shape[1], ts.shape[1]
    n = m["n_o"]
    eta = 1.0 / n

    def lut_coord(x, count):              # [0, 1] -> the centres of the first and last texels
        return g.math("DIVIDE", g.math("ADD", g.math("MULTIPLY", x, count - 1), 0.5), count)

    geo = g.node("ShaderNodeNewGeometry")
    N, V = (geo, "Normal"), (geo, "Incoming")
    # the maps, in object space (they turn with the lobe)
    tc = g.node("ShaderNodeTexCoord")
    ox, oy, _ = g.split((tc, "Object"))
    uv = g.xyz(g.math("DIVIDE", g.math("SUBTRACT", ox, x0), x1 - x0), g.math("DIVIDE", g.math("SUBTRACT", oy, y0), y1 - y0))
    mask, dn, _ = g.split(g.tex(inlay, uv, "Closest"))
    nm = g.node("ShaderNodeNormalMap")
    nm.space = "OBJECT"
    g.link(g.tex(layers, uv, "Linear"), nm.inputs["Color"])
    L = (nm, "Normal")
    # in through the polished surface
    cv = g.math("MINIMUM", g.math("MAXIMUM", g.vec("DOT_PRODUCT", N, V), 1e-4), 1.0)
    ct = g.math("SQRT", g.math("SUBTRACT", 1.0, g.math("MULTIPLY", eta * eta, g.math("SUBTRACT", 1.0, g.math("MULTIPLY", cv, cv)))))
    t = g.vec("ADD", g.vec("SCALE", V, scale=-eta), g.vec("SCALE", N, scale=g.math("SUBTRACT", g.math("MULTIPLY", cv, eta), ct)))
    # off the layers
    cl = g.math("MAXIMUM", g.math("MULTIPLY", g.vec("DOT_PRODUCT", t, L), -1.0), 0.0)
    b = g.math("MULTIPLY", g.math("SQRT", g.math("MAXIMUM", g.math("SUBTRACT", 1.0, g.math("MULTIPLY", cl, cl)), 0.0)), n)
    r = g.vec("ADD", t, g.vec("SCALE", L, scale=g.math("MULTIPLY", cl, 2.0)))
    # out through the polished surface
    ci = g.vec("DOT_PRODUCT", r, N)
    s2 = g.math("MULTIPLY", n * n, g.math("SUBTRACT", 1.0, g.math("MULTIPLY", ci, ci)))
    ok = g.math("MULTIPLY", g.math("GREATER_THAN", ci, 0.0), g.math("LESS_THAN", s2, 1.0))
    co = g.math("SQRT", g.math("MAXIMUM", g.math("SUBTRACT", 1.0, s2), 1e-8))
    I = g.vec("ADD", g.vec("SCALE", r, scale=n), g.vec("SCALE", N, scale=g.math("SUBTRACT", co, g.math("MULTIPLY", ci, n))))
    H = g.vec("NORMALIZE", g.vec("ADD", V, I))
    # the tables
    sv = g.xyz(lut_coord(g.math("DIVIDE", b, m["b_max"]), n_b), lut_coord(dn, n_d))
    Rs, Rp = g.tex(st_s, sv, "Linear"), g.tex(st_p, sv, "Linear")
    at_v, at_o = g.xyz(lut_coord(cv, n_mu), 0.5), g.xyz(lut_coord(co, n_mu), 0.5)
    lobes = []
    for R, top in ((Rs, tp_s), (Rp, tp_p)):
        Tv = g.vec("SUBTRACT", (1.0, 1.0, 1.0), g.tex(top, at_v, "Linear"))
        To_r = g.tex(top, at_o, "Linear")
        To = g.vec("SUBTRACT", (1.0, 1.0, 1.0), To_r)
        num = g.vec("MULTIPLY", g.vec("MULTIPLY", Tv, To), R)
        den = g.vec("SUBTRACT", (1.0, 1.0, 1.0), g.vec("MULTIPLY", To_r, R))
        lobes.append(g.vec("DIVIDE", num, den))
    lobe = g.vec("SCALE", g.vec("ADD", *lobes), scale=g.math("MULTIPLY", ok, 0.5))
    gl = g.node("ShaderNodeBsdfAnisotropic", Color=lobe, Roughness=math.sqrt(m["layers_alpha"]), Normal=H)
    gl.distribution = "GGX"
    top = g.vec("SCALE", g.vec("ADD", g.tex(tp_s, at_v, "Linear"), g.tex(tp_p, at_v, "Linear")), scale=0.5)
    gt = g.node("ShaderNodeBsdfAnisotropic", Color=top, Roughness=math.sqrt(m["shell_alpha"]), Normal=N)
    gt.distribution = "GGX"
    shell = g.node("ShaderNodeAddShader")
    g.link(gt, shell.inputs[0])
    g.link(gl, shell.inputs[1])
    # black lacquer: Fresnel-weighted mirror over its faint diffuse body
    F = g.node("ShaderNodeFresnel", IOR=m["lacquer_eta"])
    gk = g.node("ShaderNodeBsdfAnisotropic", Color=F, Roughness=math.sqrt(m["lacquer_alpha"]))
    gk.distribution = "GGX"
    kd = g.math("MULTIPLY", g.math("SUBTRACT", 1.0, F), m["lacquer_diffuse"])
    dk = g.node("ShaderNodeBsdfDiffuse", Color=g.xyz(kd, kd, kd))
    lacquer = g.node("ShaderNodeAddShader")
    g.link(gk, lacquer.inputs[0])
    g.link(dk, lacquer.inputs[1])
    mix = g.node("ShaderNodeMixShader", Fac=mask)
    g.link(lacquer, mix.inputs[1])
    g.link(shell, mix.inputs[2])
    return mix


def barbule(g, m):
    """Shot 17's peacock barbules (tools/rgbscene.py barbule; the physics in shots/17-peacock/barbule.py): a GGX lobe
    about the shading normal coloured by the table at (s = the UV map's u, mu = cos(view, shading normal)), plus the
    dark diffuse body. Nodes cannot see the light's direction, so the colour is the view's (mirror reflection: the
    angle of incidence equals the view's); the light picks which barbules (which normals) are bright. A barbule's
    curved cross-section is in its vertex normals (scene.py), not here."""
    T = np.array(m["table"])                                        # (n_s, n_mu, 3)
    n_s, n_mu = T.shape[0], T.shape[1]
    img = float_image("barbule", T)

    def lut_coord(x, count):
        return g.math("DIVIDE", g.math("ADD", g.math("MULTIPLY", x, count - 1), 0.5), count)

    geo = g.node("ShaderNodeNewGeometry")
    mu = g.math("MINIMUM", g.math("ABSOLUTE", g.vec("DOT_PRODUCT", (geo, "Normal"), (geo, "Incoming"))), 1.0)
    tc = g.node("ShaderNodeTexCoord")
    if m.get("s_attribute"):
        at = g.node("ShaderNodeAttribute")
        at.attribute_type = "GEOMETRY"
        at.attribute_name = m["s_attribute"]
        s = (at, "Fac")
    else:
        s, _, _ = g.split((tc, "UV"))
    col = g.tex(img, g.xyz(lut_coord(mu, n_mu), lut_coord(s, n_s)), "Linear")
    if "table2" in m:                                               # r3: graded into a second region's table
        T2 = np.array(m["table2"])
        img2 = float_image("barbule2", T2)

        def attr(name):
            a = g.node("ShaderNodeAttribute")
            a.attribute_type = "GEOMETRY"
            a.attribute_name = name
            return (a, "Fac")
        col2 = g.tex(img2, g.xyz(lut_coord(mu, T2.shape[1]), lut_coord(attr(m["s2_attribute"]), T2.shape[0])), "Linear")
        mx = g.node("ShaderNodeMix")
        mx.data_type = "RGBA"
        sock = {x.identifier: x for x in mx.inputs}
        g.link(attr(m["mix_attribute"]), sock["Factor_Float"])
        g.link(col, sock["A_Color"])
        g.link(col2, sock["B_Color"])
        col = (mx, [o.identifier for o in mx.outputs].index("Result_Color"))
    gl = g.node("ShaderNodeBsdfAnisotropic", Color=col, Roughness=math.sqrt(m["alpha"]))
    gl.distribution = "GGX"
    if m.get("anisotropy", 0.0):
        # the tangent: the UV map's u direction (Cycles widens alpha along it for anisotropy > 0)
        tg = g.node("ShaderNodeTangent")
        tg.direction_type = "UV_MAP"
        tg.uv_map = "UVMap"
        g.link((tg, "Tangent"), gl.inputs["Tangent"])
        gl.inputs["Anisotropy"].default_value = m["anisotropy"]
    dk = g.node("ShaderNodeBsdfDiffuse", Color=rgba(m["body"]))
    add = g.node("ShaderNodeAddShader")
    g.link(gl, add.inputs[0])
    g.link(dk, add.inputs[1])
    return add


def conductor(g, m, base, normal=None):
    """pbrt's conductor (rgbscene.conductor): the Metallic BSDF as a physical conductor with per-channel eta, k (exact
    complex Fresnel, closure/bsdf_util.h, as pbrt's FrComplex), single-scattering GGX with the height-correlated
    Smith G (as pbrt's TrowbridgeReitz; not Multiscatter GGX, which adds energy pbrt does not have), Cycles' alpha =
    roughness^2, no thin film. `normal`: a bump map's."""
    if "alpha_texture" in m:
        rough = g.math("POWER", g.math("MAXIMUM", float_texture(g, m["alpha_texture"], base), 0.0), 0.5)
    else:
        rough = math.sqrt(m["alpha"])
    n = g.node("ShaderNodeBsdfMetallic")
    n.distribution = "GGX"
    n.fresnel_type = "PHYSICAL_CONDUCTOR"         # first: IOR and Extinction cannot be looked up until they show
    for k, v in (("Roughness", rough), ("IOR", tuple(m["eta"])), ("Extinction", tuple(m["k"])), ("Thin Film Thickness", 0.0)):
        g.link(v, n.inputs[k])
    if normal is not None:
        g.link(normal, n.inputs["Normal"])
    return n


def material(o, media, base):
    """One object's Blender material. The dispatch: a new material is one more branch (rgbscene.material writes
    its JSON). A bump map's normal is `normal`, passed to the BSDFs that take one."""
    m = o["material"]
    mat = bpy.data.materials.new(o["name"])
    g = Graph(mat)
    textured = any(k in m for k in ("displacement", "alpha_texture", "reflectance_family", "transmittance_family"))
    if textured and o["kind"] not in ("quad", "ply"):
        raise SystemExit(f"{o['name']}: textures need UVs; only quads and plymesh have them here, not {o['kind']}")
    nrm = {}
    if "displacement" in m:
        # pbrt: height in scene units along the normal. The Bump node's Distance scales the height to metres.
        bump = g.node("ShaderNodeBump", Height=float_texture(g, m["displacement"], base))
        bump.inputs["Distance"].default_value = m["displacement_m_per_unit"]
        nrm = {"Normal": bump}
    if m["type"] == "diffuse":
        col = family_colour(g, m["reflectance_family"], base) if "reflectance_family" in m else rgba(m["reflectance"])
        surf = g.node("ShaderNodeBsdfDiffuse", Color=col, **nrm)
    elif m["type"] == "diffusetransmission":     # pbrt's: R/pi on the side of incidence, T/pi through (a leaf)
        R = family_colour(g, m["reflectance_family"], base) if "reflectance_family" in m else rgba(m["reflectance"])
        T = family_colour(g, m["transmittance_family"], base) if "transmittance_family" in m else rgba(m["transmittance"])
        d = g.node("ShaderNodeBsdfDiffuse", Color=R, **nrm)
        t = g.node("ShaderNodeBsdfTranslucent", Color=T, **nrm)
        surf = g.node("ShaderNodeAddShader")
        g.nt.links.new(d.outputs[0], surf.inputs[0])
        g.nt.links.new(t.outputs[0], surf.inputs[1])
    elif m["type"] == "dielectric":
        if "alpha_texture" in m:      # pbrt's alpha = the texture (remaproughness false), Cycles' alpha = roughness^2
            rough = g.math("POWER", g.math("MAXIMUM", float_texture(g, m["alpha_texture"], base), 0.0), 0.5)
        else:
            rough = math.sqrt(m["alpha"])
        surf = g.node("ShaderNodeBsdfGlass", Roughness=rough, IOR=m["eta"], Color=(1, 1, 1, 1), **nrm)
        surf.distribution = "GGX"
    elif m["type"] == "thindielectric":
        if "transmittance" in m or "transmittance_family" in m:      # ours: a film (rgbscene: eta 1 only)
            surf = film(g, m, base, nrm.get("Normal"))
        else:
            surf = thin_dielectric(g, m["eta"], nrm.get("Normal"))
    elif m["type"] == "conductor":
        surf = conductor(g, m, base, nrm.get("Normal"))
    elif m["type"] == "nacreinlay":
        surf = nacre_inlay(g, m, base)
    elif m["type"] == "barbule":
        surf = barbule(g, m)
    else:
        raise SystemExit(f"material {m['type']}")
    if o.get("emission"):
        mat.cycles.emission_sampling = "FRONT"
        E = o["emission"]
        k = max(E)
        em = g.node("ShaderNodeEmission", Color=rgba([e / k for e in E]), Strength=k)
        front = g.node("ShaderNodeAddShader")
        g.nt.links.new(em.outputs[0], front.inputs[0])
        g.nt.links.new(surf.outputs[0], front.inputs[1])
        geo = g.node("ShaderNodeNewGeometry")
        mix = g.node("ShaderNodeMixShader")
        g.nt.links.new(geo.outputs["Backfacing"], mix.inputs[0])
        g.nt.links.new(front.outputs[0], mix.inputs[1])
        g.nt.links.new(surf.outputs[0], mix.inputs[2])           # the back: no emission
        surf = mix
    g.nt.links.new(surf.outputs[0], g.out.inputs["Surface"])
    inside, outside = o.get("inside"), o.get("outside")
    if inside != outside:
        if m["type"] == "dielectric" and inside and not outside:
            md = media[inside]
            v = g.node("ShaderNodeVolumeCoefficients", **{"Absorption Coefficients": md["sigma_a_per_m"],
                                                         "Scatter Coefficients": md["sigma_s_per_m"],
                                                         "Anisotropy": md["g"]})
            v.phase = "HENYEY_GREENSTEIN"
            g.nt.links.new(v.outputs[0], g.out.inputs["Volume"])
        elif m["type"] == "diffuse":
            pass                     # opaque: a medium on either side only bounds it
        else:
            raise SystemExit(f"{o['name']}: medium interface {inside}/{outside} on {m['type']} not handled")
    return mat


# --- objects ---------------------------------------------------------------------------------
def set_uv(me, uv):
    """uv: one (u, v) per vertex, carried onto the loops as the mesh's UV map."""
    uv = np.asarray(uv, np.float32)
    vi = np.empty(len(me.loops), np.int32)
    me.loops.foreach_get("vertex_index", vi)
    layer = me.uv_layers.new(name="UVMap")
    layer.data.foreach_set("uv", uv[vi].ravel())


def mesh_object(name, verts, faces, mat, uv=None):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], [tuple(f) for f in faces])
    me.update()
    if uv is not None:
        set_uv(me, uv)
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    ob.data.materials.append(mat)
    return ob


def ply_object(path, name, mat):
    bpy.ops.object.select_all(action="DESELECT")
    bpy.ops.wm.ply_import(filepath=path)
    ob = bpy.context.selected_objects[0]
    ob.name = name
    # pbrt reads "u","v" or "s","t" (or texture_u/v, texture_s/t) vertex properties; Blender keeps them as attributes
    at = ob.data.attributes
    for a, b in (("u", "v"), ("s", "t"), ("texture_u", "texture_v"), ("texture_s", "texture_t")):
        if a in at and b in at:
            n = len(ob.data.vertices)
            u, v = np.empty(n, np.float32), np.empty(n, np.float32)
            at[a].data.foreach_get("value", u)
            at[b].data.foreach_get("value", v)
            set_uv(ob.data, np.stack([u, v], 1))
            break
    orient_to_normals(ob.data, name)
    ob.data.materials.clear()
    ob.data.materials.append(mat)
    return ob


def orient_to_normals(me, name):
    """pbrt's rule for a mesh with vertex normals: the shading normal decides which side is the front (the
    geometric normal is turned to face it, SetShadingGeometry's orientationIsAuthoritative); Cycles keeps the
    winding's normal, and a shading normal against it loses the reflection of a thin dielectric (docs/slab.md,
    steep films: a mirror kept 55% of its light). So each face whose corner normals point, summed, against its
    winding is turned over, and the vertex normals are set again as they came (only when a face was turned)."""
    if not me.has_custom_normals or not len(me.polygons):
        return
    n = len(me.polygons)
    fn = np.empty(3 * n, np.float64)
    me.polygons.foreach_get("normal", fn)
    cn = np.empty(3 * len(me.loops), np.float64)
    me.corner_normals.foreach_get("vector", cn)
    cn = cn.reshape(-1, 3)
    tot = np.empty(n, np.int32)
    me.polygons.foreach_get("loop_total", tot)
    face = np.repeat(np.arange(n), tot)
    against = np.bincount(face, weights=np.einsum("ij,ij->i", cn, fn.reshape(n, 3)[face]), minlength=n) < 0
    if not against.any():
        return
    vi = np.empty(len(me.loops), np.int32)
    me.loops.foreach_get("vertex_index", vi)
    vn = np.zeros((len(me.vertices), 3))
    vn[vi] = cn                                   # PLY: one normal per vertex
    for i in np.nonzero(against)[0]:
        me.polygons[int(i)].flip()
    me.normals_split_custom_set_from_vertices([tuple(v) for v in vn])
    me.update()
    print(f"{name}: {int(against.sum())} of {n} faces turned over to face their vertex normals (pbrt's orientation)")


def place(ob, o, frame):
    M0 = Matrix(o["matrix"])
    if "matrix_end" not in o:
        ob.matrix_world = M0
        return
    M1 = Matrix(o["matrix_end"])
    for M, f in ((M0, frame - 0.5), (M1, frame + 0.5)):
        ob.matrix_world = M
        ob.keyframe_insert("location", frame=f)
        ob.keyframe_insert("rotation_euler", frame=f)
        ob.keyframe_insert("scale", frame=f)


def camera(c, res):
    cam = bpy.data.cameras.new("cam")
    ob = bpy.data.objects.new("cam", cam)
    bpy.context.scene.collection.objects.link(ob)
    eye, tgt, up = Vector(c["eye"]), Vector(c["target"]), Vector(c["up"])
    z = (eye - tgt).normalized()                 # Blender looks down -Z
    x = up.cross(z).normalized()
    y = z.cross(x)
    R = Matrix((x, y, z)).transposed()
    ob.matrix_world = Matrix.Translation(eye) @ R.to_4x4()
    cam.sensor_fit = "VERTICAL" if res[0] >= res[1] else "HORIZONTAL"
    fov = math.radians(c["fov_short_deg"])
    if cam.sensor_fit == "VERTICAL":
        cam.angle_y = fov
    else:
        cam.angle_x = fov
    cam.clip_start, cam.clip_end = 1e-4, 100.0
    if c.get("lens_radius_m", 0) > 0:
        cam.dof.use_dof = True
        cam.dof.focus_distance = c["focus_m"]
        cam.dof.aperture_fstop = cam.lens * 1e-3 / (2 * c["lens_radius_m"])   # Cycles: radius = lens/(2 N)
        cam.dof.aperture_blades = 0
    bpy.context.scene.camera = ob
    return ob


# --- render ----------------------------------------------------------------------------------
def setup(sc, a, scene):
    s = bpy.context.scene
    s.render.engine = "CYCLES"
    prefs = bpy.context.preferences.addons["cycles"].preferences
    if a.device == "GPU":
        prefs.compute_device_type = "METAL"
        prefs.get_devices()
        for d in prefs.devices:
            d.use = d.type == "METAL"
        if not any(d.use for d in prefs.devices):
            raise SystemExit("no Metal GPU")
    s.cycles.device = a.device
    res = [int(x) for x in a.res.split("x")] if a.res else sc["film"]["res"]
    s.render.resolution_x, s.render.resolution_y = res
    s.render.resolution_percentage = 100
    s.cycles.samples = a.spp or sc.get("spp", 64)
    s.cycles.use_adaptive_sampling = a.adaptive is not None
    if a.adaptive is not None:
        s.cycles.adaptive_threshold = a.adaptive
        s.cycles.adaptive_min_samples = a.min_spp
    s.cycles.time_limit = a.time_limit
    s.cycles.use_denoising = a.denoise
    if a.denoise:
        s.cycles.denoiser = "OPENIMAGEDENOISE"
        s.cycles.denoising_input_passes = "RGB_ALBEDO_NORMAL"
        s.cycles.denoising_prefilter = "ACCURATE"
        s.cycles.denoising_use_gpu = a.device == "GPU"
    d = sc.get("maxdepth", 64)
    s.cycles.max_bounces = d
    for k in ("diffuse_bounces", "glossy_bounces", "transmission_bounces", "volume_bounces", "transparent_max_bounces"):
        setattr(s.cycles, k, d)
    s.cycles.caustics_reflective = s.cycles.caustics_refractive = True
    s.cycles.blur_glossy = 0.0
    s.cycles.sample_clamp_direct = s.cycles.sample_clamp_indirect = 0.0
    s.cycles.use_light_tree = True
    s.cycles.seed = a.seed
    s.cycles.pixel_filter_type = "GAUSSIAN"
    s.cycles.filter_width = 1.5
    s.render.film_transparent = False
    w = bpy.data.worlds.new("black")
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.0
    s.world = w
    sh = sc["camera"].get("shutter", [0, 1])
    s.render.use_motion_blur = any("matrix_end" in o for o in sc["objects"])
    s.render.motion_blur_shutter = sh[1] - sh[0]
    s.render.motion_blur_position = "CENTER"
    s.frame_set(1)
    s.render.image_settings.file_format = "OPEN_EXR"
    s.render.image_settings.color_depth = "32"
    s.render.image_settings.color_mode = "RGB"
    s.render.image_settings.exr_codec = "ZIP"
    return res


def flip_written(path):
    img = bpy.data.images.load(path)
    w, h = img.size
    px = np.empty(w * h * img.channels, np.float32)
    img.pixels.foreach_get(px)
    px = px.reshape(h, w, img.channels)[:, ::-1, :].copy()
    img.pixels.foreach_set(px.ravel())
    img.filepath_raw = path
    img.file_format = "OPEN_EXR"
    img.save()


# --- light groups --------------------------------------------------------------------------
def light_groups(sc):
    """The scene's light groups, in order of appearance; [] if it has none (then nothing here changes the render)."""
    groups = []
    for o in sc["objects"]:
        g = o.get("light_group")
        if g is not None and g not in groups:
            if not re.fullmatch(r"[A-Za-z0-9_]+", g):
                raise SystemExit(f"light group {g!r}: letters, digits and _ only (it names a pass and a file)")
            if g in ("albedo", "normal", "layers"):
                raise SystemExit(f"light group {g!r}: reserved for the denoising passes' files")
            groups.append(g)
    if groups and any(o.get("emission") and o.get("light_group") is None for o in sc["objects"]):
        raise SystemExit("some emitters have no light group: the groups would not add up to the render")
    return groups


def render_groups(out, groups):
    """Render once to a multilayer EXR (all passes), then write the combined image to `out` and each group's pass,
    the denoising albedo and the normal beside it, flipped to pbrt's orientation. Blender 5.2 writes a multilayer
    EXR as one part per pass; Blender's bundled OpenImageIO reads them."""
    import OpenImageIO as oiio
    s = bpy.context.scene
    s.view_layers[0].cycles.denoising_store_passes = True       # "Denoising Albedo", "Denoising Normal"
    st = s.render.image_settings
    st.media_type = "MULTI_LAYER_IMAGE"
    st.file_format = "OPEN_EXR_MULTILAYER"
    st.color_depth = "32"
    st.exr_codec = "ZIP"
    stem = os.path.splitext(out)[0]
    layers = stem + ".layers.exr"
    s.render.filepath = layers
    bpy.ops.render.render(write_still=True)
    inp = oiio.ImageInput.open(layers)
    if inp is None:
        raise SystemExit(f"{layers}: not written")
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
        a = np.ascontiguousarray(parts[key][:, ::-1, :3], np.float32)       # left-right, as flip_written
        spec = oiio.ImageSpec(a.shape[1], a.shape[0], 3, oiio.FLOAT)
        spec.attribute("compression", "zip")
        o = oiio.ImageOutput.create(path)
        if o is None or not o.open(path, spec) or not o.write_image(a):
            raise SystemExit(f"{path}: could not write")
        o.close()
    os.remove(layers)
    return {g: os.path.basename(f"{stem}.{g}.exr") for g in groups}


def main():
    a = args()
    t0 = time.time()
    sc = json.load(open(a.scene))
    base = os.path.dirname(os.path.abspath(a.scene))
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.preferences.edit.keyframe_new_interpolation_type = "LINEAR"   # constant speed over the shutter
    res = setup(sc, a, bpy.context.scene)
    groups = light_groups(sc)
    for g in groups:
        bpy.context.scene.view_layers[0].lightgroups.add(name=g)
    for o in sc["objects"]:
        mat = material(o, sc["media"], base)
        if o["kind"] == "quad":
            ob = mesh_object(o["name"], o["P"], [(0, 1, 3, 2)], mat,       # pbrt's p00 p10 p01 p11
                             o.get("uv", [(0, 0), (1, 0), (0, 1), (1, 1)]))
        elif o["kind"] == "disk":
            n = 256
            verts = [(0.0, 0.0, 0.0)] + [(o["radius"] * math.cos(2 * math.pi * i / n),
                                          o["radius"] * math.sin(2 * math.pi * i / n), 0.0) for i in range(n)]
            ob = mesh_object(o["name"], verts, [(0, 1 + i, 1 + (i + 1) % n) for i in range(n)], mat)
        elif o["kind"] == "ply":
            ob = ply_object(os.path.join(base, o["file"]), o["name"], mat)
        else:
            raise SystemExit(f"object kind {o['kind']}")
        place(ob, o, 1)
        if o.get("light_group"):
            ob.lightgroup = o["light_group"]
    camera(sc["camera"], res)
    t1 = time.time()
    passes = {}
    if groups:
        passes = render_groups(os.path.abspath(a.out), groups)
    else:
        bpy.context.scene.render.filepath = os.path.abspath(a.out)
        bpy.ops.render.render(write_still=True)
    t2 = time.time()
    if not groups:
        flip_written(os.path.abspath(a.out))
    info = {"scene": os.path.abspath(a.scene), "device": a.device, "res": res,
            "spp": bpy.context.scene.cycles.samples, "adaptive": a.adaptive, "min_spp": a.min_spp,
            "denoise": a.denoise, "seed": a.seed, "time_limit": a.time_limit,
            "seconds_build": round(t1 - t0, 2), "seconds_render": round(t2 - t1, 2),
            "blender": bpy.app.version_string}
    if groups:
        info["light_groups"] = passes
        info["denoise_note"] = "the groups are never denoised; --denoise applies to the combined image only"
    with open(os.path.splitext(os.path.abspath(a.out))[0] + ".json", "w") as f:
        json.dump(info, f, indent=1)
    print("CYCLES_DONE", json.dumps(info))


main()
