import React, { useMemo, useState } from "react";
import { BrowserRouter, Routes, Route, Navigate, useNavigate } from "react-router-dom";
import "./App.css";

import Navbar from "./components/Navbar";
import HomePage from "./pages/HomePage";
import InvoicesPage from "./pages/InvoicesPage";
import ReportsPage from "./pages/ReportsPage";
import AddIncomePage from "./pages/AddIncomePage";
import { loginUser, registerUser } from "./api";


function RequireAuth({ isAuthenticated, children }) {
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  return children;
}

function LoginPage({ onAuthSuccess }) {
  const navigate = useNavigate();
  const [mode, setMode] = useState("login");
  const [email, setEmail] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [sessionExpired, setSessionExpired] = useState(false);

  React.useEffect(() => {
    if (localStorage.getItem("sessionExpired")) {
      setSessionExpired(true);
      localStorage.removeItem("sessionExpired");
    }
  }, []);

  const submit = async (e) => {
    e.preventDefault();
    try {
      setLoading(true);

      const res =
        mode === "login"
          ? await loginUser(username, password)
          : await registerUser(email, username, password);

      const { access_token, user } = res.data;
      localStorage.setItem("token", access_token);
      localStorage.setItem("user", JSON.stringify(user));
      onAuthSuccess(user);
      navigate("/", { replace: true });
    } catch (error) {
      const msg = error?.response?.data?.detail || "Giriş/Kayıt başarısız";
      alert(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="card auth-card">
      <h2>Hesabına Giriş Yap</h2>
      <p className="upload-desc">Sistemi kullanmak için giriş yap veya yeni hesap oluştur.</p>
      {sessionExpired && (
        <div style={{ color: "#b71c1c", background: "#ffeaea", padding: 10, borderRadius: 6, marginBottom: 10, textAlign: "center" }}>
          Oturum süreniz doldu, lütfen tekrar giriş yapın.
        </div>
      )}
      <div className="auth-tabs">
        <button
          type="button"
          className={mode === "login" ? "auth-tab active" : "auth-tab"}
          onClick={() => setMode("login")}
        >
          Giriş
        </button>
        <button
          type="button"
          className={mode === "register" ? "auth-tab active" : "auth-tab"}
          onClick={() => setMode("register")}
        >
          Kayıt Ol
        </button>
      </div>

      <form className="auth-form" onSubmit={submit}>
        {mode === "register" && (
          <input
            type="email"
            placeholder="E-posta"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        )}

        <input
          type="text"
          placeholder="Kullanıcı adı"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          required
        />

        <input
          type="password"
          placeholder="Şifre"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />

        <button type="submit" disabled={loading}>
          {loading
            ? "Bekleyin..."
            : mode === "login"
            ? "Giriş Yap"
            : "Hesap Oluştur"}
        </button>
      </form>
    </section>
  );
}


function App() {
  const initialUser = useMemo(() => {
    const raw = localStorage.getItem("user");
    if (!raw) return null;
    try {
      return JSON.parse(raw);
    } catch {
      return null;
    }
  }, []);

  const [currentUser, setCurrentUser] = useState(initialUser);
  const token = localStorage.getItem("token");
  const isAuthenticated = Boolean(token && currentUser);

  const logout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    setCurrentUser(null);
  };

  return (
    <BrowserRouter>
      <div className={isAuthenticated ? "app-root app-shell" : "app-root auth-shell"}>
        {isAuthenticated && (
          <Navbar
            isAuthenticated={isAuthenticated}
            currentUser={currentUser}
            onLogout={logout}
          />
        )}

        <div className={isAuthenticated ? "app-content" : "auth-content"}>
          <main className={isAuthenticated ? "app-main" : "auth-main"}>
            <Routes>
              <Route
                path="/login"
                element={
                  isAuthenticated ? (
                    <Navigate to="/" replace />
                  ) : (
                    <LoginPage onAuthSuccess={setCurrentUser} />
                  )
                }
              />
              <Route
                path="/"
                element={
                  <RequireAuth isAuthenticated={isAuthenticated}>
                    <HomePage />
                  </RequireAuth>
                }
              />
              <Route
                path="/invoices"
                element={
                  <RequireAuth isAuthenticated={isAuthenticated}>
                    <InvoicesPage />
                  </RequireAuth>
                }
              />
              <Route
                path="/reports"
                element={
                  <RequireAuth isAuthenticated={isAuthenticated}>
                    <ReportsPage />
                  </RequireAuth>
                }
              />
              <Route
                path="/add-income"
                element={
                  <RequireAuth isAuthenticated={isAuthenticated}>
                    <AddIncomePage />
                  </RequireAuth>
                }
              />

              {/* Tanımsız route gelirse anasayfaya gönder */}
              <Route
                path="*"
                element={<Navigate to={isAuthenticated ? "/" : "/login"} replace />}
              />
            </Routes>
          </main>
        </div>
      </div>
    </BrowserRouter>
  );
}

export default App;
