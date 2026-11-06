"""Silk floss, thread by thread, and its satin ground.

A bundle of parallel filaments is rough across the thread (the facets of its surface point all round it) and smooth along it. So a thread lights up only where the half vector is square to its length, and that is why one shade of floss is bright in one patch and dark in the next. In a microfacet lobe that means a roughness large across the thread and small along it: Principled stretches its lobe along the Tangent input, so `tc`, the direction across the thread, goes there.

Two lobes: the dielectric one from the surface, white; and one tinted by the dye, a metal lobe standing in for the light that enters the filaments and comes out again (silk's triangular section, and the stack of filaments). A translucent part stands in for light through the floss. These two weights are by eye.

Thread attributes (per vertex, soup mesh): n (shading normal), tc (across the thread), col, r.
"""

import bpy
import numpy as np


def _attr(nt, name):
    a = nt.nodes.new("ShaderNodeAttribute")
    a.attribute_name = name
    return a


def make(name, p):
    return (ground if p.get("kind") == "ground" else floss)(name, p)


def floss(name, p):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    n, tc, col, r = _attr(nt, "n"), _attr(nt, "tc"), _attr(nt, "col"), _attr(nt, "r")
    unit = nt.nodes.new("ShaderNodeVectorMath")
    unit.operation = "NORMALIZE"
    nt.links.new(n.outputs["Vector"], unit.inputs[0])

    def lobe(metal, gain):
        b = nt.nodes.new("ShaderNodeBsdfPrincipled")
        nt.links.new(col.outputs["Color"], b.inputs["Base Color"])
        rr = nt.nodes.new("ShaderNodeMath")
        rr.operation = "MULTIPLY"
        nt.links.new(r.outputs["Fac"], rr.inputs[0])
        rr.inputs[1].default_value = gain
        nt.links.new(rr.outputs[0], b.inputs["Roughness"])
        b.inputs["Metallic"].default_value = metal
        b.inputs["Specular IOR Level"].default_value = p.get("spec", 0.45)
        b.inputs["Anisotropic"].default_value = p.get("aniso", 0.92)
        nt.links.new(tc.outputs["Vector"], b.inputs["Tangent"])
        nt.links.new(unit.outputs[0], b.inputs["Normal"])
        return b

    a, b = lobe(0.0, 1.0), lobe(1.0, 1.25)
    mix = nt.nodes.new("ShaderNodeMixShader")
    mix.inputs[0].default_value = p.get("tint", 0.75)
    nt.links.new(a.outputs[0], mix.inputs[1])
    nt.links.new(b.outputs[0], mix.inputs[2])
    tr = nt.nodes.new("ShaderNodeBsdfTranslucent")
    nt.links.new(col.outputs["Color"], tr.inputs["Color"])
    nt.links.new(unit.outputs[0], tr.inputs["Normal"])
    mix2 = nt.nodes.new("ShaderNodeMixShader")
    mix2.inputs[0].default_value = p.get("through", 0.12)
    nt.links.new(mix.outputs[0], mix2.inputs[1])
    nt.links.new(tr.outputs[0], mix2.inputs[2])
    nt.links.new(mix2.outputs[0], out.inputs["Surface"])
    return m


def satin_tile(n=256):
    """Five-end satin: warp floats side by side along v, each bound down once in five picks, the binding points stepping by two warps."""
    u = (np.arange(n) + 0.5) / n * 5.0
    v = (np.arange(n) + 0.5) / n * 5.0
    U, V = np.meshgrid(u, v)
    i = np.floor(U).astype(int)
    fu = U - i
    sec = np.sqrt(np.clip(1.0 - (2.0 * fu - 1.0) ** 2, 0.0, 1.0))
    d = np.mod(V - (2 * i % 5) - 0.5 + 2.5, 5.0) - 2.5  # picks from this warp's binding point
    return (sec * (1.0 - 0.75 * np.exp(-((d / 0.55) ** 2)))).astype(np.float32)


def ground(name, p):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    h = satin_tile()
    img = bpy.data.images.new("satin_tile", h.shape[1], h.shape[0], float_buffer=True, alpha=False)
    img.colorspace_settings.name = "Non-Color"
    img.pixels.foreach_set(np.repeat(h.reshape(-1, 1), 4, 1).reshape(-1))
    img.pack()
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.vector_type = "POINT"
    ang = p.get("warp_rad", 0.32)
    mp.inputs["Rotation"].default_value = (0.0, 0.0, -ang)
    mp.inputs["Scale"].default_value = (1.0 / (5 * p["warp"]), 1.0 / (5 * p["pick"]), 1.0)
    nt.links.new(geo.outputs["Position"], mp.inputs["Vector"])
    tx = nt.nodes.new("ShaderNodeTexImage")
    tx.image = img
    tx.extension = "REPEAT"
    tx.interpolation = "Cubic"
    nt.links.new(mp.outputs[0], tx.inputs["Vector"])
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 1.0
    bump.inputs["Distance"].default_value = p.get("bump", 0.0005)
    nt.links.new(tx.outputs["Color"], bump.inputs["Height"])
    across = nt.nodes.new("ShaderNodeCombineXYZ")
    across.inputs["X"].default_value = float(np.cos(ang))
    across.inputs["Y"].default_value = float(np.sin(ang))
    col = _attr(nt, "col")

    def lobe(metal):
        b = nt.nodes.new("ShaderNodeBsdfPrincipled")
        nt.links.new(col.outputs["Color"], b.inputs["Base Color"])
        b.inputs["Roughness"].default_value = 0.5
        b.inputs["Metallic"].default_value = metal
        b.inputs["Specular IOR Level"].default_value = 0.05
        b.inputs["Anisotropic"].default_value = 0.85
        nt.links.new(across.outputs[0], b.inputs["Tangent"])
        nt.links.new(bump.outputs[0], b.inputs["Normal"])
        return b

    mix = nt.nodes.new("ShaderNodeMixShader")
    mix.inputs[0].default_value = 0.03
    nt.links.new(lobe(0.0).outputs[0], mix.inputs[1])
    nt.links.new(lobe(1.0).outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs["Surface"])
    return m
