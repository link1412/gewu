# Studio lighting data, for a physically based renderer

We simulate a photo studio (lights, backdrops) for product and museum-object photography. Every number needs a source (URL, and the page/table). Say for each value whether it is measured data, a manufacturer's spec, or someone's estimate.

Find:

1. **Backdrop reflectance**, spectral if it exists, else a single value:
   - black velvet, black flocked paper / flock sheet (e.g. the "light trap" flock papers sold for optics and photography);
   - photographic seamless paper (white, mid grey, black; Savage, Colorama or similar);
   - the 18% grey card (Kodak or other), and any spectral data for it.
2. **LED studio light spectra** as numbers (wavelength, relative power): the CIE LED illuminants of CIE 015:2018 (LED-B1 ... B5, BH1, RGB1, V1, V2) and, if published, a high-CRI studio LED (Aputure, ARRI, Godox ...). Also what spectrum a studio xenon flash has (a measured SPD, or its correlated colour temperature with a source).
3. **How museums light objects for their catalogue photographs** (the Met, the Palace Museum, the British Museum, Getty, Smithsonian; imaging guidelines such as FADGI or Metamorfoze if they cover 3D objects): light types, positions and angles, sizes, backgrounds. Also the usual sizes of studio modifiers (softbox, strip box, octabox) from makers' specs.

Deliver, in this directory:
- `report.md`: the findings, short, each with its source URL;
- one CSV per spectrum or reflectance curve you can get as numbers (`name.csv`: `wavelength_nm,value`, a comment line on top with the source URL).


