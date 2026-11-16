# Missing fields

The current `public/data/analogs_data.json` contract does not contain:

- closed-basin and relief classification;
- EMIT scene counts or measured mineral identifiers (the mineral profile is a literature prior);
- a water time series for wet-to-dry validation;
- MODIS MCD19A2 aerosol observations;
- a measured validation status or rank-sensitivity value;
- radiation observations and Mars temperature comparison values.
- measured regolith granulometry or surface roughness;
- ice/permafrost, brine, lava-tube, and cave inventories;
- cloud-cover and aerosol optical-depth time series.

The similarity engine uses NASA POWER climate variables, stored Copernicus DEM slope/elevation,
and transparent coordinate-derived proxies for latitude, platform stability, and weather-window
screening. It does not treat those proxies as direct Moon or Mars measurements. The UI renders
unavailable fields as explanatory text rather than inventing values.
