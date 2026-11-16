import { getBasin } from "../../../../lib/data";
export async function GET(_: Request, { params }: { params: Promise<{ id: string }> }) {
  const records = await getBasin((await params).id);
  return records.length ? Response.json(records) : Response.json({ error: "Basin not found" }, { status: 404 });
}
