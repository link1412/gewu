"""The optics layer's studio: a rig of lamps and a backdrop (optics/rigs/*.json) placed around an object's bounding
box and a camera, written as pbrt-v4 scene fragments that tools/rgbscene.py also reads (docs/optics.md).

World frame: millimetres, Z up, the object standing on the floor z = 0 with its bounding box centred on the Z axis.
The camera looks at the object from `front`, a horizontal unit vector (azimuth 0: -Y). A rig's directions are about
the camera, as a photographer gives them: azimuth 0 is the camera's side, +90 the image's right, 180 straight behind
the object; elevation is above the horizontal. "Image right" is pbrt's: right = up x dir (pbrt's LookAt), which a
Cycles render matches once tools/cycles_scene.py has flipped it.

Lengths in a rig are {"R": k} (k times the bounding box's half-diagonal, so one rig fits a cup or a jar) or {"mm": x}.
A lamp's strength is the illuminance it gives at the point it aims at ("lux", on a meter facing the lamp, the object
not in the way), in pbrt's photometric units (an area light's "scale" is its luminance: lights.cpp normalises the
spectrum to "1 nit"); only ratios matter to the picture, as the exposure is set by tools/camera.py.
"""

import json
import math
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import rgbscene  # noqa: E402

SENSOR_MM = (36.0, 24.0)          # full frame (the 5D Mark IV's 36 x 24 mm); a 16:9 picture uses its full width
UP = np.array([0.0, 0.0, 1.0])
BLACK = '"spectrum reflectance" [ 360 0 830 0 ]'      # a lamp's body: black, so no lamp lights another (skill-notes 18, 24)


# --- lengths and directions ------------------------------------------------------------------
def length(v, R, what):
    """{"R": k} -> k R; {"mm": x} -> x; lists element-wise."""
    if not isinstance(v, dict) or len(v) != 1 or next(iter(v)) not in ("R", "mm"):
        raise SystemExit(f"{what}: a length is {{\"R\": k}} or {{\"mm\": x}}, got {v!r}")
    k, x = next(iter(v.items()))
    x = np.asarray(x, float)
    return x * R if k == "R" else x


def unit(v):
    v = np.asarray(v, float)
    n = np.linalg.norm(v)
    if not n > 0:
        raise SystemExit("zero vector")
    return v / n


# --- the object ------------------------------------------------------------------------------
def ply_vertices(path):
    """The x, y, z of a PLY's vertices (binary little-endian or ASCII; float or double)."""
    with open(path, "rb") as f:
        head = []
        while True:
            line = f.readline()
            if not line:
                raise SystemExit(f"{path}: no end_header")
            line = line.decode("ascii", "replace").strip()
            head.append(line)
            if line == "end_header":
                break
        body = f.read()
    fmt = next(l.split()[1] for l in head if l.startswith("format"))
    props, n, in_vertex = [], 0, False
    for l in head:
        w = l.split()
        if w[0] == "element":
            in_vertex = w[1] == "vertex"
            if in_vertex:
                n = int(w[2])
        elif w[0] == "property" and in_vertex:
            if w[1] == "list":
                raise SystemExit(f"{path}: list property in the vertex element")
            props.append((w[2], w[1]))
    types = {"float": "<f4", "float32": "<f4", "double": "<f8", "float64": "<f8", "uchar": "u1", "uint8": "u1",
             "int": "<i4", "int32": "<i4", "uint": "<u4", "short": "<i2", "ushort": "<u2", "char": "i1"}
    if fmt == "binary_little_endian":
        dt = np.dtype([(name, types[t]) for name, t in props])
        V = np.frombuffer(body, dt, count=n)
        return np.stack([V["x"], V["y"], V["z"]], 1).astype(float)
    if fmt == "ascii":
        rows = body.decode().split("\n")[:n]
        names = [p[0] for p in props]
        A = np.array([[float(x) for x in r.split()[:len(names)]] for r in rows])
        return A[:, [names.index("x"), names.index("y"), names.index("z")]]
    raise SystemExit(f"{path}: PLY format {fmt} not handled")


