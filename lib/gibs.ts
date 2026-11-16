export const GIBS_BASE_URL = "https://gibs.earthdata.nasa.gov/wmts/epsg3857/best";
export const GIBS_LAYERS = {
  blue_marble: {
    label: "Blue Marble reference",
    sensor: "NASA reference basemap",
    layer: "BlueMarble_ShadedRelief_Bathymetry",
    matrix: "GoogleMapsCompatible_Level8",
    extension: "jpeg",
    date: null,
  },
  modis_terra: {
    label: "Terra MODIS true color",
    sensor: "Terra / MODIS",
    layer: "MODIS_Terra_CorrectedReflectance_TrueColor",
    matrix: "GoogleMapsCompatible_Level9",
    extension: "jpeg",
    date: "2026-11-16",
  },
  modis_aqua: {
    label: "Aqua MODIS true color",
    sensor: "Aqua / MODIS",
    layer: "MODIS_Aqua_CorrectedReflectance_TrueColor",
    matrix: "GoogleMapsCompatible_Level9",
    extension: "jpeg",
    date: "2026-11-15",
  },
  viirs_snpp: {
    label: "Suomi NPP VIIRS true color",
    sensor: "Suomi NPP / VIIRS",
    layer: "VIIRS_SNPP_CorrectedReflectance_TrueColor",
    matrix: "GoogleMapsCompatible_Level9",
    extension: "jpeg",
    date: "2026-11-02",
  },
} as const;
export type GibsLayer = keyof typeof GIBS_LAYERS;
