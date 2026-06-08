/**
 * PDF-related types shared across PDF tool components.
 *
 * @module types/pdf
 */

export interface PdfPageThumb {
  page_no: number;
  thumb: string; // base64 data URL
  width: number;
  height: number;
}

export type CompressLevel = "light" | "medium" | "heavy";
export type ImageFormat = "png" | "jpeg";
export type PageSize = "original" | "a4" | "a4_landscape" | "letter" | "letter_landscape";
