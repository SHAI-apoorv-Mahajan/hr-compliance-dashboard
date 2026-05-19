import { useEffect, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import PeriodPicker, { defaultPeriod } from "../components/PeriodPicker";
import { analyticsApi } from "../api";

const COLORS = [
  "#2563eb",
  "#dc2626",
  "#f59e0b",
  "#10b981",
  "#8b5cf6",
  "#ec4899",
  "#0891b2",
  "#6b7280",
  "#84cc16",
];

export default function Dashboard() {
  const [period, setPeriod] = useState(defaultPeriod());
  const [overview, setOverview] = useState(null);
  const [attendance, setAttendance] = useState([]);
  const [flags, setFlags] = useState([]);
  const [trend, setTrend] = useState([]);

  useEffect(() => {
    Promise.all([
      analyticsApi.overview(period.start, period.end),
      analyticsApi.attendanceChart(period.start, period.end),
      analyticsApi.flagDistribution(period.start, period.end),
      analyticsApi.lateTrend(),
    ])
      .then(([o, a, f, t]) => {
        setOverview(o);
        setAttendance(a);
        setFlags(f);
        setTrend(t);
      })
      .catch(() => {});
  }, [period.start, period.end]);

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-semibold">Dashboard</h1>
        <PeriodPicker start={period.start} end={period.end} onChange={setPeriod} />
      </div>

      <div className="grid grid-cols-5 gap-4">
        <Card label="Total Employees" value={overview?.total_employees ?? "—"} />
        <Card
          label="Flagged This Period"
          value={overview?.flagged_employees ?? "—"}
          tone="red"
        />
        <Card
          label="Attendance Rate"
          value={overview ? `${overview.attendance_rate_pct}%` : "—"}
        />
        <Card
          label="WFH Compliance"
          value={overview ? `${overview.wfh_compliance_pct}%` : "—"}
        />
        <Card label="Emails Sent" value={overview?.emails_sent_this_period ?? "—"} />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <Panel title="Attendance % by Employee">
          {attendance.length === 0 ? (
            <Empty />
          ) : (
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={attendance}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                <YAxis />
                <Tooltip />
                <Bar dataKey="attendance_pct" fill="#2563eb" />
              </BarChart>
            </ResponsiveContainer>
          )}
        </Panel>
        <Panel title="Flag Distribution">
          {flags.length === 0 ? (
            <Empty />
          ) : (
            <ResponsiveContainer width="100%" height={280}>
              <PieChart>
                <Pie data={flags} dataKey="count" nameKey="flag_type" outerRadius={100}>
                  {flags.map((_, i) => (
                    <Cell key={i} fill={COLORS[i % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          )}
        </Panel>
      </div>

      <Panel title="Late Arrivals — Trend (last 6 periods)">
        {trend.length === 0 ? (
          <Empty />
        ) : (
          <ResponsiveContainer width="100%" height={240}>
            <LineChart data={trend}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="period_start" />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey="late_arrival_total" stroke="#dc2626" />
            </LineChart>
          </ResponsiveContainer>
        )}
      </Panel>
    </div>
  );
}

function Card({ label, value, tone }) {
  return (
    <div className="bg-white rounded shadow-sm p-4">
      <div className="text-xs text-slate-500">{label}</div>
      <div className={`text-2xl font-semibold mt-1 ${tone === "red" ? "text-red-600" : ""}`}>
        {value}
      </div>
    </div>
  );
}

function Panel({ title, children }) {
  return (
    <div className="bg-white rounded shadow-sm p-4">
      <div className="text-sm font-medium text-slate-700 mb-3">{title}</div>
      {children}
    </div>
  );
}

function Empty() {
  return (
    <div className="h-60 flex items-center justify-center text-slate-400 text-sm">
      No data for this period. Upload files and run the pipeline.
    </div>
  );
}
