"""Shot 19 round 1 (螺钿): a black-lacquer dish inlaid with thin coloured mother-of-pearl, a silver-bound rim; the far
rim is the original's arc; the dish and the camera stay still and the light moves (docs/shots/19-luodian.md).

    python3 -I shots/19-luodian/scene.py --lut out/shots/19-luodian/nacre_lut.npz --out DIR --frame k [--spp N] [--res WxH]

Writes DIR/scene.pbrt, dish.ply, silver.ply, inlay.npz, optics.json, framing.json. World: mm, Z up, the dish stands on
the table z = 0 with its axis on Z; the camera is on -Y looking at the far rim (+Y). Object x = -design x (pattern.py).

Every light is in a light group (tools/cycles_scene.py renders each group's pass in the same render), so the studio's
levels are fitted afterwards as a linear mix (fit.py) without re-rendering:
- p00..pNN: a gradient panel behind, above and over the dish to behind the camera, strips on a cylinder of radius
  PANEL_DIST about the far rim's apex (axis X), facing it, in elevation bands BANDS (from behind the dish, 0, over the
  zenith, 90, to over the camera, 140; each band one group, every strip 5500 K, scale 1). The floor mirrors ~24-40
  deg (the body's sheen; the shell pieces, whose layers are tilted, see ~0-60 deg); the cavetto just inside the rim
  turns towards the lens and mirrors from ~24 deg at its foot to ~130 deg at the lip: the light band along the arc;
- key: the moving soft source, a long horizontal strip (a stack of strips, narrower in front: a soft edge) on the
  panel's cylinder, rising from KEY_ELEV[0] to KEY_ELEV[1] over the shot, above the floor's mirror: it lights the
  shell pieces whose tilted layers face it, and draws a moving highlight in the cavetto and on the silver lip.
The table (a dark cloth, diffuse) is lit by all of them; the lens sees it over the rim (the original's dark sky).
"""

import argparse
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "optics"))
import framing  # noqa: E402
import pattern  # noqa: E402

SPEC = json.load(open(os.path.join(ROOT, "spec", "shots.json")))
SHOT = next(s for s in SPEC["shots"] if s["shot"] == 19)

# --- the dish (mm). Diameter 126 and height 12: the Shanghai Museum's 漆螺钿山水人物图圆盘 [查到, luodian.md 1].
# The rest of the profile is ours [A]: floor at FLOOR_Z out to pattern.FLOOR_R, a cavetto rising as a parabola to the
# lip, a rounded lip of radius LIP_R bound in silver (银扣), the outer wall down to a foot.
R_OUT = 63.0
H_TOP = 12.0
LIP_R = 1.5
LIP_C = (R_OUT - LIP_R, H_TOP - LIP_R)          # the lip's centre (r, z)
FLOOR_Z = 8.6
SILVER_DOWN = 1.2                                # the binding reaches this far below the lip's centre, both sides [A]

# --- camera: Canon EF 100 mm f/2.8L Macro on the 5D Mark IV, cropped to 16:9 (thin lens) [A, a choice]
FOCAL_MM = 100.0
SENSOR_W_MM = 36.0
ELEV_DEG = 24.0          # elevation of the line from the lens to the far rim's apex [A]
FNUMBER = 16.0            # [A]
FOCUS_ROW = 0.80         # the focus is on the floor under this row of the frame's centre column (the bridge) [A]

# --- materials
LACQUER = {"diffuse": 0.0028, "alpha": 0.002}    # as S2 (docs/shots/19-dianluo.md; Lee 2023, Aoki 2019)
SHELL = {"alpha_top": 0.002, "alpha_layers": 0.02}   # as S2; the layers' 0.02 is a PLACEHOLDER
SILVER_ALPHA = 0.01      # polished silver, worn [A]
TABLE_RGB = (0.00416, 0.00323, 0.00152)            # black velvet [F: `fit.py table` (r1 fix), the sky over the rim; velvet is ~1 %]

