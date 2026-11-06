# Optical data provenance

The three CSV files contain the 380–780 nm rows, at the original 10 nm spacing, transcribed from the CC0 refractiveindex.info database on 2026-11-01. No interpolation or digitization. The source files use wavelength in micrometres; these CSVs convert only that unit to nm. Convention is n + i k, k ≥ 0.

- Hematite ordinary ray: https://raw.githubusercontent.com/polyanskiy/refractiveindex.info-database/master/database/data/main/Fe2O3/nk/Querry-o.yml
- Hematite extraordinary ray: https://raw.githubusercontent.com/polyanskiy/refractiveindex.info-database/master/database/data/main/Fe2O3/nk/Querry-e.yml
- Magnetite: https://raw.githubusercontent.com/polyanskiy/refractiveindex.info-database/master/database/data/main/Fe3O4/nk/Querry.yml

The database attributes all to M. R. Querry, *Optical constants*, Contractor Report CRDC-CR-85034 (1985), https://apps.dtic.mil/sti/pdfs/ADA158623.pdf . The original report could not be retrieved during this session: original page/table numbers, specimen, measurement inversion and uncertainty remain unverified. These are bulk mineral reference constants, not measurements of Inaba Tenmoku, not epsilon-Fe2O3, and not iron-containing silicate glaze. Hematite is birefringent: o/e are alternatives for the two optical components, not duplicate measurements. Do not assign either directly to randomly oriented crystals without an orientation/effective-medium model.

Data licence: public domain, CC0 1.0, as declared in each source YAML. CSV values were checked against the visible web raw-data rows; a source downloader may later preserve the full YAML files independently.
