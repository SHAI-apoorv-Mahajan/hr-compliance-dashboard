export default function PeriodPicker({ start, end, onChange }) {
  return (
    <div className="flex items-center gap-2">
      <label className="text-sm text-slate-600">Period:</label>
      <input
        type="date"
        value={start}
        onChange={(e) => onChange({ start: e.target.value, end })}
        className="border border-slate-300 rounded px-2 py-1 text-sm"
      />
      <span className="text-slate-400">to</span>
      <input
        type="date"
        value={end}
        onChange={(e) => onChange({ start, end: e.target.value })}
        className="border border-slate-300 rounded px-2 py-1 text-sm"
      />
    </div>
  );
}

export function defaultPeriod() {
  const today = new Date();
  const start = new Date(today.getFullYear(), today.getMonth() - 1, 1);
  const end = new Date(today.getFullYear(), today.getMonth(), 0);
  return {
    start: start.toISOString().slice(0, 10),
    end: end.toISOString().slice(0, 10),
  };
}
