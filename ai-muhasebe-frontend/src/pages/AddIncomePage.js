import React, { useState } from "react";
import { addManualIncome } from "../api";

export default function AddIncomePage() {
  const [amount, setAmount] = useState("");
  const [date, setDate] = useState("");
  const [description, setDescription] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    if (!amount || !date) {
      alert("Tutar ve tarih zorunludur");
      return;
    }

    const payload = {
      amount: Number(amount),   // ✅ backend: amount
      date: date,               // ✅ backend: date (YYYY-MM-DD)
      description: description // ✅ backend: description
    };

    console.log("Gönderilen veri:", payload);

    try {
      setLoading(true);
      await addManualIncome(payload);
      alert("Gelir başarıyla eklendi");

      setAmount("");
      setDate("");
      setDescription("");
    } catch (err) {
      console.error(err);
      alert("Gelir eklenirken hata oluştu");
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="card">
      <h2>Gelir Ekle</h2>

      <div className="form-group">
        <label>Tutar (₺)</label>
        <input
          type="number"
          value={amount}
          onChange={(e) => setAmount(e.target.value)}
          placeholder="Örn: 500"
        />
      </div>

      <div className="form-group">
        <label>Tarih</label>
        <input
          type="date"
          value={date}
          onChange={(e) => setDate(e.target.value)}
        />
      </div>

      <div className="form-group">
        <label>Açıklama</label>
        <input
          type="text"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Örn: Nakit satış"
        />
      </div>

      <button onClick={handleSubmit} disabled={loading}>
        {loading ? "Kaydediliyor..." : "Gelir Ekle"}
      </button>
    </section>
  );
}