# --- lights
PANEL_DIST = 400.0
PANEL_HALF_W = 500.0
STRIP_DEG = 1.0
BANDS = [0, 4, 8, 12, 16, 20, 24, 28, 32, 36, 40, 45, 50, 56, 64, 72, 80, 88, 96, 104, 112, 120, 130, 140]
# The key: a long soft horizontal strip on the panel's cylinder that rises slowly over the shot, kept above the
# floor's mirror (24-31 deg; checked by tracing the framing): round 1's key (a 110 mm disc stack at 36 deg) reached
# into the floor's mirror and lit the black lacquer as a grey haze. Up here only shell pieces whose layers lean away
# from the lens by ~3-6 deg send it to the lens (their layer reflection, refracted out at ~66 deg, moves ~5 deg on the
# panel per degree of tilt), so as it rises other flame bands of each piece light up (pattern.py: the bands' tablet
# thickness, hence hue, goes with their slope). Two tries first (r1 fix): a 3-deg disc lit so few
# pieces that they blew out at the fitted level; a 6-deg disc moving sideways changed the pieces' hue by a median
# 3 (a*b*). A strip lights pieces of every sideways tilt at once; a 45-57 deg rise changed the hue by a median ~2 on
# the raw mix, so the rise is 38-64 deg (~5 deg of layer slope, as much as the flame's swing).
KEY_ELEV = (38.0, 64.0)                             # deg, the strip's centre at the first and last frame [A]
KEY_HALF_W = 350.0                                  # mm along X [A]
KEY_HALF_DEG = (3.0, 2.0, 1.0)                      # the stack's strips, elevation half-widths; widest at the back
KEY_LEVELS = (0.25, 0.5, 1.0)                       # their radiances: a soft edge [A]
N_FRAMES = SHOT["frame_out"] - SHOT["frame_in"]


def profile():
    """The dish's surface of revolution as named pieces: (name, r, z) arrays from the centre outward and round."""
    rf = pattern.FLOOR_R
    # cavetto: z = FLOOR_Z + a (r - rf)^2 up to where it meets the lip's circle tangentially enough; we end it at the
    # lip's leftmost point (r = LIP_C[0] - LIP_R, z = LIP_C[1]).
    r_end = LIP_C[0] - LIP_R
    a = (LIP_C[1] - FLOOR_Z) / (r_end - rf) ** 2
    rc = np.linspace(rf, r_end, 120)
    cav = (rc, FLOOR_Z + a * (rc - rf) ** 2)
    floor = (np.linspace(0.0, rf, 60), np.full(60, FLOOR_Z))
    # inner silver: the last bit of the cavetto (from SILVER_DOWN under the lip's centre), then the lip over the top
    th = np.linspace(math.pi, 0.0, 120)
    lip = (LIP_C[0] + LIP_R * np.cos(th), LIP_C[1] + LIP_R * np.sin(th))
    outer_s = (np.full(10, R_OUT), np.linspace(LIP_C[1], LIP_C[1] - SILVER_DOWN, 10))
    outer = (np.r_[np.full(20, R_OUT), np.linspace(R_OUT, R_OUT - 4, 20)],
             np.r_[np.linspace(LIP_C[1] - SILVER_DOWN, 1.0, 20), np.linspace(1.0, 0.0, 20)])
    base = (np.linspace(R_OUT - 4, 0.0, 30), np.zeros(30))
    cut = cav[1] < LIP_C[1] - SILVER_DOWN
    cav_lacq = (cav[0][cut], cav[1][cut])
    cav_silv = (cav[0][~cut], cav[1][~cut])
    silver = (np.r_[cav_silv[0], lip[0][1:], outer_s[0][1:]], np.r_[cav_silv[1], lip[1][1:], outer_s[1][1:]])
    lacquer = (np.r_[floor[0], cav_lacq[0][1:]], np.r_[floor[1], cav_lacq[1][1:]])
    return {"lacquer": lacquer, "silver": silver, "outer": outer, "base": base}


