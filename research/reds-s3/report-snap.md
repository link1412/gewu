# Representative Chinese reds as physically based materials

Research date: 28 October 2026. This is a material-selection and evidence brief, not a set of calibrated shaders. No remote files were saved or downloaded; image and dataset URLs are supplied for later use.

**Recommended first builds:** carved vermilion lacquer, copper-red glaze with a separate Jun variant, and gold-ruby glass / gold-pink enamel. Together they test an opaque pigment layer, a nanoparticle-bearing glass, and transparent versus opacified colour. Iron-red plaster and dyed silk are valuable next surfaces. This recommendation and the final aesthetic ranking are editorial judgments, grounded in the evidence below.

**Evidence key.** [M] means a measurement reported in the cited source, including the source authors' stated measurement-based estimates and museum dimensions; [D] means a calculation, figure reading, or explicitly stated inference from measured results; [?] means uncertain, indirect, secondary-reported, or inadequately specified. Approximate measurements retain their approximation. Bibliographic dates, section/figure numbers, accession identifiers, chemical formula subscripts, URLs and licence version numbers are identifiers rather than scientific quantities. “Not found” means not located or verified during this time-bounded search, not proof that a datum does not exist.

**How to use the references.** Each section separates material physics from museum-object evidence. A catalogue material name is not an object-specific chemical assay. Most photographs below support shape, texture and overall scale; measured illumination, camera spectral response, surface roughness and object-matched optical spectra were generally not found. Do not treat image pixels as calibrated reflectance or transfer a solution spectrum directly to silk, a pigment-paint spectrum directly to lacquer, or a modern glaze's microstructure to every historical kiln. These are modelling constraints inferred from the sample differences documented below. No render-to-photograph validation was performed in this research task.

### Spectral evidence at a glance

The target interval is **380–780 nm** (brief specification, not a measurement). Curves, numerical datasets and peak positions are distinguished throughout; unmeasured endpoints have not been filled in.

| Material | Strongest located optical reference | Coverage / practical status |
|---|---|---|
| HgS | Fioretti et al. reference-paint FORS [H2] | **300–900 nm [M]**, Fig. 8 / Table 5; covers target; not lacquer/paste |
| Copper red | Zhu et al. historical underglaze red [C2]; Yuan et al. Jun [C4] | Historical reflectance **400–700 nm [M]** for Zhu; Jun UV–Vis Fig. 5. Full target-interval numeric historical dataset: **not found** |
| Gold red | Haslbeck et al. experimental gold-ruby glass [G12]; Haiss et al. aqueous particles [G2] | Measured absorption and particle-size evidence; historical Qing object-matched full-visible spectrum: **not found** |
| Iron red | Sherman–Waite iron-oxide spectra [I1]; USGS [I7] | Original absorption / diffuse-reflectance measurements **200–2000 nm [M]**; target covered |
| Red lead | Fioretti et al. reference-paint FORS [H2] | **300–900 nm [M]**, Fig. 8 / Table 5; target covered; identified 万年红 sheet spectrum: **not found** |
| Organic reds | Fonseca madder/cochineal lakes [O6] | **350–2500 nm [M]** acquisition; target covered. Other dyes: partial/unspecified coverage |
| Others | Yang et al. precious coral [X4] | Reflectance **200–900 nm [M]**, transformed by Kubelka–Munk; Fig. 7, raw-data link below; chicken-blood-stone object spectrum: **not found** |

### Shared numerical-data lead — URLs only

