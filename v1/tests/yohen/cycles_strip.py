"""Cycles' thin film (Principled BSDF, Thin Film Thickness / IOR) against tools/tmm.py on a flat strip.

A black, smooth dielectric plane (Principled: base colour 0, roughness 0, IOR = the substrate's) carrying a thin
film whose thickness runs linearly along x from 0 to DMAX nm, under a uniform white world of radiance 1, seen by an
orthographic camera at a fixed angle to the normal: every pixel is the specular reflectance R(d, angle) in
Cycles' scene-linear RGB (Rec.709). tests/yohen/strip_compare.py compares it with tools/tmm.py.

    blender -b --factory-startup --python-exit-code 1 -P tests/yohen/cycles_strip.py -- \
        --film 2.5 --sub 1.6 --dmax 600 --angle 30 --out strip.exr

Only a real film index: Cycles' thin film has no absorption (k).
"""
import argparse
import math
import sys

import bpy

a = argparse.ArgumentParser()
a.add_argument("--film", type=float, required=True)
a.add_argument("--sub", type=float, required=True)
a.add_argument("--dmax", type=float, required=True)
a.add_argument("--angle", type=float, required=True)
a.add_argument("--width", type=int, default=800)
a.add_argument("--height", type=int, default=60)
a.add_argument("--spp", type=int, default=16)
a.add_argument("--out", required=True)
args = a.parse_args(sys.argv[sys.argv.index("--") + 1:])

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.engine = "CYCLES"
cy = scene.cycles
cy.device = "GPU"
prefs = bpy.context.preferences.addons["cycles"].preferences
prefs.compute_device_type = "METAL"
prefs.get_devices()
for d in prefs.devices:
    d.use = True
cy.samples = args.spp
cy.use_denoising = False
cy.use_adaptive_sampling = False
cy.max_bounces = 4
scene.render.resolution_x, scene.render.resolution_y = args.width, args.height
scene.render.resolution_percentage = 100
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "None"
scene.view_settings.exposure = 0
scene.view_settings.gamma = 1
scene.render.image_settings.file_format = "OPEN_EXR"
scene.render.image_settings.color_depth = "32"
scene.render.image_settings.color_mode = "RGB"        # as tools/cycles_scene.py: pbrt's imgtool reads RGB EXRs
scene.render.image_settings.exr_codec = "ZIP"
scene.render.film_transparent = False

world = bpy.data.worlds.new("w")
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bg.inputs["Color"].default_value = (1, 1, 1, 1)
bg.inputs["Strength"].default_value = 1.0
scene.world = world

bpy.ops.mesh.primitive_plane_add(size=1)
plane = bpy.context.active_object
plane.scale = (2.0, 4.0, 1.0)            # x from -1 to 1: the thickness ramp; y long enough for any tilt

mat = bpy.data.materials.new("film")
mat.use_nodes = True
nt = mat.node_tree
p = nt.nodes["Principled BSDF"]
p.inputs["Base Color"].default_value = (0, 0, 0, 1)
p.inputs["Roughness"].default_value = 0.0
p.inputs["Metallic"].default_value = 0.0
p.inputs["IOR"].default_value = args.sub
p.inputs["Thin Film IOR"].default_value = args.film
tc = nt.nodes.new("ShaderNodeTexCoord")
sep = nt.nodes.new("ShaderNodeSeparateXYZ")
mr = nt.nodes.new("ShaderNodeMapRange")
mr.inputs["From Min"].default_value = -1.0
mr.inputs["From Max"].default_value = 1.0
mr.inputs["To Min"].default_value = 0.0
mr.inputs["To Max"].default_value = args.dmax
mr.clamp = True
nt.links.new(tc.outputs["Object"], sep.inputs[0])
nt.links.new(sep.outputs["X"], mr.inputs["Value"])
nt.links.new(mr.outputs["Result"], p.inputs["Thin Film Thickness"])
plane.data.materials.append(mat)
# the object coordinate is in the mesh's own units (size 1: x from -0.5 to 0.5); rescale the ramp
mr.inputs["From Min"].default_value = -0.5
mr.inputs["From Max"].default_value = 0.5

cam_data = bpy.data.cameras.new("cam")
cam_data.type = "ORTHO"
cam_data.ortho_scale = 2.0
cam = bpy.data.objects.new("cam", cam_data)
scene.collection.objects.link(cam)
th = math.radians(args.angle)
cam.location = (0.0, -10.0 * math.sin(th), 10.0 * math.cos(th))
cam.rotation_euler = (th, 0.0, 0.0)
scene.camera = cam

scene.render.filepath = args.out
bpy.ops.render.render(write_still=True)
print("wrote", args.out)
