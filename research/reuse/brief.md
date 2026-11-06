# Research brief: reusable models and data for the hard shots of a film

You are researching for a film project. Find existing papers, open-source code and measured data that we can reuse directly, so we do not derive physical models from scratch. Use web search, and search Chinese sources too (CNKI abstracts, museum and university reports).

## Context
- We render with pbrt-v4 in spectral mode, then simulate a camera (sensor noise, H.264).
- Quality bar: photographic, matching a reference film at 1080p, 5.1 Mb/s.
- pbrt-v4 built-ins:
  - **Materials:** coatedconductor, coateddiffuse, conductor (named metal spectra such as metal-Au-eta, metal-Cu-eta), dielectric, diffuse, diffusetransmission, hair, interface, measured (RGL-EPFL .bsdf files), mix, subsurface, thindielectric.
  - **Shapes:** bilinearmesh, curve, cylinder, disk, loopsubdiv, plymesh, sphere, trianglemesh.
  - **Media:** cloud, homogeneous, nanovdb, rgbgrid, uniformgrid. Emission works through blackbody spectra.
  - **Lights:** diffuse area, distant, goniometric, infinite, point, projection, spot.
  - **Not supported:** polarization.

## Items, in priority order
1. **Shots 01 and 38, 墨晕.**
   - The scene: Chinese ink (carbon soot plus glue binder) spreading in xuan paper (宣纸), seen back-lit and at an angle. In shot 38 a light behind the paper rises like a sunrise.
   - Find (a) ink-diffusion simulation models and open-source implementations: Chu & Tai 2005 "MoXi" (DOI 10.1145/1073204.1073221), Curtis et al. 1997 "Computer-Generated Watercolor", and anything newer and physically based.
   - Find (b) optical data: scattering and absorption coefficients, thickness, grammage and transmittance of xuan paper (or paper in general, e.g. Kubelka–Munk data), and the absorption of dried carbon-ink films.
2. **Shot 14, 走马灯 (revolving lantern).** A candle flame inside a paper lantern, with cut-paper figures rotating and casting shadows on the paper. Find:
   - measured candle-flame data: temperature and soot volume fraction fields, emission spectra;
   - translucency data for lantern paper;
   - models that have code.
3. **Shot 22, 掐丝珐琅 (cloisonné).** Gilded copper wires, vitreous enamel (glass with pigments and opacifiers), a polished surface with pits and bubbles. Find:
   - measured reflectance spectra or optical data of cloisonné or vitreous enamels (Chinese 景泰蓝 if possible), enamel layer thickness, bubble sizes;
   - how to model it with pbrt-v4's layered materials.
4. **Cross-cutting items. Keep each one brief.**
   - **Shot 19, 点螺** (mother-of-pearl in black lacquer): nacre iridescence models (multilayer aragonite), e.g. Belcour & Barla 2017's thin-film microfacet model, and any rendering work specific to nacre. Note code and licence.
   - **Shot 23, mica between crossed polarizers:** computing interference colours from first principles (Michel-Lévy), e.g. Sørensen 2013 in the European Journal of Mineralogy, and any open code.
   - **Shot 27, gold-leaf flakes falling:**
     - dynamics of fluttering and tumbling plates (Andersen, Pesavento & Wang 2005, J. Fluid Mech.) and implementations of it;
     - gold-leaf thickness and its spectral transmission.
   - **Shot 2, 点茶:** approaches for rendering whisked tea foam, and bubble-size data.
   - **Shot 5, cinnabar (HgS) crystals:** ordinary and extraordinary refractive indices versus wavelength, and the absorption edge.
   - **Shot 25, nephrite jade:** any measured scattering or absorption data.
   - **The RGL-EPFL measured material database:** list the entries relevant to us (gold, copper, brass, paper, ceramics or glazes, lacquer, nacre or iridescent materials) and its licence.

## Deliverable
- Write `reuse-map.md` in the working directory. Write it incrementally, so partial results survive if you stop early.
- For each item give:
  - the recommended approach, in one line;
  - the sources (authors, title, venue, year, DOI or URL);
  - what each source gives us (equations, parameter values with units, code);
  - code: URL, licence, language, last activity;
  - data: dataset name and licence;
  - how it maps onto the pbrt-v4 built-ins above;
  - the gaps.
- Tag every claim:
  - [M]: measured in the cited paper;
  - [D]: a description or a secondary source;
  - [A]: abstract only;
  - [I]: your inference.
- Your final message: per item, one line with the recommendation and the biggest gap.

## Rules
- Open every source to confirm it exists and says what you report. Do not cite from memory.
- If a number cannot be found, write "not found". Never fill one in silently.
- Do not download or run third-party code. Record the URL and licence only.
- Spend most of the effort on items 1–3.
- Budget: about 80 searches and page reads.
