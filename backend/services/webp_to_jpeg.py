"""WebP → JPEG conversion using Pillow.

WebP has no entry in `utils.file_security.MAGIC_SIGNATURES`, so the magic-number
layer is skipped for .webp uploads — Pillow's decoder is the only content gate.
"""

import os

from errors import ErrorCode, ServiceResult

DEFAULT_QUALITY = 90


def webp_to_jpeg(
    filepath: str,
    output_path: str,
    quality: int = DEFAULT_QUALITY,
) -> ServiceResult[dict]:
    """Convert a single WebP image to JPEG.

    Transparency is composited onto white: JPEG has no alpha channel, and
    Pillow's plain RGBA→RGB conversion renders transparent pixels black.
    Animated WebP lands on its first frame — `Image.open` positions there.

    Args:
        filepath: Path to the source .webp.
        output_path: Path to write the .jpg to.
        quality: JPEG quality (1–95).

    Returns:
        ServiceResult with dict keys: output, width, height.
    """
    if not os.path.isfile(filepath):
        return ServiceResult.fail(ErrorCode.FILE_NOT_FOUND, f"File not found: {filepath}")

    from PIL import Image

    try:
        with Image.open(filepath) as img:
            if img.mode in ("RGBA", "LA", "P"):
                rgba = img.convert("RGBA")
                canvas = Image.new("RGB", rgba.size, (255, 255, 255))
                canvas.paste(rgba, mask=rgba.split()[3])
                rgb = canvas
            else:
                rgb = img.convert("RGB")

            width, height = rgb.size
            rgb.save(output_path, format="JPEG", quality=quality)
    except Exception as e:
        return ServiceResult.fail(ErrorCode.CONVERSION_FAILED, f"Failed to convert WebP: {e}")

    return ServiceResult.ok({"output": output_path, "width": width, "height": height})
