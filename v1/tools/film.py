"""The whole film, always playable next to the original (DESIGN 0, S8).

    python3 -I tools/film.py build            # spec/film.json + spec/shots.json -> out/film/{film,side,stack}.mp4, fNNNN.png, index.html
    python3 -I tools/film.py build --no-check # skip the self-check (frame counts, cuts, arcs, side timing)
    python3 -I tools/film.py check            # the self-check alone -> out/film/check.json (shown in index.html)
    python3 -I tools/film.py status           # which shot comes from where

Every one of the 500 frames comes from the shot's source in spec/film.json (a directory of developed
PNGs named by film frame, or one still held for the shot), or else a placeholder drawn only from the
original's measured numbers in spec/shots.json: the sky at its measured luma (grey: only the luma is
measured, not the sky's colour), the object region below the measured arc in the measured object mean
RGB, a hazard-striped border and a label. Shots whose arc is measured by hand get a flat card.

Encoding is camera.py's: BT.709 limited-range 4:2:0, x264 with the original's own options, cut into the
original's 75-frame segments. The build is incremental: each shot's frames are cached as Y'CbCr, each
75-frame segment (film, side, stack and its decoded PNGs) is redone only when a shot inside it changed,
and the outputs are joined by stream copy.

    out/film/film.mp4    ours, the original's encoder settings (untagged, like the original)
    out/film/side.mp4    3840x1080, original left, ours right (crf 14, re-encoded for viewing only)
    out/film/stack.mp4   960x1080, original above, ours below (half size, like compare.py stack)
    out/film/fNNNN.png   ours decoded the way browsers decode it, for tools/compare.py
    out/film/index.html  local player: frame steps, jump to cuts, the shot table
"""

import argparse
import hashlib
import html
import inspect
import json
import mmap
import os
import re
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor

import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import camera  # noqa: E402
import compare  # noqa: E402
import spec_measure as sm  # noqa: E402

ROOT = camera.ROOT
FW, FH, FPS, SEG = camera.FW, camera.FH, camera.FPS, camera.SEGMENT
FRAME_BYTES = FW * FH * 3 // 2
OUT = os.path.join(ROOT, "out/film")
CACHE = os.path.join(OUT, "cache")
ORIG = os.path.join(ROOT, "ref/opus55.mp4")
MANIFEST = os.path.join(ROOT, "spec/film.json")
FONT = "/System/Library/Fonts/Hiragino Sans GB.ttc"
FF = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y"]
VIEW_X264 = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "14", "-bf", "0", "-g", "25", "-pix_fmt", "yuv420p",
             "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-color_range", "tv"]


# --- inputs ---------------------------------------------------------------------------------------
def load_manifest():
    with open(MANIFEST) as f:
        m = json.load(f)
    return {int(k): v for k, v in m["shots"].items()}


def design_subjects():
    """Shot -> our subject, the "我们" column of DESIGN.md's section 4 table."""
    out = {}
    with open(os.path.join(ROOT, "DESIGN.md")) as f:
        for line in f:
            if re.match(r"^\| \d+", line):
                cells = [c.strip() for c in line.split("|")]
                out[int(re.match(r"\d+", cells[1]).group())] = cells[5]
    return out


def plan():
    """Per shot: spec dict, subject, manifest entry, status, source files (sorted by film frame)."""
    spec = compare.load_spec()
    man, subj = load_manifest(), design_subjects()
    if spec["frames"] != sum(s["frame_out"] - s["frame_in"] for s in spec["shots"]):
        raise SystemExit("spec/shots.json: shot lengths do not add up to its frame count")
    shots = []
    for sh in spec["shots"]:
        n, e = sh["shot"], man.get(sh["shot"], {})
        if n not in subj and "subject" not in e:
            raise SystemExit(f"shot {n}: no subject in DESIGN.md section 4 nor in spec/film.json")
        p = {"spec": sh, "n": n, "subject": e.get("subject", subj.get(n)), "entry": e, "files": []}
        if "frames" in e:
            d = os.path.join(ROOT, e["frames"])
            p["files"] = [os.path.join(d, f"f{f:04d}.png") for f in range(sh["frame_in"], sh["frame_out"])]
            p["kind"] = "frames"
        elif "still" in e:
            p["files"] = [os.path.join(ROOT, e["still"])]
            p["kind"] = "still"
        else:
            p["kind"] = "placeholder"
        missing = [f for f in p["files"] if not os.path.exists(f)]
        if missing:
            raise SystemExit(f"shot {n}: {len(missing)} source frames missing, first {missing[0]}")
        p["status"] = e.get("status", "placeholder") if p["kind"] != "placeholder" else "placeholder"
        p["source"] = e.get("frames") or e.get("still") or "placeholder (spec/shots.json)"
        shots.append(p)
    return spec, shots


