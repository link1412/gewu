"""Enamel, gilt wire, open air and glass that light comes through, in one surface.

Attributes: col, rough, metal, coat, crough; glass (0..1): plique-a-jour, enamel with nothing behind it; void (0..1): pierced, nothing there.
Glass is a Translucent lobe lit by a real lamp behind the plate, with a little straight-through (Transparent, tinted) and a glossy skin on top. It is a thin sheet, not a solid with refraction: stand-in, chosen for speed, and because each cell is thinner than the frame can resolve.
Voids are Transparent: the backdrop is seen through them, shadows pass.
"""

import bpy


def _attr(nt, name):
    a = nt.nodes.new("ShaderNodeAttribute")
    a.attribute_name = name
    return a


def make(name, p):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    col = _attr(nt, "col").outputs["Color"]

    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(col, b.inputs["Base Color"])
    nt.links.new(_attr(nt, "rough").outputs["Fac"], b.inputs["Roughness"])
    nt.links.new(_attr(nt, "metal").outputs["Fac"], b.inputs["Metallic"])
    b.inputs["Specular IOR Level"].default_value = 0.5
    b.inputs["IOR"].default_value = 1.5
    nt.links.new(_attr(nt, "coat").outputs["Fac"], b.inputs["Coat Weight"])
    nt.links.new(_attr(nt, "crough").outputs["Fac"], b.inputs["Coat Roughness"])
    b.inputs["Coat IOR"].default_value = 1.5

    tl = nt.nodes.new("ShaderNodeBsdfTranslucent")
    nt.links.new(col, tl.inputs["Color"])
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    nt.links.new(col, tr.inputs["Color"])
    mg = nt.nodes.new("ShaderNodeMixShader")
    mg.inputs[0].default_value = float(p.get("through", 0.2))
    nt.links.new(tl.outputs[0], mg.inputs[1])
    nt.links.new(tr.outputs[0], mg.inputs[2])
    # the skin of the glass: a reflection by Fresnel, over the light coming through
    fr = nt.nodes.new("ShaderNodeFresnel")
    fr.inputs["IOR"].default_value = 1.5
    gl = nt.nodes.new("ShaderNodeBsdfAnisotropic")
    gl.inputs["Roughness"].default_value = float(p.get("skin", 0.14))
    gl.inputs["Color"].default_value = (1, 1, 1, 1)
    ms = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(fr.outputs[0], ms.inputs[0])
    nt.links.new(mg.outputs[0], ms.inputs[1])
    nt.links.new(gl.outputs[0], ms.inputs[2])

    m1 = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(_attr(nt, "glass").outputs["Fac"], m1.inputs[0])
    nt.links.new(b.outputs[0], m1.inputs[1])
    nt.links.new(ms.outputs[0], m1.inputs[2])
    hole = nt.nodes.new("ShaderNodeBsdfTransparent")
    hole.inputs["Color"].default_value = (1, 1, 1, 1)
    m2 = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(_attr(nt, "void").outputs["Fac"], m2.inputs[0])
    nt.links.new(m1.outputs[0], m2.inputs[1])
    nt.links.new(hole.outputs[0], m2.inputs[2])
    nt.links.new(m2.outputs[0], out.inputs["Surface"])
    return m
