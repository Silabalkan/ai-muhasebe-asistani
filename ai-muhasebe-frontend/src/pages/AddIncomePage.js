import React, { useState } from "react";
import { addManualIncome, uploadIncomeInvoice } from "../api";

export default function AddIncomePage() {
  // Tab Seçimi
  const [activeTab, setActiveTab] = useState("upload"); // "upload" | "manual"

  // FİŞ YÜKLEME
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [uploadLoading, setUploadLoading] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState(false);
  const [uploadResult, setUploadResult] = useState(null);

  // MANUEL GELİR
  const [amount, setAmount] = useState("");
  const [date, setDate] = useState("");
  const [description, setDescription] = useState("");
  const [manualLoading, setManualLoading] = useState(false);
  const [manualSuccess, setManualSuccess] = useState(false);

  // FİŞ YÜKLEME HANDLER
  const handleUpload = async () => {
    if (!file) {
      alert("Lütfen bir fiş seçin");
      return;
    }

    try {
      setUploadLoading(true);
      const response = await uploadIncomeInvoice(file);
      setUploadResult(response.data);
      setUploadSuccess(true);
      setTimeout(() => setUploadSuccess(false), 3000);

      // Formu sıfırla
      setFile(null);
      setPreview(null);
    } catch (err) {
      console.error(err);
      alert("Fiş yüklenirken bir hata oluştu");
    } finally {
      setUploadLoading(false);
    }
  };

  // MANUEL GELİR HANDLER
  const handleManualSubmit = async () => {
    if (!amount || !date) {
      alert("⚠️ Tutar ve tarih zorunludur");
      return;
    }

    const payload = {
      amount: Number(amount),
      date: date,
      description: description
    };

    try {
      setManualLoading(true);
      await addManualIncome(payload);
      
      setManualSuccess(true);
      setTimeout(() => setManualSuccess(false), 3000);

      setAmount("");
      setDate("");
      setDescription("");
    } catch (err) {
      console.error(err);
      alert("❌ Gelir eklenirken hata oluştu");
    } finally {
      setManualLoading(false);
    }
  };

  return (
    <>
      {/* BİLGİLENDİRME */}
      <section className="card info-card">
        <h3>ℹ️ Gelirinizi Kaydedin</h3>
        <p className="info-text">
          Tüm gelir kaynaklarınızı takip etmek önemlidir. Fiş veya fatura yükleyerek veya manuel olarak gelir ekleyerek 
          işletmenizin finansal durumunu güncel tutabilirsiniz. Gelir ve gider dengesini rapor sayfasından takip edebilirsiniz.
        </p>
      </section>

      {/* TAB SEÇİMİ */}
      <section className="card">
        <div className="tab-buttons">
          <button
            className={`tab-btn ${activeTab === "upload" ? "active" : ""}`}
            onClick={() => setActiveTab("upload")}
          >
            📸 Fiş Yükle
          </button>
          <button
            className={`tab-btn ${activeTab === "manual" ? "active" : ""}`}
            onClick={() => setActiveTab("manual")}
          >
            ✍️ Manuel Ekle
          </button>
        </div>
      </section>

      {/* FİŞ YÜKLEME TAB */}
      {activeTab === "upload" && (
        <section className="card upload-card">
          <h2>📸 Fiş Yükleyerek Gelir Ekle</h2>
          <p className="upload-desc">
            Fiş veya fatura görselini yükleyin. AI sistem otomatik olarak gelir bilgilerini çıkarsın ve kaydetsın.
          </p>

          {uploadSuccess && (
            <p className="success-text">✅ Gelir başarıyla kaydedildi!</p>
          )}

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
            <button onClick={handleUpload} disabled={uploadLoading}>
              {uploadLoading ? "⏳ Analiz ediliyor..." : "🚀 Analiz Et"}
            </button>
          </div>

          {file && (
            <p className="file-name">
              ✓ Seçilen dosya: <span>{file.name}</span>
            </p>
          )}

          {/* ANALİZ SONUÇLARI */}
          {uploadResult && (
            <section className="result-card">
              <h3>✨ Analiz Sonuçları</h3>

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
                    <span className="value highlight">{uploadResult.total_amount} ₺</span>
                  </div>

                  <div className="result-row">
                    <span className="label">📅 Tarih:</span>
                    <span className="value">{uploadResult.invoice_date || "-"}</span>
                  </div>

                  <div className="result-row">
                    <span className="label">🧾 Satıcı:</span>
                    <span className="value">{uploadResult.vendor || "-"}</span>
                  </div>

                  <div className="result-row">
                    <span className="label">💳 Ödeme Tipi:</span>
                    <span className="value">{uploadResult.payment_type || "-"}</span>
                  </div>

                  <div className="result-row">
                    <span className="label">📊 KDV Oranı:</span>
                    <span className="value">
                      {uploadResult.kdv_rate != null ? `%${uploadResult.kdv_rate}` : "-"}
                    </span>
                  </div>

                  <div className="result-row">
                    <span className="label">📈 KDV Tutarı:</span>
                    <span className="value">
                      {uploadResult.kdv_amount != null ? `${uploadResult.kdv_amount} ₺` : "-"}
                    </span>
                  </div>

                  <div className="result-row">
                    <span className="label">⏱️ Kayıt Zamanı:</span>
                    <span className="value small">
                      {new Date(uploadResult.created_at).toLocaleString("tr-TR")}
                    </span>
                  </div>
                </div>
              </div>
            </section>
          )}
        </section>
      )}

      {/* MANUEL GELİR EKLE TAB */}
      {activeTab === "manual" && (
        <section className="card">
          <h2>✍️ Manuel Gelir Ekle</h2>

          {manualSuccess && (
            <p className="success-text">✅ Gelir başarıyla kaydedildi!</p>
          )}

          <div className="form-group">
            <label>💰 Tutar (₺)</label>
            <input
              type="number"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              placeholder="Örn: 500"
              min="0"
              step="0.01"
            />
          </div>

          <div className="form-group">
            <label>📅 Tarih</label>
            <input
              type="date"
              value={date}
              onChange={(e) => setDate(e.target.value)}
            />
          </div>

          <div className="form-group">
            <label>📝 Açıklama</label>
            <input
              type="text"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Örn: Danışmanlık hizmet bedeli"
            />
          </div>

          <button onClick={handleManualSubmit} disabled={manualLoading}>
            {manualLoading ? "⏳ Kaydediliyor..." : "💾 Gelir Ekle"}
          </button>
        </section>
      )}
    </>
  );
}
