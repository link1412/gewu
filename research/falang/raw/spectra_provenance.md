# Spectra provenance and missing-data schema

[I] `../enamel_spectra.csv` is a header-only schema, not a measured dataset. There are no wavelength or reflectance samples. This explicit absence prevents empty cells, invented flat reflectances or RGB-derived curves being mistaken for observations.

| Column | Accepted source of reflectance ordinates | Status |
|---|---|---|
| wavelength_nm | not found | [I] No data rows |
| opaque_red | not found | [I] No data rows |
| pink | not found | [I] No data rows |
| turquoise | not found | [I] No data rows |
| cobalt_blue | not found | [I] No data rows |
| yellow | not found | [I] No data rows |
| white | not found | [I] No data rows |
| green | not found | [I] No data rows |
| black | not found | [I] No data rows |

[I] Chemical composition measurements and absorption-band wavelengths are not entered in this reflectance CSV. No data were digitised, interpolated or extrapolated. No [D] numeric spectrum is claimed. A future digitised spectrum must retain its source figure, axes, geometry, normalisation, sampling, digitisation uncertainty and substitute status.
