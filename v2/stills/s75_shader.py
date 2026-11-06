"""Shot 75: the sugar. A clear solid that absorbs by how far light crosses it, so that it stays pale where thin and goes amber where it pools.

Shadow rays pass the sugar without bending, or the fruit under it would get no direct light (as s71_shader): no caustics from the shell yet, a stand-in.
"""

import bpy


def make(name, p):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    g = nt.nodes.new("ShaderNodeBsdfGlass")
    g.inputs["IOR"].default_value = p["ior"]
    g.inputs["Roughness"].default_value = p.get("rough", 0.0)
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    lp = nt.nodes.new("ShaderNodeLightPath")
    mx = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(lp.outputs["Is Shadow Ray"], mx.inputs[0])
    nt.links.new(g.outputs[0], mx.inputs[1])
    nt.links.new(tr.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], out.inputs["Surface"])
    s = p.get("sigma")
    if s:
        d = max(s)
        ab = nt.nodes.new("ShaderNodeVolumeAbsorption")
        ab.inputs["Color"].default_value = (1 - s[0] / d, 1 - s[1] / d, 1 - s[2] / d, 1)
        ab.inputs["Density"].default_value = d
        nt.links.new(ab.outputs[0], out.inputs["Volume"])
    return m
