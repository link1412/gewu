"""Blender script: tools/cycles_scene.py with one setting changed, to find where Cycles loses light in a glaze
volume (docs/slab.md). The change comes from the environment, GEWU_PROBE="key=value,key=value":
    maxb=N            every bounce limit N (max, diffuse, glossy, transmission, volume, transparent)
    node=coef|split|principled   the volume as Volume Coefficients (the adapter's), Scatter + Absorption, Principled
    homog=1           the material's homogeneous-volume flag on
    vsamp=DISTANCE|EQUIANGULAR|MULTIPLE_IMPORTANCE   the material's volume sampling
    tree=0            no light tree
    surf=transparent  the glaze's surface a Transparent BSDF (for eta 1 variants: no glass at all)
    thin=transparent|glossy|mixhalf   every thin dielectric replaced by a Transparent BSDF, a sharp Glossy BSDF,
                      or Mix(transparent, glossy) at a constant 0.5 (the air-film question, docs/slab.md)
    thin=diffuse|metal  ... or a white Diffuse BSDF, or a white sharp Metallic BSDF (F82)
    rough=A           the probes' Glossy (and the adapter's thin dielectric's) GGX roughness A instead of 0
    gcol=C            their Glossy's Color (C, C, C) instead of white; gcol=0.8 is Blender's default, which the
                      adapter's thin dielectric had until the film question was settled (docs/slab.md)
    dist=GGX|BECKMANN|MULTI_GGX|ASHIKHMIN_SHIRLEY   their Glossy's distribution
    vbias=1           the scene's volume_biased (ray marching) instead of the unbiased null scattering
    body=glossy       the opaque body (a diffuse with a medium outside) a sharp white Glossy BSDF
    boxmirror=1       the glaze box's bottom faces a sharp white Glossy BSDF (a second material with the same volume)
It prints the volume-related settings it ends up with. Same arguments as tools/cycles_scene.py.
"""
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.environ.get("GEWU_CYCLES_SCENE", os.path.expanduser("~/gewu-render/tools/cycles_scene.py"))
code = open(SRC).read()
assert code.rstrip().endswith("main()"), "cycles_scene.py should end with main()"
ns = {"__name__": "cycles_scene", "__file__": SRC}
exec(compile(code.rstrip()[: -len("main()")], SRC, "exec"), ns)

probe = dict(kv.split("=", 1) for kv in os.environ.get("GEWU_PROBE", "").split(",") if kv)
print("PROBE", probe)

orig_setup = ns["setup"]


def setup(sc, a, scene):
    res = orig_setup(sc, a, scene)
    c = scene.cycles
    if "maxb" in probe:
        n = int(probe["maxb"])
        c.max_bounces = n
        for k in ("diffuse_bounces", "glossy_bounces", "transmission_bounces", "volume_bounces",
                  "transparent_max_bounces"):
            setattr(c, k, n)
    if probe.get("tree") == "0":
        c.use_light_tree = False
    if probe.get("vbias") == "1":
        c.volume_biased = True
    return res


orig_material = ns["material"]
glaze = {}                       # the glaze objects' names -> their medium (for boxmirror)


def glossy(g):
    """The probes' Glossy BSDF: white (or `gcol`), GGX (or `dist`), roughness `rough` (0: sharp)."""
    gl = g.node("ShaderNodeBsdfAnisotropic", Roughness=float(probe.get("rough", 0.0)))   # the Glossy BSDF's id
    gl.distribution = probe.get("dist", "GGX")
    c = float(probe.get("gcol", 1.0))
    gl.inputs["Color"].default_value = (c, c, c, 1.0)
    return gl


def volume(nt, out, md):
    """The adapter's volume (Volume Coefficients, HG) on a material's Volume output."""
    v = nt.nodes.new("ShaderNodeVolumeCoefficients")
    v.inputs["Absorption Coefficients"].default_value = md["sigma_a_per_m"]
    v.inputs["Scatter Coefficients"].default_value = md["sigma_s_per_m"]
    v.inputs["Anisotropy"].default_value = md["g"]
    v.phase = "HENYEY_GREENSTEIN"
    nt.links.new(v.outputs[0], out.inputs["Volume"])


