# Documentación de Cambios, Arquitectura e Ideas Añadidas — ARES v2 (5 km² Global Engine)

Este documento registra todas las mejoras arquitectónicas, modelos matemáticos, fuentes de datos espaciales, scripts de automatización y funcionalidades de interfaz añadidas en esta rama para responder integralmente al reto de **NASA Space Apps Challenge: *"Identify Earth Locations that Analog the Permanent Moon Base Locations and Mars"***.

---

## 1. Visión y Concepto Central Añadido

### Unidad Estándar de Muestreo Planetario: Parcelas de $5.0\text{ km}^2$ ($2.24\text{ km} \times 2.24\text{ km}$)
- **Problema original:** Los estudios tradicionales evalúan regiones enormes (todo el Desierto de Atacama, toda la Antártida) como un único punto o por simple parecido visual, ignorando la escala real de aterrizaje y operación de un rover o base.
- **Solución implementada:** Se definió una unidad estándar de muestreo de **$5.0\text{ km}^2$ de terreno sólido** ($\approx 2.236\text{ km} \times 2.236\text{ km}$), equivalente a una zona real de alunizaje/amartizaje y campo de pruebas de hardware.
- **Corrección Esférica de Latitud:**
  $$\Delta\text{lat} = \frac{\sqrt{5.0}}{111.320} \approx 0.020087^\circ, \qquad \Delta\text{lon}(\phi) = \frac{\Delta\text{lat}}{\max(\cos\phi, 0.15)}$$
  Esto garantiza que cada parcela tenga exactamente $5.0\text{ km}^2$ sin importar si está en el ecuador o cerca de los polos.

---

## 2. Modelo Matemático de Doble Índice (Sub-Índice A + Sub-Índice B)

El motor pasó de evaluar únicamente 5 variables generales a un **sistema dual de 49 atributos por ventana mensual**:

### SUB-ÍNDICE A: Similitud Planetaria (Fidelidad del Análogo)
Evalúa qué tan fielmente reproduce la parcela de $5\text{ km}^2$ las condiciones geológicas, ambientales y de recursos de la Luna o Marte:

1. **Morfología y Regolito (`A.1`):**
   - **Pendiente topográfica (`slope_deg`, `slope_norm`):** Derivada de Copernicus DEM.
   - **Rugosidad superficial (`roughness_m`, `roughness_norm`):** Índice de Rugosidad del Terreno (TRI) en metros a partir de la desviación estándar altimétrica.
   - **Composición mineralógica y Basalto/Olivino (`mineral_profile`, `basalt_olivine_norm`):** Integra carbonatos, sulfatos/evaporitas, filosilicatos (esmectitas) y **basalto/olivino** (fundamental para regolito lunar, cráteres marcianos como Jezero y escudos volcánicos), preparado para fusión directa con **ISS EMIT L2BMIN**.
   - **Granulometría del polvo (`grain_size_um`, `granulometry_class`, `regolith_norm`):** Tamaño medio de partícula en micrómetros ($\mu\text{m}$) y textura mecánica del suelo (limo ultrafino marciano, regolito basáltico angular, arena evaporítica o brecha de impacto).
   - **Albedo Superficial (`albedo_wsa`):** Reflectancia de onda corta (MODIS `MCD43A3`).

2. **Extremos Ambientales (`A.2`):**
   - **Amplitud térmica diurna (`diurnal_temp_range_c`, `thermal_norm`):** Choque térmico diario ($\Delta T = T_{\max} - T_{\min}$).
   - **Aridez (`aridity_norm`):** Basada en precipitación mensual (`PRECTOTCORR`) y humedad relativa (`RH2M`).
   - **Dinámica eólica y tormentas de polvo (`dust_norm`):** Movilización eólica combinando velocidad del viento a 10 m (`WS10M`), sequedad superficial y aridez.

3. **Recursos In Situ (ISRU) y Subsuelo (`A.3`):**
   - **Hielo / Permafrost (`cryo_norm`):** Presencia de criosfera o congelamiento estacional ($T_{\min} \le 0^\circ\text{C}$ y cuencas criogénicas de alta montaña/polares, comparables con datos de **NASA LRO Diviner**).
   - **Salmueras y minerales hidratados (`brine_norm`):** Potencial de extracción de agua/oxígeno in situ.
   - **Tubos de lava y cuevas subterráneas (`caves_norm`):** Disponibilidad de refugios naturales contra radiación y micrometeoritos en provincias volcánicas, maares y sistemas kársticos.
   - **Índice compuesto ISRU (`isru_norm`, `isru_resources`).**

---

### SUB-ÍNDICE B: Viabilidad de Operaciones de Base y Despegue
Evalúa qué tan seguro, estable y eficiente es establecer una base de pruebas, operar rovers y realizar despegues/aterrizajes verticales en esa parcela:

1. **Geometría Orbital (`B.1` — `orbital_geometry_norm`):**
   - **Latitud (`orbital_eq_norm` / `orbital_polar_norm`):** Cercanía al ecuador ($\cos|\text{lat}|$) para aprovechar el impulso rotacional en misiones ecuatoriales/marcianas, o latitud polar para simular iluminación solar rasante en el Polo Sur Lunar (*Shackleton Rim*).
   - **Altitud sobre el nivel del mar (`elevation_m`, `elevation_norm`):** Eficiencia energética/atmosférica y enlace de comunicaciones.
   - **Exposición solar (`solar_kwh_m2_day`, `solar_norm`):** Disponibilidad energética fotovoltaica.

