# Missing fields

The current `frontend/analogs_data.json` contract does not contain:

- closed-basin and relief classification;
- EMIT scene counts or measured mineral identifiers (the mineral profile is a literature prior);
- a water time series for wet-to-dry validation;
- MODIS MCD19A2 aerosol observations;
- a measured validation status or rank-sensitivity value;
- radiation observations and Mars temperature comparison values.

The UI renders these as `n/a`, `Proxy`, or explanatory text rather than inventing values.
