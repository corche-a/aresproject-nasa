export async function GET(request: Request) {
  const name = new URL(request.url).searchParams.get("name");
  const apiKey = process.env.GOOGLE_MAPS_API_KEY;
  if (!name || !name.startsWith("places/") || !apiKey) return new Response("Photo unavailable", { status: 404 });
  const response = await fetch(`https://places.googleapis.com/v1/${name}/media?maxWidthPx=900&key=${encodeURIComponent(apiKey)}`, { next: { revalidate: 86400 } });
  if (!response.ok || !response.body) return new Response("Photo unavailable", { status: 404 });
  return new Response(response.body, { headers: { "content-type": response.headers.get("content-type") ?? "image/jpeg", "cache-control": "public, max-age=86400" } });
}
