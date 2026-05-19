import { useEffect, useState } from "react";
import { BrowserRouter, Routes, Route, useLocation, Navigate } from "react-router-dom";
import "@/App.css";

import { api } from "@/lib/api";
import Login from "@/pages/Login";
import AuthCallback from "@/pages/AuthCallback";
import Chat from "@/pages/Chat";

function AppRouter() {
  const location = useLocation();

  // Process OAuth callback synchronously during render — prevents race conditions
  if (typeof window !== "undefined" && window.location.hash?.includes("session_id=")) {
    return <AuthCallback />;
  }

  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/" element={<ProtectedHome />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

function ProtectedHome() {
  const location = useLocation();
  const [authState, setAuthState] = useState(location.state?.user ? "in" : "checking");
  const [user, setUser] = useState(location.state?.user || null);

  useEffect(() => {
    if (location.state?.user) return;
    // CRITICAL: skip /me check if returning from OAuth callback
    if (window.location.hash?.includes("session_id=")) return;

    let cancelled = false;
    (async () => {
      try {
        const { data } = await api.get("/auth/me");
        if (cancelled) return;
        setUser(data);
        setAuthState("in");
      } catch {
        if (cancelled) return;
        setAuthState("out");
      }
    })();
    return () => { cancelled = true; };
  }, [location.state]);

  const handleLogout = async () => {
    try { await api.post("/auth/logout"); } catch {}
    setUser(null);
    setAuthState("out");
  };

  if (authState === "checking") {
    return (
      <div className="min-h-screen w-full bg-[#F9F8F6] flex items-center justify-center text-[#7A7A71] font-body text-sm">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-[#D05C42] animate-pulse" />
          <span className="w-2 h-2 rounded-full bg-[#D05C42] animate-pulse [animation-delay:150ms]" />
          <span className="w-2 h-2 rounded-full bg-[#D05C42] animate-pulse [animation-delay:300ms]" />
        </div>
      </div>
    );
  }

  if (authState === "out") return <Navigate to="/login" replace />;
  return <Chat user={user} onLogout={handleLogout} />;
}

function App() {
  return (
    <BrowserRouter>
      <AppRouter />
    </BrowserRouter>
  );
}

export default App;
