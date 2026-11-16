import { askAres, GoogleAiRequestError } from "../../../lib/ai";
import { promises as fs } from "node:fs";
import path from "node:path";

export async function POST(request: Request) {
  const body = await request.json().catch(() => null);
  if (!body || typeof body.question !== "string" || body.question.trim().length === 0 || body.question.length > 500) {
    return Response.json({ error: "Question must be 1-500 characters" }, { status: 400 });
  }
  const hasGoogleKey = Boolean(process.env.GOOGLE_AI_API_KEY);
  let failureReason: "request_failed" | "service_unavailable" | "invalid_api_key" | "quota_exceeded" | "model_unavailable" = "request_failed";
  try {
    const result = await askAres(body.question, body.context ?? {});
    if (result) return Response.json({ ...result, label: "AI-generated from NASA data" });
  } catch (error) {
    console.error("ARES Google AI request failed", error);
    if (error instanceof GoogleAiRequestError) {
      if (error.status === 401 || error.status === 403) failureReason = "invalid_api_key";
      else if (error.status === 429) failureReason = "quota_exceeded";
      else if (error.status === 404) failureReason = "model_unavailable";
      else if (error.status === 503) failureReason = "service_unavailable";
    }
  }
  const fallback = JSON.parse(await fs.readFile(path.join(process.cwd(), "public", "data", "briefs.json"), "utf8")) as { briefs: { answer: string }[] };
  const fallbackReason = hasGoogleKey ? failureReason : "missing_api_key";
  const answer = fallbackReason === "service_unavailable"
    ? "Google AI Studio is temporarily unavailable. Please try Ask ARES again in a moment. The local NASA ranking remains available."
    : fallbackReason === "invalid_api_key"
      ? "The Google AI Studio key was rejected. Check GOOGLE_AI_API_KEY in Amplify and redeploy. The local NASA ranking remains available."
      : fallbackReason === "quota_exceeded"
        ? "The Google AI Studio quota was exceeded. Check billing or limits for the key. The local NASA ranking remains available."
        : fallbackReason === "model_unavailable"
          ? "The configured Gemini model is unavailable for this API key. Set GOOGLE_AI_MODEL to a model enabled in Google AI Studio and redeploy."
          : fallback.briefs[0]?.answer ?? "Fallback brief unavailable.";
  return Response.json({
    answer,
    fallback: true,
    fallbackReason,
    label: !hasGoogleKey
      ? "Google AI Studio key not configured - local fallback"
      : failureReason === "service_unavailable"
        ? "Google AI Studio temporarily unavailable - local fallback"
        : failureReason === "invalid_api_key"
          ? "Google AI Studio key rejected - local fallback"
          : failureReason === "quota_exceeded"
            ? "Google AI Studio quota exceeded - local fallback"
            : failureReason === "model_unavailable"
              ? "Google AI Studio model unavailable - local fallback"
              : "Google AI Studio request failed - local fallback",
  });
}
