"""
Automatizador Oficial de la API REST de NASA AppEEARS para el Grid de 5 km².
============================================================================
Documentacion API NASA AppEEARS: https://appeears.earthdatacloud.nasa.gov/api/

Funciones:
- Lee credenciales de NASA Earthdata Login desde variables de entorno o archivo .env
  (EARTHDATA_USERNAME y EARTHDATA_PASSWORD).
- Obtiene el token Bearer en POST /api/login.
- Envia lotes de hasta 1,000 coordenadas de 5 km² desde data/appeears_batches/ (POST /api/task).
- Guarda el estado en data/appeears_batches/appeears_state.json para reanudar sin duplicar tareas.
- Descarga automaticamente los archivos .csv completados en data/raw/appeears/.
"""

import argparse
import glob
import json
import os
import time
from urllib import request, error
import base64

API_BASE = "https://appeears.earthdatacloud.nasa.gov/api"
STATE_FILE = "data/appeears_batches/appeears_state.json"
OUTPUT_DIR = "data/raw/appeears"


def load_env_file(filepath=".env"):
    if not os.path.exists(filepath):
        return
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"submitted_batches": {}, "downloaded_files": []}


def save_state(state):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def appeears_login(username, password):
    creds = f"{username}:{password}".encode("utf-8")
    b64_creds = base64.b64encode(creds).decode("ascii")
    req = request.Request(
        f"{API_BASE}/login",
        method="POST",
        headers={
            "Authorization": f"Basic {b64_creds}",
            "Content-Length": "0",
        },
    )
    with request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        return data["token"]


def submit_batch(token, batch_file):
    with open(batch_file, "r", encoding="utf-8") as f:
        payload_bytes = f.read().encode("utf-8")
    req = request.Request(
        f"{API_BASE}/task",
        data=payload_bytes,
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
    )
    with request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def check_and_download_tasks(token, state):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    for batch_name, info in state["submitted_batches"].items():
        task_id = info.get("task_id")
        if not task_id or info.get("status") == "done":
            continue

        req = request.Request(
            f"{API_BASE}/task/{task_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        with request.urlopen(req, timeout=30) as resp:
            t_data = json.loads(resp.read().decode("utf-8"))

        status = t_data.get("status", "unknown")
        info["status"] = status
        print(f"  - Lote {batch_name} (task_id={task_id}): estado = {status}")

        if status == "done":
            b_req = request.Request(
                f"{API_BASE}/bundle/{task_id}",
                headers={"Authorization": f"Bearer {token}"},
            )
            with request.urlopen(b_req, timeout=30) as b_resp:
                bundle = json.loads(b_resp.read().decode("utf-8"))

            for f_obj in bundle.get("files", []):
                fname = f_obj.get("file_name", "")
                fid = f_obj.get("file_id", "")
                if fname.endswith(".csv"):
                    safe_name = f"{batch_name}_{os.path.basename(fname)}"
                    dest_path = os.path.join(OUTPUT_DIR, safe_name)
                    if dest_path not in state["downloaded_files"]:
                        dl_req = request.Request(
                            f"{API_BASE}/bundle/{task_id}/{fid}",
                            headers={"Authorization": f"Bearer {token}"},
                        )
                        with request.urlopen(dl_req, timeout=120) as dl_resp:
                            with open(dest_path, "wb") as out_f:
                                out_f.write(dl_resp.read())
                        state["downloaded_files"].append(dest_path)
                        print(f"    [DESCARGADO] {dest_path}")

        save_state(state)


def main():
    parser = argparse.ArgumentParser(description="Automatizador de lotes AppEEARS")
    parser.add_argument("--max-submit", type=int, default=1, help="Maximo de lotes de 1,000 puntos a enviar en esta corrida")
    parser.add_argument("--poll", action="store_true", help="Verificar estado y descargar CSVs de tareas ya enviadas")
    args = parser.parse_args()

    load_env_file()
    username = os.environ.get("EARTHDATA_USERNAME", "").strip()
    password = os.environ.get("EARTHDATA_PASSWORD", "").strip()

    batch_files = sorted(glob.glob("data/appeears_batches/appeears_task_batch_*.json"))
    print(f"Lotes JSON de 1,000 coordenadas listos en data/appeears_batches/: {len(batch_files)}")

    if not username or not password:
        print(
            "\n[INFO] Para enviar o descargar lotes automaticamente en los servidores de NASA AppEEARS,\n"
            "define tus credenciales de NASA Earthdata Login en un archivo .env en la raiz del proyecto:\n"
            "  EARTHDATA_USERNAME=tu_usuario\n"
            "  EARTHDATA_PASSWORD=tu_password\n"
            "O sube directamente cualquiera de los archivos de 'data/appeears_batches/' en:\n"
            "  https://appeears.earthdatacloud.nasa.gov/task/point"
        )
        return

    print(f"Autenticando en NASA AppEEARS como '{username}'...")
    try:
        token = appeears_login(username, password)
    except error.HTTPError as e:
        print(f"[ERROR] Fallo de autenticacion en NASA Earthdata (HTTP {e.code}). Verifica usuario/password.")
        return

    state = load_state()
    submitted_count = 0

    for b_path in batch_files:
        b_name = os.path.splitext(os.path.basename(b_path))[0]
        if b_name in state["submitted_batches"]:
            continue
        if submitted_count >= args.max_submit:
            break

        print(f"Enviando lote {b_name} (hasta 1,000 parcelas de 5 km²) a NASA AppEEARS...")
        res = submit_batch(token, b_path)
        task_id = res.get("task_id")
        state["submitted_batches"][b_name] = {
            "task_id": task_id,
            "submitted_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "status": "submitted",
        }
        save_state(state)
        print(f"  [OK] Tarea creada en NASA AppEEARS: task_id = {task_id}")
        submitted_count += 1

    if args.poll or state["submitted_batches"]:
        print("\nVerificando estado de tareas en NASA AppEEARS...")
        check_and_download_tasks(token, state)


if __name__ == "__main__":
    main()
