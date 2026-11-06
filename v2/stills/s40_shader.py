"""A cicada's wing close to its base, shot 40. Runs inside Blender. Membrane and veins are one sheet, as they are in the insect.

Membrane: Transparent (`tr`, the smoke) + a black Principled for the gloss, with a thin film (`film`, nm) + a share `haze` of Translucent for the scatter off microtrichia and wear. Added, not mixed; the small energy excess is left in (a stand-in, as in wing_shader).
Vein: a Principled with `col`, mostly opaque; `op` says how much of the sheet is vein at this point. Attributes: tr, haze, film, op, col, rough."""

import bpy


def make(name, p):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    a = {k: nt.nodes.new("ShaderNodeAttribute") for k in ("tr", "haze", "film", "op", "col", "rough")}
    for k, n in a.items():
        n.attribute_name = k
    tp = nt.nodes.new("ShaderNodeBsdfTransparent")
    nt.links.new(a["tr"].outputs["Color"], tp.inputs["Color"])
    g = nt.nodes.new("ShaderNodeBsdfPrincipled")
    g.inputs["Base Color"].default_value = (0, 0, 0, 1)
    nt.links.new(a["rough"].outputs["Fac"], g.inputs["Roughness"])
    g.inputs["Specular IOR Level"].default_value = p.get("spec", 0.4)
    g.inputs["IOR"].default_value = 1.5
    nt.links.new(a["film"].outputs["Fac"], g.inputs["Thin Film Thickness"])
    g.inputs["Thin Film IOR"].default_value = 1.5
    add = nt.nodes.new("ShaderNodeAddShader")
    nt.links.new(tp.outputs[0], add.inputs[0])
    nt.links.new(g.outputs[0], add.inputs[1])
    tl = nt.nodes.new("ShaderNodeBsdfTranslucent")
    tl.inputs["Color"].default_value = (*p.get("haze_rgb", [0.86, 0.74, 0.54]), 1)
    mh = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(a["haze"].outputs["Fac"], mh.inputs[0])
    nt.links.new(add.outputs[0], mh.inputs[1])
    nt.links.new(tl.outputs[0], mh.inputs[2])
    v = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(a["col"].outputs["Color"], v.inputs["Base Color"])
    v.inputs["Roughness"].default_value = p.get("vein_rough", 0.26)
    v.inputs["Specular IOR Level"].default_value = p.get("vein_spec", 0.5)
    mv = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(a["op"].outputs["Fac"], mv.inputs[0])
    nt.links.new(mh.outputs[0], mv.inputs[1])
    nt.links.new(v.outputs[0], mv.inputs[2])
    nt.links.new(mv.outputs[0], out.inputs["Surface"])
    return m
