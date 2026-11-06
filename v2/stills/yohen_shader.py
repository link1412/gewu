"""Shaders for the yohen glaze (s02, s47). Selected by params["kind"].

under   The fired surface under the glass. Two lobes mixed by `cov` (how much of this pixel the iron-oxide film covers):
        a bare Principled, and one with a real Thin Film (attribute `film`, nm; params film_ior). The colour is true interference: it shifts with the angle
        and it only shows where the surface mirrors something bright.
shell   The glass above it: Fresnel gloss over transparent. Shadow rays pass, so the light still reaches what is under it; no refraction (the cost: the depth reads a little deeper than through n = 1.55).
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
    if p["kind"] == "under":
        col, rough = _attr(nt, "col"), _attr(nt, "rough")
        ior = p.get("ior", 1.55)

        def bsdf(film):
            b = nt.nodes.new("ShaderNodeBsdfPrincipled")
            if not (film and p.get("metal")):
                nt.links.new(col.outputs["Color"], b.inputs["Base Color"])
            nt.links.new(rough.outputs["Fac"], b.inputs["Roughness"])
            b.inputs["IOR"].default_value = ior
            if film:
                b.inputs["Thin Film IOR"].default_value = p.get("film_ior", 2.5)
                nt.links.new(_attr(nt, "film").outputs["Fac"], b.inputs["Thin Film Thickness"])
                if p.get("metal"):
                    # the film lies on an iron-oxide layer, opaque and strongly reflecting: an ESTIMATE that gives the real lustre, a dielectric on glass reflects too little
                    b.inputs["Metallic"].default_value = p["metal"]
                    b.inputs["Base Color"].default_value = (*p.get("metal_rgb", [0.6, 0.6, 0.6]), 1)
            else:
                b.inputs["Specular IOR Level"].default_value = p.get("bare_spec", 0.3)
            return b

        mx = nt.nodes.new("ShaderNodeMixShader")
        nt.links.new(_attr(nt, "cov").outputs["Fac"], mx.inputs[0])
        nt.links.new(bsdf(False).outputs[0], mx.inputs[1])
        nt.links.new(bsdf(True).outputs[0], mx.inputs[2])
        nt.links.new(mx.outputs[0], out.inputs["Surface"])
    elif p["kind"] == "shell":
        # the same from both sides: see skin_fresnel in glaze_shader.py
        n = p.get("ior", 1.55)
        geo = nt.nodes.new("ShaderNodeNewGeometry")
        iorv = nt.nodes.new("ShaderNodeMix")
        iorv.data_type = "FLOAT"
        nt.links.new(geo.outputs["Backfacing"], iorv.inputs[0])
        iorv.inputs[2].default_value = n
        iorv.inputs[3].default_value = 1.0 / n
        fr = nt.nodes.new("ShaderNodeFresnel")
        nt.links.new(iorv.outputs[0], fr.inputs["IOR"])
        tr = nt.nodes.new("ShaderNodeBsdfTransparent")
        gl = nt.nodes.new("ShaderNodeBsdfAnisotropic")
        nt.links.new(_attr(nt, "rough").outputs["Fac"], gl.inputs["Roughness"])
        mx = nt.nodes.new("ShaderNodeMixShader")
        mul = nt.nodes.new("ShaderNodeMath")
        mul.operation = "MULTIPLY"
        nt.links.new(fr.outputs[0], mul.inputs[0])
        nt.links.new(_attr(nt, "on").outputs["Fac"], mul.inputs[1])
        nt.links.new(mul.outputs[0], mx.inputs[0])
        nt.links.new(tr.outputs[0], mx.inputs[1])
        nt.links.new(gl.outputs[0], mx.inputs[2])
        nt.links.new(mx.outputs[0], out.inputs["Surface"])
    else:
        raise ValueError(p["kind"])
    return m
