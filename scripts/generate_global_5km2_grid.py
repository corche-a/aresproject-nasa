"""
Generador de Malla Global de 5 km² (Opcion 2: Zonas Aridas, Volcanicas, Polares y Crateres en Tierra Firme).
============================================================================================================
Calcula celdas estrictamente de 5.0 km² (2.2361 km x 2.2361 km) con correccion esferica de latitud:
    dlat_deg = 2.236068 / 111.320  (~0.020087 grados)
    dlon_deg = 2.236068 / (111.320 * cos(radians(lat)))

Incluye:
1. Cinturones aridos, hiperaridos, volcanicos, periglaciares/polares y cuencas endorreicas en TIERRA FIRME
   (~15,000,000 km² = ~3,000,000 de parcelas de 5 km²).
2. Generacion por particiones/lotes (streaming en disco) para no saturar la memoria RAM.
3. Exportacion automatica de lotes de 1,000 coordenadas listos para NASA AppEEARS.
4. Catalogo global estratificado inmediato (todos los continentes y las 5 categorias del reto NASA).
"""

import argparse
import csv
import json
import math
import os

SIDE_KM = math.sqrt(5.0)  # 2.2360679775 km por lado => 5.0 km² exactos
DLAT_DEG = SIDE_KM / 111.320  # ~0.02008685 grados de latitud

