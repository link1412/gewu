"""The Inaba tenmoku's form: a lathe profile and the camera of the 1937 side view, solved together from the photo's
edges (measure.py), with the museum's mouth diameter as the scale.

    python3 -I objects/yohen_inaba/form.py fit     -> form.json, out/yohen/form/{fit.json, fit.png}
    python3 -I objects/yohen_inaba/form.py show

Recorded [M]: height 7.2 cm, mouth 12.2 cm, foot 3.8 cm, 276 g (NPM 2018 p.23, table 1; ref/yohen/report.md). The
mouth sets the scale; height and foot are fitted and checked against the record.

Object frame: mm, z up along the axis, z = 0 on the foot ring's bottom; right-handed. The profile (r, z) is the
outer surface (glaze over the wall, bare body on the foot), run from the foot's inner edge:
  foot bottom -> bead (rounded) -> foot outer face -> crease -> underside (the bare band between the foot and the
  glaze's lower edge, nearly flat) -> roll (rounded: the glaze's thick lower edge) -> wall (a cubic spline r(z)
  through knots at fixed heights: it carries the groove below the lip, the "suppon-guchi") -> lip (a half round).
What the side view shows fixes the outer side; the inner surface and the foot's inside are not seen there (see
ASSUMED, and the top view for the well).

Camera: tools/lathe.py's pinhole (from objects/ru_washer/form.py): focal length, distance, elevation, yaw, pitch,
roll fitted; principal point at the centre of the upper plate as cropped here [A: the printed plate is itself
cropped]; square pixels; no distortion [A].
"""
import argparse
import json
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy.interpolate import CubicSpline
from scipy.optimize import least_squares

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import lathe  # noqa: E402

EDGES = os.path.join(ROOT, "out/yohen/form/edges.json")
FORM = os.path.join(HERE, "form.json")
OUT = os.path.join(ROOT, "out/yohen/form")

MOUTH_MM = 122.0          # [M] NPM 2018 p.23: mouth diameter 12.2 cm (taken as the lip's outer diameter)
HEIGHT_MM_RECORD = 72.0   # [M] height 7.2 cm: fitted, then compared
FOOT_MM_RECORD = 38.0     # [M] foot diameter 3.8 cm: fitted, then compared
MASS_G_RECORD = 276.0     # [M]
FIT_SETS = ("outline_top", "outline_side", "outline_bottom", "lip_front")
KNOTS_U = (0.0, 0.14, 0.28, 0.42, 0.55, 0.67, 0.78, 0.87, 0.94, 1.0)   # wall knots: fractions of its height

ASSUMED = {
    "lip_mm": {"value": 3.0, "why": "the lip's thickness (a half round): not resolved in the side view's outline"},
    "bead_mm": {"value": 1.0, "why": "the foot ring's rounded bottom edge"},
    "crease_mm": {"value": 1.0, "why": "the corner between the foot's outer face and the underside"},
    "roll_mm": {"value": 2.5, "why": "the glaze's thick lower edge, rounding the corner between underside and wall"},
    "groove_fillet_mm": {"value": 1.5, "why": "the groove under the lip band, rounded (its sharpness is not resolved)"},
    "foot_width_mm": {"value": 5.0, "why": "the foot ring's width at its bottom (its inner face is hidden)"},
    # the inside: not in the side view. The wall's thickness is set by the recorded mass (MASS_G_RECORD) with these
    "density_g_cm3": {"value": 2.3, "why": "bulk density of the fired body with its glaze (iron-rich stoneware, a "
                                          "few % porosity: 2.2-2.4; the glaze ~2.5 is a thin share)"},
    "recess_frac": {"value": 0.5, "why": "the base's underside inside the foot ring, recessed above the foot's bottom "
                                        "by this fraction of the foot's height"},
    "floor_fillet_mm": {"value": 10.0, "why": "the inner wall turns into the floor in a broad curve (the well)"},
    "thickness_shape": {"value": "linear", "why": "the wall thickens linearly from the lip's thickness at the groove "
                                                 "to w_low at the wall's foot; the base under the floor is w_low thick"},
}

