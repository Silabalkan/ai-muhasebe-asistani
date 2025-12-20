import React, { useEffect, useState } from "react";
import { Bar } from "react-chartjs-2";
import { getReportSummary } from "../api";

import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from "chart.js";

/* 🔴 ÇOK ÖNEMLİ: register MUTLAKA component dışı */
ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
);

export default function ReportsPage() {
  const [summary, setSummary] = useState(null);
  const [period, setPeriod] = useState("monthly");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadSummary();
  }, [period]);

  const loadSummary = async () => {
    try {
      setLoading(true);
      const response = await getReportSummary({ period });
      setSummary(response.data);
    } catch (err) {
      console.error(err);
      alert("Rapor alınırken hata oluştu");
    } finally {
      setLoading(false);
    }
  };

  /* 🔒 Chart verisi SADECE summary varsa oluşturuluyor */
  const chartData =
    summary && {
      labels: ["Gelir", "Gider"],
      datasets: [
        {
          label: "₺ Tutar",
          data: [summary.total_income, summary.total_expense],
          backgroundColor: ["#10b981", "#ef4444"],
          borderRadius: 8,
          borderWidth: 2,
          borderColor: ["#059669", "#dc2626"],
        },
      ],
    };

  const chartOptions = {
    responsive: true,
    plugins: {
      legend: {
        display: true,
        position: "top",
        labels: {
          padding: 20,
          font: {
            size: 14,
            weight: 600,
          },
        },
      },
      title: {
        display: false,
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        ticks: {
          callback: function (value) {
            return value + " ₺";
          },
        },
      },
    },
  };

  return (
    <section className="card">
      <h2>📊 Finansal Raporlar</h2>

      {/* FİLTRE */}
      <div className="filter-row">
        <label>🗓️ Dönem Seçin:</label>
        <select
          value={period}
          onChange={(e) => setPeriod(e.target.value)}
        >
          <option value="weekly">📅 Haftalık</option>
          <option value="monthly">📆 Aylık</option>
          <option value="yearly">📅 Yıllık</option>
        </select>
      </div>

      {loading && (
        <p className="empty-text">⏳ Rapor yükleniyor...</p>
      )}

      {!loading && summary && (
        <>
          {/* ÖZET KARTLAR */}
          <div className="summary-cards">
            <div className="summary income">
              <span>💰 Toplam Gelir</span>
              <strong>{summary.total_income.toLocaleString("tr-TR")} ₺</strong>
            </div>

            <div className="summary expense">
              <span>💸 Toplam Gider</span>
              <strong>{summary.total_expense.toLocaleString("tr-TR")} ₺</strong>
            </div>

            <div className="summary net">
              <span>📈 Net Durum</span>
              <strong>{summary.net.toLocaleString("tr-TR")} ₺</strong>
            </div>
          </div>

          {/* 🔴 Chart SADECE data varsa render */}
          {chartData && (
            <div className="chart-wrapper">
              <Bar data={chartData} options={chartOptions} />
            </div>
          )}
        </>
      )}
    </section>
  );
}
