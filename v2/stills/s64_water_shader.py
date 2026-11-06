"""Pond water seen from above: a mirror by Fresnel on the real, rippled surface, over the light that comes back out of the turbid body.

That body lies under the surface, so the ripple must not shade it as it would a wet wall: its diffuse term takes a level normal. Shadows on it still come from the geometry.
Params: ior, rough. Attribute `col`: the body's reflectance.
"""

import bpy


def make(name, p):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    col = nt.nodes.new("ShaderNodeAttribute")
    col.attribute_name = "col"
    up = nt.nodes.new("ShaderNodeCombineXYZ")
    up.inputs["Z"].default_value = 1.0
    dif = nt.nodes.new("ShaderNodeBsdfDiffuse")
    nt.links.new(col.outputs["Color"], dif.inputs["Color"])
    nt.links.new(up.outputs[0], dif.inputs["Normal"])
    gl = nt.nodes.new("ShaderNodeBsdfAnisotropic")
    gl.inputs["Roughness"].default_value = p.get("rough", 0.04)
    gl.inputs["Color"].default_value = (1, 1, 1, 1)
    fr = nt.nodes.new("ShaderNodeFresnel")
    fr.inputs["IOR"].default_value = p.get("ior", 1.33)
    mx = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(fr.outputs[0], mx.inputs[0])
    nt.links.new(dif.outputs[0], mx.inputs[1])
    nt.links.new(gl.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], out.inputs["Surface"])
    return m
