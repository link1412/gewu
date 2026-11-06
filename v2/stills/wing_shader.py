"""An insect wing's membrane: clear, so the blurred world shows through it, with a gloss on top that carries a thin-film colour, and a small share of scatter from the fine hairs and the wear (`haze`).

Added, not mixed: Transparent (`tr`) + a black Principled (gloss only, thin film from attribute `film`, in nm). Then mixed by `haze` towards Translucent. Fresnel is what the Principled does on its own; the small energy excess of adding is left in (a stand-in).
"""

import bpy


def make(name, p):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    tr = nt.nodes.new("ShaderNodeAttribute")
    tr.attribute_name = "tr"
    hz = nt.nodes.new("ShaderNodeAttribute")
    hz.attribute_name = "haze"
    fl = nt.nodes.new("ShaderNodeAttribute")
    fl.attribute_name = "film"
    tp = nt.nodes.new("ShaderNodeBsdfTransparent")
    nt.links.new(tr.outputs["Color"], tp.inputs["Color"])
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    b.inputs["Base Color"].default_value = (0, 0, 0, 1)
    b.inputs["Roughness"].default_value = p.get("rough", 0.14)
    b.inputs["Specular IOR Level"].default_value = p.get("spec", 0.5)
    b.inputs["IOR"].default_value = p.get("ior", 1.5)
    nt.links.new(fl.outputs["Fac"], b.inputs["Thin Film Thickness"])
    b.inputs["Thin Film IOR"].default_value = 1.5
    add = nt.nodes.new("ShaderNodeAddShader")
    nt.links.new(tp.outputs[0], add.inputs[0])
    nt.links.new(b.outputs[0], add.inputs[1])
    tl = nt.nodes.new("ShaderNodeBsdfTranslucent")
    tl.inputs["Color"].default_value = (*p.get("haze_rgb", [0.85, 0.72, 0.5]), 1)
    mx = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(hz.outputs["Fac"], mx.inputs[0])
    nt.links.new(add.outputs[0], mx.inputs[1])
    nt.links.new(tl.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], out.inputs["Surface"])
    return m
