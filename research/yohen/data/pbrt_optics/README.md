# PBRT candidate mineral spectra

Each .spd is a two-column wavelength[nm]/value text file converted directly from the adjacent Querry CSV. eta means n; k is dimensionless. No interpolation or extrapolation was performed in these files. Coverage is only 380–780nm; outside that range no validated constants are supplied. PBRT may interpolate or extend spectra internally; do not interpret that as measured data.

These files describe bulk alpha-Fe2O3 ordinary/extraordinary components and Fe3O4, not epsilon-Fe2O3 and not Inaba glaze. They are candidate inputs to a physically appropriate interface/scattering model, not a ready-made Yohen material. Anisotropic hematite cannot be represented exactly by an isotropic scalar material.

Source, licence (CC0), original-report limitation and CSVs: [provenance](../optical_data_README.md). PBRT spectrum-file syntax: https://pbrt.org/fileformat-v4 . No PBRT scene was rendered or validated in this research task.
