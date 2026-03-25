import React from "react";
import { NavLink } from "react-router-dom";

export default function Navbar({ isAuthenticated, currentUser, onLogout }) {
  return (
    <header className="app-header">
      <div className="brand">
        <span className="app-icon">💼</span>
        <h1>AI Muhasebe</h1>
      </div>

      {isAuthenticated ? (
        <nav className="nav">
          <NavLink
            to="/"
            end
            className={({ isActive }) =>
              isActive ? "nav-link active" : "nav-link"
            }
          >
            🏠 Ana Sayfa
          </NavLink>

          <NavLink
            to="/invoices"
            className={({ isActive }) =>
              isActive ? "nav-link active" : "nav-link"
            }
          >
            📋 Fişler
          </NavLink>

          <NavLink
            to="/reports"
            className={({ isActive }) =>
              isActive ? "nav-link active" : "nav-link"
            }
          >
            📊 Raporlar
          </NavLink>

          <NavLink
            to="/add-income"
            className={({ isActive }) =>
              isActive ? "nav-link active" : "nav-link"
            }
          >
            ➕ Gelir Ekle
          </NavLink>

          <span className="user-badge">👤 {currentUser?.username}</span>
          <button type="button" className="logout-btn" onClick={onLogout}>
            Çıkış
          </button>
        </nav>
      ) : (
        <nav className="nav">
          <NavLink
            to="/login"
            className={({ isActive }) =>
              isActive ? "nav-link active" : "nav-link"
            }
          >
            🔐 Giriş
          </NavLink>
        </nav>
      )}
    </header>
  );
}
