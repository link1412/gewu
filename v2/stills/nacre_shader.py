"""Shell inlaid in lacquer, under a polished coat. The colour of the shell is not painted: it is interference, and it changes as the dish turns.

The layers of nacre do not lie parallel to the ground face of a piece: a piece is cut from a curved shell and ground flat, so its layers are tilted, each piece its own way. So the glossy lobe of the shell uses a normal tipped by (tx, ty) in the flat of the dish, the coat above it the true surface. A piece lights up when the window falls into its lobe, and goes dark again: this is why most of the pieces in a real dish are dark and a few flash, and why they flash in turn when it moves. The tilt is in object space, so it turns with the dish.

One thin film stands in for the real stack of layers (attribute `film`, nm; params film_ior), as in yohen_shader: Cycles computes the interference from the angle. A real Bragg stack has narrower bands: this is a stand-in, picked for the colour.

`sat` mixes the film lobe with the same lobe without a film: real nacre is mostly silver with a cast of colour.

Attributes: col, rough, metal, spec, coat, crough, film, sat, tx, ty. Lacquer is simply metal 0, film 0, tilt 0.
"""

import bpy


def _attr(nt, name):
    a = nt.nodes.new("ShaderNodeAttribute")
    a.attribute_name = name
    return a


def make(name, p):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")

    comb = nt.nodes.new("ShaderNodeCombineXYZ")
    nt.links.new(_attr(nt, "tx").outputs["Fac"], comb.inputs["X"])
    nt.links.new(_attr(nt, "ty").outputs["Fac"], comb.inputs["Y"])
    turn = nt.nodes.new("ShaderNodeVectorTransform")
    turn.vector_type = "VECTOR"
    turn.convert_from = "OBJECT"
    turn.convert_to = "WORLD"
    nt.links.new(comb.outputs[0], turn.inputs[0])
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    add = nt.nodes.new("ShaderNodeVectorMath")
    add.operation = "ADD"
    nt.links.new(geo.outputs["Normal"], add.inputs[0])
    nt.links.new(turn.outputs[0], add.inputs[1])
    unit = nt.nodes.new("ShaderNodeVectorMath")
    unit.operation = "NORMALIZE"
    nt.links.new(add.outputs[0], unit.inputs[0])

    col, rough, metal, spec, coat, crough = (_attr(nt, n) for n in ("col", "rough", "metal", "spec", "coat", "crough"))

    def lobe(film):
        b = nt.nodes.new("ShaderNodeBsdfPrincipled")
        nt.links.new(col.outputs["Color"], b.inputs["Base Color"])
        nt.links.new(rough.outputs["Fac"], b.inputs["Roughness"])
        nt.links.new(metal.outputs["Fac"], b.inputs["Metallic"])
        nt.links.new(spec.outputs["Fac"], b.inputs["Specular IOR Level"])
        nt.links.new(coat.outputs["Fac"], b.inputs["Coat Weight"])
        nt.links.new(crough.outputs["Fac"], b.inputs["Coat Roughness"])
        b.inputs["Coat IOR"].default_value = 1.5
        nt.links.new(unit.outputs[0], b.inputs["Normal"])  # the coat keeps the true surface: its own normal is left unlinked
        if film:
            b.inputs["Thin Film IOR"].default_value = p.get("film_ior", 1.9)
            nt.links.new(_attr(nt, "film").outputs["Fac"], b.inputs["Thin Film Thickness"])
        return b

    mx = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(_attr(nt, "sat").outputs["Fac"], mx.inputs[0])
    nt.links.new(lobe(False).outputs[0], mx.inputs[1])
    nt.links.new(lobe(True).outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], out.inputs["Surface"])
    return m
