/**
 * Office document API: properties, Excel merge, metadata clean, page decoration.
 *
 * @module api/modules/office
 */
import api, { postFormBlob, postFormJson } from "../index";

export interface PropertiesPayload {
  created?: string;
  modified?: string;
  creator?: string;
  last_modified_by?: string;
  unify_time?: boolean;
  unified_time?: string;
}

export interface PropertiesInfoResponse {
  filename: string;
  created: string;
  modified: string;
  creator: string;
  last_modified_by: string;
  title: string;
  pages?: number;
}

export const propertiesApi = {
  /** Read metadata from an Office document. */
  info: (file: File) => {
    const fd = new FormData();
    fd.append("file", file);
    return postFormJson<PropertiesInfoResponse>("/api/v1/properties/info", fd);
  },

  /** Modify metadata of a single Office document. */
  modify: (file: File, props: PropertiesPayload) => {
    const fd = new FormData();
    fd.append("file", file);
    Object.entries(props).forEach(([k, v]) => {
      if (v !== undefined && v !== null) fd.append(k, String(v));
    });
    return postFormBlob("/api/v1/properties", fd);
  },

  /** Batch-modify metadata on multiple Office documents. */
  modifyBatch: (files: File[], props: PropertiesPayload) => {
    const fd = new FormData();
    files.forEach((f) => fd.append("files", f));
    Object.entries(props).forEach(([k, v]) => {
      if (v !== undefined && v !== null) fd.append(k, String(v));
    });
    return postFormBlob("/api/v1/properties/batch", fd);
  },
};

export const officeApi = {
  /** Merge multiple Excel/CSV files with identical structure. */
  mergeExcel: (files: File[], outputName?: string) => {
    const fd = new FormData();
    files.forEach((f) => fd.append("files", f));
    if (outputName) fd.append("filename", outputName);
    return postFormBlob("/api/v1/excel-merge", fd);
  },

  /** Strip metadata from an Office document. */
  cleanMetadata: (file: File) => {
    const fd = new FormData();
    fd.append("file", file);
    return postFormBlob("/api/v1/metadata-clean", fd);
  },

  /** Add page numbers, headers, and footers to a PDF. */
  pageDecorate: (
    file: File,
    config: Record<string, string | number | boolean>,
  ) => {
    const fd = new FormData();
    fd.append("file", file);
    Object.entries(config).forEach(([k, v]) => {
      fd.append(k, String(v));
    });
    return postFormBlob("/api/v1/page-decorate", fd);
  },
};
