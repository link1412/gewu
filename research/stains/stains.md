| phase | spectrum source | sample and grain size | file name | tag |
|---|---|---|---|---|
| lepidocrocite-bearing mixture | USGS v7, pinned mirror¹; Beckman | GDS80 (synthetic); size **not found**; XRD: lepidocrocite + goethite in subequal proportions | `raw/lepidocrocite/splib07a_Lepidocrocite_GDS80_(Syn)_BECKb_AREF.txt` | [M]; **not a pure-phase spectrum** |
| hematite | USGS v7, pinned mirror¹; Beckman | GDS69.g, nominal <10 μm fraction; microscopy average 10.5 μm, trace quartz | `raw/hematite/splib07a_Hematite_GDS69.g_lt10um_BECKb_AREF.txt` | [M] |
| goethite, preferred powder | USGS v7, pinned mirror¹; ASD full range | GDS134, brown powder; numeric grain size **not found** | `raw/goethite/splib07a_Goethite_GDS134_ASDFRb_AREF.txt` | [M] |
| pyrite | USGS v7, pinned mirror¹; ASD full range | GDS483.c, 30–60 μm; minor szomolnokite and rhomboclase | `raw/pyrite/splib07a_Pyrite_GDS483.c_30-60um_ASDFRc_AREF.txt` | [M] |
| black carbon | USGS v7, pinned mirror¹; ASD full range | GDS68, carbon black; SEM spheres 0.17 μm, larger clumps | `raw/carbon/splib07a_Carbon_Black_GDS68_ASDFRa_AREF.txt` | [M] |
| goethite + clay pigment, comparison | USGS v7, pinned mirror¹; ASD full range | Italian natural sienna GDS805, dry powder; grain size and Fe₂O₃ wt% **not found** | `raw/sienna/splib07a_Italian_nat_sienna_GDS805_ASDFRa_AREF.txt` | [M]; analogue relevance [I] |
| goethite-bearing fine coating, comparison | USGS v7, pinned mirror¹; Beckman | MPCMA2-B, visually fine rock coating; numeric size **not found**, host-rock contribution | `raw/goethite/splib07a_Goethite_MPCMA2-B_FineGr_adj_BECKb_AREF.txt` | [M]; **not pure powder** |

# Guan/Ge crackle stains: measured data and remaining gaps

Research date: 2026-10-28. Tags: **[M]** measured/reported characterization in the cited source; **[D]** figure or secondary/index-derived reading; **[A]** abstract only; **[I]** inference, access assessment, or processing. Table tags apply to all factual contents in that row. Interpolated numbers below carry [M→I]: measured inputs, computationally resampled outputs. Missing measurements are explicitly **not found**.

[I] **Recommendation:** use the supplied powder spectra as material reference inputs, with the sample caveats below; treat cell-size and crack-depth parameters as unresolved calibration tasks. The GDS80 column is a measured mixture, not a pure lepidocrocite endmember. No synthetic measurements were substituted for missing data.

[I] Completed: seven numerical spectra, saved source ASCII and metadata, wavelength pairing, reproducible interpolation, and dimensional/résidue findings with access qualifications. Still incomplete: pure lepidocrocite, direct calibrated line colour, verified gold/black cell-size distributions, and stain depth.

## 1. Reflectance spectra

### Sources, provenance and sample selection

