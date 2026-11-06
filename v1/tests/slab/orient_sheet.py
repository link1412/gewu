"""S8 root fix (docs/slab.md, "顶点法线和三角形的绕向相反"): the before / after sheet of the Cycles orient-normals fix
and the sealed glazes, with the numbers measured on the renders written on it.

    python3 -I tests/slab/orient_sheet.py        # -> out/s8/rootfix/sheet.png and numbers.json

Inputs (see docs/slab.md for how they were rendered):
- out/ru/vf/<v>/{pbrt,cyc,cyc_orient}.exr       vfilm v1-v3: pbrt, Cycles before the fix, after (GPU, 4096 spp, seed 0)
- out/s8/rootfix/guan/{pbrt,cyc_before,cyc_after}.exr     the Guan heirloom card (Cycles 1024 spp, seed 0)
- out/materials/guan_glaze/lt/p_gap_t15/raw.exr (pbrt crop), .../gap_t15/cyc1.exr (old, open glaze),
  out/s8/rootfix/lt_gap_t15/cyc1_new.exr (sealed, fixed adapter; 512 spp, seed 1)
- out/s8/rootfix/06/{f0_old,f0_pre,f0_new}.exr   shot 6 frame 0, Cycles 128 spp + denoise: old (open glaze, S4
  adapter), sealed with the adapter before the fix, sealed with the fix
The pictures are developed with one white balance (5500 K, the cards' camera) and one exposure per row (the row's
reference at 18% grey), so brightness differences inside a row are real.
"""
import json
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(0, HERE)
import camera  # noqa: E402
import vfilm as VF  # noqa: E402

R = os.path.join(ROOT, "out/s8/rootfix")
FONT = "/System/Library/Fonts/PingFang.ttc"
LT_CROP = (180, 68)          # the pbrt crop's corner in the 960 x 540 frame (cropwindow 0.07 .. , 0.333 ..; aligned)


def cal():
    cam = json.load(open(os.path.join(ROOT, "out/materials/guan_glaze/p5/camera.json")))
    S = camera.Spectra("canon_eos_5d_mkiv")
    return camera.calibrate(S, camera.balance_spectrum(cam))


def lin(raw, c):
    return np.maximum((raw * c["gains"]) @ c["C"].T, 0)


def picture(l, scale, size):
    rgb = camera.srgb_encode(np.clip(l * scale, 0, 1))
    im = Image.fromarray((rgb * 255 + 0.5).astype(np.uint8))
    return im.resize(size, Image.NEAREST if size[0] >= im.size[0] else Image.LANCZOS)


def guan_numbers(p, c, g7):
    from scipy.ndimage import uniform_filter
    loc = uniform_filter(g7, 9)
    line, rest = g7 < 0.97 * loc, g7 > loc       # tests/slab/guan_card.py's mask, from the third render (seed 7)
    k = lambda im: float((im[..., 1][line] / uniform_filter(im[..., 1], 9)[line]).mean())
    return {"frame_G": float(c[..., 1].mean() / p[..., 1].mean()), "lines_G": float(c[line, 1].mean() / p[line, 1].mean()),
            "off_G": float(c[rest, 1].mean() / p[rest, 1].mean()), "contrast": k(c), "contrast_pbrt": k(p)}