# Poligonos rectangulares estrictamente interiores en TIERRA FIRME (sin mar/oceano)
# que cubren el ~10% de la superficie emergida: desiertos, escudos volcanicos, zonas polares y cuencas.
TERRESTRIAL_ANALOG_BELTS = [
    # --- NORTEAMERICA ---
    {"region_id": "NA_GREAT_BASIN_MOJAVE", "name": "Great Basin, Mojave & Black Rock", "category": "arid_desert", "min_lat": 34.5, "max_lat": 41.5, "min_lon": -119.2, "max_lon": -112.5},
    {"region_id": "NA_SONORAN_PINACATE", "name": "Desierto de Sonora y Escudo Volcanico El Pinacate", "category": "volcanic", "min_lat": 31.8, "max_lat": 33.8, "min_lon": -114.2, "max_lon": -111.5},
    {"region_id": "NA_CHIHUAHUAN_BOLSON", "name": "Desierto Chihuahuense, Mapimi y Cuatro Cienegas", "category": "endorheic", "min_lat": 25.5, "max_lat": 31.5, "min_lon": -106.5, "max_lon": -101.5},
    {"region_id": "NA_SNAKE_RIVER_LAVA", "name": "Craters of the Moon & Snake River Basalt Plain", "category": "volcanic", "min_lat": 42.8, "max_lat": 44.2, "min_lon": -114.5, "max_lon": -112.2},
    {"region_id": "NA_COLORADO_PLATEAU", "name": "Meseta del Colorado y Meteor Crater", "category": "impact_crater", "min_lat": 35.0, "max_lat": 38.8, "min_lon": -111.8, "max_lon": -108.5},
    {"region_id": "NA_DEVON_ISLAND_ARCTIC", "name": "Isla Devon y Crater Haughton (Artico Canadiense)", "category": "polar_permafrost", "min_lat": 74.7, "max_lat": 75.6, "min_lon": -91.5, "max_lon": -86.5},

    # --- SUDAMERICA ---
    {"region_id": "SA_ATACAMA_CORE", "name": "Nucleo Hiperarido de Atacama y Monturaqui", "category": "arid_desert", "min_lat": -25.8, "max_lat": -21.5, "min_lon": -69.6, "max_lon": -68.0},
    {"region_id": "SA_ALTIPLANO_PUNA", "name": "Altiplano Andino, Uyuni y Puna Volcanica", "category": "endorheic", "min_lat": -26.8, "max_lat": -18.2, "min_lon": -68.2, "max_lon": -65.5},
    {"region_id": "SA_PAYUNIA_VOLCANIC", "name": "Campo Volcanico La Payunia y Auca Mahuida", "category": "volcanic", "min_lat": -37.5, "max_lat": -35.2, "min_lon": -69.5, "max_lon": -68.2},
    {"region_id": "SA_PATAGONIA_STEPPE", "name": "Meseta Basaltica y Periglacial Patagonica", "category": "polar_permafrost", "min_lat": -50.2, "max_lat": -46.5, "min_lon": -71.2, "max_lon": -68.5},

    # --- AFRICA ---
    {"region_id": "AF_SAHARA_WEST_TANEZROUFT", "name": "Sahara Occidental, Tanezrouft y Crater Tenoumer", "category": "arid_desert", "min_lat": 20.0, "max_lat": 28.5, "min_lon": -11.0, "max_lon": 3.0},
    {"region_id": "AF_SAHARA_TIBESTI_ENNEDI", "name": "Macizo Volcanico del Tibesti, Hoggar y Ennedi", "category": "volcanic", "min_lat": 18.0, "max_lat": 25.5, "min_lon": 5.0, "max_lon": 22.5},
    {"region_id": "AF_SAHARA_EAST_UWEINAT", "name": "Gran Mar de Arena, Gilf Kebir y Jebel Uweinat", "category": "arid_desert", "min_lat": 20.0, "max_lat": 27.5, "min_lon": 23.0, "max_lon": 30.8},
    {"region_id": "AF_BODELE_CHAD", "name": "Depresion de Bodele y Cuenca del Mega-Chad", "category": "endorheic", "min_lat": 13.5, "max_lat": 18.0, "min_lon": 14.0, "max_lon": 20.0},
    {"region_id": "AF_AFAR_DANAKIL", "name": "Triangulo de Afar, Danakil y Escudo Erta Ale", "category": "volcanic", "min_lat": 11.2, "max_lat": 14.5, "min_lon": 40.0, "max_lon": 42.2},
    {"region_id": "AF_EAST_RIFT_VALLEY", "name": "Rift Oriental: Turkana, Natron y Magadi", "category": "volcanic", "min_lat": -3.2, "max_lat": 4.2, "min_lon": 35.5, "max_lon": 37.5},
    {"region_id": "AF_NAMIB_KALAHARI", "name": "Desierto del Namib Interior, Roter Kamm y Etosha", "category": "impact_crater", "min_lat": -27.8, "max_lat": -18.5, "min_lon": 15.6, "max_lon": 26.0},

    # --- MEDIO ORIENTE Y ANATOLIA ---
    {"region_id": "ME_HARRAT_KHAYBAR", "name": "Campos de Lava Harrat Khaybar y Rahat (Escudo Arabe)", "category": "volcanic", "min_lat": 22.5, "max_lat": 27.0, "min_lon": 39.2, "max_lon": 42.5},
    {"region_id": "ME_RUB_AL_KHALI", "name": "Desierto Hiperarido Rub al Khali y Wabar", "category": "arid_desert", "min_lat": 18.0, "max_lat": 23.0, "min_lon": 46.0, "max_lon": 55.0},
    {"region_id": "ME_ANATOLIA_KARAPINAR", "name": "Anatolia Central: Karapinar, Salda y Tuz", "category": "volcanic", "min_lat": 37.2, "max_lat": 39.2, "min_lon": 29.5, "max_lon": 34.5},
    {"region_id": "ME_LUT_KAVIR_IRAN", "name": "Dasht-e Lut (Polo de Calor Terrestre) y Dasht-e Kavir", "category": "arid_desert", "min_lat": 29.5, "max_lat": 35.8, "min_lon": 53.0, "max_lon": 60.5},

    # --- ASIA CENTRAL Y ORIENTAL ---
    {"region_id": "AS_KYZYLKUM_ZHAMANSHIN", "name": "Kyzylkum, Karakum, Aral Sur y Crater Zhamanshin", "category": "impact_crater", "min_lat": 39.0, "max_lat": 48.8, "min_lon": 58.0, "max_lon": 66.0},
    {"region_id": "AS_TAKLAMAKAN_LOP_NUR", "name": "Cuenca del Tarim, Desierto de Taklamakan y Lop Nur", "category": "arid_desert", "min_lat": 37.5, "max_lat": 41.5, "min_lon": 78.0, "max_lon": 92.0},
    {"region_id": "AS_QAIDAM_MARS_VALLEY", "name": "Cuenca de Qaidam (Yardangs Marcianos y Evaporitas)", "category": "endorheic", "min_lat": 36.2, "max_lat": 39.0, "min_lon": 90.5, "max_lon": 97.5},
    {"region_id": "AS_TIBET_PERMAFROST", "name": "Meseta de Changtang-Tibet y Campo Volcanico Kunlun", "category": "polar_permafrost", "min_lat": 32.0, "max_lat": 36.0, "min_lon": 80.0, "max_lon": 92.0},
    {"region_id": "AS_GOBI_DESERT", "name": "Desierto del Gobi y Cuenca de Nemegt", "category": "arid_desert", "min_lat": 41.5, "max_lat": 45.5, "min_lon": 96.0, "max_lon": 108.0},
    {"region_id": "AS_DECCAN_LONAR", "name": "Traps Basalticos del Decan y Crater de Impacto Lonar", "category": "impact_crater", "min_lat": 19.2, "max_lat": 21.0, "min_lon": 75.5, "max_lon": 77.5},
    {"region_id": "AS_KAMCHATKA_TOLBACHIK", "name": "Macizo Volcanico Tolbachik (Sitio de Pruebas Lunokhod)", "category": "volcanic", "min_lat": 55.4, "max_lat": 56.2, "min_lon": 159.8, "max_lon": 160.8},

    # --- OCEANIA ---
    {"region_id": "OC_AUSTRALIA_RED_CENTER", "name": "Desiertos de Simpson, Tirari, Lake Eyre y Crater Henbury", "category": "arid_desert", "min_lat": -31.2, "max_lat": -23.5, "min_lon": 128.0, "max_lon": 140.5},

    # --- POLAR Y SUBPOLAR ---
    {"region_id": "PO_MCMURDO_DRY_VALLEYS", "name": "Valles Secos de McMurdo (Wright, Taylor y Victoria Valley)", "category": "polar_permafrost", "min_lat": -78.0, "max_lat": -77.1, "min_lon": 160.5, "max_lon": 163.5},
    {"region_id": "PO_ICELAND_ASKJA_SANDUR", "name": "Tierras Altas de Islandia: Askja, Holuhraun y Odadahraun", "category": "volcanic", "min_lat": 64.5, "max_lat": 65.3, "min_lon": -17.5, "max_lon": -16.0},
    {"region_id": "PO_SVALBARD_BOCKFJORD", "name": "Svalbard: Complejo Volcanico-Permafrost de Bockfjorden", "category": "polar_permafrost", "min_lat": 78.2, "max_lat": 79.5, "min_lon": 13.5, "max_lon": 17.5},
]


