"""Shared shader_py for shots 21, 15, 34, 39, 40, 31, 16 (make(name, params), run inside Blender by studio_bpy).

kinds (params["kind"]):
- "sheet": a thin translucent sheet, the logic of s37_shader. Attributes tau, scat, trans, mask; optional gold + dn.
- "pbr": Principled, params["map"] maps inputs to attribute names or constants.
- "fibre": a silk thread: translucent body with an anisotropic-looking sheen. Attributes col, opac (optional).
- "film": a clear membrane with a thin film. Attributes film (nm), mask, col (veins), vein.

Separate strands: studio_bpy.grid_mesh only makes a fully connected grid. With params["strand_k"] = k, the rows of P come
in groups of k and no faces are made between groups, so a thread is really one thread and costs no transparent hits; with
an attribute `keep`, faces with any vertex below 0.5 are dropped. This replaces grid_mesh from inside make(), so that
studio_bpy.py stays untouched.
"""

import sys

import bpy
import numpy as np


def _cut_grid(name, P, attrs, mat, k):
    ny, nx = P.shape[:2]
    idx = np.arange(nx * ny, dtype=np.int32).reshape(ny, nx)
    good = np.ones((ny - 1, nx - 1), bool)
    if k:
        good[np.arange(ny - 1) % k == k - 1] = False
    keep = attrs.pop("keep", None)
    if keep is not None:
        v = keep > 0.5
        good &= v[:-1, :-1] & v[1:, :-1] & v[1:, 1:] & v[:-1, 1:]
    loops = np.stack([idx[:-1, :-1][good], idx[1:, :-1][good], idx[1:, 1:][good], idx[:-1, 1:][good]], -1).ravel()
    nf = loops.size // 4
    me = bpy.data.meshes.new(name)
    me.vertices.add(nx * ny)
    me.vertices.foreach_set("co", P.reshape(-1).astype(np.float32))
    me.loops.add(nf * 4)
    me.loops.foreach_set("vertex_index", loops)
    me.polygons.add(nf)
    me.polygons.foreach_set("loop_start", np.arange(nf, dtype=np.int32) * 4)
    me.update(calc_edges=False)
    me.polygons.foreach_set("use_smooth", np.ones(nf, dtype=bool))
    for a, v in attrs.items():
        if v.ndim == 3:
            at = me.attributes.new(a, "FLOAT_COLOR", "POINT")
            rgba = np.concatenate([v, np.ones(v.shape[:2] + (1,), v.dtype)], -1)
            at.data.foreach_set("color", rgba.reshape(-1).astype(np.float32))
        else:
            at = me.attributes.new(a, "FLOAT", "POINT")
            at.data.foreach_set("value", v.reshape(-1).astype(np.float32))
    me.update()
    me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    return ob


def _patch(name, p):
    g = sys._getframe(2).f_globals  # the globals of studio_bpy.main()
    prev = g["grid_mesh"]
    k = int(p.get("strand_k", 0))

    def grid_mesh(n, P, attrs, mat):
        if n != name:
            return prev(n, P, attrs, mat)
        return _cut_grid(n, P, dict(attrs), mat, k)

    g["grid_mesh"] = grid_mesh


def _math(nt, op, a, b=None, clamp=False):
    n = nt.nodes.new("ShaderNodeMath")
    n.operation = op
    n.use_clamp = clamp
    for i, x in enumerate((a, b)):
        if x is None:
            continue
        if isinstance(x, (int, float)):
            n.inputs[i].default_value = x
        else:
            nt.links.new(x, n.inputs[i])
    return n.outputs[0]


def _mix(nt, fac, a, b):
    n = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(fac, n.inputs[0])
    nt.links.new(a, n.inputs[1])
    nt.links.new(b, n.inputs[2])
    return n.outputs[0]


def _attr(nt, a):
    n = nt.nodes.new("ShaderNodeAttribute")
    n.attribute_name = a
    return n


def _view_cos(nt, cos_min):
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    dot = nt.nodes.new("ShaderNodeVectorMath")
    dot.operation = "DOT_PRODUCT"
    nt.links.new(geo.outputs["Normal"], dot.inputs[0])
    nt.links.new(geo.outputs["Incoming"], dot.inputs[1])
    return _math(nt, "MAXIMUM", _math(nt, "ABSOLUTE", dot.outputs["Value"]), cos_min)