def revolve(r, z, phis, up_side=+1):
    """Vertices, normals, triangles of the profile (r, z) revolved over the angles phis (closed loop if full circle).
    Normals: the profile's normal turned to the side up_side (+1: the inside/top faces, as seen from above)."""
    r, z = np.asarray(r, float), np.asarray(z, float)
    dr, dz = np.gradient(r), np.gradient(z)
    k = np.hypot(dr, dz) + 1e-12
    nR, nZ = -dz / k, dr / k                       # left of the direction of travel
    if up_side < 0:
        nR, nZ = -nR, -nZ
    c, s = np.cos(phis), np.sin(phis)
    P = np.stack([r[None] * c[:, None], r[None] * s[:, None], np.broadcast_to(z, (len(phis), len(r)))], -1)
    N = np.stack([nR[None] * c[:, None], nR[None] * s[:, None], np.broadcast_to(nZ, (len(phis), len(r)))], -1)
    n_phi, n_r = len(phis), len(r)
    idx = np.arange(n_phi * n_r).reshape(n_phi, n_r)
    nxt = np.roll(idx, -1, axis=0)
    a, b, cc, d = idx[:, :-1], idx[:, 1:], nxt[:, :-1], nxt[:, 1:]
    T = np.concatenate([np.stack([a, b, d], -1).reshape(-1, 3), np.stack([a, d, cc], -1).reshape(-1, 3)])
    return P.reshape(-1, 3), N.reshape(-1, 3), T


def write_ply(path, P, N, tris):
    P = np.asarray(P, np.float32)
    N = np.asarray(N, np.float32)
    N = N / (np.linalg.norm(N, axis=1, keepdims=True) + 1e-12)
    V = np.ascontiguousarray(np.concatenate([P, N], 1))
    head = ["ply", "format binary_little_endian 1.0", f"element vertex {len(P)}",
            "property float x", "property float y", "property float z",
            "property float nx", "property float ny", "property float nz",
            f"element face {len(tris)}", "property list uchar int vertex_indices", "end_header"]
    T = np.asarray(tris, np.int32)
    face = np.zeros(len(T), dtype=[("n", "u1"), ("i", "<i4", (3,))])
    face["n"] = 3
    face["i"] = T
    with open(path, "wb") as f:
        f.write(("\n".join(head) + "\n").encode())
        f.write(V.astype("<f4").tobytes())
        f.write(face.tobytes())


def merge(parts):
    Ps, Ns, Ts, off = [], [], [], 0
    for P, N, T in parts:
        Ps.append(P)
        Ns.append(N)
        Ts.append(T + off)
        off += len(P)
    return np.concatenate(Ps), np.concatenate(Ns), np.concatenate(Ts)


# --- camera -------------------------------------------------------------------------------------------------------
class Camera:
    """Pinhole at C, looking along fwd (yaw 0, pitched down by beta), image-up from world Z (no roll); focused at u."""

    def __init__(self, C, beta, u, res):
        self.C = np.asarray(C, float)
        self.beta = beta
        self.u = u
        self.v = 1.0 / (1.0 / FOCAL_MM - 1.0 / u)
        self.res = res
        self.sensor_h = SENSOR_W_MM * res[1] / res[0]
        self.fwd = np.array([0.0, math.cos(beta), -math.sin(beta)])
        self.right = np.array([-1.0, 0.0, 0.0])          # pbrt's LookAt: up x dir; with up = +Z, dir ~ +Y: -X
        self.up = np.cross(self.fwd, self.right) * -1.0
        if self.up[2] < 0:
            self.up = -self.up

    def project(self, P, res=None):
        W, H = res or self.res
        sh = SENSOR_W_MM * H / W
        d = np.asarray(P, float) - self.C
        zf = d @ self.fwd
        x = (d @ self.right) / zf * self.v
        y = (d @ self.up) / zf * self.v
        return np.c_[W / 2 + x / SENSOR_W_MM * W, H / 2 - y / sh * H]

    def ray(self, fx, fy):
        """Direction through the frame point (fx, fy) in fractions of the width and height."""
        d = (self.fwd + (fx - 0.5) * SENSOR_W_MM / self.v * self.right + (0.5 - fy) * self.sensor_h / self.v * self.up)
        return d / np.linalg.norm(d)

    @property
    def fov_short_deg(self):
        return math.degrees(2 * math.atan(0.5 * self.sensor_h / self.v))


