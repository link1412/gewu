# Research brief: 掐丝珐琅 (Chinese cloisonné enamel), its colours and its surface

You are researching for a film project. We need measured data we can use directly. Use web search, and search Chinese and Japanese sources too (CNKI abstracts, 故宫博物院 / Palace Museum publications, museum sites, university repositories).

## Context
- We render one shot with a physically based renderer, in the camera's raw RGB, from spectra: the rim of a red-ground (红地) cloisonné plate, seen from above, on a dark blue cloth. The plate is copper, the cells are filled with opaque enamel glass, the wire tops are gilded and polished flush with the enamel.
- Today our enamel colours are sRGB values that we chose by eye (substitutes). We need measured reflectance spectra to replace them, and the optics of the glass and the gilding.

## Questions, in priority order
1. **Measured reflectance spectra of cloisonné and painted enamel colours**: diffuse reflectance or FORS, 380–780 nm, as numbers or as a figure we can digitise (mark [D]).
   - Chinese pieces first: Ming and Qing cloisonné (景泰蓝, 铜胎掐丝珐琅), Qing painted enamel (画珐琅), and modern Beijing production.
   - Colours: opaque red, pink, turquoise, lapis or cobalt blue, yellow, white, green, black.
   - For each colour, which colourant and opacifier was found and by what method (Raman, XRF, SEM-EDS). Expected examples, all to be confirmed: copper turquoise in lead-potash glass; cobalt blue; lead-tin yellow or lead antimonate yellow; lead arsenate or tin oxide white; iron red; gold-ruby pink (colloidal gold); cadmium sulfoselenide red in modern pieces.
   - If no Chinese spectra exist, give the closest measured ones (European painted enamels, Limoges, Canton enamels, or glass with the same colourant), and label them as substitutes.
2. **Optics of the enamel glass**:
   - refractive index of lead-potash silicate enamel glass, as a function of PbO content if a source gives it;
   - absorption spectra (absorption coefficient per mm) of the colourants in glass, for translucent colours: cobalt, copper(II);
   - the surface after polishing: gloss values or roughness measurements, if any.
3. **The craft, with sources**:
   - wire: copper strip height and thickness, for Ming/Qing and modern pieces;
   - gilding: method (fire-gilding with mercury amalgam vs electroplating) and thickness, period by period; what worn gilding looks like (copper showing through);
   - firing: number of fillings and firings, shrinkage;
   - polishing (磨光): the steps and abrasives (e.g. 金刚砂, 黄石, 木炭), and whether the wire tops end up flush with the enamel;
   - surface defects: size and density of pits (砂眼) and bubbles in the enamel, measured or described.
4. **Red-ground cloisonné plates and dishes as reference images** (visual reference only, they will not appear in the film). Search open-access collections: The Met (CC0), Cleveland Museum of Art (CC0), Smithsonian / National Museum of Asian Art (CC0), Rijksmuseum, Palace Museum.
   - Look for Chinese cloisonné with a red ground (红地), or with red as a major colour, preferably plates or dishes (盘) with a rim.
   - Download the largest available image of up to 8 objects into `raw/images/`.
   - For each, list object number, title, date, dimensions (diameter, height), licence and URL, and describe the rim decoration (bands, wire density, gilt edge).
5. **The cloth**: measured reflectance spectrum, 380–780 nm, of indigo-dyed cotton (denim) or dark blue wool felt, as numbers or a figure.

## Deliverable
- Write `falang.md` in the working directory, incrementally, so partial results survive if you stop early. Start it with a table of the numbers found: quantity / value / unit / colour or object / source / tag.
- Put any tabulated or digitised spectra in `enamel_spectra.csv`.
  - The first column is wavelength_nm.
  - One column per colour.
  - Say where each column came from.
- Keep downloaded data files under `raw/`.
- One section per question: sources (authors, title, venue, year, DOI or URL), the numbers, the gaps.
- Tag every claim:
  - [M]: measured in the cited source;
  - [D]: read off a figure or from a secondary source;
  - [A]: abstract only;
  - [I]: your inference.
- Your final message: a 10-line summary of what was found, file names, and the biggest gaps.

## Rules
- Open every source to confirm it exists and says what you report. Do not cite from memory.
- If a number cannot be found, write "not found". Never fill one in silently.
- Data files (CSV, PDF, images) may be downloaded. Do not download or run third-party code.

- Budget: about 60 searches and page reads, about one hour. When the budget is used up, finish the file with what you have.