def bounds(scene_path, key_K=5500.0):
    """The bounding box (lo, hi, mm) of everything in a pbrt fragment, as tools/rgbscene.py reads it."""
    sc = rgbscene.convert(scene_path, "canon_eos_5d_mkiv", key_K)
    base = os.path.dirname(os.path.abspath(scene_path))
    pts = []
    for o in sc["objects"]:
        M = np.array(o["matrix"]) / rgbscene.MM            # metres back to mm (the matrix carries the mm -> m scale)
        M[3, 3] = 1.0
        if o["kind"] == "quad":
            P = np.array(o["P"])
        elif o["kind"] == "disk":
            a = np.linspace(0, 2 * np.pi, 65)
            P = np.c_[o["radius"] * np.cos(a), o["radius"] * np.sin(a), np.zeros_like(a)]
        elif o["kind"] == "ply":
            P = ply_vertices(os.path.join(base, o["file"]))
        else:
            raise SystemExit(f"{o['name']}: kind {o['kind']}")
        pts.append((np.c_[P, np.ones(len(P))] @ M.T)[:, :3])
    if not pts:
        raise SystemExit(f"{scene_path}: no shapes")
    P = np.concatenate(pts)
    return P.min(0), P.max(0)


# --- the camera ------------------------------------------------------------------------------
class Camera:
    """A thin lens. Two ways to place it:
    - "fill": looking at `aim` from azimuth/elevation, at the distance that makes the object's height `fill` of the
      picture's height (magnification from the thin-lens equation; perspective of the box's depth ignored, so the
      fill is approximate), focused on `aim`;
    - "frame": {"arc_of_shot": n} (or {"arc": {apex_x, apex_y, sagitta_of_width}}): looking along azimuth/elevation,
      the lens moved (across, up, along the view) and focused so the object's upper silhouette makes that arc, with
      the focus on the silhouette at the arc's apex (optics/framing.py; the object must come with its silhouette).
    pbrt's fov is the full angle across the picture's shorter side."""

    def __init__(self, spec, lo, hi, res, silhouette=None):
        self.spec = spec
        self.res = tuple(res)
        f = float(spec["focal_mm"])
        self.f, self.N = f, float(spec["f_number"])
        self.sensor_w = SENSOR_MM[0]
        self.sensor_h = SENSOR_MM[0] * self.res[1] / self.res[0]
        if self.sensor_h > SENSOR_MM[1] + 1e-9:
            raise SystemExit(f"res {res}: taller than 3:2 is not handled")
        az, el = math.radians(spec.get("azimuth_deg", 0.0)), math.radians(spec.get("elevation_deg", 0.0))
        self.front = np.array([-math.sin(az), -math.cos(az), 0.0])     # azimuth 0: the camera on -Y
        self.arc = self.arc_target = None
        if "frame" in spec:
            if silhouette is None:
                raise SystemExit("camera 'frame': the object has no silhouette file (<object>.silhouette.json)")
            self._frame_to_arc(spec["frame"], silhouette, lo, hi, el)
        else:
            centre = 0.5 * (lo + hi)
            aim = {"centre": centre, "floor": np.array([centre[0], centre[1], lo[2]]),
                   "top": np.array([centre[0], centre[1], hi[2]])}[spec.get("aim", "centre")]
            self.aim = aim + np.asarray(spec.get("aim_offset_mm", [0, 0, 0]), float)
            height = hi[2] - lo[2]
            if "distance_mm" in spec:
                self.u = float(spec["distance_mm"])
            else:
                k = spec.get("fill", 0.75) * self.sensor_h / height          # magnification v/u
                self.u = f * (1 + 1 / k)
            if not self.u > f:
                raise SystemExit("the object is closer than the focal length")
            self.v = 1 / (1 / f - 1 / self.u)
            self.eye = self.aim + self.u * (math.cos(el) * self.front + math.sin(el) * UP)
        self.dir = unit(self.aim - self.eye)
        self.right = unit(np.cross(UP, self.dir))                          # pbrt's LookAt
        self.upv = np.cross(self.dir, self.right)
        self.fov = math.degrees(2 * math.atan(0.5 * min(self.sensor_w, self.sensor_h) / self.v))

    def _frame_to_arc(self, fr, sil, lo, hi, el):
        """Newton on (distance, across, up, focus): the measured arc = the target, the focus distance = the depth of
        the silhouette's point at the apex. The view's direction is fixed by azimuth and elevation."""
        import framing
        tgt = framing.shot_arc(fr["arc_of_shot"]) if "arc_of_shot" in fr else \
            {k: float(fr["arc"][k]) for k in ("apex_x", "apex_y", "sagitta_of_width")}
        d = unit(-(math.cos(el) * self.front + math.sin(el) * UP))
        r = unit(np.cross(UP, d))
        up = np.cross(d, r)
        top = np.array([0.5 * (lo[0] + hi[0]), 0.5 * (lo[1] + hi[1]), hi[2]])
        width = float(max(hi[0] - lo[0], hi[1] - lo[1]))
        Wg, Hg = framing.GRID
        sw, sh = self.sensor_w, self.sensor_w * Hg / Wg

        def look(x):
            D, s, t, u = x
            v = 1 / (1 / self.f - 1 / u)
            eye = top - D * d + s * r + t * up
            P = sil.points(eye)
            q = P - eye
            z = q @ d
            xy = np.c_[Wg / 2 + (q @ r) / z * v / sw * Wg, Hg / 2 - (q @ up) / z * v / sh * Hg]
            xy[z <= 0] = np.nan
            xs, ys, Ps = framing.upper_silhouette(xy, P)
            a = framing.measure(xs, ys)
            i = int(np.argmin(np.abs(xs - a["apex_x"] * Wg)))
            a["focus_depth"] = float((Ps[i] - eye) @ d)
            return a, eye, xs, ys

        def F(x):
            a = look(x)[0]
            return np.array([a["sagitta_of_width"] - tgt["sagitta_of_width"], a["apex_x"] - tgt["apex_x"],
                             a["apex_y"] - tgt["apex_y"], (a["focus_depth"] - x[3]) / x[3]])

        u0 = self.f * (1 + width / 1.5 / sw)                    # a first guess: the frame 2/3 of the object wide
        x = np.array([u0, 0.0, 0.0, u0])
        steps = np.array([0.5, 0.1, 0.1, 0.5])
        fx = F(x)
        for _ in range(40):
            if np.abs(fx).max() < 1e-6:
                break
            J = np.zeros((4, 4))
            for j in range(4):
                dx = np.zeros(4)
                dx[j] = steps[j]
                J[:, j] = (F(x + dx) - fx) / steps[j]
            step = np.linalg.solve(J, fx)
            lam = 1.0
            while True:                                       # damped: never let the error grow
                try:
                    x1 = x - lam * step
                    f1 = F(x1)
                    if np.abs(f1).max() < np.abs(fx).max() or lam < 1e-3:
                        break
                except SystemExit:
                    pass
                lam /= 2
                if lam < 1e-3:
                    raise SystemExit(f"framing to the arc {tgt}: Newton stalls at {x} (residual {fx})")
            x, fx = x1, f1
        if np.abs(fx).max() > 1e-4:
            raise SystemExit(f"framing to the arc {tgt}: no solution (residual {fx}); try another elevation or object")
        a, eye, xs, ys = look(x)
        self.u = float(x[3])
        if not self.u > self.f:
            raise SystemExit("the object is closer than the focal length")
        self.v = 1 / (1 / self.f - 1 / self.u)
        self.eye, self.aim = eye, eye + self.u * d
        self.arc, self.arc_target = {k: round(v, 6) for k, v in a.items()}, tgt
        self._env = (xs / Wg, ys / Hg)                          # the upper silhouette, in fractions of the frame

    def silhouette_y(self, x_px):
        """The upper silhouette's y (pixels at this camera's res) at x (pixels); nan where it is not in the frame."""
        if self.arc is None:
            raise SystemExit("silhouette_y: only for a camera framed to an arc")
        W, H = self.res
        xs, ys = self._env
        y = np.interp(np.asarray(x_px) / W, xs, ys, left=np.nan, right=np.nan)
        return y * H

    @property
    def magnification(self):
        return self.v / self.u

    def project(self, P):
        """World points -> pixels (x right, y down), as pbrt's perspective camera; nan behind the lens."""
        d = np.atleast_2d(P) - self.eye
        z = d @ self.dir
        x = (d @ self.right) / z * self.v
        y = (d @ self.upv) / z * self.v
        W, H = self.res
        out = np.c_[W / 2 + x / self.sensor_w * W, H / 2 - y / self.sensor_h * H]
        out[z <= 0] = np.nan
        return out

    def lines(self):
        """The scene header up to WorldBegin (pbrt's syntax)."""
        e, t = self.eye, self.aim
        return [f"LookAt {e[0]:.4f} {e[1]:.4f} {e[2]:.4f}  {t[0]:.4f} {t[1]:.4f} {t[2]:.4f}  0 0 1",
                f'Camera "perspective" "float fov" [ {self.fov:.6f} ] "float lensradius" [ {self.f / (2 * self.N):.5f} ] '
                f'"float focaldistance" [ {self.u:.4f} ]']

    def optics_json(self):
        """For tools/camera.py's diffraction (working f-number N (1 + m))."""
        return {"f_number": self.N, "magnification": round(self.magnification, 6), "sensor_width_mm": self.sensor_w,
                "focal_mm": self.f}

    def summary(self):
        out = {"eye": self.eye.tolist(), "aim": self.aim.tolist(), "distance_mm": self.u, "fov_deg": self.fov,
               "magnification": self.magnification, "frame_width_mm": self.sensor_w / self.magnification}
        if self.arc is not None:
            out.update(arc=self.arc, arc_target=self.arc_target)
        return out


