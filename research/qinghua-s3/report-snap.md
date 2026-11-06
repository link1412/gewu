# Blue-and-white porcelain (青花): evidence for a physically based material

Research date: 2026-10-28. Target: bright, clean modern Jingdezhen ware, with Kangxi 翠毛蓝 as a historical visual reference. This is a literature and reference-image report, **not a calibrated material preset**.

**Recommended direction — research inference:** represent a transparent glaze over a cobalt-bearing interaction region and a scattering porcelain body. Allow dissolved cobalt and residual pigment/crystal phases to contribute separately. Keep modern clean ware, vivid Kangxi ware, and early-Ming iron-rich/heaped decoration as different targets. This follows the observed cross sections and the demonstrated dependence of colour on host glass, particles and firing; a uniform blue surface colour cannot express those observations.[^S1][^S3][^S4]

The strongest quantitative optical anchor found is an absolute absorption measurement in a glass surrogate. Direct absolute visible absorption for modern Jingdezhen glaze, and a complete same-object optical/structural dataset for vivid Kangxi, were **not found**. The missing parameters below must not be filled by treating unrelated ceramic or glass measurements as measurements of the target.

## Evidence conventions and scope

- **[M]**: a measurement reported in the cited source. It does not imply that the source measured the modern target. Museum dimensions and reported raster dimensions also use this tag.
- **[D]**: derived here, calculated by the source, or read from a figure. The method is stated.
- **[?]**: uncertain provenance, interpretation, applicability, or a descriptive/recipe number without an inspected measurement protocol.
- **not found**: not located and verified in the sources consulted within this research budget; not a claim that the information does not exist.

Tags apply to numerical scientific values and dimensions. Bibliographic years, page numbers, DOI strings, object identifiers, formula subscripts, section numbers and catalogued dates are identifiers rather than measured material parameters. Ranges belong to the specified population, not to all 青花. Raw ore, processed pigment, fired residual particles, blue glaze, and glazed white ground are kept distinct. Source pages and indexed primary-paper text were read; no source files or image files were saved or downloaded locally.

## 1. Cobalt blue: measured optics

### Absolute absorption in a silicate-glass surrogate

Thiemsorn et al. measured a soda–lime–silica host series. Their CoO addition is **0.04 mol% [M], not wt%**; the reported cobalt concentration is **0.016 mol/L [M]**. Spectra cover **250–1500 nm [M]**, encompassing the requested visible range. Figure 7 supplies the spectral shape; Table 4 supplies the absolute middle-band anchor below. This is **glass, not a measured porcelain glaze**.[^A1]

| Sample | Density, g/cm³ [M] | Decadic A/path, cm⁻¹ [M], at 595 nm [M] | Molar ε, L mol⁻¹ cm⁻¹ [D, source] | Natural-log α, mm⁻¹ [D] | α per wt% CoO, mm⁻¹/(wt%) [D] |
|---|---:|---:|---:|---:|---:|
| Co1 | 2.481 | 2.44 | 152.50 | 0.562 | 11.6 |
| Co2 | 2.497 | 2.65 | 165.63 | 0.610 | 12.7 |
| Co3 | 2.521 | 2.80 | 175.00 | 0.645 | 13.6 |
| Co4 | 2.536 | 2.95 | 184.38 | 0.679 | 14.4 |
| Co5 | 2.552 | 3.09 | 193.13 | 0.711 | 15.1 |

Conversion [D]: with `A = ε c l_cm`, `T = 10^(−A) = exp(−α l_mm)`, density `ρ` in g/cm³ and numerical concentration `w` in wt%,

```text
α_mm = ln(10) × (A/l_cm) / 10
c_mol/L = 10 × ρ × w / M_CoO
α_mm / w = ln(10) × ε × ρ / M_CoO
```

`M_CoO = 74.9326 g/mol [D, tabulated molecular weight]`.[^A7] Linear concentration normalization assumes the same host and cobalt speciation [?]. A numerical wavelength-by-wavelength array was **not found**; no curve was downloaded or digitized. Do not extrapolate this peak normalization to arbitrary crystalline pigment loadings.

### Band centres and widths

| Material / observable | Visible centres | Individual FWHM | Source / applicability |
|---|---|---|---|
| Soda–lime–silica glass absorption | 525, 595, 650 nm [M] | **not found** | Thiemsorn et al., Fig. 7; glass surrogate[^A1] |
| Archaeological high-lime/low-alkali glass absorption | approximately 535, 595, 640 nm [M] | **not found** | Patin et al.; host-specific glass, not porcelain[^A3] |
| Actual mid-Ming Jingdezhen blue-area FORS minima | approximately 520, 583, 672 nm [M] | **not found** | Hsieh et al., Fig. 4/Table 2[^A5] |
| Dry sodium aluminosilicate glass, fitted visible components | 15075, 16589, 19697 cm⁻¹ [D, source fit] → 663.35, 602.81, 507.69 nm [D] | **not found** | Nowak & Keppler, Table 4; component centres are not total-spectrum maxima[^A2] |

For the last row, fitted component ε values are **85.8, 59.1, 43.4 L mol⁻¹ cm⁻¹ [D]**, respectively. The dry specimen contains **0.95 wt% CoO [M]**; Figure 1 presents absorption normalized to **1 wt% CoO [D]** and **250 µm [D]**. Its full curve is another useful absolute aluminosilicate surrogate, not a modern glaze calibration. Widths of the fitted Gaussians were not tabulated in the verified material.[^A2]

Thus the approximate triplet in the brief is a search guide, not a universal set of fixed centres. Controlled host-composition spectroscopy explicitly finds changes in cobalt coordination and band shape.[^A4] **Proposed implementation:** use a measured host-specific spectrum when available; do not manufacture Gaussian widths from the spacing between peaks.

