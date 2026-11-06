"""Gold leaf for s27 (make(name, params), run inside Blender by studio_bpy): a real conductor with complex IOR, plus the little light a 100 nm film lets straight through.

Metallic BSDF, Physical Conductor: params ior, ext are the RGB n and k. Add a Transparent BSDF coloured by attribute `trans`: a film thinner than a wavelength does not refract, so transmitted light keeps its direction.
Alpha (attribute) only softens the torn edge within a mesh cell; faces with `keep` below .5 do not exist at all (no invisible surface hangs beyond the edge, see s27_float.py on the old black streaks).
"""

import sys

import bpy
import numpy as np


def _cut_grid(name, P, attrs, mat):
    ny, nx = P.shape[:2]
    idx = np.arange(nx * ny, dtype=np.int32).reshape(ny, nx)
    v = attrs.pop("keep") > 0.5
    good = v[:-1, :-1] & v[1:, :-1] & v[1:, 1:] & v[:-1, 1:]
    loops = np.stack([idx[:-1, :-1][good], idx[1:, :-1][good], idx[1:, 1:][good], idx[:-1, 1:][good]], -1).ravel()
    nf = loops.size // 4
    me = bpy.data.meshes.new(name)
    me.vertices.add(nx * ny)
    me.vertices.foreach_set("co", P.reshape(-1).astype(np.float32))
    me.loops.add(nf * 4)
    me.loops.foreach_set("vertex_index", loops)
    me.polygons.add(nf)
    me.polygons.foreach_set("loop_start", np.arange(nf, dtype=np.int32) * 4)
    me.update(calc_edges=False)
    me.polygons.foreach_set("use_smooth", np.ones(nf, dtype=bool))
    for a, val in attrs.items():
        if val.ndim == 3:
            at = me.attributes.new(a, "FLOAT_COLOR", "POINT")
            rgba = np.concatenate([val, np.ones(val.shape[:2] + (1,), val.dtype)], -1)
            at.data.foreach_set("color", rgba.reshape(-1).astype(np.float32))
        else:
            me.attributes.new(a, "FLOAT", "POINT").data.foreach_set("value", val.reshape(-1).astype(np.float32))
    me.update()
    me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    return ob


def make(name, p):
    g = sys._getframe(2).f_globals  # the globals of studio_bpy.main(): replaces grid_mesh for this mesh only, as s21_sheets.py does
    prev = g["grid_mesh"]

    def grid_mesh(n, P, attrs, mat):
        return _cut_grid(n, P, dict(attrs), mat) if n == name else prev(n, P, attrs, mat)

    g["grid_mesh"] = grid_mesh

    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")

    def attr(a):
        n = nt.nodes.new("ShaderNodeAttribute")
        n.attribute_name = a
        return n

    metal = nt.nodes.new("ShaderNodeBsdfMetallic")
    metal.fresnel_type = "PHYSICAL_CONDUCTOR"
    metal.distribution = "MULTI_GGX"
    metal.inputs["IOR"].default_value = p["ior"]
    metal.inputs["Extinction"].default_value = p["ext"]
    nt.links.new(attr("rough").outputs["Fac"], metal.inputs["Roughness"])

    through = nt.nodes.new("ShaderNodeBsdfTransparent")
    nt.links.new(attr("trans").outputs["Color"], through.inputs["Color"])
    add = nt.nodes.new("ShaderNodeAddShader")
    nt.links.new(metal.outputs[0], add.inputs[0])
    nt.links.new(through.outputs[0], add.inputs[1])

    hole = nt.nodes.new("ShaderNodeBsdfTransparent")
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(attr("alpha").outputs["Fac"], mix.inputs[0])
    nt.links.new(hole.outputs[0], mix.inputs[1])
    nt.links.new(add.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs["Surface"])
    return m
