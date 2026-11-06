"""A transparent coat over a diffuse base, in true geometry: the pbrt text for a flat coated tile (docs/coats.md).

    from coat import coat_medium, coated_tile
    text = coat_medium("glaze", sigma_a=None)                    # before the shapes (a clear coat needs none)
    text += coated_tile((x0, x1), (y0, y1), z_base=-0.3, thickness=0.3, eta=1.52, alpha=0.008, medium="glaze",
                        base='Material "diffuse" "texture reflectance" "fam"',
                        film='Material "thindielectric" "float eta" 1 "texture transmittance" "co"')

What it writes, all in pbrt-v4's syntax (plus our "familymap" and the film's "transmittance", which the patched
pbrt and tools/rgbscene.py both read):
- the base: a quad at z_base, normal up, its material as given (diffuse: a uniform reflectance or a familymap);
- the film, if given: a quad `film_gap` above the base (a thindielectric of eta 1 with a "transmittance": an
  absorbing layer at the boundary, like cobalt under a glaze or a stain under a varnish);
- the coat's surface: a quad `thickness` above the base, a dielectric (eta, GGX alpha, remaproughness false), with
  the coat's medium inside if it absorbs. "bool refractivenee" lets the patched pbrt connect the base to the
  lights through it (docs/rnee.md); Cycles ignores it.
The tile has no side walls: a ray that walks inside the coat past the tile's edge goes on in the coat's medium in
both renderers alike, so make the tile larger than what the camera sees (the walk is a few mm at most).
UVs run (0,0)-(1,1) over the tile, the same on the base and the film.

The layers are triangles (a unit square in `coat_quad.ply`, write it with write_quad(scene_dir), placed by Translate and
Scale), not pbrt's bilinear patches: pbrt-v4's bilinear patch intersection rejects hits closer than
gamma(30) * (|o| + |d| + the corners' |p|), about 9e-6 times the distance from the camera in pbrt's cameraworld render
space (3.6 um at 400 mm), so a ray leaving the film downwards missed the base 2 um below and the tile went black
(measured, docs/coats.md). Triangles test in coordinates relative to the ray's origin; what limits the gap then is the
spawned ray's offset, gamma(7) |p| ~ 4e-7 times the distance (0.17 um at 400 mm), so the default gap of 4 um holds out to
a few metres.
"""


def spectrum(pairs):
    """[l0, v0, l1, v1, ...] as pbrt's sampled spectrum."""
    return "[ " + " ".join(f"{x:g}" for x in pairs) + " ]"


def coat_medium(name, sigma_a=None):
    """A homogeneous, non-scattering medium for the coat, sigma_a in 1/mm as [l0, v0, ...]; None: no medium."""
    if sigma_a is None:
        return ""
    return (f'MakeNamedMedium "{name}" "string type" "homogeneous" "spectrum sigma_a" {spectrum(sigma_a)} '
            f'"spectrum sigma_s" [ 360 0 830 0 ] "float scale" 1\n')


QUAD_PLY = "coat_quad.ply"


def write_quad(d):
    """The unit square [0,1]^2 at z = 0 as two triangles with u = x, v = y, normal +z; `d` is the scene's directory."""
    open(f"{d}/{QUAD_PLY}", "w").write(
        "ply\nformat ascii 1.0\nelement vertex 4\nproperty float x\nproperty float y\nproperty float z\n"
        "property float u\nproperty float v\nelement face 2\nproperty list uchar int vertex_indices\nend_header\n"
        "0 0 0 0 0\n1 0 0 1 0\n1 1 0 1 1\n0 1 0 0 1\n3 0 1 2\n3 0 2 3\n")


def _quad(x, y, z):
    (x0, x1), (y0, y1) = x, y
    return (f"  Translate {x0:.6f} {y0:.6f} {z:.6f}\n  Scale {x1 - x0:.6f} {y1 - y0:.6f} 1\n"
            f'  Shape "plymesh" "string filename" "{QUAD_PLY}"\n')


def coated_tile(x, y, z_base, thickness, eta, alpha, base, medium=None, film=None, film_gap=0.004,
                refractivenee=True, coat_extra=""):
    """pbrt text for the tile; x, y: (min, max) in mm. `base` and `film` are Material lines (strings).
    The layers' normals point up (+z). Needs write_quad(scene_dir) once."""
    if thickness <= film_gap:
        raise ValueError("the coat must be thicker than the film's gap")
    inside = f'"{medium}"' if medium else '""'
    out = []
    out.append("AttributeBegin  # coated tile: base\n")
    if medium:
        out.append(f'  MediumInterface "" {inside}\n')
    out.append(f"  {base}\n" + _quad(x, y, z_base) + "AttributeEnd\n")
    if film:
        out.append("AttributeBegin  # coated tile: film\n")
        if medium:
            out.append(f"  MediumInterface {inside} {inside}\n")
        out.append(f"  {film}\n" + _quad(x, y, z_base + film_gap) + "AttributeEnd\n")
    out.append("AttributeBegin  # coated tile: coat surface\n")
    if medium:
        out.append(f'  MediumInterface {inside} ""\n')
    out.append(f'  Material "dielectric" "float eta" [ {eta} ] "float roughness" [ {alpha} ] "bool remaproughness" false'
               + (' "bool refractivenee" true' if refractivenee else "") + coat_extra + "\n"
               + _quad(x, y, z_base + thickness) + "AttributeEnd\n")
    return "".join(out)