### Actual porcelain reflectance paired with cobalt content

Hsieh et al. pair FORS and pXRF for Hongzhi Jingdezhen Santa Cruz dishes selected for atypical hues. Representative Table 2 rows follow; Figure 4 plots reflectance.[^A5]

| Dish | Co in blue spot, ppm [M] | First minimum, nm [M] | Second, nm [M] | Third, nm [M] |
|---|---:|---:|---:|---:|
| SC-256 | 1276 | 519, weak | 583, strong | 678, strong |
| SC-14878 | 166 | 522 | 586 | 655, broad |

FORS/pXRF spots: approximately **10/6 mm [M]**; concentrations include glaze, not pure pigment.[^A5] Reflectance alone cannot identify α without scattering/layer geometry [D]. Bright Kangxi/modern paired spectra/loading: **not found**. A further late-Ming/early-Qing study is Fischer & Hsieh; numerical tables were not inspected.[^A6]

## 2. Cross section: where the blue resides

| Question | Verified observation | Numeric evidence / limit | Primary source |
|---|---|---|---|
| Location | Pigment-bearing interaction region near the body–glaze boundary; cobalt also dispersed in the glass | A universally uniform, sharply bounded coloured slab is unsupported | Jiang et al., Figs. 1/3; Wang et al. synchrotron maps[^S1][^S3] |
| Vertical coloured-zone thickness | A museum-journal discussion describes an interfacial pigment layer | about **10 µm [?]**, cited literature statement, not the authors' own SEM measurement; direct modern/Kangxi value **not found** | Miao & Yu, p. 88[^S8] |
| Crystals | Anorthite encloses CoAl₂O₄ spinel with Fe/Mn substitution; bodies contain quartz/mullite | Xuande As–Co–Ni–Cu-rich sphere approximately **500 nm [M]**; Fe/Mn-rich amorphous droplets mostly **<100 nm [M]** | Jiang et al., Fig. 3/Table 1; Qu et al.[^S1][^S2] |
| Bubbles near pigment | Glaze contains bubbles; residual pigment can accumulate at bubble boundaries | Yuan residual particles generally **>5 µm [M]** at bubble interfaces versus submicron particles [M] at the body interface | Jiang et al., Fig. 4[^S1] |
| SEM/EPMA character of blue zones | Central colouring-element enrichment surrounded by dense columnar/flower-like anorthite | Bubble sizes unequal; exact diameter/density and zone-thickness distributions **not found** in accessible text | Qu et al.[^S2] |
| Heaping/piling, Yongle | SEM-EDS/EPMA distinguish nonreflective and reflective spots; shallow dendritic/snow-shaped iron-rich crystals run parallel to the surface | Spot depth **not found**; this is a direct Yongle study, not a measurement of every Xuande ware | Wang et al. 2016[^S5] |
| Xuande and later dark spots | Co- and Mn-bearing ferrite/spinel solid solutions also occur | One described crystal-block length is **150 µm [M]**; **not** coloured-layer thickness | Wang et al. 2023[^S6] |

The spot phases identified in the latter study include **CoFe₂O₄–Fe₃O₄** and **Mn₃O₄–MnFe₂O₄–Fe₃O₄** solid solutions, together with Ca/Na aluminosilicate phases. Iron-like dark or metallic spots are therefore **not a unique assay of imported 苏麻离青**.[^S6] Jiang et al. likewise show elemental partitioning during firing, so glaze Fe/Mn ratios need not preserve raw-ore ratios.[^S1]

**Proposed rendering implication:** place colour below the clear surface, model a spatial concentration/particle field, and reserve surface-near iron-rich defects for the relevant historical samples. A modern clean surface should not automatically inherit archaeological corrosion or early-Ming heaping. Evidence for lateral diffusion is discussed separately below; it does not supply a vertical layer thickness.[^S1][^S5][^S7]

## 3. Ore, processing and colour

### Measured oxide ratios: retain the sampling basis

The following are **mass ratios of oxides**, not atomic ratios or elemental Fe/Co. They are measurements of fired-blue material unless specifically described otherwise.

| Source population | MnO/CoO | Fe₂O₃/CoO | Interpretation and limit |
|---|---:|---:|---|
| Yuan fired blue, **5 specimens [M]** | **0.01–0.06 [M]** | **2.21–3.02 [M]** | Low-Mn/high-Fe anchor; not a bulk assay of authenticated raw Sumali ore[^C1] |
| Ming fired blue, **5 specimens [M]**, reigns pooled | **0.81–6.08 [M]** | **0.41–5.81 [M]** | Mixed population; cannot define a single named ore[^C1] |
| Qing fired blue, **3 specimens [M]** | **5–7 [M]** | **0.4–1 [M]** | Original authors infer refined/calcined Zhejiang ore; provenance inference, not a measured Kangxi raw-ore range[^C1] |
| Hongwu–Yongle blue glaze, PIXE compilation | **0.005–0.15 [M]** | **2.0–24 [M]** | Different dataset and measurement basis; do not merge with the narrow Yuan range[^C2] |
| Jiajing blue glaze, PIXE compilation | **0.2–1.3 [M]** | **0.2–3.2 [M]** | Associated with Mohammedan blue in source; not pure Huiqing ore chemistry[^C2] |
| Asbolite pigment comparator | **4.8–9.0 [M]** | **0.35–1.66 [M]** | Material category, not a unique Chinese mine[^C2] |

**Access limit for Cheng et al.:** Table 2 was available as indexed primary-paper text; the old full-text host now redirects. Its numbers have lower auditability than the publisher abstract of Chen et al. Neither table should be converted into a historical raw-ore recipe.[^C1][^C2]

