"""Water standing on a lotus leaf: smooth on top, rough underneath, with dirt in its underside.

The water never touches the leaf. It rests on the tips of the papillae over a film of air, so its underside is a water-air boundary dimpled at a very small scale. A ray in the water meets that boundary at every slope, and wherever the slope is past the critical angle (48.6 degrees for water) it is totally reflected. This is the silver of a drop on a lotus leaf.

A rolling drop picks up the dirt it meets (the lotus effect), and the dirt sits in that underside. So it shows even where the boundary is a mirror and the leaf below cannot be seen: this is why a real drop looks full of specks.

And the film of air is not whole. Where the water has pushed down onto the leaf there is no boundary to reflect from, and the leaf is simply seen: green islands with sharp map-like edges in a field of silver. This is the look of a drop on an old leaf (read off ref/lotus_leaf_drop, as our reading of the photographs, not measured).

Per vertex: rg, the roughness, standing in for the papillae and picked by eye; dc and dw, the colour and cover of the dirt (s64 also paints the far top of a drop dark through these, as a stand-in); wet, where the water touches the leaf, and it is not 0 elsewhere: a little contact everywhere takes the silver from white to cream. A mesh without these attributes reads them as 0: plain rough glass. Params: none.
"""

import bpy


def make(name, p):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    rg = nt.nodes.new("ShaderNodeAttribute")
    rg.attribute_name = "rg"
    g = nt.nodes.new("ShaderNodeBsdfGlass")
    g.distribution = "MULTI_GGX"
    g.inputs["Color"].default_value = (1, 1, 1, 1)
    g.inputs["IOR"].default_value = 1.33
    nt.links.new(rg.outputs["Fac"], g.inputs["Roughness"])
    dc = nt.nodes.new("ShaderNodeAttribute")
    dc.attribute_name = "dc"
    dw = nt.nodes.new("ShaderNodeAttribute")
    dw.attribute_name = "dw"
    df = nt.nodes.new("ShaderNodeBsdfDiffuse")
    nt.links.new(dc.outputs["Color"], df.inputs["Color"])
    wet = nt.nodes.new("ShaderNodeAttribute")
    wet.attribute_name = "wet"
    tp = nt.nodes.new("ShaderNodeBsdfTransparent")
    mw = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(wet.outputs["Fac"], mw.inputs[0])
    nt.links.new(g.outputs[0], mw.inputs[1])
    nt.links.new(tp.outputs[0], mw.inputs[2])
    mx = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(dw.outputs["Fac"], mx.inputs[0])
    nt.links.new(mw.outputs[0], mx.inputs[1])
    nt.links.new(df.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], out.inputs["Surface"])
    return m
