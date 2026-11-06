"""The crop's reflection map: for rows and columns of the compared crop (240 x 220 px of the 1920 film) on the
card's piece, the direction a mirror there reflects the camera's ray to: elevation, azimuth (0 = toward the camera,
+ = the image's right). The lights of card.py RIG are placed by it (docs/materials/gilt_copper.md).

    python3 -I materials/gilt_copper/refmap.py out/materials/gilt_copper/g1      # a built card directory
"""
import json
import math
import os
import sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import card
d = sys.argv[1]
info = json.load(open(os.path.join(d, "build.json")))
eye, tgt = np.array(info["eye"]), np.array(card.TARGET)
fwd = (tgt - eye) / np.linalg.norm(tgt - eye)
right = np.cross(fwd, [0, 0, 1.0]); right /= np.linalg.norm(right)
up = np.cross(right, fwd)
t = math.tan(math.radians(info["fov_deg"]) / 2)
r0, c0 = card.card_dome_box(d, (240, 220))
C = np.array([0, 0, card.DOME_H - card.DOME_R])
for row in range(0, 220, 20):
    out = []
    for col in (0, 60, 120, 180, 239):
        y = r0 + row + 0.5; x = c0 + col + 0.5
        u = (x - 960) / 540 * t; v = -(y - 540) / 540 * t
        dvec = fwd + u * right + v * up; dvec /= np.linalg.norm(dvec)
        Sx = np.array([1 / card.DOME_SX, 1, 1])
        oc = (eye - C) * Sx; dd = dvec * Sx
        A = dd @ dd; b = oc @ dd; cc = oc @ oc - card.DOME_R ** 2
        disc = b * b - A * cc
        if disc < 0: out.append("miss"); continue
        s = (-b - math.sqrt(disc)) / A
        p = eye + s * dvec; n = (p - C) * Sx * Sx; n /= np.linalg.norm(n)
        r = dvec - 2 * (dvec @ n) * n
        el = math.degrees(math.asin(r[2])); az = math.degrees(math.atan2(r[0], -r[1]))   # az 0 = toward the camera (-y)
        pol = math.degrees(math.acos(n[2]))
        out.append(f"{el:3.0f} {az:4.0f}")
    print(row, " | ".join(out))
