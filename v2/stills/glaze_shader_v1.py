"""Shaders for glazed ware with a real medium (shots 29, 6, 11, 26, 28). Selected by params["kind"].

glaze   Closed shell. Surface: transparent + Fresnel gloss (shadow rays pass, so light reaches the medium directly and the noise
        drops by a large factor; the cost is no refraction: depths read about 1.5x deeper than they would through n = 1.5, so
        the scripts scale them). Volume: scatter + absorption per channel, sigma in 1/cm because 1 unit = 1 cm.
crack   A fracture sheet inside the glaze: an air gap seen from glass, so Fresnel at eta 1/n with total reflection; `op` says
        how open the gap is, `pale` how much whitish deposit it holds.
bubble  An air bubble inside the glaze: the same Fresnel, so a bright rim and a clear middle.
layer   A sheet inside the glaze: transparent coloured by `tint`, part diffuse by `milk`, coloured `mcol`. Colorant layers and clouds.
tint    A sheet inside the glaze that filters light: transparent coloured by `tint` (3 channels), used for colorant layers
        (copper red, purple flushes), because a volume cannot read mesh attributes.
"""

import bpy


def _attr(nt, name):
    a = nt.nodes.new("ShaderNodeAttribute")
    a.attribute_name = name
    return a


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


def _inner_fresnel(nt, n_glass):
    """Reflectance of an air gap seen from the glass, on either side of the sheet: TIR beyond the critical angle."""
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    # Cycles flips eta on back faces; give it the value that comes out as 1/n both ways
    iorv = nt.nodes.new("ShaderNodeMix")
    iorv.data_type = "FLOAT"
    nt.links.new(geo.outputs["Backfacing"], iorv.inputs[0])
    iorv.inputs[2].default_value = 1.0 / n_glass
    iorv.inputs[3].default_value = n_glass
    fr = nt.nodes.new("ShaderNodeFresnel")
    nt.links.new(iorv.outputs[0], fr.inputs["IOR"])
    return fr.outputs[0]


def _volume(nt, out, p):
    ss, sa = p["sigma_s"], p["sigma_a"]
    d = max(ss)
    sc = nt.nodes.new("ShaderNodeVolumeScatter")
    sc.inputs["Color"].default_value = (ss[0] / d, ss[1] / d, ss[2] / d, 1)
    sc.inputs["Density"].default_value = d
    sc.inputs["Anisotropy"].default_value = p.get("g", 0.6)
    da = max(max(sa), 1e-6)
    ab = nt.nodes.new("ShaderNodeVolumeAbsorption")
    ab.inputs["Color"].default_value = (1 - sa[0] / da, 1 - sa[1] / da, 1 - sa[2] / da, 1)
    ab.inputs["Density"].default_value = da
    add = nt.nodes.new("ShaderNodeAddShader")
    nt.links.new(sc.outputs[0], add.inputs[0])
    nt.links.new(ab.outputs[0], add.inputs[1])
    nt.links.new(add.outputs[0], out.inputs["Volume"])


def make(name, p):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    kind = p["kind"]
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    if kind == "glaze":
        fr = nt.nodes.new("ShaderNodeFresnel")
        fr.inputs["IOR"].default_value = p.get("ior", 1.5)
        gl = nt.nodes.new("ShaderNodeBsdfAnisotropic")
        nt.links.new(_attr(nt, "rough").outputs["Fac"], gl.inputs["Roughness"])
        mx = nt.nodes.new("ShaderNodeMixShader")
        nt.links.new(fr.outputs[0], mx.inputs[0])
        nt.links.new(tr.outputs[0], mx.inputs[1])
        nt.links.new(gl.outputs[0], mx.inputs[2])
        nt.links.new(mx.outputs[0], out.inputs["Surface"])
        _volume(nt, out, p)
    elif kind == "crack":
        f = _inner_fresnel(nt, p.get("ior", 1.5))
        gl = nt.nodes.new("ShaderNodeBsdfAnisotropic")
        gl.inputs["Roughness"].default_value = p.get("rough", 0.12)
        op = _attr(nt, "op").outputs["Fac"]
        pale = _attr(nt, "pale").outputs["Fac"]
        di = nt.nodes.new("ShaderNodeBsdfDiffuse")
        di.inputs["Color"].default_value = (*p.get("pale_rgb", [0.85, 0.82, 0.72]), 1)
        a = nt.nodes.new("ShaderNodeMixShader")
        nt.links.new(_math(nt, "MULTIPLY", f, op), a.inputs[0])
        nt.links.new(tr.outputs[0], a.inputs[1])
        nt.links.new(gl.outputs[0], a.inputs[2])
        b = nt.nodes.new("ShaderNodeMixShader")
        nt.links.new(pale, b.inputs[0])
        nt.links.new(a.outputs[0], b.inputs[1])
        nt.links.new(di.outputs[0], b.inputs[2])
        nt.links.new(b.outputs[0], out.inputs["Surface"])
    elif kind == "bubble":
        f = _inner_fresnel(nt, p.get("ior", 1.5))
        gl = nt.nodes.new("ShaderNodeBsdfAnisotropic")
        gl.inputs["Roughness"].default_value = 0.03
        a = nt.nodes.new("ShaderNodeMixShader")
        nt.links.new(f, a.inputs[0])
        nt.links.new(tr.outputs[0], a.inputs[1])
        nt.links.new(gl.outputs[0], a.inputs[2])
        nt.links.new(a.outputs[0], out.inputs["Surface"])
    elif kind == "tint":
        ca = _attr(nt, "tint")
        nt.links.new(ca.outputs["Color"], tr.inputs["Color"])
        nt.links.new(tr.outputs[0], out.inputs["Surface"])
    elif kind == "layer":
        # a colorant or a cloud inside the glaze: `tint` filters what passes, `milk` of it is a white scatterer coloured `mcol`
        nt.links.new(_attr(nt, "tint").outputs["Color"], tr.inputs["Color"])
        di = nt.nodes.new("ShaderNodeBsdfDiffuse")
        nt.links.new(_attr(nt, "mcol").outputs["Color"], di.inputs["Color"])
        a = nt.nodes.new("ShaderNodeMixShader")
        nt.links.new(_attr(nt, "milk").outputs["Fac"], a.inputs[0])
        nt.links.new(tr.outputs[0], a.inputs[1])
        nt.links.new(di.outputs[0], a.inputs[2])
        nt.links.new(a.outputs[0], out.inputs["Surface"])
    else:
        raise ValueError(kind)
    return m
