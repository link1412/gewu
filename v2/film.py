"""Assemble the film: the shots of v2/cut.json in order, each filled with a take or a still under a slow push, then captions.

    python3 -I v2/film.py                     whole film, out/v2/film/film.mp4, plus sheet.jpg (one frame of every shot)
    python3 -I v2/film.py --sheet             only the contact sheet
    python3 -I v2/film.py --only=15-24        a part of the film, out/v2/film/part.mp4
    python3 -I v2/film.py --master            whole film, lossless RGB, out/v2/film/film_master.mkv
    python3 -I v2/film.py --master --en       the same with English captions and names, out/v2/film/film_master_en.mkv. Only the words differ: they go on after the grain, and the grain's seed is the frame number

An entry of v2/cut.json has `src` (the name of its folder in out/v2) and `len` in rendered frames, and optionally name (what this is, very small in the top left corner), apex_y, caption, end (the last shot, which carries the titles), first, dx, dy, zoom, push, dev, still,
caption_ink, slow. It is shown for shown(entry) frames, see SLOW. Its pictures are found by `src`:
    <src>_move_final/take.linear_###.npy     a real camera move rendered by kit.shoot (GEWU_MOVE=final): scene-linear, developed here frame by frame
    <src>_take_{final,mid,preview}/f###.png   a take, already developed with its own grain
    <src>/{final,mid,preview}.linear.npy      a still; developed here without grain, grain goes on per frame at 1080p
spec/shots.json is what was measured from the original film; the cut no longer has to follow it.
Every frame then goes through darkroom.print_look (the lab's print, the same for the whole film; an entry's `print` overrides it) and film_grain.
A shot without pictures is a labelled grey card, so that the film can be watched while it is being made. No audio: the
original's music is not ours.
"""

import glob
import json
import os
import subprocess
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from darkroom import develop, film_grain, print_look  # noqa: E402
from tween import Tween  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "out", "v2")
W, H, FPS = 1920, 1080, 25
PUSH = 0.03  # scale per second: every still drifts in slowly, as a hand on a slider would
SLOW = 1.15  # the film runs this much slower than it was rendered, in between frames from tween.py. An entry's `slow` overrides it: 1 is as rendered, below 1 is faster

# stand-ins: Songti in place of the 宋刻本集字 the design asks for; Baskerville for the English end card
SONG = (os.environ.get("GEWU_FONT_SONG", "/System/Library/Fonts/Supplemental/Songti.ttc"), int(os.environ.get("GEWU_FONT_SONG_INDEX", 6)))
LATIN = (os.environ.get("GEWU_FONT_LATIN", "/System/Library/Fonts/Supplemental/Baskerville.ttc"), int(os.environ.get("GEWU_FONT_LATIN_INDEX", 0)))
CAPTIONS = ("苟日新", "日日新", "又日新")
# --en, for people who do not read Chinese. One sentence across the three captions, in the end card's face. A name that is missing here is an error, not a guess
CAPTIONS_EN = {"苟日新": "If truly new one day", "日日新": "new day after day", "又日新": "and new again"}
CAPTION_EN_SIZE = 62
NAMES_EN = {
    "墨晕": "Ink bloom", "曜变": "Yohen tenmoku", "印泥": "Seal paste", "钧窑": "Jun ware", "磁青": "Indigo sutra paper", "银杏": "Ginkgo",
    "剔红": "Carved red lacquer", "豇豆红": "Peachbloom glaze", "苏绣": "Suzhou embroidery", "走马灯": "Trotting-horse lantern", "折扇": "Folding fan", "荔枝": "Lychee",
    "点翠": "Kingfisher-feather inlay", "打铁花": "Molten-iron fireworks", "油纸伞": "Oil-paper umbrella", "螺钿": "Mother-of-pearl inlay", "红灯笼": "Red lantern", "剪纸": "Paper-cut",
    "南红": "Nanhong agate", "金箔": "Gold leaf", "德化白瓷": "Dehua porcelain", "荷花": "Lotus", "螺钿竹": "Mother-of-pearl bamboo", "狂草": "Wild cursive",
    "一滴": "A drop of ink", "油纸伞·黑": "Oil-paper umbrella on black", "孔雀羽": "Peacock feather", "南珠": "Nanzhu pearl", "黄花梨": "Huanghuali wood", "青花": "Blue-and-white porcelain",
    "金鱼": "Goldfish", "珐琅": "Cloisonné", "木炭": "Charcoal", "日出": "Sunrise",
}
NAME_SIZE, NAME_X, NAME_Y, NAME_OPACITY = 26, 54, 46, 0.88  # the name of each subject: size in pixels at 1080p, left and top margins of the glyphs.


