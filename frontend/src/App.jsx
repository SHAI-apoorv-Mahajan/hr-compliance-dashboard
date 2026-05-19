import { Navigate, Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import ProtectedRoute from "./components/ProtectedRoute";
import Attendance from "./pages/Attendance";
import Dashboard from "./pages/Dashboard";
import EmailCenter from "./pages/EmailCenter";
import Employees from "./pages/Employees";
import Flags from "./pages/Flags";
import Leave from "./pages/Leave";
import Login from "./pages/Login";
import Settings from "./pages/Settings";
import Upload from "./pages/Upload";

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/upload" element={<Upload />} />
        <Route path="/employees" element={<Employees />} />
        <Route path="/attendance" element={<Attendance />} />
        <Route path="/leave" element={<Leave />} />
        <Route path="/flags" element={<Flags />} />
        <Route path="/email" element={<EmailCenter />} />
        <Route path="/settings" element={<Settings />} />
      </Route>
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}