def cell_bbox_5km2(lat, lon):
    """Devuelve el bounding box exacto de 5.0 km² (2.236 km x 2.236 km) centrado en (lat, lon)."""
    half_lat = DLAT_DEG / 2.0
    cos_lat = max(math.cos(math.radians(lat)), 0.15)
    half_lon = (DLAT_DEG / cos_lat) / 2.0
    return [
        round(lon - half_lon, 5),
        round(lat - half_lat, 5),
        round(lon + half_lon, 5),
        round(lat + half_lat, 5),
    ]


def estimate_total_5km2_cells():
    """Calcula cuantas parcelas de 5.0 km² caben exactamente en los cinturones terrestres definidos."""
    total = 0
    breakdown = []
    for belt in TERRESTRIAL_ANALOG_BELTS:
        n_lat = int(round((belt["max_lat"] - belt["min_lat"]) / DLAT_DEG))
        mid_lat = 0.5 * (belt["min_lat"] + belt["max_lat"])
        dlon = DLAT_DEG / max(math.cos(math.radians(mid_lat)), 0.15)
        n_lon = int(round((belt["max_lon"] - belt["min_lon"]) / dlon))
        cells = n_lat * n_lon
        total += cells
        breakdown.append((belt["region_id"], belt["name"], belt["category"], cells, round(cells * 5.0)))
    return total, breakdown


def generate_grid_partitions(output_dir="data/grid_5km2", stride=1, max_cells_per_file=50000, max_total_cells=None):
    """
    Genera en streaming las celdas de 5 km² sobre tierra firme sin saturar la RAM.
    - Con stride=1: genera el 100% de la malla continua de 5 km² (~3,000,000 de celdas).
    - Con stride>1: genera un submuestreo sistematico uniforme sobre los mismos cinturones.
    """
    os.makedirs(output_dir, exist_ok=True)
    part_idx = 1
    rows_in_part = 0
    total_written = 0
    f_out = None
    writer = None

    def open_next_part(p_idx):
        path = os.path.join(output_dir, f"grid_5km2_part_{p_idx:04d}.csv")
        fh = open(path, mode="w", encoding="utf-8", newline="")
        w = csv.writer(fh)
        w.writerow(["cell_id", "region_id", "category", "lat", "lon", "min_lon", "min_lat", "max_lon", "max_lat", "area_km2"])
        return fh, w, path

    f_out, writer, current_path = open_next_part(part_idx)
    generated_files = [current_path]

    try:
        for belt in TERRESTRIAL_ANALOG_BELTS:
            lat = belt["min_lat"] + (DLAT_DEG * 0.5)
            lat_step = DLAT_DEG * stride
            while lat <= belt["max_lat"]:
                cos_lat = max(math.cos(math.radians(lat)), 0.15)
                dlon = DLAT_DEG / cos_lat
                lon_step = dlon * stride
                lon = belt["min_lon"] + (dlon * 0.5)
                while lon <= belt["max_lon"]:
                    total_written += 1
                    bbox = cell_bbox_5km2(lat, lon)
                    cell_id = f"C5K_{total_written:07d}"
                    writer.writerow([
                        cell_id,
                        belt["region_id"],
                        belt["category"],
                        round(lat, 5),
                        round(lon, 5),
                        bbox[0], bbox[1], bbox[2], bbox[3],
                        5.0,
                    ])
                    rows_in_part += 1

                    if max_total_cells and total_written >= max_total_cells:
                        return total_written, generated_files

                    if rows_in_part >= max_cells_per_file:
                        f_out.close()
                        part_idx += 1
                        rows_in_part = 0
                        f_out, writer, current_path = open_next_part(part_idx)
                        generated_files.append(current_path)

                    lon += lon_step
                lat += lat_step
    finally:
        if f_out and not f_out.closed:
            f_out.close()

    return total_written, generated_files


