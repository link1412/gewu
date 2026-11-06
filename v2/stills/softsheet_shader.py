"""A translucent sheet that may also let some light straight through: oiled paper, a thin leaf, a wing.

Principled (`col`) mixed with Translucent (`tr`, the diffuse part of what passes through) and, by `fw`, a rough Refraction (`tr`): oiled paper shows the bright patch of the sun and the shapes behind it, blurred, and a beam goes on across the dome to fall on the far paper. Nothing painted.
Params: k, fw, rough, spec, sheen, sheen_rough, fw_rough, fw_ior; `smooth` True makes a triangle soup shade smoothly, by wrapping studio_bpy's soup_mesh (a patch of the same kind as s21_sheets: if the studio changes it may break).
"""

import sys

import bpy
import numpy as np


def _smooth_soups():
    g = sys._getframe(2).f_globals
    if "soup_mesh" not in g or getattr(g["soup_mesh"], "_soft", False):
        return
    old = g["soup_mesh"]

    def soft(name, V, F, attrs, mat, smooth=False):
        ob = old(name, V, F, attrs, mat, smooth=smooth)
        ob.data.polygons.foreach_set("use_smooth", np.ones(len(F), dtype=bool))
        ob.data.update()
        return ob

    soft._soft = True
    g["soup_mesh"] = soft


def make(name, p):
    _smooth_soups()
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    col = nt.nodes.new("ShaderNodeAttribute")
    col.attribute_name = "col"
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(col.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = p.get("rough", 0.45)
    b.inputs["Specular IOR Level"].default_value = p.get("spec", 0.4)
    b.inputs["Sheen Weight"].default_value = p.get("sheen", 0.0)
    b.inputs["Sheen Roughness"].default_value = p.get("sheen_rough", 0.5)
    if p.get("metal_attr"):
        a = nt.nodes.new("ShaderNodeAttribute")
        a.attribute_name = p["metal_attr"]
        nt.links.new(a.outputs["Fac"], b.inputs["Metallic"])
    if p.get("rough_attr"):
        a = nt.nodes.new("ShaderNodeAttribute")
        a.attribute_name = p["rough_attr"]
        nt.links.new(a.outputs["Fac"], b.inputs["Roughness"])
    last = b.outputs[0]
    k = p.get("k", 0.0)
    if k > 0 or p.get("k_attr"):
        tr = nt.nodes.new("ShaderNodeAttribute")
        tr.attribute_name = "tr"
        tl = nt.nodes.new("ShaderNodeBsdfTranslucent")
        nt.links.new(tr.outputs["Color"], tl.inputs["Color"])
        mx = nt.nodes.new("ShaderNodeMixShader")
        if p.get("k_attr"):
            a = nt.nodes.new("ShaderNodeAttribute")
            a.attribute_name = p["k_attr"]
            nt.links.new(a.outputs["Fac"], mx.inputs[0])
        else:
            mx.inputs[0].default_value = k
        nt.links.new(last, mx.inputs[1])
        nt.links.new(tl.outputs[0], mx.inputs[2])
        last = mx.outputs[0]
        fw = p.get("fw", 0.0)
        if fw > 0:
            rf = nt.nodes.new("ShaderNodeBsdfRefraction")
            nt.links.new(tr.outputs["Color"], rf.inputs["Color"])
            rf.inputs["Roughness"].default_value = p.get("fw_rough", 0.45)
            rf.inputs["IOR"].default_value = p.get("fw_ior", 1.25)
            mf = nt.nodes.new("ShaderNodeMixShader")
            mf.inputs[0].default_value = fw
            nt.links.new(last, mf.inputs[1])
            nt.links.new(rf.outputs[0], mf.inputs[2])
            last = mf.outputs[0]
    nt.links.new(last, out.inputs["Surface"])
    return m