FIT_PARAMS = [
    # name, start, lower, upper, x_scale
    ("f_px", 9600.0, 2000.0, 80000.0, 100.0),
    ("dist_mm", 600.0, 150.0, 6000.0, 5.0),
    ("elev_deg", 11.0, 0.0, 40.0, 0.05),
    ("dyaw_deg", 0.0, -10.0, 10.0, 0.01),
    ("dpitch_deg", 0.0, -10.0, 10.0, 0.01),
    ("roll_deg", 0.0, -5.0, 5.0, 0.05),
    ("r_foot_bottom", 18.0, 10.0, 30.0, 0.2),
    ("r_foot_top", 18.0, 10.0, 30.0, 0.2),
    ("h_foot", 5.0, 1.0, 15.0, 0.2),
    ("r_w0", 21.0, 12.0, 40.0, 0.2),       # the wall's lowest point (the corner the roll rounds)
    ("dz_under", 1.0, 0.0, 15.0, 0.2),     # ... its height above the foot's top (the underside's rise)
    ("height_mm", 72.0, 55.0, 90.0, 0.2),
    ("h_lip", 6.0, 2.0, 15.0, 0.2),        # the lip band: from the groove up to the top
    ("r_groove", 58.5, 45.0, 61.0, 0.2),   # the groove's radius (the wall's top)
] + [(f"r_k{i}", None, 15.0, 70.0, 0.3) for i in range(1, len(KNOTS_U) - 1)]
NAMES = [q[0] for q in FIT_PARAMS]
CAM = NAMES[:6]


def start_knots(p):
    # a cone from r_w0 to near the mouth, then the groove and the flare (by eye on the plate)
    R = MOUTH_MM / 2
    shape = {0.14: 0.27, 0.28: 0.48, 0.42: 0.64, 0.55: 0.76, 0.67: 0.85, 0.78: 0.92, 0.87: 0.96, 0.94: 0.985}
    return {f"r_k{i}": p["r_w0"] + (p["r_groove"] - p["r_w0"]) * shape[u] for i, u in enumerate(KNOTS_U[1:-1], start=1)}


def params(x, names, meta):
    p = dict(zip(names, map(float, x)))
    p.update(meta)
    p["z_w0"] = p["h_foot"] + p["dz_under"]
    return p


def line(P, Q, n):
    w = np.linspace(0, 1, n)[:, None]
    return (1 - w) * np.asarray(P, float) + w * np.asarray(Q, float)


def round_corner(A, B, Cc, rho, n=60):
    """The corner B of the path A -> B -> C replaced by an arc of radius rho tangent to both legs (a fixed count
    of points, so the profile moves smoothly with the parameters). Returns the points from the first leg's
    tangent point to the second's."""
    u = (A - B) / np.linalg.norm(A - B)
    v = (Cc - B) / np.linalg.norm(Cc - B)
    th = math.acos(float(np.clip(u @ v, -1, 1)))
    if th > math.pi - 1e-4:
        return B[None]
    L = min(rho / math.tan(th / 2), 0.45 * np.linalg.norm(A - B), 0.45 * np.linalg.norm(Cc - B))
    rho = L * math.tan(th / 2)
    P0, P1 = B + L * u, B + L * v
    bis = (u + v) / np.linalg.norm(u + v)
    ctr = B + bis * (rho / math.sin(th / 2))
    a0 = math.atan2(*(P0 - ctr)[::-1])
    a1 = math.atan2(*(P1 - ctr)[::-1])
    da = (a1 - a0 + math.pi) % (2 * math.pi) - math.pi
    w = np.linspace(0, 1, n)
    return ctr + rho * np.c_[np.cos(a0 + da * w), np.sin(a0 + da * w)]


def wall_spline(p):
    """The wall from its foot (r_w0, z_w0) up to the groove (r_groove, H - h_lip)."""
    z0, z1 = p["z_w0"], p["height_mm"] - p["h_lip"]
    zk = z0 + (z1 - z0) * np.asarray(KNOTS_U)
    rk = np.r_[p["r_w0"], [p[f"r_k{i}"] for i in range(1, len(KNOTS_U) - 1)], p["r_groove"]]
    return CubicSpline(zk, rk, bc_type="natural"), zk, rk


