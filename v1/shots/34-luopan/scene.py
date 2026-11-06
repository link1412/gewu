"""Shot 34 (shader shot): a feng-shui luopan from straight above in bright daylight. A kit scene (tools/kit_bpy.py; run
by tools/shotkit.py). Same scene as legacy/scene.py (S9 v1), on the kit. All [A] unless noted:
- the plate (天盘): a 30 cm disc 2 mm proud of the board, pale lacquer with the face texture (face.py), ink a little duller;
- the red cross threads (天心十字线), 0.5 mm, 2 mm above the face;
- the square board (地盘) around it, warm white like the original's paper, faint mottling;
- camera straight down, 100 mm f/8, placed so the rim is the spec arc (kit_bpy.frame_on_circle);
- light: a 0.4 m soft panel above and beyond the frame's top (group "key") and a white world (group "sky", its colour
  tied to the key's in the fit) [F].
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402
import numpy as np  # noqa: E402
from mathutils import Vector  # noqa: E402

import kit_bpy as K  # noqa: E402

R = 0.15                                                   # plate radius (m)
TH = 0.002                                                 # 天盘 almost flush in the board (2 cm shaded the board ~10 codes)


def face_material(tex):
    m, b, nt = K.principled("face", (0.8, 0.8, 0.8), 0.35)
    tx = K.image(nt, os.path.join(tex, "face.png"), colorspace="sRGB")
    K.link(nt, tx.outputs["Color"], b.inputs["Base Color"])
    ti = K.image(nt, os.path.join(tex, "face_ink.png"))
    mr = K.node(nt, "ShaderNodeMapRange", **{"To Min": 0.35, "To Max": 0.6})   # lacquer 0.35, ink duller 0.6
    K.link(nt, ti.outputs["Color"], mr.inputs["Value"])
    K.link(nt, mr.outputs["Result"], b.inputs["Roughness"])
    return m


def paper_material():
    m, b, nt = K.principled("paper", (0.82, 0.82, 0.82), 0.9, Specular_IOR_Level=0.3)
    n = K.node(nt, "ShaderNodeTexNoise", Scale=180.0, Detail=8.0)
    ramp = K.node(nt, "ShaderNodeMapRange", **{"To Min": 0.95, "To Max": 1.03})
    K.link(nt, n.outputs["Fac"], ramp.inputs["Value"])
    tint = nt.nodes.new("ShaderNodeMix")
    tint.data_type, tint.blend_type = "RGBA", "MULTIPLY"
    tint.inputs["Factor"].default_value = 1.0
    tint.inputs["A"].default_value = (0.87, 0.82, 0.75, 1)          # the plate's lacquer tint: one light colour fits both
    K.link(nt, ramp.outputs["Result"], tint.inputs["B"])
    K.link(nt, tint.outputs["Result"], b.inputs["Base Color"])
    return m


def plate(tex):
    n = 720
    t = np.linspace(0, 2 * np.pi, n, endpoint=False)
    rim = np.stack([R * np.sin(t), R * np.cos(t)], 1)
    top = [(0, 0, TH)] + [(x, y, TH) for x, y in rim]
    uv = [(0.5, 0.5)] + [(x / (2 * R) + 0.5, y / (2 * R) + 0.5) for x, y in rim]
    K.mesh("face", top, [(0, 1 + (i + 1) % n, 1 + i) for i in range(n)], face_material(tex), uv=uv)
    ring = [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
    wood, _, _ = K.principled("wood", (0.42, 0.28, 0.16), 0.5)
    K.mesh("edge", [(x, y, TH - 0.0008) for x, y in rim] + [(x, y, 0.0) for x, y in rim], ring, wood, smooth=True)
    lac, _, _ = K.principled("rimlac", (0.55, 0.42, 0.22), 0.3)
    K.mesh("bevel", [(x, y, TH) for x, y in rim] + [(x, y, TH - 0.0008) for x, y in rim], ring, lac, smooth=True)


def thread(name, p0, p1, r, mat):
    d = Vector(p1) - Vector(p0)
    bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=r, depth=d.length, location=(Vector(p0) + Vector(p1)) / 2)
    ob = bpy.context.active_object
    ob.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
    ob.name = name
    ob.data.materials.append(mat)
    bpy.ops.object.shade_smooth()


a = K.args(lambda ap: ap.add_argument("--tex", required=True))
K.setup(a)
K.world(strength=0.6, group="sky")
tex = os.path.join(K.HERE, a.tex)
K.mesh("paper", [(-2, -2, 0), (2, -2, 0), (2, 2, 0), (-2, 2, 0)], [(0, 1, 2, 3)], paper_material())
plate(tex)
red, rb, _ = K.principled("thread", (0.70, 0.13, 0.08), 0.6, Sheen_Weight=0.5)
z = TH + 0.002
thread("thread_ns", (0, -R * 1.02, z), (0, R * 1.02, z), 0.0005, red)
thread("thread_ew", (-R * 1.02, 0, z), (R * 1.02, 0, z), 0.0005, red)
(cx, cy, dist), W = K.frame_on_circle(a, R)
K.area("key", (cx - 0.1, cy + 0.45, 0.45), (cx, cy, 0), 0.4, "key", shape="RECTANGLE", size_y=0.4)
K.camera((cx, cy, TH + dist), None, focal_mm=100, fnum=8, focus=dist)
K.render(a)
