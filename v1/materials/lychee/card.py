"""The lychee's material card: the three pieces of the card's photograph (Ivar Leidus, 'Lychee fruits and seed',
ref/lychee/, CC BY-SA 4.0) laid out as it shows them, for objects/lychee/run.py with materials/lychee/card-leidus.json.

    python3 -I materials/lychee/card.py            # -> out/lychee/objects/leidus_card/leidus_card.pbrt

- the whole fruit lying on its side, its stem to the right (the photo's left piece);
- the peeled aril standing in a cup of its pericarp (the right piece);
- the seed lying in front.
Image right is -x (pbrt's LookAt, optics/studio.py, the camera on -y). Sizes from objects/lychee/leidus.json (its scale assumed, so the card's px/mm is uncertain by ~15 %); positions read
off the photo's 1500 px preview at about 17.8 px/mm [A]. The aril's crinkled skin is objects/lychee/lychee.py
write_aril_skin with the numbers below.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "objects/lychee"))
import lychee as L  # noqa: E402

SKIN = {"across_mm": 0.35, "along_mm": 2.0, "rms_mm": 0.012,
        "source": "the photo's aril at full size: creases about 30-60 px apart and several times longer, along the "
                  "meridians [M, by eye, ~70 px/mm assumed]; depth not measurable [A]"}


def main():
    cfg = L.load("leidus")
    out = os.path.join(ROOT, "out/lychee/objects/leidus_card")
    os.makedirs(out, exist_ok=True)
    B = L.Builder(cfg)
    a, c = B.F.a, B.F.c
    H = float(B.F.H.mean())
    body = []
    # the whole fruit, lying, stem to the right
    L.build(cfg, out, "fruit", ("pericarp", "aril", "seed"), axis_to=(-1, 0, 0), at=(19.0, 0.0, a + H), lines=body)
    # the peeled aril, upright, in the apex's cup of pericarp
    skin = L.write_aril_skin(os.path.join(out, "peeled_skin.pfm"), B, SKIN)
    z_aril = c + H
    L.build(cfg, out, "peeled", ("aril", "seed"), axis_to=(0, 0, 1), at=(-19.0, 4.0, z_aril), lines=body,
            aril_uv="peeled_skin.pfm")
    L.build(cfg, out, "cup", ("pericarp",), cut_z=-0.45 * c, axis_to=(0, 0, 1), at=(-19.0, 4.0, z_aril), lines=body)
    # the seed, lying in front, its hilum to the right
    sa = B.seed_axes
    L.build(cfg, out, "seed", ("seed",), axis_to=(-1, 0, 0), at=(-3.0 + B.seed_z, -20.0, sa[1]), lines=body)
    L.write_fragment(out, "leidus_card", cfg["material_set"], body,
                     "the lychee material card's pieces (materials/lychee/card.py), as the Leidus photograph lays them out")
    json.dump({"config": "leidus", "skin": skin}, open(os.path.join(out, "leidus_card.json"), "w"), indent=1)
    print(f"-> {out}")


if __name__ == "__main__":
    main()
