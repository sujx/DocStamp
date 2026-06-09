/**
 * Watermark API: add and remove watermarks on PDF/DOCX files.
 *
 * @module api/modules/watermark
 */
import { postFormBlob } from "../index";

export interface WatermarkParams {
  watermark_type: "text" | "image";
  text?: string;
  font?: string;
  font_size?: number;
  color?: string;
  opacity?: number;
  rotation?: number;
  position?: "tile" | "center";
  spacing_x?: number;
  spacing_y?: number;
  image_size?: number;
}

export const watermarkApi = {
  /** Add a text or image watermark to a document. */
  add: (file: File, params: WatermarkParams, imageFile?: File) => {
    const fd = new FormData();
    fd.append("file", file);
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null) fd.append(k, String(v));
    });
    if (imageFile) fd.append("image", imageFile);
    return postFormBlob("/api/v1/watermark", fd);
  },

  /** Remove watermarks from a document. */
  remove: (file: File) => {
    const fd = new FormData();
    fd.append("file", file);
    return postFormBlob("/api/v1/watermark/remove", fd);
  },
};
