import React from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import "./App.css";

import Navbar from "./components/Navbar";
import HomePage from "./pages/HomePage";
import InvoicesPage from "./pages/InvoicesPage";
import ReportsPage from "./pages/ReportsPage";
import AddIncomePage from "./pages/AddIncomePage";


function App() {
  return (
    <BrowserRouter>
      <div className="app-root">
        <Navbar />

        <main className="app-main">
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/invoices" element={<InvoicesPage />} />
            <Route path="/reports" element={<ReportsPage />} />

            {/* Tanımsız route gelirse anasayfaya gönder */}
            <Route path="*" element={<Navigate to="/" replace />} />
            <Route path="/add-income" element={<AddIncomePage />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;