def _sheet(nt, p):
    tau, scat, trans, mask = (_attr(nt, a) for a in ("tau", "scat", "trans", "mask"))
    cos = _view_cos(nt, p.get("cos_min", 0.2))
    path = _math(nt, "DIVIDE", 1.0, cos)
    depth = _math(nt, "MULTIPLY", _math(nt, "MULTIPLY", tau.outputs["Fac"], p.get("k_tau", 1.0)), path)
    opacity = _math(nt, "SUBTRACT", 1.0, _math(nt, "EXPONENT", _math(nt, "MULTIPLY", depth, -1.0)))
    gamma = nt.nodes.new("ShaderNodeGamma")
    nt.links.new(trans.outputs["Color"], gamma.inputs["Color"])
    nt.links.new(path, gamma.inputs["Gamma"])
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    nt.links.new(gamma.outputs[0], tr.inputs["Color"])
    tl = nt.nodes.new("ShaderNodeBsdfTranslucent")
    nt.links.new(scat.outputs["Color"], tl.inputs["Color"])
    df = nt.nodes.new("ShaderNodeBsdfDiffuse")
    nt.links.new(scat.outputs["Color"], df.inputs["Color"])
    front = _math(nt, "ADD", p.get("front", 0.25), 0.0)
    body = _mix(nt, opacity, tr.outputs[0], _mix(nt, front, tl.outputs[0], df.outputs[0]))
    fr = nt.nodes.new("ShaderNodeFresnel")
    fr.inputs["IOR"].default_value = p.get("ior", 1.45)
    gl = nt.nodes.new("ShaderNodeBsdfGlossy")
    gl.inputs["Roughness"].default_value = p.get("rough", 0.3)
    w = _math(nt, "MULTIPLY", _math(nt, "MULTIPLY", fr.outputs[0], mask.outputs["Fac"]), p.get("k_gloss", 0.5))
    out = _mix(nt, w, body, gl.outputs[0])
    if p.get("gold"):
        # leaf: opaque metal on the sheet; each flake has its own tilt (dn, in world axes, 0.5 = none)
        g, dn = _attr(nt, "gold"), _attr(nt, "dn")
        geo = nt.nodes.new("ShaderNodeNewGeometry")
        off = nt.nodes.new("ShaderNodeVectorMath")
        off.operation = "SUBTRACT"
        nt.links.new(dn.outputs["Color"], off.inputs[0])
        off.inputs[1].default_value = (0.5, 0.5, 0.5)
        sc = nt.nodes.new("ShaderNodeVectorMath")
        sc.operation = "SCALE"
        nt.links.new(off.outputs[0], sc.inputs[0])
        sc.inputs["Scale"].default_value = 2.0
        add = nt.nodes.new("ShaderNodeVectorMath")
        add.operation = "ADD"
        nt.links.new(geo.outputs["Normal"], add.inputs[0])
        nt.links.new(sc.outputs[0], add.inputs[1])
        nrm = nt.nodes.new("ShaderNodeVectorMath")
        nrm.operation = "NORMALIZE"
        nt.links.new(add.outputs[0], nrm.inputs[0])
        b = nt.nodes.new("ShaderNodeBsdfPrincipled")
        b.inputs["Base Color"].default_value = (*p.get("gold_rgb", [1.0, 0.72, 0.30]), 1)
        b.inputs["Metallic"].default_value = 1.0
        b.inputs["Roughness"].default_value = p.get("gold_rough", 0.28)
        nt.links.new(nrm.outputs[0], b.inputs["Normal"])
        out = _mix(nt, g.outputs["Fac"], out, b.outputs[0])
    return out


def _pbr(nt, p):
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    for inp, val in p.get("map", {}).items():
        if isinstance(val, str):
            a = _attr(nt, val)
            is_color = inp in ("Base Color", "Emission Color", "Subsurface Radius")
            nt.links.new(a.outputs["Color" if is_color else "Fac"], b.inputs[inp])
        elif isinstance(val, list):
            b.inputs[inp].default_value = (*val, 1)[: len(b.inputs[inp].default_value)]
        else:
            b.inputs[inp].default_value = val
    return b.outputs[0]


