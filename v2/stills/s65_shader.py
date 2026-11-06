"""Shaders for shot 65. params["kind"]:

paper   the outside of an oiled paper sheet. Under the oil: Principled (`col`), mixed with Translucent and a little rough Refraction (`tr`), as softsheet_shader. Over it a real dielectric film of tung oil: a Glossy mixed in by the Fresnel factor times the film's cover (`film`), roughness `rough`, so the sheen falls off with angle and the body colour is not washed out where the film reflects little. A very fine bump (noise in object space, so it turns with the sheet).
water   clear water. Glass, IOR 1.33; soups shade smoothly.

Also: studio_bpy.take uses `Quaternion` in spin_pose without importing it, so a spin dies with a NameError. Until that is fixed there, make() puts it in the studio's globals. It does nothing once the studio has it.
Numbers are estimates set by eye.
"""

import sys

import bpy
import numpy as np


def _studio_patch():
    g = sys._getframe(2).f_globals
    if "take" not in g:
        return
    if "Quaternion" not in g:
        from mathutils import Quaternion

        g["Quaternion"] = Quaternion
    if "soup_mesh" in g and not getattr(g["soup_mesh"], "_soft", False):
        old = g["soup_mesh"]

        def soft(name, V, F, attrs, mat):
            ob = old(name, V, F, attrs, mat)
            ob.data.polygons.foreach_set("use_smooth", np.ones(len(F), dtype=bool))
            ob.data.update()
            return ob

        soft._soft = True
        g["soup_mesh"] = soft


def _attr(nt, name, out="Color"):
    a = nt.nodes.new("ShaderNodeAttribute")
    a.attribute_name = name
    return a.outputs[out]


def paper(nt, out, p):
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(_attr(nt, "col"), b.inputs["Base Color"])
    rough = _attr(nt, "rough", "Fac")
    b.inputs["Roughness"].default_value = 0.5
    b.inputs["Specular IOR Level"].default_value = p.get("spec", 0.1)
    # very fine cockle of the sheet, in the object's own space
    tc = nt.nodes.new("ShaderNodeTexCoord").outputs["Object"]
    n1 = nt.nodes.new("ShaderNodeTexNoise")
    nt.links.new(tc, n1.inputs["Vector"])
    n1.inputs["Scale"].default_value = p.get("cockle_scale", 6.0)
    n1.inputs["Detail"].default_value = 4.0
    n1.inputs["Roughness"].default_value = 0.55
    bump = nt.nodes.new("ShaderNodeBump")
    nt.links.new(n1.outputs[0], bump.inputs["Height"])
    bump.inputs["Distance"].default_value = p.get("wr", 0.012)
    bump.inputs["Strength"].default_value = 1.0
    nrm = bump.outputs[0]
    nt.links.new(nrm, b.inputs["Normal"])
    tl = nt.nodes.new("ShaderNodeBsdfTranslucent")
    nt.links.new(_attr(nt, "tr"), tl.inputs["Color"])
    mx = nt.nodes.new("ShaderNodeMixShader")
    mx.inputs[0].default_value = p.get("k", 0.42)
    nt.links.new(b.outputs[0], mx.inputs[1])
    nt.links.new(tl.outputs[0], mx.inputs[2])
    last = mx.outputs[0]
    if p.get("fw", 0) > 0:
        rf = nt.nodes.new("ShaderNodeBsdfRefraction")
        nt.links.new(_attr(nt, "tr"), rf.inputs["Color"])
        rf.inputs["Roughness"].default_value = p.get("fw_rough", 0.42)
        rf.inputs["IOR"].default_value = p.get("fw_ior", 1.22)
        mf = nt.nodes.new("ShaderNodeMixShader")
        mf.inputs[0].default_value = p["fw"]
        nt.links.new(last, mf.inputs[1])
        nt.links.new(rf.outputs[0], mf.inputs[2])
        last = mf.outputs[0]
    # the oil film
    fr = nt.nodes.new("ShaderNodeFresnel")
    fr.inputs["IOR"].default_value = p.get("coat_ior", 1.5)
    nt.links.new(nrm, fr.inputs["Normal"])
    mul = nt.nodes.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    nt.links.new(fr.outputs[0], mul.inputs[0])
    nt.links.new(_attr(nt, "film", "Fac"), mul.inputs[1])
    gl = nt.nodes.new("ShaderNodeBsdfGlossy")
    gl.inputs["Color"].default_value = (1, 1, 1, 1)
    nt.links.new(rough, gl.inputs["Roughness"])
    nt.links.new(nrm, gl.inputs["Normal"])
    mc = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(mul.outputs[0], mc.inputs[0])
    nt.links.new(last, mc.inputs[1])
    nt.links.new(gl.outputs[0], mc.inputs[2])
    nt.links.new(mc.outputs[0], out.inputs["Surface"])


def water(nt, out, p):
    g = nt.nodes.new("ShaderNodeBsdfGlass")
    g.inputs["Roughness"].default_value = 0.0
    g.inputs["IOR"].default_value = p.get("ior", 1.33)
    nt.links.new(g.outputs[0], out.inputs["Surface"])


def make(name, p):
    _studio_patch()
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    {"paper": paper, "water": water}[p["kind"]](nt, out, p)
    return m
