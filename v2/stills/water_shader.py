"""Clear water: a real refracting surface, smooth shaded. Used for drops."""

import sys

import bpy
import numpy as np


def _smooth():
    g = sys._getframe(2).f_globals
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


def make(name, p):
    _smooth()
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    b.inputs["Base Color"].default_value = (1, 1, 1, 1)
    b.inputs["Transmission Weight"].default_value = 1.0
    b.inputs["IOR"].default_value = 1.33
    b.inputs["Roughness"].default_value = 0.0
    nt.links.new(b.outputs[0], out.inputs["Surface"])
    return m
