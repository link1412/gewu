"""Polished old wood, shot 62: runs inside Blender.

Wax on top (Principled coat, dielectric). Under it the wood: a diffuse body, and the light that goes in and comes back off the translucent fibres: a highlight stretched across the fibre, tinted by the wood.
Fibres lean differently from one group of growth years to the next, so this lobe brightens some bands and leaves others dark and swaps them as the camera moves. That is chatoyance, the depth of polished wood.
The lobe is added on top of the Principled, so energy is not strictly kept: its strength `sheen` is chosen by eye (an estimate, not measured).

Attributes: col (albedo), rough, coatr (roughness of the wax), fib (direction of the fibres, world, written as a colour)."""

import bpy


def make(name, p):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    a = {k: nt.nodes.new("ShaderNodeAttribute") for k in ("col", "rough", "coatr", "fib")}
    for k, n in a.items():
        n.attribute_name = k
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(a["col"].outputs["Color"], b.inputs["Base Color"])
    nt.links.new(a["rough"].outputs["Fac"], b.inputs["Roughness"])
    nt.links.new(a["coatr"].outputs["Fac"], b.inputs["Coat Roughness"])
    b.inputs["Specular IOR Level"].default_value = p.get("spec", 0.3)
    b.inputs["Coat Weight"].default_value = p.get("coat", 0.7)
    b.inputs["Coat IOR"].default_value = 1.5
    b.inputs["Subsurface Weight"].default_value = p.get("sss", 0.18)
    b.inputs["Subsurface Radius"].default_value = (1.0, 0.45, 0.18)
    b.inputs["Subsurface Scale"].default_value = 0.05
    g = nt.nodes.new("ShaderNodeBsdfAnisotropic")
    g.distribution = "GGX"
    sc = nt.nodes.new("ShaderNodeVectorMath")
    sc.operation = "SCALE"
    nt.links.new(a["col"].outputs["Color"], sc.inputs[0])
    sc.inputs["Scale"].default_value = p.get("sheen", 1.0)
    nt.links.new(sc.outputs[0], g.inputs["Color"])
    g.inputs["Roughness"].default_value = p.get("sheen_rough", 0.6)
    g.inputs["Anisotropy"].default_value = p.get("sheen_aniso", -0.7)  # negative: stretched across the tangent, which is the fibre
    nt.links.new(a["fib"].outputs["Vector"], g.inputs["Tangent"])
    add = nt.nodes.new("ShaderNodeAddShader")
    nt.links.new(b.outputs[0], add.inputs[0])
    nt.links.new(g.outputs[0], add.inputs[1])
    nt.links.new(add.outputs[0], out.inputs["Surface"])
    return m
