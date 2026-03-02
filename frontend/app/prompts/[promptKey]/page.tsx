"use client";

import { useParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { createDraft, getPrompt, publishPrompt, rollbackPrompt } from "../../../lib/api";
import type { PromptDetail } from "../../../lib/types";

const DEFAULT_CONTENT = `SYSTEM:
너는 유용한 AI 어시스턴트다.
사용자 요청에 대해 간결하고 정확하게 응답한다.
`;

export default function PromptDetailPage() {
  const params = useParams<{ promptKey: string }>();
  const promptKey = decodeURIComponent(params.promptKey);

  const [detail, setDetail] = useState<PromptDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionMessage, setActionMessage] = useState<string | null>(null);

  const [content, setContent] = useState(DEFAULT_CONTENT);
  const [description, setDescription] = useState("Prompt description");
  const [ownerTeam, setOwnerTeam] = useState("platform");
  const [createdBy, setCreatedBy] = useState("admin");
  const [schemaText, setSchemaText] = useState('{"type":"object","properties":{}}');
  const [env, setEnv] = useState("dev");
  const [publishedBy, setPublishedBy] = useState("admin");
  const [rollbackVersion, setRollbackVersion] = useState(1);

  const activeVersionText = useMemo(() => {
    if (!detail || detail.active_version_id == null) {
      return "-";
    }
    const row = detail.versions.find((v) => v.id === detail.active_version_id);
    return row ? `${row.version}` : "-";
  }, [detail]);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const data = await getPrompt(promptKey);
      setDetail(data);
      if (data.description) {
        setDescription(data.description);
      }
      if (data.owner_team) {
        setOwnerTeam(data.owner_team);
      }
      const top = data.versions[0];
      if (top) {
        setContent(top.content);
        setRollbackVersion(top.version);
        setSchemaText(top.variables_schema ? JSON.stringify(top.variables_schema, null, 2) : '{"type":"object","properties":{}}');
      }
    } catch (err) {
      const msg = (err as Error).message;
      if (!msg.startsWith("404")) {
        setError(msg);
      }
      setDetail(null);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, [promptKey]);

  async function onDraftSave() {
    setActionMessage(null);
    setError(null);
    let variablesSchema: Record<string, unknown> | null = null;
    try {
      variablesSchema = schemaText.trim() ? JSON.parse(schemaText) : null;
    } catch {
      setError("variables_schema JSON이 올바르지 않습니다.");
      return;
    }

    try {
      await createDraft(promptKey, {
        content,
        variables_schema: variablesSchema,
        created_by: createdBy,
        description,
        owner_team: ownerTeam
      });
      setActionMessage("Draft 저장 완료");
      await load();
    } catch (err) {
      setError((err as Error).message);
    }
  }

  async function onPublish() {
    setActionMessage(null);
    setError(null);
    try {
      const res = await publishPrompt(promptKey, env, publishedBy);
      setActionMessage(`Publish 완료: event=${res.publish_event_id}, version=${res.version}, deliveries=${res.deliveries_created}`);
      await load();
    } catch (err) {
      setError((err as Error).message);
    }
  }

  async function onRollback() {
    setActionMessage(null);
    setError(null);
    try {
      const res = await rollbackPrompt(promptKey, env, rollbackVersion, publishedBy);
      setActionMessage(`Rollback 완료: event=${res.publish_event_id}, version=${res.version}`);
      await load();
    } catch (err) {
      setError((err as Error).message);
    }
  }

  return (
    <div className="card">
      <h1>Prompt Detail</h1>
      <p>
        key: <b>{promptKey}</b> | active version: <b>{activeVersionText}</b>
      </p>
      {loading && <p>Loading...</p>}
      {error && <p style={{ color: "#b91c1c" }}>{error}</p>}
      {actionMessage && <p style={{ color: "#065f46" }}>{actionMessage}</p>}

      <h3>Draft Editor</h3>
      <div className="row" style={{ marginBottom: 8 }}>
        <input className="input" value={description} onChange={(e) => setDescription(e.target.value)} placeholder="description" />
        <input className="input" value={ownerTeam} onChange={(e) => setOwnerTeam(e.target.value)} placeholder="owner_team" />
        <input className="input" value={createdBy} onChange={(e) => setCreatedBy(e.target.value)} placeholder="created_by" />
      </div>
      <textarea className="textarea" value={content} onChange={(e) => setContent(e.target.value)} />
      <p>variables_schema(JSON)</p>
      <textarea className="textarea" value={schemaText} onChange={(e) => setSchemaText(e.target.value)} />
      <div className="row" style={{ marginTop: 8 }}>
        <button className="button" onClick={onDraftSave}>
          Save Draft
        </button>
      </div>

      <h3 style={{ marginTop: 20 }}>Publish / Rollback</h3>
      <div className="row" style={{ marginBottom: 8 }}>
        <select className="select" value={env} onChange={(e) => setEnv(e.target.value)}>
          <option value="dev">dev</option>
          <option value="stg">stg</option>
          <option value="prod">prod</option>
        </select>
        <input
          className="input"
          value={publishedBy}
          onChange={(e) => setPublishedBy(e.target.value)}
          placeholder="published_by"
        />
        <button className="button secondary" onClick={onPublish}>
          Publish Latest Draft
        </button>
      </div>
      <div className="row">
        <input
          className="input"
          type="number"
          value={rollbackVersion}
          min={1}
          onChange={(e) => setRollbackVersion(Number(e.target.value))}
        />
        <button className="button warning" onClick={onRollback}>
          Rollback
        </button>
      </div>

      <h3 style={{ marginTop: 20 }}>Versions</h3>
      <table className="table">
        <thead>
          <tr>
            <th>version</th>
            <th>status</th>
            <th>checksum</th>
            <th>created_by</th>
            <th>updated_at</th>
          </tr>
        </thead>
        <tbody>
          {(detail?.versions ?? []).map((item) => (
            <tr key={item.id} style={detail?.active_version_id === item.id ? { background: "#eff6ff" } : undefined}>
              <td>{item.version}</td>
              <td>{item.status}</td>
              <td>{item.checksum.slice(0, 16)}...</td>
              <td>{item.created_by ?? "-"}</td>
              <td>{new Date(item.updated_at).toLocaleString()}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
