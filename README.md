# ARES: Planetary Analog & Launch Operations Discovery Engine (5 km² Global Sampling)

Motor de descubrimiento espacial y temporal basado en datos abiertos de la NASA (Earthdata, AppEEARS, NASA POWER, GIBS, LRO Diviner y PDS) y ESA Copernicus DEM para identificar las mejores parcelas terrestres de **5.0 km² ($2.24 \times 2.24\text{ km}$)** y ventanas mensuales de campaña como análogos de sitios clave en la Luna y Marte.

## Arquitectura de Índices y Fuentes de Datos
- **Sub-Índice A (Similitud Planetaria):**
  1. **Morfología y Regolito:** Pendiente DEM, rugosidad superficial (TRI), afinidad mineralógica (Carbonatos, Sulfatos, Filosilicatos, **Basalto/Olivino** vía ISS EMIT L2BMIN) y granulometría del polvo.
  2. **Extremos Ambientales:** Amplitud térmica diurna ($\Delta T$), aridez, albedo MODIS y dinámica eólica/polvo.
  3. **Recursos y Subsuelo (ISRU):** Hielo/permafrost, salmueras hidratadas y tubos de lava / refugios cratéricos.
- **Sub-Índice B (Viabilidad de Operaciones de Base y Despegue):**
  1. **Geometría Orbital:** Latitud (impulso rotacional ecuatorial o iluminación rasante polar lunar), altitud s.n.m. y radiación solar.
  2. **Estabilidad Geotécnica de Plataforma:** Terreno plano ($< 5^\circ$), firmeza del sustrato en seco y baja dispersión abrasiva.
  3. **Ventana Meteorológica:** Velocidad media y ráfagas de viento, estabilidad atmosférica, baja nubosidad y baja opacidad por polvo.

## Automatización de Malla Global de 5 km² (Opción 2: Cinturones Áridos, Volcánicos, Polares y Cráteres)

Ejecutar el pipeline maestro automatizado:

```bash
python scripts/automate_option2_pipeline.py
```

Opciones avanzadas:
- Para generar el 100% de la malla continua de ~2.28 millones de parcelas de $5.0\text{ km}^2$ en particiones en disco (`data/grid_5km2/`):
  ```bash
  python scripts/automate_option2_pipeline.py --stride 1
  ```
- Para enviar y descargar lotes de 1,000 coordenadas automáticamente desde la API REST de **NASA AppEEARS**, copia `.env.example` a `.env` con tus credenciales de NASA Earthdata Login y ejecuta:
  ```bash
  python scripts/appeears_automator.py --max-submit 5 --poll
  python scripts/merge_appeears.py
  python scripts/build_engine.py
  ```
