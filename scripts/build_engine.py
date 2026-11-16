import json
import os
import numpy as np
import pandas as pd

master_path = "data/processed/basins_master.parquet"
base_path = "data/processed/basins_base.parquet"
df = pd.read_parquet(master_path if os.path.exists(master_path) else base_path)

df["aridity_norm"] = df["aridity_index"].clip(0, 1)
df["thermal_norm"] = (df["diurnal_temp_range_c"] / 28.0).clip(0, 1)
df["dust_norm"] = df["dust_activity_norm"].clip(0, 1)
df["slope_norm"] = (df["slope_deg"] / 15.0).clip(0, 1)

CARBONATE_BASINS = {"B002_Laguna_Alchichica", "B004_Cuatro_Cienegas", "B029_Lake_Natron", "B030_Lake_Magadi", "B037_Lake_Van", "B038_Lake_Salda"}
SULFATE_CHLORIDE_BASINS = {"B001_Laguna_Sayula", "B007_Great_Salt_Lake", "B008_Bonneville_Salt_Flats", "B011_Badwater_Basin", "B015_Salar_de_Uyuni", "B018_Salar_de_Atacama", "B034_Dead_Sea", "B049_Lake_Eyre"}
PHYLLOSILICATE_BASINS = {"B003_Lago_Cuitzeo", "B010_Owens_Lake", "B013_Mono_Lake", "B020_Mar_Chiquita", "B025_Lake_Chad", "B043_Lake_Balkhash"}

def infer_mineral_class(row):
    if "emit_mineral_id" in row and pd.notna(row["emit_mineral_id"]):
        return str(row["emit_mineral_id"])
    bid = row["basin_id"]
    if bid in CARBONATE_BASINS:
        return "Carbonates / Hydromagnesite (Lit. Prior)"
    if bid in SULFATE_CHLORIDE_BASINS:
        return "Sulfates / Halite-Gypsum (Lit. Prior)"
    if bid in PHYLLOSILICATE_BASINS:
        return "Phyllosilicates / Smectite Clays (Lit. Prior)"
    return "Mixed Evaporites / Siliciclastics (Lit. Prior)"

df["mineral_profile"] = df.apply(infer_mineral_class, axis=1)

TARGETS = [
    {
        "id": "jezero_mars",
        "name": "Jezero Crater (Mars 2020)",
        "body": "Mars",
        "description": "Antiguo paleolago y delta con carbonatos lacustres, arcillas esmectitas y abanicos fluviales.",
        "expected_mineral": "Carbonates",
        "ideal": {"aridity": 0.92, "thermal": 0.85, "dust": 0.65, "slope": 0.30, "mineral": 1.0},
        "weights": {"aridity": 0.25, "thermal": 0.25, "dust": 0.15, "slope": 0.15, "mineral": 0.20},
    },
    {
        "id": "gale_mars",
        "name": "Gale Crater / Aeolis Palus (Mars)",
        "body": "Mars",
        "description": "Cuenca cerrada con estratos de sulfatos, lutitas lacustres y alta actividad eolica.",
        "expected_mineral": "Sulfates",
        "ideal": {"aridity": 0.95, "thermal": 0.88, "dust": 0.80, "slope": 0.35, "mineral": 1.0},
        "weights": {"aridity": 0.25, "thermal": 0.20, "dust": 0.25, "slope": 0.10, "mineral": 0.20},
    },
    {
        "id": "meridiani_mars",
        "name": "Meridiani Planum (Mars)",
        "body": "Mars",
        "description": "Planicie evaporitica rica en sulfatos (jarosita/yeso) con pendiente casi nula.",
        "expected_mineral": "Sulfates",
        "ideal": {"aridity": 0.96, "thermal": 0.82, "dust": 0.70, "slope": 0.05, "mineral": 1.0},
        "weights": {"aridity": 0.30, "thermal": 0.20, "dust": 0.15, "slope": 0.15, "mineral": 0.20},
    },
    {
        "id": "eberswalde_mars",
        "name": "Eberswalde Paleolake (Mars)",
        "body": "Mars",
        "description": "Cuenca endorreica con depositos de filosilicatos y delta invertido bien preservado.",
        "expected_mineral": "Phyllosilicates",
        "ideal": {"aridity": 0.88, "thermal": 0.78, "dust": 0.55, "slope": 0.25, "mineral": 1.0},
        "weights": {"aridity": 0.25, "thermal": 0.20, "dust": 0.15, "slope": 0.15, "mineral": 0.25},
    },
    {
        "id": "lunar_south_pole",
        "name": "Shackleton Rim / Lunar Regolith (Moon)",
        "body": "Moon",
        "description": "Entorno hiperarido sin atmosfera con choque termico extremo y polvo abrasivo fino.",
        "expected_mineral": "Siliciclastics",
        "ideal": {"aridity": 1.00, "thermal": 1.00, "dust": 0.85, "slope": 0.45, "mineral": 0.8},
        "weights": {"aridity": 0.30, "thermal": 0.35, "dust": 0.20, "slope": 0.10, "mineral": 0.05},
    },
]

records = []
for _, r in df.iterrows():
    records.append({
        "basin_id": r["basin_id"],
        "basin_name": r["basin_name"],
        "lat": round(float(r["lat"]), 4),
        "lon": round(float(r["lon"]), 4),
        "month": int(r["month"]),
        "month_name": r["month_name"],
        "elevation_m": float(r["elevation_m"]),
        "slope_deg": float(r["slope_deg"]),
        "temp_max_c": float(r["temp_max_c"]),
        "temp_min_c": float(r["temp_min_c"]),
        "diurnal_temp_range_c": float(r["diurnal_temp_range_c"]),
        "precip_mm": float(r["precip_mm"]),
        "wind_ms": float(r["wind_ms"]),
        "rh_pct": float(r["rh_pct"]),
        "solar_kwh_m2_day": float(r["solar_kwh_m2_day"]),
        "aridity_norm": round(float(r["aridity_norm"]), 3),
        "thermal_norm": round(float(r["thermal_norm"]), 3),
        "dust_norm": round(float(r["dust_norm"]), 3),
        "slope_norm": round(float(r["slope_norm"]), 3),
        "mineral_profile": r["mineral_profile"],
    })

payload = {
    "metadata": {
        "basins_count": int(df["basin_id"].nunique()),
        "total_windows": len(records),
        "emit_integrated": bool("emit_mineral_id" in df.columns and df["emit_mineral_id"].notna().any()),
    },
    "targets": TARGETS,
    "records": records,
}

os.makedirs("public/data", exist_ok=True)
with open("public/data/analogs_data.json", "w", encoding="utf-8") as f:
    json.dump(payload, f, ensure_ascii=False)

print(f"Motor generado: {len(records)} ventanas evaluadas para {len(TARGETS)} sitios planetarios.")
