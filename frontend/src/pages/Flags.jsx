import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import PeriodPicker, { defaultPeriod } from "../components/PeriodPicker";
import { flagsApi } from "../api";
import { detailFromError } from "../api/client";

const FLAG_TYPES = [
  "LATE_ARRIVAL",
  "EARLY_DEPARTURE",
  "ABSENT_WITHOUT_LEAVE",
  "CONSECUTIVE_ABSENCE",
  "NO_OUT_PUNCH",
  "HALF_DAY_FREQUENCY",
  "WFH_QUOTA_EXCEEDED",
  "LOW_WORK_HOURS",
  "WFO_VIOLATION",
];

export default function Flags() {
  const [period, setPeriod] = useState(defaultPeriod());
  const [flagType, setFlagType] = useState("");
  const [empCode, setEmpCode] = useState("");
  const [flags, setFlags] = useState([]);
  const [selected, setSelected] = useState(new Set());
  const [err, setErr] = useState("");
  const navigate = useNavigate();

  async function refresh() {
    try {
      const data = await flagsApi.list({
        period_start: period.start,
        period_end: period.end,
        flag_type: flagType || undefined,
        emp_code: empCode || undefined,
      });
      setFlags(data);
    } catch (e) {
      setErr(detailFromError(e));
    }
  }

  useEffect(() => {
    refresh();
  }, [period.start, period.end, flagType, empCode]);

  async function resolve(flagId) {
    await flagsApi.resolve(flagId);
    refresh();
  }

  function toggle(id) {
    setSelected((s) => {
      const next = new Set(s);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  function sendBulk() {
    if (selected.size === 0) return;
    const ids = Array.from(selected).join(",");
    navigate(`/email?flag_ids=${ids}`);
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-semibold">Flags</h1>
        <PeriodPicker
          start={period.start}
          end={period.end}
          onChange={setPeriod}
        />
      </div>

      {err && (
        <div className="bg-red-50 text-red-700 text-sm p-3 rounded">{err}</div>
      )}

      <div className="bg-white rounded shadow-sm p-3 flex gap-3 items-center">
        <select
          value={flagType}
          onChange={(e) => setFlagType(e.target.value)}
          className="border rounded px-2 py-1 text-sm"
        >
          <option value="">All flag types</option>
          {FLAG_TYPES.map((t) => (
            <option key={t} value={t}>
              {t}
            </option>
          ))}
        </select>
        <input
          type="text"
          placeholder="Emp code"
          value={empCode}
          onChange={(e) => setEmpCode(e.target.value)}
          className="border rounded px-2 py-1 text-sm"
        />
        <div className="flex-1" />
        <button
          onClick={sendBulk}
          disabled={selected.size === 0}
          className="bg-blue-600 hover:bg-blue-700 disabled:opacity-40 text-white px-3 py-1 rounded text-sm"
        >
          Send Bulk Emails ({selected.size})
        </button>
      </div>

      <div className="bg-white rounded shadow-sm overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="text-left text-slate-500 text-xs uppercase">
            <tr>
              <th className="px-3 py-2"></th>
              <th>Employee</th>
              <th>Flag Type</th>
              <th>Value</th>
              <th>Threshold</th>
              <th>Dates</th>
              <th>Email Sent</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {flags.length === 0 && (
              <tr>
                <td colSpan="8" className="text-center text-slate-400 py-6">
                  No active flags.
                </td>
              </tr>
            )}
            {flags.map((f) => (
              <tr key={f.id} className="border-t border-slate-100">
                <td className="px-3 py-2">
                  <input
                    type="checkbox"
                    checked={selected.has(f.id)}
                    onChange={() => toggle(f.id)}
                  />
                </td>
                <td>{f.employee_name || f.emp_code}</td>
                <td className="font-mono text-xs">{f.flag_type}</td>
                <td>{f.flag_value}</td>
                <td>{f.threshold_value}</td>
                <td className="text-xs text-slate-600">
                  {(f.flag_details?.dates || []).join(", ")}
                </td>
                <td>{f.email_sent ? "✓" : ""}</td>
                <td>
                  <button
                    onClick={() => resolve(f.id)}
                    className="text-xs text-slate-600 hover:text-slate-900"
                  >
                    Resolve
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
