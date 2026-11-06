"""The ginkgo blade: a thin sheet that scatters most of the light forward, tinted by its pigment (the path through it is longer when it is turned away), with a waxy cuticle.
Same idea as s37_shader.py, with one more attribute: glw, how much cuticle shows at this point. The cuticle takes only the light of the overhead sky scrim: the sun is hidden from gloss.
Attributes: tau, scat, trans, mask, glw."""

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
    att = {}
    for k in ("tau", "scat", "trans", "glw"):
        att[k] = nt.nodes.new("ShaderNodeAttribute")
        att[k].attribute_name = k
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    dot = nt.nodes.new("ShaderNodeVectorMath")
    dot.operation = "DOT_PRODUCT"
    nt.links.new(geo.outputs["Normal"], dot.inputs[0])
    nt.links.new(geo.outputs["Incoming"], dot.inputs[1])
    cos = _math(nt, "MAXIMUM", _math(nt, "ABSOLUTE", dot.outputs["Value"]), p.get("cos_min", 0.3))
    path = _math(nt, "DIVIDE", 1.0, cos)
    depth = _math(nt, "MULTIPLY", _math(nt, "MULTIPLY", att["tau"].outputs["Fac"], p.get("k_tau", 1.0)), path)
    opacity = _math(nt, "SUBTRACT", 1.0, _math(nt, "EXPONENT", _math(nt, "MULTIPLY", depth, -1.0)))
    gamma = nt.nodes.new("ShaderNodeGamma")
    nt.links.new(att["trans"].outputs["Color"], gamma.inputs["Color"])
    nt.links.new(path, gamma.inputs["Gamma"])
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    nt.links.new(gamma.outputs[0], tr.inputs["Color"])
    tl = nt.nodes.new("ShaderNodeBsdfTranslucent")
    nt.links.new(att["scat"].outputs["Color"], tl.inputs["Color"])
    df = nt.nodes.new("ShaderNodeBsdfDiffuse")
    nt.links.new(att["scat"].outputs["Color"], df.inputs["Color"])
    body = _mix(nt, opacity, tr.outputs[0], _mix(nt, _math(nt, "ADD", p.get("front", 0.1), 0.0), tl.outputs[0], df.outputs[0]))
    # Schlick by hand from |cos|. The Fresnel node takes the mesh's facing: this grid's normals point away from the camera, and from behind it reads 1/ior and goes to total reflection past 42 degrees,
    # which painted mirror-like islands all over the leaf (that is the camouflage SHOTS.md warns of on thick translucent sheets)
    f0 = ((p.get("ior", 1.45) - 1) / (p.get("ior", 1.45) + 1)) ** 2
    raw = _math(nt, "ABSOLUTE", dot.outputs["Value"])
    fres = _math(nt, "ADD", f0, _math(nt, "MULTIPLY", 1 - f0, _math(nt, "POWER", _math(nt, "MAXIMUM", _math(nt, "SUBTRACT", 1.0, raw), 0.0), 5.0)))
    gl = nt.nodes.new("ShaderNodeBsdfAnisotropic")
    gl.inputs["Roughness"].default_value = p.get("rough", 0.3)
    w = _math(nt, "MULTIPLY", _math(nt, "MULTIPLY", fres, att["glw"].outputs["Fac"]), p.get("k_gloss", 1.0))
    nt.links.new(_mix(nt, w, body, gl.outputs[0]), out.inputs["Surface"])
    return m
