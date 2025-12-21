import axios from "axios";

const API = axios.create({
  baseURL: "http://127.0.0.1:8000",
});

export const uploadInvoice = (file) => {
  const formData = new FormData();
  formData.append("file", file);

  return API.post("/invoices/upload-analyze", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });
};

// GELİR OLARAK FİŞ YÜKLE (AddIncomePage'de kullanılır)
export const uploadIncomeInvoice = (file) => {
  const formData = new FormData();
  formData.append("file", file);

  return API.post("/invoices/upload-analyze-income", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });
};

// TÜM FİŞLERİ GETİR
export const getInvoices = () => {
  return API.get("/invoices");
};

// RAPOR ÖZETİ (opsiyonel filtreli)
export const getReportSummary = (params) => {
  return API.get("/reports/summary", { params });
};

// HIZLI ÖZET (ANA SAYFA İÇİN)
export const getQuickSummary = () => {
  return API.get("/reports/quick-summary");
};

// GELİŞMİŞ RAPOR (KPI & ANALİZ)
export const getAdvancedReport = (params) => {
  return API.get("/reports/advanced", { params });
};

// AYLIK TREND VERİSİ
export const getTrendReport = (params) => {
  return API.get("/reports/trend", { params });
};

// KATEGORİ DAĞILIM
export const getCategoryDistribution = (params) => {
  return API.get("/reports/category-distribution", { params });
};

export const addManualIncome = (payload) => {
  return API.post("/invoices/manual-income", payload);
};
