"""Shot 74's two surfaces. Selected by params["kind"].

skin    The boiled rice skin, a closed solid. Surface: transparent + Fresnel gloss in two lobes, sharp and wide, the same from both sides (as s28_shader: shadow rays pass, so light reaches the medium directly and the noise drops; the cost is no refraction). Volume: scatter + absorption per channel, sigma in 1/cm; with `clear_r` and `clear_k` the scattering thins towards the surface. Attributes: rough; pool (3 channels), the tint the surface gives what passes through it.
filling The black sesame filling, or the thin oil and paste at its edge. Mix of Transparent (`tint`) and a body by `alpha`, so a thin smear is a filter over the skin and a thick one is opaque. The body: a rough paste of ground seed, with fine grit in its normal (`nb`, as n/2 + 1/2), under one Fresnel lobe of oil on the mesh's own normal. Attributes: col, rb, roil (the oil's roughness), alpha, tint, nb.
core    What lies under the skin: dark and matte. Attributes: col.
"""

import bpy


def _attr(nt, name):
    a = nt.nodes.new("ShaderNodeAttribute")
    a.attribute_name = name
    return a


def _skin(m, nt, out, p):
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    nt.links.new(_attr(nt, "pool").outputs["Color"], tr.inputs["Color"])
    n = p.get("ior", 1.36)
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    iorv = nt.nodes.new("ShaderNodeMix")
    iorv.data_type = "FLOAT"
    nt.links.new(geo.outputs["Backfacing"], iorv.inputs[0])
    iorv.inputs[2].default_value = n
    iorv.inputs[3].default_value = 1.0 / n
    fr = nt.nodes.new("ShaderNodeFresnel")
    nt.links.new(iorv.outputs[0], fr.inputs["IOR"])
    gl = nt.nodes.new("ShaderNodeBsdfAnisotropic")
    nt.links.new(_attr(nt, "rough").outputs["Fac"], gl.inputs["Roughness"])
    # a sticky surface: the sharp highlight sits in a wide soft one
    gw = nt.nodes.new("ShaderNodeBsdfAnisotropic")
    gw.inputs["Roughness"].default_value = p.get("haze_rough", 0.28)
    gm = nt.nodes.new("ShaderNodeMixShader")
    gm.inputs[0].default_value = p.get("haze", 0.3)
    nt.links.new(gl.outputs[0], gm.inputs[1])
    nt.links.new(gw.outputs[0], gm.inputs[2])
    mx = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(fr.outputs[0], mx.inputs[0])
    nt.links.new(tr.outputs[0], mx.inputs[1])
    nt.links.new(gm.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], out.inputs["Surface"])
    ss, sa = p["sigma_s"], p["sigma_a"]
    d = max(ss)
    sc = nt.nodes.new("ShaderNodeVolumeScatter")
    sc.inputs["Color"].default_value = (ss[0] / d, ss[1] / d, ss[2] / d, 1)
    sc.inputs["Density"].default_value = d
    if "clear_r" in p:
        # a clear gel at the surface that turns milky with depth, by distance from the centre: no second surface, so no edge between them
        ge = nt.nodes.new("ShaderNodeNewGeometry")
        ln = nt.nodes.new("ShaderNodeVectorMath")
        ln.operation = "LENGTH"
        nt.links.new(ge.outputs["Position"], ln.inputs[0])
        mr = nt.nodes.new("ShaderNodeMapRange")
        mr.interpolation_type = "SMOOTHSTEP"
        nt.links.new(ln.outputs["Value"], mr.inputs["Value"])
        mr.inputs["From Min"].default_value = p["clear_r"][0]
        mr.inputs["From Max"].default_value = p["clear_r"][1]
        mr.inputs["To Min"].default_value = d
        mr.inputs["To Max"].default_value = d * p["clear_k"]
        nt.links.new(mr.outputs["Result"], sc.inputs["Density"])
    sc.inputs["Anisotropy"].default_value = p.get("g", 0.7)
    da = max(max(sa), 1e-6)
    ab = nt.nodes.new("ShaderNodeVolumeAbsorption")
    ab.inputs["Color"].default_value = (1 - sa[0] / da, 1 - sa[1] / da, 1 - sa[2] / da, 1)
    ab.inputs["Density"].default_value = da
    add = nt.nodes.new("ShaderNodeAddShader")
    nt.links.new(sc.outputs[0], add.inputs[0])
    nt.links.new(ab.outputs[0], add.inputs[1])
    nt.links.new(add.outputs[0], out.inputs["Volume"])


def _filling(m, nt, out, p):
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(_attr(nt, "col").outputs["Color"], b.inputs["Base Color"])
    nt.links.new(_attr(nt, "rb").outputs["Fac"], b.inputs["Roughness"])
    b.inputs["Specular IOR Level"].default_value = p.get("spec", 0.05)
    # the paste's normal, decoded; the oil's gloss below is left on the mesh's own
    sub =nt.nodes.new("ShaderNodeVectorMath")
    sub.operation = "SUBTRACT"
    nt.links.new(_attr(nt, "nb").outputs["Vector"], sub.inputs[0])
    sub.inputs[1].default_value = (0.5, 0.5, 0.5)
    nor = nt.nodes.new("ShaderNodeVectorMath")
    nor.operation = "NORMALIZE"
    nt.links.new(sub.outputs[0], nor.inputs[0])
    nt.links.new(nor.outputs[0], b.inputs["Normal"])
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    nt.links.new(_attr(nt, "tint").outputs["Color"], tr.inputs["Color"])
    mx = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(_attr(nt, "alpha").outputs["Fac"], mx.inputs[0])
    nt.links.new(tr.outputs[0], mx.inputs[1])
    nt.links.new(b.outputs[0], mx.inputs[2])
    # oil over everything, the thin edge too: one Fresnel lobe on the mesh's normal, so each bead has its glint
    fr = nt.nodes.new("ShaderNodeFresnel")
    fr.inputs["IOR"].default_value = p.get("oil_ior", 1.47)
    gl = nt.nodes.new("ShaderNodeBsdfAnisotropic")
    nt.links.new(_attr(nt, "roil").outputs["Fac"], gl.inputs["Roughness"])
    top = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(fr.outputs[0], top.inputs[0])
    nt.links.new(mx.outputs[0], top.inputs[1])
    nt.links.new(gl.outputs[0], top.inputs[2])
    nt.links.new(top.outputs[0], out.inputs["Surface"])


def _core(m, nt, out, p):
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(_attr(nt, "col").outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.7
    b.inputs["Specular IOR Level"].default_value = 0.0
    nt.links.new(b.outputs[0], out.inputs["Surface"])


def make(name, p):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    {"skin": _skin, "filling": _filling, "core": _core}[p["kind"]](m, nt, out, p)
    return m