def export_appeears_batches(grid_csv_files, batch_dir="data/appeears_batches", batch_size=1000, max_batches=10):
    """
    Lee las particiones del grid de 5 km² y genera archivos JSON de solicitud por lotes de 1,000 puntos
    compatibles con la API REST oficial de NASA AppEEARS (POST https://appeears.earthdatacloud.nasa.gov/api/task).
    """
    os.makedirs(batch_dir, exist_ok=True)
    coords_buffer = []
    batch_files = []
    batch_num = 1

    def flush_batch(coords, b_num):
        task_payload = {
            "task_type": "point",
            "task_name": f"ARES_Global_5km2_Batch_{b_num:04d}",
            "params": {
                "dates": [{"startDate": "01-01-2023", "endDate": "12-31-2024"}],
                "layers": [
                    {"product": "EMITL2BMIN.001", "layer": "group_1_band_depth"},
                    {"product": "MOD11A2.061", "layer": "LST_Day_1km"},
                    {"product": "MOD11A2.061", "layer": "LST_Night_1km"},
                    {"product": "MCD43A3.061", "layer": "Albedo_WSA_shortwave"},
                    {"product": "NASADEM_NC.001", "layer": "NASADEM_HGT"},
                ],
                "coordinates": coords,
            },
        }
        out_path = os.path.join(batch_dir, f"appeears_task_batch_{b_num:04d}.json")
        with open(out_path, "w", encoding="utf-8") as fh:
            json.dump(task_payload, fh, indent=2)
        return out_path

    for csv_file in grid_csv_files:
        with open(csv_file, "r", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                coords_buffer.append({
                    "id": row["cell_id"],
                    "category": row["category"],
                    "latitude": float(row["lat"]),
                    "longitude": float(row["lon"]),
                })
                if len(coords_buffer) >= batch_size:
                    batch_files.append(flush_batch(coords_buffer, batch_num))
                    coords_buffer = []
                    batch_num += 1
                    if max_batches and batch_num > max_batches:
                        return batch_files

    if coords_buffer and (not max_batches or batch_num <= max_batches):
        batch_files.append(flush_batch(coords_buffer, batch_num))

    return batch_files


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generador de Malla Global de 5 km² (Opcion 2)")
    parser.add_argument("--stride", type=int, default=25, help="Paso de muestreo de celdas (1 = ~3M celdas completas; 25 = malla rapida)")
    parser.add_argument("--max-cells", type=int, default=0, help="Limite opcional de celdas a escribir (0 = sin limite para el stride dado)")
    parser.add_argument("--max-batches", type=int, default=5, help="Numero de lotes JSON de 1,000 puntos a exportar para AppEEARS")
    args = parser.parse_args()

    total_est, breakdown = estimate_total_5km2_cells()
    print("=" * 78)
    print(f"CAPACIDAD TOTAL DE LA MALLA DE 5.0 km² (STRIDE=1): {total_est:,} parcelas (~{total_est*5:,} km²)")
    print("=" * 78)
    for rid, rname, rcat, c_count, area_km2 in breakdown[:8]:
        print(f"  - {rid:<26} | {rcat:<16} | {c_count:>9,} celdas de 5 km² ({area_km2:>10,} km²)")
    print(f"  ... (+ {len(breakdown) - 8} cinturones continentales adicionales)")

    max_c = args.max_cells if args.max_cells > 0 else None
    written, files = generate_grid_partitions(stride=args.stride, max_total_cells=max_c)
    print(f"\n[OK] Celdas de 5 km² generadas en disco (stride={args.stride}): {written:,} parcelas en {len(files)} archivo(s).")

    batches = export_appeears_batches(files, max_batches=args.max_batches)
    print(f"[OK] Lotes AppEEARS (1,000 coords/tarea) exportados en data/appeears_batches/: {len(batches)} archivo(s).")
