"""Document conversion engine via subprocess calls to system tools.

Uses Pandoc for Markdown to DOCX conversion.
All system tools are called via subprocess — none are Python dependencies.
"""

import subprocess

from flask_babel import lazy_gettext as _l

from errors import ErrorCode, ServiceResult


# Default timeout in seconds for subprocess calls
SUBPROCESS_TIMEOUT = 120

# Per-tool timeout overrides (seconds)
_OPERATION_TIMEOUTS = {
    "pandoc": 300,
}


class ConversionError(Exception):
    """Raised when a document conversion fails."""


def _run_subprocess(
    cmd: list[str],
    description: str = "",
    timeout: int | None = None,
) -> None:
    """Run a subprocess command with timeout and error handling.

    Args:
        cmd: Command and arguments as a list.
        description: Human-readable description for error messages.
        timeout: Override timeout in seconds (uses per-operation config
                 or SUBPROCESS_TIMEOUT if not specified).

    Raises:
        ConversionError: If the command fails or times out.
    """
    if timeout is None:
        # Check for per-operation timeout override by command name
        timeout = _OPERATION_TIMEOUTS.get(cmd[0], SUBPROCESS_TIMEOUT)

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            timeout=timeout,
            check=False,
            text=True,
        )
        if result.returncode != 0:
            raise ConversionError(
                _l(
                    "%(description)s failed (exit code %(code)s): %(stderr)s"
                )
                % {
                    "description": description,
                    "code": result.returncode,
                    "stderr": result.stderr.strip(),
                }
            )
    except subprocess.TimeoutExpired:
        raise ConversionError(
            _l("%(description)s timed out after %(timeout)ss")
            % {"description": description, "timeout": timeout}
        )
    except FileNotFoundError:
        raise ConversionError(
            _l(
                "%(description)s failed: command '%(cmd)s' not found. "
                "Please ensure it is installed."
            )
            % {"description": description, "cmd": cmd[0]}
        )


def md_to_docx(md_path: str, docx_path: str) -> ServiceResult[str]:
    """Convert a Markdown file to DOCX using Pandoc.

    Returns the document title extracted from the first h1 heading.

    Args:
        md_path: Path to the input .md file.
        docx_path: Path for the output .docx file.
    """
    try:
        _run_subprocess(
            ["pandoc", md_path, "-o", docx_path,
             "--from", "markdown+tex_math_dollars+tex_math_single_backslash"],
            "Markdown to DOCX conversion",
        )
    except ConversionError as e:
        return ServiceResult.fail(ErrorCode.CONVERSION_FAILED, str(e))

    return ServiceResult.ok(_extract_title(md_path))


def _extract_title(md_path: str) -> str:
    """Extract the first h1 heading from a markdown file as the document title."""
    try:
        with open(md_path, "r", encoding="utf-8") as f:
            for line in f:
                stripped = line.strip()
                if stripped.startswith("# ") and not stripped.startswith("## "):
                    return stripped[2:].strip()
    except (OSError, UnicodeDecodeError):
        pass
    return "document"


# Remaining functions removed (ebook-to-md dropped)
