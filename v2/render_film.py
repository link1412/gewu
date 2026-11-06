"""Render the film's shots, each with the command that made the frames in the film, and put them where film.py reads them.

    python3 v2/render_film.py --list            every shot, and whether its frames are there
    python3 v2/render_film.py s30_huali s02_yaobian
    python3 v2/render_film.py --all             the shots that have no frames yet, in the film's order
    python3 v2/render_film.py --force s30_huali render again over what is there
    python3 v2/film.py                          then cut the film from the frames (see README.md)

GEWU_ENDS=1 renders only the first and last frame of a moving shot, with their real motion blur, to compare with the film quickly. A shot rendered that way counts as not done.
"""
import glob
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "out", "v2")
FINAL = {"GEWU_MOVE": "final"}


def still(script, *args, cand=False):
    return {"steps": [({}, script, list(args) or ["final"])], "cand": cand}


def move(script, *args, rename=None):
    return {"steps": [(FINAL, script, list(args) or ["final"])], "rename": rename}


# Shot -> how it was made. rename: the scripts write a candidate under its own name so as not to overwrite the film's frames; the film reads the second folder.
# torch: the shot's solver needs torch and an NVIDIA GPU.
SHOTS = {
    "s01_moyun": {"steps": [({}, "s38_richu.py", ["take", "final"])]},  # writes s01_moyun and s38_richu
    "s02_yaobian": move("s02_yaobian.py"),
    "s05_yinni": still("s05_yinni.py", cand=True),
    "s06_junyao": move("s06_junyao.py", rename=("s06_junyao_cand_move_final", "s06_junyao_move_final")),
    "s07_cijing": still("s07_cijing.py", cand=True),
    "s09_yinxing": {"steps": [({}, "s09_ginkgo.py", ["take", "final"])], "rename": ("s09_yinxing_take_cand", "s09_yinxing_take_final")},
    "s61_tihong": move("s61_tihong.py"),
    "s11_jiangdou": still("s11_jiangdou.py"),
    "s59_suxiu": move("s59_suxiu.py", "final", "lan"),
    "s54_zoumadeng": {"steps": [({}, "s54_zoumadeng.py", ["take", "final"])]},
    "s15_zheshan": {"steps": [({}, "s15_zheshan.py", ["open", "final", "24"])], "rename": ("s15_zheshan_open_move_final", "s15_zheshan_move_final")},
    "s16_lizhi_v1": still("s16_lizhi_v1.py"),
    "s55_diancui": move("s55_diancui.py", rename=("s55_diancui_cand_move_final", "s55_diancui_move_final")),
    "s14_datiehua": {"steps": [({}, "s14_datiehua.py", ["take", "final"])]},
    "s66_xieyang": move("s66_xieyang.py"),
    "s46_luopan": {"steps": [(FINAL, "s46_luopan.py", ["final"]), ({}, "s46_luopan.py", ["deliver"])], "rename": ("s46_luopan_take_cand", "s46_luopan_take_final")},
    "s20_denglong": still("s20_denglong.py"),
    "s24_jianzhi": {
        "steps": [({}, "s24_jianzhi.py", ["final"]), ({}, "s24_wind.py", ["--frames=24"]), ({}, "s24_jianzhi.py", ["wind", "final"])],
        "rename": ("s24_jianzhi_wind_move_final", "s24_jianzhi_move_final"),
    },
    "s63_nanhong": {"steps": [({}, "s63_nanhong.py", ["take", "final"])], "rename": ("s63_nanhong_take_cand", "s63_nanhong_take_final")},
    "s27_jinbo": {"steps": [({}, "s27_jinbo.py", ["take", "final"])], "rename": ("s27_jinbo_take_cand", "s27_jinbo_take_final")},
    "s28_dehua": move("s28_dehua.py"),
    "s39_hehua": {
        "steps": [({}, "s39_cand.py", ["take", "final"]), ({}, "s39_cand.py", ["deliver", os.path.join(OUT, "s39_hehua_wind_move_final")])],
        "rename": ("s39_hehua_take_cand", "s39_hehua_take_final"),
    },
    "s19_luodian": still("s19_luodian.py", "look", "final"),
    "s35_kuangcao": still("s35_kuangcao.py", cand=True),
    "s76_yidi": {"steps": [({}, "s76_yidi.py", ["take", "n_pass=480000000,soft=0.55,looks=[6.0],frames=36,z_cam=-7.698"])], "rename": ("s76_yidi_move_take", "s76_yidi_move_final"), "torch": True},
    "s73_heisan": still("s73_heisan.py"),
    "s45_kongque": {"steps": [({}, "s45_kongque.py", ["flick", "final"])], "rename": ("s45_kongque_flick_move_final", "s45_kongque_move_final")},
    "s36_nanzhu": move("s36_nanzhu.py", rename=("s36_nanzhu_cand_move_final", "s36_nanzhu_move_final")),
    "s30_huali": still("s30_huali.py"),
    "s50_qinghua": move("s50_qinghua.py"),
    "s37_jinyu": {"steps": [({}, "s37_jinyu.py", ["final", "--take=24"])]},
    "s49_falang": move("s49_falang_v1.py", rename=("s49_falang_cand_move_final", "s49_falang_move_final")),
    "s69_mutan_raw": {"steps": [({}, "s69_mutan_raw.py", ["take_prep", "final"]), ({}, "s69_mutan_raw.py", ["take_render", "final"])], "rename": ("s69_mutan_move_final", "s69_mutan_raw_move_final"), "torch": True},
    "s38_richu": {"same_as": "s01_moyun"},
}


