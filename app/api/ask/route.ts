import { askAres } from "../../../lib/ai";
import { promises as fs } from "node:fs";
import path from "node:path";

export async function POST(request: Request) {
  const body = await request.json().catch(() => null);
  if (!body || typeof body.question !== "string" || body.question.trim().length === 0 || body.question.length > 500) {
    return Response.json({ error: "Question must be 1-500 characters" }, { status: 400 });
  }
  const hasGoogleKey = Boolean(process.env.GOOGLE_AI_API_KEY);
  let failureReason: "request_failed" | "service_unavailable" = "request_failed";
  try {
    const result = await askAres(body.question, body.context ?? {});
    if (result) return Response.json({ ...result, label: "AI-generated from NASA data" });
  } catch (error) {
    console.error("ARES Google AI request failed", error);
    if (error instanceof Error && error.message.includes(" 503 ")) failureReason = "service_unavailable";
  }
  const fallback = JSON.parse(await fs.readFile(path.join(process.cwd(), "public", "data", "briefs.json"), "utf8")) as { briefs: { answer: string }[] };
  const fallbackReason = hasGoogleKey ? failureReason : "missing_api_key";
  return Response.json({
    answer: fallback.briefs[0]?.answer ?? "Fallback brief unavailable.",
    fallback: true,
    fallbackReason,
    label: !hasGoogleKey
      ? "Google AI Studio key not configured - local fallback"
      : failureReason === "service_unavailable"
        ? "Google AI Studio temporarily unavailable - local fallback"
        : "Google AI Studio request failed - local fallback",
  });
}
