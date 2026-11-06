# Research brief: colour of the stains in Guan/Ge crackle, and crackle cell sizes

You are researching for a film project. We need measured data we can use directly. Use web search, and search Chinese sources too (CNKI abstracts, university repositories, museum sites).

## Context
- We render a macro shot of a Southern Song Guan vase whose crackle is stained "iron wire and golden thread" (金丝铁线): a black network of large cells (铁线) and a golden, yellow-brown network of small cells (金丝).
- We model each stained crack as a vertical wall through the glaze coated with the deposit, seen through the glaze. The wall needs a diffuse reflectance spectrum, 400-750 nm.
- Already known (do not repeat): Wu Haoze et al. 2025, J. Beijing Univ. Chem. Technol. 52(5):133-144, Laohudong sherds: golden thread = lepidocrocite + hematite + quartz in a clay-like deposit (EDS Fe2O3 5.7-6.5 wt%), fading with depth into the crack; iron wire = carbon (Raman D band, no graphite) + a little pyrite + quartz (EDS Fe2O3 about 10 wt%), not fading with depth. Li, Deng & Xu 2001, MRS Bulletin 26(1). Yang et al. 2012 OCT chapter (InTech, DOI 10.5772/31213).

## Questions, in priority order
1. **Reflectance spectra of the stain phases**, 350-800 nm or at least 400-750 nm, as numbers:
   lepidocrocite (gamma-FeOOH), hematite (alpha-Fe2O3), goethite (alpha-FeOOH), pyrite (FeS2), and a black carbon (charcoal, biochar or carbon black).
   - First choice: USGS Spectral Library Version 7 (Kokaly et al. 2017, public domain): download the ASCII data files for each mineral, prefer the finest grain size (powders, < 45 um or "fine"), and note sample ID, grain size, instrument and the wavelength column.
   - Others if USGS lacks one: RELAB (Brown University), ASU, ECOSTRESS/ASTER library (JPL), or a paper with a tabulated or plotted spectrum (then digitise and mark it [D]).
   - Also any reflectance of an iron-oxide-stained clay or soil similar to a golden-thread deposit (clay with 5-7 wt% Fe2O3 as lepidocrocite/hematite).
2. **Measured colour of the stained lines themselves** on Guan or Ge ware (L*a*b*, RGB with calibration, or reflectance spectra of 金丝 or 铁线), any study.
3. **Crackle cell sizes measured on Guan and Ge ware**, in mm, with glaze thickness if given:
   - Lahlil S., Li W., Xu J. 2013, "Crack patterns: morphology of ancient Chinese wares", The Old Potter's Almanack (Heidelberg journals, https://journals.ub.uni-heidelberg.de/index.php/opa/article/download/11773/5630/19803 was blocked by an anti-bot page for us; try other routes: the article landing page, archive.org, Google Scholar versions, ResearchGate, Semantic Scholar);
   - Chinese literature on 开片 or 纹片 sizes: 哥窑 金丝铁线, 鱼子纹, 百圾碎, 官窑 冰裂纹, 蟹爪纹; cell size, crack width, and how they relate to glaze thickness.
4. **Crack opening at the surface and stain depth**, in um, for Guan or Ge crackle (SEM, OCT, thin sections).
5. Nice to have: the results of Li, Yuan, Cao & Hein 2022, Microscopy and Microanalysis 28(6):1878-1889, on what fills the glaze cracks (any open version).

## Deliverable
- Write `stains.md` in the working directory, incrementally, so partial results survive if you stop early. Start it with a table: phase / spectrum source / sample and grain size / file name / tag.
- Write the spectra as `stain_spectra.csv`: first column wavelength_nm (400 to 750 by 10 nm, wider if the source has it), one column per phase, reflectance as a fraction 0-1. Keep the downloaded raw files too, each in its own folder under `raw/`, and say which column you used.
- One section per question: sources (authors, title, venue, year, DOI or URL), the numbers, gaps.
- Tag every claim:
  - [M]: measured in the cited source;
  - [D]: read off a figure or from a secondary source;
  - [A]: abstract only;
  - [I]: your inference.
- Your final message: a 10-line summary of what was found, file names, and the biggest gaps.

## Rules
- Open every source to confirm it exists and says what you report. Do not cite from memory.
- If a number cannot be found, write "not found". Never fill one in silently.
- Data files (ASCII, CSV, PDF) may be downloaded. Do not download or run third-party code.

- Budget: about 50 searches and page reads.
