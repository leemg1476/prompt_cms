import type { PromptDetail, PromptSummary, PublishEventItem } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

type PublishResult = {
  ok: boolean;
  prompt_key: string;
  publish_event_id: number;
  version: number;
  environment: string;
  deliveries_created: number;
};

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {})
    },
    cache: "no-store"
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`${res.status} ${res.statusText}: ${text}`);
  }
  return (await res.json()) as T;
}

export function getPrompts() {
  return request<PromptSummary[]>("/api/prompts");
}

export function getPrompt(promptKey: string) {
  return request<PromptDetail>(`/api/prompts/${encodeURIComponent(promptKey)}`);
}

export function createDraft(promptKey: string, body: Record<string, unknown>) {
  return request(`/api/prompts/${encodeURIComponent(promptKey)}/draft`, {
    method: "POST",
    body: JSON.stringify(body)
  });
}

export function publishPrompt(promptKey: string, env: string, publishedBy: string) {
  return request<PublishResult>(`/api/prompts/${encodeURIComponent(promptKey)}/publish?env=${encodeURIComponent(env)}`, {
    method: "POST",
    body: JSON.stringify({ published_by: publishedBy || null })
  });
}

export function rollbackPrompt(promptKey: string, env: string, toVersion: number, publishedBy: string) {
  return request<PublishResult>(`/api/prompts/${encodeURIComponent(promptKey)}/rollback?env=${encodeURIComponent(env)}`, {
    method: "POST",
    body: JSON.stringify({ to_version: toVersion, published_by: publishedBy || null })
  });
}

export function getPublishEvents(promptKey?: string) {
  const query = promptKey ? `?prompt_key=${encodeURIComponent(promptKey)}` : "";
  return request<PublishEventItem[]>(`/api/publish-events${query}`);
}

export function runWorkerOnce() {
  return request<{ processed: number; succeeded: number; failed: number; still_pending: number }>(
    "/api/worker/run-once",
    { method: "POST" }
  );
}