def material(o, media, base):
    mat = orig_material(o, media, base)
    inside, outside = o.get("inside"), o.get("outside")
    kind = o["material"]["type"]
    if probe.get("body") == "glossy" and kind == "diffuse" and outside and not inside:
        g = ns["Graph"](mat)
        gl = glossy(g)
        g.nt.links.new(gl.outputs[0], g.out.inputs["Surface"])
        print("PROBE body", o["name"], "a sharp Glossy BSDF")
    has_vol = kind == "dielectric" and inside and not outside
    if has_vol:
        glaze[o["name"]] = media[inside]
    if not has_vol:
        return mat
    nt = mat.node_tree
    out = next(n for n in nt.nodes if n.bl_idname == "ShaderNodeOutputMaterial")
    md = media[inside]
    node = probe.get("node", "coef")
    if node != "coef":
        for l in list(out.inputs["Volume"].links):
            nt.links.remove(l)
        if node == "split":
            sa = nt.nodes.new("ShaderNodeVolumeAbsorption")
            ss = nt.nodes.new("ShaderNodeVolumeScatter")
            # Cycles (svm_node_closure_volume): absorption = density * (1 - colour), scattering = density * colour
            k_a, k_s = max(md["sigma_a_per_m"]), max(md["sigma_s_per_m"])
            sa.inputs["Color"].default_value = (*[1 - v / k_a if k_a else 1 for v in md["sigma_a_per_m"]], 1)
            sa.inputs["Density"].default_value = k_a
            ss.inputs["Color"].default_value = (*[v / k_s if k_s else 0 for v in md["sigma_s_per_m"]], 1)
            ss.inputs["Density"].default_value = k_s
            ss.inputs["Anisotropy"].default_value = md["g"]
            if hasattr(ss, "phase"):
                ss.phase = "HENYEY_GREENSTEIN"
            add = nt.nodes.new("ShaderNodeAddShader")
            nt.links.new(sa.outputs[0], add.inputs[0])
            nt.links.new(ss.outputs[0], add.inputs[1])
            nt.links.new(add.outputs[0], out.inputs["Volume"])
        elif node == "principled":
            # Principled Volume: scattering = density * color, absorption = density * (1 - color) with a black
            # absorption colour (Cycles svm_node_principled_volume); a grey medium only
            st = md["sigma_a_per_m"][0] + md["sigma_s_per_m"][0]
            alb = md["sigma_s_per_m"][0] / st
            pv = nt.nodes.new("ShaderNodeVolumePrincipled")
            pv.inputs["Color"].default_value = (alb, alb, alb, 1)
            pv.inputs["Density"].default_value = st
            pv.inputs["Anisotropy"].default_value = md["g"]
            pv.inputs["Absorption Color"].default_value = (0, 0, 0, 1)
            nt.links.new(pv.outputs[0], out.inputs["Volume"])
    if probe.get("homog") == "1":
        mat.cycles.homogeneous_volume = True
    if "vsamp" in probe:
        mat.cycles.volume_sampling = probe["vsamp"]
    if probe.get("surf") == "transparent":
        for l in list(out.inputs["Surface"].links):
            nt.links.remove(l)
        tr = nt.nodes.new("ShaderNodeBsdfTransparent")
        nt.links.new(tr.outputs[0], out.inputs["Surface"])
    vol = {p.identifier: getattr(mat.cycles, p.identifier) for p in mat.cycles.bl_rna.properties
           if "vol" in p.identifier or "homog" in p.identifier}
    print("PROBE material", mat.name, vol)
    return mat


orig_thin = ns["thin_dielectric"]


def thin_dielectric(g, eta, normal=None):
    kind = probe.get("thin")
    if kind is None:
        mix = orig_thin(g, eta, normal)
        for n in g.nt.nodes:
            if n.bl_idname == "ShaderNodeBsdfAnisotropic":
                if "rough" in probe:
                    n.inputs["Roughness"].default_value = float(probe["rough"])
                if "dist" in probe:
                    n.distribution = probe["dist"]
                if "gcol" in probe:
                    c = float(probe["gcol"])
                    n.inputs["Color"].default_value = (c, c, c, 1.0)
        return mix
    tr = g.node("ShaderNodeBsdfTransparent")
    gl = glossy(g)
    if kind == "transparent":
        return tr
    if kind == "glossy":
        return gl
    if kind == "diffuse":
        return g.node("ShaderNodeBsdfDiffuse", Color=(1, 1, 1, 1))
    if kind == "metal":
        m = g.node("ShaderNodeBsdfMetallic", Roughness=float(probe.get("rough", 0.0)))
        m.distribution = "GGX"
        m.inputs["Base Color"].default_value = (1, 1, 1, 1)
        m.inputs["Edge Tint"].default_value = (1, 1, 1, 1)
        return m
    mix = g.node("ShaderNodeMixShader")
    mix.inputs[0].default_value = 0.5
    g.nt.links.new(tr.outputs[0], mix.inputs[1])
    g.nt.links.new(gl.outputs[0], mix.inputs[2])
    return mix


orig_camera = ns["camera"]


def camera(c, res):
    if probe.get("boxmirror") == "1":
        import numpy as np
        for name, md in glaze.items():
            ob = bpy.data.objects[name]
            me = ob.data
            mat = bpy.data.materials.new(name + "-mirror")
            g = ns["Graph"](mat)
            g.nt.links.new(glossy(g).outputs[0], g.out.inputs["Surface"])
            volume(g.nt, g.out, md)
            me.materials.append(mat)
            zc = np.array([(ob.matrix_world @ p.center).z for p in me.polygons])
            bottom = zc < zc.min() + 1e-9
            for p, b in zip(me.polygons, bottom):
                if b:
                    p.material_index = 1
            print("PROBE boxmirror", name, int(bottom.sum()), "faces at z", float(zc.min()))
    return orig_camera(c, res)


ns["camera"] = camera
ns["setup"] = setup
ns["material"] = material
ns["thin_dielectric"] = thin_dielectric
ns["main"]()
sc = bpy.context.scene
print("PROBE scene.cycles volume settings",
      {p.identifier: getattr(sc.cycles, p.identifier) for p in sc.cycles.bl_rna.properties if "vol" in p.identifier})
print("PROBE final bounces", {k: getattr(bpy.context.scene.cycles, k) for k in
      ("max_bounces", "diffuse_bounces", "glossy_bounces", "transmission_bounces", "volume_bounces",
       "transparent_max_bounces", "use_light_tree")})
