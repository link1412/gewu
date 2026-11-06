"""Patterns for crafts/carving/carve.py: motifs traced off real pieces, and the geometric diaper grounds (锦地).

lotus_dish(R, ...): the Yuan lotus dish of the Cleveland Museum of Art, 1918.933 (carved cinnabar lacquer on wood,
overall 15.9 cm, CC0; ref/carved_lacquer/cma/). Read off the museum's front photograph (1918.933_print.jpg) at
15.19 px/mm (the dish's 2415 px across = 159 mm, the catalogue's 'overall' taken as the diameter) with a 1 mm grid
laid over it (docs/crafts/carving.md, 纹样): positions and radii are [M] (measured by us on the photo), +-0.5 mm; the heights are not visible in a
frontal photo and are our estimate from the shading and the side view (alt2) [A]. The dish's own dish-shaped
curvature is left out: this is a flat test piece cut from the design.

Diaper grounds, cut into the ground (z = ground) as V lines before the motifs are raised over them (DIAPER below,
measured on Met 2020.323.1a-b):
- 'tian' 天锦 (sky): rows of interlocking keys;
- 'di' 地锦 (earth, terrace): a diamond lattice of double lines with a four-petal flower in every diamond;
- 'shui' 水锦 (water): interlocking crests of nested arcs, each row shifted half a crest.
"""
import math

import numpy as np

from carve import sdf_annulus, sdf_circle, sdf_polygon

# --- the Cleveland lotus dish 1918.933 ---------------------------------------------------------------
# world: x right, y up, origin at the dish centre (the photo's y runs down: y_world = -y_photo)
POD = {"centre": (0.5, 0.2), "r": 27.3}                         # flat field, outlined by a groove [M]
BAND = {"r0": 28.3, "r1": 32.3}                                 # the raised ring round the pod [M]
SEEDS = [(0.6, 0.6), (-9.3, 15.6), (8.1, 15.9), (-16.5, -0.3), (17.7, 1.5), (-7.2, -15.6), (10.5, -14.7)]   # [M]
SEED = {"dome_r": 4.4, "channel_r": 5.5, "ring_r": 6.9, "outer_r": 7.2}                                  # [M]
PETALS = {"n": 12, "phase_deg": 90 + 15, "r0": 31.0, "r1": 69.5,
          # half-width (mm) at the fraction t of the petal's length, read off the photo [M]
          "w": [(0.0, 8.2), (0.12, 10.2), (0.3, 12.2), (0.5, 13.5), (0.65, 13.5), (0.78, 11.5), (0.88, 7.5), (0.95, 3.5), (1.0, 0.0)],
          "inner_inset": 2.2, "inner_t": (0.06, 0.78)}
SEPALS = {"n": 12, "phase_deg": 90, "r0": 49.0, "r1": 73.0,
          "w": [(0.0, 0.0), (0.15, 3.0), (0.4, 5.2), (0.7, 3.6), (0.9, 1.4), (1.0, 0.0)]}
RIM = {"r0": 72.5, "r1": 79.5}

# heights (mm above the substrate) [A]: the photo is frontal; these were set from the shading of the domes and petals
H = {"ground": 0.0,
     "pod": dict(base=0.3, edge=1.8, top=2.0, kind="flat", wall_deg=72, shoulder_mm=0.5),
     "band": dict(base=0.3, edge=1.2, top=3.0, kind="pillow", wall_deg=65, shoulder_mm=1.0, smooth_mm=0.5),
     "petal": dict(base=0.3, edge=0.9, top=3.8, kind="pillow", wall_deg=60, shoulder_mm=1.5, smooth_mm=2.5),
     "sepal": dict(base=0.2, edge=0.9, top=2.0, kind="ridge", wall_deg=65, shoulder_mm=0.3),
     "rim": dict(base=0.4, edge=2.0, top=4.0, kind="pillow", wall_deg=70, shoulder_mm=0.6),
     "seed_floor": 0.7,
     "seed_line": dict(depth=0.45, angle_deg=90),          # V lines at the dome's foot and outside the ring
     "dome": dict(edge=0.9, top=3.9, kind="dome", wall_deg=80, shoulder_mm=0.3),
     "ring": dict(edge=1.6, top=2.5, kind="pillow", wall_deg=72, shoulder_mm=0.25),
     "petal_line": dict(depth=0.35, angle_deg=60)}