# --- placeholders ----------------------------------------------------------------------------------
def _font(size):
    if not os.path.exists(FONT):
        raise SystemExit(f"{FONT}: missing (needed for the Chinese labels)")
    return ImageFont.truetype(FONT, size)


def hazard(img, width=16, period=48, colours=((236, 180, 32), (24, 24, 24))):
    yy, xx = np.mgrid[0:FH, 0:FW]
    border = (xx < width) | (xx >= FW - width) | (yy < width) | (yy >= FH - width)
    stripe = ((xx + yy) // (period // 2)) % 2 == 0
    img[border & stripe] = colours[0]
    img[border & ~stripe] = colours[1]


def placeholder(p):
    """One frame from the original's measured numbers only; obviously not a render."""
    sh = p["spec"]
    if sh["sky_luma"] is None or sh["object_rgb"] is None:
        raise SystemExit(f"shot {p['n']}: spec/shots.json has no sky_luma/object_rgb; measure it, do not guess")
    sky = float(sh["sky_luma"])
    img = np.full((FH, FW, 3), sky, np.float32)
    if sh["arc"]:
        y_of = compare.arc_poly(sh["arc"])
        cover = np.clip(np.arange(FH)[:, None] + 1.0 - y_of(np.arange(FW) + 0.0)[None, :], 0, 1)[..., None]
        img = img * (1 - cover) + np.array(sh["object_rgb"], np.float32) * cover
    img = np.clip(np.round(img), 0, 255).astype(np.uint8)
    hazard(img)
    im = Image.fromarray(img)
    d = ImageDraw.Draw(im)
    ink = (245, 245, 245) if sky < 140 else (16, 16, 16)
    r, g, b = sh["object_rgb"]
    if sh["arc"]:
        a = sh["arc"]
        meas = (f"原片量出:天 {sky:.0f} · 物 {r},{g},{b} · 弧顶 {a['apex_x']:.2f},{a['apex_y']:.2f}"
                f" · 矢高 {100 * a['sagitta_of_width']:.1f}%")
    else:
        meas = f"弧要手量({sh['arc_manual_reason']});天 {sky:.0f} · 物 {r},{g},{b}"
        f = _font(260)
        t = f"{p['n']:02d}"
        w = d.textlength(t, font=f)
        d.text(((FW - w) / 2, FH / 2 - 190), t, font=f, fill=ink)
        f2 = _font(48)
        w2 = d.textlength(p["subject"], font=f2)
        d.text(((FW - w2) / 2, FH / 2 + 110), p["subject"], font=f2, fill=ink)
    x, y = 44, 40
    d.text((x, y), f"{p['n']:02d}  占位  PLACEHOLDER", font=_font(32), fill=ink)
    d.text((x, y + 46), p["subject"], font=_font(26), fill=ink)
    d.text((x, y + 84), f"帧 {sh['frame_in']}–{sh['frame_out'] - 1} · {sh['seconds']} s", font=_font(20), fill=ink)
    d.text((x, y + 112), meas, font=_font(20), fill=ink)
    return np.asarray(im)


# --- caches ----------------------------------------------------------------------------------------
def code_hash(*objs):
    h = hashlib.sha1()
    for o in objs:
        h.update((inspect.getsource(o) if callable(o) else str(o)).encode())
    return h.hexdigest()


SHOT_CODE = code_hash(hazard, placeholder, camera.ycbcr420, camera.read_png16, FONT)


def file_sig(path):
    st = os.stat(path)
    return [os.path.relpath(path, ROOT), st.st_size, st.st_mtime_ns]


def shot_key(p):
    used = ("frame_in", "frame_out", "seconds", "arc", "arc_manual_reason", "sky_luma", "object_rgb")
    blob = json.dumps({"code": SHOT_CODE, "spec": {k: p["spec"].get(k) for k in used}, "subject": p["subject"], "entry": p["entry"],
                       "kind": p["kind"], "files": [file_sig(f) for f in p["files"]]}, sort_keys=True, ensure_ascii=False)
    return hashlib.sha1(blob.encode()).hexdigest()


def read_json(path):
    try:
        with open(path) as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def write_atomic_json(path, obj):
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
    os.replace(tmp, path)


def planes(rgb01):
    return b"".join(pl.tobytes() for pl in camera.ycbcr420(rgb01))


def build_shot(p):
    """Shot -> cache/shotNN.yuv (one frame for a placeholder or a still, else every frame)."""
    n = p["n"]
    path, meta = os.path.join(CACHE, f"shot{n:02d}.yuv"), os.path.join(CACHE, f"shot{n:02d}.json")
    key = shot_key(p)
    old = read_json(meta)
    if old and old["key"] == key and os.path.exists(path):
        return key, False
    tmp = path + ".tmp"
    with open(tmp, "wb") as f:
        if p["kind"] == "placeholder":
            f.write(planes(placeholder(p) / 255.0))
        else:
            for src in p["files"]:
                f.write(planes(camera.read_png16(src)))
    os.replace(tmp, path)
    nf = 1 if p["kind"] != "frames" else len(p["files"])
    write_atomic_json(meta, {"key": key, "frames": nf, "kind": p["kind"]})
    return key, True


def frame_bytes(p, f, maps):
    mm = maps[p["n"]]
    i = 0 if len(mm) == FRAME_BYTES else f - p["spec"]["frame_in"]
    return mm[i * FRAME_BYTES:(i + 1) * FRAME_BYTES]


def encode_segment(frames, shot_of, maps, dst):
    enc = subprocess.Popen(FF + ["-f", "rawvideo", "-pix_fmt", "yuv420p", "-s", f"{FW}x{FH}", "-r", str(FPS), "-i", "-",
                                 "-c:v", "libx264", "-profile:v", "high", "-x264-params", camera.X264, dst],
                           stdin=subprocess.PIPE)
    for f in frames:
        enc.stdin.write(frame_bytes(shot_of[f], f, maps))
    enc.stdin.close()
    if enc.wait():
        raise SystemExit(f"x264 failed on {dst}")


def view_segment(seg, s, nframes, dst, layout):
    t0 = f"{s * SEG / FPS:.6f}"
    if layout == "side":
        fc = "[0:v][1:v]hstack=inputs=2[v]"
    else:
        fc = "[0:v]scale=960:540:flags=area[a];[1:v]scale=960:540:flags=area[b];[a][b]vstack=inputs=2[v]"
    subprocess.run(FF + ["-ss", t0, "-i", ORIG, "-i", seg, "-filter_complex", fc, "-map", "[v]", "-an",
                         "-frames:v", str(nframes), "-r", str(FPS)] + VIEW_X264 + [dst], check=True)


def decode_pngs(seg, first, nframes):
    subprocess.run(FF + ["-i", seg, "-vf", compare.DECODE_VF, "-frames:v", str(nframes), "-compression_level", "1",
                         "-start_number", str(first), os.path.join(OUT, "f%04d.png")], check=True)


SEG_CODE = code_hash(encode_segment, view_segment, decode_pngs, camera.X264, VIEW_X264, compare.DECODE_VF)


def build_segment(s, frames, shot_of, keys, maps, orig_sig):
    seg = os.path.join(CACHE, f"seg{s}.mp4")
    meta = os.path.join(CACHE, f"seg{s}.json")
    key = hashlib.sha1(json.dumps([SEG_CODE, orig_sig, frames[0], frames[-1],
                                   [keys[shot_of[f]["n"]] for f in frames]]).encode()).hexdigest()
    pngs = [os.path.join(OUT, f"f{f:04d}.png") for f in frames]
    old = read_json(meta)
    outs = [seg] + [os.path.join(CACHE, f"{v}{s}.mp4") for v in ("side", "stack")]
    if old and old["key"] == key and all(map(os.path.exists, outs)) and all(map(os.path.exists, pngs)) \
            and old.get("pngs") == [file_sig(q)[1:] for q in pngs]:
        return False
    tmp = seg + ".tmp.mp4"
    encode_segment(frames, shot_of, maps, tmp)
    os.replace(tmp, seg)
    for v in ("side", "stack"):
        t = os.path.join(CACHE, f"{v}{s}.tmp.mp4")
        view_segment(seg, s, len(frames), t, v)
        os.replace(t, os.path.join(CACHE, f"{v}{s}.mp4"))
    decode_pngs(seg, frames[0], len(frames))
    write_atomic_json(meta, {"key": key, "pngs": [file_sig(q)[1:] for q in pngs]})
    return True


def concat(parts, dst):
    with tempfile.NamedTemporaryFile("w", suffix=".txt", dir=CACHE, delete=False) as f:
        f.writelines(f"file '{q}'\n" for q in parts)
    try:
        subprocess.run(FF + ["-f", "concat", "-safe", "0", "-i", f.name, "-c", "copy", "-movflags", "+faststart",
                             dst + ".tmp.mp4"], check=True)
        os.replace(dst + ".tmp.mp4", dst)
    finally:
        os.unlink(f.name)


# --- commands --------------------------------------------------------------------------------------
def cmd_build(a):
    t0 = time.time()
    os.makedirs(CACHE, exist_ok=True)
    spec, shots = plan()
    n = spec["frames"]
    keys, redone = {}, []
    with ThreadPoolExecutor(a.jobs) as ex:
        for p, (k, did) in zip(shots, ex.map(build_shot, shots)):
            keys[p["n"]] = k
            if did:
                redone.append(p["n"])
    t1 = time.time()
    shot_of = {f: p for p in shots for f in range(p["spec"]["frame_in"], p["spec"]["frame_out"])}
    maps = {}
    for p in shots:
        with open(os.path.join(CACHE, f"shot{p['n']:02d}.yuv"), "rb") as f:
            maps[p["n"]] = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
    orig_sig = file_sig(ORIG)[1:]
    segs = [list(range(s * SEG, min(n, (s + 1) * SEG))) for s in range((n + SEG - 1) // SEG)]
    with ThreadPoolExecutor(a.jobs) as ex:
        did = list(ex.map(lambda sf: build_segment(sf[0], sf[1], shot_of, keys, maps, orig_sig), enumerate(segs)))
    t2 = time.time()
    for v, name in (("seg", "film"), ("side", "side"), ("stack", "stack")):
        concat([os.path.join(CACHE, f"{v}{s}.mp4") for s in range(len(segs))], os.path.join(OUT, f"{name}.mp4"))
    t3 = time.time()
    print(f"shots redone: {redone or 'none'}; segments redone: {[s for s, d in enumerate(did) if d] or 'none'}")
    print(f"time: shots {t1 - t0:.1f} s, segments {t2 - t1:.1f} s, join {t3 - t2:.1f} s")
    if not a.no_check:
        cmd_check(a, spec, shots)
    write_index(spec, shots)
    print(f"build {time.time() - t0:.1f} s -> {os.path.relpath(OUT, ROOT)}/index.html")


def count_frames(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-count_packets", "-select_streams", "v:0", "-show_entries",
                        "stream=nb_read_packets,width,height", "-of", "json", path], capture_output=True, text=True, check=True)
    s = json.loads(r.stdout)["streams"][0]
    return int(s["nb_read_packets"]), s["width"], s["height"]


def cmd_check(a, spec=None, shots=None):
    t0 = time.time()
    if spec is None:
        spec, shots = plan()
    res = {"time": time.strftime("%Y-%m-%d %H:%M:%S")}
    res["frames"] = {k: count_frames(os.path.join(OUT, f"{k}.mp4")) for k in ("film", "side", "stack")}
    res["frames_ok"] = all(v[0] == spec["frames"] for v in res["frames"].values())
    # cuts, found in our film the way spec_measure found them in the original
    v = sm.decode(os.path.join(OUT, "film.mp4"), sm.W, sm.H)
    found, _ = sm.find_cuts(v)
    want = [s["frame_in"] for s in spec["shots"]]
    res["cuts"] = {"found": len(found), "want": len(want), "missing": sorted(set(want) - set(found)),
                   "extra": sorted(set(found) - set(want))}
    # arcs, exactly as compare.py check measures them (mid frame, 480x270, spec_measure.fit_arc)
    arcs = {}
    for sh in spec["shots"]:
        if not sh["arc"]:
            continue
        f = (sh["frame_in"] + sh["frame_out"]) // 2
        im = compare.read_png(os.path.join(OUT, f"f{f:04d}.png"))[::4, ::4].astype(np.float32)
        _, ax, ay, sag, inl, rs = sm.fit_arc(im)
        t = sh["arc"]
        ok = abs(ay - t["apex_y"]) < 0.03 and abs(ax - t["apex_x"]) < 0.03 and abs(sag / t["sagitta_of_width"] - 1) < 0.3
        arcs[sh["shot"]] = {"apex": [round(float(ax), 3), round(float(ay), 3)], "sagitta": round(float(sag), 4),
                            "d_apex_y": round(float(ay - t["apex_y"]), 4), "d_apex_x": round(float(ax - t["apex_x"]), 4),
                            "sag_ratio": round(float(sag / t["sagitta_of_width"]), 3), "ok": bool(ok)}
    res["arcs"] = arcs
    # side.mp4's left half at each cut must be the original's frame there, not its neighbour's
    o = sm.decode(ORIG, sm.W, sm.H)
    sd = sm.decode(os.path.join(OUT, "side.mp4"), 2 * sm.W, sm.H)[:, :, :sm.W]
    bad = []
    for c in want[1:]:
        here, before = np.abs(sd[c] - o[c]).mean(), np.abs(sd[c] - o[c - 1]).mean()
        if not here < before:
            bad.append(c)
    res["side_timing"] = {"cuts_checked": len(want) - 1, "misaligned": bad,
                          "mean_abs_left_vs_original": round(float(np.abs(sd - o).mean()), 2)}
    write_atomic_json(os.path.join(OUT, "check.json"), res)
    na = sum(r["ok"] for r in arcs.values())
    print(f"frames {res['frames']} ok={res['frames_ok']}")
    print(f"cuts found {len(found)}/{len(want)}, missing {res['cuts']['missing']}, extra {res['cuts']['extra']}")
    print(f"arcs ok {na}/{len(arcs)}; worst |d apex y| {max(abs(r['d_apex_y']) for r in arcs.values()):.4f}, "
          f"worst |sag ratio - 1| {max(abs(r['sag_ratio'] - 1) for r in arcs.values()):.3f}")
    for s, r in arcs.items():
        if not r["ok"]:
            print(f"  shot {s}: off {r}")
    print(f"side timing: misaligned at cuts {bad or 'none'}; left half vs original mean |diff| "
          f"{res['side_timing']['mean_abs_left_vs_original']} (8-bit, 480x270)")
    print(f"check {time.time() - t0:.1f} s")
    if a is not None and getattr(a, "cmd", "") == "check":
        write_index(spec, shots)


def cmd_status(a):
    _, shots = plan()
    for p in shots:
        sh = p["spec"]
        print(f"{p['n']:>2} {sh['frame_in']:>3}-{sh['frame_out'] - 1:<3} {sh['seconds']:>4}s  {p['status']:<11} "
              f"{p['source']:<32} {p['subject']}")


# --- the page --------------------------------------------------------------------------------------
PAGE = r"""<!doctype html>
<html lang="zh"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>格物 整片骨架</title>
<style>
:root{--bg:#141414;--panel:#1d1d1d;--line:#333;--fg:#e8e6e1;--dim:#9a978f;--accent:#e2b13c;--prev:#6fa8dc;--fin:#7cc47c;--ph:#5a5852}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:14px/1.5 -apple-system,"PingFang SC","Hiragino Sans GB",sans-serif}
main{max-width:1800px;margin:0 auto;padding:16px}
h1{font-size:18px;font-weight:600;margin:0 0 4px}.sub{color:var(--dim);font-size:12px;margin-bottom:12px}
.labels{display:grid;grid-template-columns:1fr 1fr;color:var(--dim);font-size:12px;margin-bottom:4px}
.labels.stack,.labels.ours{display:none}
video{width:100%;background:#000;display:block}
.bar{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin:8px 0}
button,select{background:var(--panel);color:var(--fg);border:1px solid var(--line);border-radius:4px;padding:4px 10px;font:inherit;cursor:pointer}
button:hover{border-color:var(--dim)}.on{border-color:var(--accent);color:var(--accent)}
#readout{font-variant-numeric:tabular-nums;margin-left:auto}
.strip{display:flex;height:34px;gap:1px;margin:6px 0 4px;cursor:pointer;position:relative}
.strip div{flex:none;font-size:11px;line-height:34px;text-align:center;overflow:hidden;color:#111}
.strip .placeholder{background:var(--ph);color:#ddd}.strip .preview{background:var(--prev)}.strip .final{background:var(--fin)}
.strip .cur{outline:2px solid var(--accent);outline-offset:-2px}
#head{position:absolute;top:-3px;bottom:-3px;width:2px;background:var(--accent);pointer-events:none}
.keys{color:var(--dim);font-size:12px}
table{border-collapse:collapse;width:100%;margin-top:16px;font-size:13px}
th,td{border-bottom:1px solid var(--line);padding:4px 8px;text-align:left;vertical-align:top}
th{color:var(--dim);font-weight:500}td.n{font-variant-numeric:tabular-nums}
tr{cursor:pointer}tr:hover td{background:var(--panel)}tr.cur td{background:#2a2617}
.st{display:inline-block;padding:0 6px;border-radius:3px;color:#111;font-size:12px}
.st.placeholder{background:var(--ph);color:#ddd}.st.preview{background:var(--prev)}.st.final{background:var(--fin)}
.ok{color:var(--fin)}.bad{color:#e06c5c}.src{color:var(--dim);font-family:ui-monospace,Menlo,monospace;font-size:12px}
.check{color:var(--dim);font-size:12px;margin-top:10px}
</style></head><body><main>
<h1>格物 · 整片骨架</h1>
<div class="sub">__BUILT__ · 500 帧 25 fps · 左原片 右我们(side.mp4)。占位帧只用原片量出的数:天的亮度、物体均色、弧。</div>
<div class="labels side" id="lab"><span>原片 ref/opus55.mp4</span><span>我们 out/film/film.mp4</span></div>
<video id="v" src="side.mp4" preload="auto" playsinline muted></video>
<div class="strip" id="strip"><div id="head"></div></div>
<div class="bar">
 <button id="play">播放 ␣</button><button id="prev">← 一帧</button><button id="next">一帧 →</button>
 <button id="pcut">⇧← 上一镜</button><button id="ncut">下一镜 ⇧→</button>
 <button id="loop">循环本镜 L</button>
 <select id="rate"><option value="1">1×</option><option value="0.5">0.5×</option><option value="0.25">0.25×</option></select>
 <select id="view"><option value="side">左右 side</option><option value="stack">上下 stack</option><option value="ours">只看我们 film</option></select>
 <span id="readout"></span>
</div>
<div class="keys">键:空格 播放/暂停 · ← → 一帧 · ⇧← ⇧→ 上/下一个剪辑点 · L 循环本镜 · 1/2/3 切换 side/stack/film · 点表格或色条跳到该镜</div>
<table id="tab"><thead><tr><th>#</th><th>帧</th><th>秒</th><th>我们拍什么</th><th>状态</th><th>来源</th><th>弧(compare.py check)</th></tr></thead><tbody></tbody></table>
<div class="check" id="check"></div>
</main>
<script>
const SHOTS = __SHOTS__, CHECK = __CHECK__, FPS = 25, N = __N__;
const v = document.getElementById('v'), strip = document.getElementById('strip'), head = document.getElementById('head');
const tb = document.querySelector('#tab tbody'), ro = document.getElementById('readout');
let frame = 0, loopShot = false;
const shotAt = f => SHOTS.find(s => f >= s.in && f < s.out) || SHOTS[SHOTS.length - 1];
SHOTS.forEach(s => {
  const d = document.createElement('div');
  d.className = s.status; d.style.width = `calc(${100 * (s.out - s.in) / N}% - 1px)`; d.textContent = s.n;
  d.title = `${s.n} ${s.subject} (${s.status})`; d.onclick = e => { e.stopPropagation(); seek(s.in); }; s.el = d; strip.appendChild(d);
  const tr = document.createElement('tr'); const a = CHECK && CHECK.arcs ? CHECK.arcs[s.n] : null;
  const arc = s.manual ? `手量:${s.manual}` : a ? `<span class="${a.ok ? 'ok' : 'bad'}">${a.ok ? '对上' : '偏'}</span> 弧顶 ${a.apex[0].toFixed(3)},${a.apex[1].toFixed(3)} · 矢高 ${(100 * a.sagitta).toFixed(1)}% / 原片 ${(100 * s.sag).toFixed(1)}%` : '';
  tr.innerHTML = `<td class="n">${s.n}</td><td class="n">${s.in}–${s.out - 1}</td><td class="n">${s.sec}</td><td>${s.subject}</td>` +
    `<td><span class="st ${s.status}">${s.status}</span></td><td class="src">${s.source}${s.note ? '<br>' + s.note : ''}</td><td>${arc}</td>`;
  tr.onclick = () => { seek(s.in); window.scrollTo({top: 0, behavior: 'smooth'}); }; s.tr = tr; tb.appendChild(tr);
});
strip.onclick = e => { const r = strip.getBoundingClientRect(); seek(Math.floor((e.clientX - r.left) / r.width * N)); };
function seek(f) { f = Math.max(0, Math.min(N - 1, f)); v.pause(); frame = f; frameAtLoop = f; v.currentTime = (f + 0.5) / FPS; show(); }
function show() {
  const s = shotAt(frame);
  ro.textContent = `帧 ${frame} / ${N - 1} · ${(frame / FPS).toFixed(2)} s · 第 ${s.n} 镜(${s.in}–${s.out - 1})· ${s.subject} · ${s.status}`;
  SHOTS.forEach(t => { t.el.classList.toggle('cur', t === s); t.tr.classList.toggle('cur', t === s); });
  head.style.left = `${100 * (frame + 0.5) / N}%`;
}
function tick(now, md) { frame = Math.min(N - 1, Math.round(md.mediaTime * FPS));
  if (loopShot && !v.paused) { const s = shotAt(frameAtLoop); if (frame >= s.out - 1 || frame < s.in) { v.currentTime = (s.in + 0.5) / FPS; } }
  show(); v.requestVideoFrameCallback(tick); }
let frameAtLoop = 0;
if ('requestVideoFrameCallback' in HTMLVideoElement.prototype) v.requestVideoFrameCallback(tick);
else v.addEventListener('timeupdate', () => { frame = Math.min(N - 1, Math.floor(v.currentTime * FPS)); show(); });
const cuts = SHOTS.map(s => s.in);
const toggle = () => v.paused ? v.play() : v.pause();
const prevCut = () => seek([...cuts].reverse().find(c => c < frame) ?? 0);
const nextCut = () => seek(cuts.find(c => c > frame) ?? N - 1);
const setLoop = () => { loopShot = !loopShot; frameAtLoop = frame; document.getElementById('loop').classList.toggle('on', loopShot); };
function setView(k) { const f = frame, play = !v.paused; v.src = {side: 'side.mp4', stack: 'stack.mp4', ours: 'film.mp4'}[k];
  document.getElementById('view').value = k; document.getElementById('lab').className = 'labels ' + k;
  v.style.maxWidth = k === 'stack' ? '960px' : ''; v.style.margin = k === 'stack' ? '0 auto' : '';
  v.addEventListener('loadedmetadata', () => { seek(f); v.playbackRate = +document.getElementById('rate').value; if (play) v.play(); }, {once: true}); }
document.getElementById('play').onclick = toggle;
document.getElementById('prev').onclick = () => seek(frame - 1);
document.getElementById('next').onclick = () => seek(frame + 1);
document.getElementById('pcut').onclick = prevCut; document.getElementById('ncut').onclick = nextCut;
document.getElementById('loop').onclick = setLoop;
document.getElementById('rate').onchange = e => v.playbackRate = +e.target.value;
document.getElementById('view').onchange = e => setView(e.target.value);
v.onclick = toggle;
document.addEventListener('keydown', e => {
  if (e.target.tagName === 'SELECT') return;
  if (e.key === ' ') { e.preventDefault(); toggle(); }
  else if (e.key === 'ArrowLeft') { e.preventDefault(); e.shiftKey ? prevCut() : seek(frame - 1); }
  else if (e.key === 'ArrowRight') { e.preventDefault(); e.shiftKey ? nextCut() : seek(frame + 1); }
  else if (e.key === 'l' || e.key === 'L') setLoop();
  else if (e.key in {'1': 1, '2': 1, '3': 1}) setView(['side', 'stack', 'ours'][+e.key - 1]);
});
v.addEventListener('loadedmetadata', () => seek(0), {once: true});
if (CHECK) { const c = CHECK, na = Object.values(c.arcs).filter(a => a.ok).length;
  document.getElementById('check').textContent = `自检 ${c.time}:帧数 film/side/stack = ${c.frames.film[0]}/${c.frames.side[0]}/${c.frames.stack[0]};` +
  `从我们的片子里找到剪辑点 ${c.cuts.found}/${c.cuts.want}(缺 ${c.cuts.missing.join(',') || '无'},多 ${c.cuts.extra.join(',') || '无'});` +
  `弧对上 ${na}/${Object.keys(c.arcs).length};side 左半和原片在剪辑点错位:${c.side_timing.misaligned.join(',') || '无'}。`; }
show();
</script></body></html>
"""


def write_index(spec, shots):
    rows = []
    for p in shots:
        sh = p["spec"]
        rows.append({"n": p["n"], "in": sh["frame_in"], "out": sh["frame_out"], "sec": sh["seconds"],
                     "subject": html.escape(p["subject"]), "status": p["status"], "source": html.escape(p["source"]),
                     "note": html.escape(p["entry"].get("note", "")), "manual": sh["arc_manual_reason"],
                     "sag": sh["arc"]["sagitta_of_width"] if sh["arc"] else None})
    check = read_json(os.path.join(OUT, "check.json"))
    page = (PAGE.replace("__SHOTS__", json.dumps(rows, ensure_ascii=False))
            .replace("__CHECK__", json.dumps(check, ensure_ascii=False))
            .replace("__N__", str(spec["frames"]))
            .replace("__BUILT__", "构建于 " + time.strftime("%Y-%m-%d %H:%M")))
    with open(os.path.join(OUT, "index.html"), "w") as f:
        f.write(page)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("cmd", choices=["build", "check", "status"])
    ap.add_argument("--no-check", action="store_true")
    ap.add_argument("--jobs", type=int, default=2, help="shots/segments in parallel (each x264 uses 5 threads)")
    a = ap.parse_args()
    {"build": cmd_build, "check": cmd_check, "status": cmd_status}[a.cmd](a)


if __name__ == "__main__":
    main()
