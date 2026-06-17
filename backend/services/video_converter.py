"""Video conversion service: MP4 → WMV via ffmpeg."""

import os
import shutil
import subprocess

from errors import ErrorCode, ServiceResult


def mp4_to_wmv(input_path: str, output_path: str) -> ServiceResult[dict]:
    """Convert a video file to WMV format using ffmpeg.

    Uses the WMV2 video codec and WMA2 audio codec for maximum PowerPoint
    compatibility with older Windows versions.

    Args:
        input_path:  Path to the source video file (.mp4, .mov, etc.).
        output_path: Path for the output .wmv file.

    Returns:
        ServiceResult[dict] with input_size, output_size, duration_seconds.
    """
    if shutil.which("ffmpeg") is None:
        return ServiceResult.fail(
            ErrorCode.TOOL_NOT_AVAILABLE,
            "ffmpeg is not installed on this server",
        )

    # Get input video duration for the result
    duration = _probe_duration(input_path)

    cmd = [
        "ffmpeg",
        "-y",                              # overwrite output
        "-i", input_path,
        "-c:v", "wmv2",                    # WMV2 codec — max PPT compat
        "-c:a", "wmav2",                   # WMA2 audio
        "-q:v", "3",                        # quality (2-5, lower = better)
        "-q:a", "3",
        "-loglevel", "error",              # only errors to stderr
        output_path,
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600,  # 10-minute timeout for large files
        )
    except subprocess.TimeoutExpired:
        return ServiceResult.fail(
            ErrorCode.CONVERSION_FAILED,
            "Video conversion timed out (10-minute limit). Try a smaller file.",
        )

    if result.returncode != 0:
        return ServiceResult.fail(
            ErrorCode.CONVERSION_FAILED,
            f"ffmpeg error: {result.stderr.strip()[:200]}",
        )

    if not os.path.isfile(output_path) or os.path.getsize(output_path) == 0:
        return ServiceResult.fail(
            ErrorCode.CONVERSION_FAILED,
            "Conversion produced no output",
        )

    return ServiceResult.ok({
        "input_size": os.path.getsize(input_path),
        "output_size": os.path.getsize(output_path),
        "duration_seconds": duration,
    })


def _probe_duration(filepath: str) -> float:
    """Get video duration in seconds via ffprobe, or 0 on failure."""
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "csv=p=0",
                filepath,
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        return float(result.stdout.strip()) if result.stdout.strip() else 0.0
    except Exception:
        return 0.0
