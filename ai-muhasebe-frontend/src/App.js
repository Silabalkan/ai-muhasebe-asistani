import React, { useState } from "react";
import "./App.css";

function App() {
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleUpload = async () => {
    if (!file) {
      alert("Lütfen bir fiş seçin");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    try {
      setLoading(true);
      const response = await fetch(
        "http://127.0.0.1:8000/invoices/upload-analyze",
        {
          method: "POST",
          body: formData,
        }
      );

      const data = await response.json();
      console.log("Backend yanıtı:", data);
      setResult(data);
    } catch (err) {
      console.error(err);
      alert("Bir hata oluştu");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-root">
      <header className="app-header">
        <span className="app-icon">🧾</span>
        <h1>AI Muhasebe Asistanı</h1>
      </header>

      <main className="app-main">
        {/* Yükleme kartı */}
        <section className="card upload-card">
          <h2>Fiş Yükle</h2>
          <p className="upload-desc">
            Fiş veya fatura görselini yükleyin, sistem otomatik olarak tutar ve
            temel bilgileri çıkarsın.
          </p>

          <div className="upload-row">
            <input
              type="file"
              onChange={(e) => setFile(e.target.files[0])}
            />
            <button onClick={handleUpload} disabled={loading}>
              {loading ? "Analiz ediliyor..." : "Analiz Et"}
            </button>
          </div>

          {file && (
            <p className="file-name">
              Seçilen dosya: <span>{file.name}</span>
            </p>
          )}
        </section>

        {/* Sonuç kartı */}
        <section className="card result-card">
          <div className="result-header">
        
            <h2>Analiz Sonuçları</h2>
          </div>

          {!result && (
            <p className="empty-text">
              Henüz bir fiş yüklenmedi. Üstten bir fiş seçip{" "}
              <strong>Analiz Et</strong> butonuna basın.
            </p>
          )}

          {result && (
            <div className="result-grid">
              <div className="result-row">
                <span className="label">Toplam Tutar:</span>
                <span className="value">
                  {result.total_amount} <span className="currency">₺</span>
                </span>
              </div>

              <div className="result-row">
                <span className="label">Ödeme Tipi:</span>
                <span className="value">
                  {result.payment_type || "-"}
                </span>
              </div>

              <div className="result-row">
                <span className="label">KDV Oranı:</span>
                <span className="value">
                  {result.kdv_rate != null ? `%${result.kdv_rate}` : "-"}
                </span>
              </div>

              <div className="result-row">
                <span className="label">KDV Tutarı:</span>
                <span className="value">
                  {result.kdv_amount != null ? `${result.kdv_amount} ₺` : "-"}
                </span>
              </div>

              <div className="result-row">
                <span className="label">Kategori:</span>
                <span className="value">
                  {result.category || "-"}
                </span>
              </div>

              <div className="result-row">
                <span className="label">Tarih:</span>
                <span className="value">
                  {result.invoice_date || "-"}
                </span>
              </div>

              <div className="result-row">
                <span className="label">Satıcı / Barkod:</span>
                <span className="value">
                  {result.vendor || "-"}
                </span>
              </div>

              <div className="result-row">
                <span className="label">Dosya Adı:</span>
                <span className="value">
                  {result.filename}
                </span>
              </div>

              <div className="result-row">
                <span className="label">Kayıt Zamanı:</span>
                <span className="value small">
                  {new Date(result.created_at).toLocaleString("tr-TR")}
                </span>
              </div>
            </div>
          )}
        </section>
      </main>
    </div>
  );
}

export default App;
