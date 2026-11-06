"""Shaders for shot 8. params["kind"]: shell is the skin of clear glass above the pattern: Fresnel gloss over a slightly brown transparent, so shadow rays pass and the light reaches the pattern; there is a real gap under it, so the rings part from their reflections and move under the skin. No refraction [the cost: a little less depth than true n = 1.5]. Attribute `cover` is how much of the skin survives; `rough` its roughness."""

import bpy


def make(name, p):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    cov = nt.nodes.new("ShaderNodeAttribute")
    cov.attribute_name = "cover"
    rg = nt.nodes.new("ShaderNodeAttribute")
    rg.attribute_name = "rough"
    fr = nt.nodes.new("ShaderNodeFresnel")
    fr.inputs["IOR"].default_value = p.get("ior", 1.5)
    mul = nt.nodes.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    nt.links.new(fr.outputs[0], mul.inputs[0])
    nt.links.new(cov.outputs["Fac"], mul.inputs[1])
    gl = nt.nodes.new("ShaderNodeBsdfGlossy")
    nt.links.new(rg.outputs["Fac"], gl.inputs["Roughness"])
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    tint = p.get("tint", [0.86, 0.76, 0.66])
    tmix = nt.nodes.new("ShaderNodeMixRGB")  # the worn-through places have no glass to tint the light
    nt.links.new(cov.outputs["Fac"], tmix.inputs[0])
    tmix.inputs[1].default_value = (1, 1, 1, 1)
    tmix.inputs[2].default_value = (*tint, 1)
    nt.links.new(tmix.outputs[0], tr.inputs["Color"])
    mx = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(mul.outputs[0], mx.inputs[0])
    nt.links.new(tr.outputs[0], mx.inputs[1])
    nt.links.new(gl.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], out.inputs["Surface"])
    return m