def silhouette_object(build):
    """The rim for optics/framing.py: the lip and the outer wall, revolved about Z."""
    pr = profile()
    side = {"kind": "revolved", "origin": [0, 0, 0], "axis": [0, 0, 1],
            "pieces": [[pr["silver"][0].tolist(), pr["silver"][1].tolist()], [pr["outer"][0].tolist(), pr["outer"][1].tolist()]]}
    path = os.path.join(build, "dish.silhouette.json")
    json.dump(side, open(path, "w"))
    return framing.Revolved(path)


def arc_of(cam, obj):
    P = obj.points(cam.C)
    front = (P - cam.C) @ cam.fwd > 1.0
    P = P[front]
    xy = cam.project(P, framing.GRID)
    x, y, _ = framing.upper_silhouette(xy, P)
    return framing.measure(x, y)


APEX = np.array([0.0, R_OUT, H_TOP])            # the far rim's top, design/world y > 0 is away from the lens


def camera_at(D, beta, u, res):
    e = math.radians(ELEV_DEG)
    return Camera(APEX + D * np.array([0.0, -math.cos(e), math.sin(e)]), beta, u, res)


def floor_hit(cam, fx, fy):
    d = cam.ray(fx, fy)
    t = (FLOOR_Z - cam.C[2]) / d[2]
    return cam.C + t * d


def solve_camera(obj, res):
    """Distance D (lens to apex) and pitch beta so the arc has the original's sagitta and apex row; the focus u
    (on the floor under FOCUS_ROW) is solved with them, as focusing changes the lens's extension (the field)."""
    tgt = np.array([SHOT["arc"]["sagitta_of_width"], SHOT["arc"]["apex_y"]])
    x = np.array([300.0, math.radians(ELEV_DEG)])
    u = 300.0
    for outer in range(8):
        def F(x):
            a = arc_of(camera_at(x[0], x[1], u, res), obj)
            return np.array([a["sagitta_of_width"], a["apex_y"]]) - tgt
        for _ in range(40):
            f = F(x)
            if np.abs(f).max() < 1e-6:
                break
            J = np.zeros((2, 2))
            for j, h in enumerate((0.5, 1e-4)):
                dx = np.zeros(2)
                dx[j] = h
                J[:, j] = (F(x + dx) - f) / h
            x = x - np.linalg.solve(J, f)
        else:
            raise SystemExit("framing: Newton did not converge")
        cam = camera_at(x[0], x[1], u, res)
        p = floor_hit(cam, 0.5, FOCUS_ROW)
        u_new = float((p - cam.C) @ cam.fwd)
        if abs(u_new - u) < 1e-4:
            break
        u = u_new
    cam = camera_at(x[0], x[1], u, res)
    return cam, arc_of(cam, obj)


# --- lights ---------------------------------------------------------------------------------------------------------
def quad(w, corners, L, group, body=0.02):
    """An area light on black velvet (body reflectance; S2: a grey body lit the dark strips)."""
    w("AttributeBegin")
    w(f'  Material "diffuse" "rgb reflectance" [ {body} {body} {body} ]')
    w(f'  Attribute "light" "string group" [ "{group}" ]')
    w(f'  AreaLightSource "diffuse" "blackbody L" [ 5500 ] "float scale" [ {L:.6g} ]')
    P = " ".join(f"{v:.4f}" for c in corners for v in c)
    w(f'  Shape "bilinearmesh" "point3 P" [ {P} ] "integer indices" [ 0 1 2 3 ]')
    w("AttributeEnd")


def facing(corners, target):
    c = [np.asarray(v, float) for v in corners]
    n = np.cross(c[1] - c[0], c[2] - c[0])
    if n @ (np.asarray(target) - 0.25 * sum(c)) <= 0:
        return [c[1], c[0], c[3], c[2]]
    return c


def band_name(i):
    return f"p{i:02d}"