def cut():
    return json.load(open(os.path.join(ROOT, "v2", "cut.json")))["shots"]


def shown(ov):
    """Frames this entry is on screen: as many as fit before its last rendered frame, so that the take never runs off its end and halts for a frame."""
    return int((ov["len"] - 1) * ov.get("slow", SLOW) + 1e-9) + 1


def find(ov):
    """Return ('take', frames, q) or ('still', linear path, develop dict, q) or None."""
    src = ov["src"]
    mv = sorted(glob.glob(os.path.join(OUT, f"{src}_move_final", "take.linear_[0-9][0-9][0-9].npy")))
    if mv and not ov.get("still"):
        dj = os.path.join(OUT, f"{src}_move_final", "develop.json")
        return ("move", mv, json.load(open(dj)) if os.path.exists(dj) else {}, "final")
    for q in ("final", "mid", "preview"):
        frames = sorted(glob.glob(os.path.join(OUT, f"{src}_take_{q}", "f[0-9][0-9][0-9].png")))
        if frames and not ov.get("still"):
            return ("take", frames, q)
    for q in ("final", "mid", "preview"):
        p = os.path.join(OUT, src, f"{q}.linear.npy")
        if os.path.exists(p):
            dj = p[: -len(".linear.npy")] + ".develop.json"
            dev = json.load(open(dj)) if os.path.exists(dj) else {}
            return ("still", p, dev, q)
    return None


def text_mask(text, font, size, bloom=1.0):
    """White text as an alpha mask at 1080p: drawn at 4x, reduced, with the faint bloom of letters on a bright screen. The mask has 40 pixels of margin on every side."""
    f = ImageFont.truetype(font[0], size * 4, index=font[1])
    x0, y0, x1, y1 = f.getbbox(text)
    pad = 160
    im = Image.new("L", (x1 - x0 + 2 * pad, y1 - y0 + 2 * pad), 0)
    ImageDraw.Draw(im).text((pad - x0, pad - y0), text, fill=255, font=f)
    a = cv2.resize(np.asarray(im, np.float32) / 255.0, None, fx=0.25, fy=0.25, interpolation=cv2.INTER_AREA)
    sharp = cv2.GaussianBlur(a, (0, 0), 0.55)
    return np.clip(sharp + bloom * (0.22 * cv2.GaussianBlur(a, (0, 0), 3.5) + 0.12 * cv2.GaussianBlur(a, (0, 0), 11.0)), 0.0, 1.0)


def put_text(img, mask, cx, cy, opacity=1.0, ink=None):
    """Composite the mask at a sub-pixel position; the ink is white, or black when the picture behind it is light."""
    h, w = mask.shape
    M = np.array([[1.0, 0.0, cx * W - w / 2.0], [0.0, 1.0, cy * H - h / 2.0]])
    a = cv2.warpAffine(mask, M, (W, H), flags=cv2.INTER_LINEAR)
    if ink is None:
        core = a > 0.5
        lum = float(img[core].mean()) if core.any() else 0.0
        ink = (0.02, 0.02, 0.02) if lum > 0.62 else (0.98, 0.97, 0.95)
    a = (a * opacity)[..., None]
    return img * (1.0 - a) + np.array(ink, np.float32) * a


