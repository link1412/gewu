"""Shot 71: the glass, the water and the tea. Interfaces are told apart by the side a ray hits, so one mesh can hold air/water at the surface and glass/water at the wall.

glass   Air to glass, shadow rays pass.
water   The closed body of water, IOR per vertex (`ior`): air to water on top, glass to water (below 1) at the wall. The volume is the faint liquor.
tea     The cloud: a Volume object, absorption from the VDB's grids `fine` + `coarse`, in the same units as the liquor.
leaf    A soaked tea leaf: dull and dark by reflection, amber with the light behind it, wet on top.
"""

import bpy


def _absorb(nt, sigma, density_socket=None, scale=1.0):
    d = max(sigma)
    ab = nt.nodes.new("ShaderNodeVolumeAbsorption")
    ab.inputs["Color"].default_value = (1 - sigma[0] / d, 1 - sigma[1] / d, 1 - sigma[2] / d, 1)
    if density_socket is None:
        ab.inputs["Density"].default_value = d * scale
    else:
        m = nt.nodes.new("ShaderNodeMath")
        m.operation = "MULTIPLY"
        m.inputs[1].default_value = d * scale
        nt.links.new(density_socket, m.inputs[0])
        nt.links.new(m.outputs[0], ab.inputs["Density"])
    return ab


def _shadow_clear(nt, surface, out):
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    lp = nt.nodes.new("ShaderNodeLightPath")
    mx = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(lp.outputs["Is Shadow Ray"], mx.inputs[0])
    nt.links.new(surface, mx.inputs[1])
    nt.links.new(tr.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], out.inputs["Surface"])


def make(name, p):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    if p["kind"] == "glass":
        g = nt.nodes.new("ShaderNodeBsdfGlass")
        g.inputs["IOR"].default_value = p["ior"]
        g.inputs["Roughness"].default_value = 0.0
        _shadow_clear(nt, g.outputs[0], out)
    elif p["kind"] == "water":
        g = nt.nodes.new("ShaderNodeBsdfGlass")
        g.inputs["Roughness"].default_value = 0.0
        a = nt.nodes.new("ShaderNodeAttribute")
        a.attribute_name = "ior"
        nt.links.new(a.outputs["Fac"], g.inputs["IOR"])
        _shadow_clear(nt, g.outputs[0], out)
        if p.get("liquor"):
            nt.links.new(_absorb(nt, p["sigma"], scale=p["liquor"]).outputs[0], out.inputs["Volume"])
    elif p["kind"] == "tea":
        a = nt.nodes.new("ShaderNodeAttribute")
        a.attribute_type = "GEOMETRY"
        a.attribute_name = "fine"
        b = nt.nodes.new("ShaderNodeAttribute")
        b.attribute_type = "GEOMETRY"
        b.attribute_name = "coarse"
        add = nt.nodes.new("ShaderNodeMath")
        add.operation = "ADD"
        nt.links.new(a.outputs["Fac"], add.inputs[0])
        nt.links.new(b.outputs["Fac"], add.inputs[1])
        nt.links.new(_absorb(nt, p["sigma"], add.outputs[0], p.get("K", 1.0)).outputs[0], out.inputs["Volume"])
    elif p["kind"] == "leaf":
        col = nt.nodes.new("ShaderNodeAttribute")
        col.attribute_name = "col"
        thr = nt.nodes.new("ShaderNodeAttribute")
        thr.attribute_name = "thru"
        pr = nt.nodes.new("ShaderNodeBsdfPrincipled")
        nt.links.new(col.outputs["Color"], pr.inputs["Base Color"])
        pr.inputs["Roughness"].default_value = p.get("rough", 0.38)
        tl = nt.nodes.new("ShaderNodeBsdfTranslucent")
        nt.links.new(thr.outputs["Color"], tl.inputs["Color"])
        mx = nt.nodes.new("ShaderNodeMixShader")
        mx.inputs[0].default_value = p.get("mix", 0.6)
        nt.links.new(pr.outputs[0], mx.inputs[1])
        nt.links.new(tl.outputs[0], mx.inputs[2])
        nt.links.new(mx.outputs[0], out.inputs["Surface"])
    else:
        raise ValueError(p["kind"])
    return m
