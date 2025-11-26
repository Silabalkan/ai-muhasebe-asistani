import axios from "axios";

const API = axios.create({
    baseURL: "http://127.0.0.1:8000",
});

export const uploadInvoice = (file) => {
    const formData = new FormData();
    formData.append("file", file);
    return API.post("/invoices/upload-analyze", formData, {
        headers: { "Content-Type": "multipart/form-data" },
    });
};