def outer_profile(p, n_wall=900):
    """The outer profile as labelled pieces (dense polylines (r, z))."""
    A = {k: v["value"] for k, v in ASSUMED.items()}
    rb, rt, hf = p["r_foot_bottom"], p["r_foot_top"], p["h_foot"]
    rw, zw, H = p["r_w0"], p["z_w0"], p["height_mm"]
    t, R = A["lip_mm"], MOUTH_MM / 2
    zg = H - p["h_lip"]
    if not (rw > rt + 0.5 and zg > zw + 5 and p["h_lip"] > t):
        raise ValueError("foot, underside, wall and lip do not fit together")
    sp, _, _ = wall_spline(p)
    fi = np.array([rb - A["foot_width_mm"], 0.0])
    Pb, Pt, Pw = np.array([rb, 0.0]), np.array([rt, hf]), np.array([rw, zw])
    Pg, Pl = np.array([p["r_groove"], zg]), np.array([R, H - t / 2])
    bead = round_corner(fi, Pb, Pt, A["bead_mm"])
    crease = round_corner(Pb, Pt, Pw, A["crease_mm"])
    # the roll and the groove: tangent to the wall's tangent line at its end and to the next straight leg; the wall
    # is sampled between them with a fixed count, so that the profile moves smoothly with the parameters
    unit = lambda v: v / np.linalg.norm(v)
    t0, t1 = unit(np.array([float(sp(zw, 1)), 1.0])), unit(np.array([float(sp(zg, 1)), 1.0]))
    roll = round_corner(Pt, Pw, Pw + 10 * t0, A["roll_mm"])
    # the band's top Pl: placed so that the lip's half round (below) reaches out to the mouth's radius R exactly
    for _ in range(3):
        u = unit(Pl - Pg)
        Pl = np.array([R + t / 2 * (u[1] - 1), H - t / 2])
    groove = round_corner(Pg - 10 * t1, Pg, Pl, A["groove_fillet_mm"])
    zz = np.linspace(roll[-1, 1], groove[0, 1], n_wall)
    wall = np.c_[sp(zz), zz]
    # the lip: a half round on the lip band's top, across its thickness (the band's outward normal n), so that the
    # inner side, the band moved in by t, starts at its other end
    u = unit(Pl - groove[-1])
    n = np.array([u[1], -u[0]])
    ang = np.linspace(0, math.pi, 200)[:, None]
    lip = Pl - t / 2 * n + t / 2 * (np.cos(ang) * n + np.sin(ang) * u)
    pieces = [("foot_bottom", line(fi, bead[0], 40)), ("bead", bead), ("face", line(bead[-1], crease[0], 60)),
              ("crease", crease), ("underside", line(crease[-1], roll[0], 60)), ("roll", roll),
              ("wall", wall[1:-1]), ("groove", groove), ("lip_face", line(groove[-1], Pl, 80)[1:]), ("lip", lip[1:])]
    return pieces


def closed_profile(p, w_low):
    """The whole section (r, z) as one closed polygon run outer side first: axis under the base -> base underside ->
    foot ring -> ... -> lip -> inner wall -> floor -> axis; labelled. The inner wall is the outer wall moved inwards
    along its normal by w(z): the lip's thickness at the groove and up the lip band, growing linearly to w_low at
    the wall's foot [A]; cut at the floor (w_low above the foot's top [A]) and rounded into it."""
    A = {k: v["value"] for k, v in ASSUMED.items()}
    pcs = dict(outer_profile(p))
    t = A["lip_mm"]
    zg, zw, hf = p["height_mm"] - p["h_lip"], p["z_w0"], p["h_foot"]
    rfi = pcs["foot_bottom"][0, 0]
    zr = A["recess_frac"] * hf
    under = [("base", line((0.0, zr), (rfi, zr), 200)), ("foot_inner", line((rfi, zr), (rfi, 0.0), 40)[1:-1])]
    outer = [k for k in ("foot_bottom", "bead", "face", "crease", "underside", "roll", "wall", "groove", "lip_face", "lip")]
    up = np.vstack([pcs[k] for k in ("wall", "groove", "lip_face")])
    N = lathe.normals(np.vstack([pcs["roll"][-2:], up, pcs["lip"][1:3]]))[2:-2]
    w = np.where(up[:, 1] >= zg, t, t + (w_low - t) * np.clip((zg - up[:, 1]) / (zg - zw), 0, 1))
    inn = (up - w[:, None] * N)[::-1]
    inn[0] = pcs["lip"][-1]          # the same point up to rounding
    zf = hf + w_low
    below = np.nonzero(inn[:, 1] <= zf)[0]
    if len(below) == 0:
        raise ValueError("the inner wall ends above the floor")
    j = below[0]
    if j == 0:
        raise ValueError("the inner wall starts below the floor")
    w0 = (inn[j - 1, 1] - zf) / (inn[j - 1, 1] - inn[j, 1])
    end = inn[j - 1] + w0 * (inn[j] - inn[j - 1])
    inn = np.vstack([inn[:j], end])
    # monotone in r going down (an offset of a curve tighter than w would fold): keep the running minimum
    inn[:, 0] = np.minimum.accumulate(inn[:, 0])
    floor = line(end, (0.0, zf), 300)
    far = inn[np.nonzero(np.hypot(*(inn - end).T) > 3 * A["floor_fillet_mm"])[0][-1]]
    fil = round_corner(far, end, np.array([0.0, zf]), A["floor_fillet_mm"], n=120)
    k0 = int(np.argmin(np.hypot(*(inn - fil[0]).T)))
    k1 = int(np.argmin(np.hypot(*(floor - fil[-1]).T)))
    inner = [("inner", inn[:k0]), ("well", fil), ("floor", floor[k1 + 1:])]
    seq = under + [(k, pcs[k]) for k in outer] + inner
    C = np.vstack([c for _, c in seq])
    lab = np.concatenate([[k] * len(c) for k, c in seq])
    keep = np.r_[True, np.hypot(*np.diff(C, axis=0).T) > 1e-6]
    return C[keep], lab[keep]