def frames_of(src):
    """The frames film.py would use: a count, or 0."""
    n = len(glob.glob(os.path.join(OUT, f"{src}_move_final", "take.linear_[0-9][0-9][0-9].npy")))
    n = n or len(glob.glob(os.path.join(OUT, f"{src}_take_final", "f[0-9][0-9][0-9].png")))
    return n or int(os.path.exists(os.path.join(OUT, src, "final.linear.npy")))


def cut_lengths():
    return [s["src"] for s in json.load(open(os.path.join(HERE, "cut.json")))["shots"]]


def render(src):
    r = SHOTS[src]
    if "same_as" in r:
        src, r = r["same_as"], SHOTS[r["same_as"]]
    print(f"== {src}", flush=True)
    for env, script, args in r["steps"]:
        cmd = [sys.executable, "-I", os.path.join(HERE, "stills", script), *args]
        print("  ", " ".join(f"{k}={v}" for k, v in env.items()), script, " ".join(args), flush=True)
        subprocess.run(cmd, cwd=ROOT, env={**os.environ, **env}, check=True)
    if r.get("cand"):
        d = os.path.join(OUT, src)
        for f in glob.glob(os.path.join(d, "cand.*")):
            os.replace(f, os.path.join(d, "final." + os.path.basename(f)[len("cand.") :]))
    if r.get("rename"):
        a, b = (os.path.join(OUT, x) for x in r["rename"])
        if os.path.exists(b):
            shutil.rmtree(b)
        os.replace(a, b)


def main():
    args = sys.argv[1:]
    force = "--force" in args
    names = [a for a in args if not a.startswith("--")]
    order = cut_lengths()
    missing = [s for s in order if s not in SHOTS]
    if missing:
        raise SystemExit(f"no recipe for {missing}")
    if "--list" in args or not args:
        for s in order:
            r = SHOTS[s]
            r = SHOTS[r["same_as"]] if "same_as" in r else r
            print(f"{s:16s} {frames_of(s):4d} frames  {r['steps'][0][1]}{'  (needs torch and an NVIDIA GPU)' if r.get('torch') else ''}")
        return
    if "--all" in args:
        names = [s for s in order if not frames_of(s)]
    unknown = [n for n in names if n not in SHOTS]
    if unknown:
        raise SystemExit(f"unknown shots {unknown}; see --list")
    for s in names:
        if force or not frames_of(s):
            render(s)
        else:
            print(f"{s}: frames are there, skipped (--force to render again)")


main()
