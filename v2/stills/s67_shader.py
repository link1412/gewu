"""Shaders for s67_mutan.

kind "char": Principled driven by vertex attributes (col, emit, rough, spec), with emission importance sampling off. The face has millions of glowing triangles; a light tree over them costs
far more than it gives. Neighbouring coals are still lit by that glow: a diffuse or glossy ray that happens to hit it collects it. So the glow on the next block is real path tracing, only found by chance rather than aimed at.

kind "card": a flame already integrated along the line of sight (s67_mutan.flame_card). Attribute fc is added to what is behind, and the ray passes straight on.
"""

import bpy


def make(name, p):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    if hasattr(m, "cycles"):
        m.cycles.emission_sampling = "NONE"
    if p.get("kind") == "card":
        nt.nodes.clear()
        out = nt.nodes.new("ShaderNodeOutputMaterial")
        at = nt.nodes.new("ShaderNodeAttribute")
        at.attribute_name = "fc"
        em = nt.nodes.new("ShaderNodeEmission")
        nt.links.new(at.outputs["Color"], em.inputs["Color"])
        em.inputs["Strength"].default_value = 1.0
        tr = nt.nodes.new("ShaderNodeBsdfTransparent")
        tr.inputs["Color"].default_value = (1, 1, 1, 1)
        add = nt.nodes.new("ShaderNodeAddShader")
        nt.links.new(em.outputs[0], add.inputs[0])
        nt.links.new(tr.outputs[0], add.inputs[1])
        nt.links.new(add.outputs[0], out.inputs["Surface"])
        return m
    b = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")

    def attr(inp, a_name, socket="Fac"):
        a = nt.nodes.new("ShaderNodeAttribute")
        a.attribute_name = a_name
        nt.links.new(a.outputs[socket], b.inputs[inp])

    attr("Base Color", "col", "Color")
    attr("Emission Color", "emit", "Color")
    b.inputs["Emission Strength"].default_value = 1.0
    attr("Roughness", "rough")
    attr("Specular IOR Level", "spec")
    return m