def volume_mm3(C):
    """Volume of the solid of revolution of the closed section C (r >= 0), by Pappus: 2 pi * area * centroid r."""
    r, z = C[:, 0], C[:, 1]
    r2, z2 = np.roll(r, -1), np.roll(z, -1)
    cr = r * z2 - r2 * z
    area = 0.5 * cr.sum()
    rc = (cr * (r + r2)).sum() / (6 * area)
    return abs(2 * math.pi * area * rc)


def thickness_from_mass(p, density=None):
    """w_low such that the volume times the assumed density (g/cm^3) is the recorded mass (bisection)."""
    rho = (density or ASSUMED["density_g_cm3"]["value"]) / 1000.0           # g / mm^3
    lo, hi = ASSUMED["lip_mm"]["value"], 15.0
    m = lambda w: volume_mm3(closed_profile(p, w)[0]) * rho
    if not (m(lo) < MASS_G_RECORD < m(hi)):
        raise ValueError(f"the recorded mass is outside {m(lo):.0f}-{m(hi):.0f} g")
    for _ in range(50):
        mid = 0.5 * (lo + hi)
        lo, hi = (mid, hi) if m(mid) < MASS_G_RECORD else (lo, mid)
    return 0.5 * (lo + hi)


def visible(p):
    pcs = outer_profile(p)
    C = np.vstack([c for _, c in pcs])
    lab = np.concatenate([[k] * len(c) for k, c in pcs])
    keep = np.r_[True, np.hypot(*np.diff(C, axis=0).T) > 1e-6]
    C, lab = C[keep], lab[keep]
    N = lathe.normals(C)
    sel = lambda names: (C[np.isin(lab, names)], N[np.isin(lab, names)])
    return {"foot": sel(["foot_bottom", "bead", "face", "crease"]), "under": sel(["underside", "roll"]),
            "wall": sel(["wall", "groove", "lip_face"]), "lip": sel(["lip"]), "C": C, "lab": lab}


def model_curves(p):
    V = visible(p)
    pr = lambda Ls: [lathe.project(L, p) for L in Ls if len(L) > 1]
    lip_all = pr(lathe.contour_points(*V["lip"], p))
    lip_front = pr(lathe.contour_points(*V["lip"], p, front=True))
    wall = pr(lathe.contour_points(*V["wall"], p, vmax=0.6))
    under = pr(lathe.contour_points(*V["under"], p, vmax=0.6))
    foot = pr(lathe.contour_points(*V["foot"], p))
    outline = lathe.Polylines(lip_all + wall + under + foot)
    return {"outline_top": outline, "outline_side": outline, "outline_bottom": outline,
            "lip_front": lathe.Polylines(lip_front)}


def load_edges(path):
    J = json.load(open(path))
    W, Hh = J["photo_size_px"]
    return J, {k: np.asarray(v, float) for k, v in J["sets"].items()}, {"cx": W / 2, "cy": Hh / 2}


