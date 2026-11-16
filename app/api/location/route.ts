export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const lat = Number(searchParams.get("lat"));
  const lon = Number(searchParams.get("lon"));
  const name = searchParams.get("name") ?? "";
  if (!Number.isFinite(lat) || !Number.isFinite(lon)) return Response.json({ error: "lat and lon are required" }, { status: 400 });

  let country = "Country unavailable";
  let countryEnglish = country;
  let address = "Address unavailable";
  try {
    const reverse = await fetch(`https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat=${lat}&lon=${lon}`, {
      headers: { "user-agent": "ARES-Analog-Discovery/1.0" },
      next: { revalidate: 86400 },
    });
    if (reverse.ok) {
      const location = await reverse.json() as { display_name?: string; address?: { country?: string } };
      country = location.address?.country ?? country;
      address = location.display_name ?? address;
    }
    const englishReverse = await fetch(`https://nominatim.openstreetmap.org/reverse?format=jsonv2&accept-language=en&lat=${lat}&lon=${lon}`, {
      headers: { "user-agent": "ARES-Analog-Discovery/1.0" },
      next: { revalidate: 86400 },
    });
    if (englishReverse.ok) {
      const location = await englishReverse.json() as { address?: { country?: string } };
      countryEnglish = location.address?.country ?? countryEnglish;
    }
  } catch (error) {
    console.error("Reverse geocoding failed", error);
  }

  const photos: string[] = [];
  const apiKey = process.env.GOOGLE_MAPS_API_KEY;
  if (apiKey && name) {
    try {
      const places = await fetch("https://places.googleapis.com/v1/places:searchText", {
        method: "POST",
        headers: {
          "content-type": "application/json",
          "x-goog-api-key": apiKey,
          "x-goog-fieldmask": "places.photos,places.formattedAddress",
        },
        body: JSON.stringify({ textQuery: name, maxResultCount: 1, locationBias: { circle: { center: { latitude: lat, longitude: lon }, radius: 50000 } } }),
        next: { revalidate: 86400 },
      });
      if (places.ok) {
        const result = await places.json() as { places?: { photos?: { name?: string }[]; formattedAddress?: string }[] };
        const place = result.places?.[0];
        if (place?.formattedAddress) address = place.formattedAddress;
        place?.photos?.forEach((photo) => { if (photo.name) photos.push(photo.name); });
      }
    } catch (error) {
      console.error("Google Places lookup failed", error);
    }
  }
  return Response.json({ country, countryEnglish, address, photos: photos.slice(0, 5) });
}
