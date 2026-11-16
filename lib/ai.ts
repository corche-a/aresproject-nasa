export interface AskContext {
  month?: number;
  target?: string;
  weights?: Record<string, number>;
  tools_data?: unknown;
}

interface GeminiResponse {
  candidates?: Array<{ content?: { parts?: Array<{ text?: string }> } }>;
}

export async function askAres(question: string, context: AskContext) {
  const apiKey = process.env.GOOGLE_AI_API_KEY;
  if (!apiKey) return null;

  const model = process.env.GOOGLE_AI_MODEL ?? "gemini-2.5-flash";
  const endpoint = `https://generativelanguage.googleapis.com/v1beta/models/${encodeURIComponent(model)}:generateContent?key=${encodeURIComponent(apiKey)}`;
  const prompt = [
    "You are ARES, a concise scientific assistant for a NASA analogue-site explorer.",
    "Answer only from the provided ARES context. Explain uncertainty and do not invent measurements.",
    `Question: ${question}`,
    `ARES context: ${JSON.stringify(context)}`,
  ].join("\n\n");
  const response = await fetch(endpoint, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({
      contents: [{ role: "user", parts: [{ text: prompt }] }],
      generationConfig: { temperature: 0.2, maxOutputTokens: 600 },
    }),
    signal: AbortSignal.timeout(15000),
  });
  if (!response.ok) throw new Error(`Google AI Studio request failed: ${response.status}`);

  const result = await response.json() as GeminiResponse;
  const answer = result.candidates?.[0]?.content?.parts
    ?.map((part) => part.text)
    .filter((text): text is string => Boolean(text))
    .join("\n")
    .trim();
  if (!answer) throw new Error("Google AI Studio returned no answer text");
  return { answer, citations: [], model };
}