def _fibre(nt, p):
    col = _attr(nt, "col")
    tl = nt.nodes.new("ShaderNodeBsdfTranslucent")
    nt.links.new(col.outputs["Color"], tl.inputs["Color"])
    df = nt.nodes.new("ShaderNodeBsdfDiffuse")
    nt.links.new(col.outputs["Color"], df.inputs["Color"])
    body = _mix(nt, _math(nt, "ADD", p.get("front", 0.5), 0.0), tl.outputs[0], df.outputs[0])
    gl = nt.nodes.new("ShaderNodeBsdfGlossy")
    gl.inputs["Roughness"].default_value = p.get("rough", 0.35)
    gl.inputs["Color"].default_value = (*p.get("sheen_rgb", [1.0, 0.97, 0.9]), 1)
    fr = nt.nodes.new("ShaderNodeFresnel")
    fr.inputs["IOR"].default_value = p.get("ior", 1.55)
    return _mix(nt, _math(nt, "MULTIPLY", fr.outputs[0], p.get("k_gloss", 1.0), clamp=True), body, gl.outputs[0])


def _film(nt, p):
    """A clear membrane: thin-film specular only, transparent otherwise. Veins are an opaque translucent layer on top."""
    film, mask, vein, col = _attr(nt, "film"), _attr(nt, "mask"), _attr(nt, "vein"), _attr(nt, "col")
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    b.inputs["Base Color"].default_value = (0.0, 0.0, 0.0, 1)
    b.inputs["Roughness"].default_value = p.get("rough", 0.14)
    b.inputs["IOR"].default_value = p.get("ior", 1.5)
    b.inputs["Specular IOR Level"].default_value = p.get("spec", 0.5)
    b.inputs["Thin Film IOR"].default_value = p.get("film_ior", 1.56)
    nt.links.new(film.outputs["Fac"], b.inputs["Thin Film Thickness"])
    # specular over transparent: add the gloss to a transparent base
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    tr.inputs["Color"].default_value = (*p.get("through", [0.97, 0.95, 0.9]), 1)
    add = nt.nodes.new("ShaderNodeAddShader")
    nt.links.new(tr.outputs[0], add.inputs[0])
    nt.links.new(b.outputs[0], add.inputs[1])
    # the veins
    tl = nt.nodes.new("ShaderNodeBsdfTranslucent")
    nt.links.new(col.outputs["Color"], tl.inputs["Color"])
    df = nt.nodes.new("ShaderNodeBsdfDiffuse")
    nt.links.new(col.outputs["Color"], df.inputs["Color"])
    gl = nt.nodes.new("ShaderNodeBsdfGlossy")
    gl.inputs["Roughness"].default_value = p.get("vein_rough", 0.3)
    gl.inputs["Color"].default_value = (1.0, 0.9, 0.75, 1)
    fr = nt.nodes.new("ShaderNodeFresnel")
    fr.inputs["IOR"].default_value = 1.5
    v = _mix(nt, fr.outputs[0], _mix(nt, _math(nt, "ADD", p.get("vein_front", 0.5), 0.0), tl.outputs[0], df.outputs[0]), gl.outputs[0])
    t0 = nt.nodes.new("ShaderNodeBsdfTransparent")
    hz = nt.nodes.new("ShaderNodeBsdfTranslucent")
    hz.inputs["Color"].default_value = (*p.get("haze_rgb", [1.0, 0.72, 0.4]), 1)
    hazed = _mix(nt, _math(nt, "ADD", p.get("haze", 0.0), 0.0), add.outputs[0], hz.outputs[0])
    body = _mix(nt, mask.outputs["Fac"], t0.outputs[0], hazed)
    return _mix(nt, vein.outputs["Fac"], body, v)


def make(name, p):
    if p.get("strand_k") or p.get("cut"):
        _patch(name, p)
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    s = {"sheet": _sheet, "pbr": _pbr, "fibre": _fibre, "film": _film}[p.get("kind", "sheet")](nt, p)
    nt.links.new(s, out.inputs["Surface"])
    return m