### Requested named materials

| Material | Supported distinction | Authenticated bulk CoO / MnO / Fe₂O₃ wt% ranges |
|---|---|---|
| 苏麻离青 | Low-Mn/high-Fe imported-colourant tradition is compatible with the Yuan analytical set; mixtures and firing partitioning complicate attribution[^C1][^S1] | **not found** in a directly verified primary raw-ore table |
| 国产青料 | Domestic asbolite ores are generally Mn-rich relative to cobalt; “domestic” is not one mineral composition[^C1] | **not found** as a single valid range |
| 珠明料 / Yunnan Zhuming | Early-Qing minyao chemistry fits Yunnan asbolites/refined Zhuming more closely than Zhejiang in one study[^C3] | **not found** in inspected primary numerical tables |
| 浙料 / Zhejiang Zheliao | Historical attribution exists, but **Kangxi does not imply Zheliao for every vessel**. Zhang & Gethin examined **15 sherds [M]**, **5 per reign [M]**, and favoured Yunnan for that minyao set[^C3] | **not found** as an authenticated Kangxi Zheliao range |
| 回青 / Huiqing | Late-Zhengde/Jiajing material is described as low Mn, high Co, low Al₂O₃ and vivid slightly purplish blue[^C4] | **not found** for pure authenticated raw Huiqing; fired-glaze ratios above are not a substitute |
| Modern refined cobalt oxide | Industrial oxides are used in modern controlled experiments, but impurity assays and a representative Jingdezhen supply specification were not reported in the inspected source[^C5] | **not found**; MnO/Fe₂O₃ must not be assumed zero |

Verified primary raw-ore assays for the requested historical names: **not found**. The fired-blue measurements above do not establish those missing bulk-ore ranges.

### Ingredient effects are conditional

| Ingredient / mechanism | Evidence | Limit |
|---|---|---|
| Mn → grey/dark | Controlled Ji-blue glaze: MnO₂ **2.56–6.58 wt% [M]** shifts dark blue toward blue-grey/silver-blue; above **4.57 wt% [M]** the authors describe silver-blue[^C5] | This is a coloured-glaze recipe, not a universal Qinghua threshold; **MnO₂ is not MnO** |
| Fe → dark/black/brown | Same experiment: Fe₂O₃ **2.98–4.01 wt% [M]** gives dark to black-blue; **5.03 wt% [M]** and above dark brown; cobalt oxide **0.57 wt% [M]** in the base recipe[^C5] | Chinese and English abstracts disagree on the iron interval; these values follow the Chinese abstract |
| Fe/Mn-rich dark spots | Direct microscopy identifies segregated ferrite/spinel phases[^S5][^S6] | Local crystalline spots differ from a homogeneous dissolved absorber |
| Mn → purple | **A universal rule is not established**: low-Mn Huiqing can be purplish; colour depends on host, firing, particles and elemental ratios[^C4][^S4] | Purple-blue cannot be assigned solely from bulk Mn |
| Oxidation/coordination state | Synthetic Kangxi-like pigment has predominantly tetrahedral Co(II), Mn(II), and Fe(III); Fe can substitute Al in spinel[^C6] | XAS evidence is not an absolute optical absorption coefficient |

## 4. The rest of the material stack

### Numerically supported comparators

| Property | Value | What the value actually describes |
|---|---|---|
| Glaze thickness, archaeological Yuan blue-and-white | **0.18–0.22 mm [M]**; mean **0.20 ± 0.01 mm [M]** | Sun et al., OCT, Fig. 2; **not Kangxi or modern commercial ware**[^S9] |
| Generic historical Jingdezhen glaze thickness | **200–500 µm [?]** | Miao & Yu's cited contextual statement; not a new direct measurement[^S8] |
| White-area glaze CaO and K₂O | **6.1 ± 0.9 wt% [M]**, **4.3 ± 0.4 wt% [M]** | Hongzhi Santa Cruz export plates; pXRF, possible surface alteration[^A5] |
| Glazed white-ground colour | **L*=67.95 ± 3.64 [M]**, **a*=−3.92 ± 0.41 [M]**, **b*=3.27 ± 1.85 [M]** | Yuan blue-and-white, Sun et al. Table 5; **not body-only whiteness or spectral reflectance**[^S9] |
| Measured Yuan glaze composition | See YQH-185 below | Archaeological comparator, not modern or Kangxi[^S9] |

Measured historical-glaze comparator: Yuan specimen **YQH-185**, Sun et al. Table 3.[^S9]

| Oxide | Glaze wt% [M] | Oxide | Glaze wt% [M] | Oxide | Glaze wt% [M] |
|---|---:|---|---:|---|---:|
| SiO₂ | 75.24 | Al₂O₃ | 11.71 | CaO | 4.37 |
| MgO | 0.33 | K₂O | 3.02 | Na₂O | 3.44 |
| Fe₂O₃ | 0.83 | TiO₂ | 0.06 | P₂O₅ | 0.02 |

YQH-185's listed oxides total **99.02 wt% [D]**; the unlisted balance is **not found**. No renormalization is applied.[^S9]

### Target-specific gaps

| Requested parameter | Modern Jingdezhen bright blue-and-white | Kangxi vivid blue-and-white |
|---|---|---|
| Body-only reflectance spectrum | **not found** | **not found** |
| Body whiteness with specified standard/geometry | **not found** | **not found** |
| Spectral transmission/translucency versus measured thickness | **not found** | **not found** |
| Transparent-glaze complete measured composition | **not found** for a representative target product | **not found** in inspected target-specific numerical tables |
| Visible refractive index and dispersion | **not found** | **not found** |
| Glaze thickness distribution | **not found** | **not found**; generic historical statements above are not Kangxi-specific |
| Bubble size distribution and number/volume density | **not found** | **not found** |
| Gloss in GU with measurement angle | **not found** | **not found** |
| Quantified Fe²⁺ contribution to clear-glaze tint | **not found** | **not found** |

