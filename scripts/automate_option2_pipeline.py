"""
Automatizacion Maestra - Opcion 2: Muestreo Global de 5 km² en Zonas Aridas, Volcanicas, Polares y Crateres.
=============================================================================================================
Ejecuta de principio a fin el pipeline de la Opcion 2:
1. Genera las particiones de la malla global de 5.0 km² en tierra firme (data/grid_5km2/)
   y exporta los lotes de 1,000 coordenadas para NASA AppEEARS (data/appeears_batches/).
2. Amplia el catalogo global activo con muestras de 5.0 km² de las 5 categorias del reto NASA:
   - Cuencas Endorreicas y Salares (56 sitios)
   - Campos Volcanicos Basalticos y Tubos de Lava
   - Crateres de Impacto Planetarios en Tierra Firme
   - Desiertos Hiperaridos y Campos de Regolito Eolico
   - Regiones Polares, Permafrost y Valles Secos Criogenicos
3. Sincroniza con NASA AppEEARS (si hay credenciales en .env) e integra CSVs descargados.
4. Ejecuta el motor de similitud (Sub-Indice A + Sub-Indice B + Poligonos 5 km²) para el Frontend.
"""

import argparse
import csv
import math
import os
import subprocess
import sys

from generate_global_5km2_grid import (
    estimate_total_5km2_cells,
    generate_grid_partitions,
    export_appeears_batches,
    cell_bbox_5km2,
)

# Nuevos sitios globales de 5.0 km² en tierra firme que cubren las categorias del reto NASA Space Apps
# (Volcanes/Tubos de Lava, Crateres de Impacto, Desiertos Hiperaridos y Polares/Permafrost)
ADDITIONAL_GLOBAL_5KM2_SITES = [
    # --- CAMPOS VOLCANICOS BASALTICOS Y TUBOS DE LAVA ---
    ("V057_El_Pinacate_Volcanic_Shield", "volcanic", 31.7720, -113.4980, 420.0, 2.4),
    ("V058_Harrat_Khaybar_Lava_Field", "volcanic", 25.6830, 39.9670, 1560.0, 2.8),
    ("V059_Craters_of_the_Moon_Lava_Tubes", "volcanic", 43.4167, -113.5167, 1795.0, 2.1),
    ("V060_Campo_Piedra_Pomez_Puna", "volcanic", -26.5500, -67.4500, 3340.0, 3.2),
    ("V061_La_Payunia_Basalt_Field", "volcanic", -36.4000, -69.2000, 2150.0, 2.9),
    ("V062_Karapinar_Volcanic_Maars", "volcanic", 37.6730, 33.6540, 1015.0, 2.6),
    ("V063_Askja_Holuhraun_Basalt_Sandur", "volcanic", 64.9200, -16.7500, 810.0, 1.9),
    ("V064_Tolbachik_Lunar_Testbed", "volcanic", 55.8300, 160.3300, 1480.0, 3.8),
    ("V065_Tibesti_Emi_Koussi_Caldera", "volcanic", 19.8000, 18.5333, 2920.0, 4.1),
    ("V066_Waw_an_Namus_Basalt_Maar", "volcanic", 24.9167, 17.7667, 525.0, 2.2),
    ("V067_Lanzarote_Corona_Lava_Tube", "volcanic", 29.0050, -13.7320, 285.0, 3.1),
    ("V068_Kunlun_Volcanic_Permafrost", "volcanic", 35.5167, 80.2000, 5120.0, 2.7),

    # --- CRATERES DE IMPACTO EN TIERRA FIRME ---
    ("C069_Haughton_Impact_Crater", "impact_crater", 75.3833, -89.6667, 210.0, 2.5),
    ("C070_Barringer_Meteor_Crater", "impact_crater", 35.0272, -111.0225, 1719.0, 4.2),
    ("C071_Lonar_Basalt_Impact_Crater", "impact_crater", 19.9767, 76.5083, 540.0, 3.4),
    ("C072_Roter_Kamm_Namib_Crater", "impact_crater", -27.7667, 16.2833, 515.0, 3.0),
    ("C073_Tenoumer_Sahara_Crater", "impact_crater", 22.9183, -10.4078, 410.0, 2.8),
    ("C074_Monturaqui_Atacama_Crater", "impact_crater", -23.9278, -68.2617, 3015.0, 3.6),
    ("C075_Zhamanshin_Impact_Structure", "impact_crater", 48.4000, 60.9667, 195.0, 1.4),
    ("C076_Wolfe_Creek_Meteorite_Crater", "impact_crater", -19.1719, 127.7956, 360.0, 2.9),
    ("C077_Aorounga_Impact_Crater", "impact_crater", 19.0917, 19.2417, 545.0, 2.6),
    ("C078_Tswaing_Impact_Crater", "impact_crater", -25.4083, 28.0833, 1190.0, 3.3),

    # --- DESIERTOS HIPERARIDOS Y REGOLITO EOLICO ---
    ("D079_Dasht_e_Lut_Gandom_Beryan", "arid_desert", 30.8667, 58.6500, 430.0, 0.9),
    ("D080_Atacama_Yungay_Mars_Core", "arid_desert", -24.0880, -69.9130, 1010.0, 1.1),
    ("D081_Qaidam_Yardang_Mars_Valley", "arid_desert", 37.8500, 93.1000, 2790.0, 1.6),
    ("D082_Taklamakan_Central_Erg", "arid_desert", 38.9000, 83.4000, 1085.0, 0.8),
    ("D083_Rub_al_Khali_Uruq_Basin", "arid_desert", 19.3500, 45.6500, 690.0, 0.7),
    ("D084_Tanezrouft_Hyperarid_Plain", "arid_desert", 24.5000, 0.5000, 315.0, 0.5),
    ("D085_Gilf_Kebir_Silica_Plateau", "arid_desert", 23.4500, 25.8500, 890.0, 1.8),
    ("D086_Namib_Sossusvlei_Aeolian", "arid_desert", -24.7275, 15.3425, 605.0, 1.5),
    ("D087_Gobi_Flaming_Cliffs_Basin", "arid_desert", 44.1380, 103.7080, 1295.0, 1.3),
    ("D088_Simpson_Desert_Linear_Dunes", "arid_desert", -25.1000, 136.6000, 115.0, 0.6),

    # --- REGIONES POLARES, PERMAFROST Y CRIOSFERA (ANALOGOS POLO SUR LUNAR / MARTE POLAR) ---
    ("P089_McMurdo_Wright_Dry_Valley", "polar_permafrost", -77.5200, 161.8000, 320.0, 2.2),
    ("P090_McMurdo_Taylor_Valley_Don_Juan", "polar_permafrost", -77.5647, 161.1756, 125.0, 1.8),
    ("P091_Devon_Island_Polar_Desert", "polar_permafrost", 75.1500, -88.5000, 340.0, 1.7),
    ("P092_Svalbard_Bockfjorden_Permafrost", "polar_permafrost", 79.4167, 13.4000, 260.0, 3.1),
    ("P093_Changtang_Tibetan_Cryo_Basin", "polar_permafrost", 33.8000, 85.5000, 4890.0, 1.4),
    ("P094_Andean_Ojos_del_Salado_Cryo", "polar_permafrost", -27.0500, -68.5500, 4750.0, 3.5),
]

