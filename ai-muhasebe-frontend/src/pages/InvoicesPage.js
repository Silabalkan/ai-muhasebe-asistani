import React, { useEffect, useState } from "react";
import { getInvoices } from "../api";

export default function InvoicesPage() {
  const [invoices, setInvoices] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadInvoices();
  }, []);

  const loadInvoices = async () => {
    try {
      const response = await getInvoices();
      setInvoices(response.data);
    } catch (err) {
      console.error(err);
      alert("Fişler yüklenirken hata oluştu");
    } finally {
      setLoading(false);
    }
  };

  const getCategoryBadge = (category) => {
    if (category === "Gelir") {
      return "🟢";
    } else if (category === "Gider") {
      return "🔴";
    }
    return "⚪";
  };

  return (
    <section className="card">
      <h2>📋 Kayıtlı Fişler</h2>

      {loading && <p className="empty-text">⏳ Yükleniyor...</p>}

      {!loading && invoices.length === 0 && (
        <p className="empty-text">📭 Henüz kayıtlı fiş bulunmuyor.</p>
      )}

      {!loading && invoices.length > 0 && (
        <div className="table-wrapper">
          <table className="invoice-table">
            <thead>
              <tr>
                <th>📅 Tarih</th>
                <th>🏪 Satıcı</th>
                <th>📌 Kategori</th>
                <th>💳 Ödeme Tipi</th>
                <th>💰 Tutar</th>
              </tr>
            </thead>
            <tbody>
              {invoices.map((inv) => (
                <tr key={inv.id}>
                  <td>{inv.invoice_date || "Tarih yok"}</td>
                  <td>{inv.vendor || "-"}</td>
                  <td>
                    <span>
                      {getCategoryBadge(inv.category)} {inv.category || "-"}
                    </span>
                  </td>
                  <td>{inv.payment_type || "-"}</td>
                  <td className="amount">
                    {inv.total_amount?.toLocaleString("tr-TR") || "0"} ₺
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