These gaps survived searches of primary spectroscopy, SEM/EPMA, OCT and glaze studies. Dental porcelain, other kiln bodies, monochrome opaque glazes, THz refractive index, generic glass index assumptions and unstandardized historical “whiteness” tables were not substituted.

**Faint blue-green tint:** a primary Jingdezhen kiln experiment attributes blue-green celadon colour to Fe²⁺ and yellow-green/brown tendencies to Fe³⁺. Its measured Fe²⁺/Fe³⁺ XPS area ratios are **1.31 ± 0.14 [M]**, **3.89 ± 0.59 [M]**, and **0.77 ± 0.04 [M]** for S3, S11 and S13. This supports the chemical mechanism, **not a tint magnitude for a transparent blue-and-white glaze**.[^S11] Dresden's museum catalogue independently describes the best Kangxi ware as white-bodied, brilliant translucent blue, with a clear slightly bluish glaze; this is a connoisseurial description, not spectral data.[^P7]

## 5. Painting: outlines, graded washes and motifs

| Feature | Supported description | Quantitative status |
|---|---|---|
| 勾线 | Brush-painted outlines precede filled washes; the V&A documents painting the shaped porcelain body[^P1][^P2] | Typical stroke width in mm: **not found** |
| 分水 | A full 兰花头 brush deposits different strengths of cobalt suspension inside outlines[^P2] | Conventional **5, 7 or 9 tones [?]** in the Palace Museum glossary; UMMA describes **5 [?]** “colours of blue.” These are workshop/art-historical categories, not discrete spectral levels[^P3] |
| Painting suspension | Palace Museum glossary gives water content **82–96% [?]**[^P2] | Concentration basis/protocol **not found**; cannot convert to fired wt% CoO |
| Lateral bleeding | A diffusion-focused study reexamines the simple glaze-viscosity explanation[^S7] | Early/middle Zhengde about **100 µm [M]**; late Zhengde/Jiajing **180–650 µm [M]**, from Li et al. abstract. These are **dispersion distances, not brush widths or vertical layers**[^C4] |
| Within-stroke variation | No verified universal transverse cobalt profile was located | Edge/centre concentration ratio, darker-edge rule, pooling depth and concentration law: **not found** |
| Motifs | Entwined lotus (缠枝莲), cloud/dragon (云龙), bird/flower, landscapes and narrative scenes occur in museum catalogues[^P2][^P5][^P6][^I1][^I3] | “Typical” here means documented examples, not measured frequency or a universal physical motif size |

**Proposed painting model:** independently parameterize outlines, wash optical depth and local diffusion; use continuous concentrations rather than quantizing the spectrum into the conventional tonal count. Darker pooling or edge accumulation may be an artistic hypothesis [?], but was not established as a universal measured physical law for 分水 in this search.

## 6. Reference images and scale audit

Image URLs and coverage status are listed below and in `download.txt`. The manifest includes the open Kangxi originals and explicitly unqualified academic close-up candidates. The Met records explicitly mark these works Public Domain; its image policy applies CC0 to such open images.[^I7] The `/original/` files are the largest publicly exposed originals located in the image index. They were **not fetched**, so raster dimensions, colour calibration, bit depth and binary availability were not independently tested. A museum photograph with known object size supports geometric comparison; it does not by itself measure reflectance or gloss.

### A. Kangxi objects with documented size and open images

| Ref | Object / period | Physical dimensions | Image file URL, original | Licence / source |
|---|---|---|---|---|
| K1 | Vase with Flowering Plants and Birds, Met 14.40.276; Kangxi, late seventeenth–early eighteenth century | Height **45.7 cm [M]** | https://images.metmuseum.org/CRDImages/as/original/DP-14605-071.jpg | CC0 / Public Domain; [object page](https://www.metmuseum.org/art/collection/search/42204)[^I1] |
| K2 | Plate with cartouches of women and plants, Met 18.61.2; Kangxi, late seventeenth–early eighteenth century | Height **3.8 cm [M]**, width **16.5 cm [M]** | https://images.metmuseum.org/CRDImages/as/original/DP-15944-021.jpg | CC0 / Public Domain; [object page](https://www.metmuseum.org/art/collection/search/47583)[^I2] |
| K3 | Vase with landscape scenes, Met 14.40.424; Kangxi, late seventeenth century | Height **73.7 cm [M]**, diameter **27.9 cm [M]** | https://images.metmuseum.org/CRDImages/as/original/LC-14_40_424-20230217-01.jpg | CC0 / Public Domain; [object page](https://www.metmuseum.org/art/collection/search/46094)[^I3] |

These provide floral, figure and wash-painted landscape comparators. “Vivid” is a visual-selection goal, not an instrumentally measured property of these photographs; no spectral or colour-target calibration was supplied by the inspected object pages.

### B. Additional image leads and unresolved requirements