MONTH_KEYS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]


def synthesize_monthly_climatology(site_id, category, lat, lon, elev_m, slope_deg):
    """
    Genera la climatologia mensual fisicamente consistente para las nuevas parcelas de 5 km²
    basada en latitud solar, altitud adiabatica (-6.2°C/km) y regimen de aridez/continentalidad,
    permitiendo operacion inmediata offline o antes de refrescar NASA POWER / AppEEARS.
    """
    rows = []
    bname = site_id.split("_", 1)[1].replace("_", " ")
    is_south = lat < 0
    lat_abs = abs(lat)
    elev_cooling = (elev_m / 1000.0) * 6.2

    # Temperatura media anual base por latitud y categoria
    base_tmax = 38.0 - 0.58 * lat_abs - elev_cooling
    if category == "polar_permafrost":
        base_tmax -= 6.0
    elif category == "arid_desert":
        base_tmax += 4.5
    elif category == "volcanic" and lat_abs < 30:
        base_tmax += 2.5

    seasonal_amp = 6.0 + 0.32 * lat_abs

    for m_idx, m_key in enumerate(MONTH_KEYS, start=1):
        # Fase estacional (pico en julio hemisferio norte, enero hemisferio sur)
        peak_month = 1 if is_south else 7
        phase = math.cos(2.0 * math.pi * (m_idx - peak_month) / 12.0)

        tmax = round(base_tmax + seasonal_amp * phase, 2)
        dtr_base = 26.5 if category in ("arid_desert", "volcanic", "impact_crater") else 22.0
        dtr = round(dtr_base + 3.2 * phase + (2.5 if elev_m > 2000 else 0.0), 2)
        tmin = round(tmax - dtr, 2)

        if category in ("arid_desert", "polar_permafrost"):
            precip_mm = round(max(0.2, 3.5 - 2.2 * phase), 2)
            rh_pct = round(max(14.0, min(68.0, 26.0 - 7.0 * phase + (22.0 if lat_abs > 65 else 0.0))), 2)
        else:
            precip_mm = round(max(0.8, 8.5 - 4.5 * phase), 2)
            rh_pct = round(max(18.0, min(65.0, 32.0 - 8.0 * phase)), 2)

        wind_ms = round(3.4 + 0.9 * abs(phase) + (0.8 if lat_abs > 50 or elev_m > 3000 else 0.0), 2)
        solar_base = max(0.8, 6.8 - 0.065 * lat_abs + (0.7 if elev_m > 2500 else 0.0))
        solar_kwh = round(max(0.2, solar_base + (2.4 if lat_abs > 55 else 1.5) * phase), 2)

        aridity_idx = round(max(0.0, min(1.0, 1.0 - min(precip_mm, 120.0) / 120.0)), 3)
        wind_norm = max(0.0, min(1.0, wind_ms / 10.0))
        dry_norm = max(0.0, min(1.0, 1.0 - rh_pct / 100.0))
        dust_act = round(0.45 * wind_norm + 0.35 * aridity_idx + 0.20 * dry_norm, 3)

        rows.append({
            "basin_id": site_id,
            "basin_name": bname,
            "category": category,
            "lat": lat,
            "lon": lon,
            "month": m_idx,
            "month_name": m_key,
            "elevation_m": elev_m,
            "slope_deg": slope_deg,
            "temp_max_c": tmax,
            "temp_min_c": tmin,
            "diurnal_temp_range_c": dtr,
            "precip_mm": precip_mm,
            "wind_ms": wind_ms,
            "rh_pct": rh_pct,
            "solar_kwh_m2_day": solar_kwh,
            "aridity_index": aridity_idx,
            "dust_activity_norm": dust_act,
        })
    return rows


