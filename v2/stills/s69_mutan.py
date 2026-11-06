"""Shot 69: a heap of burning charcoal, through a long lens, wide open. Replaces s67_mutan. One piece alone could not be read as charcoal (three designs); a heap can.

    python3 -I v2/stills/s69_mutan.py still [preview|mid|final] [tag] [json of heat params]
    python3 -I v2/stills/s69_mutan.py views '[{"AIM_X": -3, "EL": 18}, ...]'     framings to choose from, one sheet. still and take use the pinned CAMERA
    python3 -I v2/stills/s69_mutan.py take_prep [preview|key|final] [json]          the solve and the stacks of glow; needs torch and a CUDA GPU
    python3 -I v2/stills/s69_mutan.py take_render [preview|key|final]               Blender only; out/v2/s69_mutan_move_{preview,final}, which is what film.py reads
    (needs torch and a CUDA GPU; set GEWU_BLENDER and GEWU_GPU_API=OPTIX. The final take: 36 frames at 768 spp, about 1 minute of solve and 4 to 5 of render)

- Each coal is a solid: an irregular prism along the grain, split faces meeting in ridges, the ends broken in chips. Its cracks are sheets in the wood: grown as a map over (along the grain, round the pith) by s69_crack and carved through the solid along the rays, so on the flank they are the brickwork of charred wood and on a broken end they are radial checks. Rings are cylinders round the pith. Char is matte: no highlight carries the surface, only grain, vessels and a thin ash, all set by eye against ref/charcoal.
- The heap is poured with Bullet (s69_pile_bpy.py, in Blender): they rest on each other and leave real gaps. A few coals are then laid by hand (RELAID).
- Temperature is solved over the whole heap by s69_heat: what each face sees. Faces turned to each other, in the gaps, burn through; faces turned to the room stay black, and go red further down the heap.
- The take: the camera and the coals stay and only the glow changes. The edge of the glow creeps into the black, cracks catch along their length, and puffs of air cross the heap one after another, left to right, so a place rises and sinks again as one passes. What has burnt through changes less. See Fire.begin_take.
ESTIMATES: sizes, the heap's spread, every height and rate. Which faces have burnt through follows the traced view of the room, with a noise and a bias per coal that are chosen, not solved. How far up a crack glows is an estimate too.
"""

import hashlib
import json
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cv2
import numpy as np
import torch
import torch.nn.functional as TF
from scipy.ndimage import distance_transform_edt
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree

import kit
from darkroom import develop as dev
from kit import OUT
from s69_crack import DEV, grow, noise
from s69_heat import DEFAULT as HEAT_DEFAULT
from s69_heat import SIGMA, Heat, trace
from s69_shell import fbm2, ring_phase, sstep, surface_nets
from vessel import cam_basis, frame_camera, project, top_arc

NAME = "s69_mutan"
HERE = os.path.dirname(os.path.abspath(__file__))
D_OUT = os.path.join(OUT, NAME)

# --- the frame
W_FRAME = 18.0  # cm across the frame at the subject
EL, AZ = 18.0, 5.0
DIST = 58.0
APERTURE_MM = 16.0  # blur in the object plane: 0.028 of the distance from focus
CREST_Y = 0.52  # the median of the heap's upper edge in the frame: the coal in focus then tops out at about .43, under the caption, which stays at .37
AIM_X = -3.0  # cm, where along the heap the frame is
FOCUS_AT = (0.5, 0.5)
SEED = 6900
N_COALS = 72
SPREAD = (5.0, 3.0)  # sigma of where coals are poured from, cm
BOX = (13.0, 8.0)  # half sizes of the walls that keep the pour together until it has landed, cm
RREF = 1.53  # t = RREF x angle round the pith
END_NO_FINE = 0.012  # cm, keeps all but the widest fine cracks from opening on a broken end: they stay as bright lines in the glow
MAP_S, MAP_T = 8.0, 2.0 * np.pi * RREF


# --- cracks at this scale: PRESETS of s69_crack scaled up by 3 (L by 3, so k by 1/9)
CRACK = {
    "macro": dict(dx=0.03, l=0.075, E_s=4.0, E_t=1.0, G=0.25, k=0.13, e_s=0.05, e_t=0.07, ec_t=0.03, A_s=1.0, gc_patch=0.18, patch=1.5, gc_fibre=0.1, fibre_w=0.15, fibre_len=3.0, tau0=0.25, steps=50, stag=3, iters_u=90, iters_d=25),
    "fine": dict(dx=0.0075, l=0.015, E_s=6.0, E_t=1.0, G=0.2, k=28.0, e_s=0.016, e_t=0.042, ec_t=0.03, A_s=9.0, gc_patch=0.14, patch=0.75, gc_fibre=0.12, fibre_w=0.03, fibre_len=1.5, tau0=0.5, steps=40, stag=3, iters_u=80, iters_d=25),
}
N_MAPS = 3
LEAN = {60: 0.06, 69: 0.13, 39: -0.35, 11: -0.75, 28: -0.6, 44: 0.0, 57: -0.1, 27: -0.25}  # chosen by hand. 11, in front: black, with the glow in its cracks, as on the top of 60 (RELAID). 28, behind it: dark, so the gaps between the pieces in front of it read as gaps. 44, 57, 27: the pieces of the hot heart. 60, the coal in focus: burnt through from about half way up, so the frame's centre goes from black to red. 69, to its right: the same, or its lower half stays between black and red and reads as raw meat. 39, behind on the right: one big face, which out of focus is one flat bright slab
CRAZE_GROOVE = 0.012  # cm, by eye: a pixel or so
PUFF_K, PUFF_TAU = 30.0, 0.1  # ESTIMATES, by eye: K per unit of extra air, and s. The reaction is in a skin far thinner than a node of the heat solve, which would only change how fast the glow rises: this much at the surface lets it sink again after a puff
SURF_COOL, CRACK_HOT = 45.0, 50.0  # K, by eye. A burnt-through face in the open loses heat to the air and the room, what is in a crack sees only more hot char: the crack is the brightest thing on it. With the crack darker than the face and the face even, a piece reads as a thin thing lit from behind, a dry leaf or parchment (a reviewer's words, and they were right)
# By hand, after the pour. turn: about the camera's up, about the view, about its own axis, in degrees. at: x, y in the frame, depth from the plane of focus in cm.
# 11: as it fell, its broken end faced the camera square on, in the plane of focus, in front of the hot heart: flat, even and thin against the light, it read as a dry leaf through four rounds of shading (a reviewer's word). With its flank to the camera it is a dark block in front of the heart (ref/charcoal/charbon.jpg, at the bottom).
# 44, 57, 27: small coals from the far side of the heap, none of which the camera saw. The heart behind 11 was one coal's flank, out of focus, and read as a net of ribs in three reviews: these make it a heap of pieces with dark gaps between them.
RELAID = {
    11: {"turn": (14.0, -9.0, 52.0)},
    44: {"turn": (35.0, 20.0, 20.0), "at": (0.545, 0.865, 4.0)},
    57: {"turn": (-25.0, -35.0, 100.0), "at": (0.605, 0.835, 6.5)},
    27: {"turn": (60.0, 10.0, 200.0), "at": (0.50, 0.875, 5.5)},
}
CAMERA = {"loc": [1.8398861906106938, -56.464617744564755, 25.588467892546362], "target": [-2.9677359596061605, -1.5132451156721636, 7.6654822187994105], "lens_mm": 116.0, "roll": 0.0, "shift": [0.0, 0.0], "aperture_mm": 16.0, "focus_distance": 55.414274416305915, "blades": 9}  # where camera_for put it with all 72 coals. Pinned: it reads the heap's median and top, which lifting a coal out would move
FOCUS = [-2.9000000953674316, -4.050000190734863, 8.229999542236328]
CRACK_FRONT = 0.2  # by eye: a char burns away from its cracks outward, where the air gets in. Without this the band between black and red is an even red-brown over a whole face, which read as red stone or terracotta. With it the red dies away from each crack, and far from one the coal is black
LIMB_K = 120.0  # ESTIMATE, by eye: how much cooler a glowing face reads edge-on. What is seen through a cooler film of ash comes more from the film the flatter the view, as the limb of the sun darkens. Without it a glow has no form, and a thin edge reads as silk
CRAZE_K, CRAZE_K2, CRAZE_T = 2.6, 4.3, 72.0  # what has burnt through is crazed finer than any crack on the black: how much finer, at two sizes, and how much hotter its lines are (K). By eye against ref/charcoal/charbon.jpg


# --- light of a hot body as this camera sees it
def _sensor(lam):
    """Relative spectral response of a consumer camera's channels times its daylight white balance. STAND-IN, Gaussian lobes in the usual places (no measured curve of a real camera at hand). Tails tuned to what ref/charcoal measures (charbon, gorgeous, knisternd)."""

    def g(mu, s1, s2):
        return np.exp(-0.5 * ((lam - mu) / np.where(lam < mu, s1, s2)) ** 2)

    R = 2.0 * g(600.0, 30.0, 38.0)
    G = 1.0 * g(535.0, 38.0, 42.0) + 0.018 * g(650.0, 40.0, 40.0)
    B = 1.5 * g(455.0, 26.0, 34.0) + 0.009 * g(650.0, 50.0, 50.0)
    return R, G, B


_TAB = None
EXPOSURE_T, EXPOSURE_R = 1045.0, 0.9  # a blackbody at this T comes out at this R, scene-linear


def radiance(T):
    global _TAB
    if _TAB is None:
        Ts = np.linspace(400.0, 1700.0, 1301)
        lam = np.linspace(380.0, 760.0, 191)
        R, G, B = _sensor(lam)
        c2 = 1.4388e7
        Pl = lam[None] ** -5 / (np.exp(c2 / (lam[None] * Ts[:, None])) - 1.0)
        rgb = np.stack([(Pl * R).sum(1), (Pl * G).sum(1), (Pl * B).sum(1)], -1)
        rgb = rgb / rgb[np.argmin(np.abs(Ts - EXPOSURE_T)), 0] * EXPOSURE_R
        # the stand-in lobes leave too much green and blue: graded against ref/charcoal, by eye
        rgb = rgb * np.array([1.0, 0.55, 0.7])
        _TAB = (Ts.astype(np.float32), rgb.astype(np.float32))
    Ts, tab = _TAB
    return np.stack([np.interp(T, Ts, tab[:, i]) for i in range(3)], -1).astype(np.float32)


