"""A living petal, for s39_cand.py: reflected light with a velvet sheen, light scattered through the tissue, and a little light that goes straight through.

The straight part is a coloured Transparent closure. It is the only closure a shadow ray can pass in Cycles, so a petal's shadow on the next one is pink and not grey, and an edge behind shows through softly. Real tissue scatters forward in a lobe; a straight share is the stand-in for that lobe.
Maps come as image files, per petal, in the plan of that petal (one texel about 0.1 mm), and the mesh stays coarse so that it can move:
    col: reflectance, tr: colour of the transmitted light, aux: R height (cm x 10, 0.5 is flat), G the scattered share k, B the straight share t.
Params: col, tr, aux (paths), rough, spec, sheen, sheen_rough, bump (Bump distance, cm).
"""

import bpy


def make(name, p):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    uv = nt.nodes.new("ShaderNodeAttribute")
    uv.attribute_name = "uvw"

    def tex(key):
        n = nt.nodes.new("ShaderNodeTexImage")
        img = bpy.data.images.load(p[key])
        img.colorspace_settings.name = "Non-Color"
        n.image = img
        n.extension = "EXTEND"
        n.interpolation = "Linear"
        nt.links.new(uv.outputs["Vector"], n.inputs["Vector"])
        return n

    col, tr, aux = tex("col"), tex("tr"), tex("aux")
    sep = nt.nodes.new("ShaderNodeSeparateColor")
    nt.links.new(aux.outputs["Color"], sep.inputs[0])
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 1.0
    bump.inputs["Distance"].default_value = p.get("bump", 0.06)
    nt.links.new(sep.outputs[0], bump.inputs["Height"])
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(col.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = p.get("rough", 0.55)
    b.inputs["Specular IOR Level"].default_value = p.get("spec", 0.25)
    b.inputs["Sheen Weight"].default_value = p.get("sheen", 0.6)
    b.inputs["Sheen Roughness"].default_value = p.get("sheen_rough", 0.5)
    nt.links.new(bump.outputs[0], b.inputs["Normal"])
    tl = nt.nodes.new("ShaderNodeBsdfTranslucent")
    nt.links.new(tr.outputs["Color"], tl.inputs["Color"])
    nt.links.new(bump.outputs[0], tl.inputs["Normal"])
    mx = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(sep.outputs[1], mx.inputs[0])
    nt.links.new(b.outputs[0], mx.inputs[1])
    nt.links.new(tl.outputs[0], mx.inputs[2])
    tp = nt.nodes.new("ShaderNodeBsdfTransparent")
    nt.links.new(tr.outputs["Color"], tp.inputs["Color"])
    mt = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(sep.outputs[2], mt.inputs[0])
    nt.links.new(mx.outputs[0], mt.inputs[1])
    nt.links.new(tp.outputs[0], mt.inputs[2])
    nt.links.new(mt.outputs[0], out.inputs["Surface"])
    return m
