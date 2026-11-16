import { askAres } from "../../../lib/ai";
import { promises as fs } from "node:fs";
import path from "node:path";
export async function POST(request: Request) {
  const body = await request.json().catch(() => null);
  if (!body || typeof body.question !== "string" || body.question.length > 500) return Response.json({ error: "Question must be 1-500 characters" }, { status: 400 });
  try {
    const result = await askAres(body.question, body.context ?? {});
    if (result) return Response.json({ ...result, label: "AI-generated from NASA data" });
  } catch (error) { console.error(error); }
  const fallback = JSON.parse(await fs.readFile(path.join(process.cwd(), "public", "data", "briefs.json"), "utf8")) as { briefs: { answer: string }[] };
  return Response.json({ answer: fallback.briefs[0]?.answer ?? "Fallback brief unavailable.", fallback: true, label: "AI-generated from NASA data" });
}
