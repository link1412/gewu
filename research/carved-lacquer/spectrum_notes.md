# Visible-spectrum research notes

The strongest newly identified match is a primary study of cured, unpigmented refined urushi with an explicitly stated **dry-film thickness**, rather than a liquid urushiol solution or a modified synthetic resin.

## S1 — thickness-calibrated transmission spectra of cured clear urushi

**Citation:** Hiroshi Oyabu (大藪 泰) and Toru Asami (阿佐見 徹), “Effects of Curing Condition on Transparency of Urushi Films” / 「漆膜の透明性におよぼす硬化条件の影響」, *Journal of the Japan Society of Colour Material* / 色材協会誌 **60**(2), 94–99 (1987). DOI: [10.4011/shikizai1937.60.94](https://doi.org/10.4011/shikizai1937.60.94). [Publisher landing page](https://www.jstage.jst.go.jp/article/shikizai1937/60/2/60_94/_article/-char/en), [free publisher PDF](https://www.jstage.jst.go.jp/article/shikizai1937/60/2/60_94/_pdf/-char/en).

The study uses **sugurome-urushi (スグロメ漆)**: raw lacquer subjected to nayashi/kurome and reduced to a few percent water; the introduction explicitly excludes added orpiment and oils. This is an appropriate unpigmented refined lacquer comparison, although the accessible text does not establish a Chinese source for the sap.

| Quantity / evidence | Value | Classification and location |
|---|---|---|
| Actual dry, detached film thickness for spectral transmission | **30 ± 3 µm** | Author-reported measured sample property, §2.2.3, p.95; not a wet applicator gap. |
| Thickness used for published spectral curves | **30 µm**, corrected using Lambert’s law | Author-reported normalization, §2.2.3 p.95 and §3.3 p.97. |
| Spectral acquisition | **380–780 nm, 5 nm intervals** | Author-reported measurement method; Shimadzu UV-350A, §2.2.3 p.95. |
| Film specimen size for transmission | **20 × 40 mm** | Author-reported experimental specimen dimension, §2.2.3 p.95. |
| Initial curing | **24 h**, **20 or 30 °C**; **60, 70, 80, 90 or 98% RH** | Author-reported controlled experimental conditions, §2.1.2 p.95. |
| Later exposure | Up to **90 days** at natural light from a north window | Author-reported protocol, abstract, §2.2.3 and §3.3. |
| Full visible T(λ) with curing humidity varied | **Figure 5**, p.97, initial curing at **30 °C** | Primary measured spectra, presented graphically; curve values have **not** been digitized in this run. |
| Full visible T(λ) with elapsed time varied | **Figure 6**, p.97, initial curing at **20 °C, 80% RH** | Primary measured spectra, presented graphically; curve values have **not** been digitized in this run. |
| Single-wavelength comparisons | **600 nm**, Figs **7–8**, pp.97–98 | Primary measured transmission plotted against humidity / drying time. |

Higher curing humidity lowered transparency; transmission rose during subsequent exposure, with differences still remaining at the final observation. Those trends are the authors’ interpretation of their measurements, not a numerical substitute for the curves.

**Use for material calibration (inference):** choose a stated curing/age condition before digitizing the figure. Treat `−ln(T)/0.030 mm` as an *apparent attenuation* until reflection and scattering contributions have been assessed; the paper does not directly give a measured spectral absorption coefficient. The curves describe a particular refined lacquer and curing history, not a universal absorption spectrum for all historical lacquer.

## Why the apparently close alternatives were not accepted as the main answer

- [Yang et al., “Prepolymerization of Lacquer Sap under Pure Oxygen Atmosphere and Its Effects on the Properties of Lacquer Film” (2015), DOI 10.1155/2015/517202](https://onlinelibrary.wiley.com/doi/10.1155/2015/517202): the UV–visible spectra monitor raw and prepolymerized **sap**, rather than a thickness-calibrated cured film. Do not turn these absorbance curves into a bulk film absorption coefficient.
- [“Biobased Polymer Coating Using Catechol Derivative Urushiol” (2016), DOI 10.1021/acs.langmuir.6b00484](https://pubs.acs.org/doi/10.1021/acs.langmuir.6b00484): the supporting information advertises UV–visible spectra of **materials in ethanol**, even though film thicknesses are characterized elsewhere. Those are distinct measurements.
- The previously known *Polymers* **17**, 1481 (2025) study states a transmission scan and gives a single-wavelength transparency result, but its **50 ± 1 µm is wet thickness**. This is not an independently established dry thickness. It is not repeated as the requested new full spectrum.

## File/download status

**No binary PDF or spectrum image was saved.** The free publisher PDF was identified and its indexed methods, text, and figure captions were read; the figures themselves were not obtained. No spectrum ordinates were invented or represented as read from the figure.

Saved:

- `spectrum_notes.md` — these notes.
- `sources/spectra/download_manifest.tsv` — exact source URLs and intended local filenames, with failure status; it is not a substitute for the missing PDF.