def fit(a):
    J, E, pp = load_edges(a.edges)
    meta = dict(pp)
    sets = a.sets.split(",")
    Ef = {k: E[k][::a.stride] for k in sets}
    x0 = {q[0]: q[1] for q in FIT_PARAMS if q[1] is not None}
    x0.update(start_knots(x0))
    if a.start:
        x0.update(json.load(open(a.start))["x"])
    names = NAMES
    lo = np.array([q[2] for q in FIT_PARAMS])
    hi = np.array([q[3] for q in FIT_PARAMS])
    xs = np.array([q[4] for q in FIT_PARAMS])
    x = np.clip(np.array([x0[n] for n in names]), lo + 1e-9, hi - 1e-9)

    def fun(y):
        p = params(y, names, meta)
        p["ref_z"] = p["height_mm"] / 2
        try:
            M = model_curves(p)
        except ValueError:
            return np.full(sum(len(Ef[k]) for k in sets), 1e3)
        return np.concatenate([M[k].distance(Ef[k]) for k in sets])

    cost = np.inf
    for _ in range(a.rounds):
        r = least_squares(fun, x, bounds=(lo, hi), loss="soft_l1", f_scale=2.0, x_scale=xs, max_nfev=a.max_nfev,
                          diff_step=2e-4, xtol=1e-10, ftol=1e-10, gtol=1e-10, verbose=1)
        done = r.cost > cost * 0.998
        x, cost = r.x, r.cost
        if done:
            break
    p = params(x, names, meta)
    p["ref_z"] = p["height_mm"] / 2
    dof = max(1, len(r.fun) - len(r.x))
    s2 = float(np.sum(r.fun ** 2) / dof)
    try:
        sd = np.sqrt(np.diag(np.linalg.inv(r.jac.T @ r.jac) * s2 * a.stride))
    except np.linalg.LinAlgError:
        sd = np.full(len(x), np.nan)
    M = model_curves(p)
    stats = {}
    for k in FIT_SETS:
        d = M[k].distance(E[k])
        stats[k] = {"n": int(len(d)), "median_px": round(float(np.median(d)), 3),
                    "p90_px": round(float(np.percentile(d, 90)), 3), "max_px": round(float(d.max()), 2)}
    return p, dict(zip(names, sd.tolist())), stats, r, J, E


def derived(p):
    V = visible(p)
    C = V["C"]
    sp, _, _ = wall_spline(p)
    zz = np.linspace(p["z_w0"], p["height_mm"] - p["h_lip"], 2000)
    return {
        "height_mm": round(p["height_mm"], 3), "height_record_mm": HEIGHT_MM_RECORD,
        "foot_diameter_bottom_mm": round(2 * p["r_foot_bottom"], 3),
        "foot_diameter_max_mm": round(2 * float(V["foot"][0][:, 0].max()), 3), "foot_record_mm": FOOT_MM_RECORD,
        "foot_height_mm": round(p["h_foot"], 3),
        "wall_bottom_r_z_mm": [round(p["r_w0"], 3), round(p["z_w0"], 3)],
        "groove_r_z_mm": [round(p["r_groove"], 3), round(p["height_mm"] - p["h_lip"], 3)],
        "lip_band_mm": round(p["h_lip"], 3), "lip_flare_mm": round(MOUTH_MM / 2 - p["r_groove"], 3),
        "wall_radius_at_z_mm": {f"{z:g}": round(float(sp(z)), 3) for z in (10, 20, 30, 40, 50, 55, 60, 65, 68)
                                if p["z_w0"] <= z <= zz[-1]},
        "max_outer_radius_mm": round(float(C[:, 0].max()), 3),
        **inner_numbers(p),
    }


def inner_numbers(p):
    w = thickness_from_mass(p)
    C, lab = closed_profile(p, w)
    rho = ASSUMED["density_g_cm3"]["value"]
    inn = C[lab == "inner"]
    return {"w_low_mm_from_mass": round(w, 3), "mass_check_g": round(volume_mm3(C) * rho / 1000, 2),
            "floor_z_mm": round(p["h_foot"] + w, 3), "depth_inside_mm": round(p["height_mm"] - p["h_foot"] - w, 3),
            "floor_flat_radius_mm": round(float(C[lab == "floor"][:, 0].max()), 3),
            "w_low_mm_if_density_2.2_2.4": [round(thickness_from_mass(p, d), 3) for d in (2.2, 2.4)],
            "inner_wall_radius_at_z_mm": {f"{z:g}": round(float(np.interp(z, inn[::-1, 1], inn[::-1, 0])), 3)
                                          for z in (15, 20, 30, 40, 50, 60) if inn[:, 1].min() <= z <= inn[:, 1].max()}}


