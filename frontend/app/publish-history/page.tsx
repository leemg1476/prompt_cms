"use client";

import { useEffect, useState } from "react";
import { getPublishEvents, runWorkerOnce } from "../../lib/api";
import type { PublishEventItem } from "../../lib/types";

function statusClass(status: string): string {
  if (status === "success") {
    return "badge success";
  }
  if (status === "failed") {
    return "badge failed";
  }
  return "badge pending";
}

export default function PublishHistoryPage() {
  const [items, setItems] = useState<PublishEventItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      setItems(await getPublishEvents());
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function onRunWorker() {
    setMessage(null);
    setError(null);
    try {
      const res = await runWorkerOnce();
      setMessage(
        `worker result: processed=${res.processed}, succeeded=${res.succeeded}, failed=${res.failed}, pending=${res.still_pending}`
      );
      await load();
    } catch (err) {
      setError((err as Error).message);
    }
  }

  return (
    <div className="card">
      <h1>Publish History</h1>
      <div className="row" style={{ marginBottom: 10 }}>
        <button className="button secondary" onClick={load}>
          Refresh
        </button>
        <button className="button" onClick={onRunWorker}>
          Run Worker Once
        </button>
      </div>
      {message && <p style={{ color: "#065f46" }}>{message}</p>}
      {loading && <p>Loading...</p>}
      {error && <p style={{ color: "#b91c1c" }}>{error}</p>}

      {!loading &&
        !error &&
        items.map((event) => (
          <div key={event.publish_event_id} className="card" style={{ marginBottom: 12 }}>
            <p>
              <b>{event.prompt_key}</b> v{event.version} | env={event.environment} | event={event.publish_event_id} |{" "}
              {new Date(event.published_at).toLocaleString()}
            </p>
            <table className="table">
              <thead>
                <tr>
                  <th>delivery_id</th>
                  <th>agent_id</th>
                  <th>status</th>
                  <th>attempt</th>
                  <th>http</th>
                  <th>error</th>
                  <th>next_retry_at</th>
                </tr>
              </thead>
              <tbody>
                {event.deliveries.map((d) => (
                  <tr key={d.id}>
                    <td>{d.id}</td>
                    <td>{d.agent_id}</td>
                    <td>
                      <span className={statusClass(d.status)}>{d.status}</span>
                    </td>
                    <td>{d.attempt}</td>
                    <td>{d.last_http_status ?? "-"}</td>
                    <td>{d.last_error ?? "-"}</td>
                    <td>{d.next_retry_at ? new Date(d.next_retry_at).toLocaleString() : "-"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ))}
    </div>
  );
}
