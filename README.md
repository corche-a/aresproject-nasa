# ARES: Planetary Analog Temporal Discovery Engine

Motor de descubrimiento temporal basado en datos abiertos de la NASA para identificar las mejores ventanas mensuales de campaña en 56 cuencas endorreicas terrestres como analogos de sitios clave en la Luna y Marte.

## Arquitectura y Fuentes de Datos
- **Climatologia Mensual (NASA POWER API):** Rango termico diurno, precipitacion, velocidad del viento, humedad relativa y radiacion solar (672 ventanas cuenca-mes).
- **Topografia (Copernicus DEM):** Elevacion y pendiente real en grados alrededor del nucleo lacustre.
- **Mineralogia Hiperespectral (ISS EMIT L2BMIN via AppEEARS):** Identificacion mineral y profundidad de banda espectral (`scripts/merge_appeears.py`).

## Inicio Rapido
1. Clonar el repositorio:

    git clone https://github.com/corche-a/aresproject-nasa.git
    cd aresproject-nasa

2. Abrir `frontend/index.html` directamente en cualquier navegador web para explorar el mapa interactivo y los perfiles estacionales.
3. Para integrar los resultados de **EMIT (AppEEARS)** una vez descargado el ZIP:
   - Colocar los archivos `.csv` en `data/raw/appeears/`
   - Ejecutar:

    python scripts/merge_appeears.py
    python scripts/build_engine.py