def studio(w, frame):
    # the panel's strips, each band its own group
    for i in range(len(BANDS) - 1):
        for e0 in np.arange(BANDS[i], BANDS[i + 1], STRIP_DEG):
            e1 = min(e0 + STRIP_DEG, BANDS[i + 1])
            p0 = APEX + PANEL_DIST * np.array([0.0, math.cos(math.radians(e0)), math.sin(math.radians(e0))])
            p1 = APEX + PANEL_DIST * np.array([0.0, math.cos(math.radians(e1)), math.sin(math.radians(e1))])
            cs = facing([p0 + [PANEL_HALF_W, 0, 0], p0 - [PANEL_HALF_W, 0, 0], p1 + [PANEL_HALF_W, 0, 0], p1 - [PANEL_HALF_W, 0, 0]], APEX)
            quad(w, cs, 1.0, band_name(i))
    # the key: a stack of horizontal strips centred on the elevation of this frame, narrower ones in front
    ke = KEY_ELEV[0] + (KEY_ELEV[1] - KEY_ELEV[0]) * frame / max(N_FRAMES - 1, 1)
    for j, (hd, L) in enumerate(zip(KEY_HALF_DEG, KEY_LEVELS)):
        rr = PANEL_DIST - 1.0 - 0.6 * j
        e0, e1 = math.radians(ke - hd), math.radians(ke + hd)
        q0 = APEX + rr * np.array([0.0, math.cos(e0), math.sin(e0)])
        q1 = APEX + rr * np.array([0.0, math.cos(e1), math.sin(e1)])
        cs = facing([q0 + [KEY_HALF_W, 0, 0], q0 - [KEY_HALF_W, 0, 0], q1 + [KEY_HALF_W, 0, 0], q1 - [KEY_HALF_W, 0, 0]], APEX)
        quad(w, cs, L, "key")
    kx = ke
    return kx


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lut", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--frame", type=int, default=0, help="0..11 within the shot")
    ap.add_argument("--spp", type=int, default=256)
    ap.add_argument("--res", default="960x540")
    ap.add_argument("--seed", type=int, default=19, help="the pieces' colours and tilts")
    a = ap.parse_args()
    res = tuple(int(v) for v in a.res.split("x"))
    os.makedirs(a.out, exist_ok=True)

    obj = silhouette_object(a.out)
    cam, arc = solve_camera(obj, res)
    m = cam.v / cam.u
    frame_w = SENSOR_W_MM * cam.u / cam.v
    lens_r = FOCAL_MM / (2 * FNUMBER)
    print(f"lens at {np.round(cam.C, 2)} mm, pitch {math.degrees(cam.beta):.3f} deg down, focus {cam.u:.2f} mm "
          f"(floor under row {FOCUS_ROW}), magnification {m:.3f}, frame {frame_w:.1f} mm wide at the focus; "
          f"arc apex ({arc['apex_x']:.4f}, {arc['apex_y']:.4f}) sagitta {arc['sagitta_of_width']:.4f} "
          f"(spec {SHOT['arc']['apex_y']}, {SHOT['arc']['sagitta_of_width']}), resid {arc['resid_px']:.2f} px")

    # the inlay maps over the floor the lens sees (design coordinates; pattern.maps flips to object space)
    L = np.load(a.lut)
    inlay, layers, ext, st, _, _ = pattern.maps((-50.0, 50.0, 14.0, 58.0), (float(L["d_nm"][0]), float(L["d_nm"][-1])), a.seed)
    np.savez_compressed(os.path.join(a.out, "inlay.npz"), inlay=inlay, layers=layers, extent=np.array(ext))
    print(f"inlay: {st['pieces']} pieces, shell {st['shell_fraction']:.0%} of the map, {st['texels']} texels")

    pr = profile()
    fine = np.radians(np.arange(0.0, 360.0, 0.25))
    write_ply(os.path.join(a.out, "dish.ply"), *merge([
        revolve(*pr["lacquer"], fine, +1), revolve(*pr["outer"], np.radians(np.arange(0, 360, 1.0)), +1),
        revolve(*pr["base"], np.radians(np.arange(0, 360, 2.0)), +1)]))
    write_ply(os.path.join(a.out, "silver.ply"), *revolve(*pr["silver"], fine, +1))

    lut_rel = os.path.relpath(os.path.abspath(a.lut), os.path.abspath(a.out))
    Lw = []
    w = Lw.append
    w(f"# shot 19 round 1 (螺钿), generated by shots/19-luodian/scene.py, frame {a.frame}; light groups p00.., key "
      "(levels fitted afterwards by fit.py as a linear mix). PLACEHOLDER: the layers' lobe spread")
    tgt = cam.C + cam.fwd * cam.u
    w(f"LookAt {cam.C[0]:.5f} {cam.C[1]:.5f} {cam.C[2]:.5f}  {tgt[0]:.5f} {tgt[1]:.5f} {tgt[2]:.5f}  0 0 1")
    w(f'Camera "perspective" "float fov" [ {cam.fov_short_deg:.6f} ] "float lensradius" [ {lens_r:.5f} ] '
      f'"float focaldistance" [ {cam.u:.5f} ]')
    w(f'Sampler "zsobol" "integer pixelsamples" [ {a.spp} ]')
    w('Integrator "volpath" "integer maxdepth" [ 12 ]')
    w(f'Film "rgb" "integer xresolution" [ {res[0]} ] "integer yresolution" [ {res[1]} ] '
      f'"string filename" [ "frame{a.frame:02d}.exr" ] "string sensor" [ "canon_eos_5d_mkiv" ] "float iso" [ 100 ] '
      f'"bool rawsensor" true')
    w("WorldBegin")
    kx = studio(w, a.frame)
    w("AttributeBegin")
    r, g, b = TABLE_RGB
    w(f'  Material "diffuse" "rgb reflectance" [ {r} {g} {b} ]')
    w('  Shape "bilinearmesh" "point3 P" [ -2000 -2000 0  2000 -2000 0  -2000 2000 0  2000 2000 0 ] "integer indices" [ 0 1 2 3 ]')
    w("AttributeEnd")
    w("AttributeBegin")
    w(f'  Material "nacreinlay" "string tables" [ "{lut_rel}" ] "string maps" [ "inlay.npz" ] '
      f'"float lacquereta" [ {json.loads(str(L["params"]))["lacquer_n"]["value"]} ] '
      f'"float lacquerdiffuse" [ {LACQUER["diffuse"]} ] "float lacquerroughness" [ {LACQUER["alpha"]} ] '
      f'"float shellroughness" [ {SHELL["alpha_top"]} ] "float layersroughness" [ {SHELL["alpha_layers"]} ]')
    w('  Shape "plymesh" "string filename" [ "dish.ply" ]')
    w("AttributeEnd")
    w("AttributeBegin")
    w(f'  Material "conductor" "spectrum eta" [ "metal-Ag-eta" ] "spectrum k" [ "metal-Ag-k" ] '
      f'"float roughness" [ {SILVER_ALPHA} ] "bool remaproughness" false')
    w('  Shape "plymesh" "string filename" [ "silver.ply" ]')
    w("AttributeEnd")
    with open(os.path.join(a.out, "scene.pbrt"), "w") as f:
        f.write("\n".join(Lw) + "\n")
    with open(os.path.join(a.out, "optics.json"), "w") as f:
        json.dump({"f_number": FNUMBER, "magnification": round(m, 5), "sensor_width_mm": SENSOR_W_MM,
                   "focal_mm": FOCAL_MM}, f)
    json.dump({"C": cam.C.tolist(), "beta_deg": math.degrees(cam.beta), "u": cam.u, "v": cam.v, "arc": arc,
               "frame_w_mm": frame_w, "key_elev_deg": kx, "res": list(res)}, open(os.path.join(a.out, "framing.json"), "w"), indent=1)
    print(f"key strip at elevation {kx:.2f} deg -> {a.out}/scene.pbrt")


if __name__ == "__main__":
    main()