| Requirement / candidate | Verified metadata | Remaining limitation |
|---|---|---|
| Cleveland Vase with Cover, 1954.575; Kangxi | Height **45.6 cm [M]**, CC0. Commons JPEG **2233 × 3400 px [M]**; a TIFF **3361 × 5117 px [M]** is listed in its collection category[^I4] | Largest TIFF page could not be read; direct master URL **not found** in verified metadata. Do not call the smaller JPEG the largest master |
| Cleveland lid, 1954.575.b; Kangxi | Catalogue dimension **15.1 cm [M]**, axis unspecified; CC0. Commons JPEG **3400 × 2471 px [M]**; listed TIFF **8000 × 5815 px [M]**[^I5] | Physical axis and actual object pixel footprint not verified; **≥20 px/mm not established**. Filename/large canvas size alone is insufficient |
| Modern Jingdezhen, wangzhao, *China 青花花瓶01.JPG* | Original **1920 × 2560 px [M]**; photographed 2012-01-05; categorized modern Jingdezhen; **CC BY-SA 3.0**, attribution wangzhao[^I6] | Object manufacture date and physical dimensions **not found**. BY-SA is not the requested CC0/CC BY licence class. Excluded from the strict download list |
| Scaled brush-stroke and bubble closeups | See microscope leads below | Fully verified original image + licence + scale qualification: **not found** at this stage |

Modern lead object/file page: https://commons.wikimedia.org/wiki/File:China_%E9%9D%92%E8%8A%B1%E8%8A%B1%E7%93%B601.JPG . A photograph's capture date does not establish the object's manufacturing date.

### C. Microscopy leads, not falsely certified scale references