class Shot:
    def __init__(self, n, a, ov):
        self.n = n
        self.a, self.b = a, a + shown(ov)
        self.ov = ov
        self.slow = ov.get("slow", SLOW)
        self.src = find(ov)
        self.still = None
        self.tw = None
        self.apex_y = ov.get("apex_y", 0.48)  # where this picture really has its arc

    def picture(self):
        if self.still is None:
            kind = self.src[0]
            assert kind == "still"
            dev = dict(self.src[2])
            dev.update(self.ov.get("dev", {}))
            self.grain = dev.get("grain", 1.2)
            dev["grain"] = 0
            L = np.load(self.src[1]).astype(np.float32)
            self.still = develop(L, **dev)
        return self.still

    def rendered(self, k):
        """The take's picture at k rendered frames into this shot, between two of them if need be."""
        if self.tw is None:
            frames = self.src[1]
            if self.src[0] == "move":
                self.tw = Tween(lambda j: np.load(frames[j]).astype(np.float32), len(frames))
            else:
                self.tw = Tween(lambda j: cv2.imread(frames[j], cv2.IMREAD_UNCHANGED)[..., ::-1].astype(np.float32) / 65535.0, len(frames), linear=False)
        return self.tw.at(self.ov.get("first", 0) + k)

    def shifted(self, d):
        """A take or a move with the override's dx, dy (fractions of the frame, + is down/right), so that a dark sky can be moved without a new render. Whole pixels, so that the grain a take carries stays sharp; the sky mirrors in rather than repeating its top row, which would draw that row's grain as vertical streaks."""
        h, w = d.shape[:2]
        dx, dy = round(self.ov.get("dx", 0.0) * w), round(self.ov.get("dy", 0.0) * h)
        if not (dx or dy):
            return d
        return cv2.warpAffine(d, np.array([[1.0, 0.0, dx], [0.0, 1.0, dy]], np.float64), (w, h), flags=cv2.INTER_NEAREST, borderMode=cv2.BORDER_REFLECT_101)

    def frame(self, i):
        """Frame number i of the film, as float RGB at 1080p."""
        k = (i - self.a) / self.slow  # in rendered frames
        t = k / FPS
        if self.src is None:
            img = np.full((H, W, 3), 28, np.uint8)
            cv2.putText(img, f"{self.n}", (W // 2 - 40, H // 2), cv2.FONT_HERSHEY_SIMPLEX, 2.0, (100, 100, 100), 3, cv2.LINE_AA)
            return img.astype(np.float32) / 255.0
        look = self.ov.get("print", {})
        if self.src[0] == "move":
            dev = dict(self.src[2])
            dev.update(self.ov.get("dev", {}))
            gr = dev.get("grain", 1.2)
            dev["grain"] = 0
            d = develop(self.rendered(k), **dev)
            if d.shape[1] != W:
                d = cv2.resize(d, (W, H), interpolation=cv2.INTER_AREA)
            return film_grain(print_look(np.clip(self.shifted(d), 0.0, 1.0), **look), self.ov.get("grain", 1.0) * gr / 1.2, seed=100000 + i)
        if self.src[0] == "take":
            d = self.rendered(k)
            if d.shape[1] != W:
                d = cv2.resize(d, (W, H), interpolation=cv2.INTER_AREA if d.shape[1] > W else cv2.INTER_CUBIC)
            return film_grain(print_look(self.shifted(d), **look), 0.55, seed=100000 + i)  # it carries its own grain already
        pic = self.picture()
        h, w = pic.shape[:2]
        rate = self.ov.get("push", PUSH)
        z = (1.0 + rate * t) * self.ov.get("zoom", 1.0)
        # pivot on the apex of the arc, and let the override shift the picture (fractions of the frame, + is down/right)
        px, py = 0.5 * w, self.ov.get("pivot_y", self.apex_y) * h
        dx, dy = self.ov.get("dx", 0.0) * w, self.ov.get("dy", 0.0) * h
        M = np.array([[z, 0.0, px * (1 - z) + dx], [0.0, z, py * (1 - z) + dy]], np.float64)
        d = cv2.warpAffine(pic, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
        d = cv2.resize(d, (W, H), interpolation=cv2.INTER_AREA)
        return film_grain(print_look(np.clip(d, 0.0, 1.0), **look), self.ov.get("grain", 1.0) * self.grain / 1.2, seed=100000 + i)


CAPTION_Y = 0.37  # It no longer follows each shot's arc; here it clears every arc at .42 or lower in the frame, and a shot whose arc is higher has the words over its subject


class Titles:
    def __init__(self, en=False):
        self.en = en
        self.cn = {t: text_mask(CAPTIONS_EN[t], LATIN, CAPTION_EN_SIZE) if en else text_mask(t, SONG, 74) for t in CAPTIONS}
        self.name = text_mask("Claude Opus 5.5", LATIN, 72)
        self.names = {}

    def apply(self, img, i, sh):
        nm = sh.ov.get("name")
        if nm:
            m = self.names.setdefault(nm, text_mask(NAMES_EN[nm], LATIN, NAME_SIZE, bloom=0.35) if self.en else text_mask(nm, SONG, NAME_SIZE, bloom=0.35))
            h, w = m.shape
            cx, cy = (NAME_X + (w - 80) / 2.0) / W, (NAME_Y + (h - 80) / 2.0) / H
            if not hasattr(sh, "name_ink"):  # one ink for the whole shot, chosen on what lies behind the glyphs: a light picture gets black
                x0, y0 = NAME_X, NAME_Y
                sh.name_ink = (0.02, 0.02, 0.02) if float(img[y0 : y0 + h - 80, x0 : x0 + w - 80].mean()) > 0.62 else (0.98, 0.97, 0.95)
            img = put_text(img, m, cx, cy, NAME_OPACITY, ink=sh.name_ink)
        t = sh.ov.get("caption")
        if t:
            ink = sh.ov.get("caption_ink")  # a dark ink for a picture whose sky is bright
            img = put_text(img, self.cn[t], 0.5, CAPTION_Y, ink=tuple(ink)) if ink else put_text(img, self.cn[t], 0.5, CAPTION_Y)
        if sh.ov.get("end"):
            k = (i - sh.a) / sh.slow + sh.ov.get("first", 0)
            # what it is for, on the ink of the land, riding up with the horizon under the sun, to the last frame.
            # It starts at rendered frame 84, not at the 92 it had at full length: this shot now runs fast (for people to watch to the end), and the name must still stay long enough to read
            o = float(np.clip((k - 84) / 12.0, 0, 1))
            if o > 0:
                if not sh.src:
                    raise SystemExit(f"{sh.ov['src']}: no frames yet, so no end title. Render it first: python3 v2/render_film.py --list")
                apex = json.load(open(os.path.join(os.path.dirname(sh.src[1][0]), "apex.json")))  # written by the shot; no file, no title
                img = put_text(img, self.name, 0.5, float(np.interp(k, np.arange(len(apex)), apex)) + 0.19, o, ink=(0.98, 0.97, 0.95))
        return img


def to8(img):
    return (np.clip(img, 0.0, 1.0) * 255.0 + 0.5).astype(np.uint8)


def sheet(shots, titles, tag=""):
    tiles = []
    for sh in shots:
        i = sh.b - 6 if sh.ov.get("end") else (sh.a + sh.b) // 2
        im = titles.apply(sh.frame(i), i, sh)
        th = to8(cv2.resize(im, (480, 270), interpolation=cv2.INTER_AREA))[..., ::-1].copy()
        q = "—" if sh.src is None else sh.src[0] if sh.src[0] == "move" else sh.src[-1] if sh.src[0] == "still" else sh.src[2]
        cv2.putText(th, f"{sh.n} {sh.ov['src']} {sh.ov['len']}f {q if sh.src else 'none'}", (8, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
        tiles.append(th)
        sh.still = sh.tw = None  # sheet touches every still once; do not keep them all in 16 GB
    cols = 6
    rows = [np.hstack(tiles[r : r + cols] + [np.zeros((270, 480, 3), np.uint8)] * (cols - len(tiles[r : r + cols]))) for r in range(0, len(tiles), cols)]
    p = os.path.join(OUT, "film", f"sheet{tag}.jpg")
    cv2.imwrite(p, np.vstack(rows), [cv2.IMWRITE_JPEG_QUALITY, 90])
    print(p, flush=True)


def main():
    args = sys.argv[1:]
    only = next((a.split("=")[1] for a in args if a.startswith("--only=")), None)
    os.makedirs(os.path.join(OUT, "film"), exist_ok=True)
    shots, a = [], 0
    for n, ov in enumerate(cut(), 1):
        shots.append(Shot(n, a, ov))
        a = shots[-1].b
    print(f"{len(shots)} shots, {a} frames, {a / FPS:.1f} s", flush=True)
    tag = "_en" if "--en" in args else ""
    titles = Titles(bool(tag))
    print("missing shots:", [sh.ov["src"] for sh in shots if sh.src is None], flush=True)
    print("not final:", [sh.ov["src"] for sh in shots if sh.src and sh.src[-1] != "final"], flush=True)
    sheet(shots, titles, tag)
    if "--sheet" in args:
        return
    use = shots
    name = f"film{tag}.mp4"
    if only:
        lo, hi = (only.split("-") + [only])[:2]
        use = [sh for sh in shots if int(lo) <= sh.n <= int(hi)]
        name = f"part{tag}.mp4"
    out = os.path.join(OUT, "film", name)
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-"]
    if "--master" in args:
        out = os.path.join(OUT, "film", f"film_master{tag}.mkv")
        cmd += ["-c:v", "libx264rgb", "-qp", "0", "-preset", "medium", "-color_primaries", "bt709", "-color_trc", "bt709", out]
    else:
        cmd += ["-vf", "scale=out_color_matrix=bt709:out_range=tv,format=yuv420p", "-c:v", "libx264", "-crf", "13", "-preset", "slow", "-tune", "grain"]
        cmd += ["-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-movflags", "+faststart", out]
    ff = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for sh in use:
        for i in range(sh.a, sh.b):
            ff.stdin.write(to8(titles.apply(sh.frame(i), i, sh)).tobytes())
        sh.still = sh.tw = None
        print(f"shot {sh.n} done", flush=True)
    ff.stdin.close()
    if ff.wait() != 0:
        raise SystemExit("ffmpeg failed")
    print(out)


if __name__ == "__main__":
    main()
