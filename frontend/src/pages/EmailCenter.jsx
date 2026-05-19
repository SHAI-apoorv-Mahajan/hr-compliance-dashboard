import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { emailApi, flagsApi } from "../api";
import { detailFromError } from "../api/client";

export default function EmailCenter() {
  const [tab, setTab] = useState("send");
  const [config, setConfig] = useState({ configured: false, missing: [] });

  useEffect(() => {
    emailApi.configStatus().then(setConfig).catch(() => {});
  }, []);

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-semibold">Email Center</h1>
        <div className="flex gap-2">
          <button
            onClick={() => setTab("send")}
            className={`px-3 py-1 rounded text-sm ${tab === "send" ? "bg-slate-900 text-white" : "bg-slate-200"}`}
          >
            Send
          </button>
          <button
            onClick={() => setTab("history")}
            className={`px-3 py-1 rounded text-sm ${tab === "history" ? "bg-slate-900 text-white" : "bg-slate-200"}`}
          >
            History
          </button>
        </div>
      </div>

      {!config.configured && (
        <div className="bg-yellow-50 border border-yellow-200 text-yellow-800 text-sm p-3 rounded">
          Email service is not yet configured. Contact the system administrator. (Missing:{" "}
          {config.missing.join(", ")})
        </div>
      )}

      {tab === "send" ? <SendTab configured={config.configured} /> : <HistoryTab />}
    </div>
  );
}

function SendTab({ configured }) {
  const [params] = useSearchParams();
  const [templates, setTemplates] = useState([]);
  const [templateId, setTemplateId] = useState("");
  const [flagIds, setFlagIds] = useState([]);
  const [flags, setFlags] = useState([]);
  const [preview, setPreview] = useState([]);
  const [err, setErr] = useState("");
  const [sending, setSending] = useState(false);
  const [results, setResults] = useState([]);

  useEffect(() => {
    emailApi.templates().then(setTemplates).catch(() => {});
    flagsApi.list({}).then(setFlags).catch(() => {});
    const pre = params.get("flag_ids");
    if (pre) setFlagIds(pre.split(","));
  }, []);

  function toggleFlag(id) {
    setFlagIds((s) => (s.includes(id) ? s.filter((x) => x !== id) : [...s, id]));
  }

  async function doPreview() {
    setErr("");
    setPreview([]);
    setResults([]);
    try {
      const out = await emailApi.send(flagIds, templateId, true);
      setPreview(out);
    } catch (e) {
      setErr(detailFromError(e));
    }
  }

  async function doSend() {
    if (!confirm(`Send ${flagIds.length} emails?`)) return;
    setErr("");
    setSending(true);
    try {
      const out = await emailApi.send(flagIds, templateId, false);
      setResults(out);
      setPreview([]);
    } catch (e) {
      setErr(detailFromError(e));
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="grid grid-cols-2 gap-4">
      <div className="bg-white rounded shadow-sm p-4">
        <div className="text-sm font-medium mb-2">1. Select flags</div>
        <div className="max-h-80 overflow-y-auto text-sm space-y-1">
          {flags.map((f) => (
            <label key={f.id} className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={flagIds.includes(f.id)}
                onChange={() => toggleFlag(f.id)}
              />
              <span>
                {f.employee_name || f.emp_code} — {f.flag_type} ({f.flag_value})
              </span>
            </label>
          ))}
        </div>

        <div className="text-sm font-medium mt-4 mb-2">2. Choose template</div>
        <select
          value={templateId}
          onChange={(e) => setTemplateId(e.target.value)}
          className="w-full border rounded px-2 py-1 text-sm"
        >
          <option value="">Select template…</option>
          {templates.map((t) => (
            <option key={t.id} value={t.id}>
              {t.name} {t.flag_type ? `(${t.flag_type})` : ""}
            </option>
          ))}
        </select>

        <div className="flex gap-2 mt-4">
          <button
            disabled={!templateId || flagIds.length === 0}
            onClick={doPreview}
            className="px-3 py-1 rounded bg-slate-700 text-white text-sm disabled:opacity-40"
          >
            Preview
          </button>
          <button
            disabled={!templateId || flagIds.length === 0 || !configured || sending}
            onClick={doSend}
            className="px-3 py-1 rounded bg-blue-600 text-white text-sm disabled:opacity-40"
          >
            {sending ? "Sending…" : "Send"}
          </button>
        </div>
        {err && <div className="text-sm text-red-600 mt-2">{err}</div>}
      </div>

      <div className="bg-white rounded shadow-sm p-4">
        <div className="text-sm font-medium mb-2">3. Preview / Result</div>
        <div className="space-y-3 max-h-96 overflow-y-auto text-xs">
          {preview.map((p) => (
            <div key={p.flag_id} className="border border-slate-200 rounded p-2">
              <div className="font-semibold">{p.subject}</div>
              <div className="text-slate-500">To: {p.recipient_email || "(no email)"}</div>
              <pre className="whitespace-pre-wrap mt-1 text-slate-700">{p.body}</pre>
            </div>
          ))}
          {results.map((r) => (
            <div
              key={r.flag_id}
              className={`border rounded p-2 ${
                r.status === "sent" ? "border-green-200" : "border-red-200"
              }`}
            >
              <div>
                {r.recipient_email}: {r.status}
              </div>
              {r.error_message && <div className="text-red-600">{r.error_message}</div>}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function HistoryTab() {
  const [logs, setLogs] = useState([]);
  useEffect(() => {
    emailApi.logs({}).then(setLogs).catch(() => {});
  }, []);
  return (
    <div className="bg-white rounded shadow-sm overflow-x-auto">
      <table className="w-full text-sm">
        <thead className="text-left text-slate-500 text-xs uppercase">
          <tr>
            <th className="px-3 py-2">Recipient</th>
            <th>Subject</th>
            <th>Status</th>
            <th>Sent At</th>
            <th>Sent By</th>
          </tr>
        </thead>
        <tbody>
          {logs.length === 0 && (
            <tr>
              <td colSpan="5" className="text-center text-slate-400 py-6">
                No emails sent yet.
              </td>
            </tr>
          )}
          {logs.map((l) => (
            <tr key={l.id} className="border-t border-slate-100">
              <td className="px-3 py-2">{l.recipient_email}</td>
              <td className="truncate max-w-xs">{l.subject}</td>
              <td
                className={
                  l.status === "sent"
                    ? "text-green-600"
                    : l.status === "failed"
                    ? "text-red-600"
                    : "text-yellow-600"
                }
              >
                {l.status}
              </td>
              <td className="text-xs text-slate-500">
                {l.sent_at ? new Date(l.sent_at).toLocaleString() : "—"}
              </td>
              <td className="text-xs text-slate-500">{l.sent_by}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
