"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { getPrompts } from "../../lib/api";
import type { PromptSummary } from "../../lib/types";

export default function PromptsPage() {
  const [items, setItems] = useState<PromptSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [newPromptKey, setNewPromptKey] = useState("stock.recommend.prepare");

  async function load() {
    setLoading(true);
    setError(null);
    try {
      setItems(await getPrompts());
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  return (
    <div className="card">
      <h1>Prompt List</h1>
      <p>프롬프트를 선택하거나 새 prompt_key로 상세 페이지를 열어 Draft를 생성하세요.</p>
      <div className="row" style={{ marginBottom: 12 }}>
        <input
          className="input"
          value={newPromptKey}
          onChange={(e) => setNewPromptKey(e.target.value)}
          style={{ minWidth: 320 }}
        />
        <Link href={`/prompts/${encodeURIComponent(newPromptKey)}`} className="button">
          Open Prompt
        </Link>
        <button className="button secondary" onClick={load}>
          Refresh
        </button>
      </div>

      {loading && <p>Loading...</p>}
      {error && <p style={{ color: "#b91c1c" }}>{error}</p>}

      {!loading && !error && (
        <table className="table">
          <thead>
            <tr>
              <th>Prompt Key</th>
              <th>Description</th>
              <th>Owner Team</th>
              <th>Active Version</th>
              <th>Updated At</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item) => (
              <tr key={item.prompt_key}>
                <td>
                  <Link href={`/prompts/${encodeURIComponent(item.prompt_key)}`}>{item.prompt_key}</Link>
                </td>
                <td>{item.description ?? "-"}</td>
                <td>{item.owner_team ?? "-"}</td>
                <td>{item.active_version ?? "-"}</td>
                <td>{new Date(item.updated_at).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
