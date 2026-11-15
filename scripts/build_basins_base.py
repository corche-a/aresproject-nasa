import math
from concurrent.futures import ThreadPoolExecutor, as_completed
import numpy as np
import pandas as pd
import requests

cuencas = pd.read_csv("data/raw/cuencas.csv", encoding="utf-8-sig")
print(f"Procesando {len(cuencas)} cuencas con Copernicus DEM + NASA POWER...")

delta = 0.005
lats, lons = [], []
for _, r in cuencas.iterrows():
    lat, lon = float(r["Latitude"]), float(r["Longitude"])
    lats.extend([lat, lat + delta, lat - delta, lat, lat])
    lons.extend([lon, lon, lon, lon + delta, lon - delta])

dem_map = {}
try:
    elevs = []
    for i in range(0, len(lats), 100):
        resp = requests.get(
            "https://api.open-meteo.com/v1/elevation",
            params={
                "latitude": ",".join(f"{x:.5f}" for x in lats[i:i+100]),
                "longitude": ",".join(f"{x:.5f}" for x in lons[i:i+100]),
            },
            timeout=20,
        )
        resp.raise_for_status()
        elevs.extend(resp.json()["elevation"])

    for idx, r in cuencas.iterrows():
        base = idx * 5
        z0, zn, zs, ze, zw = elevs[base:base+5]
        lat_rad = math.radians(float(r["Latitude"]))
        dy = 2 * delta * 111320.0
        dx = 2 * delta * 111320.0 * max(math.cos(lat_rad), 0.1)
        dz_dy = (zn - zs) / dy
        dz_dx = (ze - zw) / dx
        slope_deg = math.degrees(math.atan(math.sqrt(dz_dx**2 + dz_dy**2)))
        dem_map[r["ID"]] = (round(float(z0), 1), round(float(slope_deg), 2))
    print("Topografia Copernicus DEM calculada.")
except Exception as e:
    print("Aviso DEM (usando respaldo):", e)
    for _, r in cuencas.iterrows():
        dem_map[r["ID"]] = (500.0, 2.5)

MONTH_KEYS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]

def fetch_power(row):
    bid = row["ID"]
    lat = float(row["Latitude"])
    lon = float(row["Longitude"])
    url = "https://power.larc.nasa.gov/api/temporal/climatology/point"
    params = {
        "parameters": "T2M_MAX,T2M_MIN,PRECTOTCORR,WS10M,RH2M,ALLSKY_SFC_SW_DWN",
        "community": "RE",
        "longitude": lon,
        "latitude": lat,
        "format": "JSON",
    }
    r = requests.get(url, params=params, timeout=25)
    r.raise_for_status()
    p = r.json()["properties"]["parameter"]
    elev_m, slope_deg = dem_map[bid]

    rows = []
    for m_idx, m_key in enumerate(MONTH_KEYS, start=1):
        vals = [
            float(p["T2M_MAX"].get(m_key, np.nan)),
            float(p["T2M_MIN"].get(m_key, np.nan)),
            float(p["PRECTOTCORR"].get(m_key, np.nan)),
            float(p["WS10M"].get(m_key, np.nan)),
            float(p["RH2M"].get(m_key, np.nan)),
            float(p["ALLSKY_SFC_SW_DWN"].get(m_key, np.nan)),
        ]
        tmax, tmin, precip_day, wind, rh, solar = [np.nan if v <= -900 else v for v in vals]
        precip_mm = precip_day * 30.44 if not np.isnan(precip_day) else np.nan
        diurnal = (tmax - tmin) if (not np.isnan(tmax) and not np.isnan(tmin)) else np.nan

        rows.append({
            "basin_id": bid,
            "basin_name": bid.split("_", 1)[1].replace("_", " "),
            "lat": lat,
            "lon": lon,
            "month": m_idx,
            "month_name": m_key,
            "elevation_m": elev_m,
            "slope_deg": slope_deg,
            "temp_max_c": round(tmax, 2) if not np.isnan(tmax) else np.nan,
            "temp_min_c": round(tmin, 2) if not np.isnan(tmin) else np.nan,
            "diurnal_temp_range_c": round(diurnal, 2) if not np.isnan(diurnal) else np.nan,
            "precip_mm": round(precip_mm, 2) if not np.isnan(precip_mm) else np.nan,
            "wind_ms": round(wind, 2) if not np.isnan(wind) else np.nan,
            "rh_pct": round(rh, 2) if not np.isnan(rh) else np.nan,
            "solar_kwh_m2_day": round(solar, 2) if not np.isnan(solar) else np.nan,
        })
    return rows

all_rows = []
with ThreadPoolExecutor(max_workers=8) as ex:
    futures = [ex.submit(fetch_power, row) for _, row in cuencas.iterrows()]
    for fut in as_completed(futures):
        all_rows.extend(fut.result())

df = pd.DataFrame(all_rows).sort_values(["basin_id", "month"]).reset_index(drop=True)
num_cols = ["temp_max_c", "temp_min_c", "diurnal_temp_range_c", "precip_mm", "wind_ms", "rh_pct", "solar_kwh_m2_day"]
for c in num_cols:
    df[c] = df[c].fillna(df[c].median())

df["aridity_index"] = (1.0 - (df["precip_mm"].clip(0, 120) / 120.0)).round(3)
wind_norm = (df["wind_ms"] / 10.0).clip(0, 1)
dry_norm = (1.0 - (df["rh_pct"] / 100.0)).clip(0, 1)
df["dust_activity_norm"] = (0.45 * wind_norm + 0.35 * df["aridity_index"] + 0.20 * dry_norm).round(3)

df.to_parquet("data/processed/basins_base.parquet", index=False)
df.to_csv("data/processed/basins_base.csv", index=False)
print(f"\nEXITO: {len(df)} filas guardadas en data/processed/basins_base.parquet")
print(df[["basin_id", "month_name", "elevation_m", "slope_deg", "diurnal_temp_range_c", "aridity_index", "dust_activity_norm"]].head(6))
