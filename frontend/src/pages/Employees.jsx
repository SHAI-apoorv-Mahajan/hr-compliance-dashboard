import { useEffect, useState } from "react";
import { employeesApi } from "../api";
import { detailFromError } from "../api/client";

export default function Employees() {
  const [rows, setRows] = useState([]);
  const [err, setErr] = useState("");
  const [editing, setEditing] = useState({}); // emp_code -> draft email
  const [selected, setSelected] = useState(null);

  async function refresh() {
    try {
      setRows(await employeesApi.list());
    } catch (e) {
      setErr(detailFromError(e));
    }
  }

  useEffect(() => {
    refresh();
  }, []);

  async function saveEmail(empCode) {
    const draft = editing[empCode];
    if (!draft) return;
    try {
      await employeesApi.updateEmail(empCode, draft);
      setEditing((s) => {
        const next = { ...s };
        delete next[empCode];
        return next;
      });
      await refresh();
    } catch (e) {
      setErr(detailFromError(e));
    }
  }

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">Employees</h1>
      {err && (
        <div className="bg-red-50 text-red-700 text-sm p-3 rounded">{err}</div>
      )}
      <div className="bg-white rounded shadow-sm overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="text-left text-slate-500 text-xs uppercase">
            <tr>
              <th className="px-3 py-2">Emp Code</th>
              <th>Name</th>
              <th>Email</th>
              <th>Project</th>
              <th>Client</th>
              <th>Role</th>
              <th>Billing</th>
              <th>Working Model</th>
              <th>WFH Credits</th>
              <th>InTime Deadline</th>
            </tr>
          </thead>
          <tbody>
            {rows.length === 0 && (
              <tr>
                <td colSpan="10" className="text-center text-slate-400 py-6">
                  No employees yet. Upload a roster file first.
                </td>
              </tr>
            )}
            {rows.map((r) => (
              <tr
                key={r.id}
                className="border-t border-slate-100 hover:bg-slate-50 cursor-pointer"
                onClick={() => setSelected(r)}
              >
                <td className="px-3 py-2 font-mono text-xs">
                  {r.emp_code || "—"}
                </td>
                <td>{r.name}</td>
                <td onClick={(e) => e.stopPropagation()}>
                  <input
                    type="email"
                    defaultValue={r.email || ""}
                    onBlur={(e) => {
                      if (e.target.value !== (r.email || "")) {
                        setEditing((s) => ({
                          ...s,
                          [r.emp_code]: e.target.value,
                        }));
                        saveEmail(r.emp_code);
                      }
                    }}
                    onKeyDown={(e) => {
                      if (e.key === "Enter") e.target.blur();
                    }}
                    className="border border-slate-200 rounded px-2 py-0.5 text-xs w-48"
                  />
                </td>
                <td>{r.project || "—"}</td>
                <td>{r.client || "—"}</td>
                <td>{r.in_team_role || "—"}</td>
                <td>{r.billing_status || "—"}</td>
                <td>
                  {r.working_model}
                  {r.is_permanent_wfh && (
                    <span className="ml-1 text-xs px-1 rounded bg-purple-100 text-purple-700">
                      Perm
                    </span>
                  )}
                </td>
                <td>{r.wfh_credits_monthly}</td>
                <td>{r.intime_deadline || "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {selected && (
        <div
          className="fixed inset-0 bg-black/30 flex justify-end z-50"
          onClick={() => setSelected(null)}
        >
          <div
            className="bg-white w-96 h-full p-6 overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex justify-between items-start">
              <div>
                <div className="font-semibold">{selected.name}</div>
                <div className="text-xs text-slate-500">
                  {selected.emp_code}
                </div>
              </div>
              <button
                onClick={() => setSelected(null)}
                className="text-slate-400"
              >
                ×
              </button>
            </div>
            <div className="mt-4 space-y-2 text-sm">
              <Field label="Email" v={selected.email} />
              <Field label="Project" v={selected.project} />
              <Field label="Client" v={selected.client} />
              <Field label="Role" v={selected.in_team_role} />
              <Field label="Billing" v={selected.billing_status} />
              <Field label="Working Model" v={selected.working_model} />
              <Field
                label="Permanent WFH"
                v={selected.is_permanent_wfh ? "Yes" : "No"}
              />
              <Field label="WFH Credits" v={selected.wfh_credits_monthly} />
              <Field label="InTime Deadline" v={selected.intime_deadline} />
              <div className="mt-3">
                <div className="text-xs text-slate-500 mb-1">Schedule</div>
                <div className="flex gap-1 flex-wrap">
                  {[
                    ["Mon", selected.schedule_monday],
                    ["Tue", selected.schedule_tuesday],
                    ["Wed", selected.schedule_wednesday],
                    ["Thu", selected.schedule_thursday],
                    ["Fri", selected.schedule_friday],
                    ["Sat", selected.schedule_saturday],
                    ["Sun", selected.schedule_sunday],
                  ].map(([d, v]) => (
                    <span
                      key={d}
                      className="text-xs px-2 py-0.5 rounded bg-slate-100 text-slate-700"
                    >
                      {d}: {v || "—"}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function Field({ label, v }) {
  return (
    <div>
      <div className="text-xs text-slate-500">{label}</div>
      <div>{v ?? "—"}</div>
    </div>
  );
}