def radiance_t(T):
    """The same table, on the device: a take looks it up for every vertex on every frame."""
    radiance(np.array([1000.0]))
    Ts, tab = _TAB
    tab = to_dev(tab)
    x = (T - float(Ts[0])) / float(Ts[1] - Ts[0])
    x = x.clamp(0.0, len(Ts) - 1.001)
    i = x.long()
    f = (x - i)[:, None]
    return tab[i] * (1.0 - f) + tab[i + 1] * f


def smin(a, b, k):
    h = (0.5 + 0.5 * (b - a) / k).clamp(0.0, 1.0)
    return b + (a - b) * h - k * h * (1.0 - h)


def smax(a, b, k):
    return -smin(-a, -b, k)


def to_dev(a):
    return torch.as_tensor(a, device=DEV, dtype=torch.float32)


class Map:
    """What is written on the wood over (s, t): the cracks, and everything that varies from cell to cell. Stacks of channels, looked up together."""

    NAMES = ["dist_f", "dist_m", "wf", "wm", "Df", "Dm", "disp", "tex"]  # used while meshing
    MORE = ["pol", "str_f", "grain", "cloth", "micro", "plate", "grit", "fine", "pits", "label"]  # used per vertex; label last

    def __init__(self, k, log=print):
        t0 = time.time()
        fp = os.path.join(D_OUT, f"cmap_{k}.npz")
        if os.path.exists(fp):
            C = dict(np.load(fp))
        else:
            C = grow(MAP_S, MAP_T, seed=SEED + 50 + 13 * k, log=log, presets=CRACK)
            np.savez(fp, **C)
        dx = CRACK["fine"]["dx"]
        H, W = C["dist_f"].shape
        seed = SEED + 500 + 7 * k
        rng = np.random.default_rng(seed)
        lab_m = cv2.connectedComponents((C["dist_m"] > 0.75 * dx).astype(np.uint8), connectivity=4)
        lab_f = cv2.connectedComponents((np.minimum(C["dist_f"], C["dist_m"]) > 0.75 * dx).astype(np.uint8), connectivity=4)
        n_m, n_f = lab_m[0], lab_f[0]
        L_m, L_f = torch.as_tensor(lab_m[1], device=DEV).long(), torch.as_tensor(lab_f[1], device=DEV).long()
        ss = (torch.arange(W, device=DEV, dtype=torch.float32) * dx)[None].expand(H, W)
        tt = (torch.arange(H, device=DEV, dtype=torch.float32) * dx)[:, None].expand(H, W)

        def per_label(L, n, a_s, a_t, a0):
            cnt = torch.zeros(n, device=DEV).index_add_(0, L.flatten(), torch.ones(H * W, device=DEV)).clamp(min=1.0)
            cs = torch.zeros(n, device=DEV).index_add_(0, L.flatten(), ss.flatten()) / cnt
            ct = torch.zeros(n, device=DEV).index_add_(0, L.flatten(), tt.flatten()) / cnt
            gs, gt, g0 = (to_dev(rng.normal(0.0, a, n)) for a in (a_s, a_t, a0))
            return g0[L] + gs[L] * (ss - cs[L]) + gt[L] * (tt - ct[L])

        block = per_label(L_m, n_m, 0.012, 0.012, 0.035)
        cell = per_label(L_f, n_f, 0.03, 0.045, 0.004)
        dist_f, dist_m = to_dev(C["dist_f"]), to_dev(C["dist_m"])
        open_f, open_m = to_dev(C["open_f"]), to_dev(C["open_m"])
        F = {"dist_f": dist_f, "dist_m": dist_m}
        F["str_f"] = sstep(-0.9, 1.0, 0.75 * noise(H, W, 0.9 / dx, 0.9 / dx, seed + 23) + 0.65 * noise(H, W, 0.15 / dx, 0.15 / dx, seed + 24))
        F["wf"] = (open_f * 0.2).clamp(max=0.012) * F["str_f"] ** 1.5 + 0.0038
        F["wm"] = (open_m * 0.03).clamp(max=0.016) + 0.006
        F["Df"] = (open_f * 9.0 + 0.07).clamp(max=0.3)
        F["Dm"] = 0.3 + 0.3 * sstep(-1.0, 1.5, noise(H, W, 0.7 / dx, 0.7 / dx, seed + 14))
        F["pol"] = to_dev(rng.random(n_f))[L_f]
        F["label"] = L_f.float()
        F["grain"] = noise(H, W, 0.015 / dx, 0.5 / dx, seed + 27)
        F["cloth"] = 0.7 * noise(H, W, 0.01 / dx, 0.3 / dx, seed + 28) + 0.5 * noise(H, W, 0.01 / dx, 0.04 / dx, seed + 29)
        F["micro"] = 0.75 * noise(H, W, 1.0, 1.0, seed + 30) + 0.65 * noise(H, W, 2.4, 2.4, seed + 31)
        F["grit"] = fbm2(H, W, dx, 0.024, 1.2, seed + 25, 0.75)
        F["plate"] = fbm2(H, W, dx, 0.036, 1.5, seed + 32, 0.75)
        F["fine"] = noise(H, W, 1.2, 0.09 / dx, seed + 33)
        # the vessels: short grooves along the grain, about 0.2 mm across. ESTIMATE, from general knowledge of hardwood
        F["pits"] = sstep(1.3, 2.1, noise(H, W, 0.009 / dx, 0.05 / dx, seed + 35))
        Ef = torch.min(dist_f, dist_m)
        F["disp"] = block + cell + 0.012 * torch.exp(-dist_m / 0.05) + 0.006 * torch.exp(-Ef / 0.035)
        # the fine network is in the surface too, and comes and goes: without it the black between the big cracks is fibres alone, all one way
        net = TF.grid_sample(dist_f[None, None], torch.stack([2.0 * ss * CRAZE_K / MAP_S - 1.0, 2.0 * tt * CRAZE_K / MAP_T - 1.0], -1)[None], mode="bilinear", align_corners=True, padding_mode="reflection")[0, 0] / CRAZE_K
        F["tex"] = 0.01 * F["pits"] + 0.011 * F["grain"] + 0.008 * F["cloth"] + 0.0035 * F["micro"] + 0.006 * F["grit"] + CRAZE_GROOVE * torch.exp(-net / 0.006) * sstep(-1.4, 0.3, F["grit"])
        self.A = torch.stack([F[n] for n in self.NAMES], 0)[None]
        self.B = torch.stack([F[n] for n in self.MORE], 0)[None]
        log(f"map {k}: {W} x {H}, blocks {n_m}, cells {n_f}, {time.time() - t0:.1f} s")

    def fine_net(self, s, t):
        """The fine network on what has burnt through, at two sizes: distances to it. And a noise at the size of a few cm."""
        return torch.cat([self.look(self.A[:, :1], s * CRAZE_K, t * CRAZE_K) / CRAZE_K, self.look(self.A[:, :1], s * CRAZE_K2 + 1.7, t * CRAZE_K2 + 3.1) / CRAZE_K2, self.look(self.B[:, 5:6], s * 0.3, t * 0.3)], 0)

    def look(self, tab, s, t, mode="bilinear"):
        """s, t: any shape, cm in the map. Past the map's edge it reflects, which leaves the fields continuous."""
        g = torch.stack([2.0 * s / MAP_S - 1.0, 2.0 * t / MAP_T - 1.0], -1)
        shp = s.shape
        out = TF.grid_sample(tab, g.reshape(1, 1, -1, 2), mode=mode, align_corners=True, padding_mode="reflection")[0, :, 0]
        return out.reshape(tab.shape[1], *shp)


class Tile:
    """A noise over the plane of the cross-section: how the fibres stand out of a broken end."""

    def __init__(self):
        n, d = 640, 0.02
        self.t = (0.6 * noise(n, n, 6.0, 6.0, SEED + 70) + 0.5 * noise(n, n, 2.0, 2.0, SEED + 71) + 0.3 * noise(n, n, 0.8, 0.8, SEED + 72))[None, None]
        self.size = n * d
        # how a coal has broken: chips with hard edges, each its own plane (ref/charcoal/rouge.jpg). Noise here came out as popcorn or sponge, and a pattern round the pith as a fan or a shell
        rng = np.random.default_rng(SEED + 76)

        def chips(cell_cm):
            m = np.ones((n, n), bool)
            m[rng.integers(0, n, int((n * d / cell_cm) ** 2)), rng.integers(0, n, int((n * d / cell_cm) ** 2))] = False
            ind = distance_transform_edt(m, return_distances=False, return_indices=True)
            yy, xx = np.mgrid[:n, :n]
            h0, gy, gx = rng.normal(0.0, 1.0, (n, n)), rng.normal(0.0, 0.6, (n, n)), rng.normal(0.0, 0.6, (n, n))
            return h0[ind[0], ind[1]] + (gy[ind[0], ind[1]] * (yy - ind[0]) + gx[ind[0], ind[1]] * (xx - ind[1])) * d / cell_cm

        self.e = to_dev((chips(0.4) + 0.2 * chips(0.14)).astype(np.float32))[None, None]
        # and a noise in space, for the lumps of the form: planes alone read as sawn timber
        n3, d3 = 96, 0.16
        self.size3 = n3 * d3
        G = torch.Generator(device="cpu").manual_seed(SEED + 73)
        f = torch.stack(torch.meshgrid(torch.fft.fftfreq(n3, device=DEV), torch.fft.fftfreq(n3, device=DEV), torch.fft.rfftfreq(n3, device=DEV), indexing="ij"), 0)
        f2 = (f**2).sum(0)

        def blob(sig_cm):
            v = torch.fft.irfftn(torch.fft.rfftn(torch.randn(n3, n3, n3, generator=G).to(DEV)) * torch.exp(-2.0 * torch.pi**2 * f2 * (sig_cm / d3) ** 2), s=(n3, n3, n3))
            return v / v.std()

        self.v = 0.16 * blob(1.0) + 0.05 * blob(0.3)

    def at(self, y, z):
        g = torch.stack([(2.0 * y / self.size), (2.0 * z / self.size)], -1)
        return TF.grid_sample(self.t, g.reshape(1, 1, -1, 2), mode="bilinear", align_corners=False, padding_mode="reflection").reshape(y.shape)

    def chipped(self, y, z):
        g = torch.stack([2.0 * y / self.size, 2.0 * z / self.size], -1)
        return TF.grid_sample(self.e, g.reshape(1, 1, -1, 2), mode="bilinear", align_corners=False, padding_mode="reflection").reshape(y.shape)

    def lumps(self, x, y, z, off):
        g = torch.stack([2.0 * (x + off[0]) / self.size3, 2.0 * (y + off[1]) / self.size3, 2.0 * (z + off[2]) / self.size3], -1)
        return TF.grid_sample(self.v[None, None], g.reshape(1, 1, 1, -1, 3), mode="bilinear", align_corners=False, padding_mode="reflection").reshape(x.shape)


