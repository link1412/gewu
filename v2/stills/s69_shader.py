"""Shader for s69_mutan: Principled driven by vertex attributes, no light sampling of the emissive surface.

A glowing surface of millions of triangles in a light tree costs far more than it gives; a diffuse or glossy ray that happens to hit the glow still collects it, so the light from one coal on the next is real path tracing, found by chance rather than aimed at (same choice as s67).
"""

import bpy


def make(name, p):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    if hasattr(m, "cycles"):
        m.cycles.emission_sampling = "NONE"
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
    b.inputs["Diffuse Roughness"].default_value = 1.0  # a porous surface: flat, with no bright centre
    return m
