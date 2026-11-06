"""Dehua glaze for shot 28: glaze_shader's closed shell with a real medium, plus glaze pooled in the recesses: the transparent part of the surface takes its colour from
the vertex attribute `pool` (thick glaze reads faintly grey-green-cream). Attributes: rough, pool. The medium's sigma are params, as in glaze_shader."""

import bpy


def make(name, p):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    pool = nt.nodes.new("ShaderNodeAttribute")
    pool.attribute_name = "pool"
    nt.links.new(pool.outputs["Color"], tr.inputs["Color"])
    rough = nt.nodes.new("ShaderNodeAttribute")
    rough.attribute_name = "rough"
    # the same from both sides: see skin_fresnel in glaze_shader.py
    n = p.get("ior", 1.5)
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    iorv = nt.nodes.new("ShaderNodeMix")
    iorv.data_type = "FLOAT"
    nt.links.new(geo.outputs["Backfacing"], iorv.inputs[0])
    iorv.inputs[2].default_value = n
    iorv.inputs[3].default_value = 1.0 / n
    fr = nt.nodes.new("ShaderNodeFresnel")
    nt.links.new(iorv.outputs[0], fr.inputs["IOR"])
    gl = nt.nodes.new("ShaderNodeBsdfAnisotropic")
    nt.links.new(rough.outputs["Fac"], gl.inputs["Roughness"])
    mx = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(fr.outputs[0], mx.inputs[0])
    nt.links.new(tr.outputs[0], mx.inputs[1])
    nt.links.new(gl.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], out.inputs["Surface"])
    ss, sa = p["sigma_s"], p["sigma_a"]
    d = max(ss)
    sc = nt.nodes.new("ShaderNodeVolumeScatter")
    sc.inputs["Color"].default_value = (ss[0] / d, ss[1] / d, ss[2] / d, 1)
    sc.inputs["Density"].default_value = d
    sc.inputs["Anisotropy"].default_value = p.get("g", 0.3)
    da = max(max(sa), 1e-6)
    ab = nt.nodes.new("ShaderNodeVolumeAbsorption")
    ab.inputs["Color"].default_value = (1 - sa[0] / da, 1 - sa[1] / da, 1 - sa[2] / da, 1)
    ab.inputs["Density"].default_value = da
    add = nt.nodes.new("ShaderNodeAddShader")
    nt.links.new(sc.outputs[0], add.inputs[0])
    nt.links.new(ab.outputs[0], add.inputs[1])
    nt.links.new(add.outputs[0], out.inputs["Volume"])
    return m
