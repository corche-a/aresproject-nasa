export interface AskContext { month?: number; target?: string; weights?: Record<string, number>; tools_data?: unknown; }
export async function askAres(question: string, context: AskContext) {
  const endpoint = process.env.ARES_AI_ENDPOINT;
  if (!endpoint) return null;
  // TODO(AWS-AI): adjust request/response shape to my endpoint (API Gateway/Lambda/SageMaker/Bedrock).
  const response = await fetch(endpoint, { method: "POST", headers: { "content-type": "application/json", ...(process.env.ARES_AI_TOKEN ? { authorization: `Bearer ${process.env.ARES_AI_TOKEN}` } : {}) }, body: JSON.stringify({ question, filters: context, tools_data: context.tools_data }), signal: AbortSignal.timeout(8000) });
  if (!response.ok) throw new Error(`ARES AI request failed: ${response.status}`);
  return response.json() as Promise<{ answer: string; chart?: unknown; actions?: unknown; citations?: string[] }>;
}
