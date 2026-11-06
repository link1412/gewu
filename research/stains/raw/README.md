# Raw data and provenance

[I] Spectrum and HTML files here are the UTF-8 payloads retrieved through the GitHub connector, not manually transcribed or digitised. No repository code was downloaded or executed. The transport is a third-party mirror of USGS-authored files; an independent checksum comparison with the USGS distribution was not possible.

[I] Pinned mirror: https://github.com/Skylar-TyZhang/EX-spec/tree/06598564cd6cb19cfd3663cb732f759c821bd83c

[I] Reflectance source paths in that revision: `ASCIIdata/ASCIIdata_splib07a/ChapterM_Minerals/<filename>` for all selected minerals, `ASCIIdata/ASCIIdata_splib07a/ChapterA_ArtificialMaterials/<filename>` for sienna. Wavelength files: `ASCIIdata/ASCIIdata_splib07a/<filename>`. Metadata: `HTMLmetadata/<filename>`.

[I] Intended official distribution: https://doi.org/10.5066/F7RR1WDJ ; ASCII catalog https://www.sciencebase.gov/catalog/item/586e8c88e4b0f5ce109fccae ; report https://doi.org/10.3133/ds1035 . These official hosts could not be opened successfully in this session; do not interpret the links as independently verified downloads.

[I] Each spectrum's first line identifies the USGS library, record, sample and instrument code. Each remaining line has **one** number. Pair line 2 with line 2 of the appropriate wavelength file, and so on. The wavelength unit is micrometres. AREF values are retained as fractions, without percent conversion, normalisation or clipping. `-1.23e34` is an invalid-data sentinel, not negative reflectance.

[I] `spectra_manifest.json` records columns, pairings, local SHA-256 checksums and processing. All 16 saved raw ASCII/HTML files were also checked against the pinned mirror Git blob SHA-1 and byte size, recorded in `mirror_file_checksums.json`; all match. This does not authenticate them against the official USGS archive. `../scripts/build_stain_spectra.py` is our own standard-library-only offline resampling script. No third-party code is required.

[I] `crackle_sources/*.json` are search-index extracts prepared by the background researcher, **not downloaded original PDFs**. Their measurements are provisional and tagged [D] in the report.
