"""A stretched silk: most of the light from inside is scattered through it, and it scatters forward.

Forward scattering is why a lantern is bright where you look straight through it and deep red at its rim:
the radiance falls with the view cosine (cos^k) and the longer path along the view deepens the colour.
Attributes: col (colour of a single pass), tau (optical depth at normal incidence), mask.
"""

import bpy


def _math(nt, op, a, b=None):
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


def make(name, p):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    col = nt.nodes.new("ShaderNodeAttribute")
    col.attribute_name = "col"
    tau = nt.nodes.new("ShaderNodeAttribute")
    tau.attribute_name = "tau"

    geo = nt.nodes.new("ShaderNodeNewGeometry")
    dot = nt.nodes.new("ShaderNodeVectorMath")
    dot.operation = "DOT_PRODUCT"
    nt.links.new(geo.outputs["Normal"], dot.inputs[0])
    nt.links.new(geo.outputs["Incoming"], dot.inputs[1])
    cos = _math(nt, "MAXIMUM", _math(nt, "ABSOLUTE", dot.outputs["Value"]), p.get("cos_min", 0.06))
    path = _math(nt, "DIVIDE", 1.0, cos)

    # the colour deepens along the path
    gamma = nt.nodes.new("ShaderNodeGamma")
    nt.links.new(col.outputs["Color"], gamma.inputs["Color"])
    nt.links.new(_math(nt, "POWER", path, p.get("k_deep", 0.6)), gamma.inputs["Gamma"])

    # and the forward lobe falls off away from the straight-through direction
    fall = _math(nt, "ADD", p.get("floor", 0.2), _math(nt, "MULTIPLY", p.get("peak", 3.0), _math(nt, "POWER", cos, p.get("k_cos", 1.5))))
    mul = nt.nodes.new("ShaderNodeVectorMath")
    mul.operation = "SCALE"
    nt.links.new(gamma.outputs[0], mul.inputs[0])
    nt.links.new(fall, mul.inputs["Scale"])
    tl = nt.nodes.new("ShaderNodeBsdfTranslucent")
    nt.links.new(mul.outputs[0], tl.inputs["Color"])

    # a little goes straight through
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    tr.inputs["Color"].default_value = (*p.get("through", [1.0, 0.25, 0.12]), 1)
    opacity = _math(nt, "SUBTRACT", 1.0, _math(nt, "EXPONENT", _math(nt, "MULTIPLY", _math(nt, "MULTIPLY", tau.outputs["Fac"], path), -1.0)))
    mx = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(opacity, mx.inputs[0])
    nt.links.new(tr.outputs[0], mx.inputs[1])
    nt.links.new(tl.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], out.inputs["Surface"])
    return m
