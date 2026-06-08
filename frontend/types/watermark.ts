/**
 * Watermark configuration types shared between WatermarkTab and API.
 *
 * @module types/watermark
 */

export type WatermarkType = "text" | "image";
export type WatermarkPosition = "tile" | "center";

export interface WatermarkParams {
  watermark_type: WatermarkType;
  text: string;
  font: string;
  font_size: number;
  color: string;
  opacity: number;
  rotation: number;
  position: WatermarkPosition;
  spacing_x: number;
  spacing_y: number;
  image_size: number;
}

export const DEFAULT_WATERMARK_PARAMS: WatermarkParams = {
  watermark_type: "text",
  text: "",
  font: "Helvetica",
  font_size: 48,
  color: "#D0D0D0",
  opacity: 0.3,
  rotation: -45,
  position: "tile",
  spacing_x: 200,
  spacing_y: 200,
  image_size: 150,
};
