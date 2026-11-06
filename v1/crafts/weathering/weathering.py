"""Weathering (风化, 失光): light and air age a surface's skin. For Asian lacquer, light aging pits and cracks the
surface, raises its roughness and haze and lowers its gloss, most of all in vermilion formulations, with blanching;
the vermilion also darkens and gets black spots (Han, Webb, Hao, Khanjian, Schilling 2023, J. Cult. Herit. 63:249-262,
doi 10.1016/j.culher.2023.08.010, abstract [I]). Modelled: the skin's roughness only, as the GGX alpha of the
weathered skin (`skin_alpha`, weathering.json). Not modelled: blanching (a whitish diffuse veil) and the pigment's
darkening. A new piece: skin_alpha 0 (the material's own alpha).

    skin_alpha(alpha0, P) -> alpha of the weathered skin (alpha0 and skin_alpha in quadrature)
"""
import json
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))


def load():
    return json.load(open(os.path.join(HERE, "weathering.json")))


def skin_alpha(alpha0, P):
    return math.sqrt(alpha0 ** 2 + P["skin_alpha"] ** 2)
