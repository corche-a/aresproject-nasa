import csv
import json
import math
import os

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

csv_path = "data/processed/basins_base.csv"
enriched_csv_path = "data/processed/basins_enriched.csv"
master_parquet = "data/processed/basins_master.parquet"
base_parquet = "data/processed/basins_base.parquet"

SIDE_KM = math.sqrt(5.0)  # 2.236068 km por lado => 5.0 km² exactos
DLAT_DEG = SIDE_KM / 111.320

# ==============================================================================
# 1. CATALOGOS GEOLOGICOS, MINERALOGICOS E ISRU (SUB-INDICE A.1 y A.3)
# ==============================================================================
CARBONATE_BASINS = {
    "B002_Laguna_Alchichica", "B004_Cuatro_Cienegas", "B029_Lake_Natron",
    "B030_Lake_Magadi", "B037_Lake_Van", "B038_Lake_Salda",
}
SULFATE_CHLORIDE_BASINS = {
    "B001_Laguna_Sayula", "B007_Great_Salt_Lake", "B008_Bonneville_Salt_Flats",
    "B011_Badwater_Basin", "B015_Salar_de_Uyuni", "B018_Salar_de_Atacama",
    "B034_Dead_Sea", "B049_Lake_Eyre", "B017_Salar_de_Coipasa",
    "B019_Salar_Hombre_Muerto", "B021_Salinas_Grandes", "B022_Chott_el_Djerid",
    "B046_Qaidam_Dabusun", "B053_Lake_Elton", "B054_Lake_Baskunchak",
    "D080_Atacama_Yungay_Mars_Core", "D081_Qaidam_Yardang_Mars_Valley",
    "P090_McMurdo_Taylor_Valley_Don_Juan",
}
PHYLLOSILICATE_BASINS = {
    "B003_Lago_Cuitzeo", "B010_Owens_Lake", "B013_Mono_Lake",
    "B020_Mar_Chiquita", "B025_Lake_Chad", "B043_Lake_Balkhash",
    "B026_Bodele_Depression", "B041_Hamun_Lake", "D087_Gobi_Flaming_Cliffs_Basin",
}
BASALT_OLIVINE_BASINS = {
    "B002_Laguna_Alchichica", "B003_Lago_Cuitzeo", "B012_Playa_Black_Rock",
    "B013_Mono_Lake", "B029_Lake_Natron", "B030_Lake_Magadi",
    "B031_Lake_Turkana", "B032_Lake_Assal", "B033_Danakil_Depression",
    "B037_Lake_Van", "B038_Lake_Salda",
    "C071_Lonar_Basalt_Impact_Crater", "C074_Monturaqui_Atacama_Crater",
    "D079_Dasht_e_Lut_Gandom_Beryan", "P089_McMurdo_Wright_Dry_Valley",
    "P092_Svalbard_Bockfjorden_Permafrost", "P094_Andean_Ojos_del_Salado_Cryo",
}
LAVA_TUBES_OR_CAVES_BASINS = {
    "B002_Laguna_Alchichica", "B004_Cuatro_Cienegas", "B012_Playa_Black_Rock",
    "B013_Mono_Lake", "B029_Lake_Natron", "B031_Lake_Turkana",
    "B032_Lake_Assal", "B033_Danakil_Depression", "B037_Lake_Van",
}
FINE_SILT_DUST_BASINS = {
    "B003_Lago_Cuitzeo", "B010_Owens_Lake", "B012_Playa_Black_Rock",
    "B014_Carson_Sink", "B025_Lake_Chad", "B026_Bodele_Depression",
    "B027_Etosha_Pan", "B028_Makgadikgadi_Pan", "B041_Hamun_Lake",
    "B042_South_Aral_Sea", "B044_Lop_Nur",
}


def clamp(val, low=0.0, high=1.0):
    return max(low, min(high, val))


def compute_bbox_5km2(lat, lon):
    half_lat = DLAT_DEG / 2.0
    cos_lat = max(math.cos(math.radians(lat)), 0.15)
    half_lon = (DLAT_DEG / cos_lat) / 2.0
    return [
        round(lon - half_lon, 5),
        round(lat - half_lat, 5),
        round(lon + half_lon, 5),
        round(lat + half_lat, 5),
    ]


