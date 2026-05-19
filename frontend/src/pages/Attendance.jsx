import { useEffect, useState } from "react";
import PeriodPicker, { defaultPeriod } from "../components/PeriodPicker";
import { attendanceApi } from "../api";

const cellColor = (day) => {
  if (!day) return "bg-slate-100";
  if (day.is_weekly_off) return "bg-slate-300";
  if (day.has_approved_leave) return "bg-blue-300";
  if (day.is_half_present) return "bg-yellow-300";
  if (day.is_absent) return "bg-red-400";
  if (day.status && day.status.includes("Present")) return "bg-green-400";
  return "bg-slate-100";
};

export default function Attendance() {
  const [period, setPeriod] = useState(defaultPeriod());
  const [summary, setSummary] = useState([]);
  const [openEmp, setOpenEmp] = useState(null);
  const [days, setDays] = useState([]);
  const [selectedDay, setSelectedDay] = useState(null);

  useEffect(() => {
    attendanceApi.summary(period.start, period.end).then(setSummary).catch(() => {});
  }, [period.start, period.end]);

  async function openEmployee(emp) {
    setOpenEmp(emp);
    setSelectedDay(null);
    const data = await attendanceApi.forEmployee(emp.emp_code, period.start, period.end);
    setDays(data);
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-semibold">Attendance</h1>
        <PeriodPicker start={period.start} end={period.end} onChange={setPeriod} />
      </div>

      <div className="bg-white rounded shadow-sm overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="text-left text-slate-500 text-xs uppercase">
            <tr>
              <th className="px-3 py-2">Employee</th>
              <th>Present</th>
              <th>Absent</th>
              <th>AWL</th>
              <th>Late</th>
              <th>Early</th>
              <th>No-OutPunch</th>
              <th>Half Days</th>
              <th>Work Hrs</th>
            </tr>
          </thead>
          <tbody>
            {summary.length === 0 && (
              <tr>
                <td colSpan="9" className="text-center text-slate-400 py-6">
                  No data. Run the pipeline for this period.
                </td>
              </tr>
            )}
            {summary.map((r) => (
              <tr
                key={r.emp_code}
                onClick={() => openEmployee(r)}
                className="border-t border-slate-100 hover:bg-slate-50 cursor-pointer"
              >
                <td className="px-3 py-2">{r.name || r.emp_code}</td>
                <td>{r.present_days}</td>
                <td>{r.absent_days}</td>
                <td>{r.absent_without_leave_days}</td>
                <td>{r.late_arrival_count}</td>
                <td>{r.early_departure_count}</td>
                <td>{r.no_out_punch_count}</td>
                <td>{r.half_day_count}</td>
                <td>{(r.total_work_minutes / 60).toFixed(1)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {openEmp && (
        <div className="bg-white rounded shadow-sm p-4">
          <div className="flex justify-between items-center mb-3">
            <div className="font-medium">{openEmp.name || openEmp.emp_code} — Calendar</div>
            <button
              onClick={() => setOpenEmp(null)}
              className="text-xs text-slate-500 hover:text-slate-700"
            >
              Close
            </button>
          </div>
          <div className="grid grid-cols-7 gap-1 text-xs">
            {days.map((d) => (
              <button
                key={d.att_date}
                onClick={() => setSelectedDay(d)}
                className={`h-12 rounded text-xs ${cellColor(d)} text-white font-medium flex items-center justify-center hover:opacity-80`}
              >
                {d.att_date?.slice(-2)}
              </button>
            ))}
          </div>
          <Legend />
          {selectedDay && (
            <div className="mt-3 border-t border-slate-100 pt-3 text-sm">
              <div className="font-medium">{selectedDay.att_date}</div>
              <div className="text-xs text-slate-600 grid grid-cols-4 gap-2 mt-1">
                <div>InTime: {selectedDay.in_time || "—"}</div>
                <div>OutTime: {selectedDay.out_time || "—"}</div>
                <div>LateBy: {selectedDay.late_by_minutes || 0}m</div>
                <div>EarlyGoing: {selectedDay.early_going_by_minutes || 0}m</div>
              </div>
              <div className="text-xs text-slate-500 mt-1">Status: {selectedDay.status}</div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function Legend() {
  return (
    <div className="flex gap-3 mt-3 text-xs text-slate-600">
      <Chip color="bg-green-400" label="Present" />
      <Chip color="bg-red-400" label="Absent" />
      <Chip color="bg-yellow-300" label="½ Present" />
      <Chip color="bg-blue-300" label="Approved Leave" />
      <Chip color="bg-slate-300" label="Weekly Off" />
    </div>
  );
}

function Chip({ color, label }) {
  return (
    <span className="flex items-center gap-1">
      <span className={`w-3 h-3 rounded ${color}`} />
      {label}
    </span>
  );
}
