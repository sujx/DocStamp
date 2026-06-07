"""Image processor — resize, crop, format convert, and compress images."""

import os

from PIL import Image

from errors import ErrorCode, ServiceResult


SUPPORTED_FORMATS = {"png", "jpg", "jpeg", "tiff", "tif", "webp"}


def process_image(filepath: str, output_path: str, params: dict) -> ServiceResult[dict]:
    """Process an image: resize, crop, convert format, or compress.

    Args:
        filepath: Path to the source image.
        output_path: Path to write the processed image.
        params: Dict with:
            action: "resize" / "crop" / "convert" / "compress"
            width, height: For resize (pixels)
            keep_aspect: For resize (bool, default True)
            left, top, right, bottom: For crop (pixels)
            target_format: For convert ("png"/"jpeg"/"tiff")
            quality: For compress (1-100, JPEG only)

    Returns:
        ServiceResult with dict: original_size, processed_size, format, dimensions.
    """
    action = params.get("action", "")
    if action not in ("resize", "crop", "convert", "compress"):
        return ServiceResult.fail(ErrorCode.VALIDATION_ERROR, f"Unknown action: {action}")

    if not os.path.isfile(filepath):
        return ServiceResult.fail(ErrorCode.FILE_NOT_FOUND, f"File not found: {filepath}")

    try:
        img = Image.open(filepath)
    except Exception as e:
        return ServiceResult.fail(ErrorCode.VALIDATION_ERROR, f"Failed to open image: {e}")

    original_size = os.path.getsize(filepath)
    original_dims = img.size

    if action == "resize":
        width = int(params.get("width", 0))
        height = int(params.get("height", 0))
        keep_aspect = params.get("keep_aspect", "true").lower() != "false"

        if width <= 0 and height <= 0:
            return ServiceResult.fail(ErrorCode.VALIDATION_ERROR, "At least one of width or height is required")

        if keep_aspect:
            img.thumbnail((width or 99999, height or 99999), Image.LANCZOS)
        else:
            w = width or img.width
            h = height or img.height
            img = img.resize((w, h), Image.LANCZOS)

    elif action == "crop":
        try:
            left = int(params.get("left", 0))
            top = int(params.get("top", 0))
            right = int(params.get("right", img.width))
            bottom = int(params.get("bottom", img.height))
        except (ValueError, TypeError):
            return ServiceResult.fail(ErrorCode.VALIDATION_ERROR, "Crop coordinates must be integers")

        if left < 0 or top < 0 or right > img.width or bottom > img.height or left >= right or top >= bottom:
            return ServiceResult.fail(ErrorCode.VALIDATION_ERROR, "Invalid crop coordinates")

        img = img.crop((left, top, right, bottom))

    elif action == "convert":
        target_format = params.get("target_format", "").lower()
        if target_format not in ("png", "jpeg", "jpg", "tiff"):
            return ServiceResult.fail(ErrorCode.VALIDATION_ERROR, f"Unsupported target format: {target_format}")

        if target_format == "jpg":
            target_format = "jpeg"

        # Ensure output path has correct extension
        base = os.path.splitext(output_path)[0]
        ext_map = {"png": ".png", "jpeg": ".jpg", "tiff": ".tif"}
        output_path = base + ext_map.get(target_format, ".png")

        if img.mode in ("RGBA", "LA", "P") and target_format in ("jpeg",):
            img = img.convert("RGB")

    elif action == "compress":
        quality = int(params.get("quality", 80))
        quality = max(1, min(100, quality))

        if img.mode in ("RGBA", "LA", "P"):
            img = img.convert("RGB")

    # Determine save format and options
    ext = os.path.splitext(output_path)[1].lower()
    save_format = {"png": "PNG", "jpg": "JPEG", "jpeg": "JPEG",
                   "tif": "TIFF", "tiff": "TIFF", "webp": "WEBP"}.get(ext, "PNG")

    save_kwargs = {}
    if save_format == "JPEG":
        save_kwargs["quality"] = int(params.get("quality", 85)) if action == "compress" else 85
        save_kwargs["optimize"] = True
    elif save_format == "PNG":
        save_kwargs["optimize"] = True

    img.save(output_path, format=save_format, **save_kwargs)

    processed_size = os.path.getsize(output_path)

    return ServiceResult.ok({
        "original_size": original_size,
        "processed_size": processed_size,
        "format": save_format.lower(),
        "original_dimensions": list(original_dims),
        "processed_dimensions": list(img.size),
    })