def infer_category(bid, raw_cat=None):
    if raw_cat and str(raw_cat).strip():
        return str(raw_cat).strip()
    if bid.startswith("V"):
        return "volcanic"
    if bid.startswith("C"):
        return "impact_crater"
    if bid.startswith("D"):
        return "arid_desert"
    if bid.startswith("P"):
        return "polar_permafrost"
    return "endorheic"


def is_basalt_olivine(bid, cat):
    return bid in BASALT_OLIVINE_BASINS or cat == "volcanic"


def has_lava_tubes_or_caves(bid, cat):
    return bid in LAVA_TUBES_OR_CAVES_BASINS or cat in ("volcanic", "impact_crater")


def infer_mineral_class(bid, cat, emit_val=None):
    if emit_val and str(emit_val).strip() and str(emit_val).lower() != "nan":
        return str(emit_val)
    has_basalt = is_basalt_olivine(bid, cat)
    suffix = " + Basalt/Olivine" if has_basalt else " (Lit. Prior)"
    if bid in CARBONATE_BASINS:
        return f"Carbonates / Hydromagnesite{suffix}"
    if bid in SULFATE_CHLORIDE_BASINS:
        return f"Sulfates / Halite-Gypsum{suffix}"
    if bid in PHYLLOSILICATE_BASINS:
        return f"Phyllosilicates / Smectite Clays{suffix}"
    if cat == "impact_crater":
        return "Impact Breccia / Shocked Basalt & Silicates" if has_basalt else "Impact Breccia / Shocked Siliciclastics"
    if cat == "polar_permafrost":
        return "Cryogenic Regolith / Permafrost & Basalt" if has_basalt else "Cryogenic Regolith / Ice-Cemented Silicates"
    if has_basalt:
        return "Basalt / Olivine & Pyroclastic Regolith"
    return "Mixed Evaporites / Siliciclastics (Lit. Prior)"


def infer_granulometry(bid, cat):
    if is_basalt_olivine(bid, cat):
        return 85.0, "Regolito Basaltico-Olivino Angular (60-120 µm)", 0.92
    if cat == "impact_crater":
        return 95.0, "Brecha de Impacto y Regolito Angular (50-140 µm)", 0.90
    if bid in FINE_SILT_DUST_BASINS or cat == "arid_desert":
        return 18.0, "Limo-Arena Eolica Fina / Polvo Marciano (10-45 µm)", 0.94
    if bid in SULFATE_CHLORIDE_BASINS:
        return 110.0, "Arena Evaporitica Cristalina (80-150 µm)", 0.80
    return 65.0, "Limo-Arena Siliciclastica Mixta (40-90 µm)", 0.78


# Cargar registros desde el archivo mas actualizado disponible
source_csv = enriched_csv_path if os.path.exists(enriched_csv_path) else csv_path
with open(source_csv, mode="r", encoding="utf-8-sig", newline="") as f:
    raw_rows = list(csv.DictReader(f))

# Si enriched_csv_path tenia menos filas que csv_path, usar csv_path
if os.path.exists(csv_path):
    with open(csv_path, mode="r", encoding="utf-8-sig", newline="") as f:
        alt_rows = list(csv.DictReader(f))
    if len(alt_rows) > len(raw_rows):
        raw_rows = alt_rows

records = []
emit_integrated = False
unique_basins = set()

