export interface AskContext {
  month?: number;
  target?: string;
  weights?: Record<string, number>;
  tools_data?: unknown;
}

interface GeminiResponse {
  candidates?: Array<{ content?: { parts?: Array<{ text?: string }> } }>;
}

export class GoogleAiRequestError extends Error {
  constructor(public readonly status: number, details: string) {
    super(`Google AI Studio request failed: ${status} ${details}`);
    this.name = "GoogleAiRequestError";
  }
}

export async function askAres(question: string, context: AskContext) {
  const apiKey = process.env.GOOGLE_AI_API_KEY;
  if (!apiKey) return null;

  const model = process.env.GOOGLE_AI_MODEL ?? "gemini-3.8-flash";
  const endpoint = `https://generativelanguage.googleapis.com/v1beta/models/${encodeURIComponent(model)}:generateContent?key=${encodeURIComponent(apiKey)}`;
  const prompt = [
    "You are ARES, a concise scientific assistant for a NASA analogue-site explorer.",
    "Answer only from the provided ARES context. Explain uncertainty and do not invent measurements.",
    `Question: ${question}`,
    `ARES context: ${JSON.stringify(context)}`,
  ].join("\n\n");
  const request = {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({
      contents: [{ role: "user", parts: [{ text: prompt }] }],
      generationConfig: { temperature: 0.2, maxOutputTokens: 600 },
    }),
    signal: AbortSignal.timeout(30000),
  };
  let response = await fetch(endpoint, request);
  if (response.status === 503) {
    await new Promise((resolve) => setTimeout(resolve, 1200));
    response = await fetch(endpoint, request);
  }
  if (!response.ok) {
    const details = (await response.text()).slice(0, 300);
    throw new GoogleAiRequestError(response.status, details);
  }

  const result = await response.json() as GeminiResponse;
  const answer = result.candidates?.[0]?.content?.parts
    ?.map((part) => part.text)
    .filter((text): text is string => Boolean(text))
    .join("\n")
    .trim();
  if (!answer) throw new Error("Google AI Studio returned no answer text");
  return { answer, citations: [], model };
}
