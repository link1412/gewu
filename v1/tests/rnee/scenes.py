"""Scenes that check the refracted light connection (RNEE) against brute force.

Two glazes, each rendered with "refractivenee" on and off in the integrator; the material
is the same either way, so off is plain path tracing of the same scene:
- slab: a flat glaze 1.5 mm thick over a dark body, three air cracks (thin dielectrics);
- cylinder: a glaze 1 mm thick on a 5 mm radius (triangle meshes with vertex normals,
  closed by annuli), one crack, light from above-behind and from the side.

    python3 -I tests/rnee/scenes.py slab ref1:240:160:4096:1:false on1:240:160:256:1:true ...

Each NAME:W:H:SPP:SEED:RNEE writes NAME.pbrt (rendering writes NAME.pfm) in the working
directory. docs/rnee.md has the procedure and the results.
"""

import sys

import numpy as np

HEAD = '''Film "rgb" "integer xresolution" {w} "integer yresolution" {h} "string filename" "{name}.pfm"
Sampler "zsobol" "integer pixelsamples" {spp} "integer seed" {seed}
Integrator "volpath" "integer maxdepth" 64 "bool refractivenee" {rnee}
'''
SOFTBOX = '''AttributeBegin
  AreaLightSource "diffuse" "blackbody L" 5500 "float scale" 40
  Shape "trianglemesh" "integer indices" [0 1 2 0 2 3]
    "point3 P" [-150 250 400  150 250 400  150 50 450  -150 50 450]
AttributeEnd
LightSource "infinite" "blackbody L" 6500 "float scale" 0.02
MakeNamedMedium "glaze" "string type" "homogeneous"
  "spectrum sigma_a" [400 0.02 500 0.03 600 0.08 700 0.15]
  "spectrum sigma_s" [400 0.55 500 0.5 600 0.45 700 0.42]
  "float g" 0.7
'''
GLAZE = '''  Material "dielectric" "float eta" 1.5 "float roughness" 0.02 "bool refractivenee" true
'''
BODY = '''  Material "diffuse" "spectrum reflectance" [400 0.05 550 0.06 700 0.08]
'''
CRACK = '''  MediumInterface "glaze" "glaze"
  Material "thindielectric" "float eta" 0.6667
'''


def quad(P):
    return ('  Shape "trianglemesh" "integer indices" [0 1 2 0 2 3]\n    "point3 P" [' +
            ' '.join(f'{v:g}' for p in P for v in p) + ']\n')


def mesh(P, idx, N=None):
    s = '  Shape "trianglemesh" "integer indices" [' + ' '.join(map(str, idx)) + ']\n'
    s += '    "point3 P" [' + ' '.join(f'{v:.6f}' for p in P for v in p) + ']\n'
    if N is not None:
        s += '    "normal N" [' + ' '.join(f'{v:.6f}' for n in N for v in n) + ']\n'
    return s


def slab():
    s = 'LookAt 0 -90 70   0 0 0.75   0 0 1\nCamera "perspective" "float fov" 22\n'
    return s, ('WorldBegin\n' + SOFTBOX +
               'AttributeBegin\n  MediumInterface "glaze" ""\n' + GLAZE +
               quad([(-200, -200, 1.5), (200, -200, 1.5), (200, 200, 1.5), (-200, 200, 1.5)]) +
               'AttributeEnd\nAttributeBegin\n  MediumInterface "" "glaze"\n' + BODY +
               quad([(-200, -200, 0), (200, -200, 0), (200, 200, 0), (-200, 200, 0)]) +
               'AttributeEnd\nAttributeBegin\n' + CRACK +
               quad([(-14, -8, 0.01), (-14, 8, 0.01), (-14, 8, 1.49), (-14, -8, 1.49)]) +
               quad([(0, -8, 0.01), (0, 8, 0.01), (0.86, 8, 1.49), (0.86, -8, 1.49)]) +
               quad([(12, -8, 0.01), (12, 8, 0.01), (13.77, 8, 1.49), (13.77, -8, 1.49)]) +
               'AttributeEnd\n')


def cylinder(R=5.0, RB=4.0, H=8.0, N=256):
    ph = np.linspace(0, 2 * np.pi, N, endpoint=False)
    ring = lambda r, z: [(r * np.cos(p), r * np.sin(p), z) for p in ph]

    def side(r):
        P = ring(r, -H) + ring(r, H)
        Nn = [(np.cos(p), np.sin(p), 0) for p in ph] * 2
        idx = []
        for i in range(N):
            a, b, c, d = i, (i + 1) % N, N + (i + 1) % N, N + i
            idx += [a, b, c, a, c, d]
        return mesh(P, idx, Nn)

    def annulus(z, up):          # pbrt's triangle normal is (p0 - p2) x (p1 - p2)
        idx = []
        for i in range(N):
            a, b, c, d = i, (i + 1) % N, N + (i + 1) % N, N + i
            idx += [a, c, b, a, d, c] if up else [a, b, c, a, c, d]
        return mesh(ring(RB, z) + ring(R, z), idx)

    def disk(z, up):
        idx = []
        for i in range(N):
            b, c = 1 + i, 1 + (i + 1) % N
            idx += [0, c, b] if up else [0, b, c]
        return mesh([(0, 0, z)] + ring(RB, z), idx)

    u = np.array([np.cos(np.radians(-70)), np.sin(np.radians(-70)), 0])
    crack = [u * (RB + 0.01) + [0, 0, -5], u * (R - 0.01) + [0, 0, -5],
             u * (R - 0.01) + [0, 0, 5], u * (RB + 0.01) + [0, 0, 5]]
    s = 'LookAt 0 -60 10   0 0 0   0 0 1\nCamera "perspective" "float fov" 22\n'
    return s, ('WorldBegin\n' + SOFTBOX +
               'AttributeBegin\n  AreaLightSource "diffuse" "blackbody L" 4500 "float scale" 25\n' +
               quad([(-300, -150, -100), (-300, 150, -100), (-300, 150, 200), (-300, -150, 200)]) +
               'AttributeEnd\nAttributeBegin\n  MediumInterface "glaze" ""\n' + GLAZE +
               side(R) + annulus(H, True) + annulus(-H, False) +
               'AttributeEnd\nAttributeBegin\n  MediumInterface "" "glaze"\n' + BODY + side(RB) +
               'AttributeEnd\nAttributeBegin\n' + BODY + disk(H, True) + disk(-H, False) +
               'AttributeEnd\nAttributeBegin\n' + CRACK + quad(crack) + 'AttributeEnd\n')


def main():
    camera, world = {'slab': slab, 'cylinder': cylinder}[sys.argv[1]]()
    for spec in sys.argv[2:]:
        name, w, h, spp, seed, rnee = spec.split(':')
        with open(name + '.pbrt', 'w') as f:
            f.write(camera + HEAD.format(name=name, w=w, h=h, spp=spp, seed=seed, rnee=rnee) + world)


if __name__ == '__main__':
    main()
