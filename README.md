# ARES: Planetary Analog Temporal Discovery Engine

The Next.js application compares 56 Earth endorheic basins across 672 stored monthly
windows against Mars and Moon target signatures. Values come from the checked-in NASA
pipeline output; missing measurements are disclosed rather than fabricated.

## Run locally

```bash
npm ci
npm run dev
```

Open `http://localhost:3000`. Run `npm test` for the focused similarity tests and
`npm run build` for the production build. See [DEPLOY.md](DEPLOY.md) for Amplify SSR
deployment and [scripts/README_PIPELINE.md](scripts/README_PIPELINE.md) for offline EMIT
ingestion.

## Enable Ask ARES with Google AI Studio

1. Create or regenerate a Gemini API key in Google AI Studio.
2. Create `.env.local` in the project root and add:

   ```env
   GOOGLE_AI_API_KEY=your_key_here
   GOOGLE_AI_MODEL=gemini-3.8-flash
   ```

3. Restart `npm run dev`. The key is used only by the server route `/api/ask`.
4. In Amplify, add the same variables under the SSR environment variables and redeploy.

Never commit `.env.local` or expose the key with a `NEXT_PUBLIC_*` variable.

Motor de descubrimiento temporal basado en datos abiertos de la NASA para identificar las mejores ventanas mensuales de campaña en 56 cuencas endorreicas terrestres como analogos de sitios clave en la Luna y Marte.

## Arquitectura y Fuentes de Datos
- **Climatologia Mensual (NASA POWER API):** Rango termico diurno, precipitacion, velocidad del viento, humedad relativa y radiacion solar (672 ventanas cuenca-mes).
- **Topografia (Copernicus DEM):** Elevacion y pendiente real en grados alrededor del nucleo lacustre.
- **Mineralogia Hiperespectral (ISS EMIT L2BMIN via AppEEARS):** Identificacion mineral y profundidad de banda espectral (`scripts/merge_appeears.py`).

## Inicio Rapido
1. Clonar el repositorio:

    git clone https://github.com/corche-a/aresproject-nasa.git
    cd aresproject-nasa

2. Open `http://localhost:3000` after starting Next.js to explore the map and seasonal profiles.
3. To integrate **EMIT (AppEEARS)** results after downloading the ZIP:
   - Colocar los archivos `.csv` en `data/raw/appeears/`
   - Ejecutar:

    python scripts/build_engine.py
