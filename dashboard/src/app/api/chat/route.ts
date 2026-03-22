import { anthropic } from "@ai-sdk/anthropic";
import { streamText } from "ai";

export async function POST(req: Request) {
  const { messages } = await req.json();

  const result = streamText({
    model: anthropic("claude-sonnet-4-6-20250514"),
    system: `You are an AI product manager assistant for Kisasa.io.
You help users understand their project pipeline status, suggest next steps,
and answer questions about their projects. Be concise and actionable.`,
    messages,
  });

  return result.toDataStreamResponse();
}
