"""A thin living sheet, a petal or a leaf: a surface that reflects (`col`, with its own gloss and sheen) mixed with light passing through it, scattered (`tr`).

Real light does this: a petal in front of the sun glows, and the shadow of the petal behind it falls on it from the far side. Nothing here is painted to look lit.
Params: k, the share of the light that goes through; rough, spec, sheen, the surface.
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
    tr = nt.nodes.new("ShaderNodeAttribute")
    tr.attribute_name = "tr"
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(col.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = p.get("rough", 0.45)
    b.inputs["Specular IOR Level"].default_value = p.get("spec", 0.4)
    b.inputs["Sheen Weight"].default_value = p.get("sheen", 0.0)
    b.inputs["Sheen Roughness"].default_value = p.get("sheen_rough", 0.5)
    tl = nt.nodes.new("ShaderNodeBsdfTranslucent")
    nt.links.new(tr.outputs["Color"], tl.inputs["Color"])
    mx = nt.nodes.new("ShaderNodeMixShader")
    mx.inputs[0].default_value = p.get("k", 0.4)
    nt.links.new(b.outputs[0], mx.inputs[1])
    nt.links.new(tl.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], out.inputs["Surface"])
    return m
