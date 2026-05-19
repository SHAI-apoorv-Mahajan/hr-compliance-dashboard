import { useEffect, useState } from "react";
import { emailApi, settingsApi } from "../api";
import { detailFromError } from "../api/client";

export default function Settings() {
  const [tab, setTab] = useState("thresholds");
  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-semibold">Settings</h1>
        <div className="flex gap-2">
          {["thresholds", "templates", "system"].map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`px-3 py-1 rounded text-sm capitalize ${
                tab === t ? "bg-slate-900 text-white" : "bg-slate-200"
              }`}
            >
              {t}
            </button>
          ))}
        </div>
      </div>
      {tab === "thresholds" && <Thresholds />}
      {tab === "templates" && <Templates />}
      {tab === "system" && <SystemConfig />}
    </div>
  );
}

function Thresholds() {
  const [rows, setRows] = useState([]);
  const [err, setErr] = useState("");

  function refresh() {
    settingsApi
      .thresholds()
      .then(setRows)
      .catch((e) => setErr(detailFromError(e)));
  }
  useEffect(refresh, []);

  async function save(flagType, value) {
    try {
      await settingsApi.updateThreshold(flagType, Number(value));
      refresh();
    } catch (e) {
      setErr(detailFromError(e));
    }
  }

  return (
    <div className="bg-white rounded shadow-sm p-4">
      {err && <div className="text-red-600 text-sm mb-2">{err}</div>}
      <table className="w-full text-sm">
        <thead className="text-left text-slate-500 text-xs uppercase">
          <tr>
            <th className="px-3 py-2">Flag Type</th>
            <th>Threshold</th>
            <th>Unit</th>
            <th>Description</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.flag_type} className="border-t border-slate-100">
              <td className="px-3 py-2 font-mono text-xs">{r.flag_type}</td>
              <td>
                <input
                  type="number"
                  defaultValue={r.threshold_value}
                  onBlur={(e) => {
                    if (Number(e.target.value) !== r.threshold_value) {
                      save(r.flag_type, e.target.value);
                    }
                  }}
                  className="border rounded px-2 py-0.5 text-sm w-20"
                />
              </td>
              <td className="text-xs text-slate-500">{r.threshold_unit}</td>
              <td className="text-xs text-slate-600">{r.description}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Templates() {
  const [rows, setRows] = useState([]);
  const [editing, setEditing] = useState(null);
  const [err, setErr] = useState("");

  function refresh() {
    emailApi
      .templates(true)
      .then(setRows)
      .catch((e) => setErr(detailFromError(e)));
  }
  useEffect(refresh, []);

  async function save(payload) {
    try {
      if (editing?.id) {
        await emailApi.updateTemplate(editing.id, payload);
      } else {
        await emailApi.createTemplate(payload);
      }
      setEditing(null);
      refresh();
    } catch (e) {
      setErr(detailFromError(e));
    }
  }

  async function remove(id) {
    if (!confirm("Delete this template?")) return;
    try {
      await emailApi.deleteTemplate(id);
      refresh();
    } catch (e) {
      setErr(detailFromError(e));
    }
  }

  return (
    <div className="grid grid-cols-2 gap-4">
      <div className="bg-white rounded shadow-sm p-4">
        <div className="flex justify-between items-center mb-2">
          <div className="text-sm font-medium">Templates</div>
          <button
            onClick={() =>
              setEditing({ name: "", flag_type: "", subject: "", body: "" })
            }
            className="text-xs bg-blue-600 text-white px-2 py-1 rounded"
          >
            + New
          </button>
        </div>
        {err && <div className="text-red-600 text-xs mb-2">{err}</div>}
        <div className="text-sm space-y-1 max-h-96 overflow-y-auto">
          {rows.map((t) => (
            <div
              key={t.id}
              className="border border-slate-200 rounded p-2 flex justify-between items-center"
            >
              <div>
                <div className="font-medium">{t.name}</div>
                <div className="text-xs text-slate-500">
                  {t.flag_type || "—"}
                </div>
              </div>
              <div className="flex gap-2 text-xs">
                <button onClick={() => setEditing(t)} className="text-blue-600">
                  Edit
                </button>
                <button onClick={() => remove(t.id)} className="text-red-600">
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {editing && (
        <TemplateEditor
          template={editing}
          onSave={save}
          onCancel={() => setEditing(null)}
        />
      )}
    </div>
  );
}

function TemplateEditor({ template, onSave, onCancel }) {
  const [name, setName] = useState(template.name);
  const [flagType, setFlagType] = useState(template.flag_type || "");
  const [subject, setSubject] = useState(template.subject);
  const [body, setBody] = useState(template.body);

  const sampleVars = {
    employee_name: "Alice Doe",
    emp_code: "E001",
    period: "Apr 2026",
    period_start: "2026-04-01",
    period_end: "2026-04-30",
    flag_count: "4",
    flag_dates: "2026-04-01, 2026-04-02",
    threshold: "3",
    sender_name: "HR Team, ShortHills Tech",
  };
  function render(s) {
    return s.replace(
      /\{\{\s*(\w+)\s*\}\}/g,
      (_, k) => sampleVars[k] || `{{${k}}}`,
    );
  }

  return (
    <div className="bg-white rounded shadow-sm p-4 space-y-2">
      <input
        value={name}
        onChange={(e) => setName(e.target.value)}
        placeholder="Name"
        className="w-full border rounded px-2 py-1 text-sm"
      />
      <input
        value={flagType}
        onChange={(e) => setFlagType(e.target.value)}
        placeholder="Flag type (optional)"
        className="w-full border rounded px-2 py-1 text-sm"
      />
      <input
        value={subject}
        onChange={(e) => setSubject(e.target.value)}
        placeholder="Subject"
        className="w-full border rounded px-2 py-1 text-sm"
      />
      <textarea
        value={body}
        onChange={(e) => setBody(e.target.value)}
        placeholder="Body — use {{variable}} placeholders"
        rows="10"
        className="w-full border rounded px-2 py-1 text-sm font-mono"
      />
      <div className="text-xs text-slate-500 mt-1">
        Preview (with dummy values):
      </div>
      <div className="border border-slate-200 rounded p-2 text-xs">
        <div className="font-semibold">{render(subject)}</div>
        <pre className="whitespace-pre-wrap mt-1">{render(body)}</pre>
      </div>
      <div className="flex gap-2">
        <button
          onClick={() =>
            onSave({ name, flag_type: flagType || null, subject, body })
          }
          className="bg-blue-600 text-white px-3 py-1 rounded text-sm"
        >
          Save
        </button>
        <button
          onClick={onCancel}
          className="bg-slate-200 px-3 py-1 rounded text-sm"
        >
          Cancel
        </button>
      </div>
    </div>
  );
}

function SystemConfig() {
  const [config, setConfig] = useState(null);
  useEffect(() => {
    emailApi
      .configStatus()
      .then(setConfig)
      .catch(() => {});
  }, []);
  const missing = config?.missing || [];
  const all = ["GRAPH_TENANT_ID", "GRAPH_CLIENT_ID", "GRAPH_CLIENT_SECRET"];
  return (
    <div className="bg-white rounded shadow-sm p-4">
      <div className="text-sm text-slate-600 mb-3">
        Microsoft Graph credentials are read from environment variables. Set
        them in your <code>.env</code> file and restart the backend.
      </div>
      <table className="w-full text-sm">
        <tbody>
          {all.map((k) => (
            <tr key={k} className="border-t border-slate-100">
              <td className="px-3 py-2 font-mono text-xs">{k}</td>
              <td>
                {missing.includes(k) ? (
                  <span className="text-red-600">Not Set ✗</span>
                ) : (
                  <span className="text-green-600">Set ✓</span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
