import React, { useEffect, useState } from "react";
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import {
  getAdvancedReport,
  getTrendReport,
  getCategoryDistribution,
} from "../api";

export default function ReportsPage() {
  const [period, setPeriod] = useState("monthly");
  const [customDateRange, setCustomDateRange] = useState({
    startDate: "",
    endDate: "",
  });
  const [showCustomRange, setShowCustomRange] = useState(false);
  const [advancedData, setAdvancedData] = useState(null);
  const [trendData, setTrendData] = useState(null);
  const [categoryData, setCategoryData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadAllReports();
  }, [period]);

  const loadAllReports = async () => {
    try {
      setLoading(true);
      const [advanced, trend, category] = await Promise.all([
        getAdvancedReport({ period }),
        getTrendReport({ months: 6 }),
        getCategoryDistribution({ period }),
      ]);

      setAdvancedData(advanced.data);
      setTrendData(trend.data.trend);
      setCategoryData(category.data.categories);
    } catch (err) {
      console.error(err);
      alert("Rapor yüklenirken hata oluştu");
    } finally {
      setLoading(false);
    }
  };

  // PASTA GRAFİĞİ VERİSİ
  const pieData = advancedData
    ? [
        {
          name: "Gelir",
          value: advancedData.total_income,
        },
        {
          name: "Gider",
          value: advancedData.total_expense,
        },
      ]
    : [];

  return (
    <>
      {/* BAŞLIK */}
      <section className="card">
        <h2>📊 Finansal Raporlar</h2>

        {/* FİLTRE */}
        <div className="filter-row">
          <label>🗓️ Dönem Seçin:</label>
          <select
            value={period}
            onChange={(e) => {
              setPeriod(e.target.value);
              if (e.target.value !== "custom") {
                setShowCustomRange(false);
              }
            }}
          >
            <option value="weekly">📅 Bu Hafta</option>
            <option value="monthly">📅 Bu Ay</option>
            <option value="yearly">📅 Bu Yıl</option>
            <option value="custom">📆 Özel Tarih Aralığı</option>
          </select>

          {/* ÖZEL TARİH ARAŞTIRMASI */}
          {period === "custom" && (
            <div className="custom-date-range">
              <input
                type="date"
                value={customDateRange.startDate}
                onChange={(e) =>
                  setCustomDateRange({
                    ...customDateRange,
                    startDate: e.target.value,
                  })
                }
                placeholder="Başlangıç tarihi"
              />
              <span className="date-separator">-</span>
              <input
                type="date"
                value={customDateRange.endDate}
                onChange={(e) =>
                  setCustomDateRange({
                    ...customDateRange,
                    endDate: e.target.value,
                  })
                }
                placeholder="Bitiş tarihi"
              />
              <button
                onClick={loadAllReports}
                disabled={!customDateRange.startDate || !customDateRange.endDate}
                className="btn-apply"
              >
                ✓ Uygula
              </button>
            </div>
          )}
        </div>
      </section>

      {loading ? (
        <section className="card">
          <p className="empty-text">⏳ Raporlar yükleniyor...</p>
        </section>
      ) : (
        <>
          {/* KPI KARTLARI */}
          {advancedData && (
            <section className="card">
              <h3>📈 Anahtar Metrikler (KPI)</h3>
              <div className="kpi-grid">
                {/* Toplam Gelir */}
                <div className="kpi-card">
                  <div className="kpi-icon">💰</div>
                  <div className="kpi-content">
                    <h4>Toplam Gelir</h4>
                    <p className="kpi-value income">
                      {advancedData.total_income.toLocaleString("tr-TR", {
                        maximumFractionDigits: 2,
                      })} ₺
                    </p>
                    <span className="kpi-label">
                      {advancedData.income_count} işlem
                    </span>
                  </div>
                </div>

                {/* Toplam Gider */}
                <div className="kpi-card">
                  <div className="kpi-icon">💸</div>
                  <div className="kpi-content">
                    <h4>Toplam Gider</h4>
                    <p className="kpi-value expense">
                      {advancedData.total_expense.toLocaleString("tr-TR", {
                        maximumFractionDigits: 2,
                      })} ₺
                    </p>
                    <span className="kpi-label">
                      {advancedData.expense_count} işlem
                    </span>
                  </div>
                </div>

                {/* Net Kar/Zarar */}
                <div className="kpi-card">
                  <div className="kpi-icon">📊</div>
                  <div className="kpi-content">
                    <h4>Net Kar/Zarar</h4>
                    <p
                      className={`kpi-value ${
                        advancedData.net >= 0 ? "income" : "expense"
                      }`}
                    >
                      {advancedData.net.toLocaleString("tr-TR", {
                        maximumFractionDigits: 2,
                      })} ₺
                    </p>
                    <span className="kpi-label">
                      {advancedData.profitability_rate.toFixed(1)}% Karlılık
                    </span>
                  </div>
                </div>

                {/* Ortalama Gelir */}
                <div className="kpi-card">
                  <div className="kpi-icon">📌</div>
                  <div className="kpi-content">
                    <h4>Ort. Gelir</h4>
                    <p className="kpi-value income">
                      {advancedData.avg_income.toLocaleString("tr-TR", {
                        maximumFractionDigits: 2,
                      })} ₺
                    </p>
                    <span className="kpi-label">
                      {advancedData.income_count > 0
                        ? "İşlem başına"
                        : "Veri yok"}
                    </span>
                  </div>
                </div>

                {/* Ortalama Gider */}
                <div className="kpi-card">
                  <div className="kpi-icon">📍</div>
                  <div className="kpi-content">
                    <h4>Ort. Gider</h4>
                    <p className="kpi-value expense">
                      {advancedData.avg_expense.toLocaleString("tr-TR", {
                        maximumFractionDigits: 2,
                      })} ₺
                    </p>
                    <span className="kpi-label">
                      {advancedData.expense_count > 0
                        ? "İşlem başına"
                        : "Veri yok"}
                    </span>
                  </div>
                </div>

                {/* Toplam KDV */}
                <div className="kpi-card">
                  <div className="kpi-icon">📋</div>
                  <div className="kpi-content">
                    <h4>Toplam KDV</h4>
                    <p className="kpi-value">
                      {advancedData.total_kdv.toLocaleString("tr-TR", {
                        maximumFractionDigits: 2,
                      })} ₺
                    </p>
                    <span className="kpi-label">Vergilendirebilir tutar</span>
                  </div>
                </div>
              </div>
            </section>
          )}

          {/* GRAFİKLER */}
          <div className="chart-grid">
            {/* PASTA GRAFİK */}
            {advancedData && (
              <section className="card">
                <h3>💹 Gelir vs Gider Oranı</h3>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={pieData}
                      cx="50%"
                      cy="50%"
                      labelLine={true}
                      label={({ name, value }) =>
                        `${name}: ${value.toLocaleString("tr-TR", {
                          maximumFractionDigits: 0,
                        })} ₺`
                      }
                      outerRadius={100}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      <Cell fill="#10b981" />
                      <Cell fill="#ef4444" />
                    </Pie>
                    <Tooltip
                      formatter={(value) =>
                        value.toLocaleString("tr-TR", {
                          maximumFractionDigits: 2,
                        }) + " ₺"
                      }
                    />
                  </PieChart>
                </ResponsiveContainer>
              </section>
            )}

            {/* TREND GRAFIK */}
            {trendData && trendData.length > 0 && (
              <section className="card">
                <h3>📈 Aylık Trend (Son 6 Ay)</h3>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={trendData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="month" />
                    <YAxis
                      tickFormatter={(value) =>
                        (value / 1000).toFixed(0) + "K₺"
                      }
                    />
                    <Tooltip
                      formatter={(value) =>
                        value.toLocaleString("tr-TR", {
                          maximumFractionDigits: 2,
                        }) + " ₺"
                      }
                    />
                    <Legend />
                    <Line
                      type="monotone"
                      dataKey="income"
                      stroke="#10b981"
                      strokeWidth={2}
                      name="Gelir"
                    />
                    <Line
                      type="monotone"
                      dataKey="expense"
                      stroke="#ef4444"
                      strokeWidth={2}
                      name="Gider"
                    />
                    <Line
                      type="monotone"
                      dataKey="net"
                      stroke="#0066cc"
                      strokeWidth={2}
                      name="Net"
                    />
                  </LineChart>
                </ResponsiveContainer>
              </section>
            )}
          </div>

          {/* KATEGORİ DAĞILIM */}
          {categoryData && categoryData.length > 0 && (
            <section className="card">
              <h3>🏪 En Çok Harcama Yapılan Satıcılar/Kategoriler</h3>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={categoryData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis
                    dataKey="name"
                    angle={-45}
                    textAnchor="end"
                    height={80}
                  />
                  <YAxis
                    tickFormatter={(value) =>
                      (value / 1000).toFixed(0) + "K₺"
                    }
                  />
                  <Tooltip
                    formatter={(value) =>
                      value.toLocaleString("tr-TR", {
                        maximumFractionDigits: 2,
                      }) + " ₺"
                    }
                  />
                  <Legend />
                  <Bar dataKey="amount" fill="#0066cc" name="Tutar" />
                </BarChart>
              </ResponsiveContainer>
            </section>
          )}

          {/* ÖDEME TİPİ DAĞILIM */}
          {advancedData && advancedData.payment_distribution.length > 0 && (
            <section className="card">
              <h3>💳 Ödeme Tipi Dağılımı</h3>
              <div className="payment-distribution">
                {advancedData.payment_distribution.map((payment, idx) => (
                  <div key={idx} className="payment-item">
                    <div className="payment-header">
                      <h4>{payment.type}</h4>
                      <span className="payment-count">{payment.count} işlem</span>
                    </div>
                    <p className="payment-amount">
                      {payment.amount.toLocaleString("tr-TR", {
                        maximumFractionDigits: 2,
                      })} ₺
                    </p>
                    <div className="payment-bar">
                      <div
                        className="payment-bar-fill"
                        style={{
                          width: `${
                            (payment.amount /
                              Math.max(
                                ...advancedData.payment_distribution.map(
                                  (p) => p.amount
                                )
                              )) *
                            100
                          }%`,
                        }}
                      ></div>
                    </div>
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* UYARILAR & ÖNERİLER */}
          {advancedData && (
            <section className="card warning-card">
              <h3>⚠️ Analiz & Öneriler</h3>
              <div className="alerts">
                {advancedData.profitability_rate < 0 ? (
                  <div className="alert alert-danger">
                    <span className="alert-icon">❌</span>
                    <span>
                      Dikkat! Gideriniz gelirden fazla. Kar marjı{" "}
                      <strong>
                        {advancedData.profitability_rate.toFixed(1)}%
                      </strong>
                    </span>
                  </div>
                ) : advancedData.profitability_rate < 20 ? (
                  <div className="alert alert-warning">
                    <span className="alert-icon">⚠️</span>
                    <span>
                      Kardılık oranınız{" "}
                      <strong>{advancedData.profitability_rate.toFixed(1)}%</strong> -
                      Giderleri azaltmayı düşünebilirsiniz
                    </span>
                  </div>
                ) : (
                  <div className="alert alert-success">
                    <span className="alert-icon">✅</span>
                    <span>
                      Kardılık oranınız{" "}
                      <strong>{advancedData.profitability_rate.toFixed(1)}%</strong> -
                      Harika gidiyor!
                    </span>
                  </div>
                )}

                {advancedData.income_count === 0 && (
                  <div className="alert alert-info">
                    <span className="alert-icon">ℹ️</span>
                    <span>
                      Bu dönemde henüz gelir kaydı yok. Gelir Ekle sayfasından
                      başlayın.
                    </span>
                  </div>
                )}

                {advancedData.expense_count === 0 && (
                  <div className="alert alert-info">
                    <span className="alert-icon">ℹ️</span>
                    <span>
                      Bu dönemde henüz gider kaydı yok. Ana sayfadan fiş
                      yüklemeye başlayın.
                    </span>
                  </div>
                )}

                {advancedData.total_kdv > 0 && (
                  <div className="alert alert-info">
                    <span className="alert-icon">📋</span>
                    <span>
                      Bu dönem toplam KDV tutarınız:{" "}
                      <strong>
                        {advancedData.total_kdv.toLocaleString("tr-TR", {
                          maximumFractionDigits: 2,
                        })} ₺
                      </strong>
                    </span>
                  </div>
                )}
              </div>
            </section>
          )}
        </>
      )}
    </>
  );
}