def draw(p, J, E, path):
    img = Image.open(os.path.join(ROOT, J["photo"])).convert("RGB").crop((0, 0, *J["photo_size_px"]))
    d = ImageDraw.Draw(img)
    V = visible(p)
    pr = lambda Ls: [lathe.project(L, p) for L in Ls if len(L) > 1]
    for k, colr in (("lip", (255, 60, 60)), ("wall", (0, 220, 0)), ("under", (0, 160, 255)), ("foot", (255, 0, 255))):
        for L in pr(lathe.contour_points(*V[k], p, vmax=(0.6 if k in ("wall", "under") else 1.0))):
            d.line([tuple(q) for q in L], fill=colr, width=2)
    for k, P in E.items():
        for x, y in P[::3]:
            d.point((x, y), fill=(255, 255, 0))
    img.save(path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["fit", "show"])
    ap.add_argument("--edges", default=EDGES)
    ap.add_argument("--stride", type=int, default=6)
    ap.add_argument("--max-nfev", type=int, default=300)
    ap.add_argument("--rounds", type=int, default=6)
    ap.add_argument("--start", help="fit.json of an earlier fit to start from")
    ap.add_argument("--sets", default=",".join(FIT_SETS), help="edge sets to fit (a check: leave one out)")
    a = ap.parse_args()
    if a.cmd == "show":
        print(json.dumps(json.load(open(FORM))["derived"], indent=1))
        return
    p, sd, stats, r, J, E = fit(a)
    os.makedirs(OUT, exist_ok=True)
    dv = derived(p)
    json.dump({"x": {k: p[k] for k in NAMES}, "sd": sd, "cost": float(r.cost), "status": int(r.status),
               "stats": stats}, open(os.path.join(OUT, "fit.json"), "w"), indent=1)
    tagged = lambda k: {"value": round(p[k], 4), "sd": round(sd[k], 4), "tag": "M",
                        "how": "fitted to the 1937 side view's edges (form.py fit)"}
    form = {
        "source": "Inaba yohen tenmoku, Seikado Bunko Art Museum; profile from the 1937 plate (Takahashi, Taisho "
                  "meiki kan 6; Commons PD-Japan-oldphoto; ref/yohen/images/inaba_commons_1937.jpg)",
        "frame": "mm; z up along the axis, z = 0 on the foot's bottom; outer profile (r, z)",
        "scale": {"mouth_mm": {"value": MOUTH_MM, "tag": "M", "how": "NPM 2018 p.23 table 1"}},
        "record": {"height_mm": HEIGHT_MM_RECORD, "foot_mm": FOOT_MM_RECORD, "mass_g": MASS_G_RECORD,
                   "tag": "M", "how": "NPM 2018 p.23 table 1"},
        "fitted": {k: tagged(k) for k in NAMES if k not in CAM},
        "knots_u": list(KNOTS_U),
        "assumed": ASSUMED,
        "camera_1937": {"model": "pinhole (tools/lathe.py); principal point at the cropped plate's centre [A]",
                        "principal_px": [p["cx"], p["cy"]], "ref_z_mm": p["ref_z"],
                        **{k: {"value": round(p[k], 5), "sd": round(sd[k], 5)} for k in CAM}},
        "residuals_px": stats,
        "derived": dv,
    }
    json.dump(form, open(FORM, "w"), indent=1, ensure_ascii=False)
    draw(p, J, E, os.path.join(OUT, "fit.png"))
    for k in NAMES:
        print(f"  {k:14s} {p[k]:10.4f} +- {sd[k]:.4f}")
    for k, s in stats.items():
        print(f"  {k:15s} n {s['n']:5d}  median {s['median_px']:.2f}  p90 {s['p90_px']:.2f}  max {s['max_px']:.1f}")
    print(json.dumps(dv))


if __name__ == "__main__":
    main()