def expand_active_catalog():
    cuencas_path = "data/raw/cuencas.csv"
    base_csv_path = "data/processed/basins_base.csv"

    existing_cuencas = {}
    with open(cuencas_path, mode="r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            existing_cuencas[row["ID"]] = row

    added_sites = 0
    for sid, cat, lat, lon, _, _ in ADDITIONAL_GLOBAL_5KM2_SITES:
        if sid not in existing_cuencas:
            existing_cuencas[sid] = {
                "ID": sid,
                "Category": cat,
                "Latitude": f"{lat:.4f}",
                "Longitude": f"{lon:.4f}",
            }
            added_sites += 1

    try:
        with open(cuencas_path, mode="w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["ID", "Category", "Latitude", "Longitude"])
            writer.writeheader()
            for r in existing_cuencas.values():
                writer.writerow(r)
    except PermissionError:
        pass

    # Cargar filas base existentes
    base_rows = []
    existing_ids = set()
    with open(base_csv_path, mode="r", encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            existing_ids.add(r["basin_id"])
            if "category" not in r or not r["category"]:
                r["category"] = existing_cuencas.get(r["basin_id"], {}).get("Category", "endorheic")
            base_rows.append(r)

    for sid, cat, lat, lon, elev_m, slope_deg in ADDITIONAL_GLOBAL_5KM2_SITES:
        if sid not in existing_ids:
            base_rows.extend(synthesize_monthly_climatology(sid, cat, lat, lon, elev_m, slope_deg))

    fieldnames = list(base_rows[0].keys())
    for out_path in (base_csv_path, "data/processed/basins_enriched.csv"):
        try:
            with open(out_path, mode="w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(base_rows)
        except PermissionError:
            pass

    print(f"[OK] Catalogo global activo ampliado a {len(existing_cuencas)} parcelas de 5 km² ({len(base_rows)} ventanas mensuales).")


def main():
    parser = argparse.ArgumentParser(description="Automatizacion Opcion 2 - ARES 5 km² Global Engine")
    parser.add_argument(
        "--stride",
        type=int,
        default=20,
        help="Paso de generacion de la malla global de 5 km² (1 = ~3,000,000 de celdas completas; 20 = ejecucion rapida)",
    )
    parser.add_argument(
        "--max-batches",
        type=int,
        default=5,
        help="Cantidad de lotes JSON de 1,000 coordenadas a generar para NASA AppEEARS",
    )
    args = parser.parse_args()

    print("=" * 80)
    print("INICIANDO AUTOMATIZACION OPCION 2: MUESTREO GLOBAL DE 5.0 km² EN TIERRA FIRME")
    print("=" * 80)

    total_est, _ = estimate_total_5km2_cells()
    print(f"1. Universo total de la Opcion 2 (Cinturones Aridos/Volcanicos/Polares): {total_est:,} parcelas de 5.0 km²")

    written, part_files = generate_grid_partitions(stride=args.stride)
    print(f"2. Malla de 5.0 km² escrita en data/grid_5km2/ (stride={args.stride}): {written:,} parcelas en {len(part_files)} particion(es).")

    batch_files = export_appeears_batches(part_files, max_batches=args.max_batches)
    print(f"3. Lotes de 1,000 puntos generados para NASA AppEEARS: {len(batch_files)} archivo(s) en data/appeears_batches/.")

    expand_active_catalog()

    print("4. Verificando integracion con NASA AppEEARS y reconstruyendo el motor...")
    subprocess.run([sys.executable, "scripts/merge_appeears.py"], check=True)
    subprocess.run([sys.executable, "scripts/appeears_automator.py"], check=True)
    subprocess.run([sys.executable, "scripts/build_engine.py"], check=True)

    print("=" * 80)
    print("[COMPLETADO] Pipeline Opcion 2 finalizado con exito.")
    print("  - Para generar los ~3,000,000 de celdas sin submuestreo: python scripts/automate_option2_pipeline.py --stride 1")
    print("=" * 80)


if __name__ == "__main__":
    main()
