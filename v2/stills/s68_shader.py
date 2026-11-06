"""Shot 68: the cup and the water, in the two passes that the compositor needs.

Pass R: the camera sees the cup, the sky, and the water's reflection; what is under the water is black to a camera ray.
Pass T: the camera sees only what comes through the water: its first hit on the cup or the water's reflection is black.
Rays after the first hit are the same in both passes. So R + T is the whole picture, and tea can filter T alone.

cup     The glaze as a skin (transparent + Fresnel gloss; shadow rays pass), the porcelain as a real scattering medium in the shell: thin parts glow, thick parts dim.
water   An open sheet: Fresnel between mirror and refraction. Cycles flips eta on back faces, so from below it totally reflects as it should.
"""

import bpy


def _skin_fresnel(nt, n):
    """The same as glaze_shader.skin_fresnel (the shader file travels alone to the renderer): reflectance of the glaze's skin, the same from both sides, so a shadow ray is not stopped by a false total reflection."""
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    iorv = nt.nodes.new("ShaderNodeMix")
    iorv.data_type = "FLOAT"
    nt.links.new(geo.outputs["Backfacing"], iorv.inputs[0])
    iorv.inputs[2].default_value = n
    iorv.inputs[3].default_value = 1.0 / n
    fr = nt.nodes.new("ShaderNodeFresnel")
    nt.links.new(iorv.outputs[0], fr.inputs["IOR"])
    return fr.outputs[0]


def _camera_gate(nt, out_socket, other, target):
    """target's surface = `other` for a camera ray, `out_socket` for all others."""
    lp = nt.nodes.new("ShaderNodeLightPath")
    mx = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(lp.outputs["Is Camera Ray"], mx.inputs[0])
    nt.links.new(out_socket, mx.inputs[1])
    nt.links.new(other, mx.inputs[2])
    nt.links.new(mx.outputs[0], target)


def _black(nt):
    e = nt.nodes.new("ShaderNodeEmission")
    e.inputs["Strength"].default_value = 0.0
    return e.outputs[0]


def make(name, p):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    pas = p["pass"]
    if p["kind"] == "cup":
        tr = nt.nodes.new("ShaderNodeBsdfTransparent")
        gl = nt.nodes.new("ShaderNodeBsdfAnisotropic")
        a = nt.nodes.new("ShaderNodeAttribute")
        a.attribute_name = "rough"
        nt.links.new(a.outputs["Fac"], gl.inputs["Roughness"])
        mx = nt.nodes.new("ShaderNodeMixShader")
        nt.links.new(_skin_fresnel(nt, p.get("ior", 1.5)), mx.inputs[0])
        nt.links.new(tr.outputs[0], mx.inputs[1])
        nt.links.new(gl.outputs[0], mx.inputs[2])
        if pas == "T":
            _camera_gate(nt, mx.outputs[0], _black(nt), out.inputs["Surface"])
        else:
            nt.links.new(mx.outputs[0], out.inputs["Surface"])
        ss, sa = p["sigma_s"], p["sigma_a"]
        d = max(ss)
        sc = nt.nodes.new("ShaderNodeVolumeScatter")
        sc.inputs["Color"].default_value = (ss[0] / d, ss[1] / d, ss[2] / d, 1)
        sc.inputs["Density"].default_value = d
        sc.inputs["Anisotropy"].default_value = p.get("g", 0.6)
        da = max(sa)
        ab = nt.nodes.new("ShaderNodeVolumeAbsorption")
        ab.inputs["Color"].default_value = (1 - sa[0] / da, 1 - sa[1] / da, 1 - sa[2] / da, 1)
        ab.inputs["Density"].default_value = da
        add = nt.nodes.new("ShaderNodeAddShader")
        nt.links.new(sc.outputs[0], add.inputs[0])
        nt.links.new(ab.outputs[0], add.inputs[1])
        nt.links.new(add.outputs[0], out.inputs["Volume"])
    elif p["kind"] == "water":
        f = nt.nodes.new("ShaderNodeFresnel")
        f.inputs["IOR"].default_value = p.get("ior", 1.33)
        rf = nt.nodes.new("ShaderNodeBsdfRefraction")
        rf.inputs["IOR"].default_value = p.get("ior", 1.33)
        rf.inputs["Roughness"].default_value = 0.0
        gl = nt.nodes.new("ShaderNodeBsdfAnisotropic")
        gl.inputs["Roughness"].default_value = 0.0
        full = nt.nodes.new("ShaderNodeMixShader")
        nt.links.new(f.outputs[0], full.inputs[0])
        nt.links.new(rf.outputs[0], full.inputs[1])
        nt.links.new(gl.outputs[0], full.inputs[2])
        cam = nt.nodes.new("ShaderNodeMixShader")
        nt.links.new(f.outputs[0], cam.inputs[0])
        if pas == "T":
            nt.links.new(rf.outputs[0], cam.inputs[1])
            nt.links.new(_black(nt), cam.inputs[2])
        else:
            nt.links.new(_black(nt), cam.inputs[1])
            nt.links.new(gl.outputs[0], cam.inputs[2])
        _camera_gate(nt, full.outputs[0], cam.outputs[0], out.inputs["Surface"])
    elif p["kind"] == "marker":
        e = nt.nodes.new("ShaderNodeEmission")
        e.inputs["Color"].default_value = (0, 0, 0, 1)
        nt.links.new(e.outputs[0], out.inputs["Surface"])
    else:
        raise ValueError(p["kind"])
    return m