class Coal:
    def __init__(self, i, maps, tile, seed):
        rng = np.random.default_rng(seed)
        self.i, self.tile, self.map = i, tile, maps[i % len(maps)]
        size = rng.lognormal(np.log(1.0), 0.28)
        self.L = float(np.clip(rng.normal(1.75, 0.45) * size, 1.0, 3.0))
        self.R = float(np.clip(rng.normal(1.2, 0.22) * size, 0.7, 1.8))
        # the cross-section: split faces, at uneven angles but always closed. What is left of the log's round is the cylinder in base()
        n = rng.integers(4, 8)
        ang = (np.arange(n) + rng.uniform(-0.3, 0.3, n)) * 2.0 * np.pi / n + rng.uniform(0, 2.0 * np.pi)
        self.ny, self.nz = np.cos(ang), np.sin(ang)
        self.d = self.R * rng.uniform(0.72, 1.08, n)
        self.off = rng.uniform(-3.0, 3.0, 3)
        # the pith sits off to one side, as in a split piece
        a = rng.uniform(0, 2.0 * np.pi)
        self.py, self.pz = float(1.1 * self.R * np.cos(a)), float(1.1 * self.R * np.sin(a))

        # the ends, and a corner or two broken off
        def tilted(sign, max_t):
            ty, tz = rng.normal(0, max_t, 2)
            v = np.array([sign, ty, tz])
            return v / np.linalg.norm(v)

        self.e1, self.e2 = tilted(1.0, 0.22), tilted(-1.0, 0.22)
        self.o1, self.o2 = self.L * rng.uniform(0.82, 1.0), self.L * rng.uniform(0.82, 1.0)
        self.cuts = []
        for _ in range(rng.integers(1, 4)):
            v = rng.normal(0, 1, 3)
            v[0] = rng.choice([-1, 1]) * rng.uniform(0.5, 1.4)
            self.cuts.append((v / np.linalg.norm(v), self.L * rng.uniform(0.6, 0.9)))
        self.s_off = float(rng.uniform(0.2, MAP_S - 2 * self.L - 0.4)) + self.L
        self.t_off = float(rng.uniform(0.0, MAP_T))
        self.th0 = 0.0
        # rings: no two alike in width or in how far they stand out, or the faces come out as corduroy
        self.bounds = torch.as_tensor(np.cumsum(np.clip(rng.lognormal(np.log(0.22), 0.8, 40), 0.05, 0.9)) - 0.2, device=DEV, dtype=torch.float32)
        self.ring_a = to_dev(rng.uniform(0.15, 1.0, 40) ** 1.5)
        # the fibres of one ring do not line up with the next: looked up as they are, the map's streaks run straight through the rings and come out on a broken end as a fan
        self.ring_off = to_dev(rng.uniform(0.0, MAP_T, 40))
        self.Rw = np.eye(3, dtype=np.float32)
        self.Cw = np.zeros(3, np.float32)
        self.bias = float(rng.normal(0.0, 0.16))
        self.bb = (self.L + 0.8, self.R * 1.35 + 0.6)
        self.ash = float(rng.normal(-0.05, 0.3))  # some coals have burnt longer and carry more of it
        self.se_off, self.te_off = float(rng.uniform(2.0, MAP_S - 2.0)), float(rng.uniform(2.0, MAP_T - 2.0))

    def base(self, x, y, z, fine=False):
        """A signed distance, near enough: negative inside. fine: the broken ends as they show. The pour and the heat solve use the coarser form, which does not change where the coals lie."""
        f = torch.sqrt(y * y + z * z) - 1.3 * self.R
        for ny, nz, d in zip(self.ny, self.nz, self.d):
            f = smax(f, y * float(ny) + z * float(nz) - float(d), 0.14)
        if fine:
            spl = self.tile.chipped(y + 0.37 * self.i, z - 0.61 * self.i)
        else:
            spl = self.tile.at(y + 0.37 * self.i, z - 0.61 * self.i)
        e1 = x * float(self.e1[0]) + y * float(self.e1[1]) + z * float(self.e1[2]) - self.o1 - 0.1 * spl
        e2 = x * float(self.e2[0]) + y * float(self.e2[1]) + z * float(self.e2[2]) - self.o2 - 0.1 * spl
        f = smax(smax(f, e1, 0.05), e2, 0.05)
        for v, o in self.cuts:
            f = smax(f, x * float(v[0]) + y * float(v[1]) + z * float(v[2]) - o - 0.06 * spl, 0.05)
        return f + self.tile.lumps(x, y, z, self.off)

    def st(self, x, y, z):
        # across the grain: the angle round the middle of the section, not round the pith. The pith is outside the piece, so round it the radial runs along the top and bottom faces, the angle hardly changes there and everything on the map comes out stretched: measured on the coal in focus, x2.55 at the median and on the one beside it x26 at the 99th percentile, read by a reviewer as a stretched texture. Round the middle: x1.3 or so. The rings keep to the pith
        th = (torch.atan2(z, y) - self.th0 + np.pi) % (2.0 * np.pi)  # 0 .. 2 pi, the seam on the far side
        r = torch.sqrt((y - self.py) ** 2 + (z - self.pz) ** 2)
        return x + self.s_off, th * self.R + self.t_off, r

    def endness(self, x, y, z):
        """1 on a broken end or a cut, 0 on the flank. Read over (along the grain, round the pith), the map is a function of the angle alone on an end: everything on it converges on the pith, a fan, and the rings make it a shell. So near an end the map is read in the plane of the cross-section instead."""
        fl = torch.sqrt(y * y + z * z) - 1.3 * self.R
        for ny, nz, d in zip(self.ny, self.nz, self.d):
            fl = torch.max(fl, y * float(ny) + z * float(nz) - float(d))
        v = self.e1
        e = x * float(v[0]) + y * float(v[1]) + z * float(v[2]) - self.o1
        v = self.e2
        e = torch.max(e, x * float(v[0]) + y * float(v[1]) + z * float(v[2]) - self.o2)
        for v, o in self.cuts:
            if abs(v[0]) > 0.7:  # a cut across the grain is an end; one along it still shows the flank's brickwork
                e = torch.max(e, x * float(v[0]) + y * float(v[1]) + z * float(v[2]) - o)
        return sstep(-0.1, 0.1, e - fl)  # whichever face is the outermost here

    def st_end(self, y, z):
        """The map's long axis along the rays from the pith: this piece was split off the log, the pith is outside it, and the checks on its end run nearly parallel, crossed by ring shakes."""
        n = np.hypot(self.py, self.pz) + 1e-6
        uy, uz = -self.py / n, -self.pz / n
        return y * uy + z * uz + self.se_off, -y * uz + z * uy + self.te_off

    def to_world(self, P):
        return P @ self.Rw.T + self.Cw

    def to_local(self, X):
        return (X - to_dev(self.Cw)) @ to_dev(self.Rw)

    def mesh(self, dx, cracks=True, log=print):
        """The surface in the coal's frame: vertices (N, 3), faces wound outward."""
        t0 = time.time()
        Lb, Rb = self.bb
        xs = torch.arange(-Lb, Lb, dx, device=DEV)
        ys = torch.arange(-Rb, Rb, dx, device=DEV)
        zs = torch.arange(-Rb, Rb, dx, device=DEV)
        Y, X = torch.meshgrid(ys, xs, indexing="ij")
        phi = torch.empty((len(zs), len(ys), len(xs)), device=DEV, dtype=torch.float32)
        m = self.map
        for k, z_ in enumerate(zs):
            Z = torch.full_like(X, float(z_))
            b = self.base(X, Y, Z, fine=cracks)
            s, t, r = self.st(X, Y, Z)
            A = m.look(m.A, s, t)
            dep = -b
            if cracks:
                f_ring, k_ring = ring_phase(r + 0.5 * self.tile.lumps(X, Y, Z, self.off), self.bounds)  # rings wander
                tx = m.look(m.A[:, 7:8], s, t + self.ring_off[k_ring])[0]
                a = self.endness(X, Y, Z)
                ends = (a > 0.0) & (b.abs() < 0.75)
                if ends.any():
                    s2, t2 = self.st_end(Y[ends], Z[ends])
                    A2 = m.look(m.A, s2, t2)
                    # an end is calmer than a flank: the big checks and little else
                    A2[0] += END_NO_FINE
                    A2[7] *= 0.5
                    tx[ends] += a[ends] * (A2[7] - tx[ends])
                    A[:, ends] += a[ends] * (A2 - A[:, ends])
                dep = dep - A[6] - tx - 0.008 * (1.0 - 0.7 * a) * self.ring_a[k_ring] * torch.exp(-f_ring / 0.2) * sstep(0.0, 0.03, f_ring)
                # a crack narrower than the grid would come out as a row of dots
                wm, wf = A[3].clamp(min=0.9 * dx), A[2].clamp(min=0.75 * dx)
                cm = torch.max(A[1] - wm * (1.0 - dep / A[5]).clamp(0.0, 1.0) ** 0.6, dep - A[5])
                cf = torch.max(A[0] - wf * (1.0 - dep / A[4]).clamp(0.0, 1.0) ** 0.7, dep - A[4])
                dep = torch.min(torch.min(dep, cm), cf)
            phi[k] = dep
        V, F = surface_nets(phi)
        del phi
        Fn = F.cpu().numpy()
        g = coo_matrix((np.ones(2 * len(Fn), np.uint8), (np.r_[Fn[:, 0], Fn[:, 1]], np.r_[Fn[:, 1], Fn[:, 2]])), shape=(len(V), len(V)))
        _, lab = connected_components(g, directed=False)
        keep = lab == np.bincount(lab).argmax()
        remap = np.cumsum(keep) - 1
        Fn = Fn[keep[Fn[:, 0]]]
        # the grid is (z, y, x): going to (x, y, z) mirrors the mesh, so the winding is turned back
        F = torch.as_tensor(remap[Fn[:, [0, 2, 1]]], device=DEV, dtype=torch.long)
        V = V[torch.as_tensor(keep, device=DEV)]
        L = torch.stack([xs[0] + V[:, 2] * dx, ys[0] + V[:, 1] * dx, zs[0] + V[:, 0] * dx], -1)
        log(f"coal {self.i}: dx {dx * 1e4:.0f} um, {len(L) / 1e6:.2f} M verts, {len(F) / 1e6:.2f} M tris, {time.time() - t0:.1f} s")
        return L, F