# --- the rig ---------------------------------------------------------------------------------
def load(path):
    rig = json.load(open(path))
    for k in ("name", "spectrum", "lamps", "backdrop"):
        if k not in rig:
            raise SystemExit(f"{path}: no {k!r}")
    names = [l["name"] for l in rig["lamps"]]
    if len(set(names)) != len(names):
        raise SystemExit(f"{path}: lamp names repeat")
    return rig


def frame(cam):
    """(front, right, up): the rig's directions, horizontal front towards the camera, right = the image's right."""
    return cam.front, unit(np.cross(UP, -cam.front)), UP


def direction(cam, az_deg, el_deg):
    f, r, z = frame(cam)
    a, e = math.radians(az_deg), math.radians(el_deg)
    return math.cos(e) * (math.cos(a) * f + math.sin(a) * r) + math.sin(e) * z


class Studio:
    """A rig placed about the object's box (lo, hi) for this camera."""

    def __init__(self, rig, lo, hi, cam, overrides=None):
        self.rig = json.loads(json.dumps(rig))
        for k, v in (overrides or {}).items():         # {"lamps.key.lux": 3000, "backdrop.material": "white_paper"}
            self._override(k, v)
        self.lo, self.hi, self.cam = lo, hi, cam
        self.centre = 0.5 * (lo + hi)
        self.R = 0.5 * float(np.linalg.norm(hi - lo))
        self.back = self._backdrop()
        self.lamps = [self._lamp(l) for l in self.rig["lamps"]]

    def _override(self, key, value):
        parts = key.split(".")
        node = self.rig
        for p in parts[:-1]:
            if isinstance(node, list):
                node = next((x for x in node if x.get("name") == p), None)
                if node is None:
                    raise SystemExit(f"override {key}: no lamp {p!r}")
            else:
                node = node[p]
        node[parts[-1]] = value

    def anchor(self, spec):
        c, lo, hi = self.centre, self.lo, self.hi
        name = spec.get("anchor", "centre")
        if name == "centre":
            p = c.copy()
        elif name == "top":
            p = np.array([c[0], c[1], hi[2]])
        elif name == "floor":
            p = np.array([c[0], c[1], 0.0])
        elif name == "wall":                      # the backdrop's wall behind the object, at a height above the floor
            if self.back is None or self.back["kind"] != "sweep":
                raise SystemExit("anchor 'wall' needs a sweep backdrop")
            p = np.array([c[0], c[1], 0.0]) - self.back["depth"] * self.cam.front + \
                UP * float(length(spec["height"], self.R, "wall height"))
        elif name == "ground_seen":               # the backdrop where the camera sees it, through the frame's top middle
            p = self.ground_seen()
        else:
            raise SystemExit(f"anchor {name!r}: centre, top, floor, wall or ground_seen")
        if "dz" in spec:                          # moved up (or down) from the anchor
            p = p + UP * float(length(spec["dz"], self.R, "anchor dz"))
        return p

    def ground_seen(self, y_frac=0.1):
        """The point of the sweep the lens centre sees through (0.5, y_frac) of the frame: on the floor if the ray
        lands there before the cove, else on the wall's plane (the cove taken as its floor or wall, an anchor only)."""
        if self.back is None or self.back["kind"] != "sweep":
            raise SystemExit("anchor 'ground_seen' needs a sweep backdrop")
        cam = self.cam
        d = unit(cam.v * cam.dir + (0.5 - y_frac) * cam.sensor_h * cam.upv)
        O = np.array([self.centre[0], self.centre[1], 0.0])
        back = -cam.front
        D, rho = self.back["depth"], self.back["cove"]
        if d[2] < 0:
            P = cam.eye + (-cam.eye[2] / d[2]) * d
            if (P - O) @ back < D - rho:
                return P
        t = (D - (cam.eye - O) @ back) / (d @ back)
        if not t > 0:
            raise SystemExit("anchor 'ground_seen': the camera does not look towards the backdrop")
        return cam.eye + t * d

    def _lamp(self, L):
        where = f"lamp {L['name']}"
        for k in ("group", "shape", "size", "at", "lux"):
            if k not in L:
                raise SystemExit(f"{where}: no {k!r}")
        at = L["at"]
        P = self.anchor(at) + float(length(at["distance"], self.R, where)) * direction(self.cam, at["azimuth_deg"],
                                                                                         at["elevation_deg"])
        target = self.anchor(L.get("aim", {"anchor": "centre"}))
        n = unit(target - P)                                    # the emitting side faces the target
        size = length(L["size"], self.R, where)
        if L["shape"] in ("rect", "strip"):
            w, h = (float(size[0]), float(size[1]))
            ref = UP if abs(n @ UP) < 0.95 else self.cam.front  # a lamp overhead: its "up" edge towards the camera
            vh = unit(ref - (ref @ n) * n)
            uw = unit(np.cross(vh, n))
            roll = math.radians(L.get("roll_deg", 0.0))
            uw, vh = math.cos(roll) * uw + math.sin(roll) * vh, -math.sin(roll) * uw + math.cos(roll) * vh
            corners = [P - w / 2 * uw - h / 2 * vh, P + w / 2 * uw - h / 2 * vh,
                       P - w / 2 * uw + h / 2 * vh, P + w / 2 * uw + h / 2 * vh]
            if np.cross(corners[1] - corners[0], corners[2] - corners[0]) @ n <= 0:   # pbrt's emitting side
                corners = [corners[1], corners[0], corners[3], corners[2]]
            g = {"corners": np.array(corners)}
            samples = self._rect_samples(np.array(corners))
            area = w * h
        elif L["shape"] == "disk":
            r = float(np.atleast_1d(size)[0]) / 2                    # size: the diameter
            g = {"centre": P, "normal": n, "radius": r}
            samples = self._disk_samples(P, n, r)
            area = math.pi * r * r
        else:
            raise SystemExit(f"{where}: shape {L['shape']!r}: rect, strip or disk")
        # luminance for the asked illuminance at the target (a meter facing the lamp, nothing in the way)
        meter = unit(P - target)
        d = samples - target
        r2 = (d * d).sum(1)
        dn = d / np.sqrt(r2)[:, None]
        e1 = np.maximum(dn @ meter, 0) * np.maximum(-(dn @ n), 0) / r2 * (area / len(samples))
        E1 = float(e1.sum())
        if not E1 > 0:
            raise SystemExit(f"{where}: does not light its target")
        lum = float(L["lux"]) / E1
        out = {"name": L["name"], "group": L["group"], "shape": L["shape"], "centre": P, "normal": n,
               "target": target, "luminance": lum, "lux": float(L["lux"]), "area_mm2": area,
               "spectrum": L.get("spectrum", self.rig["spectrum"]), "in_frame": bool(L.get("in_frame", False)),
               "behind_object": bool(L.get("behind_object", False)), **g}
        out["clear_px"] = self.clear_px(out)
        if out["behind_object"]:
            out["hidden_px"] = self.hidden_px(out)
            if out["hidden_px"] < self.margin_px() / 2:
                raise SystemExit(f"{where}: meant to be hidden behind the object, but comes {out['hidden_px']:.0f} px "
                                 f"short of {self.margin_px() / 2:.0f} below its upper silhouette")
        elif not out["in_frame"] and out["clear_px"] < self.margin_px():
            raise SystemExit(f"{where}: {out['clear_px']:.0f} px from the frame's edge, less than {self.margin_px():.0f} "
                             f"(move it, or mark it \"in_frame\": true)")
        self._check_in_studio(out)
        return out

    def margin_px(self):
        return 0.05 * self.cam.res[0]

    @staticmethod
    def _rect_samples(c, n=48):
        u = (np.arange(n) + 0.5) / n
        U, V = np.meshgrid(u, u)
        U, V = U.ravel()[:, None], V.ravel()[:, None]
        return (1 - U) * (1 - V) * c[0] + U * (1 - V) * c[1] + (1 - U) * V * c[2] + U * V * c[3]

    @staticmethod
    def _disk_samples(P, n, r, k=48):
        a = unit(np.cross(n, [1.0, 0, 0] if abs(n[0]) < 0.9 else [0, 1.0, 0]))
        b = np.cross(n, a)
        u = (np.arange(k) + 0.5) / k
        U, V = np.meshgrid(u, u)
        rr, th = r * np.sqrt(U.ravel()), 2 * np.pi * V.ravel()             # equal-area polar grid
        return P + (rr * np.cos(th))[:, None] * a + (rr * np.sin(th))[:, None] * b

    def outline(self, L, k=200):
        if "corners" in L:
            c = L["corners"]
            u = np.linspace(0, 1, k)[:, None]
            return np.concatenate([c[i] + u * (c[j] - c[i]) for i, j in ((0, 1), (1, 3), (3, 2), (2, 0))])
        a = unit(np.cross(L["normal"], [1.0, 0, 0] if abs(L["normal"][0]) < 0.9 else [0, 1.0, 0]))
        b = np.cross(L["normal"], a)
        t = np.linspace(0, 2 * np.pi, k)[:, None]
        return L["centre"] + L["radius"] * (np.cos(t) * a + np.sin(t) * b)

    def clear_px(self, L):
        """How far (px) the lamp's outline stays outside the frame (negative: inside), seen from the lens centre;
        every edge sampled, not just the corners (skill-notes 7)."""
        xy = self.cam.project(self.outline(L))
        W, H = self.cam.res
        ok = ~np.isnan(xy[:, 0])
        if not ok.any():
            return math.inf
        out = np.max(np.c_[-xy[ok, 0], xy[ok, 0] - W, -xy[ok, 1], xy[ok, 1] - H], axis=1)
        return float(out.min())

    def hidden_px(self, L):
        """For a lamp behind the object: how far (px) its outline stays below the object's upper silhouette, where
        it is inside the frame (the object fills the frame under the arc: framed to an arc only). inf: never in the
        frame."""
        xy = self.cam.project(self.outline(L))
        W, H = self.cam.res
        m = ~np.isnan(xy[:, 0]) & (xy[:, 0] >= 0) & (xy[:, 0] <= W) & (xy[:, 1] >= 0) & (xy[:, 1] <= H)
        if not m.any():
            return math.inf
        if self.cam.arc is None:
            raise SystemExit(f"lamp {L['name']}: 'behind_object' needs a camera framed to an arc")
        below = xy[m, 1] - self.cam.silhouette_y(xy[m, 0])
        if np.isnan(below).any():
            return -math.inf
        return float(below.min())

    def _check_in_studio(self, L):
        pts = self.outline(L)
        if pts[:, 2].min() <= 1.0:
            raise SystemExit(f"lamp {L['name']}: reaches below the floor")
        if self.back is not None and self.back["kind"] == "sweep":
            depth = (pts - np.array([self.centre[0], self.centre[1], 0.0])) @ (-self.cam.front)
            if depth.max() >= self.back["depth"] - 1.0:
                raise SystemExit(f"lamp {L['name']}: behind the backdrop's wall")

    # --- the backdrop ----------------------------------------------------------------------
    def _backdrop(self):
        b = self.rig["backdrop"]
        if b["kind"] == "none":
            return None
        if b["kind"] != "sweep":
            raise SystemExit(f"backdrop {b['kind']!r}: sweep or none")
        mats = json.load(open(os.path.join(ROOT, "optics/backdrops.json")))["materials"]
        if b["material"] not in mats:
            raise SystemExit(f"backdrop material {b['material']!r}: not in optics/backdrops.json")
        m = mats[b["material"]]
        R = self.R
        if ("reflectance" in m) == ("rgb" in m):
            raise SystemExit(f"backdrop material {b['material']!r}: give one of reflectance (a spectrum) or rgb")
        out = {"kind": "sweep", "material": b["material"], "reflectance": m.get("reflectance"), "rgb": m.get("rgb"),
               "depth": float(length(b["distance"], R, "backdrop distance")),
               "cove": float(length(b["cove"], R, "backdrop cove")),
               "height": float(length(b["height"], R, "backdrop height")),
               "width": float(length(b["width"], R, "backdrop width"))}
        # the floor runs from behind the camera to the cove
        out["front"] = self.cam.u * 1.2 + R
        return out

    def sweep_mesh(self, n_cove=48, n_x=2):
        """Floor, cove (a quarter circle) and wall, as triangles with smooth normals; in the camera's frame."""
        b = self.back
        f, r, z = frame(self.cam)
        O = np.array([self.centre[0], self.centre[1], 0.0])
        D, rho, Hh, W, F = b["depth"], b["cove"], b["height"], b["width"], b["front"]
        prof = [(-F, 0.0, 0.0, 1.0)]                           # (depth, height, normal_depth, normal_up)
        for t in np.linspace(-np.pi / 2, 0, n_cove + 1):
            d, h = (D - rho) + rho * math.cos(t), rho + rho * math.sin(t)
            prof.append((d, h, -math.cos(t), -math.sin(t)))
        prof.append((D, Hh, -1.0, 0.0))
        xs = np.linspace(-W / 2, W / 2, n_x)
        P, N = [], []
        for d, h, nd, nu in prof:
            for x in xs:
                P.append(O + d * (-f) + x * r + h * z)
                N.append(nd * (-f) + nu * z)
        P, N = np.array(P), np.array(N)
        tris = []
        m = len(xs)
        for i in range(len(prof) - 1):
            for j in range(m - 1):
                a, b_, c, d = i * m + j, i * m + j + 1, (i + 1) * m + j, (i + 1) * m + j + 1
                tris += [(a, b_, d), (a, d, c)]
        T = np.array(tris)
        # the triangles must face the object (pbrt and Blender take the winding as the geometric normal)
        gn = np.cross(P[T[:, 1]] - P[T[:, 0]], P[T[:, 2]] - P[T[:, 0]])
        if (np.einsum("ij,ij->i", gn, N[T[:, 0]]) < 0).all():
            T = T[:, [0, 2, 1]]
        return P, N, T

    # --- writing ---------------------------------------------------------------------------
    def spectrum_param(self, s):
        if "blackbody_K" in s:
            return f'"blackbody L" [ {s["blackbody_K"]:g} ]'
        if "named" in s:
            return f'"spectrum L" "{s["named"]}"'
        raise SystemExit(f"lamp spectrum {s}: blackbody_K or named (pbrt's named illuminants)")

    def write(self, path, only=None, backdrop_ply="backdrop.ply", tags=True):
        """The rig as a pbrt fragment: every lamp in its group (Attribute "light" "string group"), black bodies; with
        `only` a group name, the other groups' lamps are there but dark (same geometry: pbrt's per-group reference);
        with tags False, no groups at all (one Cycles image, as before light groups: the tests' "all on")."""
        w = [f"# rig {self.rig['name']}, written by optics/studio.py" + (f"; only group {only} lit" if only else "")]
        for L in self.lamps:
            lit = only is None or L["group"] == only
            w.append(f"# lamp {L['name']} ({L['shape']}): {L['lux']:g} lux at its target, luminance {L['luminance']:.6g}")
            w.append("AttributeBegin")
            if lit and tags:
                w.append(f'  Attribute "light" "string group" [ "{L["group"]}" ]')
            if lit:
                w.append(f'  AreaLightSource "diffuse" {self.spectrum_param(L["spectrum"])} "float scale" [ {L["luminance"]:.6g} ]')
            w.append(f"  Material \"diffuse\" {BLACK}")
            if "corners" in L:
                pts = " ".join(f"{x:.4f}" for c in L["corners"] for x in c)
                w.append(f'  Shape "bilinearmesh" "point3 P" [ {pts} ] "integer indices" [ 0 1 2 3 ]')
            else:
                c, n = L["centre"], L["normal"]
                w.append(f"  Translate {c[0]:.4f} {c[1]:.4f} {c[2]:.4f}")
                axis = np.cross([0, 0, 1.0], n)
                if np.linalg.norm(axis) > 1e-9:
                    ang = math.degrees(math.acos(np.clip(n[2], -1, 1)))
                    a = unit(axis)
                    w.append(f"  Rotate {ang:.6f} {a[0]:.6f} {a[1]:.6f} {a[2]:.6f}")
                elif n[2] < 0:
                    w.append("  Rotate 180 1 0 0")
                w.append(f'  Shape "disk" "float radius" [ {L["radius"]:.4f} ]')
            w.append("AttributeEnd")
        if self.back is not None:
            refl = self.back["reflectance"]
            if self.back["rgb"] is not None:          # pbrt's sigmoid spectrum of a linear sRGB albedo
                param = '"rgb reflectance" [ ' + " ".join(f"{x:g}" for x in self.back["rgb"]) + " ]"
            else:
                param = '"spectrum reflectance" [ ' + " ".join(
                    f"{x:g}" for x in (refl if isinstance(refl, list) else [360, refl, 830, refl])) + " ]"
            w += [f"# backdrop: {self.back['material']} sweep", "AttributeBegin",
                  f'  Material "diffuse" {param}',
                  f'  Shape "plymesh" "string filename" [ "{backdrop_ply}" ]', "AttributeEnd"]
        with open(path, "w") as f:
            f.write("\n".join(w) + "\n")

    def groups(self):
        out = []
        for L in self.lamps:
            if L["group"] not in out:
                out.append(L["group"])
        return out

    def summary(self):
        def clean(v):
            return np.round(v, 4).tolist() if isinstance(v, np.ndarray) else v
        return {"R_mm": self.R, "box_mm": [self.lo.tolist(), self.hi.tolist()],
                "lamps": [{k: clean(v) for k, v in L.items()} for L in self.lamps],
                "backdrop": self.back}


def write_ply(path, P, N, T, uv=None):
    """Binary little-endian PLY: float xyz, normals, optional u, v (rgbscene and pbrt read them as the UVs); int
    vertex_indices (as shots/06-guan/scene.py)."""
    cols = [P, N] + ([uv] if uv is not None else [])
    V = np.ascontiguousarray(np.concatenate(cols, 1), "<f4")
    head = ["ply", "format binary_little_endian 1.0", f"element vertex {len(P)}",
            "property float x", "property float y", "property float z",
            "property float nx", "property float ny", "property float nz"]
    if uv is not None:
        head += ["property float u", "property float v"]
    head += [f"element face {len(T)}", "property list uchar int vertex_indices", "end_header"]
    face = np.zeros(len(T), dtype=[("n", "u1"), ("i", "<i4", (3,))])
    face["n"] = 3
    face["i"] = T
    with open(path, "wb") as f:
        f.write(("\n".join(head) + "\n").encode())
        f.write(V.tobytes())
        f.write(face.tobytes())
