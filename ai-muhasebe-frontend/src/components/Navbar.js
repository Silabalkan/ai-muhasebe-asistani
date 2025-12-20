import React from "react";
import { NavLink } from "react-router-dom";

export default function Navbar() {
  return (
    <header className="app-header">
      <div className="brand">
        <span className="app-icon">💼</span>
        <h1>AI Muhasebe</h1>
      </div>

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
      </nav>
    </header>
  );
}
