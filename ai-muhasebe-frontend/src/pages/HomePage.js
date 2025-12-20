import React, { useState } from "react";
import { uploadInvoice } from "../api";

export default function HomePage() {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleUpload = async () => {
    if (!file) {
      alert("Lütfen bir fiş seçin");
      return;
    }

    try {
      setLoading(true);
      const response = await uploadInvoice(file);
      setResult(response.data);
    } catch (err) {
      console.error(err);
      alert("Bir hata oluştu");
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
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
              const selected = e.target.files[0];
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
    </>
  );
}
