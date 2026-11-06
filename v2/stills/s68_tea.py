"""Shot 68: what tea does to light, per wavelength band. eps = relative absorbance, 1 at 450 nm; K_abs (compositor) sets how strong undiluted tea is.

Looked up, read off a figure (not re-measured here): Sentkowska & Pyrzynska 2022, Antioxidants 11, 2489, Figure 1, the black tea infusion before any nanoparticles:
A = .34 at 400 nm, .15 at 450, .07 at 500, .04 at 550, about .01 at 600 and 650, about 0 at 700, each +-.01. Copies of the source and caveats: ref/tea_plume/report.md.
Chosen inside that error, because the curve is on its baseline there: .020 at 600, .012 at 650, .007 at 700. The red tail decides how dark the thick parts go, so it is the weakest number here.
The absolute strength is not from that paper (its dilution is not stated): K_abs is set by eye and reported as a choice.
"""

import numpy as np

SOURCE = "Sentkowska & Pyrzynska 2022, Fig 1, read off a figure; red tail chosen within its error"
TABLE_NM = np.array([400.0, 450.0, 500.0, 550.0, 600.0, 650.0, 700.0])
TABLE_A = np.array([0.34, 0.15, 0.07, 0.04, 0.020, 0.012, 0.007])


def bands():
    lams = np.linspace(415.0, 685.0, 7)
    return lams, np.exp(np.interp(lams, TABLE_NM, np.log(TABLE_A))) / 0.15
