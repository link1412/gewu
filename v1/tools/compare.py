"""Put our film next to the original, frame for frame.

Our frames live in one directory with the original's global numbering:
out/film/f0000.png … f0499.png (25 fps). Shots that are not rendered yet show
the framing template (where the arc has to be) instead.

    python3 -I tools/compare.py guide  out/guide            # framing templates for every shot
    python3 -I tools/compare.py seam   out/cmp/seam.mp4     # left half original, right half ours: the arcs join at the seam
    python3 -I tools/compare.py stack  out/cmp/stack.mp4    # original above, ours below
    python3 -I tools/compare.py check  6                    # does our shot 6 sit on the original's arc?

Options: --ours DIR (default out/film), --shots 1-14 (default all), --orig ref/opus55.mp4.
"""

import argparse
import json
import os
import subprocess
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import spec_measure as sm  # noqa: E402

FW, FH = 1920, 1080
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# How viewers see the original: browsers decode an untagged HD stream as BT.709 (ffmpeg's own
# default would be BT.601, a few code values off in saturated colours). camera.py decodes ours the same way.
DECODE_VF = "scale=in_color_matrix=bt709:in_range=tv,format=rgb24"


def load_spec():
    with open(os.path.join(ROOT, "spec/shots.json")) as f:
        return json.load(f)


def shot_range(arg, n):
    if not arg:
        return list(range(1, n + 1))
    out = []
    for part in arg.split(","):
        a, _, b = part.partition("-")
        out += list(range(int(a), int(b or a) + 1))
    return out


def read_original(path):
    raw = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", path, "-vf", DECODE_VF,
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, FH, FW, 3)


def read_png(path):
    raw = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", path, "-vf", f"scale={FW}:{FH}",
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(FH, FW, 3)


def arc_poly(arc):
    """The spec arc as y(x) in pixels of a 1920x1080 frame (parabola through apex with the measured sagitta)."""
    ax, ay, s = arc["apex_x"] * FW, arc["apex_y"] * FH, arc["sagitta_of_width"] * FW
    a = s / ((FW / 2) ** 2)
    return lambda x: ay + a * (x - ax) ** 2


def draw_arc(img, arc, color=(255, 64, 48), thick=3):
    y_of = arc_poly(arc)
    for x in range(FW):
        y = int(round(y_of(x)))
        img[max(0, y - thick // 2):min(FH, y + thick // 2 + 1), x] = color
    ax, ay = int(arc["apex_x"] * FW), int(arc["apex_y"] * FH)
    img[max(0, ay - 9):ay + 10, max(0, ax - 1):ax + 2] = (64, 255, 96)
    img[max(0, ay - 1):ay + 2, max(0, ax - 9):ax + 10] = (64, 255, 96)


def template(shot):
    """What a not-yet-rendered frame shows: dark/light sky as measured, the arc it must sit on."""
    sky = shot["sky_luma"] or 40
    img = np.full((FH, FW, 3), int(sky), np.uint8)
    if shot["arc"]:
        y_of = arc_poly(shot["arc"])
        yy = np.arange(FH)[:, None]
        below = yy > y_of(np.arange(FW))[None, :]
        img[below] = np.array(shot["object_rgb"] or (90, 90, 90), np.uint8)
        draw_arc(img, shot["arc"])
    return img


def frames_of(spec, shots):
    for sh in spec["shots"]:
        if sh["shot"] in shots:
            for f in range(sh["frame_in"], sh["frame_out"]):
                yield sh, f


def ours_frame(ours_dir, f, sh):
    p = os.path.join(ours_dir, f"f{f:04d}.png")
    return read_png(p) if os.path.exists(p) else template(sh)


def encode(frames, dst, w, h):
    os.makedirs(os.path.dirname(os.path.abspath(dst)), exist_ok=True)
    p = subprocess.Popen(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
                          "-s", f"{w}x{h}", "-r", "25", "-i", "-", "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p", dst],
                         stdin=subprocess.PIPE)
    for fr in frames:
        p.stdin.write(np.ascontiguousarray(fr).tobytes())
    p.stdin.close()
    p.wait()


def cmd_guide(a, spec):
    os.makedirs(a.dst, exist_ok=True)
    orig = read_original(a.orig)
    for sh in spec["shots"]:
        if sh["shot"] not in a.shots_list:
            continue
        f = (sh["frame_in"] + sh["frame_out"]) // 2
        o = orig[f].copy()
        if sh["arc"]:
            draw_arc(o, sh["arc"])
        t = template(sh)
        side = np.concatenate([o[::2, ::2], t[::2, ::2]], axis=1)
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
                        "-s", f"{FW}x{FH // 2}", "-i", "-", os.path.join(a.dst, f"shot{sh['shot']:02d}.png")],
                       input=np.ascontiguousarray(side).tobytes(), check=True)
    print(f"guides -> {a.dst}")