def _petal_outline(theta, P, n=90):
    """Closed outline (n*2 points) of a petal whose axis points at angle theta (rad) from the centre."""
    t = np.linspace(0, 1, n)
    tw = np.array(P["w"])
    w = np.interp(t, tw[:, 0], tw[:, 1])
    s = P["r0"] + t * (P["r1"] - P["r0"])
    ax, nx = np.array([math.cos(theta), math.sin(theta)]), np.array([-math.sin(theta), math.cos(theta)])
    left = s[:, None] * ax + w[:, None] * nx
    right = s[:, None] * ax - w[:, None] * nx
    return np.r_[left, right[::-1]]


def _inner_lines(theta, P):
    t = np.linspace(*P["inner_t"], 40)
    tw = np.array(P["w"])
    w = np.maximum(np.interp(t, tw[:, 0], tw[:, 1]) - P["inner_inset"], 0.3)
    s = P["r0"] + t * (P["r1"] - P["r0"])
    ax, nx = np.array([math.cos(theta), math.sin(theta)]), np.array([-math.sin(theta), math.cos(theta)])
    return [s[:, None] * ax + w[:, None] * nx, s[:, None] * ax - w[:, None] * nx]


def lotus_dish(rel, keep=lambda bbox: True, rng=None, jitter=None, H=H):
    """Carve the Cleveland lotus dish into Relief rel (back to front). keep(bbox) can skip motifs off the piece;
    jitter(bbox) -> a function added to each motif's distance (knife facets) or None."""
    J = (lambda bb: jitter(bb)) if jitter else (lambda bb: None)

    def add(fn, bb, h, name):
        if keep(bb):
            rel.add(fn, bb, jitter=J(bb), name=name, **h)

    for k in range(SEPALS["n"]):
        th = math.radians(SEPALS["phase_deg"] + 360.0 * k / SEPALS["n"])
        P = _petal_outline(th, SEPALS)
        add(lambda X, Y, P=P: sdf_polygon(P, X, Y), (*P.min(0), *P.max(0)), H["sepal"], f"sepal{k}")
    for k in range(PETALS["n"]):
        th = math.radians(PETALS["phase_deg"] + 360.0 * k / PETALS["n"])
        P = _petal_outline(th, PETALS)
        bb = (*P.min(0), *P.max(0))
        add(lambda X, Y, P=P: sdf_polygon(P, X, Y), bb, H["petal"], f"petal{k}")
        if keep(bb):
            for L in _inner_lines(th, PETALS):
                rel.incise(L, knife="v", name=f"petal{k}_line", **H["petal_line"])
    r = RIM
    add(lambda X, Y: sdf_annulus((0, 0), r["r0"], r["r1"], X, Y), (-r["r1"], -r["r1"], r["r1"], r["r1"]), H["rim"], "rim")
    b = BAND
    add(lambda X, Y: sdf_annulus(POD["centre"], b["r0"], b["r1"], X, Y), (-b["r1"], -b["r1"], b["r1"], b["r1"]), H["band"], "band")
    c, R = POD["centre"], POD["r"]
    add(lambda X, Y: sdf_circle(c, R, X, Y), (c[0] - R, c[1] - R, c[0] + R, c[1] + R), H["pod"], "pod")
    S = SEED
    for k, s in enumerate(SEEDS):
        bb = (s[0] - S["outer_r"], s[1] - S["outer_r"], s[0] + S["outer_r"], s[1] + S["outer_r"])
        if not keep(bb):
            continue
        rel.pocket(lambda X, Y, s=s: sdf_circle(s, S["outer_r"], X, Y), bb, H["seed_floor"], wall_deg=75, name=f"seed{k}_pocket")
        rel.add(lambda X, Y, s=s: sdf_annulus(s, S["channel_r"], S["ring_r"], X, Y), bb, base=H["seed_floor"],
                jitter=J(bb), name=f"seed{k}_ring", **H["ring"])
        rel.add(lambda X, Y, s=s: sdf_circle(s, S["dome_r"], X, Y), bb, base=H["seed_floor"],
                jitter=J(bb), name=f"seed{k}_dome", **H["dome"])
        t = np.linspace(0, 2 * math.pi, 181)
        for r, nm in ((S["dome_r"] + 0.15, "foot"), (0.5 * (S["ring_r"] + S["outer_r"]), "outer")):
            rel.incise(np.c_[s[0] + r * np.cos(t), s[1] + r * np.sin(t)], knife="v", name=f"seed{k}_{nm}", **H["seed_line"])


