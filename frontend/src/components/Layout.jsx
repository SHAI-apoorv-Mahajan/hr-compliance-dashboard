import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const navItems = [
  { to: "/dashboard", label: "Dashboard" },
  { to: "/upload", label: "Upload" },
  { to: "/employees", label: "Employees" },
  { to: "/attendance", label: "Attendance" },
  { to: "/leave", label: "Leave" },
  { to: "/flags", label: "Flags" },
  { to: "/email", label: "Email Center" },
  { to: "/settings", label: "Settings" },
];

export default function Layout() {
  const { user, signOut } = useAuth();
  const navigate = useNavigate();

  function handleSignOut() {
    signOut();
    navigate("/login");
  }

  return (
    <div className="min-h-screen flex">
      <aside className="w-56 bg-slate-900 text-slate-100 flex flex-col">
        <div className="px-4 py-5 border-b border-slate-700">
          <div className="font-semibold">HR Compliance</div>
          <div className="text-xs text-slate-400">ShortHills Tech</div>
        </div>
        <nav className="flex-1 py-2">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `block px-4 py-2 text-sm hover:bg-slate-800 ${
                  isActive ? "bg-slate-800 text-white border-l-2 border-blue-500" : ""
                }`
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="px-4 py-3 border-t border-slate-700 text-xs">
          <div className="truncate">{user?.email}</div>
          <button onClick={handleSignOut} className="mt-2 text-slate-400 hover:text-white">
            Sign out
          </button>
        </div>
      </aside>
      <main className="flex-1 overflow-auto p-6 bg-slate-50">
        <Outlet />
      </main>
    </div>
  );
}
