import React, { useState } from "react";
import { uploadInvoice } from "./api";

function App() {
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);

  const handleUpload = async () => {
    if (!file) return;

    try {
      const response = await uploadInvoice(file);
      console.log("Backend yanıtı:", response.data);
      setResult(response.data);   // 🔥 ÖNEMLİ KISIM
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div style={{ padding: 40 }}>
      <h2>AI Muhasebe Asistanı</h2>

      <input type="file" onChange={e => setFile(e.target.files[0])} />
      <button onClick={handleUpload}>Analiz Et</button>

      {result && (
        <div style={{ marginTop: 20 }}>
          <h3>Sonuç:</h3>
          <p><b>Toplam Tutar:</b> {result.total_amount} ₺</p>
          <p><b>Ödeme Tipi:</b> {result.payment_type}</p>
          <p><b>KDV Oranı:</b> {result.kdv_rate}</p>
          <p><b>Kategori:</b> {result.category}</p>
          <p><b>Satıcı:</b> {result.filename}</p>
        </div>
      )}
    </div>
  );
}

export default App;
