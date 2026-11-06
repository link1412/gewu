"""Shot 70: the water's surface and the tea.

water   One interface, air/water, with Fresnel by Glass; shadow rays pass it, so the wet glaze has direct light that the tea still absorbs on the way (the refraction of that shadow ray is not modelled). The volume is the pale liquor already in the bowl: pure absorption, so colour depends on how far light has come through it.
film    A floating bubble's dome.
tea     The cloud: a Volume object, absorption from the VDB's grids `fine` + `coarse`, in the same units as the liquor.
sigma   Absorption per cm of undiluted tea (r, g, b). Cycles' Volume Absorption removes (1 - colour) * density.
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


def make(name, p):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    if p["kind"] == "water":
        g = nt.nodes.new("ShaderNodeBsdfGlass")
        g.inputs["IOR"].default_value = p["ior"]
        g.inputs["Roughness"].default_value = 0.0
        tr = nt.nodes.new("ShaderNodeBsdfTransparent")
        lp = nt.nodes.new("ShaderNodeLightPath")
        mx = nt.nodes.new("ShaderNodeMixShader")
        nt.links.new(lp.outputs["Is Shadow Ray"], mx.inputs[0])
        nt.links.new(g.outputs[0], mx.inputs[1])
        nt.links.new(tr.outputs[0], mx.inputs[2])
        nt.links.new(mx.outputs[0], out.inputs["Surface"])
        if p.get("liquor"):
            nt.links.new(_absorb(nt, p["sigma"], scale=p["liquor"]).outputs[0], out.inputs["Volume"])
    elif p["kind"] == "film":
        # a bubble's skin: two surfaces very close, so about twice the Fresnel of one, and otherwise clear; shadow rays pass
        tr = nt.nodes.new("ShaderNodeBsdfTransparent")
        gl = nt.nodes.new("ShaderNodeBsdfGlossy")
        gl.inputs["Roughness"].default_value = 0.0
        fr = nt.nodes.new("ShaderNodeFresnel")
        fr.inputs["IOR"].default_value = p["ior"]
        dbl = nt.nodes.new("ShaderNodeMath")
        dbl.operation = "MULTIPLY"
        dbl.use_clamp = True
        dbl.inputs[1].default_value = 2.0
        nt.links.new(fr.outputs[0], dbl.inputs[0])
        mx = nt.nodes.new("ShaderNodeMixShader")
        nt.links.new(dbl.outputs[0], mx.inputs[0])
        nt.links.new(tr.outputs[0], mx.inputs[1])
        nt.links.new(gl.outputs[0], mx.inputs[2])
        nt.links.new(mx.outputs[0], out.inputs["Surface"])
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
    else:
        raise ValueError(p["kind"])
    return m
