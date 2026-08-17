import { createContext, useContext, useState } from "react";
import { api } from "../api/client.js";

const AuthContext = createContext(null);
const STORAGE_KEY = "cellmind.auth";

export function AuthProvider({ children }) {
  const [session, setSession] = useState(() => {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : null;
  });

  async function login(email, password) {
    const { accessToken, user } = await api.login(email, password);
    const next = { accessToken, user };
    localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
    setSession(next);
    return next;
  }

  function logout() {
    localStorage.removeItem(STORAGE_KEY);
    setSession(null);
  }

  const permissions = session?.user?.role?.permissions || [];
  const has = (perm) => permissions.includes(perm);

  return (
    <AuthContext.Provider value={{ session, user: session?.user, has, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
