"""Barbules of a peacock feather: coloured mirror on a dark melanin ground (shot 45).

SUBSTITUTE, not physics of the real structure. The real colour comes from a 2-D photonic crystal of melanin rods in keratin
(Zi 2003, Yoshioka 2002, Freyer 2020). Here each facet is a rough coloured mirror whose colour is read from a ramp indexed by
an effective Bragg wavelength lam_eff = lam * sqrt(1 - sin^2(th) / n^2) / sqrt(1 - sin^2(th0) / n^2), with th the angle between
view and facet normal (for a mirror the half vector is the normal, so the view is enough) and th0 the angle of the feather's
own plane to the view: `lam` therefore means "the wavelength this barbule shows at this camera's mean angle".
The ramp is hand-made from photographs (it includes the side bands that make brown and pink), not computed from a lattice.

Attributes: lam (nm-like index), amp (reflectance scale). Params: ramp [[lam, r, g, b], ...], n, cos0, rough, base, k_cuticle, rough_c.
"""

import math

import bpy


def make(name, p):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")

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

    lam = nt.nodes.new("ShaderNodeAttribute")
    lam.attribute_name = "lam"
    amp = nt.nodes.new("ShaderNodeAttribute")
    amp.attribute_name = "amp"
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    dot = nt.nodes.new("ShaderNodeVectorMath")
    dot.operation = "DOT_PRODUCT"
    nt.links.new(geo.outputs["True Normal"], dot.inputs[0])
    nt.links.new(geo.outputs["Incoming"], dot.inputs[1])
    c = op("ABSOLUTE", dot.outputs["Value"])

    # the Bragg shift, relative to the mean angle of the feather
    n2 = p.get("n", 1.6) ** 2
    cos0 = p["cos0"]
    k0 = math.sqrt(1.0 - (1.0 - cos0 * cos0) / n2)
    sin2 = op("SUBTRACT", 1.0, op("MULTIPLY", c, c))
    shift = op("DIVIDE", op("SQRT", op("SUBTRACT", 1.0, op("DIVIDE", sin2, n2))), k0)
    lam_eff = op("MULTIPLY", lam.outputs["Fac"], op("POWER", shift, p.get("k_shift", 1.0)))  # k_shift < 1 is a choice for looks, not physics

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
    nt.links.new(amp.outputs["Fac"], tint.inputs["Scale"])

    gl = nt.nodes.new("ShaderNodeBsdfAnisotropic")
    nt.links.new(tint.outputs[0], gl.inputs["Color"])
    gl.inputs["Roughness"].default_value = p.get("rough", 0.3)

    # melanin: the ground under the colour
    df = nt.nodes.new("ShaderNodeBsdfDiffuse")
    df.inputs["Color"].default_value = (*p.get("base", [0.012, 0.008, 0.006]), 1)
    both = nt.nodes.new("ShaderNodeAddShader")
    nt.links.new(gl.outputs[0], both.inputs[0])
    nt.links.new(df.outputs[0], both.inputs[1])

    # the keratin cuticle: a weak colourless gloss on top
    fr = nt.nodes.new("ShaderNodeFresnel")
    fr.inputs["IOR"].default_value = 1.55
    gc = nt.nodes.new("ShaderNodeBsdfAnisotropic")
    gc.inputs["Roughness"].default_value = p.get("rough_c", 0.2)
    mx = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(op("MULTIPLY", fr.outputs[0], p.get("k_cuticle", 0.4)), mx.inputs[0])
    nt.links.new(both.outputs[0], mx.inputs[1])
    nt.links.new(gc.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], out.inputs["Surface"])
    return m
