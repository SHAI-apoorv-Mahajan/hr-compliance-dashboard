import { useEffect, useMemo, useState } from "react";
import PeriodPicker, { defaultPeriod } from "../components/PeriodPicker";
import { leaveApi } from "../api";

export default function Leave() {
  const [period, setPeriod] = useState(defaultPeriod());
  const [rows, setRows] = useState([]);

  useEffect(() => {
    leaveApi.summary(period.start, period.end).then(setRows).catch(() => {});
  }, [period.start, period.end]);

  const allLeaveTypes = useMemo(() => {
    const set = new Set();
    rows.forEach((r) => Object.keys(r.by_type || {}).forEach((k) => set.add(k)));
    return Array.from(set).sort();
  }, [rows]);

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-semibold">Leave Analysis</h1>
        <PeriodPicker start={period.start} end={period.end} onChange={setPeriod} />
      </div>

      <div className="bg-white rounded shadow-sm overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="text-left text-slate-500 text-xs uppercase">
            <tr>
              <th className="px-3 py-2">Employee</th>
              {allLeaveTypes.map((t) => (
                <th key={t}>{t}</th>
              ))}
              <th>WFH Availed</th>
              <th>WFH Credits</th>
              <th>WFH Excess</th>
            </tr>
          </thead>
          <tbody>
            {rows.length === 0 && (
              <tr>
                <td colSpan="100" className="text-center text-slate-400 py-6">
                  No leave data for this period.
                </td>
              </tr>
            )}
            {rows.map((r) => (
              <tr key={r.emp_code} className="border-t border-slate-100">
                <td className="px-3 py-2">{r.name || r.emp_code}</td>
                {allLeaveTypes.map((t) => (
                  <td key={t}>{r.by_type?.[t] ?? 0}</td>
                ))}
                <td>{r.wfh_availed}</td>
                <td>{r.wfh_credits}</td>
                <td className={r.wfh_excess > 0 ? "text-red-600 font-medium" : ""}>
                  {r.wfh_excess}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
