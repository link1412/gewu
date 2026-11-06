"""A goldfish fin: a thin sheet that scatters a little of the light and lets the rest through, tinted by its pigment.

The optical depth is along the view: a sheet turned edge-on looks denser and brighter, which is what draws the folds.
Attributes: tau (scattering depth at normal incidence), scat and trans (colours), mask (where there is tissue at all).
"""

import bpy


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


def make(name, p):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")

    tau = nt.nodes.new("ShaderNodeAttribute")
    tau.attribute_name = "tau"
    scat = nt.nodes.new("ShaderNodeAttribute")
    scat.attribute_name = "scat"
    trans = nt.nodes.new("ShaderNodeAttribute")
    trans.attribute_name = "trans"
    mask = nt.nodes.new("ShaderNodeAttribute")
    mask.attribute_name = "mask"

    # path length through the sheet
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    dot = nt.nodes.new("ShaderNodeVectorMath")
    dot.operation = "DOT_PRODUCT"
    nt.links.new(geo.outputs["Normal"], dot.inputs[0])
    nt.links.new(geo.outputs["Incoming"], dot.inputs[1])
    cos = _math(nt, "MAXIMUM", _math(nt, "ABSOLUTE", dot.outputs["Value"]), p.get("cos_min", 0.14))
    path = _math(nt, "DIVIDE", 1.0, cos)

    depth = _math(nt, "MULTIPLY", _math(nt, "MULTIPLY", tau.outputs["Fac"], p.get("k_tau", 1.0)), path)
    opacity = _math(nt, "SUBTRACT", 1.0, _math(nt, "EXPONENT", _math(nt, "MULTIPLY", depth, -1.0)))

    # what passes straight through is tinted by the pigment, more so along a longer path
    gamma = nt.nodes.new("ShaderNodeGamma")
    nt.links.new(trans.outputs["Color"], gamma.inputs["Color"])
    nt.links.new(path, gamma.inputs["Gamma"])
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    nt.links.new(gamma.outputs[0], tr.inputs["Color"])

    # what scatters leaves on both sides, mostly forward
    tl = nt.nodes.new("ShaderNodeBsdfTranslucent")
    nt.links.new(scat.outputs["Color"], tl.inputs["Color"])
    df = nt.nodes.new("ShaderNodeBsdfDiffuse")
    nt.links.new(scat.outputs["Color"], df.inputs["Color"])
    front = _math(nt, "ADD", p.get("front", 0.25), 0.0)
    body = _mix(nt, opacity, tr.outputs[0], _mix(nt, front, tl.outputs[0], df.outputs[0]))

    # a wet skin: weak in water, but it catches a broad light at a grazing angle
    fr = nt.nodes.new("ShaderNodeFresnel")
    fr.inputs["IOR"].default_value = p.get("ior", 1.33)
    gl = nt.nodes.new("ShaderNodeBsdfAnisotropic")
    gl.inputs["Roughness"].default_value = p.get("rough", 0.22)
    w = _math(nt, "MULTIPLY", _math(nt, "MULTIPLY", fr.outputs[0], mask.outputs["Fac"]), p.get("k_gloss", 1.0))
    nt.links.new(_mix(nt, w, body, gl.outputs[0]), out.inputs["Surface"])
    return m