for r in raw_rows:
    bid = str(r["basin_id"])
    unique_basins.add(bid)
    bname = str(r["basin_name"])
    cat = infer_category(bid, r.get("category"))
    lat = round(float(r["lat"]), 4)
    lon = round(float(r["lon"]), 4)
    bbox_5km2 = compute_bbox_5km2(lat, lon)
    month = int(float(r["month"]))
    month_name = str(r["month_name"])

    elevation_m = round(float(r["elevation_m"]), 1)
    slope_deg = round(float(r["slope_deg"]), 2)
    temp_max_c = round(float(r["temp_max_c"]), 2)
    temp_min_c = round(float(r["temp_min_c"]), 2)
    diurnal_temp_range_c = round(float(r["diurnal_temp_range_c"]), 2)
    precip_mm = round(float(r["precip_mm"]), 2)
    wind_ms = round(float(r["wind_ms"]), 2)
    rh_pct = round(float(r["rh_pct"]), 2)
    solar_kwh_m2_day = round(float(r["solar_kwh_m2_day"]), 2)
    aridity_index = round(float(r.get("aridity_index", clamp(1.0 - min(precip_mm, 120.0) / 120.0))), 3)
    dust_activity_norm = round(float(r.get("dust_activity_norm", 0.5)), 3)

    # 1. SUB-INDICE A.1: Morfologia y Regolito en la muestra de 5 km²
    has_basalt = is_basalt_olivine(bid, cat)
    if "roughness_m" in r and r["roughness_m"] not in ("", None):
        roughness_m = round(float(r["roughness_m"]), 2)
    else:
        roughness_m = round(slope_deg * 1.85 + (1.40 if has_basalt else 0.35), 2)

    slope_norm = round(clamp(slope_deg / 15.0), 3)
    roughness_norm = round(clamp(roughness_m / 8.0), 3)
    basalt_olivine_norm = 0.95 if has_basalt else 0.45
    grain_size_um, granulometry_class, regolith_norm = infer_granulometry(bid, cat)

    # Albedo superficial MODIS (WSA shortwave: basaltos oscuros ~0.10-0.16, salares brillantes ~0.35-0.55)
    albedo_wsa = round(0.12 if has_basalt else (0.42 if bid in SULFATE_CHLORIDE_BASINS else 0.26), 2)

    emit_val = r.get("emit_mineral_id")
    if emit_val and str(emit_val).strip() and str(emit_val).lower() != "nan":
        emit_integrated = True
    mineral_profile = infer_mineral_class(bid, cat, emit_val)

    # 2. SUB-INDICE A.2: Extremos Ambientales
    aridity_norm = round(clamp(aridity_index), 3)
    thermal_norm = round(clamp(diurnal_temp_range_c / 28.0), 3)
    dust_norm = round(clamp(dust_activity_norm), 3)

    # 3. SUB-INDICE A.3: Recursos y Subsuelo (ISRU y Refugios)
    if temp_min_c <= -5.0 or cat == "polar_permafrost":
        cryo_norm = 0.95
    elif temp_min_c <= 2.0:
        cryo_norm = 0.75
    elif elevation_m >= 3000.0:
        cryo_norm = 0.65
    else:
        cryo_norm = 0.20

    brine_norm = 0.95 if bid in SULFATE_CHLORIDE_BASINS else (0.80 if bid in CARBONATE_BASINS else 0.55)
    caves_norm = 0.95 if has_lava_tubes_or_caves(bid, cat) else (0.65 if has_basalt else 0.25)
    isru_norm = round(0.35 * cryo_norm + 0.40 * brine_norm + 0.25 * caves_norm, 3)

    isru_tags = []
    if brine_norm >= 0.80:
        isru_tags.append("Salmueras/Sales Hidratadas")
    if cryo_norm >= 0.75:
        isru_tags.append("Hielo/Permafrost")
    if caves_norm >= 0.85:
        isru_tags.append("Tubos de Lava/Refugio Craterico")
    isru_resources = " + ".join(isru_tags) if isru_tags else "Regolito Seco ISRU"

    # 4. SUB-INDICE B.1: Geometria Orbital (Latitud, Elevacion y Exposicion Solar)
    lat_abs_rad = math.radians(abs(lat))
    orbital_eq_norm = round(clamp(math.cos(lat_abs_rad)), 3)
    orbital_polar_norm = round(clamp(0.45 + 0.55 * clamp(abs(lat) / 55.0)), 3)
    elevation_norm = round(clamp(0.35 + 0.65 * (clamp(elevation_m, -100.0, 4000.0) + 100.0) / 4100.0), 3)
    solar_norm = round(clamp(solar_kwh_m2_day / 8.0), 3)
    orbital_geometry_norm = round(0.45 * orbital_eq_norm + 0.30 * elevation_norm + 0.25 * solar_norm, 3)

    # 5. SUB-INDICE B.2: Estabilidad Geotecnica de Plataforma (< 5° pendiente, firmeza, baja abrasion)
    if slope_deg <= 5.0:
        flat_terrain_norm = round(clamp(1.0 - 0.08 * slope_deg), 3)
    else:
        flat_terrain_norm = round(clamp(0.60 - 0.06 * (slope_deg - 5.0)), 3)

    dry_surface_norm = clamp(1.0 - min(precip_mm, 80.0) / 80.0)
    low_rh_norm = clamp(1.0 - rh_pct / 100.0)
    crust_bonus = 0.12 if (bid in SULFATE_CHLORIDE_BASINS or has_basalt) else 0.04
    substrate_firmness_norm = round(clamp(0.60 * dry_surface_norm + 0.28 * low_rh_norm + crust_bonus), 3)
    low_abrasion_norm = round(clamp(1.0 - 0.75 * dust_norm, 0.15, 1.0), 3)
    geotech_stability_norm = round(
        0.45 * flat_terrain_norm + 0.35 * substrate_firmness_norm + 0.20 * low_abrasion_norm, 3
    )

    # 6. SUB-INDICE B.3: Ventana Meteorologica (Viento/rafagas, estabilidad, baja nubosidad y opacidad)
    if "wind_gust_ms" in r and r["wind_gust_ms"] not in ("", None):
        wind_gust_ms = round(float(r["wind_gust_ms"]), 2)
    else:
        wind_gust_ms = round(wind_ms * (1.45 + 0.008 * max(diurnal_temp_range_c, 0.0)), 2)

    if "cloud_cover_pct" in r and r["cloud_cover_pct"] not in ("", None):
        cloud_cover_pct = round(float(r["cloud_cover_pct"]), 1)
    else:
        cloud_cover_pct = round(
            clamp(0.62 * rh_pct + (14.0 if precip_mm > 30.0 else 0.0) - 2.2 * solar_kwh_m2_day, 2.0, 95.0), 1
        )

    wind_safety_norm = round(clamp(1.0 - max(0.0, wind_gust_ms - 2.5) / 10.0, 0.10, 1.0), 3)
    atm_stability_norm = round(clamp(0.55 * (1.0 - min(precip_mm, 100.0) / 100.0) + 0.45 * wind_safety_norm), 3)
    clear_sky_norm = round(clamp(1.0 - cloud_cover_pct / 100.0), 3)
    low_dust_opacity_norm = round(clamp(1.0 - 0.70 * dust_norm, 0.20, 1.0), 3)
    weather_window_norm = round(
        0.35 * wind_safety_norm
        + 0.25 * atm_stability_norm
        + 0.25 * clear_sky_norm
        + 0.15 * low_dust_opacity_norm,
        3,
    )

    records.append({
        "basin_id": bid,
        "basin_name": bname,
        "category": cat,
        "lat": lat,
        "lon": lon,
        "bbox_5km2": bbox_5km2,
        "area_km2": 5.0,
        "month": month,
        "month_name": month_name,
        "elevation_m": elevation_m,
        "slope_deg": slope_deg,
        "roughness_m": roughness_m,
        "albedo_wsa": albedo_wsa,
        "grain_size_um": grain_size_um,
        "granulometry_class": granulometry_class,
        "regolith_norm": regolith_norm,
        "basalt_olivine_norm": basalt_olivine_norm,
        "mineral_profile": mineral_profile,
        "temp_max_c": temp_max_c,
        "temp_min_c": temp_min_c,
        "diurnal_temp_range_c": diurnal_temp_range_c,
        "precip_mm": precip_mm,
        "wind_ms": wind_ms,
        "wind_gust_ms": wind_gust_ms,
        "rh_pct": rh_pct,
        "cloud_cover_pct": cloud_cover_pct,
        "solar_kwh_m2_day": solar_kwh_m2_day,
        "aridity_index": aridity_index,
        "dust_activity_norm": dust_activity_norm,
        "aridity_norm": aridity_norm,
        "thermal_norm": thermal_norm,
        "dust_norm": dust_norm,
        "slope_norm": slope_norm,
        "roughness_norm": roughness_norm,
        "cryo_norm": cryo_norm,
        "brine_norm": brine_norm,
        "caves_norm": caves_norm,
        "isru_norm": isru_norm,
        "isru_resources": isru_resources,
        "orbital_eq_norm": orbital_eq_norm,
        "orbital_polar_norm": orbital_polar_norm,
        "elevation_norm": elevation_norm,
        "solar_norm": solar_norm,
        "orbital_geometry_norm": orbital_geometry_norm,
        "flat_terrain_norm": flat_terrain_norm,
        "substrate_firmness_norm": substrate_firmness_norm,
        "low_abrasion_norm": low_abrasion_norm,
        "geotech_stability_norm": geotech_stability_norm,
        "wind_safety_norm": wind_safety_norm,
        "atm_stability_norm": atm_stability_norm,
        "clear_sky_norm": clear_sky_norm,
        "low_dust_opacity_norm": low_dust_opacity_norm,
        "weather_window_norm": weather_window_norm,
    })

