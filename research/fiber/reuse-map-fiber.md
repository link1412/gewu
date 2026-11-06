# Recommended pbrt-v4 stack for shots 13, 24 and 36

[I] **Recommendation:** reuse procedural yarn geometry for explicit stitches, use pbrt `hair` as the immediately available transmission-capable baseline, and evaluate the published 2020 ply model / 2025 yarn implementation before committing shot 24. **No verified, commercially cleared, turnkey spectral silk-and-gauze package was found.** A native `hair` proxy is an implementation starting point, not a measured silk fit or evidence that the photographic target is met.

| Shot | Geometry / generator | BSDF and numerical starting point | Sources, conditions and remaining work |
|---|---|---|---|
| **13 — close 苏绣, 劈丝, frame/edge** | [I] Reuse Zhao–Luan–Bala's procedural yarn family, subject to its unresolved code licence; map fibres onto individually authored stitch paths and flatten low-twist split bundles. Explicitly model the visible frame arc, cloth edge and stitch entry/exit points. Export resolved fibres as pbrt `curve`, initially `type="flat"` for the native hair model. | [I] Baseline `hair`: `eta=1.56`, `alpha=0°`, `beta_m=beta_n=0.1`. These are proposed proxy values, **not a silk calibration**; the two roughness values have no verified mapping from the cited silk models. For an undyed diagnostic, explicitly set `sigma_a=0`; dyed floss spectral absorption: **not found**. | [D] [Zhao project](https://www.cs.cornell.edu/projects/ctcloth/); [pbrt curve/hair interface](https://pbrt.org/fileformat-v4); [Aliaga optical-property lead](https://graphics.unizar.es/projects/clothEGSR17/). [I] Set bundle width, filament count and twist from the actual split floss/reference; those Suzhou-specific measurements are **not found**. Use RGL or Irawan only for unresolved backing cloth, never to replace the visible stitches/edge. |
| **24 — back-lit 双面绣 on 绡/纱** | [I] Reuse the same fibre generator for front/back stitching and an explicit sparse warp/weft substrate. Keep openings empty and connect actual front/back stitch paths rather than duplicating an opaque embroidered plane. | [I] Preferred model family to evaluate: **Montazeri et al. 2020**, which separates specular/body reflection and transmission; the later **Khattar et al. 2025 BYSDF** has a public Mitsuba 3 implementation. Neither is a built-in pbrt material. Native fallback: the silk `hair` proxy above, including TT/internal orders. Gauze-specific fitted roughness, optical density, spacing and dye spectra: **not found**. | [M] The [2020 paper](https://projects.shuangz.com/practical_cloth-sa20/practical_cloth-sa20-ld.pdf), Figs. 7–9, compares measurements/photographs, including front/back lighting. [I] This is stronger supporting evidence than a reflectance-only preset, but does not validate this specific sheer silk gauze. [D] [2025 paper/code](https://arxiv.org/html/2401.12724v2); code licence **not found**. [I] Porting and spectral validation remain necessary. |
| **36 — white 羊毫 tip on dark background** | [I] Reuse a curve/groom generator for an aligned brush bundle, with individual tapered tips. pbrt `curve` widths can vary along a segment; multiple segments can approximate a measured taper. Goat-hair diameter distribution and taper law for the actual brush: **not found**. | [D] Native `hair` defaults: `eta=1.55`, `beta_m=0.3`, `beta_n=0.3`, `alpha=2°`. [I] Retain these as an explicitly provisional baseline and set a constant `sigma_a=0` for the ideal unpigmented limit. White-goat measurements for all five controls: **not found**. | [D] [pbrt defaults](https://pbrt.org/fileformat-v4) and [hair assumptions](https://pbr-book.org/4ed/Reflection_Models/Scattering_from_Hair). [I] A white, medullated animal hair can require internal scattering that native `hair` omits. Do not substitute mohair/cashmere diameter or the width of the whole brush for an individual 羊毫 fibre. |

[I] **Why this direction:** explicit curves preserve the silhouettes, stitch relief and open gaps needed by these shots; mature aggregated ply/yarn models offer a documented alternative when the native cylindrical proxy fails. Adding a generic isotropic volume to a solid gauze sheet would introduce new unmeasured parameters without supplying the missing weave geometry.

[I] **Checkable acceptance test for later implementation:** render a crop containing the real edge/tip and a short light/camera movement; compare front-lit and back-lit versions with one material parameter set. Inspect highlights, transmitted-light direction/colour, gap visibility, edge silhouette and temporal stability after the stated camera simulation and 1080p, 5.1 Mb/s H.264 encoding. Stop the native silk-proxy route if one parameter set cannot match both lighting conditions; evaluate the published aggregate model instead of repeatedly tuning the proxy. No reference frames or scene were supplied here, so that visual match has **not** been tested.

## Evidence key and scope

[D] Research date: 2026-10-28. [M] = measurements or fits to measurements in the cited paper; [D] = model descriptions, implementation defaults, source metadata or secondary descriptions; [A] = abstract-only evidence; [I] = inference or proposed choice. A paper's imported textile-literature values are tagged [D], not misrepresented as that paper's own experiment. “**not found**” means not recovered in this bounded search, not proof that the information does not exist.

[D] Sources were searched in English and Chinese, including CNKI-targeted searches, Chinese journal sites and university repositories. Every linked source was opened or explicitly attempted; unsuccessful opens and index-only evidence are identified below. Large PDFs, access checks and timeouts prevented some primary-text verification. [I] The 2018–2026 coverage is selective, not an exhaustive bibliography. The three already-found papers in the brief are not repeated as research results.

[D] No third-party code or code/data archives were downloaded or executed. Source files were viewed on the web for provenance and licensing. This document was saved during research and then consolidated.

## 1. Fibre-level appearance models and fitted silk parameters

### Sadeghi, Bisker, De Deken & Jensen — 2013

[D] **A Practical Microcylinder Appearance Model for Cloth Rendering**, ACM TOG 32(2), Art. 14. DOI [10.1145/2451236.2451240](https://doi.org/10.1145/2451236.2451240). [Readable author/university PDF](https://datarepo.eng.ucsd.edu/~henrik/papers/practical_microcylinder_appearance_model_for_cloth_rendering.pdf), §4.3, Table II.

[D] Thread-level equations (Eqs. 2–4):

\[
f_{r,s}=F_r\cos(\phi_d/2)g(\gamma_s,\theta_h),\qquad
f_{r,v}=F\frac{(1-k_d)g(\gamma_v,\theta_h)+k_d}{\cos\theta_i+\cos\theta_r}A,
\quad f_s=\frac{f_{r,s}+f_{r,v}}{\cos^2\theta_d}.
\]

[D] `g`: normalized Gaussian; `F`: entry/exit Fresnel transmission.

| Table II silk thread | η | A, RGB coefficient | kd | γs / γv (degrees) | fraction a | tangent offsets (degrees); relative lengths |
|---|---:|---|---:|---|---:|---|
| [M] Crepe-de-Chine flat | 1.345 | (1,0.95,0.05)×0.12 | 0.2 | 5 / 10 | 0.75 | −35,−35,35,35; 1,1,1 |
| [M] Crepe-de-Chine twisted | 1.345 | (1,0.95,0.05)×0.16 | 0.3 | 18 / 32 | 0.25 | 0,0; 1 |
| [M] Shot-silk direction 1 | 1.345 | (0.1,1,0.4)×0.2 | 0.1 | 4 / 8 | 0.86 | −25,−25,25,25; 1.33,2.67,1.33 |
| [M] Shot-silk direction 2 | 1.345 | (1,0,0.1)×0.6 | 0.1 | 5 / 10 | 0.14 | 0,0; 1 |

[D] Includes thread internal/forward scattering; validated gauze BTDF: **not found**. [I] Fitted η is not physical fibroin IOR; distant-thread assumptions do not establish close embroidery fidelity. [D] Released code/data licence: **not found**.

### Aliaga, Castillo, Gutierrez, Otaduy, Lopez-Moreno & Jarabo — 2017

[D] **An Appearance Model for Textile Fibers**, CGF 36(4), 35–45, DOI [10.1111/cgf.13222](https://doi.org/10.1111/cgf.13222). [Author page](https://graphics.unizar.es/projects/clothEGSR17/) opened; [author PDF](https://graphics.unizar.es/papers/aliaga_egsr17.pdf) exceeded reader size limits. **The following numerical/equation evidence is index-only primary-PDF text, not a successfully read full PDF.**

| Imported silk property, Table 1 [D] | Value |
|---|---|
| diameter; density | 5–10 µm; 1.34 g/cm³ |
| η∥; η⊥ | 1.591; 1.538 |
| Ra; profile length l; tabulated β | 8–9 nm; 30 nm; 6–7° |

[D] Indexed equations: `μa=κε`, `κ=ρζ`, with μa in m⁻¹, κ in g/L, ε in L·g⁻¹·m⁻¹; `β=atan(Ra/l)`. Noncircular fibre cross-sections, rough dielectric interfaces and absorption generate a **tabulated four-dimensional BCSDF**, including transmission, using photon tracing. It is not a closed-form silk fit. [I] The indexed Ra/l and β entries appear numerically inconsistent; verify before implementing.

[D] The opened project page restricts code/BCSDF delivery to request, free for non-commercial purposes. Commercial licence: **not found**. [I] Best fibre-physics lead here, but neither open-source availability nor a gauze-specific back-lit validation was established.

### Irawan & Marschner — 2012; Mitsuba 0.5 `irawan`

[D] **Specular Reflection from Woven Cloth**, ACM TOG 31(1), DOI [10.1145/2077341.2077352](https://doi.org/10.1145/2077341.2077352). The opened [Cornell author abstract](https://www.cs.cornell.edu/~srm/publications/TOG12-cloth.html) describes a procedural woven-cloth reflectance model validated against measurements and fabric video. [A] It does not provide the requested numerical silk fit or equations.

[D] The opened [Mitsuba C++ plugin](https://github.com/mitsuba-renderer/mitsuba/blob/master/src/bsdfs/irawan.cpp) names **silk charmeuse** and **silk shantung**, and loads external weave files. Its registered components and evaluation are reflection-only; below-surface directions return zero. [D] Full analytical equation, numeric 0.5 silk preset files, original fitted units: **not found** in successfully read sources. [I] Do not invent `alpha`, `beta`, twist or highlight-width values from example images.

[D] [ThunderLoom](https://github.com/Thunderloom/ThunderLoom) supplies an MIT-licensed Irawan library with WIF weave input and renderer frontends. [I] Useful for opaque, unresolved woven backing; neither a silk-fibre transmission model nor direct pbrt-v4 support was verified.

### Newer, materially relevant alternatives — 2018–2026

[D] **Zahra Montazeri, Søren B. Gammelmark, Shuang Zhao & Henrik Wann Jensen, A Practical Ply-Based Appearance Model of Woven Fabrics**, TOG 39(6), Art. 251 (2020), DOI [10.1145/3414685.3417777](https://doi.org/10.1145/3414685.3417777). [Full reduced-size PDF](https://projects.shuangz.com/practical_cloth-sa20/practical_cloth-sa20-ld.pdf) opened.

[D] Near-field aggregate model: `f_x=f_x^S+f_x^B`, with corresponding specular/body terms at transmitted exit point `y`; anisotropic rough dielectric specular transport and an approximate multiple-scattering body. Round plies use curves; flat yarns use bilinear patches plus fibre-detail maps. [M] §6.1 compares a silk TAC7 reflectance scan; §6.2/Fig. 9 fits front/back-lit photographs. [D] The paper does not establish that every photographed satin is silk. Numerical fitted silk/gauze preset, code/data licence and open repository: **not found**. [I] Strongest opened validation of the required reflection-plus-transmission behavior, subject to implementation access.

[D] **Apoorv Khattar et al., A Multi-scale Yarn Appearance Model with Fiber Details**, [arXiv:2401.12724v2](https://arxiv.org/html/2401.12724v2), revised 18 March 2025 (first posted 2024); final journal DOI: **not found**. [D] BYSDF implicitly resolves plies/fibres with explicit yarn curves and four specular/body forward/backward components:

\[
f_x=f_x^S+f_x^B,\qquad
f_y=\int_{\Omega_y}(f_{\hat y}^S+f_{\hat y}^B)\rho_y(\hat y)d\hat y,
\qquad \tau(x,y)=e^{-\sigma_t\|x-y\|}.
\]

[D] σt uses inverse geometry-length units; no portable silk spectral σt was recovered. [M] Fig. 14 compares rayon 2-ply and silk 3-ply photographs using prior fibre data. [D] The paper acknowledges approximate multiple-scattering energy loss and missing flyaways. Its [public Mitsuba 3 repository](https://github.com/apoorvkhattar/yarn_model_mitsuba3/tree/master) was opened; it calls itself initial code and lists scene/documentation TODOs. Licence and last commit date: **not found**. [I] A concrete porting lead, not a ready pbrt-v4 material or validated sheer-silk preset.

[I] The scalar native silk proxy also omits silk birefringence and any polarization effects, which the stated pbrt-v4 pipeline cannot reproduce.

[I] **Selection:** Sadeghi/Irawan are useful reflection references; Aliaga targets constituent physics; Montazeri/Khattar target aggregate reflection and transmission. None supplies a verified split-floss-plus-gauze spectral fit for these shots. A reported roughness angle, a Gaussian width, GGX roughness and pbrt `beta_m/n` are different controls and must not be copied numerically across models.

## 2. Yarn and ply geometry

### Zhao, Luan & Bala — 2016

[D] **Shuang Zhao, Fujun Luan & Kavita Bala, Fitting Procedural Yarn Models for Realistic Cloth Rendering**, TOG 35(4), DOI [10.1145/2897824.2925932](https://doi.org/10.1145/2897824.2925932). Opened [Cornell project](https://www.cs.cornell.edu/projects/ctcloth/) and [author publication list](https://shuangz.com/publications/) advertise CT-fitted procedural yarns, flyaways and a **Code and Data** archive.

| Requested fitted silk parameter | Verified numeric result |
|---|---|
| ply count | [D] Original 2016 fitted table: **not found**. [M] The later Khattar Fig. 14 comparison identifies its inherited silk sample as 3-ply; that is not a recovery of the complete 2016 table. |
| yarn/ply twist or pitch, with units | [D] **not found** |
| fibres per ply / total per yarn | [D] **not found** |
| radial distribution and fibre migration | [D] **not found** |
| yarn radius, ellipse axes, flyaway statistics | [D] **not found** |

[D] The [author PDF](https://projects.shuangz.com/procyarn-sg16/procyarn-sg16.pdf) and Cornell mirror were attempted but rejected as oversized. Archive content/licence was not inspected, in accordance with the no-code-download rule. [I] Do not substitute an illustrative fibre count from another paper or a knitted-cotton preset for these missing fits. Embroidery stitch paths and the split-floss cross-section still require input even with this generator.

### Later generator / ply-based options

| Source | What can be reused | Data, code and gap |
|---|---|---|
| [D] Fujun Luan, Shuang Zhao & Kavita Bala, **Fiber-Level On-the-Fly Procedural Textiles**, CGF 36(4), 2017; DOI [10.1111/cgf.13230](https://doi.org/10.1111/cgf.13230). [Cornell project](https://www.cs.cornell.edu/projects/ctcloth/) opened. | [D] Realizes regular/flyaway fibres during rendering rather than storing all curves. | [D] Code advertised through the author pages; implementation language, licence, last activity: **not found**. [I] Renderer integration is more involved than exporting pre-generated curves. |
| [D] Montazeri et al. 2020, §3 ([PDF](https://projects.shuangz.com/practical_cloth-sa20/practical_cloth-sa20-ld.pdf)). | [D] Ply curves / flat-yarn patches with fibre-detail maps. | [D] Public code/licence: **not found**. [I] Use the model structure as a documented fallback; code availability is unresolved. |

[D] **Elena Trunz, Jonathan Klein, Jan Müller, Lukas Bode, Ralf Sarlette, Michael Weinmann & Reinhard Klein, Neural inverse procedural modeling of knitting yarns from images**, Computers & Graphics 118 (2024), 161–172, DOI [10.1016/j.cag.2023.12.013](https://doi.org/10.1016/j.cag.2023.12.013). [Author PDF](https://jonathank.de/research/paper/Trunz2023_inverse_yarns.pdf) opened. It describes a **Python/Blender hierarchical generator**, elliptical cross-sections, helix mapping, irregularity and flyaways; reflectance inference is future work. [D] Its controls include fibre/ply counts, ellipse radii, helix pitches and jitter. These are procedural controls, not measured silk fits. [D] Public repository URL, code/data licence and last activity: **not found**; a code announcement/article licence is insufficient to establish software rights. [I] A useful generator design/implementation lead, with author access still needed.

## 3. Code, licences, language and last activity

[D] “Last activity” below means a dated commit/release visible in an opened primary source. Publication year, page crawl time and copyright year are not used as substitutes. Unknown dates are explicitly **not found**.

| Artifact / primary URL | Language | Licence verified in opened source | Last activity | pbrt-v4 reuse assessment |
|---|---|---|---|---|
| [D] [Mitsuba `irawan.cpp`](https://github.com/mitsuba-renderer/mitsuba/blob/master/src/bsdfs/irawan.cpp) | C++ [D] | GPL version 3, file header [D] | **not found** [D] | [I] Reference implementation; port required. Licence differs from pbrt's own code. No transmission in this plugin. |
| [D] [ThunderLoom](https://github.com/Thunderloom/ThunderLoom) | Exact language breakdown **not found**; native library/header API described [D] | MIT, repository/README [D] | **not found** [D] | [I] Most permissive verified cloth-shader library here; port and spectral audit required. |
| [D] [Aliaga 2017 author project](https://graphics.unizar.es/projects/clothEGSR17/) | **not found** [D] | Request-only; free non-commercial; commercial terms **not found** [D] | 9 May 2018 dated project update; code commit date **not found** [D] | [I] Do not treat it as an open-source production dependency. |
| [D] [Zhao 2016 Code and Data locator](https://www.cs.cornell.edu/projects/ctcloth/) | **not found** [D] | **not found** [D] | **not found** [D] | [I] Existing generator/data advertised; archive licence must be checked before reuse. |
| [D] [Luan 2017 code locator](https://shuangz.com/publications/) | **not found** [D] | **not found** [D] | **not found** [D] | [I] On-demand procedural integration candidate. |
| [D] [Trunz generator description](https://jonathank.de/research/paper/Trunz2023_inverse_yarns.pdf) | Python / Blender [D] | **not found** [D] | **not found** [D] | [I] Repository not verified; source access unresolved. |
| [D] [Khattar yarn model](https://github.com/apoorvkhattar/yarn_model_mitsuba3/tree/master) | Jupyter workflow; exact plugin-language breakdown **not found** [D] | **not found** [D] | **not found** [D] | [I] Initial Mitsuba 3 code, requires a pbrt port; renderer base licence alone would not establish rights to added files. |
| [D] [RGL `brdf-loader`](https://github.com/rgl-epfl/brdf-loader) | C++ headers, Python/NumPy, Mitsuba plugin [D] | BSD-3-Clause, repository [D] | **not found** [D] | [I] Useful for inspecting/porting measured reflectance; not an embroidery generator or transmission database. |
[I] Public visibility and a paper's “code available” statement do not establish a software licence. For production selection, the unresolved licences above are actual reuse gaps, not a finding that the algorithms cannot be implemented.

## 4. Embroidery-specific work: physical rendering versus NPR

### Chinese journal and university sources

| Opened primary source | What it supplies | Classification; code/data/licence |
|---|---|---|
| [A] **杨克微 / Kewei Yang, 孙正兴 / Zhengxing Sun**, *物像空间依赖的乱针绣针法定义与风格生成 / Vector and Pixel Space Depended Stitch Definition and Style Transfer for Random-Needle Embroidery*, 计算机辅助设计与图形学学报, 2018, DOI [10.3724/SP.J.1089.2018.16471](https://www.jcad.cn/article/doi/10.3724/SP.J.1089.2018.16471). Publisher abstract opened. | [A] Vector-space stitch orientation/intersection/length/width, rasterization, stitch dictionary and sparse image coding. | [I] **NPR/image stylisation**. [A] Optical fit, fibre BTDF, code and licence: **not found** in abstract. |
| [A] **朱意灏 / Yihao Zhu, 赵玉 / Yu Zhao, 张玲燕 / Lingyan Zhang, 刘肖健 / Xiaojian Liu**, *乱针绣风格化生成方法的计算机辅助DIY设计 / Computer Aided DIY Design of Stylized Generation of Random Needle Embroidery*, same journal 34(4), 645–658, 2022, DOI [10.3724/SP.J.1089.2022.18962](https://www.jcad.cn/article/doi/10.3724/SP.J.1089.2022.18962). Publisher abstract opened. | [A] Image segmentation, layered stitches, controllable vector fields, lighting preview and CorelDraw tool. | [I] **NPR/design preview**; a lighting preview is not evidence of measured physical fibre transport. [A] Code, data licence, optical parameters: **not found**. |
| [A] **姚智皓 / Zhihao Yao**, *再媒介化视角下的传统艺术数字创作工具设计研究 / A Design Study of Digital Creation Tools for Traditional Art from the Perspective of Remediation*, Tsinghua PhD, 2025; supervisor 米海鹏 / Haipeng Mi. [University thesis abstract](https://newetds.lib.tsinghua.edu.cn/qh/paper/summary?dbCode=ETDQH&sysId=304848) opened. | [A] Suzhou embroidery creation-tool case describes stitch innovation using **physical simulation** and work with heritage practitioners. | [I] Physical simulation of a design tool is supported at abstract level; a physically based **optical** silk model is not established. [A] Equations, measured scattering, code and licence: **not found**. |

[D] CNKI-targeted queries included `苏绣 渲染 site:cnki.net` and `乱针绣 图像 site:cnki.net`. A relevant, directly readable CNKI rendering abstract was **not found** within this search. [I] The accessible Chinese publisher and Tsinghua records above provide positive evidence; the CNKI retrieval failure is not evidence that no such thesis exists.

### Western-published / English-language leads with access limitations

[D] The following sources were attempted but **not successfully read**; they are recorded for follow-up, not used to justify optical capabilities or a production recommendation:

- [D] **Kewei Yang & Zhengxing Sun, Paint with stitches: a style definition and image-based rendering method for random-needle embroidery**, Multimedia Tools and Applications 77 (2018), 12259–12292, DOI [10.1007/s11042-017-4882-8](https://doi.org/10.1007/s11042-017-4882-8). Metadata located; primary full text unavailable in this run. [I] Title suggests stylisation, but a full-text physical/NPR audit remains uncompleted; code/licence: **not found**.
- [D] **Xinyang Guan et al., Automatic embroidery texture synthesis for garment design**, [White Rose university manuscript](https://eprints.whiterose.ac.uk/id/eprint/177275/1/Embroidery_styletransfer.pdf). Open timed out; complete citation, physical/NPR classification, code and licence: **not found** in verified readable material.

[I] **Reuse boundary:** the verified embroidery papers can inform stitch layout, layering and artist controls. No opened source provided a measured silk embroidery BSDF, a double-sided sheer-silk transmission fit, or a verified licensed embroidery-rendering repository. Western/English full-text coverage is a remaining limitation of this report.

## 5. Measured data: RGL, fabric identity and transmission

### RGL–EPFL

[D] **Jonathan Dupuy & Wenzel Jakob, An Adaptive Parameterization for Efficient Material Acquisition and Rendering**, TOG / SIGGRAPH Asia 2018, is the method named by the opened [RGL database FAQ](https://rgl.epfl.ch/pages/lab/material-database). [D] Data licence: **CC0 unless otherwise noted**. Spectral coverage: **360–1000 nm, approximately 4 nm spacing**. The FAQ distinguishes processed/extrapolated data from raw acquisition logs; not every stored angular value is a direct measurement.

| Entry in [database](https://rgl.epfl.ch/materials) | Verified identity / use |
|---|---|
| [D] `aniso_sari_silk_2color` | Sari silk, differently coloured warp and weft, anisotropic. [I] Best directly relevant measured-reflectance candidate; not proof of satin weave, split floss or gauze. |
| [D] `acrylic_felt_white` and coloured `acrylic_felt_*` | Acrylic felt. [I] Fabric/fibre-material controls, not silk substitutes. |
| [D] `ilm_aniso_tarkin_tunic` | Film costume fabric sample. Exact fibre composition **not found**. |
| [D] `ilm_aniso_darth_vader_pants` | Neoprene costume sample. [I] Not silk. |
| [D] `satin_blue`, `satin_gold`, `satin_purple`, `satin_rosaline`, `satin_white`; `vch_silk_blue` | TeckWrap vinyl wrapping films. [I] **Reject as silk/satin-cloth evidence.** |

[D] The opened [`brdf-loader`](https://github.com/rgl-epfl/brdf-loader) provides separate spectral/RGB implementations, BSD-3-Clause. [D] pbrt's [measured-model chapter](https://pbr-book.org/4ed/Reflection_Models/Measured_BSDFs) explicitly implements **surface reflection only**. [I] Neither a `.bsdf` suffix nor the material name implies transmission. Select the appropriate spectral file only after checking the installed pbrt reader's format support; direct `_spec.bsdf` compatibility was **not verified** here.

### Sheer silk gauze / organza transmission

[I] **Result: a verified reusable angular spectral BTDF for silk gauze/organza, with downloadable data and licence, was not found.** A hemispherical transmittance spectrum alone would constrain total transmitted energy but not its directional highlight, the open-weave image or stitch occlusion.

| Attempted lead | What is established; what is missing |
|---|---|
| [A] **Xin Li, Lingda Shao, Lin Ming, Rong He, Xiaoke Jin, Chengyan Zhu & Wei Tian**, *Light transmission characteristics of interwoven decorative fabrics made of silk with hidden weft of different colors*, Advanced Textile Technology 32(5), 51–57 (2024), DOI [10.12477/xdfzjs.20240507](https://www.sciengine.com/doi/10.12477/xdfzjs.20240507). | [A] Search-indexed publisher abstract describes visible-range spectrophotometric transmission. Direct publisher open returned 403. Exact T(λ), angular data, downloadable dataset, data licence: **not found**. [I] Multilayer decorative silk is not interchangeable with sheer 绡/纱. |
| [D] *Investigation of direct welding of organza textile and PET mesh for designing free-form lighting*, Scientific Reports (2026), [publisher URL](https://www.nature.com/articles/s41598-026-39362-1). | [D] Located and attempted; publisher redirected to an inaccessible access page. Silk composition, reusable optical measurements and dataset licence: **not found in verified readable text**. [I] Do not treat a paper mentioning organza as a silk dataset without checking fibre composition. |

[I] **Minimum missing capture for shot 24:** actual substrate weave spacing and yarn width, front/back stitch coverage, calibrated front/back light-rotation images and at least total spectral transmission. Keep direct-gap transmission separate from fibre scattering. Fit one parameter set to both sides; do not import fibroin-film transparency as whole-fabric transparency.

## 6. White goat-hair brush: optics, diameter and taper

### What can be entered into pbrt now

[D] [pbrt 4e, Scattering from Hair](https://pbr-book.org/4ed/Reflection_Models/Scattering_from_Hair), §9.9, describes a rough dielectric cylinder with absorption and R/TT/TRT/higher orders. Its interior model omits explicit volume scattering, including a scattering medulla.

| Parameter | Native value / units | Evidence for white 羊毫 |
|---|---|---|
| η | 1.55, dimensionless [D] | [I] General default; goat-specific measured η(λ): **not found**. |
| σa(λ) | Diameter-normalized absorption in the [input documentation](https://pbrt.org/fileformat-v4) [D] | [I] `0` is the ideal unpigmented diagnostic, not measured keratin absorption. Goat spectral coefficients: **not found**. |
| βm / βn | 0.3 / 0.3; dimensionless controls in [0,1] [D] | [I] Goat-specific fitted longitudinal/azimuthal roughness: **not found**. |
| α | 2°, scale tilt [D] | [I] General default; goat measured scale angle: **not found**. |

[D] The interface defaults to **brown** hair when no colour/absorption controls are provided. [I] Explicitly set absorption for a white-fibre test; do not merely rely on the material's default. Treat physical coefficients in mm⁻¹ and native normalized hair coefficients as different quantities; verify conversion against the installed implementation before importing laboratory absorption. Wet/ink-loaded optics would require separate evidence and are outside the supplied white-fibre description.

### Goat-specific evidence and retrieval gaps

[D] **Analyzing the intrinsic connection between Chinese calligraphy creation and brush properties from a micro perspective**, Heritage Science / npj Heritage Science (2025), [publisher source](https://www.nature.com/articles/s40494-025-02005-1), was located and opened unsuccessfully due to an access redirect. Author list and DOI were **not recovered in successfully read text**. [D] Index excerpts identify goat-brush microscopy; numerical fibre diameter, taper profile, η, σa, roughness and tilt usable for this report: **not found**.

[D] **Shape Memory Investigation of α-Keratin Fibers as Multi-Coupled Stimuli of Responsive Smart Materials** (2019), [PMC record](https://pmc.ncbi.nlm.nih.gov/articles/PMC6432327/), was attempted but returned an access-check page. [D] Search excerpts mention selected goat guard-hair specimens; this was not a verified measurement of calligraphy-brush hair. A reliable diameter/taper value for the actual brush remains **not found**. [I] Do not silently transfer textile mohair, cashmere or a selected coarse guard-hair range into a 羊毫 tip.

[D] A Chinese patent lead, **CN108051613B**, *一种微米直径的锥形毛移动和转移纳米线的方法*, [record](https://patents.google.com/patent/CN108051613B/zh), was located; direct open failed. Its indexed claims group several hair types. [I] Patent-claim ranges are not a measured goat-hair diameter distribution or taper law; no such numbers are adopted here.

[I] **Practical gap for shot 36:** obtain a microscope width-versus-length profile from representative hairs in the actual brush, including the last tapering segment, plus a front/back light sweep. If clear-cylinder `hair` gives the wrong white body/halo, test a published fur/medulla model rather than compensating with arbitrary absorption or a diffuse paint layer. This search did not establish a commercially cleared goat-specific medulla implementation or fit.

## Delivery status and limits

[D] **Completed:** six-question reuse map; explicit shot stacks; opened Sadeghi full text and its silk table; verified reflection-only Mitsuba implementation; Aliaga access/licence restriction; opened modern reflection/transmission validation; verified public modern yarn-code lead; RGL entry identity and CC0 terms; Chinese journal/university classification; explicit missing-value register.

[D] **Partially blocked:** full Aliaga paper/table verification; original Zhao fitted geometry table; numeric Mitsuba 0.5 silk preset files; most repository activity dates; Western embroidery full texts; directly reusable sheer-silk transmission spectra/BTDF; measured white-goat optics and taper. These are marked **not found** or index-only above rather than replaced with plausible numbers. [I] The main reuse decision is therefore concrete but conditional: native curves/hair for an initial evaluation, documented aggregate transmission models for the quality-critical back-lit route, and no claim of a finished photographic match.
