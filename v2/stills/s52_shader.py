"""The glaze of s52: as glaze_shader's `glaze` (closed shell, transparent + Fresnel gloss, real scattering and absorption), with one change.

glaze_shader's Fresnel node is evaluated from inside too when a ray leaves the shell, where past 42 degrees it says total reflection, and a shadow ray cannot pass a mirror. So anything in the shell seen by the light at more than 42 degrees from the surface's normal has no direct light: a wall of a dish goes black (measured here: the wall of the washer, with a clear glaze, against the same body without the glaze). A real glaze refracts the light on the way in, into that very cone; this model has no refraction, so the reflection has to let it through. Here the Fresnel is the same from both sides.
The other shots with glaze_shader may have the same dark zones; not checked.
"""

import bpy


def _volume(nt, out, p):
    ss, sa = p["sigma_s"], p["sigma_a"]
    d = max(ss)
    sc = nt.nodes.new("ShaderNodeVolumeScatter")
    sc.inputs["Color"].default_value = (ss[0] / d, ss[1] / d, ss[2] / d, 1)
    sc.inputs["Density"].default_value = d
    sc.inputs["Anisotropy"].default_value = p.get("g", 0.6)
    da = max(max(sa), 1e-6)
    ab = nt.nodes.new("ShaderNodeVolumeAbsorption")
    ab.inputs["Color"].default_value = (1 - sa[0] / da, 1 - sa[1] / da, 1 - sa[2] / da, 1)
    ab.inputs["Density"].default_value = da
    add = nt.nodes.new("ShaderNodeAddShader")
    nt.links.new(sc.outputs[0], add.inputs[0])
    nt.links.new(ab.outputs[0], add.inputs[1])
    nt.links.new(add.outputs[0], out.inputs["Volume"])


def make(name, p):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    n = p.get("ior", 1.5)
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    iorv = nt.nodes.new("ShaderNodeMix")  # Cycles flips eta on back faces: this comes out as n both ways
    iorv.data_type = "FLOAT"
    nt.links.new(geo.outputs["Backfacing"], iorv.inputs[0])
    iorv.inputs[2].default_value = n
    iorv.inputs[3].default_value = 1.0 / n
    fr = nt.nodes.new("ShaderNodeFresnel")
    nt.links.new(iorv.outputs[0], fr.inputs["IOR"])
    a = nt.nodes.new("ShaderNodeAttribute")
    a.attribute_name = "rough"
    gl = nt.nodes.new("ShaderNodeBsdfAnisotropic")
    nt.links.new(a.outputs["Fac"], gl.inputs["Roughness"])
    mx = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(fr.outputs[0], mx.inputs[0])
    nt.links.new(tr.outputs[0], mx.inputs[1])
    nt.links.new(gl.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], out.inputs["Surface"])
    _volume(nt, out, p)
    return m
