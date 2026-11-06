# Research brief: 点螺 (thin mother-of-pearl inlay on black lacquer), and the optics of nacre

You are researching for a film project. We need measured data we can use directly. Use web search, and search Chinese and Japanese sources too (CNKI abstracts, museum sites, university repositories, ctext.org / Wikisource for classical texts).

## Context
- We render a macro shot of a Qing-style 点螺 round box (圆盒) with a gently domed lid, on a turntable, lit from behind. 点螺 = Yangzhou-style thin mother-of-pearl (薄螺钿) cut into dots, threads and flakes (点、丝、片) and inlaid in black lacquer.
- We model the shell as a stack of aragonite tablets separated by thin organic layers (a disordered multilayer), computed with a transfer matrix, over black lacquer. We need the stack's parameters for the shells actually used, and how the craft builds the surface.
- Already known (do not repeat, but do open the full texts if you can): Salman et al., "Hyperspectral interference tomography of nacre", arXiv:2010.08170 / PNAS 2021, DOI 10.1073/pnas.2023623118 (we only saw the abstract); Wakabayashi, Asai & Yamakita 2025, JASSE 12(1):152-163 (abstract only); Belcour & Barla 2017 (single thin film, not enough for nacre).

## Questions, in priority order
1. **The stack, for the shells used in 螺钿** (abalone Haliotis spp., e.g. H. discus hannai 皱纹盘鲍, H. diversicolor 杂色鲍, H. iris; also 夜光螺 Turbo marmoratus and pearl oysters Pinctada spp.):
   - aragonite tablet thickness: mean and spread (standard deviation, or a histogram), in nm, per species. Leads: Salman et al. 2021 (full text and SI: their fitted mean thickness and disorder maps); Gilbert et al. 2017, "Nacre tablet thickness records formation temperature in modern and fossil shells", EPSL (tables per species); SEM studies of abalone nacre.
   - organic interlamellar layer thickness (nm) and its refractive index;
   - aragonite refractive indices n_alpha, n_beta, n_gamma with dispersion over 400-700 nm if any source gives it (refractiveindex.info, mineralogy handbooks); which crystal axis is normal to the tablets in nacre;
   - measured reflectance spectra of nacre, 400-750 nm, ideally at several angles, as numbers or a figure we can digitise (mark [D]).
2. **The tilt of the layers against a polished surface, and the grating it makes.** Polished nacre shows diffraction from the exposed layer edges. Find the measured grating period and the tilt angle, and the size of the colour patches ("flames") on polished abalone or pearl-oyster nacre. Leads: Liu, Shigley & Hurwit 1999, Optics Express 4(5) (Pinctada margaritifera, diffraction); Tan, Wong & Lee 2004, Optics Express 12(20) (Haliotis glabra). Confirm these exist before citing.
3. **How 点螺 is made**, with sources:
   - which shells, how the thin sheets are made (boiled and split, or ground), sheet thickness in mm;
   - sizes of the dots, threads and flakes;
   - after inlaying: is the shell left exposed and flush after grinding and polishing (磨显、推光), or covered by a clear lacquer film (罩漆)? Is anything placed under the shell (衬色: coloured or gold backing), or only black lacquer?
   - the black lacquer: recipe (e.g. iron-blackened raw lacquer, 黑推光漆) and how it is polished;
   - colour sorting: 《髹饰录》 (黄成, 杨明注) has passages on 螺钿, 衬色蜔嵌 and on cutting shell by colour (something like 「分截壳色,随彩而施缀」). Quote the exact text with its source edition and URL; also 王世襄《髹饰录解说》 if available. Are there real 点螺 objects whose border bands are arranged in graded colours? Name them, or say not found.
   - 江千里 (17th c. Yangzhou): confirm who he was and the saying about his cups and plates (something like 「杯盘处处江千里」), with a source.
4. **Black urushi lacquer optics**: refractive index of cured urushi film; measured gloss, BRDF or surface roughness of polished (推光) lacquer; reflectance spectrum of black lacquer. Japanese sources (漆膜 屈折率, 光沢) are likely.
5. **Reference images** (for visual reference only, they will not appear in the film): open-access photographs of Chinese 点螺 or thin mother-of-pearl lacquer objects, especially round boxes with domed lids, and close-up details. Try The Met Open Access (CC0), Cleveland Museum of Art (CC0), Smithsonian / National Museum of Asian Art (CC0), Rijksmuseum, Palace Museum. Download the largest available image of up to 8 objects into `raw/images/`, and list object number, title, date, dimensions (diameter, height of box and lid), licence and URL. Note what the decoration layout is (lid top scene, borders on the lid wall, etc.).
6. Code metadata only: an open-source transfer-matrix implementation (e.g. the Python package `tmm`: licence, last release), and any nacre or pearl appearance model with code. Do not download or run code.

## Deliverable
- Write `dianluo.md` in the working directory, incrementally, so partial results survive if you stop early. Start it with a table of the numbers found: quantity / value / unit / species or object / source / tag.
- Put any tabulated or digitised spectra in `nacre_spectra.csv` (first column wavelength_nm) and say where each column came from. Keep downloaded data files under `raw/`.
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
