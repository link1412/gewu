"""Denoise raw camera-RGB images with OpenImageDenoise, through Blender's compositor (its Denoise node); inside Blender:

    blender -b --factory-startup --python-exit-code 1 -P tools/cycles_denoise.py -- \
        --albedo DIR/x.albedo.exr --normal DIR/x.normal.exr IN1.exr|pfm OUT1.exr [IN2 OUT2 ...]

Why: light adds, so the groups of a render (tools/cycles_scene.py, light groups) are mixed linearly, but a denoiser
is not linear: denoising each group and adding them is not the denoised mix. So the mix is made first (tools/build.py)
and denoised here, with the albedo and normal of the same render (they do not depend on the lights). This is what
Cycles' own --denoise does to a render (OIDN, albedo and normal, prefilter "Accurate", HDR), on an image made outside.

The images are read and written as data ("Non-Color": no colour transform), float EXR, RGB. Measured on a 64x36 test
(S3): an image passed through the same graph without the Denoise node comes back bit for bit.
"""

import os
import shutil
import sys

import bpy


def args():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--albedo", required=True)
    ap.add_argument("--normal", required=True)
    ap.add_argument("--quality", default="High", choices=["High", "Balanced", "Fast"])
    ap.add_argument("--device", help="ignored (mini-cpu.sh appends --device CPU to every Blender job)")
    ap.add_argument("pairs", nargs="+", help="IN.exr OUT.exr, repeated")
    a = ap.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    if len(a.pairs) % 2:
        raise SystemExit("give IN OUT pairs")
    return a


def pfm_to_exr(path):
    """A PFM (tools/build.py writes its mixes so, float32 exact) as a float EXR beside it, through Blender's
    OpenImageIO. PFM stores the bottom row first; OpenImageIO writes the top row first."""
    import numpy as np
    import OpenImageIO as oiio
    with open(path, "rb") as f:
        kind = f.readline().strip()
        w, h = map(int, f.readline().split())
        sc = float(f.readline())
        nc = {b"PF": 3, b"Pf": 1}[kind]
        a = np.frombuffer(f.read(), "<f4" if sc < 0 else ">f4").reshape(h, w, nc)
    a = np.ascontiguousarray(np.repeat(a, 3 // nc, 2)[::-1], np.float32)
    out = path + ".exr"
    spec = oiio.ImageSpec(w, h, 3, oiio.FLOAT)
    o = oiio.ImageOutput.create(out)
    if o is None or not o.open(out, spec) or not o.write_image(a):
        raise SystemExit(f"{out}: could not write")
    o.close()
    return out


def load(path):
    if not os.path.isfile(path):
        raise SystemExit(f"{path}: no such file")
    if path.lower().endswith(".pfm"):
        path = pfm_to_exr(path)
    im = bpy.data.images.load(os.path.abspath(path), check_existing=False)
    im.colorspace_settings.name = "Non-Color"
    return im


def main():
    a = args()
    s = bpy.context.scene
    albedo, normal = load(a.albedo), load(a.normal)
    W, H = albedo.size
    if tuple(normal.size) != (W, H):
        raise SystemExit("albedo and normal differ in size")
    s.render.resolution_x, s.render.resolution_y, s.render.resolution_percentage = W, H, 100
    g = bpy.data.node_groups.new("denoise", "CompositorNodeTree")
    nodes = {}
    for k, im in (("albedo", albedo), ("normal", normal), ("image", None)):
        n = g.nodes.new("CompositorNodeImage")
        n.image = im
        nodes[k] = n
    d = g.nodes.new("CompositorNodeDenoise")
    d.inputs["HDR"].default_value = True
    d.inputs["Prefilter"].default_value = "Accurate"
    d.inputs["Quality"].default_value = a.quality
    g.links.new(nodes["image"].outputs["Image"], d.inputs["Image"])
    g.links.new(nodes["albedo"].outputs["Image"], d.inputs["Albedo"])
    g.links.new(nodes["normal"].outputs["Image"], d.inputs["Normal"])
    fo = g.nodes.new("CompositorNodeOutputFile")
    fo.format.media_type = "IMAGE"
    fo.format.file_format = "OPEN_EXR"
    fo.format.color_depth = "32"
    fo.format.color_mode = "RGB"
    fo.format.exr_codec = "ZIP"
    fo.file_output_items.new("RGBA", "Image")
    g.links.new(d.outputs[0], fo.inputs["Image"])
    s.compositing_node_group = g
    s.render.use_compositing = True
    for inp, out in zip(a.pairs[0::2], a.pairs[1::2]):
        im = load(inp)
        if tuple(im.size) != (W, H):
            raise SystemExit(f"{inp}: {tuple(im.size)}, not the albedo's {(W, H)}")
        nodes["image"].image = im
        tmp = os.path.abspath(out) + ".tmpdir"
        os.makedirs(tmp, exist_ok=True)
        fo.directory = tmp
        fo.file_name = "dn"
        bpy.ops.render.render(write_still=False)
        made = [f for f in os.listdir(tmp) if f.endswith(".exr")]
        if len(made) != 1:
            raise SystemExit(f"{inp}: the compositor wrote {made}")
        os.replace(os.path.join(tmp, made[0]), os.path.abspath(out))
        shutil.rmtree(tmp)
        bpy.data.images.remove(im)
        print(f"DENOISED {inp} -> {out}")


main()
