import { useEffect, useRef, useState } from "react";
import PeriodPicker, { defaultPeriod } from "../components/PeriodPicker";
import { detailFromError } from "../api/client";
import { pipelineApi, uploadApi } from "../api";

export default function Upload() {
  const [period, setPeriod] = useState(defaultPeriod());
  const [history, setHistory] = useState([]);
  const [status, setStatus] = useState(null);
  const [running, setRunning] = useState(false);
  const [runResult, setRunResult] = useState(null);
  const [err, setErr] = useState("");

  async function refresh() {
    try {
      setHistory(await uploadApi.history());
      setStatus(await pipelineApi.status(period.start, period.end));
    } catch {
      // ignore
    }
  }

  useEffect(() => {
    refresh();
  }, [period.start, period.end]);

  async function handleUpload(kind, file) {
    setErr("");
    try {
      if (kind === "greythr") await uploadApi.greythr(file, period.start, period.end);
      else if (kind === "biometric")
        await uploadApi.biometric(file, period.start, period.end);
      else if (kind === "roster") await uploadApi.roster(file);
      await refresh();
    } catch (e) {
      setErr(detailFromError(e));
    }
  }

  async function handleRun() {
    setErr("");
    setRunning(true);
    setRunResult(null);
    try {
      const result = await pipelineApi.run(period.start, period.end);
      setRunResult(result);
      await refresh();
    } catch (e) {
      setErr(detailFromError(e));
    } finally {
      setRunning(false);
    }
  }

  async function handleDelete(id) {
    if (!confirm("Delete this upload? Bronze rows will be removed; silver/gold rebuilt on next run.")) return;
    setErr("");
    try {
      await uploadApi.delete(id);
      await refresh();
    } catch (e) {
      setErr(detailFromError(e));
    }
  }

  const canRun = status?.has_greythr && status?.has_biometric;

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-semibold">Upload</h1>
        <PeriodPicker start={period.start} end={period.end} onChange={setPeriod} />
      </div>

      {err && <div className="bg-red-50 text-red-700 text-sm p-3 rounded border border-red-200">{err}</div>}

      <div className="grid grid-cols-3 gap-4">
        <UploadCard
          title="GreytHR Leave"
          subtitle="Leave ledger (.xlsx)"
          requiresPeriod
          uploaded={status?.has_greythr}
          onUpload={(f) => handleUpload("greythr", f)}
        />
        <UploadCard
          title="Biometric Attendance"
          subtitle="Daily Attendance Report (.xlsx)"
          requiresPeriod
          uploaded={status?.has_biometric}
          onUpload={(f) => handleUpload("biometric", f)}
        />
        <UploadCard
          title="Team Roster"
          subtitle="Team timings & roster (.xlsx) — no period"
          uploaded={history.some((h) => h.file_type === "roster" && h.status === "processed")}
          onUpload={(f) => handleUpload("roster", f)}
        />
      </div>

      <div className="bg-white rounded shadow-sm p-4 space-y-2">
        <div className="flex justify-between items-center">
          <div className="text-sm font-medium text-slate-700">Run Pipeline</div>
          <button
            disabled={!canRun || running}
            onClick={handleRun}
            className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white px-4 py-1.5 rounded text-sm"
          >
            {running ? "Running…" : "Run Pipeline"}
          </button>
        </div>
        {!canRun && (
          <div className="text-xs text-amber-600">
            Need both GreytHR and Biometric uploads for this period.
          </div>
        )}
        {runResult && (
          <div className="text-xs text-slate-600 mt-2 font-mono whitespace-pre-wrap">
            {JSON.stringify(runResult, null, 2)}
          </div>
        )}
      </div>

      <div className="bg-white rounded shadow-sm p-4">
        <div className="text-sm font-medium text-slate-700 mb-3">Upload History</div>
        <table className="w-full text-sm">
          <thead className="text-left text-slate-500 text-xs uppercase">
            <tr>
              <th className="py-2">Type</th>
              <th>Filename</th>
              <th>Period</th>
              <th>Rows</th>
              <th>Status</th>
              <th>Uploaded</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {history.length === 0 && (
              <tr>
                <td colSpan="7" className="py-4 text-slate-400 text-center">
                  No uploads yet
                </td>
              </tr>
            )}
            {history.map((row) => (
              <tr key={row.id} className="border-t border-slate-100">
                <td className="py-2">{row.file_type}</td>
                <td className="truncate max-w-xs">{row.original_filename}</td>
                <td>
                  {row.period_start ? `${row.period_start} → ${row.period_end}` : "—"}
                </td>
                <td>{row.row_count ?? "—"}</td>
                <td>
                  <span
                    className={
                      row.status === "processed"
                        ? "text-green-600"
                        : row.status === "failed"
                        ? "text-red-600"
                        : "text-slate-500"
                    }
                  >
                    {row.status}
                  </span>
                </td>
                <td className="text-xs text-slate-500">
                  {new Date(row.uploaded_at).toLocaleString()}
                </td>
                <td>
                  <button
                    onClick={() => handleDelete(row.id)}
                    className="text-red-600 hover:text-red-800 text-xs"
                  >
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function UploadCard({ title, subtitle, requiresPeriod, uploaded, onUpload }) {
  const inputRef = useRef(null);
  const [selected, setSelected] = useState(null);

  function handleFile(e) {
    const f = e.target.files?.[0];
    if (!f) return;
    if (!f.name.toLowerCase().endsWith(".xlsx")) {
      alert("Only .xlsx files are accepted");
      return;
    }
    setSelected(f);
  }

  async function handleSubmit() {
    if (!selected) return;
    await onUpload(selected);
    setSelected(null);
    if (inputRef.current) inputRef.current.value = "";
  }

  return (
    <div className="bg-white rounded shadow-sm p-4 space-y-2">
      <div className="flex justify-between items-start">
        <div>
          <div className="text-sm font-medium text-slate-700">{title}</div>
          <div className="text-xs text-slate-500">{subtitle}</div>
        </div>
        <span
          className={`text-xs px-2 py-0.5 rounded ${
            uploaded ? "bg-green-100 text-green-700" : "bg-slate-100 text-slate-500"
          }`}
        >
          {uploaded ? "Uploaded ✓" : "Not yet"}
        </span>
      </div>
      <input
        type="file"
        accept=".xlsx"
        ref={inputRef}
        onChange={handleFile}
        className="text-xs"
      />
      <button
        onClick={handleSubmit}
        disabled={!selected}
        className="w-full bg-slate-700 hover:bg-slate-800 disabled:opacity-40 text-white text-xs py-1.5 rounded"
      >
        Upload
      </button>
    </div>
  );
}
