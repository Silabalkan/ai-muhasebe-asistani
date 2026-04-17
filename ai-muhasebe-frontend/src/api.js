import axios from "axios";

const API = axios.create({
  baseURL: "http://127.0.0.1:8000",
});

// ========================
// TOKEN INTERCEPTOR
// ========================
API.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

API.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error?.response?.status;
    const url = error?.config?.url || "";
    const isAuthEndpoint = url.includes("/auth/login") || url.includes("/auth/register");

    if (status === 401 && !isAuthEndpoint) {
      localStorage.removeItem("token");
      localStorage.removeItem("user");
      localStorage.setItem("sessionExpired", "1");
      if (window.location.pathname !== "/login") {
        window.location.href = "/login";
      }
    }

    return Promise.reject(error);
  }
);

// ========================
// AUTH
// ========================
export const registerUser = (email, username, password) => {
  return API.post("/auth/register", {
    email,
    username,
    password,
  });
};

export const loginUser = (username, password) => {
  return API.post("/auth/login", {
    username,
    password,
  });
};

// ========================
// INVOICES
// ========================
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

export const getForecastReport = (params) => {
  return API.get("/reports/forecast", { params });
};

export const getExpenseAnomaly = (params) => {
  return API.get("/reports/anomaly-expense", { params });
};

export const getFinancialInsight = (params) => {
  return API.get("/reports/ai-insight", { params });
};

export const addManualIncome = (payload) => {
  return API.post("/invoices/manual-income", payload);
};
