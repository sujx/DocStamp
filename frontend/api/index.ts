/**
 * Shared Axios instance and response helpers for docStamp API layer.
 *
 * Replaces ad-hoc axios.post() calls scattered across components.
 * All API modules import from here for consistent base URL, error handling,
 * and response-type typing.
 *
 * @module api/index
 */
import axios from "axios";

const BASE_URL = import.meta.dev ? "http://localhost:5000" : "";

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 120_000, // 2 min — document processing can take time
  headers: { Accept: "application/json" },
});

export default api;

/**
 * Download a file blob from a GET endpoint.
 * Used for /api/v1/download/:id and print-split batch endpoints.
 */
export async function downloadBlob(url: string): Promise<Blob> {
  const resp = await api.get(url, { responseType: "blob" });
  return resp.data;
}

/**
 * POST multipart form data and receive a blob response.
 * All file-processing endpoints return the processed document as a blob.
 */
export async function postFormBlob(url: string, formData: FormData): Promise<Blob> {
  const resp = await api.post(url, formData, { responseType: "blob" });
  return resp.data;
}

/**
 * POST multipart form data and receive JSON.
 */
export async function postFormJson<T = unknown>(url: string, formData: FormData): Promise<T> {
  const resp = await api.post(url, formData);
  return resp.data as T;
}

/**
 * POST JSON body and receive JSON.
 */
export async function postJson<T = unknown>(url: string, data: unknown): Promise<T> {
  const resp = await api.post(url, data);
  return resp.data as T;
}
