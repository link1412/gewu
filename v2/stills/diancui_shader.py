"""Kingfisher feather and old silver-gilt on one mesh (s55). The feather's colour is an angle-dependent reflection, not a paint.

SUBSTITUTE, not the physics of the structure: a satin coloured lobe plus a broad coloured scatter, tinted from a ramp indexed by lam_eff = lam * (sqrt(1 - sin^2(th)/n^2) / the same at the mean angle) ^ k_shift, with th the angle between the view and the
surface normal, on a dark melanin ground, under a weak keratin gloss. Since the normal follows each barb's real relief, hue moves across a barb, between barbs and between snips. The ramp is by eye, from ref/diancui.

Attributes: fm feather mask, lam (nm-like), amp (reflectance scale), col, rough, metal, alpha. Params: ramp [[lam, r, g, b], ...], n, cos0 (the plaque's angle to the view), k_shift, rough, k_scatter, base, k_cuticle, rough_c.
"""

import math

import bpy


def make(name, p):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")

    def attr(a):
        n = nt.nodes.new("ShaderNodeAttribute")
        n.attribute_name = a
        return n

    def op(kind, a, b=None):
        n = nt.nodes.new("ShaderNodeMath")
        n.operation = kind
        for i, x in enumerate((a, b)):
            if x is None:
                continue
            if isinstance(x, (int, float)):
                n.inputs[i].default_value = x
            else:
                nt.links.new(x, n.inputs[i])
        return n.outputs[0]

    geo = nt.nodes.new("ShaderNodeNewGeometry")
    dot = nt.nodes.new("ShaderNodeVectorMath")
    dot.operation = "DOT_PRODUCT"
    nt.links.new(geo.outputs["Normal"], dot.inputs[0])
    nt.links.new(geo.outputs["Incoming"], dot.inputs[1])
    c = op("ABSOLUTE", dot.outputs["Value"])
    n2 = p.get("n", 1.45) ** 2
    sin2 = op("SUBTRACT", 1.0, op("MULTIPLY", c, c))
    k0 = math.sqrt(1.0 - (1.0 - p["cos0"] ** 2) / n2)
    shift = op("DIVIDE", op("SQRT", op("SUBTRACT", 1.0, op("DIVIDE", sin2, n2))), k0)
    lam_eff = op("MULTIPLY", attr("lam").outputs["Fac"], op("POWER", shift, p.get("k_shift", 1.0)))  # relative to the mean angle, so lam means the colour shown from this camera; k_shift < 1 is a choice for looks

    ramp = p["ramp"]
    lo, hi = ramp[0][0], ramp[-1][0]
    rng = nt.nodes.new("ShaderNodeMapRange")
    rng.inputs["From Min"].default_value = lo
    rng.inputs["From Max"].default_value = hi
    rng.clamp = True
    nt.links.new(lam_eff, rng.inputs["Value"])
    cr = nt.nodes.new("ShaderNodeValToRGB")
    els = cr.color_ramp.elements
    while len(els) < len(ramp):
        els.new(0.5)
    for e, (l, r, g, b) in zip(els, ramp):
        e.position = (l - lo) / (hi - lo)
        e.color = (r, g, b, 1)
    nt.links.new(rng.outputs[0], cr.inputs["Fac"])
    tint = nt.nodes.new("ShaderNodeVectorMath")
    tint.operation = "SCALE"
    nt.links.new(cr.outputs["Color"], tint.inputs[0])
    nt.links.new(attr("amp").outputs["Fac"], tint.inputs["Scale"])

    gl = nt.nodes.new("ShaderNodeBsdfAnisotropic")
    nt.links.new(tint.outputs[0], gl.inputs["Color"])
    gl.inputs["Roughness"].default_value = p.get("rough", 0.36)
    # the spongy layer scatters broadly: this is what keeps a snip blue when no light mirrors in it
    sc = nt.nodes.new("ShaderNodeVectorMath")
    sc.operation = "SCALE"
    nt.links.new(tint.outputs[0], sc.inputs[0])
    sc.inputs["Scale"].default_value = p.get("k_scatter", 0.5)
    df = nt.nodes.new("ShaderNodeBsdfDiffuse")
    nt.links.new(sc.outputs[0], df.inputs["Color"])
    add = nt.nodes.new("ShaderNodeAddShader")
    nt.links.new(gl.outputs[0], add.inputs[0])
    nt.links.new(df.outputs[0], add.inputs[1])
    base = nt.nodes.new("ShaderNodeBsdfDiffuse")
    base.inputs["Color"].default_value = (*p.get("base", [0.01, 0.009, 0.012]), 1)
    add2 = nt.nodes.new("ShaderNodeAddShader")
    nt.links.new(add.outputs[0], add2.inputs[0])
    nt.links.new(base.outputs[0], add2.inputs[1])
    fr = nt.nodes.new("ShaderNodeFresnel")
    fr.inputs["IOR"].default_value = 1.55
    gc = nt.nodes.new("ShaderNodeBsdfAnisotropic")
    gc.inputs["Roughness"].default_value = p.get("rough_c", 0.26)
    mx = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(op("MULTIPLY", fr.outputs[0], p.get("k_cuticle", 0.5)), mx.inputs[0])
    nt.links.new(add2.outputs[0], mx.inputs[1])
    nt.links.new(gc.outputs[0], mx.inputs[2])

    # metal, backing, coral
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(attr("col").outputs["Color"], b.inputs["Base Color"])
    nt.links.new(attr("rough").outputs["Fac"], b.inputs["Roughness"])
    nt.links.new(attr("metal").outputs["Fac"], b.inputs["Metallic"])

    both = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(attr("fm").outputs["Fac"], both.inputs[0])
    nt.links.new(b.outputs[0], both.inputs[1])
    nt.links.new(mx.outputs[0], both.inputs[2])
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    top = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(attr("alpha").outputs["Fac"], top.inputs[0])
    nt.links.new(tr.outputs[0], top.inputs[1])
    nt.links.new(both.outputs[0], top.inputs[2])
    nt.links.new(top.outputs[0], out.inputs["Surface"])
    return m
