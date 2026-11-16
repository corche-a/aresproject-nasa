export default function About() {
  return <main className="shell">
    <section className="hero about-hero">
      <div className="eyebrow">About ARES</div>
      <h1>Earth is our testbed for planetary exploration.</h1>
      <p>ARES is a NASA open-data discovery tool that identifies Earth locations whose measured environmental patterns can help analog studies for the Moon and Mars.</p>
    </section>
    <section className="about-grid">
      <article className="card"><div className="label">Project origin</div><h2>NASA Space Apps Challenge 2026</h2><p>Developed at CUGDL in Guadalajara, Jalisco, Mexico, during the ongoing NASA Space Apps Challenge. The project is designed for transparent exploration, not as a substitute for mission or field validation.</p></article>
      <article className="card"><div className="label">Scientific purpose</div><h2>Find process analogues</h2><p>ARES compares closed-basin, aridity, thermal, aeolian, topographic, and mineral-affinity signals across 56 Earth basins and 672 monthly windows.</p></article>
    </section>
    <section className="card about-section"><div className="label">Data and APIs</div><div className="api-grid">
      <article><h2>NASA POWER</h2><p>Provides temperature, precipitation, wind, humidity, and solar-radiation climate variables for basin coordinates.</p><code>power.larc.nasa.gov</code></article>
      <article><h2>NASA GIBS</h2><p>Provides the interactive map imagery and selectable Blue Marble, MODIS Terra, MODIS Aqua, and VIIRS layers.</p><code>gibs.earthdata.nasa.gov</code></article>
      <article><h2>Copernicus DEM</h2><p>Provides the elevation and slope inputs used in the stored basin dataset.</p><code>Copernicus DEM</code></article>
      <article><h2>OpenStreetMap Nominatim</h2><p>Provides reverse-geocoded country and address context for a selected location, with server-side caching.</p><code>nominatim.openstreetmap.org</code></article>
      <article><h2>ARES AI (optional)</h2><p>Connects to your AWS endpoint for summaries. The application remains usable in fallback mode when no endpoint is configured.</p><code>ARES_AI_ENDPOINT</code></article>
    </div></section>
    <section className="card about-section"><div className="label">Complementary scoring layers</div><h2>Analogy fidelity and operational screening</h2><p>The Explorer weights NASA POWER aridity, thermal range, wind and humidity signals alongside DEM slope, mineral-literature affinity, latitude, elevation, platform flatness, and a transparent weather-window proxy. Granulometry, ice, brines, caves, cloud cover, and aerosol opacity are not scored until verified NASA products are added.</p></section>
    <section className="card about-section"><div className="label">Responsible interpretation</div><h2>Analogy is specific, never absolute.</h2><p>Every result identifies the dimensions that match and the dimensions that diverge. Earth does not reproduce extraterrestrial gravity, atmosphere, radiation, or planetary operations. Protected areas, local communities, and environmental authorities must be consulted before any field activity.</p></section>
  </main>;
}