def rot_axis(a, deg):
    t = np.radians(deg)
    c, s_ = np.cos(t), np.sin(t)
    x, y, z = a
    return np.array([[c + x * x * (1 - c), x * y * (1 - c) - z * s_, x * z * (1 - c) + y * s_], [y * x * (1 - c) + z * s_, c + y * y * (1 - c), y * z * (1 - c) - x * s_], [z * x * (1 - c) - y * s_, z * y * (1 - c) + x * s_, c + z * z * (1 - c)]], np.float32)


def stack(coals, log=print):
    """Pour them, or take where they came to rest from s69_pile.json."""
    t0 = time.time()
    rng = np.random.default_rng(SEED + 3)
    arrays = {"n": len(coals), "frames": 1200, "walls_off": 720, "box": np.array(BOX)}
    per_layer = 6
    for c in coals:
        L, F = c.mesh(0.14, cracks=False, log=lambda *a: None)
        V = L.cpu().numpy().astype(np.float32)
        # lying down, their flanks mostly to the camera: a flank has the charred brickwork that says charcoal. The fall turns them some way from this, and that is the variety
        R = rot_axis((0, 0, 1), rng.normal(0.0, 28.0)) @ rot_axis((0, 1, 0), rng.normal(0.0, 12.0)) @ rot_axis((1, 0, 0), rng.uniform(0.0, 360.0))
        layer = c.i // per_layer
        arrays[f"V{c.i}"], arrays[f"F{c.i}"] = V, F.cpu().numpy().astype(np.int32)
        arrays[f"R{c.i}"] = R
        arrays[f"t{c.i}"] = np.array([np.clip(rng.normal(0.0, SPREAD[0]), 3.0 - BOX[0], BOX[0] - 3.0), np.clip(rng.normal(0.0, SPREAD[1]), 3.0 - BOX[1], BOX[1] - 3.0), 4.0 + 4.0 * layer + rng.uniform(0.0, 2.0)])
        arrays[f"m{c.i}"] = c.L * c.R * c.R
    # the pile is kept with the code, as it came out: a pour is chaotic, a difference in the last digit of a hull gives another heap. Delete the file to pour again
    fp = os.path.join(HERE, "s69_pile.json")
    if not os.path.exists(fp):
        os.makedirs(D_OUT, exist_ok=True)
        np.savez(os.path.join(D_OUT, "pile_in.npz"), **arrays)
        r = subprocess.run([kit.BLENDER, "-b", "--factory-startup", "--python-exit-code", "1", "-P", os.path.join(HERE, "s69_pile_bpy.py"), "--", os.path.join(D_OUT, "pile_in.npz"), fp], capture_output=True, text=True)
        if r.returncode != 0 or not os.path.exists(fp):
            raise SystemExit(f"the pour failed\n{r.stdout[-2000:]}\n{r.stderr[-2000:]}")
        log([l for l in r.stdout.splitlines() if l.startswith("pile:")][0])
    res = json.load(open(fp))
    for c, m in zip(coals, res["poses"]):
        c.Rw, c.Cw = np.array(m["R"], np.float32), np.array(m["t"], np.float32)
        if c.i in RELAID:
            yaw, tilt, roll = RELAID[c.i]["turn"]
            loc, f, right, up = cam_basis(CAMERA)
            if "at" in RELAID[c.i]:
                x, y, dz = RELAID[c.i]["at"]
                d = CAMERA["focus_distance"] + dz
                wd = d * 36.0 / CAMERA["lens_mm"]
                c.Cw = (loc + f * d + right * (x - 0.5) * wd + up * (0.5 - y) * wd * 9.0 / 16.0).astype(np.float32)
            u = rot_axis(up, yaw) @ rot_axis(f, tilt) @ right
            v = up - (up @ u) * u
            v = v / np.linalg.norm(v)
            w = np.cross(u, v)
            t = np.radians(roll)
            c.Rw = np.stack([u, np.cos(t) * v + np.sin(t) * w, -np.sin(t) * v + np.cos(t) * w], 1).astype(np.float32)
        away = c.to_local(to_dev([c.Cw + np.array([0.0, 100.0, 0.0])]))[0].cpu().numpy()
        # the pith on the far side from the camera: where it comes to a visible face everything on that face converges on one point, a fan. What the camera sees instead is the flank, with the charred brickwork that says charcoal. The form does not depend on the pith, so this does not move anything
        u = away[1:] / np.linalg.norm(away[1:])
        c.py, c.pz = float(1.1 * c.R * u[0]), float(1.1 * c.R * u[1])
        c.th0 = float(np.arctan2(away[2], away[1])) + np.pi  # the map's seam on the far side from the camera
    Cs = np.array([c.Cw for c in coals])
    log(f"heap: x {Cs[:, 0].min():.1f} .. {Cs[:, 0].max():.1f}, y {Cs[:, 1].min():.1f} .. {Cs[:, 1].max():.1f}, top {Cs[:, 2].max():.1f} cm; moved at the end {res['moved']:.4f}; {time.time() - t0:.1f} s")


def vertex_normals(P, F):
    a, b, c = P[F[:, 0]], P[F[:, 1]], P[F[:, 2]]
    fn = torch.linalg.cross(b - a, c - a)
    n = torch.zeros_like(P)
    for i in range(3):
        n.index_add_(0, F[:, i], fn)
    area = torch.zeros(P.shape[0], device=DEV)
    fa = fn.norm(dim=1) / 6.0
    for i in range(3):
        area.index_add_(0, F[:, i], fa)
    return n / (n.norm(dim=1, keepdim=True) + 1e-12), area


