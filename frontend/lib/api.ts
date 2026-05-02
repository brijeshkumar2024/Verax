import { ComposePayload, ComposeResponse } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

export async function runCompose(payload: ComposePayload): Promise<ComposeResponse> {
  try {
    const res = await fetch(`${API_BASE}/v1/tick`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      cache: "no-store",
    });

    if (!res.ok) {
      throw new Error(`HTTP ${res.status}`);
    }

    return (await res.json()) as ComposeResponse;
  } catch (err) {
    console.error("API ERROR:", err);
    throw new Error("Backend not reachable");
  }
}
