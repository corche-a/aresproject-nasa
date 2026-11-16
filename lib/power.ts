export async function getPower(lat: number, lon: number) {
  const url = new URL("https://power.larc.nasa.gov/api/temporal/monthly/point");
  url.search = new URLSearchParams({ parameters: "T2M,PRECTOTCORR,WS10M,T2M_MAX,T2M_MIN", community: "RE", longitude: String(lon), latitude: String(lat), start: "2015", end: "2024", format: "JSON" }).toString();
  const response = await fetch(url, { next: { revalidate: 86400 } });
  if (!response.ok) throw new Error(`NASA POWER request failed: ${response.status}`);
  return response.json();
}
