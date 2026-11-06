"""Shaders for the plique-a-jour carp (s49_yulin).

glass    Glass BSDF, IOR 1.5, with homogeneous Volume Absorption; p["sigma"] is the absorption per cm, RGB. One material to a cell, since a mesh's vertex attributes do not reach its volume.
wire     gilt: Principled metal. Gold colour by eye, roughness moved by a small noise.
bubble   a sphere in the glass: Glass BSDF at relative IOR 1/1.5, so that going in is going from glass to air. A stand-in: no volume priority.
behind   the emitting surface behind the sheet, strength from the attribute E.

Also: soups shade smoothly here (as in s65_shader), or a cell's concave faces would be facets.
"""

import sys

import bpy
import numpy as np


def _soften():
    g = sys._getframe(2).f_globals  # the studio's, as in s65_shader
    if "soup_mesh" not in g or getattr(g["soup_mesh"], "_soft", False):
        return
    old = g["soup_mesh"]

    def soft(name, V, F, attrs, mat):
        ob = old(name, V, F, attrs, mat)
        ob.data.polygons.foreach_set("use_smooth", np.ones(len(F), dtype=bool))
        ob.data.update()
        return ob

    soft._soft = True
    g["soup_mesh"] = soft


def _glass(m, p):
    nt = m.node_tree
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    g = nt.nodes.new("ShaderNodeBsdfGlass")
    g.inputs["IOR"].default_value = 1.5
    g.inputs["Roughness"].default_value = float(p.get("rough", 0.008))
    g.inputs["Color"].default_value = (1, 1, 1, 1)
    nt.links.new(g.outputs[0], out.inputs["Surface"])
    s = np.asarray(p["sigma"], float)
    dens = float(s.max())
    col = 1.0 - s / dens  # sigma = density * (1 - colour)
    v = nt.nodes.new("ShaderNodeVolumeAbsorption")
    v.inputs["Color"].default_value = (float(col[0]), float(col[1]), float(col[2]), 1)
    v.inputs["Density"].default_value = dens
    nt.links.new(v.outputs[0], out.inputs["Volume"])
    if hasattr(m.cycles, "homogeneous_volume"):  # Blender 5 finds this out by itself
        m.cycles.homogeneous_volume = True


def _wire(m, p):
    nt = m.node_tree
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    b.inputs["Base Color"].default_value = (1.0, 0.74, 0.3, 1)
    b.inputs["Metallic"].default_value = 1.0
    tc = nt.nodes.new("ShaderNodeTexCoord")
    n = nt.nodes.new("ShaderNodeTexNoise")
    n.inputs["Scale"].default_value = 26.0
    n.inputs["Detail"].default_value = 3.0
    nt.links.new(tc.outputs["Object"], n.inputs["Vector"])
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = 0.3
    mr.inputs["From Max"].default_value = 0.7
    mr.inputs["To Min"].default_value = 0.12
    mr.inputs["To Max"].default_value = 0.26
    nt.links.new(n.outputs[0], mr.inputs["Value"])
    nt.links.new(mr.outputs[0], b.inputs["Roughness"])
    nt.links.new(b.outputs[0], out.inputs["Surface"])


def _bubble(m, p):
    nt = m.node_tree
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    g = nt.nodes.new("ShaderNodeBsdfGlass")
    g.inputs["IOR"].default_value = 1.0 / 1.5
    g.inputs["Roughness"].default_value = 0.0
    nt.links.new(g.outputs[0], out.inputs["Surface"])


def _behind(m, p):
    nt = m.node_tree
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    e = nt.nodes.new("ShaderNodeEmission")
    a = nt.nodes.new("ShaderNodeAttribute")
    a.attribute_name = "E"
    r = p.get("rgb", [1, 1, 1])
    mul = nt.nodes.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    mul.inputs[1].default_value = float(p.get("L", 5.0))
    nt.links.new(a.outputs["Fac"], mul.inputs[0])
    e.inputs["Color"].default_value = (r[0], r[1], r[2], 1)
    nt.links.new(mul.outputs[0], e.inputs["Strength"])
    nt.links.new(e.outputs[0], out.inputs["Surface"])


def make(name, p):
    _soften()
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    m.node_tree.nodes.clear()
    {"glass": _glass, "wire": _wire, "bubble": _bubble, "behind": _behind}[p["kind"]](m, p)
    return m
