const clamp = (value: number) => Math.min(1, Math.max(0, value));

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const latitude = Number(searchParams.get("lat"));
  const longitude = Number(searchParams.get("lon"));
  const month = Number(searchParams.get("month"));
  if (!Number.isFinite(latitude) || !Number.isFinite(longitude) || !Number.isInteger(month) || month < 1 || month > 12) {
    return Response.json({ error: "lat, lon and month are required" }, { status: 400 });
  }
  const endpoint = new URL("https://power.larc.nasa.gov/api/temporal/monthly/point");
  endpoint.searchParams.set("parameters", "ALLSKY_SFC_SW_DWN,CLRSKY_SFC_SW_DWN");
  endpoint.searchParams.set("community", "RE");
  endpoint.searchParams.set("longitude", longitude.toString());
  endpoint.searchParams.set("latitude", latitude.toString());
  endpoint.searchParams.set("start", "2020");
  endpoint.searchParams.set("end", "2020");
  endpoint.searchParams.set("format", "JSON");
  try {
    const response = await fetch(endpoint, { next: { revalidate: 86400 } });
    if (!response.ok) return Response.json({ error: "NASA POWER request failed" }, { status: 502 });
    const payload = await response.json() as { properties?: { parameter?: Record<string, Record<string, number>> } };
    const key = `2020${String(month).padStart(2, "0")}`;
    const allSky = payload.properties?.parameter?.ALLSKY_SFC_SW_DWN?.[key];
    const clearSky = payload.properties?.parameter?.CLRSKY_SFC_SW_DWN?.[key];
    if (typeof allSky !== "number" || typeof clearSky !== "number" || !Number.isFinite(allSky) || !Number.isFinite(clearSky) || clearSky <= 0) {
      return Response.json({ available: false, source: "NASA POWER" });
    }
    return Response.json({
      available: true,
      source: "NASA POWER",
      period: "2020 monthly baseline",
      allSkySolar: allSky,
      clearSkySolar: clearSky,
      cloudAttenuationPct: Math.round(clamp(1 - allSky / clearSky) * 100),
    });
  } catch (error) {
    console.error("NASA POWER cloud proxy failed", error);
    return Response.json({ error: "NASA POWER request failed" }, { status: 502 });
  }
}