# Guardar CSV actualizado (sin la lista bbox_5km2 serializada como objeto complejo, sino texto JSON)
if records:
    csv_records = []
    for rec in records:
        r_copy = dict(rec)
        r_copy["bbox_5km2"] = json.dumps(rec["bbox_5km2"])
        csv_records.append(r_copy)
    fieldnames = list(csv_records[0].keys())
    for out_csv in (csv_path, enriched_csv_path):
        try:
            with open(out_csv, mode="w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(csv_records)
        except PermissionError:
            pass
    if HAS_PANDAS:
        try:
            pd.DataFrame(csv_records).to_parquet(base_parquet, index=False)
        except Exception:
            pass

TARGETS = [
    {
        "id": "jezero_mars",
        "name": "Jezero Crater (Mars 2020)",
        "body": "Mars",
        "description": "Antiguo paleolago y delta con carbonatos marginales, olivino/basalto y arcillas esmectitas.",
        "expected_mineral": "Carbonates",
        "earth_limits": "Gravedad marciana (0.38 g), presion atmosferica de 6 mbar CO2 (vs 1013 mbar terrestre) y radiacion UV/cosmica no atenuada.",
        "recommended_tests": "Perforacion de testigos (rovers), espectrometria Raman/LIBS en carbonatos-olivino y navegacion autonoma en bordes de crater.",
        "ideal": {
            "aridity": 0.92, "thermal": 0.85, "dust": 0.65, "slope": 0.30,
            "roughness": 0.35, "mineral": 1.0, "isru": 0.85,
        },
        "weights": {
            "aridity": 0.20, "thermal": 0.20, "dust": 0.15, "slope": 0.15,
            "mineral": 0.18, "isru": 0.12,
            "orbital": 0.30, "geotech": 0.35, "weather": 0.35,
            "subindex_a_share": 0.65,
        },
    },
    {
        "id": "gale_mars",
        "name": "Gale Crater / Aeolis Palus (Mars)",
        "body": "Mars",
        "description": "Cuenca cerrada con estratos de sulfatos, lutitas lacustres, basaltos eolicos y alta dinamica de polvo.",
        "expected_mineral": "Sulfates",
        "earth_limits": "Tormentas de polvo a baja densidad atmosferica (0.020 kg/m³) y ciclos de percloratos anhidros bajo radiacion ionizante.",
        "recommended_tests": "Movilidad sobre dunas basalticas y costras de sulfatos, sellado contra polvo abrasivo y sensores meteorologicos marcianos.",
        "ideal": {
            "aridity": 0.95, "thermal": 0.88, "dust": 0.80, "slope": 0.35,
            "roughness": 0.40, "mineral": 1.0, "isru": 0.85,
        },
        "weights": {
            "aridity": 0.22, "thermal": 0.18, "dust": 0.20, "slope": 0.10,
            "mineral": 0.18, "isru": 0.12,
            "orbital": 0.30, "geotech": 0.35, "weather": 0.35,
            "subindex_a_share": 0.65,
        },
    },
    {
        "id": "meridiani_mars",
        "name": "Meridiani Planum (Mars)",
        "body": "Mars",
        "description": "Planicie evaporitica rica en sulfatos (jarosita/yeso) y arena basaltica con pendiente casi nula (< 2°).",
        "expected_mineral": "Sulfates",
        "earth_limits": "Ausencia de campo magnetico global y conveccion termica distinta en la capa limite planetaria de Marte.",
        "recommended_tests": "Sistemas de aterrizaje de precision (EDL/Pinpoint Landing), plataformas de despegue vertical y extraccion ISRU de agua en yeso/sulfatos.",
        "ideal": {
            "aridity": 0.96, "thermal": 0.82, "dust": 0.70, "slope": 0.05,
            "roughness": 0.10, "mineral": 1.0, "isru": 0.88,
        },
        "weights": {
            "aridity": 0.24, "thermal": 0.18, "dust": 0.14, "slope": 0.14,
            "mineral": 0.18, "isru": 0.12,
            "orbital": 0.30, "geotech": 0.40, "weather": 0.30,
            "subindex_a_share": 0.60,
        },
    },
    {
        "id": "eberswalde_mars",
        "name": "Eberswalde Paleolake (Mars)",
        "body": "Mars",
        "description": "Cuenca endorreica con depositos de filosilicatos (esmectitas), delta invertido y potencial ISRU.",
        "expected_mineral": "Phyllosilicates",
        "earth_limits": "En la Tierra las arcillas contienen materia organica moderna y humedad residual superior a la corteza desecada marciana.",
        "recommended_tests": "Deteccion de biofirmas preservadas en arcillas esmectitas y perforacion estratigrafica en paleodeltas.",
        "ideal": {
            "aridity": 0.88, "thermal": 0.78, "dust": 0.55, "slope": 0.25,
            "roughness": 0.30, "mineral": 1.0, "isru": 0.80,
        },
        "weights": {
            "aridity": 0.22, "thermal": 0.18, "dust": 0.13, "slope": 0.14,
            "mineral": 0.21, "isru": 0.12,
            "orbital": 0.30, "geotech": 0.35, "weather": 0.35,
            "subindex_a_share": 0.65,
        },
    },
    {
        "id": "lunar_south_pole",
        "name": "Shackleton Rim / Lunar South Pole (Moon)",
        "body": "Moon",
        "description": "Entorno hiperarido con regolito basaltico/anortositico, iluminacion solar rasante (LRO Diviner), hielo polar y tubos de lava.",
        "expected_mineral": "Basalt",
        "earth_limits": "Gravedad lunar (0.16 g), alto vacio (sin atmosfera), polvo cargado electrostaticamente y temperaturas de ~40 K en trampas frias.",
        "recommended_tests": "Operaciones EVA con iluminacion rasante, prospeccion de hielo/permafrost (ISRU), habitats en tubos de lava y mitigacion de polvo abrasivo.",
        "ideal": {
            "aridity": 1.00, "thermal": 1.00, "dust": 0.85, "slope": 0.45,
            "roughness": 0.50, "mineral": 0.95, "isru": 0.95,
        },
        "weights": {
            "aridity": 0.24, "thermal": 0.28, "dust": 0.16, "slope": 0.10,
            "mineral": 0.10, "isru": 0.12,
            "orbital": 0.35, "geotech": 0.35, "weather": 0.30,
            "subindex_a_share": 0.60,
        },
    },
]

payload = {
    "metadata": {
        "basins_count": len(unique_basins),
        "total_windows": len(records),
        "sample_area_km2": 5.0,
        "emit_integrated": emit_integrated,
        "subindices_enabled": True,
    },
    "targets": TARGETS,
    "records": records,
}

os.makedirs("frontend", exist_ok=True)
with open("frontend/analogs_data.json", "w", encoding="utf-8") as f:
    json.dump(payload, f, ensure_ascii=False)

with open("frontend/analogs_data.js", "w", encoding="utf-8") as f:
    f.write("window.ARES_DATA = " + json.dumps(payload, ensure_ascii=False) + ";\n")

print(f"Motor ARES v2 generado: {len(unique_basins)} parcelas de 5.0 km² ({len(records)} ventanas mensuales) para {len(TARGETS)} sitios planetarios.")
