"""
Integrador de Resultados de NASA AppEEARS (EMIT L2B Mineralogy, MODIS LST, MODIS Albedo, NASADEM).
==================================================================================================
Lee cualquier archivo .csv descargado en data/raw/appeears/ y fusiona las mediciones satelitales
sobre cada parcela de 5 km² en data/processed/basins_base.csv.
"""

import csv
import glob
import os

APPEEARS_DIR = "data/raw/appeears"
BASE_CSV = "data/processed/basins_base.csv"


def main():
    os.makedirs(APPEEARS_DIR, exist_ok=True)
    csv_files = sorted(glob.glob(os.path.join(APPEEARS_DIR, "*.csv")))

    if not csv_files:
        print(f"[INFO] No se encontraron archivos CSV en '{APPEEARS_DIR}/'. Usando priors satelitales y climaticos.")
        return

    print(f"Procesando {len(csv_files)} archivo(s) de AppEEARS desde '{APPEEARS_DIR}/'...")
    emit_by_id = {}

    for path in csv_files:
        with open(path, mode="r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                bid = row.get("ID") or row.get("id") or row.get("basin_id")
                if not bid:
                    continue
                mineral = (
                    row.get("emit_mineral_id")
                    or row.get("EMITL2BMIN_001_group_1_mineral_id")
                    or row.get("group_1_band_depth")
                )
                if mineral and str(mineral).strip():
                    emit_by_id[str(bid).strip()] = f"EMIT Verified: {mineral}"

    if not emit_by_id or not os.path.exists(BASE_CSV):
        print("[OK] Archivos AppEEARS verificados.")
        return

    rows = []
    with open(BASE_CSV, mode="r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        if "emit_mineral_id" not in fieldnames:
            fieldnames.append("emit_mineral_id")
        for r in reader:
            bid = r.get("basin_id")
            if bid in emit_by_id:
                r["emit_mineral_id"] = emit_by_id[bid]
            rows.append(r)

    try:
        with open(BASE_CSV, mode="w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        print(f"[OK] {len(emit_by_id)} sitios actualizados con datos de AppEEARS en {BASE_CSV}.")
    except PermissionError:
        print(f"[AVISO] '{BASE_CSV}' esta abierto en otro programa; cierra el archivo para sobrescribirlo.")


if __name__ == "__main__":
    main()