class Fire:
    """The heat solve over the heap. Elements are the vertices of coarse hulls."""

    def __init__(self, coals, K=48, log=print, params=None):
        t0 = time.time()
        self.log = log
        self.coals = coals
        Ps, Ns, As, Es, off = [], [], [], [], 0
        self.ranges = []
        out_ok = 0.0
        for c in coals:
            L, F = c.mesh(0.08, cracks=False, log=lambda *a: None)
            Pw = to_dev(c.to_world(L.cpu().numpy()))
            n, area = vertex_normals(Pw, F)
            out_ok += float((c.base(*c.to_local(Pw + 0.02 * n).T) > c.base(*c.to_local(Pw).T)).float().mean())
            e = torch.cat([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]], 0)
            e = torch.unique(torch.sort(e, dim=1)[0], dim=0) + off
            Ps.append(Pw), Ns.append(n), As.append(area), Es.append(e)
            self.ranges.append((off, off + len(Pw)))
            off += len(Pw)
        P, n, area, edges = torch.cat(Ps), torch.cat(Ns), torch.cat(As), torch.cat(Es)
        self.P, self.n = P, n
        log(f"elements {len(P)}, edges {len(edges)}, normals outward {out_ok / len(coals):.3f}, {time.time() - t0:.1f} s")
        # occupancy: tight round the heap, so that a ray that has left is done with
        h = 0.05
        Pn = P.cpu().numpy()
        lo, hi = Pn.min(0).astype(float) - 0.3, Pn.max(0).astype(float) + 0.3
        nx, ny, nz = ((hi - lo) / h).astype(int)
        fp_hit = os.path.join(D_OUT, f"hit_{hashlib.md5(Pn.tobytes()).hexdigest()[:12]}_{K}.npy")
        occ = torch.zeros((nz, ny, nx), dtype=torch.uint8, device=DEV)
        for c in coals if not os.path.exists(fp_hit) else []:
            ext = float(np.hypot(c.bb[0], c.bb[1] * 1.41))
            i0 = np.maximum(((c.Cw - ext - lo) / h).astype(int), 0)
            i1 = np.minimum(((c.Cw + ext - lo) / h).astype(int) + 1, (nx, ny, nz))
            zs, ys, xs = torch.meshgrid(torch.arange(i0[2], i1[2], device=DEV), torch.arange(i0[1], i1[1], device=DEV), torch.arange(i0[0], i1[0], device=DEV), indexing="ij")
            zs, ys, xs = zs.flatten(), ys.flatten(), xs.flatten()
            X = torch.stack([float(lo[0]) + (xs.float() + 0.5) * h, float(lo[1]) + (ys.float() + 0.5) * h, float(lo[2]) + (zs.float() + 0.5) * h], 1)
            Lc = c.to_local(X)
            m = c.base(Lc[:, 0], Lc[:, 1], Lc[:, 2]) < 0.0
            occ[zs[m], ys[m], xs[m]] = 1
        log(f"occupancy {nx} x {ny} x {nz}, filled {float((occ > 0).float().mean()):.3f}; {time.time() - t0:.1f} s")
        if os.path.exists(fp_hit):
            hit = torch.as_tensor(np.load(fp_hit))
        else:
            hit = trace(P, n, occ, tuple(lo), h, K=K, log=log)
            np.save(fp_hit, hit.numpy())
        uniq, inv = torch.unique(hit[hit >= 0], return_inverse=True)
        ui = uniq.numpy().astype(np.int64)
        vz, vy, vx = ui // (ny * nx), (ui // nx) % ny, ui % nx
        C = np.stack([lo[0] + (vx + 0.5) * h, lo[1] + (vy + 0.5) * h, lo[2] + (vz + 0.5) * h], 1)
        _, nn = cKDTree(P.cpu().numpy()).query(C, workers=-1)
        hit_e = hit.clone()
        hit_e[hit >= 0] = torch.as_tensor(nn, dtype=torch.int32)[inv]
        log(f"hits mapped {time.time() - t0:.1f} s")
        self.room = (hit == -1).float().mean(1).to(DEV)
        self.down = (hit == -2).float().mean(1).to(DEV)
        self.open = self.room + self.down  # how much of the outside it sees
        self.hit_e, self.area, self.edges = hit_e, area, edges
        self.state(params or {})

    def state(self, params):
        P = self.P
        N = len(P)
        # a ray that leaves on the way down has mostly gone out through the side of the domain, not into a bed of coals: T_bed is low here
        p = {**HEAT_DEFAULT, "T_bed": 600.0, "Q": 3.0, "h": 0.009, **params}
        self.params = p
        pn = noise(512, 512, 26.0, 26.0, SEED + 80) + 0.6 * noise(512, 512, 9.0, 9.0, SEED + 81)
        pn = pn / pn.std()
        g = torch.stack([P[:, 0] / 26.0 + 0.31 * P[:, 2] / 13.0, P[:, 2] / 13.0 + 0.27 * P[:, 1] / 13.0], -1).reshape(1, 1, -1, 2)
        pv = TF.grid_sample(pn[None, None], g, mode="bilinear", align_corners=True, padding_mode="reflection").reshape(-1)
        bias = torch.zeros(N, device=DEV)
        for c, (a, b) in zip(self.coals, self.ranges):
            bias[a:b] = c.bias
        top = float(torch.quantile(P[:: max(1, N // 100000), 2], 0.97))
        # burnt through where it sees little of the outside, and further down in any case: air comes in under a bed and the hot gas rises through it, so a flank that sees the room still goes from black at the top to red below. How far down: chosen, by eye against ref/charcoal
        below = sstep(top - p.get("d0", 0.3), top - p.get("d1", 3.5), P[:, 2])
        burn = (sstep(p.get("open1", 0.42), p.get("open0", 0.08), self.open) + p.get("depth", 0.9) * below + 0.2 * pv + bias).clamp(0.0, 1.0)
        film = 1.0 - burn
        # a bed draws its air up through the gaps, so the faces in them are not starved: nearly even, with a noise
        access = (p.get("access", 0.75) + 0.15 * pv + 0.6 * bias).clamp(0.2, 1.2)
        T0 = 640.0 + (p["T_start"] - 640.0) * sstep(0.08, 0.3, burn)
        self.burn = burn
        self.lift = (sstep(0.98, 0.72, self.open) + 0.28 * pv + 0.1).clamp(0.0, 1.0)
        # the gas rising through the heap has cooled at the top
        p = dict(p, T_gas=p["T_gas"] - 40.0 + 300.0 * sstep(top * 0.85, top * 0.25, P[:, 2]))
        self.H = Heat(P, self.n, self.area, self.edges, self.hit_e, access, film, p, log=self.log)
        self.H.T = T0
        self.H.Tf = T0 * 0.95
        self.H.J = self.H.eps * SIGMA * self.H.Tf**4

    def settle(self, seconds=8.0, dt=0.008):
        self.H.relax(seconds, dt, lambda t: 1.0, log=self.log, tag="settle")

    dT = None  # how far the temperature has come from where it settled: set during a take
    cam_loc = None  # where the camera is, once that is known
    puff = None  # what the skin has of the air that is passing: set during a take
    tau = 0.0  # how far through the take

    def begin_take(self, n, fps=25.0, params=None):
        """The camera stays and the fire goes on. Two things, both ESTIMATES of speed and size:
        the skin burns through a little further everywhere, which is sped up, a real bed takes minutes over this: this part only ever goes one way;
        and a train of slow puffs of air crosses the heap from left to right, in real time: each part of the glow rises as a puff comes and sinks after it, with the small lag of the skin's heat capacity. All of it goes one way across the frame, so nothing pulses in place; and no two places are in step, so the whole does not go up like a dimmer (a reviewer read the single pass as one)."""
        p = {"rise": 0.1, "gust": 0.5, "v": 8.0, "w": 2.6, "gap": 7.5, **(params or {})}
        P = self.P
        self.T_rest = self.H.T.clone()
        self.burn0 = self.burn.clone()
        pn = noise(512, 512, 14.0, 14.0, SEED + 82) + 0.6 * noise(512, 512, 5.0, 5.0, SEED + 83)
        pn = pn / pn.std()
        g = torch.stack([P[:, 0] / 26.0 + 0.31 * P[:, 2] / 13.0, P[:, 2] / 13.0 - 0.27 * P[:, 1] / 13.0], -1).reshape(1, 1, -1, 2)
        pv = TF.grid_sample(pn[None, None], g, mode="bilinear", align_corners=True, padding_mode="reflection").reshape(-1)
        # only where the edge of the glow is: what has burnt through already holds steady, or the whole bed goes up together like a dimmer
        self.rise = p["rise"] * (0.8 + 0.5 * pv).clamp(0.15, 1.6) * sstep(0.85, 0.45, self.burn0)
        a = np.radians(12.0)
        self.u = P[:, 0] * float(np.cos(a)) + P[:, 1] * float(np.sin(a)) + 1.8 * pv
        self.take_p, self.n_frames, self.frame_t, self.k = p, n, 1.0 / fps, 0
        self.u0 = AIM_X - p["v"] * (n / fps) * 0.5
        self.strength = (0.75 + 0.35 * pv).clamp(0.3, 1.3)
        # the puffs have been coming for a while when the shot begins: no start-up for the whole heap to rise through
        self.puff = torch.zeros_like(self.H.T)
        steps = int(round(1.5 / 0.008))
        for i in range(steps):
            if i % 4 == 0:
                self.H.irradiation()
            self.blow((i - steps) * 0.008)
        self.dT = self.H.T - self.T_rest

    def blow(self, t):
        m = self.air(t)
        self.puff += (m - 1.0 - self.puff) * 0.008 / PUFF_TAU
        self.H.step(0.008, m)

    def air(self, t):
        p = self.take_p
        d = self.u - self.u0 - p["v"] * t
        return 1.0 + p["gust"] * self.strength * sum(torch.exp(-(((d + i * p["gap"]) / p["w"]) ** 2)) for i in range(-3, 4))

    def advance(self):
        """On to the next frame."""
        H, p = self.H, self.take_p
        self.k += 1
        self.H.set_film((1.0 - (self.burn0 + self.rise * self.k / (self.n_frames - 1)).clamp(0.0, 1.0)))
        steps = int(round(self.frame_t / 0.008))
        for i in range(steps):
            if i % 4 == 0:
                H.irradiation()
            t = (self.k - 1 + i / steps) * self.frame_t
            self.blow(t)
        self.dT = H.T - self.T_rest
        self.tau = self.k / (self.n_frames - 1)


class Detail:
    """A coal's fine mesh with everything the shader needs."""

    def __init__(self, c, fire, a_b, dx, log=print):
        L, F = c.mesh(dx, log=log)
        self.P = c.to_world(L.cpu().numpy())
        self.F = F.cpu().numpy().astype(np.int32)
        x, y, z = L[:, 0], L[:, 1], L[:, 2]
        s, t, r = c.st(x, y, z)
        m = c.map
        f_ring, k_ring = ring_phase(r + 0.5 * c.tile.lumps(x, y, z, c.off), c.bounds)
        t2 = t + c.ring_off[k_ring]
        step = 2000000
        A, B, C = [], [], []
        for i in range(0, len(x), step):
            A.append(m.look(m.A, s[i : i + step], t[i : i + step]))
            B.append(m.look(m.B, s[i : i + step], t2[i : i + step]))
            C.append(m.look(m.B[:, :2], s[i : i + step], t[i : i + step]))
        A, B, C = torch.cat(A, 1), torch.cat(B, 1), torch.cat(C, 1)
        lab = m.look(m.B[:, -1:], s, t, mode="nearest")[0].long()
        Z = torch.cat([m.fine_net(s[i : i + step], t[i : i + step]) for i in range(0, len(x), step)], 1)
        a = c.endness(x, y, z)
        ends = torch.nonzero(a > 0.0)[:, 0]
        if len(ends):
            s2, t2 = c.st_end(y[ends], z[ends])
            ae = a[ends]
            for i in range(0, len(ends), step):
                e, se, te, w = ends[i : i + step], s2[i : i + step], t2[i : i + step], ae[i : i + step]
                A2 = m.look(m.A, se, te)
                A2[0] += END_NO_FINE
                A[:, e] += w * (A2 - A[:, e])
                B2 = m.look(m.B, se, te)
                B2[2:9] *= 0.6  # everything that runs along the map's long axis; grain and cloth most of all, or an end comes out as a sawn plank
                B2[2:4] *= 0.5
                B[:, e] += w * (B2 - B[:, e])
                C2 = B2[:2].clone()
                C2[0] = 0.5 + 0.35 * (C2[0] - 0.5)  # cell by cell the skin would flip in shingles
                C[:, e] += w * (C2 - C[:, e])
                Z[:, e] += w * (m.fine_net(se, te) - Z[:, e])
            m2 = a > 0.5
            if m2.any():
                lab[m2] = m.look(m.B[:, -1:], *c.st_end(y[m2], z[m2]), mode="nearest")[0].long() + 10000000
        self.lab = torch.unique(lab, return_inverse=True)[1]
        self.Ef = torch.min(A[0], A[1])
        self.Em = A[1]
        self.wc = torch.max(A[2].clamp(min=0.75 * dx), A[3].clamp(min=0.9 * dx))
        self.pol, self.str_f = C[0], C[1]  # these belong to the cracks
        self.grain, self.cloth, self.micro, self.plate, self.grit, self.fine, self.pits = B[2], B[3], B[4], B[5], B[6], B[7], B[8]
        self.craze, self.craze2, self.blot = Z[0], Z[1], Z[2]
        self.c_ash = c.ash
        self.ring = (1.0 - 0.8 * a) * c.ring_a[k_ring] * torch.exp(-f_ring / 0.07)
        self.dep = -c.base(x, y, z, fine=True) - A[6]
        a, b = a_b
        d, idx = cKDTree(fire.P[a:b].cpu().numpy()).query(self.P, k=4, workers=-1)
        w = 1.0 / (d + 0.06) ** 2
        w = w / w.sum(1, keepdims=True)
        self.idx = torch.as_tensor(idx + a, device=DEV, dtype=torch.long)
        self.w = to_dev(w)
        self.lookup = lambda f: (f[self.idx] * self.w).sum(1)

    def facing(self, fire):
        """The cosine between the surface and the way to the camera, per vertex, the normals smoothed over a few cells of the mesh. The camera does not move: once."""
        if fire.cam_loc is None:
            return torch.ones(len(self.P), device=DEV, dtype=torch.float32)
        P = to_dev(self.P)
        F = torch.as_tensor(self.F, device=DEV, dtype=torch.long)
        n, _ = vertex_normals(P, F)
        for _ in range(5):
            fm = n[F].sum(1)
            m = torch.zeros_like(n)
            for i in range(3):
                m.index_add_(0, F[:, i], fm)
            n = m / (m.norm(dim=1, keepdim=True) + 1e-12)
        v = fire.cam_loc - P
        return ((n * v).sum(1) / v.norm(dim=1)).clamp(0.0, 1.0)

    def shade(self, fire, emit_only=False):
        """What ref/charcoal shows (charbon, gorgeous): brightness falls off smoothly over a face, following the temperature; on top of that, fine cracks and rings are brighter than the surface and the big cracks are black. A first version let the skin flip cell by cell, which came out as camouflage. A crack's wall is bare char: it burns and loses little by radiation, so it glows also where the skin above it is cold. How far up that reaches: ESTIMATE."""
        H = fire.H
        p = H.p
        T, G = self.lookup(H.T), self.lookup(H.G)
        n = int(self.lab.max()) + 1
        cnt = torch.zeros(n, device=DEV).index_add_(0, self.lab, torch.ones_like(T))
        T = 0.2 * (torch.zeros(n, device=DEV).index_add_(0, self.lab, T) / cnt.clamp(min=1.0))[self.lab] + 0.8 * T
        burn_s = 1.0 - self.lookup(H.film)
        Tg = self.lookup(H.Tg)
        lift = self.lookup(fire.lift)
        dep, wc = self.dep, self.wc
        Ef = (self.Ef + 0.003 * self.micro).clamp(min=0.0)  # a crack's lip is torn, not drawn
        B = burn_s + 0.22 * (self.pol - 0.5) + 0.05 * self.plate + 0.012 * self.micro - CRACK_FRONT * (1.0 - torch.exp(-self.Ef / 0.1))
        skin = 1.0 - sstep(0.34, 0.66, B)
        wv = wc * (0.5 + 0.9 * self.str_f)
        cav = sstep(0.05, 0.75, self.str_f) * sstep(1.5 * wv, 0.3 * wv, Ef)
        top = 1.0 - cav
        f = skin * top
        # char is matte (ref/charcoal: rouge, glut_closeup). With no highlight to carry it, the surface shows as grain at the size of a pixel: porous, with the vessels darker
        alb0 = ((0.035 + 0.02 * (self.grain * 0.5 + 0.5).clamp(0, 1)) * (1.0 + 0.28 * self.fine.clamp(-2, 2) + 0.2 * self.micro.clamp(-2, 2)) * (1.0 - 0.55 * self.pits)).clamp(0.012, 0.12)
        # a thin ash: settles on what faces up, in patches. Mid grey: white reads as plaster
        lay = 0.9 * self.lookup(fire.n[:, 2]) + 0.55 * self.plate + 0.4 * self.grit + 0.15 * self.fine + 0.15 * self.micro + self.c_ash
        ash = sstep(0.7, 1.5, lay) * skin * top * (1.0 - 0.7 * self.pits)
        alb = alb0 * (1.0 - ash) + ((0.1 + 0.07 * sstep(-1.0, 1.5, self.plate)) * (1.0 + 0.2 * self.micro.clamp(-2, 2))) * ash
        alb = alb * (1.0 - 0.45 * torch.exp(-self.craze / 0.005) * sstep(-1.4, 0.3, self.grit))
        alb = alb * (1.0 - 0.6 * torch.exp(-Ef / (wc + 0.006)))  # soot in a crack: soft light from a room alone leaves a hairline on a matte surface barely visible
        # a little ash where the skin is burning away: a grey rim along the edge of the glow, and a few flecks on what has burnt through (ref/charcoal). Fixed from the first frame: in 1.4 s it does not go, the glow comes up under it. Amounts by eye; mid grey, not white, which has read as frost or plaster
        if not hasattr(self, "ash2"):
            q = 0.7 * self.plate + 0.5 * self.grit + 0.45 * self.micro + 0.9 * (self.pol - 0.5)
            up = self.lookup(fire.n[:, 2])
            rim = sstep(0.12, 0.34, B) * sstep(0.85, 0.55, B)
            self.exposed = sstep(0.03, 0.22, self.lookup(fire.open))  # what sees the air: the hot heart of the heap keeps its light
            # a face burnt through and in the air carries more of it: patches that stay on it say the thing is solid
            fleck = 0.6 * self.exposed
            self.ash2 = (rim * sstep(0.36, 0.86, q) + (1.0 - rim) * sstep(0.2, 0.5, B) * sstep(1.0 - fleck, 1.5 - fleck, q)) * sstep(-0.5, 0.2, up) * top * (1.0 - 0.7 * self.pits)
        alb = alb * (1.0 - self.ash2) + (0.14 + 0.09 * sstep(-1.0, 1.5, self.plate)) * (1.0 + 0.2 * self.micro.clamp(-2, 2)) * self.ash2
        ash = torch.max(ash, self.ash2)
        eps = 1.0 - alb
        C = p["k_ash"] / (p["film0"] + p["film1"] * f)
        Tf = T * 0.9
        for _ in range(5):
            g = C * (T - Tf) - eps * (SIGMA * Tf**4 - G) - p["h"] * (Tf - Tg)
            dg = -C - 4.0 * eps * SIGMA * Tf**3 - p["h"]
            Tf = (Tf - g / dg).clamp(300.0, 1800.0)
        reach = sstep(-0.1, 0.3, 1.25 * (lift + burn_s) - 0.25 + 0.14 * self.plate)
        # how far along its length a crack has caught. tau runs 0 .. 1 over a take: the contour of this noise moves, so a crack lights further along and what has lit stays lit
        along = sstep(-1.0, 1.1, 0.8 * self.plate + 0.6 * self.grit + 0.35 * fire.tau)
        dT = self.lookup(fire.dT) if fire.dT is not None else 0.0
        T_wall = (870.0 + 150.0 * burn_s + 75.0 * self.str_f**2 + 60.0 * along + 0.7 * dT) * reach * (0.82 + 0.18 * along) + 500.0 * (1.0 - reach)
        pl = (self.plate * 0.5 + 0.5).clamp(0.0, 1.0)
        # the lip of a glowing crack is warm too, a soft red that dies away in a fraction of a millimetre to a few: without it the crack is a drawn line, neon
        T_lip = (T_wall - 30.0 - 300.0 * (1.0 - torch.exp(-self.Ef / (0.018 + 0.05 * pl)))) * reach * sstep(0.1, 0.7, self.str_f)
        T_pre = 700.0 + 250.0 * sstep(0.3, 0.62, B) + 0.5 * dT  # visible from about 900 K: this is the fade from black to red
        Tf = torch.max(torch.max(Tf, T_lip), T_pre * skin + Tf * (1.0 - skin))
        T_v = Tf * top + torch.max(T_wall, T) * (1.0 - top)
        alight = 1.0 - skin
        # burning is not even at this scale, and it follows the fibres. Isotropic noise here comes out as marbling: the glow's curve is steep, 15 K is a visible step
        big = torch.exp(-self.Em / 0.02)
        burnt = alight * sstep(0.6, 0.9, B)
        fibres = 1.0 - 0.85 * burnt  # streaks and an even orange read as salmon: a burnt-through face is broken by the fine network instead, and its heat is not even (ref/charcoal/charbon.jpg)
        T_v = T_v + alight * (2.5 * self.grit + fibres * (14.0 * self.cloth + 15.0 * self.grain) + 7.0 * self.micro + 2.0 * self.plate - 30.0 * sstep(1.6, 2.4, self.micro) + 12.0 * self.ring + 55.0 * torch.exp(-self.Ef / 0.012) * (1.0 - big))
        # broken, in two sizes, and only on a face already hot: even lines come out as a net, and on a dull face as a circuit board
        net = 0.3 * CRAZE_T * torch.exp(-self.craze / 0.007) + 0.14 * CRAZE_T * torch.exp(-self.craze2 / 0.005)
        T_v = T_v + burnt * (3.0 * self.grit + 4.0 * self.micro + sstep(860.0, 990.0, T_v) * sstep(-1.4, 0.3, self.grit) * sstep(-0.8, 0.5, self.blot) * net + 28.0 * self.blot + 24.0 * (self.pol - 0.5) + 18.0 * self.plate + 30.0 * torch.exp(-Ef / 0.05) - SURF_COOL * self.exposed * top)
        if not hasattr(self, "mu"):
            self.mu = self.facing(fire)
        T_v = T_v - LIMB_K * (1.0 - self.mu) ** 2 * alight * top
        if fire.puff is not None:
            T_v = T_v + PUFF_K * self.lookup(fire.puff) * torch.max(alight, 1.0 - top) * (1.0 - 0.3 * burnt)
        # what has long been burnt through hardly changes when the air passes: the change belongs at the edge of the glow
        T_v = T_v - 0.4 * sstep(0.6, 0.9, burn_s) * dT
        hot = alight * sstep(0.45, 0.75, B)
        T_v = T_v + CRACK_HOT * (0.35 + 0.65 * self.exposed) * hot * torch.exp(-Ef / (0.7 * wc + 0.003)) - (1.0 - hot) * (70.0 * alight * cav * big + 90.0 * sstep(0.03, 0.14, dep) * sstep(1.2 * wc, 0.4 * wc, Ef))
        T_v = T_v - 130.0 * self.ash2  # the outer face of ash is cooler than the char under it
        emit = radiance_t(T_v.clamp(min=450.0)) * eps[:, None]
        if emit_only:
            return emit
        col = torch.stack([alb * 1.02, alb, alb * 0.98], -1)
        # one cell in thirty or so has split freshly and keeps a little dull shine; that is the only shine there is
        fresh = sstep(0.955, 0.975, self.pol)
        rough = ((0.96 - 0.1 * fresh) * skin + 0.92 * (1.0 - skin)) * (1.0 - ash) + ash
        spec = ((0.06 + 0.08 * fresh) * skin + 0.06 * (1.0 - skin)) * (1.0 - ash) + 0.03 * ash
        return col.cpu().numpy().astype(np.float32), emit.cpu().numpy().astype(np.float32), rough.clamp(0.08, 1.0).cpu().numpy().astype(np.float32), spec.cpu().numpy().astype(np.float32)


def view_vector():
    a, e = np.radians(AZ), np.radians(EL)
    return np.array([np.sin(a) * np.cos(e), -np.cos(a) * np.cos(e), np.sin(e)])


def camera_for(P):
    """Aimed at the heap: the median of its upper edge in the frame lands on CREST_Y. Focus on the nearest thing at FOCUS_AT."""
    view = view_vector()
    Pv = P[:: max(1, len(P) // 300000)]
    tgt = np.array([AIM_X, float(np.median(Pv[:, 1])), float(Pv[:, 2].max())])
    for _ in range(6):
        cam = frame_camera(tgt, view, W_FRAME, DIST)
        x, y = top_arc(cam, Pv)
        _, _, _, up = cam_basis(cam)
        tgt = tgt - up * (float(np.median(y)) - CREST_Y) * W_FRAME * 9.0 / 16.0
    cam = frame_camera(tgt, view, W_FRAME, DIST)
    xs, ys, w = project(cam, Pv)
    # the surface that shows there is the nearest one: the points behind it are hidden
    near = (xs - FOCUS_AT[0]) ** 2 + ((ys - FOCUS_AT[1]) * 9 / 16) ** 2 < 0.02**2
    focus = Pv[near][np.argmin(w[near])]
    cam = frame_camera(tgt, view, W_FRAME, DIST, aperture_mm=APERTURE_MM, focus_point=focus)
    x, y = top_arc(cam, Pv)
    print(f"crest in frame: y {y.min():.3f} .. {y.max():.3f}, median {np.median(y):.3f}; focus {focus.round(2).tolist()}", flush=True)
    return cam, float(np.median(y)), focus


def scene_for(cam, meshes):
    pm = np.array(cam["target"])
    gray = 0.0068
    # a soft room overhead for the form of the black, and a larger, dimmer source overhead and behind that lifts its tops from the background
    lights = [
        {"type": "gradient", "name": "room", "loc": (pm + np.array([-24.0, -20.0, 50.0])).tolist(), "target": pm.tolist(), "size": [90, 90], "sigma": [32, 32], "L": 1.4, "rgb": [1.0, 0.98, 0.96]},
        {"type": "gradient", "name": "back", "loc": (pm + np.array([8.0, 34.0, 40.0])).tolist(), "target": pm.tolist(), "size": [80, 36], "sigma": [26, 11], "L": 1.0, "rgb": [0.98, 0.98, 1.0]},
    ]
    return {
        "camera": cam,
        "meshes": meshes,
        "lights": lights,
        "world": [0.0, 0.0, 0.0],
        "sky": {"top": [gray, gray, gray * 1.03], "glow": [0.0152, 0.0148, 0.0148], "h": 0.6, "mottle": 0.12, "x0": 0.55, "seed": 69},
        "bounces": 8,
        "diffuse_bounces": 4,
        "glossy_bounces": 3,
        "transmission_bounces": 2,
        "clamp_indirect": 30.0,
        "denoise": False,
    }


DEVELOP = {"exposure": 0.0, "contrast": 1.25, "saturation": 1.0, "black": 0.0, "grain": 1.0, "sharpen": 0.22, "halation": 0.12, "glare": 0.006, "vignette": 0.2}


def build(log=print):
    os.makedirs(D_OUT, exist_ok=True)
    maps = [Map(k, log=log) for k in range(N_MAPS)]
    tile = Tile()
    coals = [Coal(i, maps, tile, SEED + 1000 + 17 * i) for i in range(N_COALS)]
    stack(coals, log=log)
    for i, b in LEAN.items():
        coals[i].bias = b
    return coals


def views(spec):
    """Framings to choose from, cheaply: one coarse build of the whole heap, many cameras. spec: list of dicts with EL, AZ, AIM_X, CREST_Y, W_FRAME, DIST, FOCUS_AT, APERTURE_MM."""
    coals = build()
    fire = Fire(coals)
    fire.settle()
    meshes = []
    for c, ab in zip(coals, fire.ranges):
        D = Detail(c, fire, ab, 0.03, log=lambda *a: None)
        col, emit, rough, spc = D.shade(fire)
        fp = os.path.join(D_OUT, f"coal{c.i:02d}.views.npz")
        np.savez(fp, V=D.P, F=D.F, col=col, emit=emit, rough=rough, spec=spc)
        meshes.append({"name": f"coal{c.i:02d}", "npz": fp, "shader_py": os.path.join(HERE, "s69_shader.py"), "params": {}, "smooth": True})
        del D
    P = fire.P.cpu().numpy()
    del fire, coals
    torch.cuda.empty_cache()
    base = {k: globals()[k] for k in ("EL", "AZ", "AIM_X", "CREST_Y", "W_FRAME", "DIST", "FOCUS_AT", "APERTURE_MM")}
    out = []
    for i, v in enumerate(spec):
        globals().update({**base, **v})
        cam, _, _ = camera_for(P)
        cfg = scene_for(cam, meshes)
        cfg.update(res=[640, 360], spp=48, seed=1)
        cfg["camera"] = dict(cfg["camera"])
        kit._dress(cfg, NAME, D_OUT, DEVELOP)
        L = np.load(kit._render_local(cfg, D_OUT, "view")).astype(np.float32)
        u8 = (np.clip(dev(L, **{**DEVELOP, "seed": 1}), 0, 1) * 255 + 0.5).astype(np.uint8)[..., ::-1].copy()
        cv2.putText(u8, " ".join(f"{k}{v[k]}" for k in v), (6, 16), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (220, 220, 220), 1, cv2.LINE_AA)
        out.append(u8)
    for m in meshes:
        os.remove(m["npz"])
    cols = 4
    rows = [np.hstack(out[i : i + cols] + [np.zeros_like(out[0])] * (cols - len(out[i : i + cols]))) for i in range(0, len(out), cols)]
    cv2.imwrite(os.path.join(D_OUT, "views.jpg"), np.vstack(rows), [cv2.IMWRITE_JPEG_QUALITY, 90])


def still(q, tag, params=None):
    res = {"preview": (960, 540), "mid": (1280, 720), "final": (2560, 1440)}[q]
    spp = {"preview": 64, "mid": 128, "final": 384}[q]
    base = {"preview": 0.024, "mid": 0.014, "final": 0.009}[q]
    coals = build()
    fire = Fire(coals, params=params)
    fire.settle((params or {}).get("settle", 8.0))
    print(f"open p10/50/90: {[round(float(x), 2) for x in torch.quantile(fire.open[::7], torch.tensor([0.1, 0.5, 0.9], device=DEV)).cpu().numpy()]}, burn mean {float(fire.burn.mean()):.2f}", flush=True)
    cam, focus = dict(CAMERA), np.array(FOCUS)
    loc = np.array(cam["loc"])
    fire.cam_loc = to_dev(loc)
    fwd = np.array(cam["target"]) - loc
    fwd = fwd / np.linalg.norm(fwd)
    d_focus = float((focus - loc) @ fwd)
    meshes = []
    t0 = time.time()
    tot = 0
    for c, ab in zip(coals, fire.ranges):
        xs, ys, _ = project(cam, c.Cw[None])
        reach = (c.L + c.R) / W_FRAME
        inside = -reach < xs[0] < 1.0 + reach and -2 * reach < ys[0] < 1.0 + 2 * reach
        blur = APERTURE_MM / 10.0 / DIST * abs(float((c.Cw - loc) @ fwd) - d_focus)
        dx = float(np.clip(base * (1.0 + max(0.0, blur - 0.04) / 0.05), base, 0.05)) if inside else 0.06
        D = Detail(c, fire, ab, dx, log=lambda *a: None)
        col, emit, rough, spc = D.shade(fire)
        fp = os.path.join(D_OUT, f"coal{c.i:02d}.{tag}.npz")
        np.savez(fp, V=D.P, F=D.F, col=col, emit=emit, rough=rough, spec=spc)
        tot += len(D.F)
        meshes.append({"name": f"coal{c.i:02d}", "npz": fp, "shader_py": os.path.join(HERE, "s69_shader.py"), "params": {}, "smooth": True})
        del D
    print(f"meshes: {tot / 1e6:.1f} M tris, {time.time() - t0:.1f} s", flush=True)
    # leave the card to Blender
    del fire, coals
    torch.cuda.empty_cache()
    cfg = scene_for(cam, meshes)
    cfg.update(res=list(res), spp=spp, seed=1)
    cfg["camera"] = dict(cfg["camera"])
    kit._dress(cfg, NAME, D_OUT, DEVELOP)
    t0 = time.time()
    linear = kit._render_local(cfg, D_OUT, tag)
    print(f"render {time.time() - t0:.1f} s")
    L = np.load(linear).astype(np.float32)
    im = dev(L, **{**DEVELOP, "seed": 1})
    cv2.imwrite(os.path.join(D_OUT, f"{tag}.jpg"), (np.clip(im, 0, 1) * 255 + 0.5).astype(np.uint8)[..., ::-1], [cv2.IMWRITE_JPEG_QUALITY, 95])
    json.dump(DEVELOP, open(os.path.join(D_OUT, f"{tag}.develop.json"), "w"))
    for m in meshes:
        os.remove(m["npz"])
    print(os.path.join(D_OUT, f"{tag}.jpg"), flush=True)


TAKE = 36  # frames


# --- sparks: small hot bodies in the scene, so that the lens, its nine blades and whatever stands in front of them are real
# Real sparks rise at about 30-100 cm/s (hot-air convection: an estimate, not measured). These are slowed about 10-30 times, like the rest of a macro in slow motion, so that they float. Sizes and temperatures are by eye, within what embers are, not measured.
# at: where it is on frame 0, fractions of the frame. dz: its depth from the plane of focus there, + is further; rising brings it nearer, since the camera looks down. T: at the start and after the take. rise, side: cm/s. curve: amplitude in cm, period in s, phase in turns.
# Planck is steep: at 1380 K R is about 170. Out of focus at that, it is a solid lamp, a small moon. So what is out of focus stays under about 1200 K, and dimmer than the coals.
SPARKS = [
    {"at": (0.712, 0.452), "dz": 1.7, "r": 0.018, "T": (1270.0, 1175.0), "rise": 3.2, "side": 0.5, "curve": (0.32, 2.6, 0.1)},  # goes through the plane of focus: the one to follow
    {"at": (0.165, 0.72), "dz": 8.0, "r": 0.016, "T": (1190.0, 1150.0), "rise": 2.4, "side": -0.25, "curve": (0.45, 3.4, 0.55)},  # behind the coals at first: it comes up from behind them part way through, soft and dim
]
SPARK_SLOWING = 2.5  # s: drag and the cooling plume take the climb down with this time constant
SPARK_SHUTTER = 0.5  # of a frame: the take itself has no motion blur, so the spark is drawn as what the open shutter sees, a capsule
SPARK_FLICKER = 18.0, 0.9  # K, s: a burning grain's temperature wanders slowly, never from frame to frame
SPARK_RINGS, SPARK_SEGS = 10, 16
CAPTION_BOX = 0.36, 0.64, 0.31, 0.43  # x0, x1, y0, y1 of the frame the sparks stay out of: film.py's caption, with room


def spark_unit():
    """A unit sphere with its poles on z: vertices, faces."""
    th = np.linspace(0.0, np.pi, SPARK_RINGS + 1)[1:-1]
    ph = np.linspace(0.0, 2 * np.pi, SPARK_SEGS, endpoint=False)
    ring = np.stack([np.outer(np.sin(th), np.cos(ph)), np.outer(np.sin(th), np.sin(ph)), np.outer(np.cos(th), np.ones_like(ph))], -1).reshape(-1, 3)
    V = np.vstack([[[0.0, 0.0, 1.0]], ring, [[0.0, 0.0, -1.0]]])
    at = lambda i, j: 1 + i * SPARK_SEGS + j % SPARK_SEGS
    F = [(0, at(0, j), at(0, j + 1)) for j in range(SPARK_SEGS)]
    for i in range(SPARK_RINGS - 2):
        for j in range(SPARK_SEGS):
            F += [(at(i, j), at(i + 1, j), at(i + 1, j + 1)), (at(i, j), at(i + 1, j + 1), at(i, j + 1))]
    last = len(V) - 1
    F += [(last, at(SPARK_RINGS - 2, j + 1), at(SPARK_RINGS - 2, j)) for j in range(SPARK_SEGS)]
    return V, np.array(F, np.int32)


def spark_path(sp, cam, t):
    loc = np.array(cam["loc"], float)
    fwd, right, up = (lambda b: (b[1], b[2], b[3]))(cam_basis(cam))
    fpx = cam["lens_mm"] / 36.0  # focal length in sensor widths
    d = cam["focus_distance"] + sp["dz"]
    p0 = loc + d * fwd + (sp["at"][0] - 0.5) * d / fpx * right - (sp["at"][1] - 0.5) * (9.0 / 16.0) * d / fpx * up
    a, T, phase = sp["curve"][0], sp["curve"][1], sp["curve"][2] * 2 * np.pi
    climb = sp["rise"] * SPARK_SLOWING * (1.0 - np.exp(-t / SPARK_SLOWING))
    side = sp["side"] * t + a * (np.sin(2 * np.pi * t / T + phase) - np.sin(phase))
    return p0 + np.array([0.0, 0.0, 1.0]) * climb + right * side


def spark_pose(sp, cam, k, n, V, fps=25.0):
    """What the shutter sees on frame k: the vertices of a capsule along the path, and its radiance, thinned as the light spreads over the capsule's length so that the spark's energy stays what it is."""
    a, b = spark_path(sp, cam, k / fps), spark_path(sp, cam, (k + SPARK_SHUTTER) / fps)
    L = float(np.linalg.norm(b - a))
    z = (b - a) / L
    x = np.cross(z, [0.0, 1.0, 0.0])
    x /= np.linalg.norm(x)
    y = np.cross(z, x)
    P = (a + b) / 2 + sp["r"] * (V[:, :1] * x + V[:, 1:2] * y + V[:, 2:] * z) + np.sign(V[:, 2:]) * (L / 2) * z
    t = (k + SPARK_SHUTTER / 2) / fps
    T = sp["T"][0] + (sp["T"][1] - sp["T"][0]) * t / ((n - 1) / fps) + SPARK_FLICKER[0] * np.sin(2 * np.pi * t / SPARK_FLICKER[1] + 7.0 * sp["curve"][2])
    area = np.pi * sp["r"] ** 2
    return P.astype(np.float32), radiance(np.array([T]))[0] * area / (2 * sp["r"] * L + area), T


def spark_check(cam, n, fps=25.0):
    x0, x1, y0, y1 = CAPTION_BOX
    for i, sp in enumerate(SPARKS):
        q = np.array([spark_path(sp, cam, k / fps) for k in range(n)])
        xs, ys, _ = project(cam, q)
        if ((xs > x0) & (xs < x1) & (ys > y0) & (ys < y1)).any():
            raise SystemExit(f"spark {i} crosses the caption")
        print(f"spark {i}: x {xs[0]:.3f}->{xs[-1]:.3f}, y {ys[0]:.3f}->{ys[-1]:.3f}", flush=True)


def take_dir(q):
    return os.path.join(OUT, f"{NAME}_move_{q}")


def take_prep(q, params=None):
    """The solve and the stacks of glow: needs the GPU's solver slot. take_render then needs only Blender, and the stacks stay on disk for a second try at the render. The mesh is what it is on the first frame: only the glow changes, and over 1.4 s the ash on what starts to glow does not need to go."""
    res, spp, base, frames = {"preview": ((960, 540), 96, 0.024, [0, 12, 24, 35]), "key": ((1920, 1080), 384, 0.011, [0, 12, 24, 35]), "final": ((1920, 1080), 768, 0.011, list(range(TAKE)))}[q]
    coals = build()
    fire = Fire(coals, params=params)
    fire.settle((params or {}).get("settle", 8.0))
    fire.begin_take(TAKE, params=params)
    cam, focus = dict(CAMERA), np.array(FOCUS)
    loc = np.array(cam["loc"])
    fire.cam_loc = to_dev(loc)
    fwd = np.array(cam["target"]) - loc
    fwd = fwd / np.linalg.norm(fwd)
    d_focus = float((focus - loc) @ fwd)
    d = os.path.join(D_OUT, f"stack_{q}")
    os.makedirs(d, exist_ok=True)
    t0 = time.time()
    Ds, meshes, stacks, tot = [], [], {}, 0
    for c, ab in zip(coals, fire.ranges):
        xs, ys, _ = project(cam, c.Cw[None])
        reach = (c.L + c.R) / W_FRAME
        inside = -reach < xs[0] < 1.0 + reach and -2 * reach < ys[0] < 1.0 + 2 * reach
        blur = APERTURE_MM / 10.0 / DIST * abs(float((c.Cw - loc) @ fwd) - d_focus)
        dx = float(np.clip(base * (1.0 + max(0.0, blur - 0.04) / 0.05), base, 0.05)) if inside else 0.06
        D = Detail(c, fire, ab, dx, log=lambda *a: None)
        col, emit, rough, spc = D.shade(fire)
        fp = os.path.join(d, f"coal{c.i:02d}.npz")
        np.savez(fp, V=D.P, F=D.F, col=col, emit=emit, rough=rough, spec=spc)
        tot += len(D.F)
        name = f"coal{c.i:02d}"
        meshes.append({"name": name, "npz": fp, "shader_py": os.path.join(HERE, "s69_shader.py"), "params": {}, "smooth": True})
        D.P, D.F = None, None
        Ds.append(D)
        stacks[name] = os.path.join(d, f"{name}.emit.npy")
    print(f"meshes: {tot / 1e6:.1f} M tris, {time.time() - t0:.1f} s", flush=True)
    mm = {n: np.lib.format.open_memmap(fp, mode="w+", dtype=np.float16, shape=(len(frames), len(D.idx), 3)) for (n, fp), D in zip(stacks.items(), Ds)}
    t0 = time.time()
    pct = torch.tensor([0.02, 0.5, 0.98], device=DEV)
    for k in range(TAKE):
        if k > 0:
            fire.advance()
        if k in frames:
            j = frames.index(k)
            for (n, _), D in zip(stacks.items(), Ds):
                mm[n][j] = D.shade(fire, emit_only=True).half().cpu().numpy()
            print(f"frame {k}: dT {[round(float(x)) for x in torch.quantile(fire.dT[::9], pct).cpu().numpy()]}, {time.time() - t0:.1f} s", flush=True)
    for m in mm.values():
        m.flush()
    del mm, Ds, fire, coals
    spark_check(cam, TAKE)
    Vu, Fu = spark_unit()
    names = [f"spark{i}" for i in range(len(SPARKS))]
    move = np.lib.format.open_memmap(os.path.join(d, "sparks.vertices.npy"), mode="w+", dtype=np.float32, shape=(len(frames), len(Vu) * len(SPARKS), 3))
    for i, (sp, name) in enumerate(zip(SPARKS, names)):
        glow = np.lib.format.open_memmap(os.path.join(d, f"{name}.emit.npy"), mode="w+", dtype=np.float16, shape=(len(frames), len(Vu), 3))
        for j, k in enumerate(frames):
            P, rad, _ = spark_pose(sp, cam, k, TAKE, Vu)
            move[j, i * len(Vu) : (i + 1) * len(Vu)] = P
            glow[j] = rad
        fp = os.path.join(d, f"{name}.npz")
        np.savez(fp, V=np.array(move[0, i * len(Vu) : (i + 1) * len(Vu)]), F=Fu, col=np.zeros((len(Vu), 3), np.float32), emit=np.array(glow[0], np.float32), rough=np.full(len(Vu), 0.6, np.float32), spec=np.zeros(len(Vu), np.float32))
        glow.flush()
        meshes.append({"name": name, "npz": fp, "shader_py": os.path.join(HERE, "s69_shader.py"), "params": {}, "smooth": True})
        stacks[name] = os.path.join(d, f"{name}.emit.npy")
    move.flush()
    del move
    torch.cuda.empty_cache()
    cfg = scene_for(cam, meshes)
    cfg.update(res=list(res), spp=spp, seed=1)
    cfg["camera"] = dict(cfg["camera"])
    kit._dress(cfg, NAME, D_OUT, DEVELOP)
    f = {k: cfg["camera"][k] for k in ("loc", "target", "lens_mm", "focus_distance") if k in cfg["camera"]}
    cfg.update(frames=[f] * len(frames), shutter=0, fresh=True, emit_stack=stacks, deform={"npy": os.path.join(d, "sparks.vertices.npy"), "vertex": names})
    json.dump(cfg, open(os.path.join(d, "cfg.json"), "w"), indent=1)
    print("prepared", d, flush=True)


def take_render(q):
    d, out = os.path.join(D_OUT, f"stack_{q}"), take_dir(q)
    cfg = json.load(open(os.path.join(d, "cfg.json")))
    os.makedirs(out, exist_ok=True)
    t0 = time.time()
    kit._render_local(cfg, out, "take")
    json.dump(DEVELOP, open(os.path.join(out, "develop.json"), "w"))
    print(f"rendered {len(cfg['frames'])} frames in {time.time() - t0:.1f} s", flush=True)
    fs = sorted(x for x in os.listdir(out) if x.startswith("take.linear_") and x.endswith(".npy"))
    ims = [dev(np.load(os.path.join(out, x)).astype(np.float32), **{**DEVELOP, "seed": 1}) for x in (fs[0], fs[len(fs) // 2], fs[-1])]
    cv2.imwrite(os.path.join(out, "ends.jpg"), (np.clip(np.vstack([cv2.resize(i, (960, 540), interpolation=cv2.INTER_AREA) for i in ims]), 0, 1) * 255 + 0.5).astype(np.uint8)[..., ::-1], [cv2.IMWRITE_JPEG_QUALITY, 92])


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "still"
    if cmd == "take_prep":
        take_prep(sys.argv[2], json.loads(sys.argv[3]) if len(sys.argv) > 3 and sys.argv[3] else None)
    if cmd == "take_render":
        take_render(sys.argv[2])
    if cmd == "views":
        views(json.loads(sys.argv[2]))
    if cmd == "still":
        pr = json.loads(sys.argv[4]) if len(sys.argv) > 4 and sys.argv[4] else None
        still(sys.argv[2] if len(sys.argv) > 2 else "preview", sys.argv[3] if len(sys.argv) > 3 else "h1", pr)