# --- diaper grounds -----------------------------------------------------------------------------------
# Measured by us on the Met's covered box 2020.323.1a-b (Ming, 15th c., diameter 26.4 cm; ref/carved_lacquer/met_diaper/
# DP-17989-122.jpg, the lid from above at 8.93 px/mm, the lid's 2359 px over 264 mm) [M], about +-15%: the incised lines
# of all three grounds are 0.70-0.85 mm apart (1D autocorrelation, 6.2-7.6 px); the repeats were counted on 1:1 crops.
DIAPER = {
    "tian": {"line_mm": 0.70, "row_mm": 2.7, "unit_mm": 6.7},          # sky: rows of interlocking keys (工 bricks)
    "di": {"line_mm": 0.75, "diamond_mm": 4.6},                         # earth/terrace: a diamond lattice, a flower in each
    "shui": {"line_mm": 0.85, "crest_mm": 7.0, "row_mm": 3.5, "lines": 4},   # water: interlocking crests of nested arcs
}


def diaper_lines(kind, bbox, scale=1.0, angle_deg=0.0, P=None):
    """Polylines (mm) of a diaper ground over bbox (x0, y0, x1, y1), to be incised; scale multiplies every length."""
    P = {k: (v * scale if k != "lines" else v) for k, v in (P or DIAPER[kind]).items()}
    x0, y0, x1, y1 = bbox
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    R = math.hypot(x1 - x0, y1 - y0) / 2 + 2
    a = math.radians(angle_deg)
    out = []
    if kind == "tian":
        # each row: a long line at its top and bottom; between them keys: short verticals alternating up and down,
        # staggered by half a unit from row to row, and a middle line broken at the keys
        L, rh, u = P["line_mm"], P["row_mm"], P["unit_mm"]
        nr = int(2 * R / rh) + 2
        for j in range(-nr // 2, nr // 2 + 1):
            yb = j * rh
            out.append(np.array([[-R, yb], [R, yb]]))
            sh = 0.5 * u * (j % 2)
            for i in range(-int(R / u) - 2, int(R / u) + 2):
                xa = i * u + sh
                out.append(np.array([[xa, yb], [xa, yb + rh - L]]))
                out.append(np.array([[xa + L, yb + L], [xa + u / 2, yb + L]]))
                out.append(np.array([[xa + u / 2, yb + L], [xa + u / 2, yb + rh]]))
                out.append(np.array([[xa + u / 2 + L, yb + rh - L], [xa + u, yb + rh - L]]))
    elif kind == "di":
        d, L = P["diamond_mm"], P["line_mm"]
        s = d / math.sqrt(2)                                  # the square's side, set on the diagonal
        a = a + math.pi / 4
        n = int(R / s) + 2
        for k in range(-n, n + 1):
            for off in (-L / 2, L / 2):                       # double lines
                out.append(np.array([[-R, k * s + off], [R, k * s + off]]))
                out.append(np.array([[k * s + off, -R], [k * s + off, R]]))
        for i in range(-n, n + 1):                            # a four-petal flower in every cell: four short cuts
            for j in range(-n, n + 1):
                c = np.array([(i + 0.5) * s, (j + 0.5) * s])
                for u in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
                    u = np.array(u, float) / math.sqrt(2)
                    out.append(np.array([c + 0.12 * s * u, c + 0.38 * s * u]))
    elif kind == "shui":
        W, rh, L, nl = P["crest_mm"], P["row_mm"], P["line_mm"], int(P["lines"])
        t = np.linspace(0, math.pi, 40)
        nr = int(2 * R / rh) + 3
        for j in range(-nr // 2, nr // 2 + 1):
            yb = j * rh
            sh = 0.5 * W * (j % 2)
            for i in range(-int(R / W) - 2, int(R / W) + 2):
                xc = i * W + sh
                for k in range(nl):
                    r = W / 2 - k * L
                    if r <= 0.2:
                        break
                    out.append(np.c_[xc + r * np.cos(t), yb + r * np.sin(t) * (2 * rh / W)])
    else:
        raise ValueError(f"diaper {kind}: tian, di or shui")
    rot = np.array([[math.cos(a), -math.sin(a)], [math.sin(a), math.cos(a)]])
    return [L_ @ rot.T + np.array([cx, cy]) for L_ in out]


def clip_polyline(L, box, step=0.1):
    """The parts of polyline L inside box (x0, y0, x1, y1), resampled every `step` mm."""
    L = np.asarray(L, float)
    seg = np.linalg.norm(np.diff(L, axis=0), axis=1)
    s = np.r_[0, np.cumsum(seg)]
    t = np.arange(0, s[-1] + 1e-9, step)
    P = np.c_[np.interp(t, s, L[:, 0]), np.interp(t, s, L[:, 1])]
    ins = (P[:, 0] >= box[0]) & (P[:, 0] <= box[2]) & (P[:, 1] >= box[1]) & (P[:, 1] <= box[3])
    out, cur = [], []
    for p, k in zip(P, ins):
        if k:
            cur.append(p)
        elif cur:
            out.append(np.array(cur)) if len(cur) > 1 else None
            cur = []
    if len(cur) > 1:
        out.append(np.array(cur))
    return out


# --- a sampler tile (our design, not a traced piece) ---------------------------------------------------
def scroll_pair(c, size):
    """A ruyi / pommel scroll (如意云纹, the usual 剔犀 motif) as two open polylines (mm): from a point below, each side
    rises round the outside of its lobe, over the top towards the axis and curls inward; the two sides mirror each
    other about the vertical through c. Our drawing [A]."""
    R = 0.32 * size
    t0, span = -math.pi / 4, 1.8 * math.pi
    t = np.linspace(t0, t0 + span, 140)
    r = R * (1 - 0.72 * (t - t0) / span)
    cr = np.array([c[0] + 0.30 * size, c[1] + 0.12 * size])
    right = np.c_[cr[0] + r * np.cos(t), cr[1] + r * np.sin(t)]
    tip = np.array([c[0], c[1] - 0.55 * size])
    right = np.r_[[tip], right]
    left = right.copy()
    left[:, 0] = 2 * c[0] - left[:, 0]
    return [right, left]


def sampler(rel, stack_kind, rng=None):
    """A carving sampler on a tile about 60 x 34 mm (the detail frame): for 'tihong', the three diaper grounds side by
    side (tian | shui | di) under raised motifs (a five-petal flower, overlapping leaves, a pine-needle disc); for
    'tixi', rows of pommel scrolls cut deep with a round gouge through the banded stack. The ground is at rel.ground."""
    g = rel.ground
    if stack_kind == "tihong":
        cols = (("tian", -30, -10), ("shui", -10, 10), ("di", 10, 30))
        for kind, xa, xb in cols:
            for L0 in diaper_lines(kind, (xa, -17, xb, 17)):
                for L in clip_polyline(L0, (xa + 0.5, -17.5, xb - 0.5, 17.5)):
                    rel.incise(L, depth=0.18, knife="v", angle_deg=70, name=f"diaper_{kind}")
        # the walls between the grounds: shallow ridges
        for xs in (-10, 10):
            rel.add(lambda X, Y, xs=xs: 0.4 - np.abs(X - xs), (xs - 0.4, -17, xs + 0.4, 17), base=g, edge=g + 0.4,
                    top=g + 0.4, kind="flat", wall_deg=45, shoulder_mm=0.2, name="divider")
        # raised motifs over the grounds, back to front
        for k, (x, y, ang) in enumerate(((-24, 8, 20), (-16, -6, -35), (-5, 9, 70))):     # overlapping leaves
            th = math.radians(ang)
            t = np.linspace(0, 1, 60)
            w = 2.6 * np.sin(math.pi * t) ** 0.8
            ax, nx = np.array([math.cos(th), math.sin(th)]), np.array([-math.sin(th), math.cos(th)])
            s = (t - 0.5) * 14
            P = np.r_[s[:, None] * ax + w[:, None] * nx, (s[:, None] * ax - w[:, None] * nx)[::-1]] + np.array([x, y])
            rel.add(lambda X, Y, P=P: sdf_polygon(P, X, Y), (*P.min(0), *P.max(0)), base=g, edge=g + 0.8 + 0.4 * k,
                    top=g + 1.6 + 0.4 * k, kind="ridge", wall_deg=60, shoulder_mm=0.3, name=f"leaf{k}")
            rel.incise(np.r_[[P[0]], [P[59]]] if False else np.c_[s * ax[0] + x, s * ax[1] + y][5:-5], depth=0.15,
                       knife="v", angle_deg=70, name=f"leaf{k}_vein")
        cx, cy = 4.0, -6.0                                        # a five-petal flower
        for k in range(5):
            th = math.radians(90 + 72 * k)
            c = (cx + 3.4 * math.cos(th), cy + 3.4 * math.sin(th))
            rel.add(lambda X, Y, c=c: sdf_circle(c, 3.0, X, Y), (c[0] - 3, c[1] - 3, c[0] + 3, c[1] + 3), base=g,
                    edge=g + 1.0, top=g + 2.4, kind="pillow", wall_deg=65, shoulder_mm=0.5, smooth_mm=0.5, name=f"petal{k}")
        rel.add(lambda X, Y: sdf_circle((cx, cy), 1.6, X, Y), (cx - 2, cy - 2, cx + 2, cy + 2), base=g + 1.5, edge=g + 2.4,
                top=g + 3.0, kind="dome", wall_deg=75, shoulder_mm=0.2, name="flower_heart")
        cx, cy = 21.0, 5.0                                        # a pine-needle disc (松针): a dome with radial cuts
        rel.add(lambda X, Y: sdf_circle((cx, cy), 5.0, X, Y), (cx - 5, cy - 5, cx + 5, cy + 5), base=g, edge=g + 0.8,
                top=g + 2.2, kind="dome", wall_deg=70, shoulder_mm=0.4, name="pine_disc")
        for k in range(36):
            th = 2 * math.pi * k / 36
            rel.incise(np.array([[cx + 0.6 * math.cos(th), cy + 0.6 * math.sin(th)],
                                 [cx + 4.6 * math.cos(th), cy + 4.6 * math.sin(th)]]), depth=0.25, knife="v",
                       angle_deg=60, name="pine_needle")
    elif stack_kind == "tixi":
        for j, y in enumerate((-8.0, 9.0)):
            for i in range(-2, 3):
                x = i * 16.0 + 8.0 * (j % 2)
                for L in scroll_pair((x, y), 14.0):
                    rel.incise(L, depth=2.4, knife="v", angle_deg=50, name="scroll")
    else:
        raise ValueError(stack_kind)
