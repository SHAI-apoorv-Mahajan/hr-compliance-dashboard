import { createContext, useContext, useEffect, useState } from "react";
import { login as apiLogin, me as apiMe } from "../api/auth";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (!token) {
      setLoading(false);
      return;
    }
    apiMe()
      .then(setUser)
      .catch(() => localStorage.removeItem("access_token"))
      .finally(() => setLoading(false));
  }, []);

  async function signIn(email, password) {
    const { access_token } = await apiLogin(email, password);
    localStorage.setItem("access_token", access_token);
    const u = await apiMe();
    setUser(u);
    return u;
  }

  function signOut() {
    localStorage.removeItem("access_token");
    setUser(null);
  }

  return (
    <AuthContext.Provider value={{ user, loading, signIn, signOut }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const v = useContext(AuthContext);
  if (!v) throw new Error("useAuth used outside AuthProvider");
  return v;
}
