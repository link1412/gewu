"""Shot 42: the door and the camera, shared by the plate (s42_yaohuo.py, Blender) and the fire (s42_fire.py, torch). Units cm. Scales are estimates."""

import numpy as np

R = 62.0  # radius of the arch
ZC = -R  # its centre: the crown of the front lip is at z = 0
THICK = 23.0  # depth of the arch, one brick's length
CEIL = 16.0  # the kiln's roof inside, above the crown
BACK = 56.0  # the back of the firebox
W = 100.0  # width of the frame at the target
DIST = 190.0
EL = np.radians(-10.0)  # the camera is low and looks up, so the underside of the arch shows
APEX = 0.50  # where the crown sits in the frame, from the top
VIEW = np.array([0.0, -np.cos(EL), np.sin(EL)])
TARGET = np.array([0.0, 0.0, -(0.5 - APEX) * W * 9.0 / 16.0])
LOC = TARGET + VIEW * DIST


def axes():
    back = VIEW / np.linalg.norm(VIEW)
    right = np.cross([0.0, 0.0, 1.0], back)
    right /= np.linalg.norm(right)
    up = np.cross(back, right)
    return right, up, back


# stand-in emitters that stand for the flames when lighting the masonry: one Blender pass each; each frame weighs them by the flame's power near them
LIGHTS = [(-24.0, -9.0, -16.0), (0.0, -9.0, -22.0), (24.0, -9.0, -16.0), (-13.0, -9.0, 3.0), (13.0, -9.0, 3.0), (-30.0, 10.0, -14.0), (0.0, 10.0, -9.0), (30.0, 10.0, -14.0)]
