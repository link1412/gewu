# Ink on xuan paper: numbers for a physical simulation and render

We are simulating a pool of Chinese ink (墨汁 / 墨) spreading on xuan paper (宣纸, 生宣) and rendering it backlit
(light behind the paper, camera in front). We need published, sourced numbers. For each number give the value,
units, the source (authors, year, title, journal/URL, page/table/figure), and whether it is measured or assumed by
that source. If something is not found, say "not found" — do not estimate.

1. Xuan paper (生宣, also any 净皮/特净/棉料, and Japanese washi or mulberry/kozo paper as a fallback, labelled):
   basis weight (g/m²), thickness (µm), porosity, fibre types and fibre length/width, mean pore radius.
   Optical: transmittance and reflectance spectra (or single-band values) dry and wet (water-saturated);
   Kubelka-Munk scattering S and absorption K if any paper study gives them; how much more transparent wet paper is.
2. Water wicking in xuan / tissue / filter paper: Lucas-Washburn coefficient (front distance^2 per time), measured
   spreading of a drop or of ink on xuan (front radius vs time), any 2D anisotropy (machine vs cross direction).
3. Chinese ink (墨汁 and ground ink-stick ink): carbon particle size distribution (primary particle and aggregate),
   carbon mass fraction, glue (animal glue / gelatin) fraction, and observations of the chromatographic separation
   on paper (dark core, lighter halo/水晕, water ring) with sizes.
4. Light absorption of soot / carbon black: mass absorption cross-section at 550 nm and the absorption Ångström
   exponent (spectral dependence), ideally a review (e.g. Bond & Bergstrom 2006).
5. Ink-wash (sumi-e) and watercolour simulation papers that give model equations and parameter values:
   Chu & Tai 2005 "MoXi", Curtis et al. 1997, Guo & Kunii, Lee 1999/2001, Xie et al., any later ones; also porous
   media "deep-bed filtration" (Iwasaki) applied to ink/paper or inkjet on paper. Give the equations and the
   parameter values used.
6. Index-matching / "darker when wet" for paper: Lekner & Dorf 1988 and any paper-specific measurement of
   reflectance and transmittance change on wetting.

Deliver: write report.md in this directory (a table per section, then notes). Download any open PDFs you rely on
into ./pdf/ (do not commit or upload anything). Keep it factual.