def cmd_seam(a, spec):
    orig = read_original(a.orig)

    def gen():
        for sh, f in frames_of(spec, a.shots_list):
            o = ours_frame(a.ours, f, sh)
            fr = np.concatenate([orig[f][:, :FW // 2], o[:, FW // 2:]], axis=1)
            fr[:, FW // 2 - 1:FW // 2 + 1] = 0
            yield fr
    encode(gen(), a.dst, FW, FH)
    print(f"seam -> {a.dst}")


def cmd_stack(a, spec):
    orig = read_original(a.orig)

    def gen():
        for sh, f in frames_of(spec, a.shots_list):
            yield np.concatenate([orig[f], ours_frame(a.ours, f, sh)], axis=0)[::2, ::2]
    encode(gen(), a.dst, FW // 2, FH)
    print(f"stack -> {a.dst}")


def cmd_check(a, spec):
    sh = next(s for s in spec["shots"] if s["shot"] == int(a.dst))
    if not sh["arc"]:
        sys.exit(f"shot {sh['shot']}: arc is measured by hand ({sh['arc_manual_reason']}); check it by eye with `guide`")
    f = (sh["frame_in"] + sh["frame_out"]) // 2
    p = os.path.join(a.ours, f"f{f:04d}.png")
    if not os.path.exists(p):
        sys.exit(f"missing {p}: render shot {sh['shot']} first")
    im = read_png(p)[::4, ::4].astype(np.float32)          # 480x270, the size the spec was measured at
    _, ax, ay, sag, inl, res = sm.fit_arc(im)
    t = sh["arc"]
    print(f"shot {sh['shot']} frame {f}: apex ({ax:.3f},{ay:.3f}) vs ({t['apex_x']:.3f},{t['apex_y']:.3f}); "
          f"sagitta {100 * sag:.1f}% vs {100 * t['sagitta_of_width']:.1f}%  (fit inliers {inl:.2f}, resid {res:.1f}px)")
    ok = abs(ay - t["apex_y"]) < 0.01 and abs(ax - t["apex_x"]) < 0.02 and abs(sag / t["sagitta_of_width"] - 1) < 0.1
    print("ok: sits on the original's arc" if ok else "off: adjust the camera (apex within 1% of height, sagitta within 10%)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["guide", "seam", "stack", "check"])
    ap.add_argument("dst")
    ap.add_argument("--ours", default=os.path.join(ROOT, "out/film"))
    ap.add_argument("--orig", default=os.path.join(ROOT, "ref/opus55.mp4"))
    ap.add_argument("--shots", default="")
    a = ap.parse_args()
    spec = load_spec()
    a.shots_list = shot_range(a.shots, len(spec["shots"]))
    {"guide": cmd_guide, "seam": cmd_seam, "stack": cmd_stack, "check": cmd_check}[a.cmd](a, spec)


if __name__ == "__main__":
    main()