2. **Estabilidad Geotécnica de Plataforma (`B.2` — `geotech_stability_norm`):**
   - **Criterio de terreno plano $< 5^\circ$ (`flat_terrain_norm`):** Validación de seguridad estructural para aterrizadores y plataformas de despegue.
   - **Firmeza del sustrato (`substrate_firmness_norm`):** Capacidad portante en seco para soportar cargas dinámicas (penalizando meses de inundación o lodo).
   - **Baja dispersión de partículas abrasivas (`low_abrasion_norm`):** Mientras que en el Sub-Índice A el polvo alto suma similitud con Marte, en el Sub-Índice B se evalúa inversamente para proteger motores, juntas y paneles solares durante operaciones críticas.

3. **Ventana Meteorológica (`B.3` — `weather_window_norm`):**
   - **Velocidad media y ráfagas de viento (`wind_ms`, `wind_gust_ms`, `wind_safety_norm`).**
   - **Estabilidad atmosférica (`atm_stability_norm`).**
   - **Baja nubosidad (`cloud_cover_pct`, `clear_sky_norm`) y baja opacidad por polvo (`low_dust_opacity_norm`).**

---

## 3. Muestreo Global en Tierra Firme y Automatización de Opción 2

### Cinturones Geomorfológicos Globales (Opción 2: ~10% de la Tierra Firme)
En `scripts/generate_global_5km2_grid.py` se definieron **26 cinturones continentales estrictamente en tierra firme** (sin océanos ni mares) que abarcan **2,287,545 parcelas de $5.0\text{ km}^2$** ($\approx 11.4\text{ millones de km}^2$) distribuidas en las **5 categorías exigidas por el reto de la NASA**:
1. **Cuencas Endorreicas y Paleolagos Evaporíticos** (`endorheic`)
2. **Campos Volcánicos Basálticos y Tubos de Lava** (`volcanic` — ej. *El Pinacate*, *Harrat Khaybar*, *Craters of the Moon*, *Campo de Piedra Pómez*, *La Payunia*, *Karapınar*, *Askja/Holuhraun*, *Tolbachik*, *Tibesti*, *Lanzarote*, *Kunlun*)
3. **Cráteres de Impacto en Tierra Firme** (`impact_crater` — ej. *Haughton*, *Barringer*, *Lonar*, *Roter Kamm*, *Tenoumer*, *Monturaqui*, *Zhamanshin*, *Wolfe Creek*, *Aorounga*, *Tswaing*)
4. **Desiertos Hiperáridos y Campos de Regolito Eólico** (`arid_desert` — ej. *Dasht-e Lut*, *Atacama Yungay*, *Qaidam Yardangs*, *Taklamakán*, *Rub' al Khali*, *Tanezrouft*, *Gilf Kebir*, *Namib*, *Gobi*, *Simpson*)
5. **Regiones Polares, Permafrost y Criosfera** (`polar_permafrost` — ej. *McMurdo Wright & Taylor Valleys*, *Isla Devon*, *Svalbard Bockfjorden*, *Changtang-Tíbet*, *Ojos del Salado*)

### Pipeline de Automatización con NASA AppEEARS
- **`scripts/generate_global_5km2_grid.py`:** Genera las celdas de $5.0\text{ km}^2$ por particiones en disco (`data/grid_5km2/`) y exporta lotes JSON de **1,000 coordenadas por tarea** (`data/appeears_batches/`), respetando el límite por tarea de la API de NASA AppEEARS.
- **`scripts/appeears_automator.py`:** Cliente automatizado para la API REST oficial de NASA AppEEARS (`https://appeears.earthdatacloud.nasa.gov/api/`) que:
  1. Autentica con credenciales de NASA Earthdata Login (`.env`).
  2. Envía tareas por lotes solicitando **EMIT L2B Mineralogy (`EMITL2BMIN.001`)**, **MODIS LST Día/Noche (`MOD11A2.061`)**, **MODIS Albedo (`MCD43A3.061`)** y **NASADEM (`NASADEM_NC.001`)**.
  3. Monitorea el progreso (`appeears_state.json`) y descarga automáticamente los CSVs en `data/raw/appeears/`.
- **`scripts/merge_appeears.py`:** Fusiona los CSVs descargados de AppEEARS con la tabla maestra.
- **`scripts/automate_option2_pipeline.py`:** Script maestro que ejecuta todo el flujo de la Opción 2 en un solo comando.

---

## 4. Mejoras en el Frontend (`frontend/index.html`) y Conexión con Google Earth / APIs NASA

1. **Visualización de la Parcela Real de $5.0\text{ km}^2$:** Dibuja sobre el mapa el rectángulo exacto de $2.24\text{ km} \times 2.24\text{ km}$ (`bbox_5km2`) de la muestra seleccionada.
2. **Capas Satelitales (Google Earth / Esri World Imagery + NASA GIBS):** Incluye vista satelital de alta resolución por defecto y la capa **NASA EOSDIS GIBS VIIRS True Color**.
3. **Integración Directa con Google Earth:**
   - Botón **🌍 Ver 5 km² en Google Earth** (abre Google Earth Web en las coordenadas y altitud exactas de la parcela).
   - Botón **📥 Exportar Polígono 5 km² (.KML)** (descarga el polígono `.kml` listo para importar en Google Earth Pro o Web).
   - Botón **🔍 Zoom a Parcela 5 km²** (encuadra automáticamente los $5.0\text{ km}^2$ en el mapa).
4. **Filtro por Provincia Geológica:** Permite filtrar entre las 5 categorías planetarias (Cuencas, Volcánico/Tubos de Lava, Cráteres de Impacto, Desiertos Hiperáridos y Polar/Permafrost).
5. **Transparencia Científica (Criterio del Reto NASA):** Cada sitio objetivo incluye las **Pruebas Recomendadas** y los **Límites del Análogo Terrestre** (gravedad reducida, vacío lunar, presión marciana de $6\text{ mbar}$ y radiación).
