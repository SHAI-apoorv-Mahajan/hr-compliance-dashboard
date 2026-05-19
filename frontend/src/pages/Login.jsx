import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { detailFromError } from "../api/client";

export default function Login() {
  const { signIn, user } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("hr@shorthills.ai");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  if (user) {
    navigate("/dashboard", { replace: true });
    return null;
  }

  async function onSubmit(e) {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      await signIn(email, password);
      navigate("/dashboard");
    } catch (err) {
      setError(detailFromError(err));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-100">
      <form
        onSubmit={onSubmit}
        className="bg-white rounded-lg shadow w-96 p-8 space-y-4"
      >
        <div>
          <div className="text-xl font-semibold">HR Compliance Dashboard</div>
          <div className="text-sm text-slate-500">ShortHills Tech — internal tool</div>
        </div>
        <div>
          <label className="text-sm text-slate-700">Email</label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full border border-slate-300 rounded px-3 py-2 text-sm mt-1"
            required
          />
        </div>
        <div>
          <label className="text-sm text-slate-700">Password</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full border border-slate-300 rounded px-3 py-2 text-sm mt-1"
            required
          />
        </div>
        {error && <div className="text-sm text-red-600">{error}</div>}
        <button
          disabled={submitting}
          className="w-full bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white rounded py-2 text-sm font-medium"
          type="submit"
        >
          {submitting ? "Signing in…" : "Sign in"}
        </button>
      </form>
    </div>
  );
}
