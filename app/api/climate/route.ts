import { getPower } from "../../../lib/power";
export async function GET(request: Request) {
  const { searchParams } = new URL(request.url); const lat = Number(searchParams.get("lat")); const lon = Number(searchParams.get("lon"));
  if (!Number.isFinite(lat) || !Number.isFinite(lon)) return Response.json({ error: "lat and lon are required" }, { status: 400 });
  try { return Response.json(await getPower(lat, lon)); } catch (error) { console.error(error); return Response.json({ error: "NASA POWER unavailable" }, { status: 502 }); }
}
