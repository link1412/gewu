# Research brief: reusable models and data for rendering silk thread and embroidery

You are researching for a film project. Find existing papers, open-source code and measured data that we can reuse directly, so we do not derive models from scratch. Use web search, and search Chinese sources too (CNKI abstracts, university repositories).

## Context
- We render with pbrt-v4 in spectral mode, then simulate a camera (sensor noise, H.264).
- Quality bar: photographic, matching a reference film at 1080p, 5.1 Mb/s.
- pbrt-v4 built-ins:
  - **Materials:** coatedconductor, coateddiffuse, conductor, dielectric, diffuse, diffusetransmission, hair (Chiang et al. 2016), interface, measured (RGL-EPFL .bsdf files), mix, subsurface, thindielectric.
  - **Shapes:** curve (flat, ribbon or cylinder), plymesh, bilinearmesh, others.
  - **Media:** homogeneous, uniformgrid, rgbgrid, nanovdb.
  - **Not supported:** polarization.
- **Shot 13:** Suzhou embroidery (苏绣) on a frame, seen close up. It is satin-like stitching of split silk floss (劈丝), and the arc of the frame or the embroidered edge is in shot.
- **Shot 24:** back-lit double-sided embroidery (双面绣) on sheer silk gauze (绡/纱).
- **Shot 36:** the tip of a goat-hair calligraphy brush (羊毫), white fibres, against a dark background.

## Already found (do not repeat)
- Khungurn et al. 2015, TOG 35(1), "Matching Real Fabrics with Micro-Appearance Models":
  - red silk satin, micro-CT, fibre radius 4.72 um;
  - fitted fibre BCSDF: beta_R 1 deg, beta_TT 10 deg, gamma_TT 19.8 deg, plus C_R and C_TT colours;
  - phenomenological; the authors say back-lit appearance is not validated.
- Perotto et al. 2017, APL 111:103702 (abstract only): refractive index of Bombyx mori fibroin film about 1.566 at 500 nm, with Cauchy coefficients.
- Ryu et al. 2017, Materials 10: silk absorbance from UV to IR; absorption is low in the visible.

## Questions, in priority order
1. **Fibre-level appearance models with fitted parameters for silk.** For each: equations, parameter values with units, and whether it handles transmission and back-lighting. Check:
   - Sadeghi, Bisker, De Deken, Jensen 2013, "A Practical Microcylinder Appearance Model for Cloth Rendering", TOG 32(2);
   - Aliaga et al. 2017, "An Appearance Model for Textile Fibers", CGF 36(4);
   - Irawan & Marschner 2012, "Specular Reflection from Woven Cloth", TOG 31(1), and the Mitsuba 0.5 `irawan` presets for silk;
   - anything newer, 2018–2026.
2. **Yarn and ply geometry.** Zhao, Luan, Bala 2016, "Fitting Procedural Yarn Models for Realistic Cloth Rendering": fitted parameters (ply count, twist, fibre count, migration) and code. Also any later ply-based models that have code.
3. **Code.** Open-source implementations of 1 and 2 (Mitsuba plugins, standalone generators). Give URL, licence, language and last activity.
4. **Embroidery-specific rendering work.** Western and Chinese, including 苏绣 and 乱针绣 rendering or simulation. Is each one physically based or image stylisation (NPR)? Is there any code?
5. **Measured data.** RGL-EPFL material database entries for silk, satin or other fabrics, with licence. Transmission data for sheer silk gauze or organza.
6. **Goat-hair brush (shot 36).** Optical parameters of white, unpigmented keratin fibres for the pbrt `hair` model (eta, absorption, roughness, scale angle), and goat-hair fibre diameter and tip taper.

## Deliverable
- Write `reuse-map-fiber.md` in the working directory. Write it incrementally, so partial results survive if you stop early.
- Start the file with a **Recommended pbrt-v4 stack for shots 13, 24 and 36**: geometry generator, BSDF, parameter values, sources.
- Then give one section per question: sources (authors, title, venue, year, DOI or URL), what each gives us, code and licence, data and licence, gaps.
- Tag every claim:
  - [M]: measured in the cited paper;
  - [D]: a description or a secondary source;
  - [A]: abstract only;
  - [I]: your inference.
- Your final message: a 10-line summary of the recommendation and the biggest gaps.

## Rules
- Open every source to confirm it exists and says what you report. Do not cite from memory.
- If a number cannot be found, write "not found". Never fill one in silently.
- Do not download or run third-party code. Record the URL and licence only.
- Budget: about 60 searches and page reads.