def main():
    c = cal()
    num = {}
    rows = []                         # (title, [(image, label)], note)
    # vfilm
    for v, title in (("v1_vert", "竖直的膜 v1"), ("v2_t15", "斜 15° 的膜 v2"), ("v3_t15_dep", "斜 15° + 沉积 v3")):
        d = os.path.join(ROOT, "out/ru/vf", v)
        m = {r: float(VF.profile(os.path.join(d, f"{r}.exr"))[0].mean()) for r in ("pbrt", "cyc", "cyc_orient")}
        num[v] = m
        L = {r: lin(camera.read_raw(os.path.join(d, f"{r}.exr")), c) for r in m}
        s = 0.18 / L["pbrt"][..., 1].mean()
        size = (384, 216)
        rows.append((title, [(picture(L["pbrt"], s, size), f"pbrt  {m['pbrt']:.5f}"),
                             (picture(L["cyc"], s, size), f"Cycles 修前  {m['cyc']:.5f}  ({m['cyc'] / m['pbrt']:.3f})"),
                             (picture(L["cyc_orient"], s, size),
                              f"Cycles 修后  {m['cyc_orient']:.5f}  ({m['cyc_orient'] / m['pbrt']:.4f})")],
                     "一个周期的平均 / 主光 [M];括号里是对 pbrt 的比"))
    num["v0_nofilm"] = {r: float(VF.profile(os.path.join(ROOT, "out/ru/vf/v0_nofilm", f"{r}.exr"))[0].mean())
                        for r in ("pbrt", "cyc")}
    # Guan card
    p = camera.read_raw(os.path.join(R, "guan/pbrt.exr"))
    g7 = camera.read_raw(os.path.join(ROOT, "out/ru/guan_check/r/cyc-heirloom-s7.exr"))[..., 1]
    G = {}
    imgs = []
    Lp = lin(p, c)
    s = 0.18 / Lp[..., 1].mean()
    box = (slice(68, 203), slice(120, 360))
    for nm, lab in (("pbrt", "pbrt"), ("cyc_before", "Cycles 修前"), ("cyc_after", "Cycles 修后")):
        im = p if nm == "pbrt" else camera.read_raw(os.path.join(R, f"guan/{nm}.exr"))
        if nm != "pbrt":
            G[nm] = guan_numbers(p, im, g7)
            lab += f"  整帧 {G[nm]['frame_G']:.4f}  线上 {G[nm]['lines_G']:.4f}  线对比 {G[nm]['contrast']:.3f}"
        else:
            lab += f"  线对比 {guan_numbers(p, p, g7)['contrast']:.3f}"
        imgs.append((picture(lin(im, c)[box], s, (384, 216)), lab))
    num["guan_heirloom"] = G
    rows.append(("官窑传世卡(Cycles/pbrt,G)", imgs, "修前修后差 3e-5:卡上只有 29 个面是反的;线上的差来自釉面凹凸(另一件事)"))
    # linetest gap_t15
    p = camera.read_raw(os.path.join(ROOT, "out/materials/guan_glaze/lt/p_gap_t15/raw.exr"))
    H, W = p.shape[:2]
    y0, x0 = LT_CROP
    o = camera.read_raw(os.path.join(ROOT, "out/materials/guan_glaze/lt/gap_t15/cyc1.exr"))[y0:y0 + H, x0:x0 + W]
    n = camera.read_raw(os.path.join(R, "lt_gap_t15/cyc1_new.exr"))[y0:y0 + H, x0:x0 + W]
    num["linetest_gap_t15"] = {"old_over_pbrt": (o.mean((0, 1)) / p.mean((0, 1))).tolist(),
                               "new_over_pbrt": (n.mean((0, 1)) / p.mean((0, 1))).tolist()}
    Lp = lin(p, c)
    s = 0.18 / Lp[..., 1].mean()
    sub = (slice(0, 181), slice(0, 322))
    q = num["linetest_gap_t15"]
    rows.append(("线的试片 gap_t15", [
        (picture(Lp[sub], s, (384, 216)), "pbrt"),
        (picture(lin(o, c)[sub], s, (384, 216)), "Cycles 旧(釉开着)  " + " ".join(f"{x:.3f}" for x in q["old_over_pbrt"])),
        (picture(lin(n, c)[sub], s, (384, 216)), "Cycles 新(封口)  " + " ".join(f"{x:.3f}" for x in q["new_over_pbrt"]))],
        "整帧对 pbrt 的比 R G B [M];这张的膜没有反的面,差全来自釉封口"))
    # shot 6
    F = {k: camera.read_raw(os.path.join(R, f"06/{k}.exr")) for k in ("f0_old", "f0_pre", "f0_new")}
    ref = F["f0_old"][..., 1].mean()
    num["shot06_f0"] = {k: (F[k].mean((0, 1)) / F["f0_old"].mean((0, 1))).tolist() for k in F}
    lo = slice(675, 1080)                 # the lower part of the frame, where the bare films are
    num["shot06_f0_lower"] = {k: float(F[k][lo, :, 1].mean() / F["f0_old"][lo, :, 1].mean()) for k in F}
    L0 = lin(F["f0_old"], c)
    s = 0.18 / L0[..., 1].mean()
    lab = {"f0_old": "旧(釉开着,S4 的转换)", "f0_pre": "封口,修前的转换", "f0_new": "封口,修后"}
    rows.append(("第 6 镜第 0 帧(对旧的比,G)", [
        (picture(lin(F[k], c), s, (384, 216)),
         f"{lab[k]}  {num['shot06_f0'][k][1]:.3f} / 下部 {num['shot06_f0_lower'][k]:.3f}") for k in F],
        "Cycles 128 spp + 降噪 [M];预览画质"))
    crop = (slice(800, 1016), slice(760, 1144))   # 1:1, the lower middle
    rows.append(("第 6 镜第 0 帧,1:1 局部", [(picture(lin(F[k], c)[crop], s, (384, 216)), lab[k]) for k in F],
                 "第二代裂缝的空气膜(cracks_g2_bare)67386 个面全是反的:修前它在 Cycles 里不反光"))
    del ref
    # draw
    f_t = ImageFont.truetype(FONT, 22)
    f_l = ImageFont.truetype(FONT, 15)
    pad, colw, imh = 16, 384, 216
    rowh = 34 + imh + 26 + 22
    Wd = pad + 3 * (colw + pad)
    head = 70
    sheet = Image.new("RGB", (Wd, head + rowh * len(rows) + pad), (246, 244, 239))
    dr = ImageDraw.Draw(sheet)
    dr.text((pad, 14), "Cycles 法线朝向修复 + 釉封口:修前 / 修后 / pbrt", font=ImageFont.truetype(FONT, 26), fill=(20, 20, 20))
    dr.text((pad, 46), "同一台 mini GPU、同种子;每行一个曝光(以本行参照为 18% 灰),所以行内的明暗差是真的",
            font=f_l, fill=(90, 90, 90))
    y = head
    for title, cells, note in rows:
        dr.text((pad, y + 4), title, font=f_t, fill=(20, 20, 20))
        for i, (im, label) in enumerate(cells):
            x = pad + i * (colw + pad)
            sheet.paste(im, (x, y + 34))
            dr.text((x, y + 34 + imh + 4), label, font=f_l, fill=(30, 30, 30))
        dr.text((pad, y + 34 + imh + 26), note, font=f_l, fill=(110, 80, 40))
        y += rowh
    os.makedirs(R, exist_ok=True)
    sheet.save(os.path.join(R, "sheet.png"))
    json.dump(num, open(os.path.join(R, "numbers.json"), "w"), indent=1)
    print(json.dumps(num, indent=1))
    print("->", os.path.join(R, "sheet.png"))


if __name__ == "__main__":
    main()
