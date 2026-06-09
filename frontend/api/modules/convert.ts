/**
 * Conversion API: MD → DOCX, preview, format conversion, stats.
 *
 * @module api/modules/convert
 */
import api, { postJson, postFormBlob } from "../index";

export interface MdConvertResponse {
  success: boolean;
  filename: string;
  title: string;
  download_id: string;
}

export interface MdPreviewResponse {
  html: string;
}

export interface StatsResponse {
  total_conversions: number;
}

export const convertApi = {
  /** Convert Markdown content to DOCX. Query ?format=official|plain. */
  convert: (content: string, format: "official" | "plain" = "official") =>
    postJson<MdConvertResponse>(`/api/convert?format=${format}`, { content }),

  /** Render Markdown to HTML for live preview. */
  preview: (content: string) =>
    postJson<MdPreviewResponse>("/api/preview", { content }),

  /** Reformat an uploaded DOCX per GB/T 9704-2012. */
  formatDocx: (file: File) => {
    const fd = new FormData();
    fd.append("file", file);
    return postFormBlob("/api/convert/doc2md", fd);
  },


  /** Get total conversion count. */
  stats: () => api.get<StatsResponse>("/api/stats").then((r) => r.data),
};