Anna Sofia Reichert, Ana Belén López-Baldomero, Francisco Moronta-Montero, Ana López-Montes, Eva María Valero and Carolina Cardell (2025), “Database of diffuse reflectance infrared Fourier transform spectroscopy (DRIFTS) and hyperspectral imaging (HSI) spectra of pigments and dyes for historical document analysis,” *Analytical and Bioanalytical Chemistry* **417**, 4351–4372, [DOI / original article](https://doi.org/10.1007/s00216-025-05948-3), provides manuscript-paint mock-ups and publicly linked numerical reflectance data. The VNIR data were cropped to **400–1000 nm [M]** and resampled at **5 nm [M]**; average spectra are supplied as CSV, with paper/parchment and gum-Arabic/egg-glair variants. This is a useful data-acquisition lead for the inorganic pigment sections, not measured Chinese lacquer or historical paper. Its short-wave crop excludes part of the target interval. [Dataset landing DOI](https://doi.org/10.6084/m9.figshare.28639103.v1). No dataset file was fetched or inspected, and no numerical array is reproduced here.

---

## 1. 朱砂 / 银朱 — cinnabar and vermilion, α-HgS

### Physics

**Recommended representation:** separate the absorbing/scattering pigment from its binder and surface. The same HgS is used in lacquer, ink and seal paste; these do not share a single gloss or texture. Natural cinnabar and manufactured vermilion are both red α-HgS; “synthetic” cannot safely be diagnosed from red hue alone. [H1, H3, H6, H8, H9]

α-HgS is a semiconductor: its visible absorption edge removes shorter wavelengths and leaves the red part of the spectrum relatively strongly reflected. Cardona et al. reproduce measured dielectric spectra alongside calculations in their Fig. 8. Their text reports an experimental gap around **2.25 eV [?]**, citing Zallen's earlier work, and an indirect edge closely followed by a direct edge; this is a secondary-reported measurement, not a fresh gap determination. Their raw LDA gaps are explicitly underestimated, so they should not be adopted as measured pigment parameters. [H1]

| Quantity / observation | Published value | What it is safe to use for | Source |
|---|---:|---|---|
| Earlier experimental electronic gap, as reported by Cardona | ≈2.25 eV [?] | Approximate electronic scale; primary experiment not independently inspected | H1, electronic-band-structure discussion |
| Measured dielectric-function curves | Fig. 8 [M] | Source of wavelength-dependent optical response, with crystal polarization retained; not a pigment-paint reflectance curve | H1 |
| Cinnabar pigment-paint reflectance rise | ≈570 nm [M] | Reference paint, not lacquer or seal paste | H2, Table 5 and Fig. 8 |
| Cinnabar reflectance inflection | ≈600 nm [M] | Characteristic sigmoidal spectral edge | H2, Table 5 |
| HgS reflectance spectra before/after chlorine doping and UV exposure | 400–800 nm [M] | Ageing-specific measured curves; requested 380–400 nm interval not covered in this source | H4, Fig. 2 |
| Additional derivative features in exposed samples | ≈650 and ≈730 nm [M] | Evidence of altered optical response, not two pristine-pigment absorption peaks | H4 |
| Hunan commercial coarse / medium / extra-fine pigment grades | 63–100 / 50–63 / <20 μm [?] | Supplier-stated grades only; do not treat as independently measured distributions | H3, Table 1 |
| Full tabulated reflectance/absorption values for a historical HgS lacquer/paste across the target interval | **not found** | Reference-paint curves available; see the shared numerical-data lead for another paint system | H1–H4 |

**Particle size:** in the Hunan series studied by Elert and Cardell, coarse pigment was bluish red and finer pigment more orange red. Their fine Almadén material nevertheless remained bluish red: particle size is an important control, not a universal colour-to-size lookup. They also demonstrate that grain size changes pigment–binder interaction and weathering. [H3]

**Darkening:** avoid a universal “red α-HgS simply becomes black β-HgS” shader. Elert, Pérez Mendoza and Cardell directly identify metallic Hg droplets in UV-aged egg-tempera paint and demonstrate a pathway through mercury sulfates without chlorides; their paint also loses binder. Pisu et al., using a different synthetic/chlorine/UV protocol, instead discuss sulfur-vacancy trap states, narrowing of the optical gap and progression toward metacinnabar. These are condition-dependent mechanisms, not mutually interchangeable ageing recipes. [H4, H5]

| Ageing evidence | Quantity | Tag and restriction | Source |
|---|---:|---|---|
| Hg droplets on UV-aged tempera | <100 nm to 1.5 μm | [M]; laboratory-aged egg tempera, not historical lacquer | H5, Fig. 6 |
| Total colour difference after laboratory UV exposure | ΔE* = 16.0 ± 0.7 | [M]; specific accelerated protocol, not a lifetime prediction | H5, Fig. 5 |

**Applications:** cinnabar is the principal historical red colorant of carved red lacquer. In lacquer carving, the wood establishes the object shape but the built-up lacquer itself is carved. Seal paste combines pigment with oil and fibrous material; the seal-paste ageing study describes cinnabar, mugwort fibre and oils, with red lead and other reds sometimes added in later practice. A Beijing University of Chinese Medicine museum account quotes the Qing imperial manufacture of red ink from cinnabar and glue and explains its use for imperial vermilion annotations (朱批); this is documentary evidence, not chemical identification of every surviving annotation. [H6, H8, H9]

### Objects

Object material names are museum catalogue identifications; no object-specific HgS spectrum or chemical analysis was found for these catalogue entries. Consequently these are strong morphology and scale references but should not be used as calibrated colour standards.

| Museum object | Size | Open image / licence | Why useful |
|---|---|---|---|
| Cleveland Museum of Art, **Lotus Dish**, Yuan dynasty, 1918.933 | Overall dimension 15.9 cm [M]; catalogue does not explicitly label this dimension “diameter” | https://www.clevelandart.org/art/1918.933 ; CC0 under CMA Open Access | Broad rounded petals, quiet surfaces, catalogue image description records fine cracking |
| Metropolitan Museum, attributed to Zhang Cheng, **Dish with long-tailed birds and hibiscuses**, mid-14th century, 2011.120.1 | Diameter 32.4 cm [M] | https://www.metmuseum.org/art/collection/search/40211 ; Public Domain / Met Open Access | Deep overlapping leaves and flowers; plain dark ground makes relief and edge shape legible |
| Metropolitan Museum, **Bowl**, Qing dynasty, 13.100.141 | Height 10.2 cm [M], diameter 21.3 cm [M] | https://www.metmuseum.org/art/collection/search/60917 ; Public Domain / Met Open Access | Cinnabar-lacquer catalogue identification; useful for curvature and wear at a larger object scale |

### Close-up look

Carved lacquer is a continuous pigmented polymer relief, not a block of raw cinnabar mineral. Look for smooth rounded high points, overlapping cut edges and lower carved geometric diaper grounds; damage may expose another coloured lacquer stratum. The Cleveland lotus catalogue explicitly describes fine cracks. The Met bird dish describes overlapping leaves at multiple relief levels above an unworked dark ground. [H6, HO1, HO2]

| Lacquer construction evidence | Value | Meaning / caution | Source |
|---|---:|---|---|
| Typical coat counts in museum overview | Often 30–35; sometimes up to 200 [?] | Curatorial generalization, not a measured universal specification | H6 |
| NGV detached fragment examined in cross-section | ≈1 mm thick [M]; at least 17 red layers [M] | Actual microstratigraphic observation for NGV Dish with peonies, 1645-D1A | H7 |
| Mean layer thickness from that fragment | ≈59 μm [D] | 1000/17; upper-bound average if more layers were unresolved, not a universal coat thickness | H7, calculation |
| NGV relief depth / estimated overall coat count | ≈9 mm [M] / ≈150 layers [D] | Count extrapolated by the conservator from fragment and relief depth | H7 |
| Quantified roughness / gloss / BRDF for these museum objects | **not found** | Do not assign a measured roughness value from an ordinary image | — |

Seal paste offers a different macro target: oil-bound pigment on and between paper fibres, with edges set by the stamp and paper. Documented ageing can create a yellow–brown oil halo around the impression; the study treats that migration as a conservation problem. For 朱砂墨/朱批, paper topography and brush deposition should therefore be modelled separately from an oil-rich stamped impression; measured binder loading, deposited thickness and gloss for specific imperial annotations were **not found**. [H8, H9; final modelling distinction is an inference]

### Sources

- **H1.** M. Cardona, R. K. Kremer, R. Lauck, G. Siegle, A. Muñoz, A. H. Romero and M. Schmidt (2010), “Electronic and phononic properties of cinnabar: Ab initio calculations and some experimental results,” *Physical Review B* **82**, 085210. https://doi.org/10.1103/PhysRevB.82.085210 ; full text https://arxiv.org/html/1007.2210v1 . Fig. 8 reproduces measured optical spectra; the earlier gap measurement is credited to R. Zallen (1967), “Fundamental Absorption Edge of Trigonal HgS,” in *II–VI Semiconducting Compounds*, D. G. Thomas, ed., p. 877; title confirmed by [Zallen’s publication list](https://www1.phys.vt.edu/~rzallen/), but the chapter and numeric gap were not independently inspected.
- **H2.** Giovanna Fioretti, Marina Clausi, Giacomo Eramo, Elisabetta Longo, Alessandro Monno, Daniela Pinto and Gioacchino Tempesta (2023), “A Non-Invasive and Sustainable Characterization of Pigments in Wall Paintings: A Library of Apulian Colors,” *Heritage* **6**, 1567–1593. https://doi.org/10.3390/heritage6020084 . Measured pigment-paint FORS curves Fig. 8; features Table 5. Text at https://www.mdpi.com/2571-9408/6/2/84 .
- **H3.** Kerstin Elert and Carolina Cardell (2019), “Weathering behavior of cinnabar-based tempera paints upon natural and accelerated aging,” *Spectrochimica Acta Part A: Molecular and Biomolecular Spectroscopy* **216**, 236–248. https://doi.org/10.1016/j.saa.2019.03.027 . Author manuscript URL (not saved): https://www.ugr.es/~grupo179/pdf/Elert%202019.pdf .
- **H4.** F. A. Pisu, M. Marceddu, P. C. Ricci, C. Melis, S. Porcu, C. M. Carbonaro and D. Chiriu (2023), “Transient absorption study on Red Vermilion darkening in presence of chlorine ions and after UV exposure,” *Journal of Photochemistry and Photobiology A: Chemistry* **435**, 114291. https://doi.org/10.1016/j.jphotochem.2022.114291 ; institutional record https://iris.unica.it/handle/11584/350159 ; publisher text https://www.sciencedirect.com/science/article/abs/pii/S1010603022005147 .
- **H5.** Kerstin Elert, Manuel Pérez Mendoza and Carolina Cardell (2021), “Direct evidence for metallic mercury causing photo-induced darkening of red cinnabar tempera paints,” *Communications Chemistry* **4**, 174. https://doi.org/10.1038/s42004-021-00610-2 ; full text https://pmc.ncbi.nlm.nih.gov/articles/PMC9814095/ .
- **H6.** The Metropolitan Museum of Art (2009), “Cinnabar: The Chinese Art of Carved Lacquer,” museum exhibition essay, journal: not applicable. https://www.metmuseum.org/exhibitions/listings/2009/cinnabar .
- **H7.** Suzi Shaw (2024; originally published in *NGV Magazine* issue 39, March–April 2023), “The craft and care of Chinese lacquer,” NGV conservation essay. https://www.ngv.vic.gov.au/essay/the-craft-and-care-of-chinese-lacquer/ .
- **H8.** 张学津、陈刚 (2023), “印谱古籍中的印油老化研究,” *文物保护与考古科学*, issue 6. Text mirror (publication attributed on page; original publisher DOI not found): https://m.fx361.com/news/2024/0111/22892619.html .
- **H9.** 冯林敏 / 北京中医药大学中医药博物馆 (2023), “可药可画的朱砂,” museum account quoting *钦定大清会典*, journal: not applicable. https://bowuguan.bucm.edu.cn/kpzl/zyyzs/83669.htm .
- **HO1.** Cleveland Museum of Art (n.d.), *Lotus Dish*, 1918.933, online catalogue; journal: not applicable. https://www.clevelandart.org/art/1918.933 . Rights https://www.clevelandart.org/open-access .
- **HO2.** The Metropolitan Museum of Art (n.d.), *Dish with long-tailed birds and hibiscuses*, 2011.120.1, online catalogue; journal: not applicable. https://www.metmuseum.org/art/collection/search/40211 .
- **HO3.** The Metropolitan Museum of Art (n.d.), *Bowl*, 13.100.141, online catalogue; journal: not applicable. https://www.metmuseum.org/art/collection/search/60917 .

---

## 2. 铜红 — Langyao 郎窑红, sacrificial red 祭红/霁红, underglaze red 釉里红, and Jun 钧红

### Physics

**Build recommendation (interpretation):** separate copper-ruby glaze from Jun's scattering, phase-separated glaze, and distinguish historical measurements from modern analogs. [C2–C4]

Metallic Cu nanoparticles in glass absorb by localized surface-plasmon resonance; larger particles add scattering. Cuvelier's radiative-transfer calculation is checked against measured spectra. [C1]

| Quantity / sample | Number and evidence status | Interpretation / limitation | Source |
|---|---|---|---|
| Modern B23 small Cu particles | **10–50 nm [M]**; mean **≈25 nm [D: TEM histogram]** | Absorbing population; historical Langyao sizes: **not found** | C1 |
| B23 large Cu particles | **≥100 nm [M]** | Scattering population | C1 |
| B23 Cu volume fraction | **≈12 × 10⁻⁴ [D: TEM sections]** | Local estimate, not elemental mass fraction | C1 |
| B23 glaze / central red-zone thickness | **0.3 mm [M]** / **150 μm [M]** | Colourless zones flank red; not a resolved particle-depth profile | C1, Fig. 2 |
| Elemental copper in historical Yuan underglaze-red shard | red **1904 ppm [M]**, orange edge **869 ppm [M]**, white **339 ppm [M]** | XRF concentration, not metallic-nanoparticle concentration | C2, Table 1 |
| Reflectance measurement of that shard | **400–700 nm [M]**, interval **10 nm [M]**, illumination/observation **45/0° [M]** | Actual measured curves in Fig. 3; missing requested spectral endpoints are not extrapolated | C2 |
| Historical Jun, Classic Liujiamen shards | glaze **above 1 mm [M]** thick | Thick spatially heterogeneous medium; not the B23 thickness | C3 |
| Cu-metal SPR in historical Jun specimen JS24 | approximately **560 nm [D]** | Absorption feature visible in measured diffuse UV–Vis spectra, Fig. 5; no digitized spectrum obtained | C4 |
| Modern ox-hair copper-red glaze, a different system | Cu₂O particles **10–30 nm [M]** | TEM/XPS-based assignment to cuprite; do not generalize Cu-metal-only results to every copper red | C5 |

**Cu₂O:** C2 finds mixed metallic/monovalent copper signatures in historical underglaze red, with metallic copper contributing the colour. C4 verifies a few metallic nanoparticles in the red areas of historical Jun even though most copper is oxidized. C5 reports a modern cuprite-dominated ox-hair system. These are sample-specific results, not mutually exclusive universal recipes. [C2, C4, C5]

**Jun red-purple on blue:** C3 documents red/purple glaze mixed with or applied over blue. C4 resolves the blue as a combination of absorption in transparent, reduced-iron-rich areas and scattering in whitish/yellowish, oxidized-iron-rich areas. Lime-rich droplets in a silica-rich matrix form by liquid–liquid separation. Copper-metal absorption then yields red over whitish areas and violet over blue. Thus “Rayleigh scattering alone makes the blue” is an incomplete production model. [C3–C4]

**White rim (脱口 / 灯草边):** for a Kangxi copper-red bowl, the British Museum explicitly explains that the glaze has receded at the rim, revealing the white porcelain body. This is evidence for glaze distribution rather than white pigment painted over red. NGA also describes flowing/pooling oxblood glaze. Relative contributions of drainage, oxidation and volatilization at a particular rim: **not found** in a spatially resolved measurement here. Do not automatically transfer the white-rim explanation to Jun's olive-green thin edges or to every sacrificial-red object. [C6; C7; C3]

**Spectral assets to obtain later (URLs only; no curves digitized or files downloaded):**

| Source | Actual measurement versus model | Where to look / coverage |
|---|---|---|
| C1 | Measured transmission / diffuse reflection compared with four-flux model | Figs. 3 and 18; exact coverage **not found**. [Paper record](https://arxiv.org/abs/1302.2302) |
| C2 | Historical Yuan red/orange measured reflectance | Fig. 3, **400–700 nm [M]**, **10 nm [M]** intervals. [Full text](https://journals.iucr.org/s/issues/2014/04/00/rv5009/index.html) |
| C3 | Historical Classic/Official Jun measured UV–visible diffuse reflectance | Figure identifier and exact coverage **not found** in accessible text. [Institutional record and manuscript link](https://upcommons.upc.edu/entities/publication/5c50278e-751b-441b-a832-ed0bc6af8380) |
| C4 | Historical Jun JS24 blue/red diffuse UV–Vis spectra | Fig. 5; integrating-sphere spot **3 × 1 mm [M]**, spectral resolution **1 nm [M]**; plotted full endpoints **not found**. The Cu SPR near **560 nm [D]** is identified in the actual spectra. [Institutional manuscript](https://upcommons.upc.edu/server/api/core/bitstreams/525370a9-cf56-474b-9bd6-179a698ea04b/content) |

### Objects

Museum dimensions below are catalogued physical measurements [M]; dates and accession identifiers are metadata, not measured optical parameters. OA image URLs are repeated in `download.txt`.

| Object and relevance | Physical scale | Image rights / attribution | Source |
|---|---|---|---|
| **Vase called “The Flame”**, Qing, early eighteenth century, NGA **1942.9.528**; Langyao/oxblood | overall **43.8 × 17.8 cm [M]** | Museum explicitly says its media is free and public domain | C7 |
| **Bowl, one of a pair**, Jin, twelfth–thirteenth century, Met **50.145.308**; Jun blue with copper-purple splashes | H **9.8 cm [M]**, diameter **22.2 cm [M]** | Public Domain; Met Open Access | C8 |
| **Dish**, Xuande mark and period, Cleveland **1989.285**; sacrificial/copper-red monochrome | diameter **15 cm [M]**, H **3.9 cm [M]** | CC0 | C9 |

For underglaze-red motif geometry, an additional OA example is the Met **Bowl with fish, 19.11**, Xuande: H **9.8 cm [M]**, diameter **20.5 cm [M]**, cobalt blue and copper red under glaze; [museum record](https://www.metmuseum.org/art/collection/search/47187). This is an alternate object, not an additional calibrated spectrum. [C10]

### Close-up look

- **Langyao:** glassy depth, multiple reds, tiny bubbles and overall fine crackle are explicitly described for “The Flame.” The museum's technical catalogue describes another oxblood vase with visible bubbles, a crackle network, red streaks and a dark glaze roll at the foot. These features should be placed within/under a glass surface, rather than painted as surface grains. [C7, C11]
- **Jun:** submillimetric cloudy areas of differing opacity, medium gloss and apparent depth; droplets, interconnected phase structures, bubbles and residual crystals contribute. The purple splash is spatially blended into a milky blue glaze. [C3]
- **Sacrificial red:** Cleveland's record describes a reflective red surface, narrow white upper edge and mottling near the foot. Universal numeric roughness/gloss values and measured ageing rates: **not found**. [C9]

### Sources — copper

- **C1.** P.-A. Cuvelier, C. Andraud, D. Chaudanson, J. Lafait and S. Nitsche (2012), “Copper red glazes: a coating with two families of particles,” *Applied Physics A* **106**, 915–929. [DOI](https://doi.org/10.1007/s00339-011-6707-3); [author manuscript record](https://arxiv.org/abs/1302.2302). Manuscript text indexed at [CiteSeer](https://citeseerx.ist.psu.edu/document?doi=1a7ab3a403e7ec5252ed9bf68417c0dffbe53557&repid=rep1&type=pdf).
- **C2.** Jian Zhu, Huiping Duan, Yimin Yang, Li Guan, Wei Xu, Dongliang Chen, Jing Zhang, Lihua Wang, Yuying Huang and Changsui Wang (2014), “Colouration mechanism of underglaze copper-red decoration porcelain (AD 13th–14th century), China,” *Journal of Synchrotron Radiation* **21**, 751–755. [DOI / full text](https://doi.org/10.1107/S1600577514009382).
- **C3.** Jiayu Hou, Trinitat Pradell, Yuan Li and Jianmin Miao (2018), “Jun ware glazes: Chemistry, nanostructure and optical properties,” *Journal of the European Ceramic Society* **38**, 4290–4302. [DOI](https://doi.org/10.1016/j.jeurceramsoc.2018.05.010); [institutional record](https://upcommons.upc.edu/entities/publication/5c50278e-751b-441b-a832-ed0bc6af8380).
- **C4.** Mingyue Yuan, Jiayu Hou, Giulio Gorni, Daniel Crespo, Yuan Li and Trinitat Pradell (2022), “Jun ware glaze colours: An X-ray absorption spectroscopy study,” *Journal of the European Ceramic Society* **42**, 3015–3022. [DOI](https://doi.org/10.1016/j.jeurceramsoc.2022.02.016); [institutional record](https://upcommons.upc.edu/entities/publication/4b405f13-52dd-466c-9b70-864c2bbf2da4).
- **C5.** Min Yang, Li Liu, Yan Liang, Lifeng Miao, Junming Wu, Ling Qiu and Naizhang Zheng (2025), “Study on the coloration mechanism of Jingdezhen ox-hair pattern copper-red glaze,” *Journal of the Ceramic Society of Japan* **133**, 670–678. [DOI](https://doi.org/10.2109/jcersj2.25097). Modern experimental specimen, not an ancient Langyao measurement.
- **C6.** British Museum (n.d.; consulted 2026), “Bowl,” **PDF,C.512**, collection catalogue and Room 95 label, journal not applicable. [Object page](https://www.britishmuseum.org/collection/object/A_PDF-C-512).
- **C7.** National Gallery of Art (n.d.; consulted 2026), “Vase, called ‘The Flame’,” collection catalogue, journal not applicable. [Object page](https://www.nga.gov/artworks/1706-vase-called-flame).
- **C8.** Metropolitan Museum of Art (n.d.; consulted 2026), “Bowl (one of a pair),” collection catalogue, journal not applicable. [Object page](https://www.metmuseum.org/art/collection/search/52663).
- **C9.** Cleveland Museum of Art (n.d.; consulted 2026), “Dish,” collection catalogue, journal not applicable. [Object page](https://www.clevelandart.org/art/1989.285).
- **C10.** Metropolitan Museum of Art (n.d.; consulted 2026), “Bowl with fish,” collection catalogue, journal not applicable. [Object page](https://www.metmuseum.org/art/collection/search/47187).
- **C11.** Virginia Bower, Josephine Hadley Knapp, Stephen Little and Robert Wilson Torchia (1998), *Decorative Arts, Part II: Far Eastern Ceramics and Paintings; Persian and Indian Rugs and Carpets*, National Gallery of Art systematic catalogue (book; journal not applicable), oxblood entries. [URL](https://www.nga.gov/sites/default/files/migrate_images/content/dam/ngaweb/research/publications/pdfs/decorative-arts-part-ii.pdf).

---

## 3. 金红 — colloidal gold, 胭脂红 enamel and gold-ruby glass

### Physics

Au nanoparticles in glass/enamel selectively absorb green-region light through surface-plasmon resonance; size, host dielectric and aggregation matter. White opacifier turns transparent ruby colour into scattering pink. [G1–G3]

**Purple of Cassius:** tin reduction of gold chloride produces colloidal Au associated with hydrated tin oxide. Qing enamels also show other routes, including arsenic-associated and tin/antimony-associated compositions; famille rose does not imply universal SnO₂. [G1, G3]

| Quantity / evidence | Number and tag | Appropriate use | Source |
|---|---|---|---|
| Typical Au-ruby glass plasmon absorption position | around **530 nm [?]** | Literature summary in the paper; not a measured universal peak for Qing objects | G1 |
| Measured absorption peak in experimental Au-ruby silicate glass with **200 ppm Au [M]** | **534 nm [M]** with **20 ppm Sn [M]**; **503 nm [M]** with **0.2 wt% Sn [M]** | Direct glass absorption measurement reported in results; modern analog, not a Qing object | G12 |
| Tin-rich Au-glass nanoparticle size | approximately **2–3 nm [D]** | Inferred from Mössbauer surface/core spectral components, not a TEM diameter | G12 |
| Synthesized aqueous Au nanoparticle sizes validated by TEM and UV–Vis | **5–100 nm [M]** | Useful original optical calibration; aqueous colloids, not Qing-glass parameters | G2 |
| Qing ruby-back specimen's optical signal | **563.5 nm [D]**, converted from measured Raman-system fluorescence displacement | Fluorescence under **514.5 nm [M]** excitation, **not reflectance or absorption** | G3, Fig. 4 |
| Historical Qing Au size, volume fraction, depth profile | **not found** | The study's proposed analogy to copper particles is an inference, not Au TEM metrology | G3 |
| Actual analysed Yongzheng bowl | Au ruby + lead-arsenate white; yellow/ruby layers | Chemical identification and macrotexture in Fig. 6, but **no numerical visible reflectance data found** | G4 |

**Faraday:** Michael Faraday's original *Philosophical Transactions* **147** (1857), pp. 145–181, DOI [10.1098/rstl.1857.0011](https://doi.org/10.1098/rstl.1857.0011), is the requested source. On pp. 146–147 he explicitly reports gold leaf transmitting green while reflecting yellow; his colloidal-gold experiments show ruby, violet and blue dispersed-gold preparations and their light scattering. These are qualitative observations, not modern calibrated spectra. Gold leaf's green transmission must not be used as the transmission spectrum of spherical ruby-glass nanoparticles. [G5]

| Spectral source | What is actually available | Limit |
|---|---|---|
| G1, Ruivo et al. | UV–visible optical absorption measured with a spectrophotometer on experimental Au glass; article discusses thermal striking | Exact figure identifier and complete wavelength coverage **not found** in accessible text; non-Chinese analog, not a Qing-object spectrum |
| G2, Haiss et al. | Fig. 4b explicitly compares measured absorbance and theory for diameter **20.4 nm [M]** aqueous Au particles; Fig. 5 compares measured and calculated SPR peak versus size | No measured spectrum for historical glass; exact plotted endpoints **not found** |
| G12, Haslbeck et al. | Results explicitly report measured optical-absorption maxima **534 nm [M]** and **503 nm [M]** for different tin concentrations in experimental Au glass | Full numerical curves and exact wavelength coverage **not found**; not historical Chinese glass |
| G3, Colomban et al. | Figs. 4–6 optical fluorescence/Raman; XRF for elements | Not a **380–780 nm** reflectance/absorption dataset. No such full measured spectrum for the listed museum objects was found |

### Objects

| Object | Physical scale | Image rights / evidential strength | Source |
|---|---|---|---|
| **Bowl with flowers**, Yongzheng mark/period, Met **65.86.12** | H **5.4 cm [M]**, diameter **11.4 cm [M]**, foot **4.4 cm [M]** | Public Domain; **this exact object was analysed**, identifying colloidal gold in the ruby enamel | G4, G6 |
| **Dish with Flowering Prunus, Pomegranate, and Pear**, Yongzheng, Walters **49.2365**; palace set | catalogue measurement **50.2 cm [M]** (page does not label the axis; diameter **[?]**) | Current museum image CC0; famille-rose classification, object-specific Au assay **not found** | G7 |
| **Dish with scene of a woman and children**, mid-eighteenth century, Met **79.2.582** | H **3.8 cm [M]**, diameter **20.2 cm [M]** | Public Domain; pink/ruby famille-rose visual reference; object-specific Au assay **not found** | G8 |

**Glass reference and explicit gap:** Corning **55.6.17 B**, Chinese bowl, possibly Beijing, nineteenth century, is specifically catalogued **gold ruby glass**, mold-blown and carved: H **8.5 cm [M]**, rim diameter **17.0 cm [M]**, foot diameter **5.9 cm [M]**. Its Qianlong mark is described as added later; it is **not evidence of a Qianlong-period palace manufacture**. Corning's image licensing is case-by-case, so an OA image is **not found**, and this object is excluded from the OA image list. [G9–G10]

Evidence counts: **one analytically confirmed Qing gold-enamel object with OA image**, **two further OA famille-rose visual references**, **one museum-catalogued gold-ruby glass carrier without confirmed OA image**, and **one OA ruby-glass candidate with colourant unconfirmed**. These are separate evidential categories; the latter candidates must not be used to infer a universal gold recipe.

Princeton's **y1936-763**, ruby-glass snuff bottle, 1780–1850, has a Public Domain download declaration and dimensions **6.8 × 4.8 × 3.2 cm [M]**, but the colourant is not specified; chemical confirmation of Au and an extractable image URL were **not found**. It is a candidate visual reference only. [G11]

### Close-up look

- **Famille-rose gold red:** smooth vitreous enamel, transparent ruby accents and milky pink mixtures. The studied Met bowl's Fig. 6 records separate coloured layers, tonal variation, and traces of other colours inside small enamel passages. Its pink is a scattering/absorbing mixture rather than simply a less saturated uniform shader. [G4]
- **Gold-ruby glass:** Corning describes minute bubbles and larger impurities, with carved landscape, flowers and pheasant; red optical path length changes through its rim, relief and body. The latter path-length effect is a rendering inference, not measured spectral data for the bowl. [G9]
- **Ageing:** numeric surface roughness, gloss, abrasion/pitting dimensions and object-specific ageing rates for these gold-red examples: **not found**. Do not add generic heavy crackle to Qing gold enamel without a close-up reference. [Research limitation]

### Sources — gold

- **G1.** Andreia Ruivo, Cristina Gomes, Augusta Lima, Maria Luísa Botelho, Rita Melo, Ana Belchior and António Pires de Matos (2008), “Gold nanoparticles in ancient and contemporary ruby glass,” *Journal of Cultural Heritage* **9**, e134–e137. [DOI](https://doi.org/10.1016/j.culher.2008.08.003); [institutional bibliography](https://novaresearch.unl.pt/en/publications/gold-nanoparticles-in-ancient-and-contemporary-ruby-glass/).
- **G2.** Wolfgang Haiss, Nguyen T. K. Thanh, Jenny Aveyard and David G. Fernig (2007), “Determination of size and concentration of gold nanoparticles from UV–vis spectra,” *Analytical Chemistry* **79**, 4215–4221. [DOI](https://doi.org/10.1021/ac0702084); [PubMed record](https://pubmed.ncbi.nlm.nih.gov/17458937/).
- **G3.** Philippe Colomban, Hui Tang and Gulsu Simsek-Franci (2025), “Non-Invasive Study of Gold Nanoparticles in Famille rose and Ruby-Back Qing Porcelain by Luminescence, Low-Wavenumber Raman Scattering and pXRF,” *Applied Sciences* **15**, 12265. [DOI / full text](https://doi.org/10.3390/app152212265).
- **G4.** Julie Bellemare, Federico Carò and Karen Stamm (2023), “Persimmon and Peonies: Orange-Colored Glass and Enamels from the Qing Imperial Workshops,” *Metropolitan Museum Journal* **58**, 96–106. [DOI](https://doi.org/10.1086/728880); [institutional article page](https://www.metmuseum.org/met-publications/bellemarecarostamm-metropolitan-museum-journal-v-58-2023); [article URL](https://resources.metmuseum.org/resources/metpublications/pdf/BellemareCaroStamm_Metropolitan_Museum_Journal_v_58_2023.pdf).
- **G5.** Michael Faraday (1857), “The Bakerian Lecture: Experimental Relations of Gold (and Other Metals) to Light,” *Philosophical Transactions of the Royal Society of London* **147**, 145–181. [DOI](https://doi.org/10.1098/rstl.1857.0011); [text PDF URL, not downloaded](https://www.fcn.unp.edu.ar/quimicainorganica/wp-content/uploads/Faraday_1857.pdf).
- **G6.** Metropolitan Museum of Art (n.d.; consulted 2026), “Bowl with flowers,” collection catalogue, journal not applicable. [Object page](https://www.metmuseum.org/art/collection/search/42319).
- **G7.** Walters Art Museum (n.d.; consulted 2026), “Dish with Flowering Prunus, Pomegranate, and Pear,” collection catalogue, journal not applicable. [Object page](https://art.thewalters.org/object/49.2365/).
- **G8.** Metropolitan Museum of Art (n.d.; consulted 2026), “Dish with scene of a woman and children,” collection catalogue, journal not applicable. [Object page](https://www.metmuseum.org/art/collection/search/51112).
- **G9.** Corning Museum of Glass (n.d.; consulted 2026), “Bowl,” **55.6.17 B**, collection catalogue, journal not applicable. [Object page](https://glasscollection.cmog.org/objects/24381/bowl).
- **G10.** Corning Museum of Glass (n.d.; consulted 2026), “Rights & Reproductions,” institutional rights policy, journal not applicable. [URL](https://info.cmog.org/rights-and-reproductions).
- **G11.** Princeton University Art Museum (n.d.; consulted 2026), “Ruby glass snuff bottle with auspicious animal's relief,” collection catalogue, journal not applicable. [Object page](https://artmuseum.princeton.edu/art/collections/objects/20242).
- **G12.** S. Haslbeck, K.-P. Martinek, L. Stievano and F. E. Wagner (2005 nominal issue; published online 2006), “Formation of gold nanoparticles in gold ruby glass: The influence of tin,” *Hyperfine Interactions* **165**, 89–94. [DOI / publisher record](https://doi.org/10.1007/s10751-006-9246-0); [author-uploaded original article text](https://www.researchgate.net/publication/226058879_Formation_of_gold_nanoparticles_in_gold_ruby_glass_The_influence_of_tin). Note publisher distinguishes issue date and online publication date.

---

## 4. 铁红 — iron-oxide reds

### Physics

**Build several surfaces around the same chromophore.** Hematite, α-Fe₂O₃, colors red overglaze, red mineral paint and many oxidized ceramic bodies, but their scattering matrices and surface finishes differ. Sherman and Waite attribute the red/yellow colors of iron oxides to magnetically intensified Fe³⁺ ligand-field and paired-ion excitations; their lowest ligand-to-metal charge transfer lies in the ultraviolet. A simple semiconductor cutoff alone therefore misses important visible structure. [I1]

| Parameter / evidence | Value and qualification | Source |
|---|---|---|
| Measured hematite optical absorption and diffuse reflectance | Spectra over **200–2000 nm [M]**, including the requested **380–780 nm [D: subset]**; plotted spectra, not an acquired numeric array | [I1] |
| Linshui red overglaze crystallites | Mean diameter about **30 nm [M: XRD estimate reported by authors]**; distorted hematite lattice; optical diffuse reflectance used | [I2] |
| Particle morphology comparison | Platelets approximately **3 µm [M]** across and **0.5 µm [M]** thick; diffuse-reflectance feature shift **40 nm [M]** relative to conventional particles. This is a morphology-specific experiment, not a universal size-to-color law | [I3] |
| Nanopowder hue trend | Trend reverses around diameter **80 nm [M: experimental trend]**; multiple mechanisms needed rather than a monotonic particle-size rule | [I4] |
| Direct spectrum for red pigment versus specular hematite | Morris et al., Fig. 11: measurements **350–2500 nm [M]**; displayed/discussed **400–1000 nm [M]**. HMS3 pigment mean diameter **0.14 µm [M, prior characterization]** versus specular HMMG1 fraction **500–1000 µm [M: sieve bounds]** | [I5] |
| Independent porcelain coating reference | Kim et al., Fig. 6: reflectance rises across **560–650 nm [M: reported interval]**; Fig. 3 SEM shows **1–3 µm [M]** platelet/polyhedral surface structures. Experimental high-fired coating, **not** a historical Fanhong recipe | [I6] |
| Machine-readable spectral lead | USGS measured reflectance library; GDS27 is XRD-confirmed hematite; reported aggregates about **200 µm [M]**, composed of grains **2–3 µm [M]**. List library URLs only; data not fetched | [I7] |

**矾红 / Fanhong.** Hao et al. identify hematite in historical Linshui overglaze. Duan et al. find hematite in red imperial overglaze, with maghemite and magnetite associated with orange-red and dark-red samples; they observe nanometric spheroids versus lamellar structures. Thus “iron red” does not license assigning pure hematite to every orange/brown patch, and these pigment phases should not be confused with copper-red underglaze. [I2, I8]

**Forbidden City walls: exact evidence, with scope.** Zhang, Wu and Wang analyze samples and colors at the Forbidden City and Beijing temple sites by Raman, FTIR and XRD. White plaster contains calcium carbonate; red plaster contains iron oxide and calcium carbonate; red slurry contains iron oxide, calcium carbonate, gypsum, and traditional glutinous-rice binder or modern polymer. This supports **iron-oxide red in the examined wall systems**. It does not demonstrate identical pigment in every wall, period or restoration, and is not evidence that all palace red surfaces are vermilion. [I9]

**Red earthenware.** At Fenghuangzui, Raman and XAFS identify poorly crystalline hematite in red paint/slip; different pastes and surface treatments matter. This is direct Chinese archaeological evidence, but does not chemically identify the Met jar below. [I10]

**Spectral links:** [Sherman–Waite original paper](https://msaweb.org/AmMin/AM70/AM70_1262.pdf); [Hao original article](https://doi.org/10.1002/jrs.4447); [Morris Fig. 11 and supporting information](https://doi.org/10.1029/2019JE006324); [Kim Fig. 6](https://journal.mrs-k.or.kr/articles/xml/e2dQ/); [USGS GDS27 sample](https://pubs.usgs.gov/of/2003/ofr-03-395/DESCRIPT/M/hematite_gds27.html); [current USGS library/data landing page](https://www.usgs.gov/labs/spectroscopy-lab/usgs-spectral-library). Exact per-wavelength values were **not found / not transcribed** in this brief. The Morris display does not establish the short-wave endpoint of the requested interval; use the wider Sherman/USGS source rather than extrapolating it.

### Objects

| Museum object / use | Physical scale | Image rights and identification limit |
|---|---|---|
| Met, *Vase in Meiping Shape*, accession 79.2.811; catalogue: porcelain with iron-red glaze, Jingdezhen | Height **12.7 cm [M: museum catalogue]** | Public Domain / Met Open Access; compact monochrome form for studying the glaze. Specific mineral/particle analysis of this vessel: **not found**. [IO1] |
| Saint Louis Art Museum, *Dish with Design of Dragons, Phoenixes, and Flaming Pearl*, accession 201:1977; catalogue explicitly says overglaze iron-red enamel | Diameter **18 cm [M: museum catalogue]** | Public Domain; useful for separating thin red painted decoration from reflective white glaze. Object-specific spectral analysis: **not found**. [IO2] |
| Met, *Jar (Guan)*, accession 1992.165.14; catalogue: painted earthenware, Majiayao/Machang | Height **38.5 cm [M]**, width excluding handles **39 cm [M]** | Public Domain / Met Open Access. **Appearance/scale comparator for earthenware only**: chemical identity of this jar’s red body/paint **not found**. [IO3] |

### Close-up look

For enamel, compare smooth glaze highlights with pigment-rich painted areas; the museum medium specifies which surface is overglaze, but measured roughness and BRDF are **not found**. For wall material, use a particulate paint/plaster model based on the measured carbonate/iron-oxide/binder system; microcracks, abrasion, local dirt and repair boundaries are variables to validate in an actual wall photograph, not universal properties proved by chemistry. For pottery, preserve pores, inclusions and any slip/body distinction rather than applying a glass topcoat. These are **rendering inferences**, grounded in the respective substrates and microscopy, not measured shader parameters. [IO1–IO3, I6, I9, I10]

Hematite particle coarsening and phase variation can change color; do not interpret every dark region as aged pigment. Quantified ageing rates, surface roughness, gloss units and site-specific weathering spectra: **not found**. [I3, I4, I8]

### Sources

- **I1.** David M. Sherman and T. David Waite (1985), “Electronic spectra of Fe³⁺ oxides and oxide hydroxides in the near IR to near UV,” *American Mineralogist* **70**, 1262–1269. [Original article URL](https://msaweb.org/AmMin/AM70/AM70_1262.pdf). Do not attach the unrelated DOI that appears in some institutional metadata.
- **I2.** Wentao Hao, Wugan Luo, Yue Chen and Changsui Wang (2014), “Micro-analysis on Chinese over-glaze red decoration of Linshui Kiln from Jin dynasty (1115–1234 AD),” *Journal of Raman Spectroscopy* **45**, 224–227. [DOI](https://doi.org/10.1002/jrs.4447). Publisher abstract and indexed text consulted; complete optical table **not found**.
- **I3.** Jun Wang, William B. White and James H. Adair (2005), “Optical Properties of Hydrothermally Synthesized Hematite Particulate Pigments,” *Journal of the American Ceramic Society* **88**, 3449–3454. [DOI](https://doi.org/10.1111/j.1551-2916.2005.00643.x).
- **I4.** Morgane Gerardin, Nicolas Holzschuch, Alain Ibanez, Bernard Schmitt and Pauline Martinetto (2021), “Influence of micro-structural features on the colour of nanocrystallised powders of hematite and visible-NIR reflectance spectra simulations,” *Journal of the International Colour Association* **26**. [Publisher](https://www.aic-publishing.org/ojs/index.php/JAIC/article/view/238), [DOI](https://doi.org/10.82019/JAIC.2606).
- **I5.** R. V. Morris et al. (2020), “Hydrothermal Precipitation of Sanidine (Adularia) Having Full Al,Si Structural Disorder and Specular Hematite at Maunakea Volcano (Hawai‘i) and at Gale Crater (Mars),” *Journal of Geophysical Research: Planets* **125**, e2019JE006324, section 3.6 and Fig. 11. [DOI](https://doi.org/10.1029/2019JE006324).
- **I6.** Kyung-Nam Kim, Hyun Park and Il-An Won (2017), “Characterization of Hematite Red Pigment for Porcelain Surface Coating,” *Korean Journal of Materials Research* **27**, 206–210. [DOI](https://doi.org/10.3740/MRSK.2017.27.4.206), [full HTML](https://journal.mrs-k.or.kr/articles/xml/e2dQ/). The abstract calls the red rise an “absorption band”; the body describes the rise of **reflectance**, which is the interpretation used here.
- **I7.** R. N. Clark et al. (2003), *USGS Digital Spectral Library splib05a*, Open-File Report 03-395, sample “Hematite GDS27.” [Sample URL](https://pubs.usgs.gov/of/2003/ofr-03-395/DESCRIPT/M/hematite_gds27.html). Current library: R. F. Kokaly et al. (2017), *USGS Spectral Library Version 7*, *USGS Data Series* 1035, [DOI](https://doi.org/10.3133/ds1035); dataset [DOI](https://doi.org/10.5066/F7RR1WDJ).
- **I8.** Hongying Duan, Ming Guan, Yujie Yang, Jianxin Jiang and Wei Qian (2024), “Non-destructive identification of iron oxide crystals in 15th century A.D. Chinese imperial red overglaze decoration,” *Journal of Archaeological Science: Reports*, article 104733. [DOI](https://doi.org/10.1016/j.jasrep.2024.104733). Publisher abstract/preview consulted.
- **I9.** 张涛 / Tao Zhang, 吴玉清 / Yu-qing Wu and 王菊琳 / Ju-lin Wang (2017), “北京宫殿、坛庙古建筑‘宫墙红’的组成及色差 / Constituent and Color Difference of ‘Red Wall’ at the Beijing Ancient Palace and Temple Buildings,” *表面技术 / Surface Technology* **46**, 18–26. [DOI](https://doi.org/10.16490/j.cnki.issn.1001-3660.2017.02.003), [publisher abstract](https://www.surface-techj.com/CN/10.16490/j.cnki.issn.1001-3660.2017.02.003).
- **I10.** Tao Li, Guoyuan Li, Zongyang Li, Tengfei Wu, Hui Tian, Siwei Shan and Lihua Wang (2022), “Surface treatment of red painted and slipped wares in the middle Yangtze River valley of Late Neolithic China: multi-analytical case analysis,” *Heritage Science*. [DOI](https://doi.org/10.1186/s40494-022-00824-0), [publisher](https://www.nature.com/articles/s40494-022-00824-0). Indexed publisher abstract consulted; full page access failed.
- **IO1.** Metropolitan Museum of Art (undated collection record, consulted October 2026), “Vase in Meiping Shape,” accession 79.2.811; institutional catalogue, journal: not applicable. [Object page](https://www.metmuseum.org/art/collection/search/51142).
- **IO2.** Saint Louis Art Museum (undated collection record, consulted October 2026), “Dish with Design of Dragons, Phoenixes, and Flaming Pearl,” accession 201:1977; institutional catalogue, journal: not applicable. [Object page](https://www.slam.org/collection/objects/8543/).
- **IO3.** Metropolitan Museum of Art (undated collection record, consulted October 2026), “Jar (Guan),” accession 1992.165.14; institutional catalogue, journal: not applicable. [Object page](https://www.metmuseum.org/art/collection/search/44690).

---

## 5. 铅丹 — red lead, Pb₃O₄

### Physics

Red lead/minium is a mixed-valence lead oxide containing Pb(II) and Pb(IV). Its visible electronic absorption produces orange red. Amat et al. compare theory and experiment and summarize earlier gap values; Panetta et al. provide a directly traceable optical-edge experiment on a modern film. [L1, L11]

| Quantity | Value | Status / use | Source |
|---|---:|---|---|
| Primary optical gap from absorption onset | **2.138 ± 0.004 eV [D]** | Derived by authors from measured Kubelka–Munk response; modern sintered film, Table 1 | L11 |
| Indirect / direct Tauc fits of the same experiment | **2.134 ± 0.004 eV [D]** / **2.221 ± 0.001 eV [D]** | Different fitting assumptions; indirect fit agrees better with onset, not independent universal gap constants | L11 |
| Film thickness / coherent crystallite size | **≈5 µm [M]** / **28 ± 1 nm [D]** | Profilometry / Scherrer estimate; coherent domain is not aggregate size | L11 |
| Earlier gap range summarized by Amat et al. | **2.1–2.3 eV [?]** | Secondary-reported; original experiments not independently checked | L1 |
| Minium paint reflectance rise | ≈535 nm [M] | Identified reference pigment-paint spectrum | H2, Table 5 |
| Minium paint reflectance inflection | ≈560 nm [M] | Contrast with cinnabar's later edge | H2, Table 5 and Fig. 8 |
| Surface coating particles on HKU sample 84 | Up to 10 μm [M] | SEM includes a mixture interpreted as red lead, carbonate and barite; not a pure minium size distribution | L2, Fig. 3c |
| Tabulated reflectance or absorption for a historical Chinese red-lead object across the target interval | **not found** | Reference-paint FORS covers **300–900 nm [M]**; preserve binder/substrate context | H2 |
| Optical spectrum directly measured on an identified 万年红 flyleaf | **not found** | Do not substitute a paint spectrum without labelling the transfer | — |

Panetta et al., Fig. 3, publishes a Kubelka–Munk optical-edge function over approximately **560–650 nm [D: plotted axis]**, not an absolute absorption coefficient or a full-visible paper spectrum. [L11]

**万年红纸 evidence:** Querner, Beenk and Linke document red lead, water and vegetable glue brushed onto Ming–Qing endsheets. Undamaged late-Qing HKU sheets were lead-rich; insect-damaged orange substitutes lacked detectable lead. Historical insecticidal intent does not establish universal protection, and EDS alone does not establish the precise Pb oxide phase. [L2]

The Palace Museum independently states that Ming–Qing 万年纸 from the Nanhai/Foshan region was coated with orange-red 铅丹, used for book front/back matter and for insect protection; it cites a *梦溪笔谈* edition dated 1631 with such lining. The National Library of China describes red-lead paper placed at the front and back flyleaves and the intention of killing insects after ingestion. [L3, L4]

### Objects

These museum objects have **identified red lead, catalogue dimensions and explicitly open images**. Their pigment layers are mixed, fragmentary or repainted; the evidence does not identify all red areas as pure minium. For 万年红 endsheets specifically, a page-scale museum reference meeting the same requirements remains **not found**.

| Museum object | Object-specific material evidence | Physical scale | Open image / licence |
|---|---|---|---|
| **Ajita, the Fifteenth Venerable Luohan**, Smithsonian National Museum of Asian Art, F1917.334 | Red lead identified by **XRD**; other reds are also recorded. [L6, Appendix 5, Table A5.1] | Image area **127 × 62.4 cm [M]** | [Object](https://asia.si.edu/explore-art-culture/collections/search/edanmdm%3Afsg_F1917.334/); **CC0** [L8] |
| **Buddha, probably Amitabha**, Met 19.186 | Orange-red robe/shawl areas contain **red lead + cinnabar**; investigated by diffraction and XRF. [L7] | **96.5 × 68.6 × 57.1 cm [M]** | [Object](https://www.metmuseum.org/art/collection/search/42163); **Public Domain / Met Open Access** [L9] |
| **Buddha**, Walters 25.9 | A pink layer contains **white lead + red lead**; repeated repainting is documented. [L7] | **105.1 × 73.1 × 55.1 cm [M]** | [Object](https://art.thewalters.org/object/25.9/); **CC0** [L10] |

For the endsheet application, HKU samples discussed by Querner et al. have analytical subsamples **1 × 1 cm [M]**, which are **not whole-page dimensions**. Book/page dimensions and a standalone open image suitable for scale validation: **not found**. [L2] The Palace Museum's cited edition of *梦溪笔谈* supplies historical use, but exact present accession, page dimensions and open image were **not found**. [L3]

### Close-up look

The sculpture study records fragmentary paint, repeated repainting and paint-layer cross-sections, including Walters Fig. S23. Use these as stratigraphy and ageing references, rather than uniform clean-pigment standards. [L7]

Orange-red 万年红 coatings can show uneven brushing, uncoated margins and coating crystals mixed with fillers. Quantitative surface gloss and roughness are **not found**. [L2]

Ageing is chemically diverse. Fleming documents blackened red lead on a Dunhuang painting; Amat et al. discuss a separate oil-paint bleaching mechanism involving reduction of Pb(IV), lead carbonates and soaps, potentially creating surface protrusions. An oil-paint ageing recipe should not automatically be applied to a glue-coated flyleaf. [L1, L5; last sentence is a modelling inference]

### Sources

- **L1.** Anna Amat, Francesca Rosi, Costanza Miliani, Paola Sassi, Marco Paolantoni and Simona Fantacci (2020), “A combined theoretical and experimental investigation of the electronic and vibrational properties of red lead pigment,” *Journal of Cultural Heritage* **46**, 374–381. https://doi.org/10.1016/j.culher.2020.04.014 ; inspected publisher text https://www.sciencedirect.com/science/article/pii/S1296207420303563 .
- **L2.** Pascal Querner, Jody Beenk and Robert Linke (2022), “The Analysis of Red Lead Endsheets in Rare Books from the Fung Ping Shan Library at the University of Hong Kong,” *Heritage* **5**, 2408–2421. https://doi.org/10.3390/heritage5030125 ; https://www.mdpi.com/2571-9408/5/3/125 . CC BY article.
- **L3.** 故宫博物院 (2017 website entry; personal author not credited), “万年纸,” museum glossary, journal: not applicable. https://www.dpm.org.cn/lemmas/242183.html .
- **L4.** 中国国家图书馆 / 中国古籍保护网 (2017; personal author/title not exposed in retrieved text), article on traditional insect-control methods, journal: not applicable. https://www.nlc.cn/pcab/gjbhzs/kj/20170713_151836.shtml . Bibliographic title beyond institution and subject: **not found**; use L2–L3 as stronger citations.
- **L5.** Lore Erwine Fleming (1997), “Paintings on Silk and Paper from Dunhuang at the British Museum: Conservation Methods,” in Neville Agnew, ed., *Conservation of Ancient Sites on the Silk Road*, Getty Conservation Institute, pp. 105–111; journal: not applicable. Fig. 7, p. 107. https://www.getty.edu/publications/resources/virtuallibrary/0892364165.pdf . No file saved. Candidate object page https://www.britishmuseum.org/collection/object/A_1919-0101-0-159 .

- **L6.** Jennifer Giaccai, Jeffrey Joseph and John Winter (2021), “Pigments in Song and Yuan Paintings from the Freer Gallery of Art,” and Appendix 5 “Complete Analysis Results,” in Blythe McCarthy and Jennifer Giaccai, eds., *Scientific Studies of Pigments in Chinese Paintings*, Archetype / Smithsonian; journal: not applicable. https://doi.org/10.5479/10088/111861 ; repository record https://repository.si.edu/items/10dc00d7-9cd5-47dc-89eb-e89463d0d88d . Source text inspected via https://repository.si.edu/bitstream/handle/10088/111861/SSOPICP_Online_wCover_092023.pdf . No PDF saved. Use p. 115 / Table A5.1 for Ajita's XRD identification.
- **L7.** Donna Strahan and Blythe McCarthy (publication year **not found**), “Construction from the Inside Out: Early Chinese Lacquer Buddha Fabrication,” National Museum of Asian Art conservation research essay; journal: not applicable. [Museum URL](https://asia.si.edu/research/essays/construction-from-the-inside-out-early-chinese-lacquer-buddha-fabrication/); [archived original text inspected](https://asia-archive.si.edu/essays/construction-from-the-inside-out-early-chinese-lacquer-buddha-fabrication/), “Pigment” subsection and Fig. S23.
- **L8.** National Museum of Asian Art (n.d.), *Ajita, the fifteenth venerable luohan*, F1917.334, collection record; journal: not applicable. https://asia.si.edu/explore-art-culture/collections/search/edanmdm%3Afsg_F1917.334/ . Scale and CC0 confirmed independently by https://collections.si.edu/search/detail/edanmdm%3Afsg_F1917.334?print=yes .
- **L9.** The Metropolitan Museum of Art (n.d.), *Buddha, probably Amitabha*, 19.186, collection record; journal: not applicable. https://www.metmuseum.org/art/collection/search/42163 .
- **L10.** The Walters Art Museum (n.d.), *Buddha*, 25.9, collection record; journal: not applicable. https://art.thewalters.org/object/25.9/ .

- **L11.** Riccardo Panetta, Simone Quaranta and Alessandro Latini (2018), “Screen Printed Pb₃O₄ Films and Their Application to Photoresponsive and Photoelectrochemical Devices,” *Materials* **11**, 1189. [DOI](https://doi.org/10.3390/ma11071189); [full text](https://pmc.ncbi.nlm.nih.gov/articles/PMC6073417/); [institutional record](https://iris.uniroma1.it/handle/11573/1130206). Optical data Fig. 3, fits Table 1.

---

## 6. Organic reds for silk and paper

### Physics

**Build direction (modelling judgment):** specify the molecular absorber, solvent/extraction state, mordant and support separately. The experiments below demonstrate that solution, lake and dyed-fibre spectra cannot be interchanged. [O1–O5, O16]

| Colourant | What physically produces the colour; important qualification | Measured spectral evidence and conditions |
|---|---|---|
| 红花 / safflower | Carthamin is the red component; other safflower components are yellow. The changing protonation states have different absorption. [O1,O7] | Otsu and Hida measure aqueous extracts over **400–600 nm [M]**, investigating **pH 1.77–11.60 [M]**; the near-neutral component pair has reconstructed maxima **520 and 500 nm [D]**. Principal-component separation is an analysis of measurements, not proof of unique molecular assignments. Full **380–780 nm** curve: **not found** in this source. The PDF's Table 1 and Fig. 1 are the usable curve/table locators. [O1] |
| 茜草 / madder | Alizarin and purpurin are hydroxyanthraquinones; lake formation coordinates the dye with metal ions. These measured references are *Rubia tinctorum*/pure compounds; they must not be equated to every Chinese *Rubia* species. [O2] | **Ethanol**, pH **not found**: alizarin **430 nm [M]**, its alum lake **500 nm [M]**; purpurin **455, 486, 520 nm [M]**, its alum lake **508, 544, 578 nm [M]**; Fig. 3a,b. Exact plotted scan limits: **not found** in the text inspected. UV–Vis resolution **2 nm [M]**. [O2] |
| 苏木 / sappanwood | **Brazilin is colourless**; oxidation produces coloured **brazilein**. Protonation/deprotonation changes the conjugated absorber. Do not label the red absorber simply “brazilin.” [O3] | Isolated brazilein in **water**, Fig. 1b: **450 nm [M]** predominates at **pH 3 [M]** (yellow); **450, 510, 544 nm [M]** appear at **pH 7 [M]** (orange); **544 nm [M]** predominates at **pH 9 [M]** (red). Scanned **300–700 nm [M]**; **700–780 nm: not found**. These are solution spectra, not a measured mordanted-silk BRDF. [O3] |
| 紫胶 / lac | Soluble lac dye contains anthraquinone **laccaic acids**, principally A and B; it is chemically distinct from cochineal/carminic acid and from the resinous shellac fraction. Metal binding and deprotonation shift the visible absorption. [O4] | Chairat et al. measured Thai and commercial lac plus isolated A/B versus metal concentration and **pH 2.5–11 [M]**; both increasing pH and adding alum/Ni ions red-shift absorption. Thai lac has a visible band at **487 nm [?]** in the paper's discussion; exact pH for that individual number: **not found** in accessible excerpt. Full numerical curve/scan limits: **not found**. Reported older values **500, 530 nm [?]** in ethanol and **490 nm [?]** in water are citations to earlier work, **not new measurements by Chairat et al.** [O4] |
| 胭脂虫 / cochineal | The principal absorber is **carminic acid**; metal complexes/lakes have a different spectrum from the free acid. [O5,O6] | Favaro et al., Fig. 3: dilute **aqueous** carminic acid, concentration **<5 × 10⁻⁵ mol dm⁻³ [M]**, maxima shift from **490 nm at pH 2 [M]** to **567 nm at pH 12 [M]**; whole investigated acidity range **pH 0.9–13 [M]**. Spectral scan endpoints: **not found** in inspected text. [O5] |

**A usable full-visible reflectance source:** Fonseca et al. measured historical-recipe madder and cochineal lakes/carmine in linseed oil, gum Arabic, egg yolk and beeswax, acquired **350–2500 nm [M]** and analysed **350–1000 nm [M]**, so this includes the requested visible band. Fig. 2c/Table 1 give madder features **469–481, 500–509, 538–548 nm [M]** across recipes, with a calcium-rich outlier. Fig. 4 shows tin carmine C-Sn at **485 nm (shoulder), 520 and 555 nm [M]**. These are recipe-specific reflectance minima/apparent-absorption features, not solution extinction coefficients or evidence for Chinese textile mordants. Machine-readable spectral samples: **not found**; the article says datasets are available on request, which was not attempted. [O6]

**Chinese madder is not automatically an alizarin-dominant material.** Mouri and Laursen compared plant specimens and dyed textile fibres by HPLC-PDA-MS: *R. tinctorum* textiles were dominated by alizarin, whereas *R. cordifolia* and *R. peregrina* generally contained purpurin, munjistin and pseudopurpurin with little/no alizarin. The latter species were not reliably distinguishable from each other by that profile. [O16] Accordingly, the pure-alizarin and European-madder measurements above are constituent/comparison spectra; they are not a measured spectrum for all Chinese 茜草.

**Historical use and what remains unidentified**

| Requested use | Supported conclusion | Boundary of evidence |
|---|---|---|
| Wedding silks | China National Silk Museum identifies safflower and sappanwood as major Qing red dyestuffs and connects red dress with celebration/marriage. Safflower produces the brighter reds; sappanwood often supplies red-browns, purples and compound shades, with alum or iron mordants. [O7] | This supports a historically plausible **safflower-red silk** build; it does **not** identify the dye in a particular wedding garment from its photograph. |
| Qing court silks, analytical anchor | Jin et al. analyse red areas of a Qianlong kesi robe at Beijing Art Museum by HPLC-DAD-MS, identifying safflower alone in A/B and safflower + Chinese cork tree in C. Extract absorption maxima: A **513, 532 nm [M]**; B **520 nm [M]**; C **371, 389, 520 nm [M]**. [O8] | A specific dye-confirmed object, but the source inspected supplies **no openly licensed museum image or physical dimensions: not found**. Extraction spectra are not intact-textile reflectance. |
| Red lanterns | A historical lantern-specific identification or recipe connecting its covering to one of the requested organic dyes: **not found**. | Do not assert that all historical red lanterns were safflower-, madder-, or sappan-dyed; the red covering requires object/date/locality evidence. |
| 春联 paper | A primary source proving one universal traditional spring-couplet dye: **not found**. | Separate the use of red paper from identification of its colourant. |
| Red paper more generally | Beijing University of Chinese Medicine Museum's Feng Linmin cites Wang Zongmu's Ming *Jiangxi dazhi · Chushu* for sappanwood red paper, and Qing *Da Qing huidian* for papermaking/dyeing supplies including sappanwood and alum. [O9] | A museum's **secondary historical report**, not direct inspection of those original archival editions; it does not specify lanterns or 春联. |
| Lac versus cochineal in Chinese textiles | Han's analytical study reports lac in object NMS-6; the brown ground of dancer's skirt NMS-7 contains carminic acid, ellagic acid and probable magenta. [O10] | The author explicitly leaves the insect species for the carminic-acid dye unresolved between American *Dactylopius* and *Porphyrophora*. Neither the word 胭脂 nor a crimson photograph proves American cochineal. |

### Objects

The following are **surface/scale references**. Their catalogue records do **not** report a dye identification; exact colourant for each: **not found**. Physical dimensions are museum catalogue measurements [M], not measurements inferred from the photographs. Digital image colour management, illumination, yarn diameter and BRDF parameters: **not found**.

| Object | Date / material and physical size | Image rights and role |
|---|---|---|
| **Woman's robe**, Cooper Hewitt, **1931-4-63**; [museum record](https://www.si.edu/object/womans-robe%3Achndm_1931-4-63), [catalogue](https://collection.cooperhewitt.org/objects/18318435/) | c. **1860 [?]** museum dating; red voided silk velvet on yellow satin, red velvet sleeve bands on blue satin; **113 × 128.3 cm [M]**. [O11] | Smithsonian explicitly **CC0**. Direct original museum image URL recovered through its Commons metadata: `https://images.collection.cooperhewitt.org/49902_433cd9420acd9253_x.jpg`. Mirror: `https://upload.wikimedia.org/wikipedia/commons/a/a1/Woman%27s_Robe_%28China%29%2C_ca._1860_%28CH_18318435%29.jpg`. Strong reference for red pile versus smooth ground. [O11,O12] |
| **Wedding Altar Frontal with Design of Peony and Lotus Scrolls, Symbols for Double Happiness, and Meandering Swastika Fret Border**, Saint Louis Art Museum **38:1917**, [object](https://www.slam.org/collection/objects/10902/) | Mid/late **18th century [?]** museum dating; cut silk velvet, **82.2 × 92.7 cm [M]**. [O13] | Museum **Public Domain**; direct image-file URL: **not found**. Particularly valuable because the museum explicitly describes formerly red pile now faded to tawny brown in light-exposed areas. [O13] |
| **Manchu Woman's Informal Robe**, Met **47.136.1**, [object](https://www.metmuseum.org/art/collection/search/69864) | Late **19th–early 20th century [?]** museum dating; silk, **144.8 × 206.1 cm [M]**. [O14] | Museum **Public Domain**; [direct front image](https://collectionapi.metmuseum.org/api/collection/v1/iiif/69864/111476/main-image). Dye identity untested in catalogue; retain as supplementary textile construction/scale reference. [O14] |

### Close-up look

**Velvet:** Cooper Hewitt explicitly describes red voided velvet over yellow satin, with a contrasting blue ground at the sleeve bands. Thus the material needs raised pile, cut/voided edges and a distinct underlying weave rather than a smooth red coating. Directional pile sheen is a rendering inference from that structure, **not** a measured roughness or anisotropy value. [O11]

**Ageing:** the SLAM wedding frontal provides unusually useful object-specific evidence: its exposed red pile faded to tawny brown, while its ribbed ground and green pile remain separate structures. Do not recolour the whole textile uniformly. [O13] Favaro et al. experimentally found photobleaching for free carminic acid and its lake; gum Arabic altered the two systems differently, showing that “organic red” cannot have a universal fading rate. [O5] Tamburini and Dyer's silk reference comparison identifies safflower and sappanwood among the most light-sensitive dyes tested; the paper includes spectra, photographed references and artificial-ageing comparisons. [O15] Ageing rate in natural museum conditions for these specific objects: **not found**.

**Build recommendation:** begin with a historically specified safflower-red silk surface and a second red velvet variant; validate weave/pile against the museum references, and validate absorption separately against a recreated dyed swatch. A “traditional red lantern” or “traditional 春联 red paper” shader should remain provisional until a period-specific covering or paper recipe is sourced. This is an evidence-based planning judgment, not a claim that the museum robes contain safflower.

### Sources

- **O1.** Tamako Otsu and Mitsuhiko Hida (2007), “The pH Dependence of Absorption Spectra of Carthamin in Aqueous Solution,” *Sen'i Gakkaishi* **63(8)**, 185–192. [DOI](https://doi.org/10.2115/fiber.63.185); [publisher page](https://www.jstage.jst.go.jp/article/fiber/63/8/63_8_185/_article/-char/en); [PDF URL, read through browser only](https://www.jstage.jst.go.jp/article/fiber/63/8/63_8_185/_pdf/-char/en). Table 1, Fig. 1; measurement range in §2.2.
- **O2.** S. Innocenti, M. Ricci, D. Quintero Balbas, R. Fontana, J. Striova and M. Becucci (2023), “Surface-enhanced Raman spectroscopy for madder lake detection in painting layers,” *European Physical Journal Plus* **138**, 381. [DOI/full text](https://doi.org/10.1140/epjp/s13360-023-03964-9), §2.1.2 and §3.1, Fig. 3a,b. Note: lakes' soluble fractions in ethanol, not the whole suspension.
- **O3.** Luxsika Ngamwonglumlert, Sakamon Devahastin, Naphaporn Chiewchan and G. S. Vijaya Raghavan (2020), “Color and molecular structure alterations of brazilein extracted from *Caesalpinia sappan* L. under different pH and heating conditions,” *Scientific Reports* **10**, 12386. [DOI](https://doi.org/10.1038/s41598-020-69189-3); [full text](https://pmc.ncbi.nlm.nih.gov/articles/PMC7382456/), Fig. 1b and Methods. No silk mordant inferred from this food-colorant experiment.
- **O4.** Montra Chairat, Vichitr Rattanaphani, John B. Bremner, Saowanee Rattanaphani and David F. Perkins (2004), “An absorption spectroscopic investigation of the interaction of lac dyes with metal ions,” *Dyes and Pigments* **63(2)**, 141–150. [DOI](https://doi.org/10.1016/j.dyepig.2004.02.006); [publisher text](https://www.sciencedirect.com/science/article/abs/pii/S014372080400018X).
- **O5.** Gianna Favaro, Costanza Miliani, Aldo Romani and Manuela Vagnini (2002), “Role of protolytic interactions in photo-aging processes of carminic acid and carminic lake in solution and painted layers,” *Journal of the Chemical Society, Perkin Transactions 2*, 192–197. [DOI](https://doi.org/10.1039/B104595B); [full-text URL](https://pubs.rsc.org/en/content/articlehtml/2002/p2/b104595b). Fig. 3 and “Effect of pH on the spectral characteristics of carminic acid.”
- **O6.** Beatriz Fonseca, Catherine Schmidt Patterson, Monica Ganio, Douglas MacLennan and Karen Trentelman (2019), “Seeing red: towards an improved protocol for the identification of madder- and cochineal-based pigments by fiber optics reflectance spectroscopy (FORS),” *Heritage Science* **7**, 92. [DOI/full text](https://doi.org/10.1186/s40494-019-0335-1), Experimental, Table 1, Figs. 2c and 4. These are newly measured recipe-dependent values, not the paper's separately quoted conventional textbook ranges.
- **O7.** 李永固、刘剑 (2021), “一文Vol.26｜一花一木——清代华服上的红色源头,” China National Silk Museum, museum research/public-education article, journal **not applicable**. [URL](https://www.chinasilkmuseum.com/gskt/info_319.aspx?itemid=28395).
- **O8.** Jianmei Jin, Jian Liu, Dan Wang, Suyun Gao, Feng Zhao and Yehong Wang (2022), “Reconstruction of traditional safflower (*Carthamus tinctorius* L.) dyeing and red colors in the Qing Dynasty (17th–19th century),” *Dyes and Pigments* **207**, 110697. [DOI](https://doi.org/10.1016/j.dyepig.2022.110697); [publisher](https://www.sciencedirect.com/science/article/pii/S0143720822006192). Extract-spectra values in “Dye analysis”; the Qianlong robe is at Beijing Art Museum.
- **O9.** 冯林敏 (2023), “染药并用——苏木,” Beijing University of Chinese Medicine Museum; journal **not applicable**. [URL](https://bowuguan.bucm.edu.cn/kpzl/zyyzs/81399.htm). Secondary textual historical evidence with named Ming/Qing sources; original editions not inspected.
- **O10.** Jing Han (2016), *The historical and chemical investigation of dyes in high status Chinese costume and textiles of the Ming and Qing dynasties (1368–1911)*, PhD thesis, University of Glasgow; journal **not applicable**. [Institutional record](https://theses.gla.ac.uk/7181/); [text URL](https://theses.gla.ac.uk/7181/1/2016.hanphd.pdf), p. 231 (cochineal discussion/Figs. 4.7–4.8) and p. 284, Table 4.11 (lac NMS-6; cochineal NMS-7). Indexed original text inspected; full PDF too large for browser extraction, no file saved.
- **O11.** Cooper Hewitt/Smithsonian Institution (catalogue, undated), “Woman's robe,” accession **1931-4-63**; journal **not applicable**. [Object URL](https://www.si.edu/object/womans-robe%3Achndm_1931-4-63); [Smithsonian indexed catalogue result with dimensions and CC0](https://collections.si.edu/search/results.htm?fq=-topic%3A%22Animals%22&fq=place%3A%22China%22&q=%22butterfly%22). Individual object URL failed live retrieval in this session; indexed institutional record and source image metadata agree on accession and measurements.
- **O12.** Wikimedia Commons (file uploaded 2017, record updated 2026), “Woman's Robe (China), ca. 1860 (CH 18318435).jpg,” museum catalogue-image mirror; journal **not applicable**. [File record](https://commons.wikimedia.org/wiki/File:Woman%27s_Robe_(China),_ca._1860_(CH_18318435).jpg). Links directly to the source museum catalogue and image; used to recover the image URL, not as an independent dye attribution.
- **O13.** Saint Louis Art Museum (catalogue, undated), “Wedding Altar Frontal with Design of Peony and Lotus Scrolls, Symbols for Double Happiness, and Meandering Swastika Fret Border,” **38:1917**; journal **not applicable**. [URL](https://www.slam.org/collection/objects/10902/). Dimensions, public-domain status and fading description are explicit.
- **O14.** Metropolitan Museum of Art (catalogue, undated), “Manchu Woman's Informal Robe,” **47.136.1**; journal **not applicable**. [URL](https://www.metmuseum.org/art/collection/search/69864). Dimensions and Public Domain explicitly stated; front image linked by the catalogue.
- **O15.** Diego Tamburini and Joanne Dyer (2019), “Fibre optic reflectance spectroscopy and multispectral imaging for the non-invasive investigation of Asian colourants in Chinese textiles from Dunhuang (7th–10th century AD),” *Dyes and Pigments* **162**, 494–511. [DOI](https://doi.org/10.1016/j.dyepig.2018.10.054). Reference silks, FORS spectra and artificial ageing; no universal ancient textile dye assignment follows from a red colour alone.

- **O16.** Chika Mouri and Richard Laursen (2012), “Identification of anthraquinone markers for distinguishing Rubia species in madder-dyed textiles by HPLC,” *Microchimica Acta* **179**, 105–113. [DOI/publisher abstract](https://doi.org/10.1007/s00604-012-0868-4). Primary comparative plant/textile HPLC-PDA-MS study; species findings are explicit in the publisher abstract.

---

## 7. Others — 鸡血石 and 红珊瑚

### Physics

**鸡血石:** Wang and Guo identify a fine-grained rock containing dickite/kaolinite, quartz and red cinnabar, with spots, streaks or clouds of HgS in a variably translucent pale, yellow or grey groundmass. It is not the iron-oxide-spotted chalcedony called heliotrope/bloodstone in other contexts. Treat it as a spatial mineral mixture; a homogeneous vermilion paint cannot reproduce its red inclusions and translucent matrix. Later mineralogical work confirms that substrates can also include alunite/pyrophyllite, so “cinnabar in dickite” is a useful starting point rather than a universal composition. A visible absorption/reflectance spectrum tied to a chemically characterized museum seal was **not found**. [X1, X2; representation is an inference]

**红珊瑚:** the red is an organic chromophore in a biomineral skeleton, not cinnabar or an iron-oxide paint. Fürst et al. identify conjugated polyene/carotenoid-related pigments in calcitic *Corallium rubrum*, while emphasizing that exact structures remain debated and pigments differ among taxa. Yang et al. interpret visible spectral features as polyene π→π* absorption; their spectra were collected in **reflectance mode and transformed by Kubelka–Munk**, rather than measuring an absolute bulk absorption coefficient. A museum label “coral” does not establish species or pigment mixture. [X3, X4]

| Quantity | Published evidence | Modelling limitation |
|---|---|---|
| Precious-coral UV–Vis reflectance / apparent absorption | Scan **200–900 nm [M]**, slit **20 nm [M]**, sampling **0.5 nm [M]**; broad maximum near **532 nm [M]**, shifting from **493 nm [M]** across the sample series. Curves: **Fig. 7**; Figs. 8–9 show correlations [X4] | Fine sampling does not remove the broad instrumental bandpass; transformed response is not an absolute absorption coefficient |
| Scientific attribution | Polyene π→π* visible absorption; specific distinct molecular species remain [?] [X3, X4] | Retain “polyene mixture” rather than asserting one fully identified red molecule |
| Numeric spectra | Coral raw UV–Vis data explicitly linked as File S2 at [Figshare](https://doi.org/10.6084/m9.figshare.32404389); **not fetched or verified as an array**. Chicken-blood-stone object spectrum: **not found** | Modern polished coral references, not a sample-matched historical object; no invented samples |

### Objects

| Museum object | Physical size | Open image / licence | Validation use |
|---|---|---|---|
| Met, **Seal**, 19th century, 2007.53; explicitly catalogued chicken-blood stone | 6.9 × 2.1 × 2.1 cm [M] | https://www.metmuseum.org/art/collection/search/73667 ; Public Domain / Open Access | Red–pale spatial mixture at seal scale |
| National Palace Museum, **雞血石「組安書畫」印**, late Qing–Republic, 贈玉000066N000000000 | Length 2.3, width 2.3, height 6.5 cm [M] | https://digitalarchive.npm.gov.tw/opendata/Pub/Detail/24813?dep=U&mode=full ; low-resolution files CC0, medium-resolution CC BY 4.0 | Straight polished faces and red blotches; museum's catalogue English “Bloodstone” should not override the Chinese material identification |
| Met, **Ornament (ruyi)**, 18th century, 02.18.623d; coral | Length 27.9 cm [M] | https://www.metmuseum.org/art/collection/search/773235 ; Public Domain / Open Access | Large carved coral object; species/pigment analysis **not found** |

### Close-up look

Chicken-blood stone provides sharply localized red mineral clouds against a fine-grained, sometimes translucent groundmass; microscopic images in Wang and Guo show cinnabar dispersed through dickite/kaolinite. Mineral proportions and polish must be represented separately. The NPM object has simple flat faces with blood-red markings; quantified gloss and roughness are **not found**. [X1, X5]

Modern polished precious coral can be shiny, but archaeological *C. rubrum* may lose red colour and gloss, exposing structural features and becoming pale enough to be confused with bone or shell. Fürst et al.'s microscopy is a stronger texture reference than assuming every coral object is uniformly smooth orange plastic. For the Met ruyi, object-specific ageing microscopy and quantitative BRDF are **not found**. [X3, X6]

### Sources

- **X1.** Wang Fuquan and Guo Jingfeng (1989), “Chicken-Blood Stone from China,” *Gems & Gemology* **25**(3), 168–170. https://doi.org/10.5741/gems.25.3.168 ; inspected GIA issue text URL https://www.gia.edu/doc/FA89.pdf .
- **X2.** Zhou Wubang, Wang Chaowen, Chen Qian and Chen Tao (2019), “Study on Mineralogical Characteristic of Hard Substrate Chicken-Blood Stone (Changhua) and Its Similar Varieties,” *Journal of Gems & Gemmology* **21**(S1), 70–77. https://doi.org/10.15964/j.cnki.027jgg.2019.S1.019 ; https://jogg.cug.edu.cn/article/doi/10.15964/j.cnki.027jgg.2019.S1.019 .
- **X3.** Sebastian Fürst, Katharina Müller, Liliana Gianni, Céline Paris, Ludovic Bellot-Gurlet, Christopher F. E. Pare and Ina Reiche (2016), “Raman Investigations to Identify *Corallium rubrum* in Iron Age Jewelry and Ornaments,” *Minerals* **6**, 56. https://doi.org/10.3390/min6020056 ; https://www.mdpi.com/2075-163X/6/2/56 .
- **X4.** Yushu Yang et al. (2026), “Compositional Characterization and Color Genesis of Precious Coral Based on Multi-Spectroscopic Techniques,” *Crystals* **16**(6), 374. https://doi.org/10.3390/cryst16060374 ; https://www.mdpi.com/2073-4352/16/6/374 . Method §2.2.5, UV–Vis curves Fig. 7, correlations Figs. 8–9; [raw-data landing DOI](https://doi.org/10.6084/m9.figshare.32404389). Exact molecular identities remain inferential.
- **X5.** National Palace Museum (n.d.), “雞血石『組安書畫』印 / Bloodstone seal with inscription ‘Zuan shu hua’,” online collection record, 贈玉000066N000000000; journal: not applicable. https://digitalarchive.npm.gov.tw/opendata/Pub/Detail/24813?dep=U&mode=full .
- **X6.** The Metropolitan Museum of Art (n.d.), “Ornament (ruyi),” 02.18.623d, online catalogue; journal: not applicable. https://www.metmuseum.org/art/collection/search/773235 .
- **X7.** The Metropolitan Museum of Art (n.d.), “Seal,” 2007.53, online catalogue; journal: not applicable. https://www.metmuseum.org/art/collection/search/73667 .

---

## Final selection and ranking

**Subjective editorial ranking [?], not a measured cultural or aesthetic score.** “Iconic” here means recognizable as a Chinese material/object tradition; “macro appeal” means useful visible depth, relief, texture and colour variation in a close photograph. The overall order balances these two judgments. Ordinals are ranks, not physical measurements. The reasons refer back to the cited evidence in each section.

| Overall order [?] | Red | Iconic rank [?] | Macro-beauty rank [?] | One-line reason |
|---|---|---|---|---|
| 1 | 朱砂 / 银朱, especially 剔红 | 1 | 2 | An unmistakable red carving tradition with deep relief, geometric grounds, polished high points and layer-revealing losses. [H6–H7, HO1–HO2] |
| 2 | 铜红, especially Jun splashes and Langyao | 3 | 1 | Saturated red, blue-violet transitions, milky phase structure, bubbles and crackle make the richest close-up optical comparison. [C3–C4, C7–C9] |
| 3 | Organic reds, especially red silk/velvet | 2 | 5 | Wedding associations and tactile pile/weave are highly legible, while the particular dye requires chemical evidence. [O7–O8, O11, O13] |
| 4 | 金红 enamel / gold-ruby glass | 5 | 3 | Ruby transparency and milky pink mixtures offer jewel-like depth; the exact studied gold-enamel bowl is especially valuable. [G4, G6, G9] |
| 5 | 铁红, especially palace plaster and Fanhong | 4 | 6 | Palace-wall red is a powerful architectural reference, with matte grains and weathering; enamel provides a complementary smooth surface. [I8–I10, IO2] |
| 6 | 鸡血石 / 红珊瑚 | 6 | 4 | Mineral red clouds and translucent matrix, or coral carving and organic structure, reward macro photography but are more specialist symbols. [X1, X3, X5–X7] |
| 7 | 铅丹, especially 万年红 | 7 | 7 | The coated-book tradition has exceptional documentary specificity; its strongest appeal is in paper fibres, brush boundaries and stratigraphy. [L2–L3, L7] |

For production planning, start with the lacquer and copper-glaze references, then the chemically analysed gold-enamel bowl. Treat **historical Qing gold-ruby glass spectra**, **page-scale 万年红 photographs**, **the exact dyes in the open-image textiles**, and **lantern-/春联-specific dye recipes** as unresolved evidence needs, not parameters to guess. All located image URLs with explicit licence and physical scale are in `download.txt`; the NPM preview was omitted because its dynamic URL's resolution-specific licence was not established, and the restricted Corning image was omitted. Whole-object dimensions establish overall size; a tightly cropped macro photograph still needs a scale reference or a defensible projection before assigning pore/yarn/crack dimensions.
