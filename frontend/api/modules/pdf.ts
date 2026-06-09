/**
 * PDF operations API: merge, compress, edit, convert, split.
 *
 * @module api/modules/pdf
 */
import api, { postFormBlob, postFormJson, downloadBlob } from "../index";

export interface PdfPageInfo {
  page_no: number;
  thumb?: string;
  width: number;
  height: number;
}

export interface PdfInfoResponse {
  total_pages: number;
  pages: PdfPageInfo[];
}

export interface PdfDeleteResponse {
  deleted_pages: number;
  total_pages: number;
}

export interface PdfInsertResponse {
  inserted_pages: number;
  total_pages: number;
}

export interface PdfReorderResponse {
  total_pages: number;
}

export interface PdfToTextResponse {
  text: string;
  pages: number;
}

export const pdfApi = {
  /** Get page count, dimensions, and thumbnails for a PDF. */
  getInfo: (file: File): Promise<PdfInfoResponse> => {
    const fd = new FormData();
    fd.append("file", file);
    return postFormJson<PdfInfoResponse>("/api/v1/pdf-editor/info", fd);
  },

  /** Delete specified pages from a PDF. */
  deletePages: (file: File, pages: number[]) => {
    const fd = new FormData();
    fd.append("file", file);
    fd.append("pages", JSON.stringify(pages));
    return postFormBlob("/api/v1/pdf-editor/delete", fd);
  },

  /** Insert pages from a source PDF into the target at a given position. */
  insertPages: (file: File, insertFile: File, atPosition: number, insertPages?: number[]) => {
    const fd = new FormData();
    fd.append("file", file);
    fd.append("insert_file", insertFile);
    fd.append("at_position", String(atPosition));
    if (insertPages && insertPages.length > 0) {
      fd.append("insert_pages", JSON.stringify(insertPages));
    }
    return postFormBlob("/api/v1/pdf-editor/insert", fd);
  },

  /** Reorder pages of a PDF. */
  reorderPages: (file: File, newOrder: number[]) => {
    const fd = new FormData();
    fd.append("file", file);
    fd.append("order", JSON.stringify(newOrder));
    return postFormBlob("/api/v1/pdf-editor/reorder", fd);
  },

  /** Merge multiple images into a PDF. */
  img2pdf: (files: File[], pageSize: string, order?: number[], outputName?: string) => {
    const fd = new FormData();
    files.forEach((f) => fd.append("images", f));
    fd.append("page_size", pageSize);
    if (order) fd.append("order", JSON.stringify(order));
    if (outputName) fd.append("filename", outputName);
    return postFormBlob("/api/v1/img2pdf", fd);
  },

  /** Convert PDF pages to images. */
  pdf2img: (file: File, format: "png" | "jpeg" = "png", dpi = 200, pages?: number[]) => {
    const fd = new FormData();
    fd.append("file", file);
    fd.append("format", format);
    fd.append("dpi", String(dpi));
    if (pages) fd.append("pages", JSON.stringify(pages));
    return postFormBlob("/api/v1/pdf2img", fd);
  },

  /** Merge multiple PDF files into one. */
  merge: (files: File[]) => {
    const fd = new FormData();
    files.forEach((f) => fd.append("files", f));
    return postFormBlob("/api/v1/pdf-merge", fd);
  },

  /** Compress a PDF. */
  compress: (file: File, level: "light" | "medium" | "heavy") => {
    const fd = new FormData();
    fd.append("file", file);
    fd.append("level", level);
    return postFormBlob("/api/v1/pdf-compress", fd);
  },

  /** Extract text from a PDF. */
  toText: (file: File) => {
    const fd = new FormData();
    fd.append("file", file);
    return postFormJson<PdfToTextResponse>("/api/v1/pdf-to-text", fd);
  },
};

export const printApi = {
  /** Split a PDF into print batches. */
  split: (file: File, batchSize: number, intervalSeconds = 0) => {
    const fd = new FormData();
    fd.append("file", file);
    fd.append("batch_size", String(batchSize));
    fd.append("interval", String(intervalSeconds));
    return postFormJson<{ task_id: string; batches: number }>("/api/v1/print-split", fd);
  },

  /** Download a specific print batch. */
  downloadBatch: (taskId: string, batchNo: number) =>
    downloadBlob(`/api/v1/print-split/${encodeURIComponent(taskId)}/batch/${batchNo}`),
};
