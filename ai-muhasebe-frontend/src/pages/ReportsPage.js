import React, { useCallback, useEffect, useMemo, useState } from "react";
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  AreaChart,
  Area,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";
import {
  getAdvancedReport,
  getTrendReport,
  getCategoryDistribution,
  getForecastReport,
  getExpenseAnomaly,
} from "../api";

export default function ReportsPage() {
  const todayStr = new Date().toISOString().slice(0, 10);
  const [period, setPeriod] = useState("monthly");
  const [forecastModel, setForecastModel] = useState("auto");
  const [anomalyThreshold, setAnomalyThreshold] = useState(1.3);
  const [anomalyMethod, setAnomalyMethod] = useState("average");
  const [customDateRange, setCustomDateRange] = useState({
    startDate: "",
    endDate: "",
  });
  const [advancedData, setAdvancedData] = useState(null);
  const [trendData, setTrendData] = useState(null);
  const [categoryData, setCategoryData] = useState(null);
  const [forecastData, setForecastData] = useState(null);
  const [anomalyData, setAnomalyData] = useState(null);
  const [loading, setLoading] = useState(true);

  const loadAllReports = useCallback(async () => {
    try {
      if (
        period === "custom" &&
        (!customDateRange.startDate || !customDateRange.endDate)
      ) {
        return;
      }

      setLoading(true);
      const historyMonthsByPeriod = {
        weekly: 6,
        monthly: 12,
        yearly: 24,
      };
      const historyMonths = historyMonthsByPeriod[period] || 12;

      const isCustom =
        period === "custom" &&
        customDateRange.startDate &&
        customDateRange.endDate;

      const advancedParams = isCustom
        ? {
            period,
            start_date: customDateRange.startDate,
            end_date: customDateRange.endDate,
          }
        : { period };

      const trendParams = isCustom
        ? {
            start_date: customDateRange.startDate,
            end_date: customDateRange.endDate,
          }
        : { months: 6 };

      const forecastParams = isCustom
        ? {
            forecast_months: 3,
            forecast_model: forecastModel,
            start_date: customDateRange.startDate,
            end_date: customDateRange.endDate,
          }
        : {
            history_months: historyMonths,
            forecast_months: 3,
            forecast_model: forecastModel,
          };

      let anomalyWindowMonths = historyMonths;
      if (isCustom) {
        const start = new Date(customDateRange.startDate);
        const end = new Date(customDateRange.endDate);
        const monthDiff =
          (end.getFullYear() - start.getFullYear()) * 12 +
          (end.getMonth() - start.getMonth()) +
          1;
        anomalyWindowMonths = monthDiff;
      }
      anomalyWindowMonths = Math.max(3, Math.min(60, anomalyWindowMonths));

      const anomalyParams = {
        window_months: anomalyWindowMonths,
        threshold_ratio: anomalyThreshold,
        baseline_method: anomalyMethod,
      };

      const [advanced, trend, category, forecast, anomaly] = await Promise.all([
        getAdvancedReport(advancedParams),
        getTrendReport(trendParams),
        getCategoryDistribution(advancedParams),
        getForecastReport(forecastParams),
        getExpenseAnomaly(anomalyParams),
      ]);

      setAdvancedData(advanced.data);
      setTrendData(trend.data.trend);
      setCategoryData(category.data.categories);
      setForecastData(forecast.data);
      setAnomalyData(anomaly.data);
    } catch (err) {
      console.error(err);
      const detail = err?.response?.data?.detail;
      alert(detail ? `Rapor yuklenirken hata olustu: ${detail}` : "Rapor yuklenirken hata olustu");
    } finally {
      setLoading(false);
    }
  }, [
    period,
    customDateRange.startDate,
    customDateRange.endDate,
    forecastModel,
    anomalyThreshold,
    anomalyMethod,
  ]);

  useEffect(() => {
    if (period === "custom") {
      return;
    }
    loadAllReports();
  }, [period, forecastModel, anomalyThreshold, anomalyMethod, loadAllReports]);

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

  const nextMonthForecast = forecastData?.forecast?.[0] || null;
  const forecastQuality = forecastData?.quality || null;

  const confidenceLabels = {
    high: "Yuksek",
    medium: "Orta",
    low: "Dusuk",
    unknown: "Yetersiz Veri",
  };

  const forecastChartData = useMemo(() => {
    if (!forecastData) return [];

    const history = (forecastData.history || []).map((item) => ({
      month: item.month,
      income_actual: item.income,
      expense_actual: item.expense,
      income_forecast: null,
      expense_forecast: null,
      income_lower: null,
      income_upper: null,
      expense_lower: null,
      expense_upper: null,
    }));

    const forecast = (forecastData.forecast || []).map((item) => ({
      month: item.month,
      income_actual: null,
      expense_actual: null,
      income_forecast: item.income,
      expense_forecast: item.expense,
      income_lower: item.income_lower,
      income_upper: item.income_upper,
      expense_lower: item.expense_lower,
      expense_upper: item.expense_upper,
    }));

    return [...history, ...forecast];
  }, [forecastData]);

  const anomalyChartData = useMemo(() => {
    if (!anomalyData?.series || !Array.isArray(anomalyData.series)) return [];
    return anomalyData.series.map((item) => ({
      month: item.month,
      expense: Number(item.expense || 0),
      threshold: Number(anomalyData?.anomaly?.threshold_value || 0),
      baseline: Number(anomalyData?.anomaly?.baseline_value || 0),
    }));
  }, [anomalyData]);

  const historyOnlyChartData = useMemo(() => {
    return forecastChartData.filter(
      (row) => row.income_actual != null || row.expense_actual != null
    );
  }, [forecastChartData]);

  const forecastOnlyChartData = useMemo(() => {
    return forecastChartData.filter(
      (row) => row.income_forecast != null || row.expense_forecast != null
    );
  }, [forecastChartData]);

  const getTightDomain = (data, keys) => {
    const values = [];
    data.forEach((row) => {
      keys.forEach((key) => {
        const v = row[key];
        if (v != null && Number.isFinite(Number(v))) {
          values.push(Number(v));
        }
      });
    });

    if (!values.length) return [0, 100];

    const minVal = Math.min(...values);
    const maxVal = Math.max(...values);

    if (minVal === maxVal) {
      const pad = Math.max(50, maxVal * 0.2 || 50);
      return [Math.max(0, minVal - pad), maxVal + pad];
    }

    const spread = maxVal - minVal;
    const pad = Math.max(20, spread * 0.15);
    return [Math.max(0, minVal - pad), maxVal + pad];
  };

  const historyDomain = useMemo(
    () => getTightDomain(historyOnlyChartData, ["income_actual", "expense_actual"]),
    [historyOnlyChartData]
  );

  const forecastDomain = useMemo(
    () =>
      getTightDomain(forecastOnlyChartData, [
        "income_forecast",
        "expense_forecast",
        "income_lower",
        "income_upper",
        "expense_lower",
        "expense_upper",
      ]),
    [forecastOnlyChartData]
  );

  const currencyTick = (value) => {
    const n = Number(value || 0);
    if (Math.abs(n) >= 10000) {
      return `${(n / 1000).toFixed(1)}K₺`;
    }
    return `${n.toLocaleString("tr-TR", { maximumFractionDigits: 0 })}₺`;
  };

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
            }}
          >
            <option value="weekly">📅 Bu Hafta</option>
            <option value="monthly">📅 Bu Ay</option>
            <option value="yearly">📅 Bu Yıl</option>
            <option value="custom">📆 Özel Tarih Aralığı</option>
          </select>

          <label>🧠 Tahmin Modeli:</label>
          <select
            value={forecastModel}
            onChange={(e) => {
              setForecastModel(e.target.value);
            }}
          >
            <option value="auto">⚙️ Otomatik</option>
            <option value="prophet">🔮 Prophet</option>
            <option value="arima">📉 ARIMA</option>
            <option value="linear">📏 Lineer</option>
          </select>

          <label>🚨 Anomali Esigi:</label>
          <select
            value={anomalyThreshold}
            onChange={(e) => setAnomalyThreshold(Number(e.target.value))}
          >
            <option value={1.2}>%20 Ustu</option>
            <option value={1.3}>%30 Ustu</option>
            <option value={1.4}>%40 Ustu</option>
          </select>

          <label>🧪 Anomali Yontemi:</label>
          <select
            value={anomalyMethod}
            onChange={(e) => setAnomalyMethod(e.target.value)}
          >
            <option value="average">Ortalama (Basit)</option>
            <option value="median_mad">Medyan+MAD (Daha Guvenli)</option>
          </select>

          {/* ÖZEL TARİH ARAŞTIRMASI */}
          {period === "custom" && (
            <div className="custom-date-range">
              <input
                type="date"
                value={customDateRange.startDate}
                max={todayStr}
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
                max={todayStr}
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

          {anomalyData && (
            <section
              className={`card ${
                anomalyData.anomaly?.is_anomaly
                  ? "warning-card"
                  : ""
              }`}
            >
              <h3>🚨 Gider Anomali Kontrolu</h3>
              <p className="upload-desc" style={{ marginTop: 6 }}>
                Son ay gideri, secilen pencere icindeki gecmis gider seviyesine gore degerlendirildi.
              </p>

              {anomalyData.anomaly?.status === "insufficient_data" ||
              anomalyData.anomaly?.status === "insufficient_baseline" ? (
                <div className="alert alert-info">
                  <span className="alert-icon">ℹ️</span>
                  <span>{anomalyData.anomaly.message}</span>
                </div>
              ) : anomalyData.anomaly?.is_anomaly ? (
                <div className="alert alert-danger">
                  <span className="alert-icon">⚠️</span>
                  <span>{anomalyData.anomaly.message}</span>
                </div>
              ) : (
                <div className="alert alert-success">
                  <span className="alert-icon">✅</span>
                  <span>{anomalyData.anomaly?.message}</span>
                </div>
              )}

              {anomalyData.anomaly?.status === "ok" && (
                <div className="kpi-grid" style={{ marginTop: 12 }}>
                  <div className="kpi-card">
                    <div className="kpi-icon">📌</div>
                    <div className="kpi-content">
                      <h4>Referans Seviye</h4>
                      <p className="kpi-value">
                        {anomalyData.anomaly.baseline_value != null
                          ? `${Number(anomalyData.anomaly.baseline_value).toLocaleString("tr-TR", {
                              maximumFractionDigits: 2,
                            })} ₺`
                          : "Veri yetersiz"}
                      </p>
                    </div>
                  </div>

                  <div className="kpi-card">
                    <div className="kpi-icon">🧾</div>
                    <div className="kpi-content">
                      <h4>Son Ay Gideri</h4>
                      <p className="kpi-value expense">
                        {Number(anomalyData.anomaly.latest_expense || 0).toLocaleString("tr-TR", {
                          maximumFractionDigits: 2,
                        })} ₺
                      </p>
                    </div>
                  </div>

                  <div className="kpi-card">
                    <div className="kpi-icon">🎯</div>
                    <div className="kpi-content">
                      <h4>Anomali Esigi</h4>
                      <p className="kpi-value">
                        {anomalyData.anomaly.threshold_value != null
                          ? `${Number(anomalyData.anomaly.threshold_value).toLocaleString("tr-TR", {
                              maximumFractionDigits: 2,
                            })} ₺`
                          : "Veri yetersiz"}
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {anomalyData.anomaly?.status === "ok" && (
                <div style={{ marginTop: 12 }}>
                  <p className="kpi-label" style={{ marginBottom: 6 }}>
                    Yontem: {anomalyData.anomaly.method_used === "median_mad" ? "Medyan+MAD" : "Ortalama"}
                  </p>
                  <p className="kpi-label" style={{ marginBottom: 6 }}>
                    Esik asim yuzdesi: {anomalyData.anomaly.exceed_percent != null && anomalyData.anomaly.exceed_percent > 0
                      ? `${anomalyData.anomaly.exceed_percent.toFixed(1)}%`
                      : "-"}
                  </p>
                </div>
              )}

              {anomalyData.anomaly?.status === "ok" && anomalyChartData.length > 0 && (
                <div style={{ marginTop: 14 }}>
                  <ResponsiveContainer width="100%" height={240}>
                    <BarChart data={anomalyChartData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="month" />
                      <YAxis tickFormatter={currencyTick} width={70} />
                      <Tooltip
                        formatter={(value) =>
                          Number(value).toLocaleString("tr-TR", {
                            maximumFractionDigits: 2,
                          }) + " ₺"
                        }
                      />
                      <Legend />
                      <ReferenceLine y={Number(anomalyData.anomaly.baseline_value || 0)} stroke="#2563eb" strokeDasharray="5 5" label="Referans" />
                      <ReferenceLine y={Number(anomalyData.anomaly.threshold_value || 0)} stroke="#dc2626" strokeDasharray="4 4" label="Esik" />
                      <Bar dataKey="expense" fill="#f97316" name="Aylik Gider" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              )}

              {Array.isArray(anomalyData.drivers) && anomalyData.drivers.length > 0 && (
                <div style={{ marginTop: 14 }}>
                  <h4 style={{ marginBottom: 8 }}>Artisa en cok etki eden saticilar</h4>
                  <div className="table-wrapper">
                    <table className="invoice-table">
                      <thead>
                        <tr>
                          <th>Satici</th>
                          <th>Bu Ay</th>
                          <th>Gecmis Ort.</th>
                          <th>Fark</th>
                          <th>Pay</th>
                        </tr>
                      </thead>
                      <tbody>
                        {anomalyData.drivers.map((item, idx) => (
                          <tr key={`${item.name}-${idx}`}>
                            <td>{item.name}</td>
                            <td>{Number(item.latest_amount || 0).toLocaleString("tr-TR", { maximumFractionDigits: 2 })} ₺</td>
                            <td>{Number(item.historical_avg || 0).toLocaleString("tr-TR", { maximumFractionDigits: 2 })} ₺</td>
                            <td className={item.delta_amount >= 0 ? "income" : "expense"}>
                              {item.delta_amount >= 0 ? "+" : ""}
                              {Number(item.delta_amount || 0).toLocaleString("tr-TR", { maximumFractionDigits: 2 })} ₺
                            </td>
                            <td>%{Number(item.share_of_latest || 0).toFixed(1)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {Array.isArray(anomalyData.anomaly?.recommendations) && anomalyData.anomaly.recommendations.length > 0 && (
                <div style={{ marginTop: 12 }}>
                  <h4 style={{ marginBottom: 8 }}>Oneri</h4>
                  {anomalyData.anomaly.recommendations.map((item, idx) => (
                    <p key={idx} className="kpi-label" style={{ marginBottom: 6 }}>
                      {idx + 1}. {item}
                    </p>
                  ))}
                </div>
              )}
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

            {/* TAHMİN GRAFİKLERİ */}
            {forecastData && forecastChartData.length > 0 && (
              <>
                <section className="card">
                  <h3>📈 Geçmiş Trend</h3>
                  <ResponsiveContainer width="100%" height={400}>
                      <LineChart data={historyOnlyChartData}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="month" interval="preserveStartEnd" minTickGap={16} />
                        <YAxis tickFormatter={currencyTick} width={70} domain={historyDomain} />
                        <Tooltip
                          formatter={(value) => {
                            if (value == null) return "-";
                            return (
                              Number(value).toLocaleString("tr-TR", {
                                maximumFractionDigits: 2,
                              }) + " ₺"
                            );
                          }}
                        />
                        <Legend />
                        <Line
                          type="monotone"
                          dataKey="income_actual"
                          stroke="#10b981"
                          strokeWidth={2.5}
                          dot={false}
                          activeDot={{ r: 4 }}
                          name="Gelir"
                        />
                        <Line
                          type="monotone"
                          dataKey="expense_actual"
                          stroke="#ef4444"
                          strokeWidth={2.5}
                          dot={false}
                          activeDot={{ r: 4 }}
                          name="Gider"
                        />
                      </LineChart>
                    </ResponsiveContainer>
                </section>

                <section className="card">
                  <h4>Gelecek Tahmini</h4>
                  <ResponsiveContainer width="100%" height={400}>
                      <AreaChart data={forecastOnlyChartData}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="month" interval="preserveStartEnd" minTickGap={16} />
                        <YAxis tickFormatter={currencyTick} width={70} domain={forecastDomain} />
                        <Tooltip
                          formatter={(value) => {
                            if (value == null) return "-";
                            return (
                              Number(value).toLocaleString("tr-TR", {
                                maximumFractionDigits: 2,
                              }) + " ₺"
                            );
                          }}
                        />
                        <Legend />

                        <Area
                          type="monotone"
                          dataKey="income_upper"
                          stroke="none"
                          fill="rgba(16, 185, 129, 0.12)"
                          legendType="none"
                          name=""
                        />
                        <Area
                          type="monotone"
                          dataKey="income_lower"
                          stroke="none"
                          fill="#fff"
                          stackId="income-band"
                          legendType="none"
                          name=""
                        />

                        <Area
                          type="monotone"
                          dataKey="expense_upper"
                          stroke="none"
                          fill="rgba(239, 68, 68, 0.12)"
                          legendType="none"
                          name=""
                        />
                        <Area
                          type="monotone"
                          dataKey="expense_lower"
                          stroke="none"
                          fill="#fff"
                          stackId="expense-band"
                          legendType="none"
                          name=""
                        />

                        <Line
                          type="monotone"
                          dataKey="income_forecast"
                          stroke="#10b981"
                          strokeWidth={2.5}
                          strokeDasharray="6 4"
                          dot={{ r: 2 }}
                          activeDot={{ r: 5 }}
                          name="Gelir Tahmin"
                        />
                        <Line
                          type="monotone"
                          dataKey="expense_forecast"
                          stroke="#ef4444"
                          strokeWidth={2.5}
                          strokeDasharray="6 4"
                          dot={{ r: 2 }}
                          activeDot={{ r: 5 }}
                          name="Gider Tahmin"
                        />
                      </AreaChart>
                    </ResponsiveContainer>
                </section>
              </>
            )}
          </div>

          {/* GELECEK AY ÖZETİ */}
          {nextMonthForecast && (
            <section className="card">
              <h3>🗓️ Gelecek Ay Tahmini</h3>
              <div className="forecast-next-grid">
                <div className="summary-item income-item">
                  <div className="summary-icon">💰</div>
                  <div className="summary-text">
                    <span className="summary-label">Tahmini Gelir</span>
                    <span className="summary-amount">
                      {nextMonthForecast.income.toLocaleString("tr-TR", {
                        maximumFractionDigits: 2,
                      })} ₺
                    </span>
                  </div>
                </div>

                <div className="summary-item expense-item">
                  <div className="summary-icon">💸</div>
                  <div className="summary-text">
                    <span className="summary-label">Tahmini Gider</span>
                    <span className="summary-amount">
                      {nextMonthForecast.expense.toLocaleString("tr-TR", {
                        maximumFractionDigits: 2,
                      })} ₺
                    </span>
                  </div>
                </div>

                <div className="summary-item net-item">
                  <div className="summary-icon">📊</div>
                  <div className="summary-text">
                    <span className="summary-label">Tahmini Net</span>
                    <span
                      className={`summary-amount ${
                        nextMonthForecast.net >= 0 ? "positive" : "negative"
                      }`}
                    >
                      {nextMonthForecast.net.toLocaleString("tr-TR", {
                        maximumFractionDigits: 2,
                      })} ₺
                    </span>
                  </div>
                </div>
              </div>
            </section>
          )}

          {forecastQuality && (
            <section className="card">
              <h3>🧪 Tahmin Kalite Ozeti</h3>
              <div className="forecast-quality-grid">
                <div className="kpi-card">
                  <div className="kpi-icon">🎯</div>
                  <div className="kpi-content">
                    <h4>Guven Seviyesi</h4>
                    <p className="kpi-value">
                      {confidenceLabels[forecastQuality.confidence_level] || "Yetersiz Veri"}
                    </p>
                    <span className="kpi-label">
                      Holdout: {forecastQuality.holdout_months || 0} ay
                    </span>
                  </div>
                </div>

                <div className="kpi-card">
                  <div className="kpi-icon">📉</div>
                  <div className="kpi-content">
                    <h4>Gelir WAPE</h4>
                    <p className="kpi-value">
                      {forecastQuality.income_wape != null
                        ? `${forecastQuality.income_wape.toFixed(1)}%`
                        : "-"}
                    </p>
                    <span className="kpi-label">
                      MAPE: {forecastQuality.income_mape != null
                        ? `${forecastQuality.income_mape.toFixed(1)}%`
                        : "-"}
                    </span>
                  </div>
                </div>

                <div className="kpi-card">
                  <div className="kpi-icon">📈</div>
                  <div className="kpi-content">
                    <h4>Gider WAPE</h4>
                    <p className="kpi-value">
                      {forecastQuality.expense_wape != null
                        ? `${forecastQuality.expense_wape.toFixed(1)}%`
                        : "-"}
                    </p>
                    <span className="kpi-label">
                      MAPE: {forecastQuality.expense_mape != null
                        ? `${forecastQuality.expense_mape.toFixed(1)}%`
                        : "-"}
                    </span>
                  </div>
                </div>
              </div>
            </section>
          )}

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
