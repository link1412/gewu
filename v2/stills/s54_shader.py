"""Two materials for the lantern.

paper: stretched paper lit from inside. The colour attribute `col` already carries the forward lobe and the deepening along the path, worked out per vertex for this camera and
       flame. `amb` is the light that has bounced around inside the lantern, which keeps a shadow from going black; it is a stand-in for those bounces, as there is no inner wall.
gobo:  a surface that only filters light: paper cut-outs, coloured film and bamboo, by the colour attribute `T` (white = open).
"""

import bpy


def make(name, p):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    if p.get("kind") == "gobo":
        t = nt.nodes.new("ShaderNodeAttribute")
        t.attribute_name = "T"
        tr = nt.nodes.new("ShaderNodeBsdfTransparent")
        nt.links.new(t.outputs["Color"], tr.inputs["Color"])
        nt.links.new(tr.outputs[0], out.inputs["Surface"])
        return m
    col = nt.nodes.new("ShaderNodeAttribute")
    col.attribute_name = "col"
    tl = nt.nodes.new("ShaderNodeBsdfTranslucent")
    nt.links.new(col.outputs["Color"], tl.inputs["Color"])
    em = nt.nodes.new("ShaderNodeEmission")
    nt.links.new(col.outputs["Color"], em.inputs["Color"])
    em.inputs["Strength"].default_value = p.get("amb", 0.01)
    add = nt.nodes.new("ShaderNodeAddShader")
    nt.links.new(tl.outputs[0], add.inputs[0])
    nt.links.new(em.outputs[0], add.inputs[1])
    nt.links.new(add.outputs[0], out.inputs["Surface"])
    return m