| Source / figure page | Subject | Licence and scale status |
|---|---|---|
| Vieira Ferreira et al., [article Fig. 6](https://www.mdpi.com/2571-9408/8/7/253) | Archaeological sherd sections/oblique coloured glaze views | CC BY 4.0; indexed caption gives **1.0 mm [M]** scale bar, but original raster and bar pixel count **not found**. Authors' “in-glaze” interpretation differs from ordinary underglaze; not a clean modern target[^S10] |
| Same authors' [preprint Fig. 6a/6b](https://www.preprints.org/manuscript/202505.2496) | Ming/Wanli and early-Qing sherd close-ups; glaze, black inclusions and bubbles | CC BY 4.0; **1.0 mm [M]** bar. Original supplied PNG links below; raster dimensions and pixels/mm **not found**. This version is **not peer reviewed**[^S10p] |

Original supplied figure files located on the author-manuscript host (no larger variant verified):

- Fig. 6a: https://www.preprints.org/frontend/picture/ms_xml/manuscript/88cb9232eedb7122d6bf620f2236b717/preprints-161592-g006a.png
- Fig. 6b: https://www.preprints.org/frontend/picture/ms_xml/manuscript/88cb9232eedb7122d6bf620f2236b717/preprints-161592-g006b.png

These are useful **bubble/pigment microstructure candidates**, not validated surface-brush photographs. Their stylistic dates are author attributions [?]. They appear in the manifest with the unresolved scale qualification stated.

Scale acceptance method [D]: `pixels/mm = measured pixels along a scale bar / labelled bar length in mm`, evaluated on the original image. For a whole object, use the object's actual projected pixel extent and the matching physical axis; do not divide the full canvas width by the object's diameter. Cropping or upsampling cannot establish additional physical resolution. No candidate is claimed to meet the requested **20 px/mm [brief requirement]** without that check.

## 7. What is ready for rendering, and what still needs measurement

**Ready:** a defensible multilayer architecture; host-dependent measured cobalt band positions; a correctly normalized absolute glass absorption anchor; actual Ming reflectance/mineral/chemical observations; historical thickness comparators; and open Kangxi object images with physical size.

**Not yet calibrated:** a complete modern or vivid-Kangxi spectral material. Obtain the target object's glaze/body spectra with specified geometry, glaze thickness/profile and visible index, body transmission at known thickness, and a measured surface reflection/gloss distribution. The reference images can then test geometry, pattern scale and visual appearance. Until those measurements exist, inferred renderer choices must remain labelled hypotheses; this report supplies no invented refractive index, roughness, bubble density, wash width or Gaussian bandwidth.

## Sources

All journal sources below are primary research unless an access limitation or literature-statement status is given. Museum sources and databases have no journal; that absence is stated rather than filled with an invented venue.

[^A1]: Worapong Thiemsorn, Kanchana Keowkamnerd, Sukon Phanichphant & Heiko Hessenkemper (2007). “Effects of Glass Structure on the Optical Absorption of Transition Ions in Industrial Soda-Lime-Silica Glasses.” *Journal of Solid Mechanics and Materials Engineering* 1(4), 508–518. DOI: [10.1299/jmmp.1.508](https://doi.org/10.1299/jmmp.1.508). [Publisher](https://www.jstage.jst.go.jp/article/jmmp/1/4/1_4_508/_article); [full-text URL](https://www.jstage.jst.go.jp/article/jmmp/1/4/1_4_508/_pdf/-char/en). Tables 1/4, Fig. 7; web-readable primary text inspected.
[^A2]: Marcus Nowak & Hans Keppler (1998). “The influence of water on the environment of transition metals in silicate glasses.” *American Mineralogist* 83(1–2), 43–50. DOI: [10.2138/am-1998-1-204](https://doi.org/10.2138/am-1998-1-204). [Primary full-text URL](https://rruff.info/doclib/am/vol83/AM83_43.pdf). Tables 1/2/4 and Figs. 1/2; primary text inspected through web tools.
[^A3]: Mathilde Patin, Karin Nys, Helena Wouters, Hugo Thienpont & Wendy Meulebroeck (2022). “Using UV-Vis-NIR absorption spectroscopy as a tool for the detection of iron and cobalt in glass: A case-study on HLLA material from the Low Countries.” *Journal of Archaeological Science: Reports* 44, 103517. DOI: [10.1016/j.jasrep.2022.103517](https://doi.org/10.1016/j.jasrep.2022.103517). [Institutional manuscript URL](https://cris.vub.be/ws/portalfiles/portal/122365054/Patinetal_UVVisNIR_Revision2_V1_WM.pdf). Primary indexed text inspected.
[^A4]: Cristina Fornacelli, Andrea Ceglia, Susanna Bracci & Marcia Vilarigues (2018). “The role of different network modifying cations on the speciation of the Co²⁺ complex in silicates and implication in the investigation of historical glasses.” *Spectrochimica Acta Part A: Molecular and Biomolecular Spectroscopy* 188, 507–515. DOI: [10.1016/j.saa.2017.07.031](https://doi.org/10.1016/j.saa.2017.07.031). [Institutional abstract](https://researchportal.vub.be/en/publications/the-role-of-different-network-modifying-cations-on-the-speciation/). Abstract inspected; full fitted width tables not accessed.
[^A5]: Ellen Hsieh, Christian Fischer & Bobby C. Orillaneda (2023). “The atypical hues of the Santa Cruz blue-and-white cargo: non-invasive analysis of glaze defects and color variations in mid-Ming porcelain.” *Heritage Science* 11, 106. DOI: [10.1186/s40494-023-00953-0](https://doi.org/10.1186/s40494-023-00953-0). [Publisher full text](https://www.nature.com/articles/s40494-023-00953-0). Methods, Table 2, Figs. 4–6 inspected; Table 2 numeric rows also checked against indexed primary-paper reproduction. CC BY 4.0, subject to figure-specific credits.
[^A6]: Christian Fischer & Ellen Hsieh (2017). “Export Chinese blue-and-white porcelain: compositional analysis and sourcing using non-invasive portable XRF and reflectance spectroscopy.” *Journal of Archaeological Science* 80, 14–26. DOI: [10.1016/j.jas.2017.01.016](https://doi.org/10.1016/j.jas.2017.01.016). [Bibliographic abstract](https://hero.epa.gov/reference/4773747/). Abstract only; numerical full-text tables not inspected.
[^A7]: National Institute of Standards and Technology (undated database entry). “Cobalt oxide.” *NIST Chemistry WebBook, SRD 69*; database, no journal. [Molecular-weight record](https://webbook.nist.gov/cgi/cbook.cgi?ID=1307-96-6).

[^S1]: Xiaochenyang Jiang, Yanjun Weng, Xiaohong Wu, Jianfeng Cui, Hongshu Lyu, Jianxin Jiang, Guodong Song, Hetian Jin, Dashu Qin & Changsui Wang (2020). “Early globalized industrial chain revealed by residual submicron pigment particles in Chinese imperial blue-and-white porcelains.” *Proceedings of the National Academy of Sciences* 117(12), 6446–6452. DOI: [10.1073/pnas.1916630117](https://doi.org/10.1073/pnas.1916630117). [Publisher](https://www.pnas.org/doi/10.1073/pnas.1916630117); [PubMed](https://pubmed.ncbi.nlm.nih.gov/32123076/). Primary HTML/captions inspected.
[^S2]: Yanan Qu, Jie Xu, Xiaoqing Xi, Chengjie Huang & Jinlong Yang (2014). “Microstructure characteristics of blue-and-white porcelain from the folk kiln of Ming and Qing Dynasties.” *Ceramics International* 40(6), 8783–8790. DOI: [10.1016/j.ceramint.2014.01.100](https://doi.org/10.1016/j.ceramint.2014.01.100). [Publisher](https://www.sciencedirect.com/science/article/pii/S0272884214001278). Accessible abstract/section text inspected; full numerical tables not accessed.
[^S3]: Tian Wang, Tiequan Zhu, Ziyang Feng, Barbara Fayard, Emeline Pouyet, Marine Cotte, Wout De Nolf, Murielle Salomé & Philippe Sciau (2016). “Synchrotron radiation-based multi-analytical approach for studying underglaze color: The microstructure of Chinese Qinghua blue decors (Ming dynasty).” *Analytica Chimica Acta* 928, 20–31. DOI: [10.1016/j.aca.2016.04.053](https://doi.org/10.1016/j.aca.2016.04.053). [PubMed](https://pubmed.ncbi.nlm.nih.gov/27251853/). Primary abstract inspected.
[^S4]: Ariane Pinto, Jesse Groenen, Bing Zhao, Tiequan Zhu & Philippe Sciau (2020). “Chromogenic mechanisms in blue-and-white porcelains.” *Journal of the European Ceramic Society* 40(15), 6181–6187. DOI: [10.1016/j.jeurceramsoc.2020.06.065](https://doi.org/10.1016/j.jeurceramsoc.2020.06.065). [Publisher](https://www.sciencedirect.com/science/article/pii/S0955221920305355). Abstract/section text inspected.
[^S5]: W. Wang, J. Zhu, J. Jiang, C. Xu, S. Wu, L. Guan, Z. Zhang, M. Wu & J. Du (2016). “Microscopic analysis of ‘iron spot’ on blue-and-white porcelain from Jingdezhen imperial kiln in early Ming dynasty (14th–15th century).” *Microscopy Research and Technique* 79(11), 1123–1130. DOI: [10.1002/jemt.22766](https://doi.org/10.1002/jemt.22766). [PubMed](https://pubmed.ncbi.nlm.nih.gov/27582182/). Abstract inspected; initials retained where expanded given names were not independently verified.
[^S6]: Wenxuan Wang, Philippe Sciau, Jian Zhu, Jianxin Jiang, Rui Wen & Magali Brunet (2023). “Microstructure analysis of ‘iron spots’ on Qinghua porcelain from Jingdezhen imperial kiln.” *Journal of the European Ceramic Society* 43(2), 708–717. DOI: [10.1016/j.jeurceramsoc.2022.09.056](https://doi.org/10.1016/j.jeurceramsoc.2022.09.056). [Publisher](https://www.sciencedirect.com/science/article/pii/S0955221922007646). Abstract and indexed section text inspected.
[^S7]: Xiaochenyang Jiang, Nian Liu, Xuekun Xu, Yan Ge, Zhimin Li, Jianfeng Cui & Yang Zhai (2024). “Revisiting the bleeding effect in historical cobalt porcelain pigments: Mechanism, influence and technical responses.” *Journal of Archaeological Science* 167, 105987. DOI: [10.1016/j.jas.2024.105987](https://doi.org/10.1016/j.jas.2024.105987). [Publisher](https://www.sciencedirect.com/science/article/abs/pii/S0305440324000554). Accessible abstract/sections inspected.
[^S8]: 苗建民 (Miao Jianmin) & 余君岳 (Yu Junyue) (1996). 《景德镇青花瓷器无损分析研究》. *故宫博物院院刊 / Palace Museum Journal*, 1996(2), starts p. 86. DOI: **not found**. [Museum record](https://www.dpm.org.cn/protect/talk/203155.html); [p. 88 URL](https://www.dpm.org.cn/Uploads/pdf/1509/T00088_00.pdf). Indexed text consulted; thickness statement cites earlier literature and is not a direct SEM result.
[^S9]: Jun Sun, Qijiang Li, Xiaoyan Xia, Min Tang, Yan Liang & Linxin Ouyang (2026). “Effect of Luanbai Glaze on the Coloration of Cobalt Pigment in Yuan Dynasty Jingdezhen Porcelains: An Experimental Study.” *Materials* 19(11), 2254. DOI: [10.3390/ma19112254](https://doi.org/10.3390/ma19112254). [Publisher](https://www.mdpi.com/1996-1944/19/11/2254); [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC13257541/). Tables 3/5, Fig. 2 and methods inspected.
[^S10]: Luís F. Vieira Ferreira, Isabel Ferreira Machado, Rosa Varela Gomes, Mário Varela Gomes & Manuel F. C. Pereira (2025). “An Archaeometric Study of Twelve Porcelain Chinese Sherds Found at the Santana Convent in Lisbon—16th to 18th Centuries.” *Heritage* 8(7), 253. DOI: [10.3390/heritage8070253](https://doi.org/10.3390/heritage8070253). [Publisher](https://www.mdpi.com/2571-9408/8/7/253). Indexed primary text/caption consulted; direct access rate-limited. CC BY 4.0.
[^S10p]: Luis Filipe Vieira Ferreira, Isabel Luisa Ferreira Machado, Rosa Varela Gomes, Mário Varela Gomes & Manuel Francisco Costa Pereira (2025). “An Archaeometric Study of Twelve Porcelain Chinese Sherds Found at the Santana Convent in Lisbon – – 16th to 18th Centuries.” *Preprints.org*, author manuscript, posted 3 June; no journal for this version, **not peer reviewed**. DOI: [10.20944/preprints202505.2496.v1](https://doi.org/10.20944/preprints202505.2496.v1). [Manuscript, figures and CC BY 4.0 statement](https://www.preprints.org/manuscript/202505.2496). The page links the published version above.
[^S11]: Caishui Jiang, Junming Wu, Lingfei Yu, Tianwei Zhao, Ting Luo, Guangyao Wang & Naizhang Zheng (2026). “Interpreting the firing technology logic of the Jingdezhen egg-shaped kiln through experimental archaeology.” *npj Heritage Science* 14, 465. DOI: [10.1038/s40494-026-02801-3](https://doi.org/10.1038/s40494-026-02801-3). [Publisher](https://www.nature.com/articles/s40494-026-02801-3). Fig. 8h/Table 4; experimental celadon mechanism only. Article licence is CC BY-NC-ND 4.0, **not** eligible for the requested image list.

[^C1]: 陈尧成 (Chen Yaocheng), 郭演仪 (Guo Yanyi) & 张志刚 (Zhang Zhigang) (1978). 《历代青花瓷器和青花色料的研究》. *硅酸盐学报 / Journal of the Chinese Ceramic Society* 6(4), 225–241 + 323–327. DOI: **not found**. [Primary publisher record and abstract](https://jccsoc.cbpt.cnki.net/portal/journal/portal/client/paper/3fab8b7e5c98d4c378af999e49035cd3). Chinese and English abstracts inspected.
[^C2]: H. S. Cheng, Z. Q. Zhang, H. N. Xia, J. C. Jiang & F. J. Yang (2002). “Non-destructive analysis and appraisal of ancient Chinese porcelain by PIXE.” *Nuclear Instruments and Methods in Physics Research Section B* 190, 488–491. DOI: [10.1016/S0168-583X(01)01280-0](https://doi.org/10.1016/S0168-583X(01)01280-0). [Indexed primary-paper URL](https://www.chineseantiques.co.uk/wp-content/uploads/2012/08/porcelain-analysis.pdf). Table 2 inspected through indexed full-paper text; current URL redirects, reducing auditability.
[^C3]: Ruiqi Zhang & Peter Gethin (2021). “Provenance of the cobalt pigment used for Jingdezhen minyao blue-and-white porcelain in the early Qing dynasty.” *Ceramics International* 47(18), 25763–25768. DOI: [10.1016/j.ceramint.2021.05.303](https://doi.org/10.1016/j.ceramint.2021.05.303). [Publisher](https://www.sciencedirect.com/science/article/pii/S0272884221017041). Abstract/snippets inspected; numeric composition Tables 1–5 not inspected.
[^C4]: Xiaolong Li, Weixia Dong, Qifu Bao, Zhipeng Chen, Yulong Yang, Kun Liu & Jianer Zhou (2025). “Study on cobalt-blue pigment of blue-and-white porcelain from the Zhengde imperial kiln of Ming Dynasty (AD 1506–1521).” *Journal of Ceramic Processing Research* 26(5), 742–753. DOI: [10.36410/jcpr.2025.26.5.742](https://doi.org/10.36410/jcpr.2025.26.5.742). [KCI author abstract](https://www.kci.go.kr/kciportal/landing/article.kci?arti_id=ART003259565). Abstract inspected; full chemistry tables not found.
[^C5]: 李豪 (Li Hao), 方圆 (Fang Yuan), 包启富 (Bao Qifu), 董伟霞 (Dong Weixia), 董文婕 (Dong Wenjie), 陈飘飘 (Chen Piaopiao), 杨晶 (Yang Jing), 顾雨琪 (Gu Yuqi) & 焦玉笛 (Jiao Yudi) (2023). 《Fe₂O₃与MnO₂的含量对霁蓝釉釉色的影响》. *江苏陶瓷 / Jiangsu Ceramics*, issue 3, 38–41. DOI: **not found**. [Primary journal issue URL](https://www.jsgsyxh.org.cn/pic/file/20231018/20231018154069706970.pdf). Indexed text inspected; Chinese/English abstract inconsistency disclosed above.
[^C6]: Mi Luo, Maolin Zhang, Wensheng Yan, Lihua Wang & Zheng Jiang (2018; online 2017). “X-ray absorption spectroscopy study of synthetic cobalt blue pigments similar to Kangxi blue and white porcelain.” *Journal of the American Ceramic Society* 101(5), 2130–2136. DOI: [10.1111/jace.15353](https://doi.org/10.1111/jace.15353). [Publisher](https://ceramics.onlinelibrary.wiley.com/doi/10.1111/jace.15353). Primary abstract inspected.

[^P1]: Victoria and Albert Museum (2024, updated 17 April). “Chinese blue-and-white ceramics.” Museum educational article; no journal/DOI. [Article](https://www.vam.ac.uk/articles/chinese-blue-and-white-ceramics).
[^P2]: 吕成龙 (Lü Chenglong), undated. 《青花松竹梅纹诗句观音尊》, accession 新00136736, including 分水技法 glossary. Palace Museum catalogue; no journal/DOI. [Object/glossary](https://www.dpm.org.cn/collection/ceramic/227862.html).
[^P3]: University of Michigan Museum of Art, undated. “Vase,” accession 1982/1.217. Museum catalogue; no journal/DOI. [Object](https://umma.umich.edu/objects/vase-1982-1-217/).
[^P5]: Palace Museum, undated. 《青花缠枝莲纹长颈瓶》, 新00095997, Kangxi. Museum catalogue; no journal/DOI. [Object](https://digicol.dpm.org.cn/cultural/detail?id=6ef09c874234456e96cf51b0d8ac7c9d).
[^P6]: Palace Museum, undated. 《青花云龙纹天球瓶》, Kangxi. Museum catalogue; no journal/DOI. [Object](https://digicol.dpm.org.cn/cultural/detail?id=a21c52f07e8b477689fae902bbd3407e).
[^P7]: Ron Fuchs II (2024). “Kangxi Blue-and-White.” *The Royal Dresden Porcelain Collection*, digital scholarly museum catalogue; no journal. [Catalogue chapter](https://royalporcelaincollection.skd.museum/catalogue/1/text/122); chapter description inspected.

[^I1]: Metropolitan Museum of Art, undated collection record. “Vase with Flowering Plants and Birds,” 14.40.276. Museum catalogue; no journal/DOI. [Object](https://www.metmuseum.org/art/collection/search/42204). Original image URL located in web image index; no binary request made.
[^I2]: Metropolitan Museum of Art, undated collection record. “Plate with cartouches of women and plants,” 18.61.2. Museum catalogue; no journal/DOI. [Object](https://www.metmuseum.org/art/collection/search/47583). Original image URL located in web image index; no binary request made.
[^I3]: Metropolitan Museum of Art, undated collection record. “Vase with landscape scenes,” 14.40.424. Museum catalogue; no journal/DOI. [Object](https://www.metmuseum.org/art/collection/search/46094). Original image URL located in web image index; no binary request made.
[^I4]: Cleveland Museum of Art, undated collection record. “Vase with Cover,” 1954.575. Museum catalogue; no journal/DOI. [Object](https://www.clevelandart.org/art/1954.575); [Commons JPEG metadata](https://commons.wikimedia.org/wiki/File:Clevelandart_1954.575.jpg); [category listing larger TIFF](https://commons.wikimedia.org/wiki/Category:Porcelain_vases_in_the_Cleveland_Museum_of_Art). Use the museum's Kangxi date rather than Commons' single-year 1661 metadata.
[^I5]: Cleveland Museum of Art, undated collection record. “Vase with Cover (lid),” 1954.575.b; photograph attributed to Gary Kirchenbauer in Commons metadata. Museum catalogue; no journal/DOI. [Object](https://www.clevelandart.org/art/1954.575.b); [Commons JPEG metadata](https://commons.wikimedia.org/wiki/File:Clevelandart_1954.575.b.jpg); [larger TIFF category listing](https://commons.wikimedia.org/wiki/Category:Porcelain_vases_in_the_Cleveland_Museum_of_Art).
[^I6]: wangzhao (2012). “China 青花花瓶01.JPG.” Wikimedia Commons photograph/file record; no journal/DOI. [File metadata](https://commons.wikimedia.org/wiki/File:China_%E9%9D%92%E8%8A%B1%E8%8A%B1%E7%93%B601.JPG); [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/).
[^I7]: Metropolitan Museum of Art, undated current policy. “Image and Data Resources.” Institutional policy; no journal/DOI. [Open Access image policy](https://www.metmuseum.org/policies/image-resources). Consulted 2026-10-28.
