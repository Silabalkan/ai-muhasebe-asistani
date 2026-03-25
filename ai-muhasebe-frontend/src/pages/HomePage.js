import React, { useState, useEffect } from "react";
import { uploadInvoice, getQuickSummary } from "../api";

export default function HomePage() {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [summary, setSummary] = useState(null);
  const [summaryLoading, setSummaryLoading] = useState(true);

  useEffect(() => {
    loadSummary();
  }, []);

  const loadSummary = async () => {
    try {
      setSummaryLoading(true);
      const response = await getQuickSummary();
      setSummary(response.data);
    } catch (err) {
      console.error(err);
    } finally {
      setSummaryLoading(false);
    }
  };

  const handleUpload = async () => {
    if (!file) {
      alert("Lütfen bir fiş seçin");
      return;
    }

    try {
      setLoading(true);
      const response = await uploadInvoice(file);
      setResult(response.data);
      loadSummary(); // Özeti güncelle
    } catch (err) {
      console.error(err);
      alert("Bir hata oluştu");
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      {/* BİLGİLENDİRME */}
      <section className="card info-card">
        <h3>ℹ️ Giden Satışlarınızı Kaydedin</h3>
        <p className="info-text">
          İşletmenizin giden satışlarını ve harcamalarını takip etmek için lütfen fiş veya faturalarınızı yükleyiniz. 
          AI sistem otomatik olarak muhasebe bilgilerinizi çıkarır ve kategorize eder. 
          Bu sayede finansal durumunuzu gerçek zamanlı olarak izleyebilirsiniz.
        </p>
      </section>

      {/* FİŞ YÜKLEME */}
      <section className="card upload-card">
        <h2>📸 Fiş Analiz Et</h2>
        <p className="upload-desc">
          Fiş veya fatura görselini yükleyin. AI sistem otomatik olarak muhasebe bilgilerini çıkarsın ve kategorize etsin.
        </p>

        <div className="upload-row">
          <input
            type="file"
            accept="image/*"
            onChange={(e) => {
              const selected = e.target.files?.[0];
              if (!selected) {
                setFile(null);
                setPreview(null);
                return;
              }
              setFile(selected);
              setPreview(URL.createObjectURL(selected));
            }}
          />
          <button onClick={handleUpload} disabled={loading}>
            {loading ? "⏳ Analiz ediliyor..." : "🚀 Analiz Et"}
          </button>
        </div>

        {file && (
          <p className="file-name">
            ✓ Seçilen dosya: <span>{file.name}</span>
          </p>
        )}
      </section>

      {/* ANALİZ SONUÇLARI */}
      {(loading || result) && (
        <section className="card result-card">
          <h2>✨ Analiz Sonuçları</h2>

          {loading && (
            <p className="empty-text">⏳ Fiş analiz ediliyor, lütfen bekleyin...</p>
          )}

          {result && (
            <>
              <p className="success-text">✅ Fiş başarıyla analiz edildi ve kaydedildi</p>

              <div className="result-layout">
                {/* SOL: FİŞ GÖRSELİ */}
                {preview && (
                  <div className="preview-wrapper">
                    <img
                      src={preview}
                      alt="Fiş Önizleme"
                      className="preview-image"
                    />
                  </div>
                )}

                {/* SAĞ: ANALİZ BİLGİLERİ */}
                <div className="result-grid">
                  <div className="result-row">
                    <span className="label">💰 Tutar:</span>
                    <span className="value highlight">{result.total_amount} ₺</span>
                  </div>

                  <div className="result-row">
                    <span className="label">🏪 Kategorisi:</span>
                    <span className="value">{result.category || "-"}</span>
                  </div>

                  <div className="result-row">
                    <span className="label">💳 Ödeme Tipi:</span>
                    <span className="value">{result.payment_type || "-"}</span>
                  </div>

                  <div className="result-row">
                    <span className="label">📅 Tarih:</span>
                    <span className="value">{result.invoice_date || "-"}</span>
                  </div>

                  <div className="result-row">
                    <span className="label">🧾 Satıcı:</span>
                    <span className="value">{result.vendor || "-"}</span>
                  </div>

                  <div className="result-row">
                    <span className="label">📊 KDV Oranı:</span>
                    <span className="value">
                      {result.kdv_rate != null ? `%${result.kdv_rate}` : "-"}
                    </span>
                  </div>

                  <div className="result-row">
                    <span className="label">📈 KDV Tutarı:</span>
                    <span className="value">
                      {result.kdv_amount != null ? `${result.kdv_amount} ₺` : "-"}
                    </span>
                  </div>

                  <div className="result-row">
                    <span className="label">📝 Dosya:</span>
                    <span className="value small">{result.filename}</span>
                  </div>

                  <div className="result-row">
                    <span className="label">⏱️ Kayıt Zamanı:</span>
                    <span className="value small">
                      {new Date(result.created_at).toLocaleString("tr-TR")}
                    </span>
                  </div>
                </div>
              </div>
            </>
          )}
        </section>
      )}

      {/* ÖZET KARTLARı */}
      {!summaryLoading && summary && (
        <>
          {/* BUGÜNÜN ÖZETİ */}
          <section className="card">
            <h3>📅 Bugün</h3>
            <div className="quick-summary-grid">
              <div className="summary-item income-item">
                <div className="summary-icon">💰</div>
                <div className="summary-text">
                  <span className="summary-label">Gelir</span>
                  <span className="summary-amount">
                    {summary.today.income.toLocaleString("tr-TR", {
                      maximumFractionDigits: 2,
                    })} ₺
                  </span>
                </div>
              </div>

              <div className="summary-item expense-item">
                <div className="summary-icon">💸</div>
                <div className="summary-text">
                  <span className="summary-label">Gider</span>
                  <span className="summary-amount">
                    {summary.today.expense.toLocaleString("tr-TR", {
                      maximumFractionDigits: 2,
                    })} ₺
                  </span>
                </div>
              </div>

              <div className="summary-item net-item">
                <div className="summary-icon">📊</div>
                <div className="summary-text">
                  <span className="summary-label">Net</span>
                  <span
                    className={`summary-amount ${
                      summary.today.net >= 0 ? "positive" : "negative"
                    }`}
                  >
                    {summary.today.net.toLocaleString("tr-TR", {
                      maximumFractionDigits: 2,
                    })} ₺
                  </span>
                </div>
              </div>
            </div>
          </section>

          {/* AYLIK ÖZET */}
          <section className="card">
            <h3>📆 Bu Ay</h3>
            <div className="quick-summary-grid">
              <div className="summary-item income-item">
                <div className="summary-icon">💰</div>
                <div className="summary-text">
                  <span className="summary-label">Gelir</span>
                  <span className="summary-amount">
                    {summary.month.income.toLocaleString("tr-TR", {
                      maximumFractionDigits: 2,
                    })} ₺
                  </span>
                </div>
              </div>

              <div className="summary-item expense-item">
                <div className="summary-icon">💸</div>
                <div className="summary-text">
                  <span className="summary-label">Gider</span>
                  <span className="summary-amount">
                    {summary.month.expense.toLocaleString("tr-TR", {
                      maximumFractionDigits: 2,
                    })} ₺
                  </span>
                </div>
              </div>

              <div className="summary-item net-item">
                <div className="summary-icon">📊</div>
                <div className="summary-text">
                  <span className="summary-label">Net</span>
                  <span
                    className={`summary-amount ${
                      summary.month.net >= 0 ? "positive" : "negative"
                    }`}
                  >
                    {summary.month.net.toLocaleString("tr-TR", {
                      maximumFractionDigits: 2,
                    })} ₺
                  </span>
                </div>
              </div>
            </div>
          </section>

          {/* SON İŞLEMLER */}
          {summary.recent && summary.recent.length > 0 && (
            <section className="card">
              <h3>⚡ Son İşlemler</h3>
              <div className="recent-transactions">
                {summary.recent.map((transaction, idx) => (
                  <div key={idx} className="transaction-item">
                    <div className="transaction-info">
                      <span className="transaction-vendor">
                        {transaction.vendor || "Bilinmiyor"}
                      </span>
                      <span className="transaction-date">
                        {new Date(transaction.date).toLocaleDateString("tr-TR")}
                      </span>
                    </div>
                    <span
                      className={`transaction-amount ${transaction.category.toLowerCase()}`}
                    >
                      {transaction.category === "Gelir" ? "+" : "-"}
                      {transaction.amount.toLocaleString("tr-TR", {
                        maximumFractionDigits: 2,
                      })} ₺
                    </span>
                  </div>
                ))}
              </div>
            </section>
          )}
        </>
      )}
    </>
  );
}