[M] The saved sample descriptions identify their source as R. F. Kokaly, R. N. Clark, G. A. Swayze, K. E. Livo, T. M. Hoefen, N. C. Pearson, R. A. Wise, W. M. Benzel, H. A. Lowers, R. L. Driscoll & A. J. Klein, **USGS Spectral Library Version 7**, U.S. Geological Survey Data Series 1035 (2017), 61 pp., DOI [10.3133/ds1035](https://doi.org/10.3133/ds1035). Data-release locator: [10.5066/F7RR1WDJ](https://doi.org/10.5066/F7RR1WDJ).

[I] ¹The actual files and USGS-authored metadata were **opened and retrieved from a third-party mirror**, pinned at [EX-spec revision 06598564cd6cb19cfd3663cb732f759c821bd83c](https://github.com/Skylar-TyZhang/EX-spec/tree/06598564cd6cb19cfd3663cb732f759c821bd83c). Official USGS hosts returned access errors; the mirror could not be checksum-compared with an official archive. This transport limitation does not turn the file values into digitised data, but it limits provenance verification. Exact mirror paths are in [raw/README.md](raw/README.md); original text payloads, sample HTML and local checksums are retained.

[M] **Lepidocrocite:** [saved USGS sample description](raw/lepidocrocite/Lepidocrocite_GDS80_(Syn)_BECKb_AREF.html), record 6355. Its XRD section reports subequal lepidocrocite and goethite, with broad/weak reflections. Its spectral discussion explicitly says interference by goethite is unknown. [I] A phase-pure γ-FeOOH spectrum is therefore **not found** in the acquired material; do not label this column pure γ-FeOOH. No subtraction or unmixing was attempted.

[M] **Hematite:** [saved description](raw/hematite/Hematite_GDS69.g_lt10um_BECKb_AREF.html), record 4976. GDS69.g is the finest of seven listed sieve fractions. Its nominal <10 μm label and the microscopy mean 10.5 μm are both preserved rather than silently reconciled. Trace quartz is reported.

[M] **Goethite:** [GDS134 description](raw/goethite/Goethite_GDS134_ASDFRb_AREF.html), record 4347, describes brown powder. Its XRD history includes contradictory earlier identifications but concludes that recent XRD indicates pure goethite; a slight OH-bearing contaminant is mentioned spectroscopically. [I] This is the preferred powder reference. The separately saved [MPCMA2-B description](raw/goethite/Goethite_MPCMA2-B_FineGr_adj_BECKb_AREF.html), record 4390, describes a visually fine coating with muscovite/other host minerals; its near-IR bands include host-rock contributions. It is a comparison, not the preferred phase endmember.

[M] **Pyrite:** [saved description](raw/pyrite/Pyrite_GDS483.c_30-60um_ASDFRc_AREF.html), record 8972. The available spectrum is GDS483.c, 30–60 μm; XRD also finds minor sulfate phases. Its metadata lists a 20–30 μm fraction in the sample series, but that fraction has no matching acquired v7 spectrum in the inspected mirror tree. [I] Thus 30–60 μm is the finest explicitly size-fractioned pyrite spectrum located here, not a claim that no finer pyrite measurement exists elsewhere.

[M] **Carbon black:** [saved description](raw/carbon/Carbon_Black_GDS68_ASDFRa_AREF.html), record 2320. GDS68 is synthetic carbon black, manufacturer composition 99.0 wt% C, 0.5 wt% ash and 0.5 wt% acetone-extractable material. SEM gives spherical grains of 0.17 μm, with larger clumps. The metadata warns that the older Clark 1983 spectrum was too reflective because of stray light; the supplied column is the v7 ASD file. [I] It is an optical reference, not a measured identification of the historical carbon deposit.

### Iron-stained clay / soil comparison

[M] [Italian natural sienna GDS805](raw/sienna/Italian_nat_sienna_GDS805_ASDFRa_AREF.html), record 18861, is a measured dry powdered Kremer pigment described as goethite and clays. Its spectrum has goethite absorptions; the metadata discusses possible montmorillonite with less kaolinite. [I] This supplies an actual clay-bearing earth-pigment spectrum for comparison. A matching **5–7 wt% Fe₂O₃**, lepidocrocite/hematite-stained clay or soil spectrum is **not found**. Sienna Fe₂O₃ concentration is **not found** and its phase assemblage differs from the requested deposit.

### Wavelength and reflectance columns; processing

[M] The raw files have **one numeric column**, preceded by one header line. For the three `BECK...` files, pair with `raw/wavelengths/splib07a_Wavelengths_BECK_Beckman_0.2-3.0_microns.txt` (480 channels). For the four `ASDFR...` files, pair with `raw/wavelengths/splib07a_Wavelengths_ASD_0.35-2.5_microns_2151_ch.txt` (2151 channels). The headers identify Beckman and ASD wavelength grids, respectively. Numeric wavelengths are in **μm**, not nm. The spectrum numeric column contains the AREF values.

[I] [stain_spectra.csv](stain_spectra.csv) uses **350–800 nm inclusive, every 10 nm** (46 rows). Convert the wavelength column by ×1000, then interpolate piecewise linearly between valid native samples. Preserve the reflectance fractions without normalisation, percent conversion, smoothing, clamping or extrapolation. Native wavelengths within 0.0001 nm of a target are treated as exact to avoid float-storage artefacts. The `-1.23e34` sentinel is excluded; no target used an invalid interpolation endpoint. Thus all requested 400–750 nm rows are present.

[I] Verification: every spectrum length matches its wavelength grid, all grids increase strictly, and all 322 output reflectances are finite and within 0–1. All 16 saved ASCII/HTML files match the pinned mirror's Git blob SHA-1 and byte size; this verifies retrieval from that revision, not agreement with the inaccessible official archive. Offline regeneration: `python3 scripts/build_stain_spectra.py`. [Manifest](raw/spectra_manifest.json) records input columns, pairings and local hashes; [mirror checksums](raw/mirror_file_checksums.json) retain source paths and blob hashes. Instruments are identified at the family/code level above; exact model, illumination/view geometry, calibration standards and uncertainty for these particular measurements were **not verified** in this session.

[I] **Rendering limit:** these are sample reflectance measurements, not validated intrinsic Lambertian wall albedos for thin deposits under glaze. Layer thickness, substrate scattering, optical geometry and glaze propagation need a separate material model. Do not infer a 5–7 wt% deposit spectrum by linearly mixing reflectances using EDS oxide percentages; no measured optical mixing law or deposition thickness is supplied here.

[M→I] Selected CSV values (fractions; full precision in CSV):

| wavelength_nm | GDS80 lepidocrocite + goethite | hematite <10 μm | goethite powder | pyrite 30–60 μm | carbon black | sienna | fine goethite coating |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 400 | 0.01261520 | 0.04120612 | 0.01761866 | 0.03503605 | 0.01981914 | 0.02692564 | 0.04052444 |
| 450 | 0.02287359 | 0.04231077 | 0.02348298 | 0.03877886 | 0.01932722 | 0.04670810 | 0.05714074 |
| 550 | 0.11897828 | 0.04049274 | 0.07292188 | 0.04704689 | 0.01906561 | 0.12165118 | 0.14945525 |
| 650 | 0.26737081 | 0.06159111 | 0.12044755 | 0.04835805 | 0.01896323 | 0.22505892 | 0.26369602 |
| 750 | 0.35032824 | 0.11157476 | 0.16394541 | 0.04795306 | 0.01886783 | 0.29788086 | 0.34555318 |

## 2. Measured colour of the stained lines themselves

[I] Guan/Ge **金丝 or 铁线 L*a*b*, calibrated RGB, or measured line reflectance: not found** in the material successfully inspected. Qualitative colour names, Raman shifts and bulk-glaze colour are not numerical colour measurements of the lines. The CSV is phase/sample reference data, not measured historical-line colour. No RGB values were sampled from uncalibrated photographs.

[A] A newly located CNKI abstract is 桑振、陈丹妮、王学武、昝硕斐、袁小娟、桑袁成林、付向阳, **《南宋哥窑“金丝铁线”的真伪鉴别研究》**, *中国陶瓷* **62(5)** (2026), 102–112, DOI [10.16521/j.cnki.issn.1001-9642.2026.05.012](https://doi.org/10.16521/j.cnki.issn.1001-9642.2026.05.012). The [CNKI journal page](https://zgtc.cbpt.cnki.net/portal/journal/portal/client/paper/cf5f43355bc76f23d2999de24a383a17) opened successfully; only the abstract was accessible. It reports microscopy, oxide-composition comparisons and Raman analysis. Numerical line colour, cell sizes, apertures or stain depths are **not found in the accessible abstract**; their absence from the full paper is not established.

[I] Chinese queries covered 金丝铁线 with 色度, L*, 色差, 反射光谱, and university/CNKI domains; no usable numerical university-repository result was verified. This limited search is not proof that no such measurement has been published.

## 3. Crackle cell sizes and glaze thickness

[D] Sophia Lahlil, Weidong Li & Ji Ming Xu, **“Crack patterns morphology of ancient Chinese wares,”** *The Old Potter’s Almanack* **18(1)** (2013), 1–9, DOI [10.11588/opa.2013.1.11773](https://doi.org/10.11588/opa.2013.1.11773). [Heidelberg original](https://journals.ub.uni-heidelberg.de/index.php/opa/article/download/11773/5630); [alternate PDF](https://www.dstretch.com/Lahlil%20et%20al.%20OPA%2018.1.pdf).

[D] **Provisional, index-derived result:** p. 5 gives a characteristic distance **l = √(A/N) = 0.17–1.41 cm**, converted to **1.7–14.1 mm**, with A the observed area and N the domain count. The indexed methods describe 23 excavated Song/Yuan sherds, 46 inner/outer glaze surfaces, from Jiaotanxia, Laohudong and Fenghuang hill, covering Guan and imitation Guan. Paired archaeological glaze thickness values: **not found**.

[I] This range describes a statistical cell-spacing measure across analysed surfaces. It is not an individual-cell diameter range and does not separate gold-thread/iron-wire networks or securely attributed heirloom Ge. It can be retained as a provisional scale clue, **not a verified rendering specification**.

[I] Access limitation: the alternate PDF opened and was identified as nine pages, but returned no readable text or usable screenshot; numerical content was available only through search-index excerpts. This falls short of the requested direct source-content verification. The extracted record in `raw/crackle_sources/lahlil_2013_index_extracted.json` is explicitly **not an original PDF**. Confirmed gold and black network cell-size distributions, cell-size/glaze-thickness pairs, and numerical fish-roe/百圾碎/蟹爪纹 categories: **not found**. No simulation or modern-replica dimensions were silently substituted.

## 4. Crack opening at the surface and stain depth

[M] Li et al. (2022), source in §5, studied **GW-1, Song Guan from Jiaotanxia**, and **GT-1, Ge-type from a Ming tomb at Jingdezhen**. SEM sections report brown cracks from **<70 μm to >400 μm** internally, about **63 μm at the surface**; GT-1 black cracks exceed **400 μm at the surface** and narrow inward. [I] These sparse measurements are sample-specific, not distributions; the Ming black-crack value is not a Southern Song Guan parameter. Quantitative **stain penetration depth: not found**. A numerical depth describing EDS sampling is not stain depth.

[D] Additional **unverified figure-label lead**: 贾翠、张雪雁、丁银忠、陈铁梅, **《无损分析方法在宋代冰裂纹青瓷研究中的应用》**, *故宫学刊* (2016), DOI and complete page range **not found / not verified**. [Museum landing page](https://www.dpm.org.cn/research_talk/252220.html), [PDF](https://www.dpm.org.cn/Uploads/File/2020/03/31/u5e82bd5beacda.pdf). Indexed p. 308, Fig. 7, lists Guan/Laohudong profile widths **a = 14.110 μm, b = 9.375 μm** with Olympus OLS4000 laser confocal microscopy. Actual figures could not be inspected; the labels may describe profilometry cursor extents. **Confirmed surface aperture from this study: not found. Do not use these labels as verified crack openings.** Extracted record: `raw/crackle_sources/jia_2016_index_extracted.json`.

## 5. Li, Yuan, Cao & Hein (2022): open text and crack fillings

[M] Zihan Li, Feng Yuan, Jianwen Cao & Anke Hein, **“Insights into the Residue Trapped in Glaze Cracks of Archaeological Ceramics Using Microchemical Analysis,”** *Microscopy and Microanalysis* **28(6)** (2022), 1878–1889, DOI [10.1017/S1431927622012375](https://doi.org/10.1017/S1431927622012375). [Author-uploaded full text on ResearchGate](https://www.researchgate.net/publication/363317892_Insights_into_the_Residue_Trapped_in_Glaze_Cracks_of_Archaeological_Ceramics_Using_Microchemical_Analysis) was opened and read, including Methods, SEM results and Discussion. [Oxford repository record](https://ora.ox.ac.uk/objects/uuid:4147a86e-094d-44e3-9d39-03c89b300e47) and [accepted-manuscript PDF locator](https://ora.ox.ac.uk/objects/uuid:4147a86e-094d-44e3-9d39-03c89b300e47/files/s2b88qd441) were located but returned 403; no original PDF was saved.

[M] Brown residues are Si/Al rich; GT-1 black residue gives average **76.48% carbon**, **0.46% silicon** by EDS. [I] The authors propose soil ingress for brown cracks and intentional carbon staining, possibly inkstick, for black cracks; ink identity remains a hypothesis. The brown/black shape differences also challenge a uniform parallel-wall model. These measurements concern the two sherds above, not direct analysis of a Southern Song heirloom Ge vase.

## Access, budget and practical gaps

[I] Raw numerical files are present under `raw/`, one material per folder, plus shared wavelengths. Original paper PDFs are **not** present. Search-index extracts are separately labelled. Local shell networking failed through the configured proxy; disabling it caused DNS failure. Browser control did not establish a working browser. The GitHub connector finally enabled retrieval of text data and metadata.

[I] Broad searching stopped once the usable spectral files and limited dimensional evidence were obtained.

[I] Biggest unresolved inputs, in priority order: **pure lepidocrocite reflectance; direct stained-line reflectance/colour; a measured 5–7 wt% Fe₂O₃ clay analogue; separate black/golden cell statistics with glaze thickness; numerical stain penetration depth**. The saved data can drive spectral material trials immediately, but they do not close those gaps.
