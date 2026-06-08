/**
 * Image processing API.
 *
 * @module api/modules/image
 */
import { postFormBlob } from "../index";

export const imageApi = {
  /** Process an image: scale, crop, convert format, compress. */
  process: (
    file: File,
    config: Record<string, string | number | boolean>,
  ) => {
    const fd = new FormData();
    fd.append("file", file);
    Object.entries(config).forEach(([k, v]) => {
      fd.append(k, String(v));
    });
    return postFormBlob("/api/image-process", fd);
  },
};
