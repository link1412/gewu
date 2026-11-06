"""A pearl's skin, in three parts (see s36_nanzhu.py for the numbers and where they come from):

1. coat: a sharp mirror lobe from the top of the stack (Fresnel, n = 1.6), which shows the window's edges;
2. orient: glossy lobes from the stack below, one per colour channel, each with its own width (attributes rr, rg, rb) and its colour read from a table of the stack's reflectance
   against the cosine of the angle and the tablet thickness (attribute `film`, nm; table written by s36_nanzhu.stack_lut). The red lobe is the widest, so a tint gathers in the edge of the highlight and nowhere else;
3. body: a milky scattering solid, no gloss of its own.
With params fine_normal, the mirror and the orient take a normal tilted by the attributes tx, ty, tz (object space): the growth lines. The body keeps the true surface.

They are added, not layered: not strictly energy conserving, weights chosen so the sum stays below 1 (see `milk`). Stand-in, not a simulation of the stack.
params: fine_normal, lut (path to a .npy, H x W x 3, float32; x is cos, y is thickness), d0, d1 (nm at the two ends of y), ior, orient (gain of part 2), milk, milk_rough, radius [r, g, b].
"""

import bpy
import numpy as np


def _attr(nt, name):
    a = nt.nodes.new("ShaderNodeAttribute")
    a.attribute_name = name
    return a


def fine_normal(nt):
    """The growth lines and flaws, attributes tx, ty, tz: a tilt in object space, so it turns with the pearl."""
    comb = nt.nodes.new("ShaderNodeCombineXYZ")
    for ax, n_ in (("X", "tx"), ("Y", "ty"), ("Z", "tz")):
        nt.links.new(_attr(nt, n_).outputs["Fac"], comb.inputs[ax])
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
    return unit.outputs[0]


def make(name, p):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")

    lut = np.load(p["lut"]).astype(np.float32)
    lh, lw = lut.shape[:2]
    im = bpy.data.images.new(name + "_lut", lw, lh, alpha=False, float_buffer=True)
    im.colorspace_settings.name = "Non-Color"
    im.pixels.foreach_set(np.concatenate([lut, np.ones((lh, lw, 1), np.float32)], -1).ravel())
    im.pack()

    geo = nt.nodes.new("ShaderNodeNewGeometry")
    cos = nt.nodes.new("ShaderNodeVectorMath")
    cos.operation = "DOT_PRODUCT"
    nt.links.new(geo.outputs["Incoming"], cos.inputs[0])
    nt.links.new(geo.outputs["Normal"], cos.inputs[1])
    film = _attr(nt, "film")
    sub = nt.nodes.new("ShaderNodeMath")
    sub.operation = "SUBTRACT"
    nt.links.new(film.outputs["Fac"], sub.inputs[0])
    sub.inputs[1].default_value = float(p["d0"])
    div = nt.nodes.new("ShaderNodeMath")
    div.operation = "DIVIDE"
    nt.links.new(sub.outputs[0], div.inputs[0])
    div.inputs[1].default_value = float(p["d1"]) - float(p["d0"])
    uv = nt.nodes.new("ShaderNodeCombineXYZ")
    nt.links.new(cos.outputs["Value"], uv.inputs["X"])
    nt.links.new(div.outputs[0], uv.inputs["Y"])
    tx = nt.nodes.new("ShaderNodeTexImage")
    tx.image = im
    tx.interpolation = "Linear"
    tx.extension = "EXTEND"
    nt.links.new(uv.outputs[0], tx.inputs["Vector"])
    sep = nt.nodes.new("ShaderNodeSeparateColor")
    nt.links.new(tx.outputs["Color"], sep.inputs[0])

    N_ = fine_normal(nt) if p.get("fine_normal") else None

    def add(a, b):
        s = nt.nodes.new("ShaderNodeAddShader")
        nt.links.new(a, s.inputs[0])
        nt.links.new(b, s.inputs[1])
        return s.outputs[0]

    def glossy(rough_socket, r, g, b):
        """r, g, b: output sockets or numbers."""
        n = nt.nodes.new("ShaderNodeBsdfAnisotropic")
        n.distribution = "GGX"
        nt.links.new(rough_socket, n.inputs["Roughness"])
        if N_ is not None:
            nt.links.new(N_, n.inputs["Normal"])
        c = nt.nodes.new("ShaderNodeCombineColor")
        for ch, v in zip(("Red", "Green", "Blue"), (r, g, b)):
            if isinstance(v, (int, float)):
                c.inputs[ch].default_value = v
            else:
                nt.links.new(v, c.inputs[ch])
        nt.links.new(c.outputs[0], n.inputs["Color"])
        return n.outputs[0]

    def gain(sock, k):
        g_ = nt.nodes.new("ShaderNodeMath")
        g_.operation = "MULTIPLY"
        nt.links.new(sock, g_.inputs[0])
        g_.inputs[1].default_value = float(k)
        return g_.outputs[0]

    # 1. the mirror
    fr = nt.nodes.new("ShaderNodeFresnel")
    fr.inputs["IOR"].default_value = float(p.get("ior", 1.6))
    if N_ is not None:
        nt.links.new(N_, fr.inputs["Normal"])
    crough = _attr(nt, "crough")
    coat = glossy(crough.outputs["Fac"], fr.outputs[0], fr.outputs[0], fr.outputs[0])

    # 2. the orient: one lobe per channel, the table's colour on it
    k = float(p.get("orient", 0.25))
    og = _attr(nt, "og").outputs["Fac"]  # how much of the stack reflects here: less on a line, where tablet edges scatter it away

    def by_og(sock):
        g_ = nt.nodes.new("ShaderNodeMath")
        g_.operation = "MULTIPLY"
        nt.links.new(sock, g_.inputs[0])
        nt.links.new(og, g_.inputs[1])
        return g_.outputs[0]

    s = add(coat, glossy(_attr(nt, "rr").outputs["Fac"], gain(by_og(sep.outputs[0]), k), 0.0, 0.0))
    s = add(s, glossy(_attr(nt, "rg").outputs["Fac"], 0.0, gain(by_og(sep.outputs[1]), k), 0.0))
    s = add(s, glossy(_attr(nt, "rb").outputs["Fac"], 0.0, 0.0, gain(by_og(sep.outputs[2]), k)))
    # a very wide, faint, untinted lobe: the many deeper layers, what makes the body look lit from inside
    milk = glossy(_attr(nt, "rmilk").outputs["Fac"], float(p.get("milk", 0.12)), float(p.get("milk", 0.12)), float(p.get("milk", 0.12)))
    s = add(s, milk)

    # 3. the body
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(_attr(nt, "col").outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.6
    b.inputs["Specular IOR Level"].default_value = 0.0
    b.inputs["Subsurface Weight"].default_value = float(p.get("sss", 1.0))
    b.inputs["Subsurface Radius"].default_value = list(p.get("radius", [0.09, 0.075, 0.06]))
    b.inputs["Subsurface Scale"].default_value = 1.0
    s = add(s, b.outputs[0])
    nt.links.new(s, out.inputs["Surface"])
    return m
