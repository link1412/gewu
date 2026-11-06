"""A clear crystal with a real medium (shot 33): a closed solid, true refraction and absorption per channel, sigma in 1/cm (1 unit = 1 cm).

Vertex attributes: `fr` the roughness of this face, `fs` how strongly its growth steps show, `axis` the crystal's c axis.
Bump, very small so that the flats stay flat: `wave` slow vicinal waves; `terrace` sharp growth steps, height in cm, square to the axis.
With `veil` in the params this is instead a thin patchy sheet inside the medium: a fracture plane or an inclusion cloud.
"""

import bpy


def make(name, p):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    geo = nt.nodes.new("ShaderNodeNewGeometry")

    def noise(scale, detail):
        n = nt.nodes.new("ShaderNodeTexNoise")
        n.inputs["Scale"].default_value = scale
        n.inputs["Detail"].default_value = detail
        nt.links.new(geo.outputs["Position"], n.inputs["Vector"])
        return n.outputs[0]

    def math(op, a, b):
        m = nt.nodes.new("ShaderNodeMath")
        m.operation = op
        for i, x in enumerate((a, b)):
            if isinstance(x, (int, float)):
                m.inputs[i].default_value = x
            else:
                nt.links.new(x, m.inputs[i])
        return m.outputs[0]

    def step(sock, lo, hi):
        r = nt.nodes.new("ShaderNodeMapRange")
        r.interpolation_type = "SMOOTHERSTEP"
        r.inputs["From Min"].default_value = lo
        r.inputs["From Max"].default_value = hi
        nt.links.new(sock, r.inputs["Value"])
        return r.outputs["Result"]

    if p.get("veil"):
        tr = nt.nodes.new("ShaderNodeBsdfTransparent")
        gl = nt.nodes.new("ShaderNodeBsdfAnisotropic")
        gl.inputs["Roughness"].default_value = 0.22
        df = nt.nodes.new("ShaderNodeBsdfDiffuse")
        df.inputs["Color"].default_value = (*p["tint"], 1)
        both = nt.nodes.new("ShaderNodeMixShader")
        both.inputs[0].default_value = 0.5
        nt.links.new(gl.outputs[0], both.inputs[1])
        nt.links.new(df.outputs[0], both.inputs[2])
        mx = nt.nodes.new("ShaderNodeMixShader")
        nt.links.new(math("MULTIPLY", step(noise(p["veil_scale"], 6.0), 0.5, 0.64), p["veil"]), mx.inputs[0])
        nt.links.new(tr.outputs[0], mx.inputs[1])
        nt.links.new(both.outputs[0], mx.inputs[2])
        nt.links.new(mx.outputs[0], out.inputs["Surface"])
        return mat

    fr = nt.nodes.new("ShaderNodeAttribute")
    fr.attribute_name = "fr"
    fs = nt.nodes.new("ShaderNodeAttribute")
    fs.attribute_name = "fs"
    ax = nt.nodes.new("ShaderNodeAttribute")
    ax.attribute_name = "axis"
    # a face's finish is not even either: duller in patches
    rough = math("MULTIPLY", fr.outputs["Fac"], math("ADD", 0.4, math("MULTIPLY", noise(9.0, 3.0), 1.2)))

    dot = nt.nodes.new("ShaderNodeVectorMath")
    dot.operation = "DOT_PRODUCT"
    nt.links.new(geo.outputs["Position"], dot.inputs[0])
    nt.links.new(ax.outputs["Vector"], dot.inputs[1])

    def steps(scale, lo):
        n = nt.nodes.new("ShaderNodeTexNoise")
        n.noise_dimensions = "1D"
        n.inputs["Scale"].default_value = scale
        n.inputs["Detail"].default_value = 2.0
        nt.links.new(dot.outputs["Value"], n.inputs["W"])
        return step(n.outputs[0], lo, lo + 0.015)

    terr = math("ADD", steps(18.0, 0.5), math("MULTIPLY", steps(45.0, 0.58), 0.5))
    height = math("ADD", math("MULTIPLY", noise(2.5, 2.0), p["wave"]), math("MULTIPLY", math("MULTIPLY", terr, fs.outputs["Fac"]), p["terrace"]))
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 1.0
    bump.inputs["Distance"].default_value = 1.0
    nt.links.new(height, bump.inputs["Height"])

    g = nt.nodes.new("ShaderNodeBsdfGlass")
    g.inputs["IOR"].default_value = p["ior"]
    nt.links.new(rough, g.inputs["Roughness"])
    nt.links.new(bump.outputs[0], g.inputs["Normal"])
    # a little light scatters back from inside: the crystal has a body colour even where nothing shines through.
    # A diffuse lobe stands in for that scattering, which a true scattering medium inside glass would make slow and noisy
    df = nt.nodes.new("ShaderNodeBsdfDiffuse")
    df.inputs["Color"].default_value = (*p["body"], 1)
    nt.links.new(bump.outputs[0], df.inputs["Normal"])
    under = nt.nodes.new("ShaderNodeMixShader")
    under.inputs[0].default_value = p["body_mix"]
    nt.links.new(g.outputs[0], under.inputs[1])
    nt.links.new(df.outputs[0], under.inputs[2])
    gl = nt.nodes.new("ShaderNodeBsdfAnisotropic")
    nt.links.new(rough, gl.inputs["Roughness"])
    nt.links.new(bump.outputs[0], gl.inputs["Normal"])
    fres = nt.nodes.new("ShaderNodeFresnel")
    fres.inputs["IOR"].default_value = p["ior"]
    mx = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(fres.outputs[0], mx.inputs[0])
    nt.links.new(under.outputs[0], mx.inputs[1])
    nt.links.new(gl.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], out.inputs["Surface"])

    sa = p["sigma_a"]
    da = max(max(sa), 1e-6)
    ab = nt.nodes.new("ShaderNodeVolumeAbsorption")
    ab.inputs["Color"].default_value = (1 - sa[0] / da, 1 - sa[1] / da, 1 - sa[2] / da, 1)
    ab.inputs["Density"].default_value = da
    nt.links.new(ab.outputs[0], out.inputs["Volume"])
    return mat
